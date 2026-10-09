<h1 align="center">
    Markdown Timelog Parser
</h1>

<p align="center">
    Calculates time totals per day, week, month, year and overall from hand-written Markdown time logs, and reports everything that looks wrong; on request also writes them as CSV.
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
│   ├── input/          # timelog.md: sample log with every date style, descriptions, midnight crossings, one line per problem kind (committed)
│   └── output/         # sessions.csv, summary.csv and problems.csv from an example run with --csv (gitignored)
├── config.yaml         # Your settings and folders (gitignored, offered on the first run)
├── config.example.yaml # Defaults: parses the example into example/output/ (committed)
├── main.py             # Entry point; its header docstring explains the steps
├── README.md
└── requirements.txt    # Pinned dependencies
```

------------------------------------------------------------------------------------------

## Usage

```bash
python main.py                                   # Same as --help: flags, current config values, examples; does nothing
python main.py --run                             # Print the totals and problems of example/input/
python main.py --run --csv                       # Also write the CSV files to example/output/
python main.py --run --entries                   # Also print every session with its duration
python main.py --run --period week,month         # Only weekly and monthly totals
python main.py --run --from 2026-01-01 --to 2026-12-31
python main.py --run --input D:/notes/timelog.md # One file
python main.py --run --input D:/notes --csv --output D:/notes/csv
python main.py --run --input D:/notes --pattern "timelog*.md"
python main.py --help                            # All flags, with the values config.yaml sets now
```

- Nothing is done without `--run`
    - `--run` uses the settings in `config.yaml`; any flag given with it overrides that setting for this run
    - flags without `--run` only print the help, plus the same command with `--run` added (exit code 2)
    - the help shows each setting's current value from `config.yaml` (`now: ...`), so you see what `--run` will do

- The log format
    - a session is one list line: `- <date> <start>-<end> [description]`
        ```markdown
        - 20250927      21.04-22.05 development: rendering test
        - 20-Feb-2025   22.20-00.36
        - 2025-09-25    14:00–15:30 planning
        ```
    - dates: any format listed in `date_formats`; as shipped `20250927`, `20-Feb-2025`, `2025-09-25`, `25.09.2025` (`%b` = English month abbreviations: Jan … Dec)
        - another style, e.g. `25/09/2025`: add `"%d/%m/%Y"` to `date_formats`, no code change needed
    - times: `HH.MM` or `HH:MM`, `-` or `–` between them; spacing between the parts doesn't matter
    - the description is optional free text after the times
    - an end before the start means the session ran past midnight; it counts for its start date (`22.20-00.36` = 2:16)
    - headings, text and list lines that don't start with a digit (`- a note`) are ignored, so notes can sit between sessions
- Periods
    - `periods` (or `--period`) picks the totals: `day`, `week`, `month`, `year`, `all`
    - weeks are ISO weeks, Monday to Sunday (`2025-W39`); the week holding 1 January can belong to the previous year
    - `date_from` / `date_to` (or `--from` / `--to`) limit the run to a date range, both ends included
- Sum
    - `sum` (or `--sum this_week,last_week`) prints one total per calendar window, counted from today
        - `this_day`, `this_week`, `this_month`, `this_year`: today, this week, this month, this year
        - `last_day`, `last_week`, `last_month`, `last_year`: the whole previous one
        - `all`: every session
    - weeks run Monday to Sunday; each line shows the dates it covers, e.g. `sum last_week  (2026-09-28 to 2026-10-04):    3:18  (2 sessions)`
    - ignores `date_from` / `date_to`: a sum always looks at every session in the log
    - printed last, in its own `=== SUM ===` block; console only (not in the CSV files)
- Problems
    - reported at the end of the run with file and line (also in `problems.csv` with `--csv`); the exit code is then 1
    - `ignore_problems: true` (or `--ignore-problems`): only their count is printed and the exit code stays 0; they are still detected and written to `problems.csv` with `--csv`

    | Kind | Meaning |
    |---|---|
    | `malformed` | starts like a session but doesn't parse: wrong shape (`9.5-10.00`), invalid time (`24.10`), or a date not in `date_formats` |
    | `unreadable` | the file can't be read as UTF-8; it is skipped (line 0) |
    | `duplicate` | same date, start and end as an earlier session |
    | `overlap` | starts before an earlier session has ended |
    | `empty` | start equals end, counted as 0 minutes (not 24 hours) |
    | `long` | longer than `max_session_hours` (default 12; 0 turns it off); **not counted** in the totals, the sums or `sessions.csv` |
    | `future` | dated after today |

    - problems are reported, never fixed: duplicates and overlaps still count in the totals, so they match the log until you correct it
    - except `long`: a session over `max_session_hours` is most likely a typo, so it isn't counted; TOTALS and SUM say so even with `ignore_problems`: a note under the TOTALS header, e.g. `(1 ignored as a possible mistake, over max_session_hours: 2025-03-03 19:33)`, and on every period row and SUM line it falls in, e.g. `2025-W10  0:00  (0 sessions; 1 ignored: 19:33 over max_session_hours, possible mistake)`
    - with `date_from` / `date_to`, problems follow the range too: a malformed line whose date can be read but falls outside it is left out; one whose date can't be read, and an unreadable file, are always reported
    - the total line names the range and how many sessions it left out, e.g. `2 sessions in 1 file(s) from 2026-10-01 to 2026-10-30, total 3:05 (13 outside the range skipped)`
- Output
    - by default the tool only calculates and prints; nothing is written
    - with `--csv` (or `write_csv: true`) it also writes three files to the output folder, overwritten on every such run
    - `sessions.csv`: `date, start, end, minutes, hours, description, file, line`, sorted by date and start
    - `summary.csv`: `kind, period, sessions, minutes, hours`: one row per period, grouped in the order day, week, month, year, all
    - `problems.csv`: `file, line, kind, message`; written even when empty, so an old one never lingers
    - the console always prints, in this order
        1. the sessions (with `--entries`) and the problems (or their count)
        2. what happened to the CSV files
        3. `=== TOTALS ===`: what was counted (date range, sessions left out), then the totals per period
        4. `=== SUM ... ===` last, if `sum` is set: one line per calendar window
- First run
    - `config.yaml` doesn't exist in a fresh checkout (it's gitignored); the first real run asks whether to create it from `config.example.yaml`
    - on `n`, without a terminal, or with `--dry-run`, nothing is created and `config.example.yaml` is used for that run
- Example data
    - as shipped, the tool reads `example/input/timelog.md` (and with `--csv` writes to `example/output/`): 13 sessions, three of them past midnight, one line for each problem kind, one note ignored (so the example run exits with 1)
    - to parse your own logs, point `input` / `output` in `config.yaml` (or flags) elsewhere; `input` may be a single file or a folder
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
- Every setting in `config.yaml` can also be given as a flag; the flag wins for that run only, `config.yaml` stays unchanged
- No `.env`: this tool needs no secrets, so every setting, including your folders, goes in `config.yaml` (gitignored). Should it ever need a secret, add `.env` the way the template does.

| Setting | `config.yaml` | Flag |
|---|---|---|
| A log file, or a folder of them | `input` | `--input` |
| Folder for the CSV files (with `write_csv`) | `output` | `--output` |
| Which files to read in a folder | `pattern` (`"*.md"`) | `--pattern` |
| Base for relative paths | `relative_to` (`tool` / `cwd`) | `--relative-to` |
| Totals to calculate | `periods` (`[day, week, month, year, all]`) | `--period week,month` |
| Accepted date styles | `date_formats` (strptime codes) | `--date-formats "%Y%m%d,%d/%m/%Y"` |
| Date range | `date_from` / `date_to` (`null` = open) | `--from` / `--to` |
| Totals for calendar windows from today, ignoring the date range | `sum` (`[this_week, last_week, this_month, last_month]`, `[]` = none) | `--sum this_week,last_month` |
| Don't count (and report) sessions longer than | `max_session_hours` (`12`, `0` = no limit) | `--max-hours` |
| Print every session | `show_entries` | `--entries` / `--no-entries` |
| Print only the number of problems, exit 0 | `ignore_problems` (`false`) | `--ignore-problems` / `--no-ignore-problems` |
| Write the CSV files | `write_csv` (`false` = only print) | `--csv` / `--no-csv` |
| Write nothing, not even `config.yaml` (wins over `write_csv`) | `dry_run` | `--dry-run` / `--no-dry-run` |

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
