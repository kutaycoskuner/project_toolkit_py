# -----------------------------------------------------------------------------------------
#   author          : Kutay Coskuner
#   ai-contributors : unknown (before 2026-10-04), Claude Opus 5.5 (claude-opus-5-5)
#   last update     : 2026-10-04
#   template        : 3.0.0
#   disclaimer      : Provided as is, without warranty of any kind; use at your own risk.
#                     Check outputs before relying on them.
# -----------------------------------------------------------------------------------------
"""
Batch renamer: adds the folder name as a prefix to files, or removes it, either in place
or as renamed copies in an output folder.

1. Bare run prints this guide and exits (no-args-usage-guide).
2. The first real run offers to create config.yaml from config.example.yaml
   (ensure_config); later runs warn when its keys differ from the example's
   (check_config_keys).
3. Settings come from CLI flags > config.yaml > DEFAULTS (load_settings).
4. Files in the work folder matching the pattern are listed (find_files).
5. Every planned rename is previewed, collisions resolved with a 01, 02 ... suffix
   (plan_renames).
6. A dry run stops here; otherwise you confirm with y/n (confirm).
7. Confirmed renames are applied: in place, or as renamed copies written to the
   output folder while the originals stay unchanged (apply_renames).

Requires: this folder's .venv (pip install -r requirements.txt); .env copied from
.env.example, for secrets only (may stay empty). config.yaml and .env are gitignored:
your work folder goes in config.yaml.

Inputs -> outputs: files in the work folder -> renamed in place when output is empty,
otherwise renamed copies in the output folder (only files that get a new name are
copied; existing files there are overwritten). As shipped, config.example.yaml copies
example/input/Stone/ into example/output/, so the samples never change.

Run:
    python main.py --run                         example: renamed copies in example/output/
    python main.py --run --dry-run               preview only, change nothing
    python main.py --folder D:/Assets/Stone --in-place
    python main.py --folder D:/Assets/Stone --mode add
    python main.py --folder D:/Assets/Stone --mode remove --pattern "*.png"
    python main.py --help                        all flags; see README.md

Gotchas:
    - the prefix match in remove mode ignores case ("stone_c" counts for folder "Stone").
    - in place, a target name that exists on disk gets a suffix even if that file is
      renamed later in the same run, because renames run one by one in preview order.
"""

# -----------------------------------------------------------------------------------------
#                libraries
# -----------------------------------------------------------------------------------------
import argparse
import glob
import os
import shutil
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

# -----------------------------------------------------------------------------------------
#                variables
# -----------------------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
DEFAULTS = {"folder": "", "output": "", "pattern": "*", "mode": "remove",
            "relative_to": "tool", "dry_run": False}
MODES = ("add", "remove")
RELATIVE_TO = ("tool", "cwd")

# -----------------------------------------------------------------------------------------
#                functions
# -----------------------------------------------------------------------------------------
def parse_args(argv: list[str]) -> argparse.Namespace:
    """Defines the CLI; flags default to None so unset ones don't override config."""
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--run", action="store_true", help="run with config defaults")
    parser.add_argument("--folder", help="work folder (default: folder in config.yaml)")
    parser.add_argument("--pattern", help='glob pattern inside the folder (default: "*")')
    parser.add_argument("--mode", choices=MODES, help="add or remove the folder prefix")
    parser.add_argument("--relative-to", choices=RELATIVE_TO,
                        help="base for relative paths: this tool's folder or the cwd")
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--output", help="write renamed copies into this folder")
    target.add_argument("--in-place", dest="output", action="store_const", const="",
                        help="rename the files themselves (ignores output in config)")
    parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=None,
                        help="preview only (--no-dry-run applies, after confirming)")
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

    Paths: an absolute "folder"/"output" is used as-is; a relative one is resolved
    against this tool's folder (relative_to: tool) or the current working directory
    (relative_to: cwd).

    Returns:
        Settings; "folder" and "output" are absolute Paths, or None: no folder set
        anywhere / rename in place.

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
    for key in ("folder", "output"):
        path = Path(settings[key]) if settings[key] else None
        settings[key] = None if path is None else (
            path if path.is_absolute() else base / path)
    return settings


def find_files(folder: Path, pattern: str) -> list[str]:
    """Paths in folder matching pattern, in glob order (which is the preview order)."""
    return glob.glob(os.path.join(folder, pattern))


