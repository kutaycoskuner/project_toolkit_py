# -----------------------------------------------------------------------------------------
#   author          : Kutay Coskuner
#   ai-contributors : Claude Opus 5.5 (claude-opus-5-5)
#   last update     : 2026-10-07
#   template        : 3.2.0
#   disclaimer      : Provided as is, without warranty of any kind; use at your own risk.
#                     Check outputs before relying on them.
# -----------------------------------------------------------------------------------------
"""
ID-name mapper: swaps file names between an ID and a readable name, from a mapping file.

Some programs find files by an ID in the file name (0x0A3C.png), which says nothing to a
person. A mapping file (YAML, `id: name` per line) gives each ID a name; to_name renames
0x0A3C.png to backpack-0x0A3C.png, to_id renames it back to 0x0A3C.png, so the
program finds it again. The ID stays in the name, so to_id needs no mapping. A "/" in
a name sorts the file into folders: gump/button puts it in gump/button-0x00D4.png, and
to_id moves it back to 0x00D4.png in the root folder. Folders listed under
ignore_folders in the mapping file are skipped in both directions.

1. Bare run prints this guide and exits (no-args-usage-guide).
2. The first real run offers to create config.yaml from config.example.yaml
   (ensure_config); later runs compare its keys with config.example.yaml's and offer
   to update it when they differ (update_config).
3. Settings come from CLI flags > config.yaml > DEFAULTS (load_settings).
4. The mapping is read and checked: names that can't become file paths are reported
   and left out (load_mapping, name_problem); to_id reads it only for ignore_folders,
   and runs without it.
5. Every file's new place (folders + name) is planned for input_dir and its subfolders
   and previewed: unchanged, not in the mapping and collisions are reported, never
   guessed (plan_renames, new_location).
6. A dry run stops here; otherwise you confirm with y/n (confirm).
7. Confirmed renames are applied: in place (folders the moves emptied are removed), or
   as renamed copies written to output_dir in the same folder layout while the
   originals stay unchanged (apply_renames, remove_empty_folders).

Requires: this folder's .venv (pip install -r requirements.txt). config.yaml is
gitignored: your input_dir and mapping file go there. No .env: no secrets needed.

Inputs -> outputs: files in input_dir + the mapping file -> renamed in place when
output_dir is empty or the same folder as input_dir, otherwise renamed copies in
output_dir (only files that get a new name are copied; existing files there are
overwritten). As shipped, config.example.yaml copies example/input/ into
example/output/, so the samples never change. Paths may be absolute or relative to
this tool's folder (relative_to: tool, default) or to the current working directory
(relative_to: cwd).

Run:
    python main.py --run                         example: named copies in example/output/
    python main.py --run --direction to_id       example: back to ID names
    python main.py --run --dry-run               preview only, change nothing
    python main.py --run --input-dir D:/files --mapping D:/files/names.yaml --in-place
    python main.py --help                        all flags; see README.md

Gotchas:
    - IDs match ignoring case (0x0a3d.png finds 0x0A3D in the mapping); the new name
      keeps the file's own spelling, so to_id gives back exactly the old name.
    - a name file (backpack-0x0A3C.png) whose mapping name changed gets the new name on
      the next to_name run; one whose ID left the mapping keeps its name.
    - the ID is the part after the last separator, so a name may contain it
      (health-bar-0x0805), an ID may not; with the default "-", to_id treats any file
      with a "-" in its name as a name file.
    - to_id moves only name files (with the separator) out of subfolders; a plain ID
      file inside a subfolder stays where it is.
    - ignore_folders is a reserved key in the mapping file, not an ID; the mapping file
      itself is never renamed, also when it sits in input_dir.
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
DEFAULTS = {"input_dir": "", "output_dir": "", "mapping": "", "direction": "to_name",
            "separator": "-", "pattern": "*", "relative_to": "tool", "dry_run": False}
DIRECTIONS = ("to_name", "to_id")
RELATIVE_TO = ("tool", "cwd")
IGNORE_KEY = "ignore_folders"  # reserved key in the mapping file, not an ID
# characters Windows forbids in file names; macOS and Linux only forbid "/"
BAD_NAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

# -----------------------------------------------------------------------------------------
#                functions
# -----------------------------------------------------------------------------------------
def parse_args(argv: list[str]) -> argparse.Namespace:
    """Defines the CLI; flags default to None so unset ones don't override config."""
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--run", action="store_true", help="run with config defaults")
    parser.add_argument("--direction", choices=DIRECTIONS,
                        help="to_name: ID -> name-ID, to_id: name-ID -> ID "
                             "(default: to_name)")
    parser.add_argument("--input-dir", help="folder whose files are renamed "
                                            "(default: input_dir in config.yaml)")
    parser.add_argument("--mapping", help="mapping file, `id: name` per line "
                                          "(default: mapping in config.yaml)")
    parser.add_argument("--separator", help='between name and ID (default: "-")')
    parser.add_argument("--pattern", help='glob pattern inside the folder (default: "*")')
    parser.add_argument("--relative-to", choices=RELATIVE_TO,
                        help="base for relative paths: this tool's folder or the cwd")
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--output-dir", help="write renamed copies into this folder; "
                                             "the input folder itself = in place")
    target.add_argument("--in-place", dest="output_dir", action="store_const", const="",
                        help="rename the files themselves (ignores output_dir in config)")
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

    Paths: an absolute "input_dir"/"output_dir"/"mapping" is used as-is; a relative one
    is resolved against this tool's folder (relative_to: tool) or the current working
    directory (relative_to: cwd). An output_dir that is the input_dir itself means in
    place: copies next to the originals would leave every file twice.

    Returns:
        Settings; "input_dir", "output_dir" and "mapping" are absolute Paths, or None
        when empty ("output_dir" None = rename in place).

    Raises:
        SystemExit: relative_to, direction or separator is invalid.
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
    if settings["direction"] not in DIRECTIONS:
        raise SystemExit(f"Invalid direction {settings['direction']!r}: "
                         "choose 'to_name' or 'to_id'.")
    separator = str(settings["separator"])
    if not separator or BAD_NAME.search(separator):
        raise SystemExit(f"Invalid separator {separator!r}: it goes into file names, so "
                         'it can\'t be empty or contain <>:"/\\|?*')
    settings["separator"] = separator
    base = HERE if settings["relative_to"] == "tool" else Path.cwd()
    for key in ("input_dir", "output_dir", "mapping"):
        path = Path(settings[key]) if settings[key] else None
        settings[key] = None if path is None else (
            path if path.is_absolute() else base / path)
    source, target = settings["input_dir"], settings["output_dir"]
    if source and target and source.resolve() == target.resolve():
        print("output_dir is the input folder: renaming in place.")
        settings["output_dir"] = None
    return settings


