# -----------------------------------------------------------------------------------------
#   author          : Kutay Coskuner
#   ai-contributors : unknown (before 2026-10-04), Claude Opus 5.5 (claude-opus-5-5)
#   last update     : 2026-10-06
#   template        : 3.2.0
#   disclaimer      : Provided as is, without warranty of any kind; use at your own risk.
#                     Check outputs before relying on them.
# -----------------------------------------------------------------------------------------
"""
Markdown formatter: cleans up text extracted from PDFs (or messy Markdown essays) into
readable Markdown, keeping front matter and code blocks as they are.

What clean_text() does to a file:
    - joins hard-wrapped lines into paragraphs, keeping blank lines between paragraphs
    - puts a blank line before and after each heading (#, ## ...)
    - keeps the front matter (--- block) and fenced code blocks unchanged
    - turns indented text into a ```plaintext block on one line, with a line break
      before each in-text citation such as "(Smith, 2020)"

1. Bare run prints this guide and exits (no-args-usage-guide).
2. The first real run offers to create config.yaml from config.example.yaml
   (ensure_config); later runs compare its keys with config.example.yaml's and offer
   to update it when they differ (update_config).
3. Settings come from CLI flags > config.yaml > DEFAULTS (load_settings).
4. The input is one file, or a folder whose files matching the pattern are all
   formatted (find_inputs).
5. Each file is cleaned and written to the output folder (format_file); a dry run
   writes nothing.

Requires: this folder's .venv (pip install -r requirements.txt). config.yaml is
gitignored: your input/output paths go there. No .env: the tool needs no secrets.

Inputs -> outputs: a Markdown/text file -> <output>/<output_name> (processed_text.md),
or a folder -> one cleaned file per input under the same name in <output>. Existing
files are overwritten; inputs are never changed. As shipped, config.example.yaml
formats example/input/ into example/output/.

Run:
    python main.py --run                         format the example into example/output/
    python main.py --run --dry-run               list what would be written, write nothing
    python main.py --input D:/notes/essay.md --output D:/notes/clean
    python main.py --help                        all flags; see README.md

Gotchas (known limitations, kept as they were):
    - consecutive list items and table rows are joined like paragraph lines, so lists
      and tables come out on one line; keep them in a code block or fix them afterwards.
    - spaces inside a line are kept; only line ends are trimmed.
    - a plaintext block follows the text before it without a blank line.
"""

# -----------------------------------------------------------------------------------------
#                libraries
# -----------------------------------------------------------------------------------------
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

import yaml

# -----------------------------------------------------------------------------------------
#                variables
# -----------------------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
DEFAULTS = {"input": "example/input", "output": "example/output", "pattern": "*.md",
            "output_name": "processed_text.md", "relative_to": "tool", "dry_run": False}
RELATIVE_TO = ("tool", "cwd")

# -----------------------------------------------------------------------------------------
#                functions
# -----------------------------------------------------------------------------------------
def parse_args(argv: list[str]) -> argparse.Namespace:
    """Defines the CLI; flags default to None so unset ones don't override config."""
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--run", action="store_true", help="run with config defaults")
    parser.add_argument("--input",
                        help="file or folder to format (default: example/input/)")
    parser.add_argument("--output",
                        help="folder for the results (default: example/output/)")
    parser.add_argument("--pattern", help='files to format in a folder (default: "*.md")')
    parser.add_argument("--relative-to", choices=RELATIVE_TO,
                        help="base for relative paths: this tool's folder or the cwd")
    parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=None,
                        help="list what would be written, write nothing")
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
        SystemExit: relative_to is neither "tool" nor "cwd".
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
    base = HERE if settings["relative_to"] == "tool" else Path.cwd()
    for key in ("input", "output"):
        path = Path(settings[key])
        settings[key] = path if path.is_absolute() else base / path
    return settings


