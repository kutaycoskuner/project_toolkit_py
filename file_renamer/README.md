<h1 align="center">
    File Renamer
</h1>

<p align="center">
    Renames the files in a folder in bulk, adding the folder's name as a prefix or removing it, either in place or as renamed copies in an output folder. Every planned rename is shown first, and nothing changes until you confirm.
</p>

<p align="center">
    <img alt="Template" src="https://img.shields.io/badge/template-3.0.0-blue" />
    <img alt="Last Update" src="https://img.shields.io/github/last-commit/kutaycoskuner/project_toolkit_py?path=file_renamer" />
</p>

------------------------------------------------------------------------------------------

## Folders

```bash
file_renamer/
├── .venv/              # Virtual environment (gitignored)
├── example/
│   ├── input/Stone/    # Sample files; "Stone" is the prefix (committed)
│   └── output/         # Renamed copies from the example run (gitignored)
├── legacy/             # Superseded code, kept for reference only; see legacy/README.md (committed)
├── .env                # Secrets only; this tool needs none (gitignored, copy of .env.example)
├── .env.example        # Secret keys .env needs (none yet)
├── config.yaml         # Your settings: folder, mode, pattern, dry_run (gitignored, offered on first run)
├── config.example.yaml # Defaults: processes the example into example/output/ (committed)
├── main.py             # Entry point; its header docstring explains the steps
├── README.md
└── requirements.txt    # Pinned dependencies
```

------------------------------------------------------------------------------------------

## Usage

```bash
python main.py                                   # Usage guide only, does nothing
python main.py --run                             # Example: renamed copies of example/input/Stone/ in example/output/
python main.py --run --dry-run                   # Preview only, change nothing
python main.py --folder D:/Assets/Stone --in-place   # Rename the files themselves
python main.py --folder D:/Assets/Stone --mode add
python main.py --folder D:/Assets/Stone --mode remove --pattern "*.png"
python main.py --help                            # All flags
```

- First run
    - `config.yaml` doesn't exist in a fresh checkout (it's gitignored); the first real run asks whether to create it from `config.example.yaml`
    - on `n`, without a terminal, or with `--dry-run`, nothing is created and `config.example.yaml` is used for that run
    - later runs warn when `config.yaml` lacks keys the example has (they use defaults) or has keys the tool doesn't read; copy new keys over after an update
- Example data
    - as shipped, the tool writes renamed copies of `example/input/Stone/` into `example/output/`, so you can see what it does before configuring anything; the samples never change
    - to work on your own files, set `folder` in `config.yaml` (or `--folder`) and choose `output` below
- In place or copy (`output`)
    - empty (`""`, or `--in-place`): the files in the work folder are renamed themselves
    - a folder (or `--output DIR`): only files that get a new name are copied there under that name; the originals stay unchanged, and files from an earlier run are overwritten
    - without an `output` key in `config.yaml`, the tool renames in place
- Modes
    - `add`: `Stone/a.png` → `Stone_a.png`
    - `remove`: `Stone/Stone_a.png` → `a.png`
        - only names starting with the folder name are renamed, ignoring upper/lower case
        - a `-` or `_` right after the prefix is removed too
        - files whose new name would be empty are skipped
- Preview and confirm
    - every planned rename is listed first; `y` applies, anything else cancels
    - with no terminal to ask on, nothing is renamed
- Paths (`folder`, `output`)
    - what you type decides absolute vs. relative; `relative_to` only matters for relative paths

    | You write | `relative_to` | Resolves to |
    |---|---|---|
    | `folder: C:/Users/me/Assets/Stone` | ignored | exactly that folder |
    | `folder: example/input/Stone` | `tool` (default) | `file_renamer/example/input/Stone`, from any folder you run it in |
    | `folder: Stone` | `cwd` | `<folder you run the command in>/Stone` |

    - absolute on macOS / Linux: `folder: /home/me/assets/Stone`
    - Windows: use `/`, or put a path with `\` in single quotes
    - `cwd` example: `cd D:/Assets`, then `python <path>/main.py --run --folder Stone --relative-to cwd` uses `D:/Assets/Stone`
- Collisions
    - if an earlier file in the same run took a name (or, in place, a file with that name already exists), a `01`, `02` … suffix is added
    - the preview marks these with `[CONFLICT RESOLVED]`

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
- this tool needs no secrets, so all its settings (including your work folder) go in `config.yaml` and `.env` may stay empty

| | `.env` | `config.yaml` |
|---|---|---|
| Holds | secrets: anything that grants access or costs money if leaked | everything else that controls the tool |
| Examples | API keys, access tokens, passwords, webhook URLs with a token, connection strings with credentials | `folder`, `output`, `relative_to`, `mode`, `pattern`, `dry_run` |
| Read by | the code that needs it, with `os.getenv("NAME")` | `load_settings()`, merged with defaults and flags |
| Committed template | `.env.example`: key names, empty values | `config.example.yaml`: working defaults with comments |
| Never | paths or behaviour settings | secrets |

| Where | In git? |
|---|---|
| `config.yaml` | no, created on the first run (after asking) |
| `.env` | no, copy from `.env.example` |
| flags | — (for whatever changes from run to run) |

| Setting | `config.yaml` | Flag |
|---|---|---|
| Work folder | `folder` | `--folder` |
| In place / copy folder | `output` | `--in-place` / `--output` |
| Base for relative paths | `relative_to` (`tool` / `cwd`) | `--relative-to` |
| `add` / `remove` | `mode` | `--mode` |
| File pattern | `pattern` | `--pattern` |
| Preview only | `dry_run` | `--dry-run` / `--no-dry-run` |

------------------------------------------------------------------------------------------

## Setup Python Environment

### Prerequisites
- **Python 3.10+**: [Install Python](https://www.python.org/downloads/) (includes `pip`).

### Steps

```bash
# Go to the tool's folder
cd project_toolkit_py/file_renamer

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