def name_problem(name: str) -> str | None:
    """
    Returns why a mapping name can't become a file path, or None when it can.

    "/" splits the name into folders and the file name (gump/button); each part must
    be a valid file name: not empty, not "." or "..", no character Windows forbids, no
    trailing dot or space.
    """
    if not name:
        return "empty name"
    for part in name.split("/"):
        if not part:
            return "empty folder or name part (a leading, trailing or double /)"
        if part in (".", ".."):
            return "'.' or '..' as a folder"
        if BAD_NAME.search(part):
            return f"forbidden character in {part!r}"
        if part[-1] in ". ":
            return f"{part!r} ends with a dot or space"
    return None


def load_mapping(path: Path) -> tuple[dict[str, str], set[str]]:
    """
    Reads the mapping file: one `id: name` per line, plus the ignore_folders list.

    Read as plain text on purpose: YAML would turn 0x0A3C into the number 2620 and
    007 into 7. A "/" (or "\\") in a name makes folders (gump/button). Names that can't
    become a file path (see name_problem), names that would put a file into an ignored
    folder, and IDs listed twice ignoring case are reported and left out, never
    silently fixed. ignore_folders (a list, or one name) holds folder names, matched
    ignoring case at any depth; an entry with a "/" is reported and left out.

    Returns:
        ({lower-case ID: name, with "/" between folders}, {lower-case ignored folder}).

    Raises:
        SystemExit: the file is missing or isn't an `id: name` mapping.
    """
    if not path.is_file():
        raise SystemExit(f"Mapping file not found: {path}")
    try:
        data = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    except yaml.YAMLError as error:
        raise SystemExit(f"Mapping file {path.name} isn't valid YAML: {error}")
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise SystemExit(f"Mapping file {path.name} must be `id: name` lines, "
                         "e.g.  0x0A3C: backpack")
    listed = data.pop(IGNORE_KEY, [])
    ignore: set[str] = set()
    for folder in [listed] if isinstance(listed, str) else listed:
        folder = str(folder).strip()
        if not folder or "/" in folder or "\\" in folder:
            print(f"mapping: {IGNORE_KEY}: skipped {folder!r} (a folder name, not a path)")
        else:
            ignore.add(folder.lower())
    if not all(isinstance(v, str) for v in data.values()):
        raise SystemExit(f"Mapping file {path.name} must be `id: name` lines, "
                         "e.g.  0x0A3C: backpack")
    mapping: dict[str, str] = {}
    first: dict[str, str] = {}  # lower-case ID -> its spelling where first listed
    for file_id, name in data.items():
        name = name.strip().replace("\\", "/")
        hidden = [f for f in name.split("/")[:-1] if f.lower() in ignore]
        problem = ("forbidden character in the ID" if BAD_NAME.search(file_id) else
                   f"listed twice, also as {first[file_id.lower()]}"
                   if file_id.lower() in first else name_problem(name) or
                   (f"goes into the ignored folder {hidden[0]}" if hidden else None))
        if problem:
            print(f"mapping: skipped {file_id}: {name!r} ({problem})")
            continue
        first[file_id.lower()] = file_id
        mapping[file_id.lower()] = name
    print(f"mapping: {len(mapping)} IDs from {path}")
    if ignore:
        print(f"ignored folders: {', '.join(sorted(ignore))}")
    return mapping, ignore


