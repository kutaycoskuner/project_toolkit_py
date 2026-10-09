<h1 align="center">
    Markdown Front Matter Migrator
</h1>

<p align="center">
    Rewrites the <code>---</code> front matter of every Markdown file in a folder to a new template, carrying selected old values over: for moving a blog or notes collection to a new metadata schema in one run.
</p>

<p align="center">
    <img alt="Template" src="https://img.shields.io/badge/template-3.2.0-blue" />
    <img alt="Last Update" src="https://img.shields.io/github/last-commit/kutaycoskuner/python-toolbox?path=markdown_frontmatter_migrator" />
</p>

------------------------------------------------------------------------------------------

## Folders

```bash
markdown_frontmatter_migrator/
├── .venv/              # Virtual environment (gitignored)
├── example/
│   ├── input/          # Old-schema posts: string tags, renamed keys, a subfolder, a file without front matter (committed)
│   └── output/         # The migrated copies from the example run (gitignored)
├── config.yaml         # Your folders and front matter template (gitignored, offered on the first run)
├── config.example.yaml # Defaults: the template and mapping, migrates the example (committed)
├── main.py             # Entry point; its header docstring explains the rules and steps
├── README.md
└── requirements.txt    # Pinned dependencies
```

------------------------------------------------------------------------------------------

## Usage

```bash
python main.py                                   # Usage guide only, does nothing
python main.py --run                             # Migrate example/input/ into example/output/
python main.py --run --dry-run                   # List what would be written, write nothing
python main.py --input D:/blog/posts --output D:/blog/posts_v1.6
python main.py --help                            # All flags
```

- How the new front matter is built
    1. every field of `template_fields`, in that order, starting from its default
    2. fields in `keep_from_old` (new field: old field) take the old file's value when it has that field
    3. `list_fields` become lists: `tags: python; markdown` → `[python, markdown]` (split on `list_separator`, items trimmed)
    4. `today_fields` are set to today's date
    - old fields mentioned nowhere are dropped; the text after the front matter is kept
- Example: with the shipped config, this old front matter
    ```yaml
    title: First post
    version: '1.1'
    date: 2023-05-02
    isVisible: false
    tags: python; markdown ;  tools
    author: someone else
    ```
    becomes `revision: 1.1`, `created: 2023-05-02`, `visibility: false`, `tags: [python, markdown, tools]`, `author: lichzelg` (the template's default, since `author` isn't in `keep_from_old`), `updated: <today>`, plus every other template field with its default
- Files
    - every file matching `pattern` under `input`, subfolders included, is written to the same relative path under `output`
    - existing results are overwritten; the inputs are never changed
    - a file without front matter gets the full template on top of its text
- Known limitations (kept from the original, to be fixed separately)
    - all quote characters are removed from the written YAML: `Don't panic: a note` becomes `title: Dont panic: a note`, which loses the apostrophe, and a `: ` inside a value makes that front matter invalid YAML
- First run
    - `config.yaml` doesn't exist in a fresh checkout (it's gitignored); the first real run asks whether to create it from `config.example.yaml`
    - on `n`, without a terminal, or with `--dry-run`, nothing is created and `config.example.yaml` is used for that run
- Example data
    - as shipped, the tool migrates `example/input/` into `example/output/`: one post with every renamed field, one in a subfolder with list tags and the apostrophe case, one without front matter; a `.txt` would be skipped
    - to migrate your own files, point `input` / `output` in `config.yaml` (or flags) elsewhere, and set `template_fields` / `keep_from_old` to your schema
- After an update (e.g. a `git pull` that adds or removes settings in `config.example.yaml`)
    - every run compares the settings (top-level keys) in your `config.yaml` with the example's; when they differ, it lists missing keys (defaults used) and unknown keys (ignored) and asks
        - `m`: new example, your values kept, including your `template_fields` and `keep_from_old` blocks; fields the example added inside them are listed for you to copy
        - `r`: fresh copy of the example, your values are lost
        - `k`: keep `config.yaml` as it is; asked again on the next run
    - before `m` or `r`, the old file is saved as `config.yaml.bak` (gitignored)
    - without a terminal, or with `--dry-run`, nothing is written
- Paths (`input`, `output`)
    - what you type decides absolute vs. relative; `relative_to` only matters for relative paths

    | You write | `relative_to` | Resolves to |
    |---|---|---|
    | `input: C:/Users/me/blog` | ignored | exactly that folder |
    | `input: example/input` | `tool` (default) | `markdown_frontmatter_migrator/example/input`, from any folder you run it in |
    | `input: posts` | `cwd` | `<folder you run the command in>/posts` |

    - absolute on macOS / Linux: `input: /home/me/blog`
    - Windows: use `/`, or put a path with `\` in single quotes

------------------------------------------------------------------------------------------

## Settings

- Read in this order; later sources override earlier ones
    1. defaults in `main.py`
    2. `config.yaml` (offered on the first real run; until then `config.example.yaml`)
    3. command-line flags
- No `.env`: this tool needs no secrets, so every setting, including your folders and your schema, goes in `config.yaml` (gitignored). Should it ever need a secret, add `.env` the way the template does.

| Setting | `config.yaml` | Flag |
|---|---|---|
| Folder with the Markdown files | `input` | `--input` |
| Folder for the migrated copies | `output` | `--output` |
| Files to migrate (subfolders included) | `pattern` (`"*.md"`) | `--pattern` |
| New front matter, in order, with defaults | `template_fields` | — |
| Fields carried over (new: old) | `keep_from_old` | — |
| Fields turned into lists / their separator | `list_fields`, `list_separator` | — |
| Fields set to today | `today_fields` | — |
| Base for relative paths | `relative_to` (`tool` / `cwd`) | `--relative-to` |
| List only | `dry_run` | `--dry-run` / `--no-dry-run` |

------------------------------------------------------------------------------------------

## Setup Python Environment

### Prerequisites
- **Python 3.10+**: [Install Python](https://www.python.org/downloads/) (includes `pip`).

### Steps

```bash
# 1. Go to the tool's folder
cd python-toolbox/markdown_frontmatter_migrator

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
