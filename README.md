# Bulk filigrane

bulk-filigrane is a tiny vibe-coding CLI tool to bulk-process documents using
api.filigrane.beta.gouv.fr and automatically apply a watermark.
Give it a folder and it will process all supported files in one go.

By default, the Filigrane website lets you upload multiple documents that get aggregated into a single PDF.
This CLI supports that aggregated mode too — but it also adds a second mode where files are processed individually, letting you download each watermarked document separately.

## 🚀 Usage

### CLI help

```shell
$ bulk-filigrane --help
Usage: bulk-filigrane [OPTIONS] FOLDER

Options:
  -w, --watermark TEXT        [default: Document exclusivement destiné à la
                              location immobilière]
  -o, --output-dir DIRECTORY  Custom output directory [default:
                              <folder>/filigrane]
  --aggregate                 Upload all files at once and produce a single
                              aggregated PDF.
  --aggregate-output TEXT     Filename for aggregated mode output.  [default:
                              aggregated_filigrane_docs.pdf]
  --help                      Show this message and exit.
```

### 📁 Supported formats

- pdf
- jpg / jpeg
- png
- heic

Unsupported files are skipped with a warning.

### With Nix (recommended)

Enter the development shell:

```shell
nix develop
```

Or automatically using direnv:

```shell
direnv allow
```

Once inside the environment, the CLI is available:

```shell
bulk-filigrane
```

### Manual run without Nix

If you prefer not to use Nix, install the dependencies manually:

```shell
pip install requests click
```

Then run the script directly:

```shell
python src/bulk_filigrane/main.py --help
```