def new_location(rel: Path, settings: dict,
                 mapping: dict[str, str]) -> tuple[str | None, str]:
    """
    Returns a file's new place, relative to the root folder, without the extension.

    `rel` is the file's path relative to input_dir. to_name: the ID is the whole stem
    (0x0A3C) or the part after the last separator (old_name-0x0A3C); a mapped ID goes
    to "<name><separator><ID>", where the name's "/" parts are folders
    (gump/button-0x00D4), keeping the file's own spelling of the ID. to_id: a
    "<name><separator><ID>" file in any folder goes to "<ID>" in the root.

    Returns:
        (new place as "folder/stem", or None when the file stays; the reason, for the
        preview).
    """
    separator, stem = settings["separator"], rel.stem
    named = separator in stem
    file_id = stem.rsplit(separator, 1)[1] if named else stem
    if settings["direction"] == "to_id":
        if not named:
            return None, "already an ID"
        return (file_id, "") if file_id else (None, "nothing after the separator")
    name = mapping.get(file_id.lower())
    if name is None:
        return None, "not in the mapping"
    target = f"{name}{separator}{file_id}"
    if target == rel.with_suffix("").as_posix():
        return None, "already named"
    return target, ""


def plan_renames(settings: dict, mapping: dict[str, str],
                 ignore: set[str]) -> list[tuple[Path, Path]]:
    """
    Prints the preview of every planned rename or move and returns them.

    Looks through input_dir and its subfolders, since named files may sit in folders.
    Skipped: folders named in `ignore` (counted in the preview), an output_dir inside
    input_dir (so earlier copies aren't picked up) and the mapping file itself.
    Files the direction leaves alone are counted by reason; files not in the mapping
    are listed, so a missing entry shows up. A target that exists on disk (in place) or
    was claimed earlier in this run is a collision: reported and skipped, since a
    numbered suffix would break the ID. Copies into output_dir overwrite what a previous
    run left there.

    Returns:
        (old path, new path) per rename, in preview order.
    """
    root, output = settings["input_dir"], settings["output_dir"]
    skip = output.resolve() if output is not None else None
    mapping_file = settings["mapping"].resolve() if settings["mapping"] else None
    files = sorted(p for p in root.rglob(settings["pattern"])
                   if p.is_file() and skip not in p.resolve().parents
                   and p.resolve() != mapping_file)
    planned: list[tuple[Path, Path]] = []
    claimed: set[str] = set()
    skipped: dict[str, list[str]] = {}
    print(f"\n--- Planned changes ({settings['direction']}) ---")
    print(f"    renamed copies go to {output}; the originals stay unchanged"
          if output is not None else "    in place: the files themselves are renamed")
    for path in files:
        rel = path.relative_to(root)
        if any(folder.lower() in ignore for folder in rel.parts[:-1]):
            skipped.setdefault("in an ignored folder", []).append(rel.as_posix())
            continue
        place, reason = new_location(rel, settings, mapping)
        if place is None:
            skipped.setdefault(reason, []).append(rel.as_posix())
            continue
        new_rel = f"{place}{path.suffix}"
        target = (root if output is None else output) / new_rel
        on_disk = (output is None and target.exists()
                   and not os.path.samefile(path, target))  # a case-only change is fine
        if on_disk or new_rel.lower() in claimed:
            print(f"  [skipped, {new_rel} already exists] {rel.as_posix()}")
            continue
        claimed.add(new_rel.lower())
        planned.append((path, target))
        print(f"[{len(planned)}] {rel.as_posix()} -> {new_rel}")
    for reason, names in skipped.items():
        listed = f": {', '.join(names)}" if reason == "not in the mapping" else ""
        print(f"  left alone, {reason}: {len(names)}{listed}")
    return planned


