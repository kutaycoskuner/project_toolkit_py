<h1 align="center">
    Text Recognizer (PDF)
</h1>

<p align="center">
    Turns PDFs into Markdown text files: each page is read from its text layer, and pages that are only an image (scans) are read with OCR (Tesseract).
</p>

<p align="center">
    <img alt="Template" src="https://img.shields.io/badge/template-3.1.1-blue" />
    <img alt="Last Update" src="https://img.shields.io/github/last-commit/kutaycoskuner/project_toolkit_py?path=text_recognition_pdf" />
</p>

------------------------------------------------------------------------------------------

## Folders

```bash
text_recognition_pdf/
├── .venv/              # Virtual environment (gitignored)
├── example/
│   ├── input/          # laser_cutter_manual.pdf (text layer) and laser_cutter_manual_scan.pdf (scanned page) (committed)
│   └── output/         # One .md per PDF from the example run (gitignored)
├── config.yaml         # Your settings and paths, e.g. tesseract_cmd (gitignored, offered on the first run)
├── config.example.yaml # Defaults: reads the example PDFs (committed)
├── main.py             # Entry point; its header docstring explains the steps
├── README.md
└── requirements.txt    # Pinned dependencies
```

------------------------------------------------------------------------------------------

## Usage

```bash
python main.py                                   # Usage guide only, does nothing
python main.py --run                             # Read the example PDFs into example/output/
python main.py --run --dry-run                   # List pages and which need OCR, write nothing
python main.py --input D:/scans/report.pdf --output D:/scans/text
python main.py --run --ocr always --ocr-zoom 3   # OCR every page at 216 dpi
python main.py --help                            # All flags
```

- Per page
    - the text layer is read with pypdf
    - with `ocr: auto`, a page without a text layer is rendered to an image (PyMuPDF, at `ocr_zoom` × 72 dpi) and read with Tesseract in `ocr_language`
    - `ocr: always` OCRs every page (for PDFs whose text layer is garbled); `ocr: never` uses text layers only
    - text pages are joined as they come; each OCR'd page is followed by a blank line
- Output
    - one `<name>.md` per PDF in `output`, overwritten on every run; the PDFs are never changed
    - text from a text layer keeps the PDF's own line breaks and spacing
- OCR quality
    - depends on resolution: `ocr_zoom: 1` (72 dpi) misreads small print ("Out Faculty", "laser cuter" in the example), `2`–`3` reads it correctly but takes longer
- Tesseract
    - needed only for pages without a text layer
    - Windows: install it from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki); if it isn't on PATH, set `tesseract_cmd` in `config.yaml` to its `tesseract.exe`
    - other languages: install their language data and set e.g. `ocr_language: eng+tur`
    - if a page needs OCR and Tesseract isn't found, the run says which pages are missing from the output
- First run
    - `config.yaml` doesn't exist in a fresh checkout (it's gitignored); the first real run asks whether to create it from `config.example.yaml`
    - on `n`, without a terminal, or with `--dry-run`, nothing is created and `config.example.yaml` is used for that run
- Example data
    - `laser_cutter_manual.pdf`: 3 pages, all with a text layer: no OCR needed
    - `laser_cutter_manual_scan.pdf`: the first page as a scanned image: read with OCR
    - to read your own PDFs, point `input` / `output` in `config.yaml` (or flags) elsewhere
- After an update (e.g. a `git pull` that changes `config.example.yaml`)
    - the next run notices the example is newer than your `config.yaml` and asks
        - `m`: new example, your values kept (new keys and comments come from the example; keys it dropped are listed)
        - `r`: fresh copy of the example, your values are lost
        - `k`: keep `config.yaml` as it is; asked again only after the next example change
    - before `m` or `r`, the old file is saved as `config.yaml.bak` (gitignored)
    - without a terminal, or with `--dry-run`, nothing is written
    - every run also warns when `config.yaml` lacks keys the example has (they use defaults) or has keys the tool doesn't read
- Paths (`input`, `output`, `tesseract_cmd`)
    - what you type decides absolute vs. relative; `relative_to` only matters for relative paths

    | You write | `relative_to` | Resolves to |
    |---|---|---|
    | `input: C:/Users/me/scans` | ignored | exactly that folder |
    | `input: example/input` | `tool` (default) | `text_recognition_pdf/example/input`, from any folder you run it in |
    | `input: scans/report.pdf` | `cwd` | `<folder you run the command in>/scans/report.pdf` |

    - absolute on macOS / Linux: `input: /home/me/scans`
    - Windows: use `/`, or put a path with `\` in single quotes
    - `tesseract_cmd` is used as written (an absolute path is safest)

------------------------------------------------------------------------------------------

## Settings

- Read in this order; later sources override earlier ones
    1. defaults in `main.py`
    2. `config.yaml` (offered on the first real run; until then `config.example.yaml`)
    3. command-line flags
- No `.env`: this tool needs no secrets, so every setting, including your paths, goes in `config.yaml` (gitignored). Should it ever need a secret, add `.env` the way the template does.

| Setting | `config.yaml` | Flag |
|---|---|---|
| A PDF or a folder of PDFs | `input` | `--input` |
| Folder for the .md files | `output` | `--output` |
| PDFs to read in a folder | `pattern` (`"*.pdf"`) | — |
| When to OCR | `ocr` (`auto` / `always` / `never`) | `--ocr` |
| OCR language(s) | `ocr_language` (`eng`) | `--ocr-language` |
| OCR resolution | `ocr_zoom` (`1` in code, `2` in the example) | `--ocr-zoom` |
| Tesseract program | `tesseract_cmd` (`""` = from PATH) | — |
| Base for relative paths | `relative_to` (`tool` / `cwd`) | `--relative-to` |
| List only | `dry_run` | `--dry-run` / `--no-dry-run` |

------------------------------------------------------------------------------------------

## Setup Python Environment

### Prerequisites
- **Python 3.10+**: [Install Python](https://www.python.org/downloads/) (includes `pip`).
- **Tesseract OCR** (only for scanned pages): [Install Tesseract](https://github.com/UB-Mannheim/tesseract/wiki).

### Steps

```bash
# 1. Go to the tool's folder
cd project_toolkit_py/text_recognition_pdf

# 2. Create a virtual environment
python -m venv .venv

# 3. Activate it
#   Windows:
.venv\Scripts\activate
#   macOS / Linux:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run it (config.yaml is offered on the first run; set tesseract_cmd there if needed)
python main.py --run

# 6. Deactivate the environment when done (optional)
deactivate
```
