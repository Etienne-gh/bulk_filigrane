import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import requests

SUPPORTED_EXT = {"jpg", "jpeg", "png", "heic", "pdf"}

CONTENT_TYPES = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "heic": "image/heic",
    "pdf": "application/pdf",
}

API_BASE = "https://api.filigrane.beta.gouv.fr/api/document"


# -----------------------------
# Helpers
# -----------------------------
def get_file_ext(file: Path) -> str:
    return file.suffix.lower().replace(".", "")


def collect_supported_files(folder: Path) -> List[Path]:
    files: List[Path] = []
    click.echo("➡️ Supported files:")
    for f in sorted(folder.iterdir()):
        if not f.is_file():
            continue

        ext = get_file_ext(f)
        if ext in SUPPORTED_EXT:
            click.echo(f"   • {f.name}")
            files.append(f)
        else:
            click.echo(f"⚠️ Skipping unsupported file: {f.name}")

    return files


def poll_until_ready(token: str, timeout_sec: int = 60) -> Optional[str]:
    poll_url = f"{API_BASE}/url/{token}"

    for _ in range(timeout_sec // 3):
        try:
            r = requests.get(poll_url, timeout=10)
            r.raise_for_status()
            data = r.json()
            if "url" in data:
                return data["url"]
        except Exception:
            # ignore and retry
            pass

        time.sleep(3)

    return None


def download_document(token: str, out_path: Path) -> bool:
    try:
        r = requests.get(f"{API_BASE}/{token}", timeout=60)
        r.raise_for_status()
    except Exception as e:
        click.echo(f"    ❌ Error downloading: {e}")
        return False

    with open(out_path, "wb") as f:
        f.write(r.content)

    return True


# -----------------------------
# Upload files
# -----------------------------
def upload_files(files: List[Path], watermark: str) -> Optional[str]:
    """
    Upload one or multiple files.
    Returns a single token (batch or single).
    """
    payload = []
    file_handles = []

    try:
        for file in files:
            ext = get_file_ext(file)
            fh = open(file, "rb")
            file_handles.append(fh)
            payload.append(("files[]", (file.name, fh, CONTENT_TYPES[ext])))

        r = requests.post(
            f"{API_BASE}/files",
            files=payload,
            data={"watermark": watermark},
            timeout=60,
        )
        r.raise_for_status()

        return r.json().get("token")

    except Exception as e:
        raise e

    finally:
        for fh in file_handles:
            try:
                fh.close()
            except Exception:
                pass


# -----------------------------
# Per-file processing task (no printing)
# -----------------------------
def process_files(files: List[Path], watermark: str, output_file_path: Path) -> Dict[str, Any]:
    result: Dict[str, Any] = {"files": [file.name for file in files], "success": False, "msg": ""}
    try:
        token = upload_files(files, watermark)
    except Exception as e:
        result["msg"] = f"upload failed: {e}"
        return result

    url = poll_until_ready(token)
    if not url:
        result["msg"] = "timeout"
        return result

    ok = download_document(token, output_file_path)
    if not ok:
        result["msg"] = "download failed"
        return result

    result["success"] = True
    result["msg"] = f"{output_file_path}"
    return result


# -----------------------------
# CLI
# -----------------------------
@click.command()
@click.argument("folder", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "--watermark",
    "-w",
    default="Document exclusivement destiné à la location immobilière",
    show_default=True,
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(file_okay=False, writable=True, path_type=Path),
    default=None,
    help="Custom output directory [default: <folder>/filigrane]",
)
@click.option(
    "--aggregate",
    is_flag=True,
    help="Upload all files at once and produce a single aggregated PDF.",
)
@click.option(
    "--aggregate-output",
    default="aggregated_filigrane_docs.pdf",
    type=str,
    show_default=True,
    help="Filename for aggregated mode output.",
)
def main(
    folder: Path,
    watermark: str,
    output_dir: Optional[Path],
    aggregate: bool,
    aggregate_output: str,
) -> None:
    if not output_dir:
        output_dir = folder / "filigrane"
    output_dir.mkdir(exist_ok=True)

    click.echo(f"Scanning folder: {folder}")
    files = collect_supported_files(folder)

    if not files:
        click.echo("No supported files found.")
        return

    if aggregate:
        click.echo(f"➡️ Aggregated mode: uploading {len(files)} files…")
        out_path = output_dir / aggregate_output
        results = [process_files(files, watermark, out_path)]
    else:
        click.echo(f"➡️ Processing {len(files)} files in parallel…")

        results: List[Dict[str, Any]] = []

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [
                executor.submit(process_files, [file], watermark, output_dir / file.name)
                for file in files
            ]

            total = len(futures)
            processed = 0

            click.echo(f"Processing files: 0/{total}", nl=False)

            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    results.append({"file": None, "success": False, "msg": f"error: {e}"})

                processed += 1
                click.echo(f"\rProcessing files: {processed}/{total}", nl=False)
            click.echo()

    click.echo("\n📄 Results:")
    for r in results:
        file_names = ",".join(r["files"]) if r.get("files") else "???"
        if r["success"]:
            click.echo(f"  ✅ {file_names}: {r['msg']}")
        else:
            click.echo(f"  ❌ {file_names}: {r['msg']}")

    click.echo("\n🎉 Done!")


if __name__ == "__main__":
    main()
