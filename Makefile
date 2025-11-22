NIX_CMD=nix develop --command bash -c

.PHONY: check
check: check-fixit check-ruff

.PHONY: check-fixit
check-fixit:
	$(NIX_CMD) "fixit lint"

.PHONY: check-ruff
check-ruff:
	$(NIX_CMD) "ruff format --check && ruff check"

.PHONY: fix
fix: fix-fixit fix-ruff

.PHONY: fix-ruff
fix-ruff:
	$(NIX_CMD) "ruff format && ruff check --fix"

.PHONY: fix-fixit
fix-fixit:
	$(NIX_CMD) "fixit fix"
