# -----------------------------------------------------------------------------------------
#   author          : Kutay Coskuner
#   ai-contributors : unknown (before 2026-10-05), Claude Opus 5.5 (claude-opus-5-5)
#   last update     : 2026-10-05
#   template        : 3.1.1
#   disclaimer      : Provided as is, without warranty of any kind; use at your own risk.
#                     Check outputs before relying on them.
# -----------------------------------------------------------------------------------------
"""
Numbered line generator: writes one line per number from `start` to `end` into a text
file, from a line template such as "pushlist spellbook_scrolls {i}".

1. Bare run prints this guide and exits (no-args-usage-guide).
2. The first real run offers to create config.yaml from config.example.yaml
   (ensure_config); later runs offer to update it when config.example.yaml has changed
   since (update_config) and warn when its keys differ from the example's
   (check_config_keys).
3. Settings come from CLI flags > config.yaml > DEFAULTS (load_settings).
4. The line template is filled in for every number from start to end, both included,
   counting by step (build_lines).
5. The lines are written to <output>/<output_file> (write_lines); a dry run only shows
   the first and last line.

Requires: this folder's .venv (pip install -r requirements.txt). config.yaml is
gitignored: your settings go there. No .env: the tool needs no secrets.

Inputs -> outputs: config / flags -> example/output/output.txt by default (overwritten
on every run). The tool reads no input files: config.example.yaml is its example.

Run:
    python main.py --run                         lines 7981..8044 into example/output/
    python main.py --run --dry-run               show first and last line, write nothing
    python main.py --start 1 --end 10 --line "pushlist spellbook_scrolls {i}"
    python main.py --start 0 --end 100 --step 10 --line "wait {i}"
    python main.py --help                        all flags; see README.md

Gotchas:
    - "{i}" in the line template is the number; other braces must be doubled ("{{" or
      "}}"), because the template is a Python format string.
    - the file has no trailing newline after the last line.
"""

# -----------------------------------------------------------------------------------------
#                libraries
# -----------------------------------------------------------------------------------------
import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

import yaml

