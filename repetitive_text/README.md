<h1 align="center">
    Repetitive Text
</h1>

<p align="center">
    Writes one line per number from a start to an end value into a text file, from a line template: for long, numbered command lists such as macro or script lines.
</p>

<p align="center">
    <img alt="Template" src="https://img.shields.io/badge/template-3.1.1-blue" />
    <img alt="Last Update" src="https://img.shields.io/github/last-commit/kutaycoskuner/python-toolbox?path=repetitive_text" />
</p>

------------------------------------------------------------------------------------------

## Folders

```bash
repetitive_text/
├── .venv/              # Virtual environment (gitignored)
├── example/
│   └── output/         # output.txt from the example config (gitignored, created on the first run)
├── config.yaml         # Your settings (gitignored, offered on the first run)
├── config.example.yaml # start, end, step, line template: the tool's example (committed)
├── main.py             # Entry point; its header docstring explains the steps
├── README.md
└── requirements.txt    # Pinned dependencies
```

------------------------------------------------------------------------------------------

## Usage

```bash
python main.py                                   # Usage guide only, does nothing
python main.py --run                             # Lines 7981..8044 into example/output/output.txt
python main.py --run --dry-run                   # Show the first and last line, write nothing
python main.py --start 1 --end 10 --line "pushlist spellbook_scrolls {i}"
python main.py --start 0 --end 100 --step 10 --line "wait {i}"     # wait 0, wait 10 ... wait 100
python main.py --help                            # All flags
```

- The line template
    - `{i}` is the number; `start` and `end` are both included, counting by `step`
    - other braces must be doubled (`{{` / `}}`), because the template is a Python format string; any other `{placeholder}` stops the run and names it
    - example: `pushlist spellbook_scrolls {i}` with 7981 … 8044 gives 64 lines, `pushlist spellbook_scrolls 7981` … `8044`
- Output
    - `output/output_file` (`example/output/output.txt` by default), overwritten on every run
    - no trailing newline after the last line
- First run
    - `config.yaml` doesn't exist in a fresh checkout (it's gitignored); the first real run asks whether to create it from `config.example.yaml`
    - on `n`, without a terminal, or with `--dry-run`, nothing is created and `config.example.yaml` is used for that run
- Example data
    - this tool reads no input files: `config.example.yaml` itself is the example, and as shipped it writes lines 7981 … 8044 to `example/output/output.txt`
- After an update (e.g. a `git pull` that changes `config.example.yaml`)
    - the next run notices the example is newer than your `config.yaml` and asks
        - `m`: new example, your values kept (new keys and comments come from the example; keys it dropped are listed)
        - `r`: fresh copy of the example, your values are lost
        - `k`: keep `config.yaml` as it is; asked again only after the next example change
    - before `m` or `r`, the old file is saved as `config.yaml.bak` (gitignored)
    - without a terminal, or with `--dry-run`, nothing is written
    - every run also warns when `config.yaml` lacks keys the example has (they use defaults) or has keys the tool doesn't read
- Paths (`output`)
    - what you type decides absolute vs. relative; `relative_to` only matters for relative paths

    | You write | `relative_to` | Resolves to |
    |---|---|---|
    | `output: C:/Users/me/macros` | ignored | exactly that folder |
    | `output: example/output` | `tool` (default) | `repetitive_text/example/output`, from any folder you run it in |
    | `output: macros` | `cwd` | `<folder you run the command in>/macros` |

    - absolute on macOS / Linux: `output: /home/me/macros`
    - Windows: use `/`, or put a path with `\` in single quotes

------------------------------------------------------------------------------------------

## Settings

- Read in this order; later sources override earlier ones
    1. defaults in `main.py`
    2. `config.yaml` (offered on the first real run; until then `config.example.yaml`)
    3. command-line flags
- No `.env`: this tool needs no secrets, so every setting goes in `config.yaml` (gitignored). Should it ever need a secret, add `.env` the way the template does.

| Setting | `config.yaml` | Flag |
|---|---|---|
| First number | `start` | `--start` |
| Last number | `end` | `--end` |
| Count by | `step` (`1`) | `--step` |
| Line template | `line` | `--line` |
| Output folder | `output` | `--output` |
| Output file name | `output_file` (`output.txt`) | — |
| Base for relative paths | `relative_to` (`tool` / `cwd`) | `--relative-to` |
| Preview only | `dry_run` | `--dry-run` / `--no-dry-run` |

------------------------------------------------------------------------------------------

## Setup Python Environment

### Prerequisites
- **Python 3.10+**: [Install Python](https://www.python.org/downloads/) (includes `pip`).

### Steps

```bash
# 1. Go to the tool's folder
cd python-toolbox/repetitive_text

# 2. Create a virtual environment
python -m venv .venv

# 3. Activate it
#   Windows:
.venv\Scripts\activate
#   macOS / Linux:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run it (config.yaml is offered on the first run)
python main.py --run

# 6. Deactivate the environment when done (optional)
deactivate
```
