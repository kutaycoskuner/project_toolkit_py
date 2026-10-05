<h1 align="center">
    Tool Name
</h1>

<p align="center">
    One or two sentences: what this tool does and when you'd use it.
</p>

<p align="center">
    <img alt="Template" src="https://img.shields.io/badge/template-3.1.1-blue" />
    <img alt="Last Update" src="https://img.shields.io/github/last-commit/kutaycoskuner/python-toolbox?path=tool_folder" />
</p>

------------------------------------------------------------------------------------------

## Folders

```bash
tool_folder/
├── .venv/              # Virtual environment (gitignored)
├── example/            # Bundled demo data, processed by default
│   ├── input/          # Sample input (committed)
│   └── output/         # Result of the demo run (gitignored)
├── .env                # Secrets only, e.g. API keys (gitignored, copy of .env.example)
├── .env.example        # Secret keys .env needs, with empty values
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
- After an update (e.g. a `git pull` that changes `config.example.yaml`)
    - the next run notices the example is newer than your `config.yaml` and asks
        - `m`: new example, your values kept (new keys and comments come from the example; keys it dropped are listed)
        - `r`: fresh copy of the example, your values are lost
        - `k`: keep `config.yaml` as it is; asked again only after the next example change
    - before `m` or `r`, the old file is saved as `config.yaml.bak` (gitignored)
    - without a terminal, or with `--dry-run`, nothing is written
    - every run also warns when `config.yaml` lacks keys the example has (they use defaults) or has keys the tool doesn't read
- Example data
    - as shipped, the tool processes `example/input/` into `example/output/`, so you can see what it does before configuring anything
    - to use your own data, point `input` / `output` in `config.yaml` (or flags) elsewhere
- Paths (`input`, `output`)
    - what you type decides absolute vs. relative; `relative_to` only matters for relative paths

    | You write | `relative_to` | Resolves to |
    |---|---|---|
    | `input: C:/Users/me/photos` | ignored | exactly that folder |
    | `input: example/input` | `tool` (default) | `tool_folder/example/input`, from any folder you run it in |
    | `input: photos` | `cwd` | `<folder you run the command in>/photos` |

    - absolute on macOS / Linux: `input: /home/me/photos`
    - Windows: use `/`, or put a path with `\` in single quotes
    - `cwd` example: `cd D:/data`, then `python <path>/main.py --run --input photos --relative-to cwd` uses `D:/data/photos`

------------------------------------------------------------------------------------------

## Settings

- Read in this order; later sources override earlier ones
    1. defaults in `main.py`
    2. `config.yaml` (offered on the first real run; until then `config.example.yaml`)
    3. command-line flags
- Relative paths resolve against `relative_to`: this tool's folder (`tool`, default) or the folder you run the command from (`cwd`).

### `.env` or `config.yaml`?

- rule of thumb: **would leaking it grant access or cost money?** Then `.env`. Otherwise `config.yaml`.
- every setting has exactly one home; never put the same value in both, or one silently overrides the other
- both files are gitignored; only `.env.example` and `config.example.yaml` are committed

| | `.env` | `config.yaml` |
|---|---|---|
| Holds | secrets: anything that grants access or costs money if leaked | everything else that controls the tool |
| Examples | API keys, access tokens, passwords, webhook URLs with a token, connection strings with credentials | input/output paths, `relative_to`, modes, patterns, sizes, thresholds, `dry_run`, usernames and IDs that aren't secret |
| Read by | the code that needs it, with `os.getenv("NAME")` | `load_settings()`, merged with defaults and flags |
| Committed template | `.env.example`: key names, empty values | `config.example.yaml`: working defaults with comments |
| Never | paths or behaviour settings | secrets |

| Where | In git? |
|---|---|
| `config.yaml` | no, created on the first run (after asking) |
| `.env` | no, copy from `.env.example` |
| flags | — (for whatever changes from run to run) |

------------------------------------------------------------------------------------------

## Setup Python Environment

### Prerequisites
- **Python 3.10+**: [Install Python](https://www.python.org/downloads/) (includes `pip`).

### Steps

```bash
# Go to the tool's folder
cd python-toolbox/tool_folder

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
#   Windows:
.venv\Scripts\activate
#   macOS / Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create your .env from the example; it holds secrets only and may stay empty (config.yaml is offered on the first run)
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
    5. no secrets needed? remove the `.env` parts: `.env.example`, the `load_dotenv` import and call in `main.py`, `python-dotenv` in `requirements.txt`, and the `.env` lines in this README; they're only here as an explicit template part
- Template version
    - the `template` field in `main.py`'s header (and the badge above) records which version a tool was copied from
    - each copy is independent: it never imports from or links to `_template/`
    - to upgrade a tool, follow the newer entries in [`_template/CHANGELOG.md`](../_template/CHANGELOG.md), then bump the field and the badge
