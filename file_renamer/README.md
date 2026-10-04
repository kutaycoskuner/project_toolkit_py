<h1 align="center">
    File Renamer
</h1>

<p align="center">
    Renames the files in a folder in bulk: adds or removes a prefix (the folder's name by default), renames to a numbered template, lower-cases names and changes extensions, either in place or as renamed copies. Every planned rename is shown first, and nothing changes until you confirm.
</p>

<p align="center">
    <img alt="Template" src="https://img.shields.io/badge/template-3.1.1-blue" />
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
python main.py --folder D:/Assets/Stone --mode none --rename frame --digits 3   # frame_001.png ...
python main.py --folder D:/Assets/Stone --mode none --lowercase --extension .md
python main.py --help                            # All flags
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
    - as shipped, the tool writes renamed copies of `example/input/Stone/` into `example/output/`, so you can see what it does before configuring anything; the samples never change
    - to work on your own files, set `folder` in `config.yaml` (or `--folder`) and choose `output` below
- In place or copy (`output`)
    - empty (`""`, or `--in-place`): the files in the work folder are renamed themselves
    - a folder (or `--output DIR`): only files that get a new name are copied there under that name; the originals stay unchanged, and files from an earlier run are overwritten
    - without an `output` key in `config.yaml`, the tool renames in place
- What changes a name: one pass, in this order
    1. `rename`: `frame` → `frame_01`, `frame_02` … (numbered in preview order, `digits` wide); empty = keep the name
    2. `mode` with `prefix` (empty `prefix` = the work folder's name)
        - `add`: `Stone/a.png` → `Stone_a.png`
        - `remove`: `Stone/Stone_a.png` → `a.png`
            - only names starting with the prefix lose it, ignoring upper/lower case; a `-` or `_` right after it goes too
            - names without the prefix stay, but still get the other steps
            - files whose new name would be empty are skipped
        - `none`: prefixes are left alone
    3. `lowercase`: `B.PNG` → `b.PNG` (the extension is kept)
    4. `extension`: `.md` changes or adds it: `notes.txt` → `notes.md`; empty = keep
    - files whose name ends up unchanged are left out of the preview
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

- No `.env`: this tool needs no secrets, so every setting, including your work folder, goes in `config.yaml` (gitignored, created on the first run after asking). Should it ever need a secret, add `.env` the way the template does.

| Setting | `config.yaml` | Flag |
|---|---|---|
| Work folder | `folder` | `--folder` |
| In place / copy folder | `output` | `--in-place` / `--output` |
| Base for relative paths | `relative_to` (`tool` / `cwd`) | `--relative-to` |
| Numbered rename | `rename`, `digits` | `--rename`, `--digits` |
| `add` / `remove` / `none` | `mode` | `--mode` |
| Prefix to add/remove | `prefix` | `--prefix` |
| Lower-case names | `lowercase` | `--lowercase` / `--no-lowercase` |
| New extension | `extension` | `--extension` |
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

# Deactivate the environment when done (optional)
deactivate
```