def confirm(count: int) -> bool:
    """Asks y/n; without a terminal to ask on, says so and answers no."""
    try:
        answer = input(f"\nApply these {count} changes? (y/n): ")
    except EOFError:
        print("\nNo terminal to confirm on. No files were changed (see --dry-run).")
        return False
    if answer.strip().lower() != "y":
        print("Cancelled. No files were changed.")
        return False
    return True


def remove_empty_folders(folders: set[Path], root: Path) -> None:
    """
    Removes the given folders and their parents up to root, while they're empty.

    Called with the folders files were moved out of, so only folders this run emptied
    go; root itself always stays.
    """
    for folder in sorted(folders, key=lambda f: len(f.parts), reverse=True):
        while folder != root and root in folder.parents:
            try:
                folder.rmdir()  # fails, and stops here, unless empty
            except OSError:
                break
            print(f"removed empty folder: {folder.relative_to(root).as_posix()}")
            folder = folder.parent


def apply_renames(planned: list[tuple[Path, Path]], root: Path,
                  output: Path | None) -> None:
    """
    Renames or moves in place, or copies to the new place in output_dir, in preview order.

    Creates the folders a name asks for; in place, folders left empty by the moves are
    removed afterwards. A failed file is reported and skipped; the others still go
    through.
    """
    print("\n--- Applying changes ---")
    done, emptied = 0, set()
    for i, (old, new) in enumerate(planned, start=1):
        try:
            new.parent.mkdir(parents=True, exist_ok=True)
            if output is None:
                old.rename(new)
                emptied.add(old.parent)
            else:
                shutil.copy2(old, new)
            print(f"[{i}/{len(planned)}] {old.relative_to(root).as_posix()} -> "
                  f"{new.relative_to(output or root).as_posix()}")
            done += 1
        except OSError as error:
            print(f"[{i}/{len(planned)}] ERROR {old.name}: {error}")
    if output is None:
        remove_empty_folders(emptied, root)
    print(f"\n{'Renamed' if output is None else 'Wrote renamed copies of'} {done} files"
          + ("." if output is None else f" to {output}."))

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
    if settings["input_dir"] is None or not settings["input_dir"].is_dir():
        print(f"Input folder not found: {settings['input_dir'] or '(not set)'}; "
              "use --input-dir or input_dir in config.yaml.")
        return 1
    print(f"input  : {settings['input_dir']}")
    # 4. Mapping (to_id reads the ID from the file name: the mapping only for its
    #    ignore_folders, and it runs without one)
    mapping: dict[str, str] = {}
    ignore: set[str] = set()
    found = settings["mapping"] is not None and settings["mapping"].is_file()
    if settings["direction"] == "to_name" or found:
        if settings["mapping"] is None:
            print("No mapping file set: use --mapping or mapping in config.yaml.")
            return 1
        mapping, ignore = load_mapping(settings["mapping"])
    else:
        print("No mapping file: no folders are ignored.")
    # 5. Preview
    planned = plan_renames(settings, mapping, ignore)
    if not planned:
        print("\nNothing to rename.")
        return 0
    print(f"\nTotal: {len(planned)} renames")
    # 6. Dry run or confirmation
    if settings["dry_run"]:
        print("\nDry run: no files were changed.")
        return 0
    if not confirm(len(planned)):
        return 0
    # 7. Rename
    apply_renames(planned, settings["input_dir"], settings["output_dir"])
    return 0


# -----------------------------------------------------------------------------------------
#                start
# -----------------------------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
