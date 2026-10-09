# -----------------------------------------------------------------------------------------
#   author          : Kutay Coskuner
#   ai-contributors : unknown (before 2026-10-05), Claude Opus 5.5 (claude-opus-5-5)
#   last update     : 2026-10-06
#   template        : 3.2.0
#   disclaimer      : Provided as is, without warranty of any kind; use at your own risk.
#                     Check outputs before relying on them.
# -----------------------------------------------------------------------------------------
"""
PDF text recognition: turns PDFs into Markdown text files, reading each page's text
layer and falling back to OCR (Tesseract) for pages that are only an image (scans).

Per page (extract_pdf):
    - the page's text layer is read with pypdf
    - with `ocr: auto`, a page without text is rendered to an image (PyMuPDF, at
      `ocr_zoom` x 72 dpi) and read with Tesseract in `ocr_language`; `always` OCRs
      every page, `never` no page
    - text pages are joined as they come; each OCR'd page is followed by a blank line

1. Bare run prints this guide and exits (no-args-usage-guide).
2. The first real run offers to create config.yaml from config.example.yaml
   (ensure_config); later runs compare its keys with config.example.yaml's and offer
   to update it when they differ (update_config).
3. Settings come from CLI flags > config.yaml > DEFAULTS (load_settings).
4. Every PDF (a single file, or the files matching `pattern` in a folder) is read page
   by page (extract_pdf) and written as <name>.md to the output folder; a dry run only
   reports which pages would need OCR.

Requires: this folder's .venv (pip install -r requirements.txt); for OCR, Tesseract
(https://github.com/UB-Mannheim/tesseract/wiki) on PATH or at `tesseract_cmd` in
config.yaml, with the language data for `ocr_language`. config.yaml is gitignored: your
paths go there. No .env: the tool needs no secrets.

Inputs -> outputs: PDFs -> <output>/<name>.md (overwritten; the PDFs are never changed).
As shipped, config.example.yaml reads example/input/: a text PDF and a scanned one.

Run:
    python main.py --run                         read the example PDFs into example/output/
    python main.py --run --dry-run               list pages needing OCR, write nothing
    python main.py --input D:/scans/report.pdf --output D:/scans/text
    python main.py --run --ocr always --ocr-zoom 3   every page by OCR, 216 dpi
    python main.py --help                        all flags; see README.md

Gotchas:
    - OCR quality depends on resolution: zoom 1 (72 dpi) misreads small print, 2-3 is
      better but slower.
    - text from the text layer keeps the PDF's own line breaks and spacing.
"""

# -----------------------------------------------------------------------------------------
#                libraries
# -----------------------------------------------------------------------------------------
import argparse
import io
import json
import re
import shutil
import sys
from pathlib import Path

import fitz  # PyMuPDF: renders pages for OCR
import pytesseract
import yaml
from PIL import Image
from pypdf import PdfReader

# -----------------------------------------------------------------------------------------
#                variables
# -----------------------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
DEFAULTS = {
    "input": "example/input",
    "output": "example/output",
    "pattern": "*.pdf",
    "ocr": "auto",
    "ocr_language": "eng",
    "ocr_zoom": 1,
    "tesseract_cmd": "",
    "relative_to": "tool",
    "dry_run": False,
}
OCR_MODES = ("auto", "always", "never")
RELATIVE_TO = ("tool", "cwd")

# -----------------------------------------------------------------------------------------
#                functions
# -----------------------------------------------------------------------------------------
def parse_args(argv: list[str]) -> argparse.Namespace:
    """Defines the CLI; flags default to None so unset ones don't override config."""
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--run", action="store_true", help="run with config defaults")
    parser.add_argument("--input",
                        help="a PDF, or a folder of PDFs (default: example/input/)")
    parser.add_argument("--output",
                        help="folder for the .md files (default: example/output/)")
    parser.add_argument("--ocr", choices=OCR_MODES,
                        help="when to OCR a page (default: auto)")
    parser.add_argument("--ocr-language",
                        help='Tesseract language(s), e.g. "eng" or "eng+tur"')
    parser.add_argument("--ocr-zoom", type=float, help="render scale for OCR, 1 = 72 dpi")
    parser.add_argument("--relative-to", choices=RELATIVE_TO,
                        help="base for relative paths: this tool's folder or the cwd")
    parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=None,
                        help="list pages and which need OCR, write nothing")
    return parser.parse_args(argv)


def ensure_config(dry_run: bool) -> Path | None:
    """
    Returns the config file to read, offering to create config.yaml on the first run.

    config.yaml is personal and gitignored, so a fresh checkout only has the committed
    config.example.yaml. A real run asks before copying it (inform-and-confirm-each-step);
    on "no", without a terminal, or in a dry run, nothing is written and the example is
    read for this run only.

    Returns:
        config.yaml, config.example.yaml (until config.yaml exists), or None when
        neither exists.
    """
    config, example = HERE / "config.yaml", HERE / "config.example.yaml"
    if config.exists():
        if example.exists():
            update_config(config, example, dry_run)
        return config
    if not example.exists():
        return None
    if not dry_run:
        try:
            answer = input("config.yaml not found. "
                           "Create it from config.example.yaml? (y/n): ")
        except EOFError:
            answer = ""
            print()
        if answer.strip().lower() == "y":
            shutil.copyfile(example, config)  # byte-identical, so it diffs cleanly later
            print(f"Created {config.name}; edit it to use your own data.")
            return config
    print("Using config.example.yaml for this run; config.yaml was not created.")
    return example


