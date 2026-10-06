<h1 align="center">
    Markdown Timelog Parser
</h1>

<p align="center">
    Turns hand-written Markdown time logs into structured data: one CSV row per session, plus totals per month and per day.
</p>

<p align="center">
    <img alt="Template" src="https://img.shields.io/badge/template-3.2.0-blue" />
    <img alt="Last Update" src="https://img.shields.io/github/last-commit/kutaycoskuner/python-toolbox?path=markdown_timelog_parser" />
</p>

------------------------------------------------------------------------------------------

## Folders

```bash
markdown_timelog_parser/
├── .venv/              # Virtual environment (gitignored)
├── example/
│   ├── input/          # timelog.md: sample log with both date styles, midnight crossings, a bad line (committed)
│   └── output/         # sessions.csv and summary.csv from the example run (gitignored)
├── config.yaml         # Your settings and folders (gitignored, offered on the first run)
├── config.example.yaml # Defaults: parses the example into example/output/ (committed)
├── main.py             # Entry point; its header docstring explains the steps
├── README.md
└── requirements.txt    # Pinned dependencies
```

------------------------------------------------------------------------------------------

## Usage

```bash
python main.py                                   # Usage guide only, does nothing
python main.py --run                             # Parse example/input/ into example/output/
python main.py --run --dry-run                   # Print the totals, write nothing
python main.py --input D:/notes --output D:/notes/csv
python main.py --input D:/notes --pattern "timelog*.md"
python main.py --help                            # All flags
```

- The log format
    - a session is one list line: `- <date> <start>-<end>`
        ```markdown
        - 20250927      21.04-22.05
        - 20-Feb-2025   22.20-00.36
        ```
    - dates: `YYYYMMDD` or `dd-Mon-yyyy` (English month abbreviations: Jan … Dec)
    - times: `HH.MM` or `HH:MM`; spacing between the parts doesn't matter
    - an end before the start means the session ran past midnight; it counts for its start date (`22.20-00.36` = 2:16)
    - headings, text and list lines that don't start with a digit (`- a note`) are ignored, so notes can sit between sessions
    - a list line that starts with a digit but doesn't parse (`- 20250930 9.5-10.00`) is reported as "Skipped, not a valid session", with file and line
    - equal start and end count as 0 minutes, not 24 hours
- Output (overwritten on every run)
    - `sessions.csv`: `date, start, end, minutes, file, line`, sorted by date and start
    - `summary.csv`: `kind, period, sessions, minutes, hours`: one row per month, then one per day
    - the console prints the total and the monthly totals
- First run
    - `config.yaml` doesn't exist in a fresh checkout (it's gitignored); the first real run asks whether to create it from `config.example.yaml`
    - on `n`, without a terminal, or with `--dry-run`, nothing is created and `config.example.yaml` is used for that run
- Example data
    - as shipped, the tool parses `example/input/timelog.md` into `example/output/`: 6 sessions, two of them past midnight, one malformed line reported, one note ignored
    - to parse your own logs, point `input` / `output` in `config.yaml` (or flags) elsewhere
- After an update (e.g. a `git pull` that adds or removes settings in `config.example.yaml`)
    - every run compares the settings (top-level keys) in your `config.yaml` with the example's; when they differ, it lists missing keys (defaults used) and unknown keys (ignored) and asks
        - `m`: new example, your values kept (new keys and comments come from the example; keys it dropped are listed)
        - `r`: fresh copy of the example, your values are lost
        - `k`: keep `config.yaml` as it is; asked again on the next run
    - before `m` or `r`, the old file is saved as `config.yaml.bak` (gitignored)
    - without a terminal, or with `--dry-run`, nothing is written
- Paths (`input`, `output`)
    - what you type decides absolute vs. relative; `relative_to` only matters for relative paths

    | You write | `relative_to` | Resolves to |
    |---|---|---|
    | `input: C:/Users/me/notes` | ignored | exactly that folder |
    | `input: example/input` | `tool` (default) | `markdown_timelog_parser/example/input`, from any folder you run it in |
    | `input: notes` | `cwd` | `<folder you run the command in>/notes` |

    - absolute on macOS / Linux: `input: /home/me/notes`
    - Windows: use `/`, or put a path with `\` in single quotes

------------------------------------------------------------------------------------------

## Settings

- Read in this order; later sources override earlier ones
    1. defaults in `main.py`
    2. `config.yaml` (offered on the first real run; until then `config.example.yaml`)
    3. command-line flags
- No `.env`: this tool needs no secrets, so every setting, including your folders, goes in `config.yaml` (gitignored). Should it ever need a secret, add `.env` the way the template does.

| Setting | `config.yaml` | Flag |
|---|---|---|
| Folder with the logs | `input` | `--input` |
| Folder for the CSV files | `output` | `--output` |
| Which files to read | `pattern` (`"*.md"`) | `--pattern` |
| Base for relative paths | `relative_to` (`tool` / `cwd`) | `--relative-to` |
| Print only | `dry_run` | `--dry-run` / `--no-dry-run` |

------------------------------------------------------------------------------------------

## Setup Python Environment

### Prerequisites
- **Python 3.10+**: [Install Python](https://www.python.org/downloads/) (includes `pip`).

### Steps

```bash
# 1. Go to the tool's folder
cd python-toolbox/markdown_timelog_parser

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
