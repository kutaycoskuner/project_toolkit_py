# Template changelog

Each tool copied from `_template/` records the template version it's on in its `main.py` header (`template    : X.Y.Z`). To upgrade a tool, apply every entry newer than its version, then bump its `template` field.

Versions: **major** = the structure or settings contract changed, **minor** = something was added, **patch** = wording or a fix.

## 1.0.0 — 2026-10-03
- First versioned template. It replaces the unversioned `template.py`, so tools without a `template` field count as pre-1.0.
- `main.py`:
  - Header and module docstring follow `code-file-header`, with 91-character separators and `"""` alone on its first line.
  - Running with no arguments prints usage. `--run` runs with the defaults. `--dry-run`, `--input` and `--output` are available.
  - Settings precedence: command-line flags > `.env` > `config.yaml` > `DEFAULTS`. Relative paths resolve against the tool's own folder.
- `config.yaml` holds behaviour and is committed. `.env.example` lists the keys for secrets and machine-specific paths; the real `.env` is gitignored.
- `requirements.txt` pins `PyYAML==6.0.3` and `python-dotenv==1.0.1`.
- `README.md` covers setup, usage, and where each setting lives.
