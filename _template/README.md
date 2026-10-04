<h1 align="center">
    Tool Name
</h1>

<p align="center">
    One or two sentences: what this tool does and when you'd use it.
</p>

<p align="right">
    <img alt="Template" src="https://img.shields.io/badge/template-2.0.0-blue" />
    <img alt="Last Update" src="https://img.shields.io/github/last-commit/kutaycoskuner/project_toolkit_py?path=tool_folder" />
</p>

------------------------------------------------------------------------------------------

## Folders

```bash
tool_folder/
├── .venv/              # Virtual environment (gitignored)
├── example/            # Bundled demo data, processed by default
│   ├── input/          # Sample input (committed)
│   └── output/         # Result of the demo run (gitignored)
├── .env                # Secrets and machine-specific paths (gitignored, copy of .env.example)
├── .env.example        # Keys .env needs, with empty values
├── config.yaml         # Your settings, may hold personal paths (gitignored, created on first run)
├── config.example.yaml # Default settings with comments (committed)
├── main.py             # Entry point; its header docstring explains the steps
├── README.md
└── requirements.txt    # Pinned dependencies
```

------------------------------------------------------------------------------------------

## Usage

```bash
python main.py                  # Usage guide only, does nothing
python main.py --run            # First run: offers to create config.yaml, processes example/input/ into example/output/
python main.py --run --dry-run  # Show what would happen, write nothing
python main.py --input D:/photos --output D:/photos_out
python main.py --help           # All flags
```

- First run
    - `config.yaml` doesn't exist in a fresh checkout (it's gitignored); the first real run asks whether to create it from `config.example.yaml`
    - on `n`, without a terminal, or with `--dry-run`, nothing is created and `config.example.yaml` is used for that run
- Example data
    - as shipped, the tool processes `example/input/` into `example/output/`, so you can see what it does before configuring anything
    - to use your own data, point `input` / `output` in `config.yaml` (or `.env`, or flags) elsewhere

------------------------------------------------------------------------------------------

## Settings

- Read in this order; later sources override earlier ones
    1. defaults in `main.py`
    2. `config.yaml` (offered on the first real run; until then `config.example.yaml`)
    3. `.env`
    4. command-line flags
- Relative paths resolve against this folder, not the folder you run the command from.

| Where | What goes there | In git? |
|---|---|---|
| `config.yaml` | How the tool behaves: modes, patterns, options, and your paths if you like | no, created on the first run (after asking) |
| `.env` | Secrets and machine-specific paths (`INPUT_DIR`, `OUTPUT_DIR`) | no, copy from `.env.example` |
| flags | Whatever changes from run to run | — |

------------------------------------------------------------------------------------------

## Setup Python Environment

### Prerequisites
- **Python 3.10+**: [Install Python](https://www.python.org/downloads/) (includes `pip`).

### Steps

```bash
# Go to the tool's folder
cd project_toolkit_py/tool_folder

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
#   Windows:
.venv\Scripts\activate
#   macOS / Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create your .env from the example, then fill in its values (config.yaml is created on the first run)
#   Windows:
copy .env.example .env
#   macOS / Linux:
cp .env.example .env

# Deactivate the environment when done (optional)
deactivate
```

------------------------------------------------------------------------------------------

## Template (delete this section in a copy)

- Starting a new tool
    1. copy the whole `_template/` folder and rename it; don't copy `CHANGELOG.md`, it belongs to the template
    2. replace `Tool Name` and `tool_folder` above, and the `<...>` placeholders in `main.py` (header docstring, `run()`)
    3. replace `example/input/` with sample data that shows what the tool does, and set `config.example.yaml` to process it
    4. add the tool's packages to `requirements.txt`, with pinned versions
- Template version
    - the `template` field in `main.py`'s header (and the badge above) records which version a tool was copied from
    - each copy is independent: it never imports from or links to `_template/`
    - to upgrade a tool, follow the newer entries in [`_template/CHANGELOG.md`](../_template/CHANGELOG.md), then bump the field and the badge
