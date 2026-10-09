# -----------------------------------------------------------------------------------------
#   author          : Kutay Coskuner
#   ai-contributors : unknown (before 2026-10-04), Claude Opus 5.5 (claude-opus-5-5)
#   last update     : 2026-10-06
#   template        : 3.2.0
#   disclaimer      : Provided as is, without warranty of any kind; use at your own risk.
#                     Check outputs before relying on them.
# -----------------------------------------------------------------------------------------
"""
Markdown front matter migrator: rewrites the --- front matter of every Markdown file in a
folder (subfolders included) to a new template, carrying selected old values over.

How a file's new front matter is built (merge_metadata):
    - every field of `template_fields`, in that order, starting from its default
    - fields listed in `keep_from_old` (new key: old key) take the old file's value when
      it has that key, e.g. created <- date, visibility <- isVisible
    - `list_fields` (tags) become lists: "a; b" is split on `list_separator`, items trimmed
    - `today_fields` (updated) are set to today's date
    - old keys not mentioned anywhere are dropped; the body after the front matter is kept

1. Bare run prints this guide and exits (no-args-usage-guide).
2. The first real run offers to create config.yaml from config.example.yaml
   (ensure_config); later runs compare its keys with config.example.yaml's and offer
   to update it when they differ (update_config).
3. Settings come from CLI flags > config.yaml > DEFAULTS (load_settings).
4. Every file matching the pattern under the input folder is migrated and written to the
   same relative path under the output folder (migrate_file); a dry run writes nothing.

Requires: this folder's .venv (pip install -r requirements.txt). config.yaml is
gitignored: your folders and your front matter template go there. No .env: the tool
needs no secrets.

Inputs -> outputs: *.md files under the input folder -> migrated copies under the output
folder (existing files overwritten, inputs never changed). As shipped,
config.example.yaml migrates example/input/ into example/output/.

Run:
    python main.py --run                         migrate the example into example/output/
    python main.py --run --dry-run               list what would be written, write nothing
    python main.py --input D:/blog/posts --output D:/blog/posts_v1.6
    python main.py --help                        all flags; see README.md

Gotchas (known limitations, kept as they were):
    - all quote characters are removed from the written YAML, so "Don't panic: x" becomes
      `title: Dont panic: x`: the apostrophe is lost and a ": " in a value breaks the YAML.
    - a file without front matter gets the full template with defaults on top of its text.
"""

# -----------------------------------------------------------------------------------------
#                libraries
# -----------------------------------------------------------------------------------------
import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

import yaml

# -----------------------------------------------------------------------------------------
#                variables
# -----------------------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
DEFAULTS = {
    "input": "example/input",
    "output": "example/output",
    "pattern": "*.md",
    # the new front matter, in this order, with the default of each field
    "template_fields": {
        "template": "1.6", "revision": "1.3", "title": "", "description": "",
        "category": ["repository"], "tags": [], "created": "2023-03-01",
        "updated": "2023-03-01", "author": "lichzelg", "translator": None, "editor": None,
        "image": "first-blog-post.jpg", "image_credit": None, "language": "en",
        "visibility": True, "sort_order": 1,
    },
    # new field: old field whose value is carried over when the old file has it
    "keep_from_old": {
        "revision": "version", "title": "title", "description": "description",
        "tags": "tags", "created": "date", "language": "language",
        "visibility": "isVisible",
    },
    "list_fields": ["tags"],
    "list_separator": ";",
    "today_fields": ["updated"],
    "relative_to": "tool",
    "dry_run": False,
}
RELATIVE_TO = ("tool", "cwd")

# -----------------------------------------------------------------------------------------
#                functions
# -----------------------------------------------------------------------------------------
def parse_args(argv: list[str]) -> argparse.Namespace:
    """Defines the CLI; flags default to None so unset ones don't override config."""
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--run", action="store_true", help="run with config defaults")
    parser.add_argument("--input",
                        help="folder with the Markdown files (default: example/input/)")
    parser.add_argument("--output",
                        help="folder for the migrated files (default: example/output/)")
    parser.add_argument("--pattern",
                        help='files to migrate, subfolders included (default: "*.md")')
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


class NoQuotesDumper(yaml.Dumper):
    """Custom YAML Dumper to remove quotes and manage spacing"""

    def increase_indent(self, flow=False, indentless=False):
        return super(NoQuotesDumper, self).increase_indent(flow, indentless)


def extract_metadata(content: str) -> tuple[dict, str]:
    """Splits a file into (front matter as a dict, body); no front matter gives {}."""
    yaml_pattern = re.compile(r"---\n(.*?)\n---", re.DOTALL)
    match = yaml_pattern.match(content)
    if match:
        old_metadata = yaml.safe_load(match.group(1)) or {}
        body = content[match.end():].lstrip()
        return old_metadata, body
    return {}, content


def to_list(value, separator: str):
    """A "a; b" string or a list as trimmed, non-empty items; anything else unchanged."""
    if isinstance(value, str):
        return [item.strip() for item in value.split(separator) if item.strip()]
    if isinstance(value, list):
        return [item.strip() for item in value if item.strip()]
    return value


def merge_metadata(old_metadata: dict, settings: dict) -> dict:
    """Builds the new front matter; the rules are listed in the module docstring."""
    new_metadata = {}
    for key, default in settings["template_fields"].items():
        old_key = settings["keep_from_old"].get(key)
        value = old_metadata.get(old_key, default) if old_key else default
        if key in settings["list_fields"]:
            value = to_list(value, settings["list_separator"])
        if key in settings["today_fields"]:
            value = datetime.now().strftime("%Y-%m-%d").strip()
        new_metadata[key] = value
    return new_metadata


def dump_metadata_to_yaml(new_metadata: dict) -> str:
    """Convert new metadata to YAML format without quotes"""
    new_metadata_yaml = yaml.dump(
        new_metadata,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
        width=float('inf'),
        Dumper=NoQuotesDumper
    )

    # Remove any remaining quotes around strings
    return new_metadata_yaml.replace('"', '').replace("'", "")


def migrate_file(source: Path, target: Path, settings: dict) -> None:
    """Migrates one file's front matter and writes it to target, creating folders."""
    print(f"Processing file: {source}")
    with open(source, "r", encoding="utf-8") as file:
        content = file.read()
    old_metadata, body = extract_metadata(content)
    new_metadata_yaml = dump_metadata_to_yaml(merge_metadata(old_metadata, settings))
    print(f"Writing updated file to: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as file:
        file.write(f"---\n{new_metadata_yaml}---\n\n{body}")

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
    source_dir, output_dir = settings["input"], settings["output"]
    if not source_dir.is_dir():
        print(f"Input directory does not exist: {source_dir}")
        return 1
    # 4. Migrate
    print("Starting metadata update process.")
    files = sorted(p for p in source_dir.rglob(settings["pattern"]) if p.is_file())
    for source in files:
        target = output_dir / source.relative_to(source_dir)
        if settings["dry_run"]:
            print(f"Would write: {target}")
        else:
            migrate_file(source, target, settings)
    print("Dry run: nothing written." if settings["dry_run"]
          else f"Metadata update process completed ({len(files)} files).")
    return 0


# -----------------------------------------------------------------------------------------
#                start
# -----------------------------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
