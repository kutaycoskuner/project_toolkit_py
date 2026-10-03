# <tool name>

<One or two sentences: what this tool does and when you'd use it.>

## Setup

```powershell
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # macOS/Linux: cp .env.example .env
```

## Usage

```powershell
python main.py                  # usage guide only, does nothing
python main.py --run            # process input/ into output/
python main.py --run --dry-run  # show what would happen, write nothing
python main.py --input D:\photos --output D:\photos_out
python main.py --help           # all flags
```

## Settings

Settings are read in this order, and later sources override earlier ones: the defaults in `main.py`, then `config.yaml`, then `.env`, then command-line flags.

| Where | What goes there | In git? |
|---|---|---|
| `config.yaml` | How the tool behaves: modes, patterns, options | yes |
| `.env` | Secrets and paths specific to one machine (`INPUT_DIR`, `OUTPUT_DIR`) | no, copy from `.env.example` |
| flags | Whatever changes from run to run | — |

Relative paths are resolved against this folder, not the folder you run the command from.

## Starting a new tool from this template

1. Copy the whole `_template/` folder and rename it. Don't copy `CHANGELOG.md`; it belongs to the template.
2. Fill in the `<...>` placeholders in `main.py` (header docstring, `run()`) and in this README.
3. Add the tool's packages to `requirements.txt`, with pinned versions.

## Template version

The `template` field in `main.py`'s header records which template version a tool was copied from. Each copy is independent: it never imports from or links to `_template/`. To upgrade a tool, follow the newer entries in [`_template/CHANGELOG.md`](../_template/CHANGELOG.md) and then bump the field.
