<h1 align="center">
    Image Resizer
</h1>

<p align="center">
    Resizes every image in a folder to one fixed size (default 1024×1024), e.g. to shrink large texture sets for game development or 3D projects. The originals are never changed.
</p>

<p align="center">
    <img alt="Template" src="https://img.shields.io/badge/template-3.1.1-blue" />
    <img alt="Last Update" src="https://img.shields.io/github/last-commit/kutaycoskuner/project_toolkit_py?path=image_resizer" />
</p>

------------------------------------------------------------------------------------------

## Folders

```bash
image_resizer/
├── .venv/              # Virtual environment (gitignored)
├── example/
│   ├── input/          # Sample images: 4096² png, 2048×1024 jpg, 128² tga, and a txt that is skipped (committed)
│   └── output/         # Resized copies from the example run (gitignored)
├── config.yaml         # Your settings and folders (gitignored, offered on the first run)
├── config.example.yaml # Defaults: resizes the example into example/output/ (committed)
├── main.py             # Entry point; its header docstring explains the steps
├── README.md
└── requirements.txt    # Pinned dependencies
```

------------------------------------------------------------------------------------------

## Usage

```bash
python main.py                                   # Usage guide only, does nothing
python main.py --run                             # Resize example/input/ into example/output/
python main.py --run --dry-run                   # List what would be resized, write nothing
python main.py --run --size 2048x2048            # Another target size
python main.py --input D:/tex_4k --output D:/tex_1k
python main.py --help                            # All flags
```

- Which files
    - only `.png`, `.jpg`, `.jpeg` and `.tga` (case-insensitive; change `extensions` in `config.yaml`); other files are skipped
    - resized copies keep their names; an existing file with the same name in the output folder is overwritten
    - the originals in the input folder are never changed
- Size
    - exact: the aspect ratio is **not** kept, so 2048×1024 becomes 1024×1024 (stretched)
    - smaller images are scaled up to the target size too
    - resampling is LANCZOS
- First run
    - `config.yaml` doesn't exist in a fresh checkout (it's gitignored); the first real run asks whether to create it from `config.example.yaml`
    - on `n`, without a terminal, or with `--dry-run`, nothing is created and `config.example.yaml` is used for that run
- Example data
    - as shipped, the tool resizes the three sample images in `example/input/` into `example/output/`: one shrinks, one is stretched to a square, one grows; the `.txt` is skipped
    - to use your own images, point `input` / `output` in `config.yaml` (or flags) elsewhere
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
    | `input: C:/Users/me/textures` | ignored | exactly that folder |
    | `input: example/input` | `tool` (default) | `image_resizer/example/input`, from any folder you run it in |
    | `input: textures` | `cwd` | `<folder you run the command in>/textures` |

    - absolute on macOS / Linux: `input: /home/me/textures`
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
| Input folder | `input` | `--input` |
| Output folder | `output` | `--output` |
| Target size | `width`, `height` | `--size WxH` |
| File types | `extensions` | — |
| Base for relative paths | `relative_to` (`tool` / `cwd`) | `--relative-to` |
| List only | `dry_run` | `--dry-run` / `--no-dry-run` |

------------------------------------------------------------------------------------------

## Setup Python Environment

### Prerequisites
- **Python 3.10+**: [Install Python](https://www.python.org/downloads/) (includes `pip`).

### Steps

```bash
# 1. Go to the tool's folder
cd project_toolkit_py/image_resizer

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
