<h1 align="center">
    Code Snippet Renderer
</h1>

<p align="center">
    Renders code snippets, written as coloured text pieces in a JSON file, as images (1920×1080 by default), with an optional rounded code-block frame and title: for slides, posts and docs.
</p>

<p align="center">
    <img alt="Template" src="https://img.shields.io/badge/template-3.1.1-blue" />
    <img alt="Last Update" src="https://img.shields.io/github/last-commit/kutaycoskuner/python-toolbox?path=code_snippet_renderer" />
</p>

------------------------------------------------------------------------------------------

## Folders

```bash
code_snippet_renderer/
├── .venv/              # Virtual environment (gitignored)
├── example/
│   ├── input/          # Snippets: symlink_powershell.json, class_person.json (both framed), hello_world.json (committed)
│   └── output/         # One .png per snippet from the example run (gitignored)
├── config.yaml         # Your settings and paths (gitignored, offered on the first run)
├── config.example.yaml # Defaults: image size, colours, font, frame; renders the examples (committed)
├── main.py             # Entry point; its header docstring explains the format and steps
├── README.md
└── requirements.txt    # Pinned dependencies
```

------------------------------------------------------------------------------------------

## Usage

```bash
python main.py                                   # Usage guide only, does nothing
python main.py --run                             # Render example/input/*.json into example/output/
python main.py --run --dry-run                   # List what would be rendered, write nothing
python main.py --input D:/posts/snippet.json --output D:/posts/images   # one file -> rendered.png
python main.py --run --width 1080 --height 1080  # Square images
python main.py --help                            # All flags
```

- The snippet format (JSON)
    ```json
    {
        "title": {"text": "windows powershell", "color": "#666666"},
        "0": [["# ", "#BBBBBB"], ["Create a symlink to a file", "#FFFFFF"]],
        "1": [["New-Item ", "#00FF00"], ["-Path ", "#00CCFF"], ["\"C:\\linked\\file.txt\"", "#FFFF33"]],
        "2": [["", "#FFFFFF"]]
    }
    ```
    - each row (`"0"`, `"1"`, …) is a list of `[text, colour]` pieces, drawn left to right; an empty piece makes an empty row
    - `title` is optional: with it, the rows get a rounded frame with the title in its top-left corner
    - colours are hex (`#RRGGBB`); spaces inside the text are kept, so indent code with spaces
- Layout
    - the font size is fitted so the longest row fills the width inside the side margins (`h_margin`); one long row makes all text smaller, so split long lines into two rows
    - the rows are centred vertically between the top and bottom margins (`v_margin`)
    - a monospace font (`Courier New` by default) keeps columns aligned; the font is looked up with matplotlib, which falls back to its default font when it isn't installed
- Output
    - a folder of snippets: one `<name>.png` per JSON file in `output`
    - a single snippet: `<output>/rendered.png` (`output_name`)
    - existing images are overwritten; a file that can't be rendered is reported by name and skipped
- First run
    - `config.yaml` doesn't exist in a fresh checkout (it's gitignored); the first real run asks whether to create it from `config.example.yaml`
    - on `n`, without a terminal, or with `--dry-run`, nothing is created and `config.example.yaml` is used for that run
- Example data
    - `symlink_powershell.json`: two PowerShell commands with comments, framed with a title
    - `class_person.json`: a Python class, framed with a title
    - `hello_world.json`: a short Python function, no frame
    - to render your own snippets, point `input` / `output` in `config.yaml` (or flags) elsewhere
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
    | `input: C:/Users/me/snippets` | ignored | exactly that folder |
    | `input: example/input` | `tool` (default) | `code_snippet_renderer/example/input`, from any folder you run it in |
    | `input: snippet.json` | `cwd` | `<folder you run the command in>/snippet.json` |

    - absolute on macOS / Linux: `input: /home/me/snippets`
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
| A snippet file or a folder of them | `input` | `--input` |
| Folder for the images | `output` | `--output` |
| Snippets to render in a folder | `pattern` (`"*.json"`) | — |
| Image name for a single snippet | `output_name` (`rendered.png`) | — |
| Image size | `width`, `height` (`1920`, `1080`) | `--width`, `--height` |
| Background colour | `bg_color` (`"#101010"`) | — |
| Font and line height | `font` (`Courier New`), `line_spacing` (`1.2`) | — |
| Margins (share of height / width) | `v_margin`, `h_margin` (`0.05`) | — |
| Frame | `frame_color`, `frame_width`, `frame_radius` | — |
| Base for relative paths | `relative_to` (`tool` / `cwd`) | `--relative-to` |
| List only | `dry_run` | `--dry-run` / `--no-dry-run` |

------------------------------------------------------------------------------------------

## Setup Python Environment

### Prerequisites
- **Python 3.10+**: [Install Python](https://www.python.org/downloads/) (includes `pip`).

### Steps

```bash
# 1. Go to the tool's folder
cd python-toolbox/code_snippet_renderer

# 2. Create a virtual environment
python -m venv .venv

# 3. Activate it
#   Windows:
.venv\Scripts\activate
#   macOS / Linux:
source .venv/bin/activate

# 4. Install dependencies (Pillow, matplotlib for the font lookup, PyYAML)
pip install -r requirements.txt

# 5. Run it (config.yaml is offered on the first run)
python main.py --run

# 6. Deactivate the environment when done (optional)
deactivate
```