def merge_config_text(example_text: str, old: dict) -> tuple[str, list[str]]:
    """
    Puts the values of an old config into the text of a new example.

    Only top-level keys are touched, so comments, order and new keys come from the
    example. A `key: value` line gets the old value as JSON (valid YAML), unless it equals
    the example's; a key followed by an indented block (a nested mapping or list) gets
    the old value as a YAML block.

    Returns:
        (merged text, old keys the example no longer has).
    """
    # key : spacing : value (a quoted value may contain #) : optional comment : line ending
    line_re = re.compile(r"^([A-Za-z_][\w-]*):([ \t]*)"
                         r"(\"(?:[^\"\\r\n]|\.)*\"|'(?:[^'\r\n]|'')*'|[^#\r\n]*?)"
                         r"([ \t]*#[^\r\n]*)?(\r?\n)?$")
    lines = example_text.splitlines(keepends=True)
    merged, used, i = [], set(), 0
    while i < len(lines):
        line, i = lines[i], i + 1
        match = line_re.match(line)
        if not match or match.group(1) not in old:
            merged.append(line)
            continue
        key, space, value, comment, newline = match.groups()
        used.add(key)
        if value.strip():
            if yaml.safe_load(value) == old[key]:
                merged.append(line)  # unchanged: keep the example's text and spacing
                continue
            new_value = json.dumps(old[key], ensure_ascii=False).ljust(len(value))
            merged.append(f"{key}:{space}{new_value}{comment or ''}{newline or ''}")
            continue
        while i < len(lines) and lines[i].startswith((" ", "\t", "- ")):
            i += 1  # skip the example's block; the old value replaces it
        block = yaml.safe_dump({key: old[key]}, sort_keys=False, allow_unicode=True,
                               default_flow_style=False).splitlines()
        nl = newline or "\n"
        merged.append(f"{block[0]}{comment or ''}{nl}")
        merged.extend(f"{b}{nl}" for b in block[1:])
    return "".join(merged), [key for key in old if key not in used]


def update_config(config: Path, example: Path, dry_run: bool) -> None:
    """
    Offers to update config.yaml when its settings differ from config.example.yaml's.

    Compares top-level keys only: the values are the user's own, and a nested block may
    hold the user's own entries. A key only the example has falls back to DEFAULTS, a key
    only config.yaml has is ignored; comment-only changes to the example don't count.
    Asked on every run until the keys match. Before overwriting, the old config.yaml is
    saved as config.yaml.bak (gitignored). Without a terminal or in a dry run, nothing is
    written (inform-and-confirm-each-step).
    """
    old = yaml.safe_load(config.read_text(encoding="utf-8")) or {}
    with open(example, encoding="utf-8", newline="") as f:
        example_text = f.read()
    new = yaml.safe_load(example_text) or {}
    missing = [key for key in new if key not in old]
    unknown = [key for key in old if key not in new]
    if not missing and not unknown:
        return
    print("config.yaml differs from config.example.yaml:")
    if missing:
        print(f"  missing (defaults used): {', '.join(missing)}")
    if unknown:
        print(f"  not read by this tool (ignored): {', '.join(unknown)}")
    if dry_run:
        print("Dry run: config.yaml left as it is.")
        return
    try:
        answer = input("  m = update: new example, keep your values (recommended)\n"
                       "  r = replace: fresh copy of the example, your values are lost\n"
                       "  k = keep config.yaml as it is (asked again on the next run)\n"
                       "Choice (m/r/k): ").strip().lower()
    except EOFError:
        print("\nNo terminal to ask on: config.yaml left as it is.")
        return
    backup = config.with_name("config.yaml.bak")
    if answer == "m":
        merged, dropped = merge_config_text(example_text, old)
        shutil.copyfile(config, backup)
        with open(config, "w", encoding="utf-8", newline="") as f:
            f.write(merged)
        print(f"Updated config.yaml, your values kept (old one: {backup.name}).")
        if dropped:
            print(f"No longer in the example, dropped: {', '.join(dropped)}.")
        for key, value in new.items():
            if isinstance(value, dict) and isinstance(old.get(key), dict):
                added = [k for k in value if k not in old[key]]
                if added:
                    print(f"New in the example, not added to your {key}: "
                          f"{', '.join(added)} (copy them from config.example.yaml).")
    elif answer == "r":
        shutil.copyfile(config, backup)
        shutil.copyfile(example, config)
        print(f"Replaced config.yaml with the example (old one: {backup.name}).")
    else:
        print("Kept config.yaml; you'll be asked again on the next run.")


