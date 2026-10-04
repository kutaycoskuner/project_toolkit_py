# -----------------------------------------------------------------------------------------
#   author          : Kutay Coskuner
#   ai-contributors : Claude Opus 5.5 (claude-opus-5-5)
#   last update     : 2026-10-04
#   template        : 3.1.0
#   disclaimer      : Provided as is, without warranty of any kind; use at your own risk.
#                     Check outputs before relying on them.
# -----------------------------------------------------------------------------------------
"""
<One line: what this tool is.>

<What it does: 1-5 lines.> As shipped, run() is a demo: it writes an upper-cased copy of
every .txt file in the input folder to the output folder.

1. Bare run prints this guide and exits (no-args-usage-guide).
2. The first real run offers to create config.yaml from config.example.yaml
   (ensure_config); later runs offer to update it when config.example.yaml has changed
   since (update_config) and warn when its keys differ from the example's
   (check_config_keys).
3. Settings come from CLI flags > config.yaml > DEFAULTS (load_settings).
4. The input folder is processed into the output folder (run).

Requires: this folder's .venv (pip install -r requirements.txt); .env copied from
.env.example, for secrets only (may stay empty). config.yaml and .env are gitignored:
personal paths go in config.yaml, never into the committed config.example.yaml.

Inputs -> outputs: example/input/ -> example/output/ until config.yaml points elsewhere.
Paths may be absolute (used as-is) or relative: resolved against this tool's folder
(relative_to: tool, default) or the current working directory (relative_to: cwd).

Run:
    python main.py --run                     process example/input/ into example/output/
    python main.py --run --dry-run           show what would happen, write nothing
    python main.py --input <dir> --output <dir>
    python main.py --help                    all flags; see README.md
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
from dotenv import load_dotenv

# -----------------------------------------------------------------------------------------
#                variables
# -----------------------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
DEFAULTS = {"input": "example/input", "output": "example/output", "relative_to": "tool",
            "dry_run": False}
RELATIVE_TO = ("tool", "cwd")

# -----------------------------------------------------------------------------------------
#                functions
# -----------------------------------------------------------------------------------------
def parse_args(argv: list[str]) -> argparse.Namespace:
    """Defines the CLI; flags default to None so unset ones don't override config."""
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--run", action="store_true", help="run with config defaults")
    parser.add_argument("--input", help="input folder (default: example/input/)")
    parser.add_argument("--output", help="output folder (default: example/output/)")
    parser.add_argument("--relative-to", choices=RELATIVE_TO,
                        help="base for relative paths: this tool's folder or the cwd")
    parser.add_argument("--dry-run", action="store_true", default=None,
                        help="show what would happen, write nothing")
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

    Only top-level `key: value` lines are touched, so comments, order and new keys come
    from the example. Values are written as JSON, which is valid YAML.

    Returns:
        (merged text, old keys the example no longer has).
    """
    # key : spacing : value : optional comment : line ending
    line_re = re.compile(r"^([A-Za-z_][\w-]*):([ \t]*)([^#\r\n]*?)"
                         r"([ \t]*#[^\r\n]*)?(\r?\n)?$")
    merged, used = [], set()
    for line in example_text.splitlines(keepends=True):
        match = line_re.match(line)
        if match and match.group(1) in old and match.group(3).strip():
            key, space, value, comment, newline = match.groups()
            new_value = json.dumps(old[key], ensure_ascii=False).ljust(len(value))
            line = f"{key}:{space}{new_value}{comment or ''}{newline or ''}"
            used.add(key)
        merged.append(line)
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
        if config_file.name == "config.yaml":
            check_config_keys(loaded)
        settings.update(loaded)
    load_dotenv(HERE / ".env")  # secrets only (os.getenv where needed); never settings
    settings.update({k: v for k, v in vars(args).items() if v is not None and k != "run"})
    if settings["relative_to"] not in RELATIVE_TO:
        raise SystemExit(f"Invalid relative_to {settings['relative_to']!r} "
                         "in config.yaml: choose 'tool' or 'cwd'.")
    base = HERE if settings["relative_to"] == "tool" else Path.cwd()
    for key in ("input", "output"):
        path = Path(settings[key])
        settings[key] = path if path.is_absolute() else base / path
    return settings


def run(settings: dict) -> None:
    """
    Demo work, replace with the tool's own: upper-cases every .txt file into output.

    Writes nothing when settings["dry_run"] is set.
    """
    dry_run = settings["dry_run"]
    print(f"input : {settings['input']}")
    print(f"output: {settings['output']}")
    files = sorted(settings["input"].glob("*.txt"))
    if not files:
        print("No .txt files in the input folder.")
        return
    if not dry_run:
        settings["output"].mkdir(parents=True, exist_ok=True)
    for src in files:
        dst = settings["output"] / src.name
        if dry_run:
            print(f"would write: {dst.name}")
            continue
        dst.write_text(src.read_text(encoding="utf-8").upper(), encoding="utf-8")
        print(f"processed: {src.name} -> {dst}")
    if dry_run:
        print("dry run: nothing written")

# -----------------------------------------------------------------------------------------
#                main
# -----------------------------------------------------------------------------------------
def main(argv: list[str]) -> int:
    # 1. No arguments: usage guide only, never work (no-args-usage-guide)
    if not argv:
        print(__doc__.strip())
        return 0
    # 2.-3. Settings from CLI, config.yaml (offered on the first real run), defaults
    settings = load_settings(parse_args(argv))
    if not settings["input"].is_dir():
        print(f"Input folder not found: {settings['input']}")
        return 1
    # 4. Work
    run(settings)
    return 0


# -----------------------------------------------------------------------------------------
#                start
# -----------------------------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
