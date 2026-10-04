<h1 align="center">
    Markdown Formatter
</h1>

<p align="center">
    Cleans up text extracted from PDFs, or messy Markdown essays, into readable Markdown: wrapped lines become paragraphs, headings get spacing, and front matter and code blocks stay as they are.
</p>

<p align="center">
    <img alt="Template" src="https://img.shields.io/badge/template-3.1.1-blue" />
    <img alt="Last Update" src="https://img.shields.io/github/last-commit/kutaycoskuner/project_toolkit_py?path=markdown_formatter" />
</p>

------------------------------------------------------------------------------------------

## Folders

```bash
markdown_formatter/
├── .venv/              # Virtual environment (gitignored)
├── example/
│   ├── input/          # essay.md: a PDF-style essay with front matter, wrapped lines, a quote, code (committed)
│   └── output/         # The cleaned essay.md from the example run (gitignored)
├── config.yaml         # Your settings and paths (gitignored, offered on the first run)
├── config.example.yaml # Defaults: formats the example into example/output/ (committed)
├── main.py             # Entry point; its header docstring explains the rules and steps
├── README.md
└── requirements.txt    # Pinned dependencies
```

------------------------------------------------------------------------------------------

## Usage

```bash
python main.py                                   # Usage guide only, does nothing
python main.py --run                             # Format example/input/ into example/output/
python main.py --run --dry-run                   # List what would be written, write nothing
python main.py --input D:/notes/essay.md --output D:/notes/clean   # one file -> processed_text.md
python main.py --input D:/notes --output D:/notes/clean            # every *.md in a folder
python main.py --help                            # All flags
```

- What it changes
    - hard-wrapped lines are joined into one paragraph; blank lines between paragraphs stay
    - each heading (`#`, `##` …) gets a blank line before and after
    - the front matter (`---` block) and fenced code blocks are kept unchanged
    - indented text becomes a ```` ```plaintext ```` block on one line, with a line break before each in-text citation such as `(Smith, 2020)`
    - line ends are trimmed
- Input and output
    - a single file is written as `<output>/processed_text.md` (`output_name`)
    - a folder: every file matching `pattern` is written under its own name in `output`
    - existing results are overwritten; the inputs are never changed
- Known limitations (kept from the original, to be fixed separately)
    - consecutive list items and table rows are joined like paragraph lines, so lists and tables come out on one line
    - spaces inside a line are kept
    - a plaintext block follows the text before it without a blank line
- First run
    - `config.yaml` doesn't exist in a fresh checkout (it's gitignored); the first real run asks whether to create it from `config.example.yaml`
    - on `n`, without a terminal, or with `--dry-run`, nothing is created and `config.example.yaml` is used for that run
- Example data
    - as shipped, the tool formats `example/input/essay.md` into `example/output/essay.md`: wrapped lines joined, headings spaced, a quote with two citations split, code kept
    - to format your own files, point `input` / `output` in `config.yaml` (or flags) elsewhere
- After an update (e.g. a `git pull` that changes `config.example.yaml`)
    - the next run notices the example is newer than your `config.yaml` and asks
        - `m`: new example, your values kept (new keys and comments come from the example; keys it dropped are listed)
        - `r`: fresh copy of the example, your values are lost
        - `k`: keep `config.yaml` as it is; asked again only after the next example change
    - before `m` or `r`, the old file is saved as `config.yaml.bak` (gitignored)
    - without a terminal, or with `--dry-run`, nothing is written
    - every run also warns when `config.yaml` lacks keys the example has (they use defaults) or has keys the tool doesn't read
- Paths (`input`, `output`)
    - what you type decides absolute vs. relative; `relative_to` only matters for relative paths

    | You write | `relative_to` | Resolves to |
    |---|---|---|
    | `input: C:/Users/me/essay.md` | ignored | exactly that file |
    | `input: example/input` | `tool` (default) | `markdown_formatter/example/input`, from any folder you run it in |
    | `input: essays` | `cwd` | `<folder you run the command in>/essays` |

    - absolute on macOS / Linux: `input: /home/me/essay.md`
    - Windows: use `/`, or put a path with `\` in single quotes

------------------------------------------------------------------------------------------

## Settings

- Read in this order; later sources override earlier ones
    1. defaults in `main.py`
    2. `config.yaml` (offered on the first real run; until then `config.example.yaml`)
    3. command-line flags
- No `.env`: this tool needs no secrets, so every setting, including your paths, goes in `config.yaml` (gitignored). Should it ever need a secret, add `.env` the way the template does.

| Setting | `config.yaml` | Flag |
|---|---|---|
| File or folder to format | `input` | `--input` |
| Folder for the results | `output` | `--output` |
| Files to format in a folder | `pattern` (`"*.md"`) | `--pattern` |
| Result name for a single file | `output_name` (`processed_text.md`) | — |
| Base for relative paths | `relative_to` (`tool` / `cwd`) | `--relative-to` |
| List only | `dry_run` | `--dry-run` / `--no-dry-run` |

------------------------------------------------------------------------------------------

## Setup Python Environment

### Prerequisites
- **Python 3.10+**: [Install Python](https://www.python.org/downloads/) (includes `pip`).

### Steps

```bash
# 1. Go to the tool's folder
cd project_toolkit_py/markdown_formatter

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