def clean_text(text: str) -> str:
    """
    Cleans one document; the rules are listed in the module docstring.

    Two passes: the first joins lines, spaces headings, keeps front matter and code
    blocks, and collects indented text into ```plaintext blocks; the second adds a line
    break before each "(Author, 2020)" citation inside those blocks.
    """
    lines = text.split("\n")
    cleaned_lines = []
    inside_metadata = False
    metadata_found = False
    last_line_was_blank = True
    inside_code_block = False
    indented_text = []

    # First pass: General formatting
    for i, line in enumerate(lines):
        stripped_line = line.rstrip()

        if stripped_line == "---":
            if not metadata_found:
                metadata_found = True
                inside_metadata = True
            elif inside_metadata:
                inside_metadata = False

            if cleaned_lines and cleaned_lines[-1] == "":
                cleaned_lines.pop()

            cleaned_lines.append("---")
            last_line_was_blank = False
            continue

        if inside_metadata:
            cleaned_lines.append(line)
            last_line_was_blank = False
            continue

        if stripped_line.startswith("```"):
            inside_code_block = not inside_code_block
            cleaned_lines.append(stripped_line)
            if not inside_code_block:
                cleaned_lines.append("")  # Ensure one empty line after code block
            continue

        if inside_code_block:
            cleaned_lines.append(line)
            continue

        if stripped_line.startswith("#"):
            if cleaned_lines and cleaned_lines[-1] != "---":
                cleaned_lines.append("")
            if len(cleaned_lines) > 1 and cleaned_lines[-2] != "":
                cleaned_lines.append("")
            cleaned_lines.append(stripped_line)
            cleaned_lines.append("")
            last_line_was_blank = True
            continue

        if line.startswith("    ") or line.startswith("\t"):
            indented_text.append(stripped_line.lstrip())  # Remove leading spaces
            last_line_was_blank = False
            continue
        elif indented_text:
            # Join indented text with spaces and trim leading/trailing spaces
            plaintext_content = " ".join(indented_text).strip()
            cleaned_lines.append("```plaintext")
            cleaned_lines.append(plaintext_content)
            cleaned_lines.append("```")
            cleaned_lines.append("")
            indented_text = []
            last_line_was_blank = True  # Ensure only one blank line is added
            continue

        if stripped_line:
            if cleaned_lines and not last_line_was_blank:
                cleaned_lines[-1] += " " + stripped_line
            else:
                cleaned_lines.append(stripped_line)
            last_line_was_blank = False
        else:
            if not last_line_was_blank:
                cleaned_lines.append("")
            last_line_was_blank = True

    if cleaned_lines[-1] == "---":
        cleaned_lines.append("")

    # Second pass: Handle in-text references within plaintext blocks
    inside_plaintext_block = False
    final_lines = []

    for line in cleaned_lines:
        if line.startswith("```plaintext"):
            inside_plaintext_block = True
            final_lines.append(line)
            continue
        elif line.startswith("```") and inside_plaintext_block:
            inside_plaintext_block = False
            final_lines.append(line)
            continue

        if inside_plaintext_block:
            # Add line breaks before in-text references
            modified_line = re.sub(r"(\s)(\([^)]+, \d{4}\))", r"\n\2", line)
            final_lines.append(modified_line)
        else:
            final_lines.append(line)

    return "\n".join(final_lines).strip()


def find_inputs(settings: dict) -> list[tuple[Path, Path]]:
    """
    Pairs each input file with its output path.

    Returns:
        [(input file, output file)]: a single input file goes to <output>/<output_name>;
        files in an input folder keep their names. Empty when nothing matches.
    """
    source, output = settings["input"], settings["output"]
    if source.is_file():
        return [(source, output / settings["output_name"])]
    return [(path, output / path.name)
            for path in sorted(source.glob(settings["pattern"])) if path.is_file()]


def format_file(source: Path, target: Path) -> None:
    """Cleans source and writes it to target, creating the folder; prints the result."""
    try:
        with open(source, "r", encoding="utf-8") as f:
            text = f.read()
        cleaned_text = clean_text(text)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(cleaned_text)
        print(f"Processed text saved to: {target}")
    except (OSError, UnicodeDecodeError, IndexError) as e:
        print(f"An error occurred with {source.name}: {e}")

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
        print(f"Error: The file or folder '{settings['input']}' was not found.")
        return 1
    # 4. Inputs
    pairs = find_inputs(settings)
    if not pairs:
        print(f"No files matching {settings['pattern']!r} in {settings['input']}.")
        return 0
    # 5. Format
    for source, target in pairs:
        if settings["dry_run"]:
            print(f"Would write: {source.name} -> {target}")
        else:
            format_file(source, target)
    if settings["dry_run"]:
        print("Dry run: nothing written.")
    return 0


# -----------------------------------------------------------------------------------------
#                start
# -----------------------------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