def plan_renames(file_list: list[str], folder_name: str, mode: str,
                 output: Path | None) -> list[tuple]:
    """
    Prints the preview of every planned rename and returns them.

    A target name is taken if it was already claimed earlier in this run or, in place,
    if it exists on disk; it then gets the first free 01, 02 ... suffix. Copies into
    output overwrite what a previous run left there.

    Returns:
        (old_path, new_path, old_name, new_name) per rename, in preview order.
    """
    folder_lower = folder_name.lower()
    planned_changes = []
    idx = 1
    # names that will exist once the renames planned so far are applied
    virtual_existing_files = set()

    print(f"\n--- Calculating Planned Changes ({mode.upper()} mode) ---")
    if output is not None:
        print(f"    renamed copies go to {output}; the originals stay unchanged")

    for file_path in file_list:
        if not os.path.isfile(file_path):
            continue

        dir_path, file_name = os.path.split(file_path)
        name, ext = os.path.splitext(file_name)

        if mode == "add":
            candidate_base = f"{folder_name}_{name}"
        else:
            if not name.lower().startswith(folder_lower):
                continue
            new_name = name[len(folder_name) :]
            if new_name.startswith(("-", "_")):
                new_name = new_name[1:]
            if new_name == "":
                print(f"  [Skipping empty name generation]: {file_name}")
                continue
            candidate_base = new_name

        target_dir = dir_path if output is None else output

        def taken(name: str) -> bool:
            on_disk = output is None and os.path.exists(os.path.join(target_dir, name))
            return on_disk or name.lower() in virtual_existing_files

        candidate = f"{candidate_base}{ext}"
        is_collision = False
        if taken(candidate):
            is_collision = True
            i = 1
            while taken(f"{candidate_base}{i:02d}{ext}"):
                i += 1
            candidate = f"{candidate_base}{i:02d}{ext}"
        candidate_path = os.path.join(target_dir, candidate)

        virtual_existing_files.add(candidate.lower())

        if file_name != candidate:
            planned_changes.append((file_path, candidate_path, file_name, candidate))
            notification = " [CONFLICT RESOLVED]" if is_collision else ""
            print(f"[{idx}] {file_name} -> {candidate}{notification}")
            idx += 1

    return planned_changes


def confirm(count: int) -> bool:
    """Asks y/n; without a terminal to ask on, says so and answers no."""
    try:
        answer = input(f"\nDo you want to apply these {count} changes? (y/n): ")
    except EOFError:
        print("\nNo terminal to confirm on. No files were altered (see --dry-run).")
        return False
    if answer.lower() != "y":
        print("Operation cancelled. No files were altered.")
        return False
    return True


def apply_renames(planned_changes: list[tuple], output: Path | None) -> None:
    """
    Renames in place, or copies under the new name into output, in preview order.

    A failed file is reported and skipped; the others still go through.
    """
    print("\n--- Applying Changes ---")
    if output is not None:
        output.mkdir(parents=True, exist_ok=True)
    total = len(planned_changes)
    rename_count = 0
    for i, (old_path, new_path, old_name, new_name) in enumerate(planned_changes, start=1):
        try:
            if output is None:
                os.rename(old_path, new_path)
            else:
                shutil.copy2(old_path, new_path)
            print(f"[{i}/{total}] Processed: {old_name} -> {new_name}")
            rename_count += 1
        except OSError as e:
            print(f"[{i}/{total}] ERROR renaming {old_name}: {e}")
    if output is None:
        print(f"\nSuccessfully renamed {rename_count} files.")
    else:
        print(f"\nSuccessfully wrote {rename_count} renamed copies to {output}.")

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
    if settings["folder"] is None:
        print("No work folder set: use --folder or folder in config.yaml.")
        return 1
    if settings["mode"] not in MODES:
        print("Invalid mode in config.yaml. Choose 'add' or 'remove'.")
        return 1
    # 4. Files
    file_list = find_files(settings["folder"], settings["pattern"])
    if not file_list:
        print("No files found matching the configuration filters.")
        return 0
    # 5. Preview
    planned = plan_renames(file_list, settings["folder"].name, settings["mode"],
                           settings["output"])
    if not planned:
        print("\nNo pending name changes detected.")
        return 0
    print(f"\nTotal operations planned: {len(planned)}")
    # 6. Dry run or confirmation
    if settings["dry_run"]:
        print("\nDry run: no files were altered.")
        return 0
    if not confirm(len(planned)):
        return 0
    # 7. Rename
    apply_renames(planned, settings["output"])
    return 0


# -----------------------------------------------------------------------------------------
#                start
# -----------------------------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