def load_settings(args: argparse.Namespace) -> dict:
    """
    Merges settings: CLI flags > config.yaml > DEFAULTS.

    Paths: an absolute "input"/"output" is used as-is; a relative one is resolved
    against this tool's folder (relative_to: tool) or the current working directory
    (relative_to: cwd).

    Returns:
        Settings with "input"/"output" as absolute Paths.

    Raises:
        SystemExit: relative_to or ocr has an invalid value.
    """
    settings = dict(DEFAULTS)
    config_file = ensure_config(bool(args.dry_run))
    if config_file:
        loaded = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
        settings.update(loaded)
    settings.update({k: v for k, v in vars(args).items() if v is not None and k != "run"})
    if settings["relative_to"] not in RELATIVE_TO:
        raise SystemExit(f"Invalid relative_to {settings['relative_to']!r} "
                         "in config.yaml: choose 'tool' or 'cwd'.")
    if settings["ocr"] not in OCR_MODES:
        raise SystemExit(f"Invalid ocr {settings['ocr']!r} in config.yaml: "
                         "choose 'auto', 'always' or 'never'.")
    base = HERE if settings["relative_to"] == "tool" else Path.cwd()
    for key in ("input", "output"):
        path = Path(settings[key])
        settings[key] = path if path.is_absolute() else base / path
    return settings


def tesseract_ready(settings: dict) -> bool:
    """Points pytesseract at tesseract_cmd (if set) and checks Tesseract runs."""
    if settings["tesseract_cmd"]:
        pytesseract.pytesseract.tesseract_cmd = settings["tesseract_cmd"]
    try:
        pytesseract.get_tesseract_version()
        return True
    except (pytesseract.TesseractNotFoundError, OSError):
        return False


def ocr_page(document, page_number: int, settings: dict) -> str:
    """
    Renders one page and reads it with Tesseract.

    The page goes through a JPEG step, as in the original tool, which saved pages as JPG
    files before OCR; keeping it keeps the OCR results the same.
    """
    zoom = settings["ocr_zoom"]
    pix = document.load_page(page_number).get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    buffer = io.BytesIO()
    img.save(buffer, "JPEG")
    buffer.seek(0)
    return pytesseract.image_to_string(Image.open(buffer), lang=settings["ocr_language"])


def needs_ocr(page_text: str | None, mode: str) -> bool:
    """Whether a page is OCR'd: always / never, or (auto) when it has no text layer."""
    return mode == "always" or (mode == "auto" and not page_text)


def extract_pdf(pdf_path: Path, settings: dict, ocr_available: bool) -> tuple[str, list]:
    """
    Reads every page: its text layer, or OCR where needs_ocr() says so.

    Returns:
        (the document's text, page numbers that needed OCR but couldn't get it).
    """
    reader = PdfReader(pdf_path)
    document = fitz.open(pdf_path)
    text, skipped = "", []
    for number, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if not needs_ocr(page_text, settings["ocr"]):
            text += page_text or ""
        elif ocr_available:
            text += ocr_page(document, number, settings) + "\n\n"
            print(f"  page {number + 1}: read with OCR")
        else:
            skipped.append(number + 1)
    return text, skipped


def find_pdfs(source: Path, pattern: str) -> list[Path]:
    """The input PDF, or the PDFs matching pattern in the input folder (sorted)."""
    if source.is_file():
        return [source]
    return sorted(p for p in source.glob(pattern) if p.is_file())

# -----------------------------------------------------------------------------------------
#                main
# -----------------------------------------------------------------------------------------
def main(argv: list[str]) -> int:
    # 1. No arguments: usage guide only, never work
    if not argv:
        print(__doc__.strip())
        return 0
    # 2.-3. Settings (config.yaml offered on the first real run)
    settings = load_settings(parse_args(argv))
    if not settings["input"].exists():
        print(f"File or folder {settings['input']} does not exist.")
        return 1
    pdfs = find_pdfs(settings["input"], settings["pattern"])
    if not pdfs:
        print(f"No PDFs matching {settings['pattern']!r} in {settings['input']}.")
        return 0
    ocr_available = settings["ocr"] != "never" and tesseract_ready(settings)
    # 4. Read every PDF
    for pdf in pdfs:
        if not pdf.suffix.lower() == ".pdf":
            print(f"File {pdf} is not a PDF.")
            continue
        reader = PdfReader(pdf)
        ocr_pages = [n + 1 for n, page in enumerate(reader.pages)
                     if needs_ocr(page.extract_text(), settings["ocr"])]
        count = len(reader.pages)
        pages = f"OCR for page(s) {ocr_pages}" if ocr_pages else "all with a text layer"
        print(f"{pdf.name}: {count} page{'' if count == 1 else 's'}, {pages}")
        if settings["dry_run"]:
            continue
        text, skipped = extract_pdf(pdf, settings, ocr_available)
        if skipped:
            print(f"  page(s) {skipped} have no text layer and Tesseract wasn't found: "
                  "they are missing. Install it or set tesseract_cmd in config.yaml.")
        target = settings["output"] / f"{pdf.stem}.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as file:
            file.write(text)
        print(f"Text extracted and saved to {target}")
    if settings["dry_run"]:
        print("Dry run: nothing written.")
    return 0


# -----------------------------------------------------------------------------------------
#                start
# -----------------------------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