# -----------------------------------------------------------------------------------------
#                variables
# -----------------------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
DEFAULTS = {
    "start": 7981,
    "end": 8044,
    "step": 1,
    "line": "pushlist spellbook_scrolls {i}",
    "output": "example/output",
    "output_file": "output.txt",
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
    parser.add_argument("--start", type=int, help="first number (included)")
    parser.add_argument("--end", type=int, help="last number (included)")
    parser.add_argument("--step", type=int, help="count by this much (default: 1)")
    parser.add_argument("--line", help='line template, "{i}" is the number')
    parser.add_argument("--output", help="output folder (default: example/output/)")
    parser.add_argument("--relative-to", choices=RELATIVE_TO,
                        help="base for relative paths: this tool's folder or the cwd")
    parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=None,
                        help="show the first and last line, write nothing")
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
    # key : spacing : value : optional comment : line ending
    line_re = re.compile(r"^([A-Za-z_][\w-]*):([ \t]*)([^#\r\n]*?)"
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
    Offers to update config.yaml when config.example.yaml changed after it was made.

    "Changed after" means the example is newer than config.yaml: a git pull that changes
    the example counts, editing config.yaml yourself doesn't. Before overwriting, the
    old config.yaml is saved as config.yaml.bak (gitignored). Without a terminal or in a
    dry run, nothing is written (inform-and-confirm-each-step).
    """
    if example.stat().st_mtime <= config.stat().st_mtime:
        return
    print("config.example.yaml has changed since your config.yaml was made.")
    if dry_run:
        print("Dry run: config.yaml left as it is.")
        return
    try:
        answer = input("  m = update: new example, keep your values (recommended)\n"
                       "  r = replace: fresh copy of the example, your values are lost\n"
                       "  k = keep config.yaml as it is\n"
                       "Choice (m/r/k): ").strip().lower()
    except EOFError:
        print("\nNo terminal to ask on: config.yaml left as it is.")
        return
    backup = config.with_name("config.yaml.bak")
    if answer == "m":
        with open(example, encoding="utf-8", newline="") as f:
            example_text = f.read()
        old = yaml.safe_load(config.read_text(encoding="utf-8")) or {}
        merged, dropped = merge_config_text(example_text, old)
        shutil.copyfile(config, backup)
        with open(config, "w", encoding="utf-8", newline="") as f:
            f.write(merged)
        print(f"Updated config.yaml, your values kept (old one: {backup.name}).")
        if dropped:
            print(f"No longer in the example, dropped: {', '.join(dropped)}.")
        for key, value in (yaml.safe_load(example_text) or {}).items():
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
        os.utime(config)  # newer than the example now: asked again after its next change
        print("Kept config.yaml; you'll be asked again after the next example change.")


def check_config_keys(loaded: dict) -> None:
    """
    Warns when config.yaml and config.example.yaml have different keys.

    config.yaml is a one-time copy, so it silently misses keys added to the example
    later (they fall back to DEFAULTS) and keeps keys the tool no longer reads.
    """
    example = HERE / "config.example.yaml"
    if not example.exists():
        return
    expected = yaml.safe_load(example.read_text(encoding="utf-8")) or {}
    missing = [key for key in expected if key not in loaded]
    unknown = [key for key in loaded if key not in expected]
    if missing:
        print(f"config.yaml is missing: {', '.join(missing)} (defaults used). "
              "Copy them from config.example.yaml.")
    if unknown:
        print(f"config.yaml has keys this tool doesn't read: {', '.join(unknown)} "
              "(ignored).")


def load_settings(args: argparse.Namespace) -> dict:
    """
    Merges settings: CLI flags > config.yaml > DEFAULTS.

    Paths: an absolute "output" is used as-is; a relative one is resolved against this
    tool's folder (relative_to: tool) or the current working directory (relative_to: cwd).

    Returns:
        Settings with "output" as an absolute Path.

    Raises:
        SystemExit: relative_to is neither "tool" nor "cwd".
    """
    settings = dict(DEFAULTS)
    config_file = ensure_config(bool(args.dry_run))
    if config_file:
        loaded = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
        if config_file.name == "config.yaml":
            check_config_keys(loaded)
        settings.update(loaded)
    settings.update({k: v for k, v in vars(args).items() if v is not None and k != "run"})
    if settings["relative_to"] not in RELATIVE_TO:
        raise SystemExit(f"Invalid relative_to {settings['relative_to']!r} "
                         "in config.yaml: choose 'tool' or 'cwd'.")
    base = HERE if settings["relative_to"] == "tool" else Path.cwd()
    path = Path(settings["output"])
    settings["output"] = path if path.is_absolute() else base / path
    return settings


def build_lines(start: int, end: int, step: int, line: str) -> list[str]:
    """
    One filled-in line per number from start to end, both included, counting by step.

    Raises:
        SystemExit: the template uses a placeholder other than {i}.
    """
    try:
        return [line.format(i=i) for i in range(start, end + 1, step)]
    except (KeyError, IndexError) as error:
        raise SystemExit(f"Line template {line!r} uses {error}; only {{i}} is defined "
                         "(write a literal brace as {{ or }}).")


def write_lines(lines: list[str], output_path: Path) -> None:
    """Writes the lines joined by newlines (no trailing newline), creating the folder."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Saved to {output_path}")

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
    if settings["step"] < 1:
        print("step must be 1 or more.")
        return 1
    # 4. Lines
    lines = build_lines(settings["start"], settings["end"], settings["step"],
                        settings["line"])
    output_path = settings["output"] / settings["output_file"]
    print(f"{len(lines)} lines" + (f", first: {lines[0]!r}, last: {lines[-1]!r}"
                                   if lines else " (end is before start)"))
    # 5. Write
    if settings["dry_run"]:
        print(f"Dry run: would write {output_path}")
        return 0
    write_lines(lines, output_path)
    return 0


# -----------------------------------------------------------------------------------------
#                start
# -----------------------------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
