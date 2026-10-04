# -----------------------------------------------------------------------------------------
#   author          : Kutay Coskuner
#   ai-contributors : unknown (before 2026-10-04), Claude Opus 5.5 (claude-opus-5-5)
#   last update     : 2026-10-04
#   template        : 3.1.1
#   disclaimer      : Provided as is, without warranty of any kind; use at your own risk.
#                     Check outputs before relying on them.
# -----------------------------------------------------------------------------------------
"""
Repetitive XML generator: builds XML elements from a pattern in config.yaml (any tags,
attributes and nesting, with repeated children) and inserts them into an XML file.

The pattern (`elements` in config.yaml) is a list of elements, each with
    tag         the element name, e.g. cooldownentry
    attributes  name: value pairs; values may use {placeholders}
    children    a list of elements, nested the same way
    repeat      optional: {name: duration, from: 0, to: 120, step: 1} generates the
                element once per value; {duration} then holds the value, and {time},
                {minutes}, {seconds} read it as seconds ("1m 5s", 1, 5)
Placeholders come from every repeat around an element, so repeats can be nested.
true/false attributes are written as True/False.

1. Bare run prints this guide and exits (no-args-usage-guide).
2. The first real run offers to create config.yaml from config.example.yaml
   (ensure_config); later runs offer to update it when config.example.yaml has changed
   since (update_config) and warn when its keys differ from the example's
   (check_config_keys).
3. Settings come from CLI flags > config.yaml > DEFAULTS (load_settings).
4. The elements are rendered to XML text, indented like the input file (build_block).
5. They are inserted right before `insert_before` (e.g. </cooldowns>) in a copy of the
   input, written to the output file (insert_block); a dry run only previews them.

Requires: this folder's .venv (pip install -r requirements.txt). config.yaml is
gitignored: your files and patterns go there. No .env: the tool needs no secrets.

Inputs -> outputs: an XML file + the pattern -> a copy of the file with the generated
elements inserted (overwritten on every run; the input is never changed). As shipped,
config.example.yaml adds two cooldown entries to example/input/cooldowns.xml.

Run:
    python main.py --run                         generate into example/output/
    python main.py --run --dry-run               preview the generated XML, write nothing
    python main.py --input D:/razor/cooldowns.xml --output D:/razor/cooldowns_new.xml
    python main.py --help                        all flags; see README.md

Gotchas:
    - the elements are inserted before the first `insert_before` text in the file, so
      use the parent's closing tag (</cooldowns>), which appears once.
    - attribute values are XML-escaped (& < > "), so write them as plain text.
    - a {placeholder} that no repeat defines stops the run with its name; write a
      literal brace as {{ or }}.
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
from xml.sax.saxutils import escape

import yaml

# -----------------------------------------------------------------------------------------
#                variables
# -----------------------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
DEFAULTS = {
    "input": "example/input/cooldowns.xml",
    "output": "example/output/cooldowns_generated.xml",
    "insert_before": "</cooldowns>",
    "indent": "auto",
    "elements": [],
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
    parser.add_argument("--input", help="XML file to add the elements to")
    parser.add_argument("--output", help="file to write the result to (overwritten)")
    parser.add_argument("--relative-to", choices=RELATIVE_TO,
                        help="base for relative paths: this tool's folder or the cwd")
    parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=None,
                        help="preview the generated XML, write nothing")
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
    settings.update({k: v for k, v in vars(args).items() if v is not None and k != "run"})
    if settings["relative_to"] not in RELATIVE_TO:
        raise SystemExit(f"Invalid relative_to {settings['relative_to']!r} "
                         "in config.yaml: choose 'tool' or 'cwd'.")
    base = HERE if settings["relative_to"] == "tool" else Path.cwd()
    for key in ("input", "output"):
        path = Path(settings[key])
        settings[key] = path if path.is_absolute() else base / path
    return settings


def time_text(total_seconds: int) -> str:
    """Seconds as a short duration: 65 -> "1m 5s", 60 -> "1m", 5 -> "5s", 0 -> "0s"."""
    minutes, seconds = divmod(total_seconds, 60)
    parts = [f"{minutes}m"] if minutes else []
    if seconds or not minutes:
        parts.append(f"{seconds}s")
    return " ".join(parts)


def fill(text, variables: dict) -> str:
    """
    Fills {placeholders} in an attribute value; true/false become True/False.

    Raises:
        SystemExit: the text uses a placeholder that no surrounding repeat defines.
    """
    if isinstance(text, bool):
        return str(text)
    try:
        return str(text).format(**variables)
    except KeyError as missing:
        known = ", ".join("{" + k + "}" for k in variables) or "none"
        raise SystemExit(f"Unknown placeholder {{{missing.args[0]}}} in {text!r}; "
                         f"defined here: {known}.")


def expand(spec: dict, variables: dict) -> list[dict]:
    """
    The variable sets an element is rendered with: one per repeat value, or just the
    surrounding ones when it doesn't repeat.
    """
    repeat = spec.get("repeat")
    if not repeat:
        return [variables]
    name = repeat["name"]
    values = range(int(repeat["from"]), int(repeat["to"]) + 1, int(repeat.get("step", 1)))
    return [{**variables, name: value, "time": time_text(value),
             "minutes": value // 60, "seconds": value % 60} for value in values]


def render(spec: dict, variables: dict, level: int, indent: str,
           counts: dict) -> list[str]:
    """
    One element (all its repeats) as XML lines at the given depth; counts every tag.

    Raises:
        SystemExit: an element has no `tag`.
    """
    if "tag" not in spec:
        raise SystemExit(f"An element in `elements` has no `tag`: {spec}")
    lines = []
    for scope in expand(spec, variables):
        tag, pad = spec["tag"], indent * level
        attributes = "".join(f' {name}="{escape(fill(value, scope), {chr(34): "&quot;"})}"'
                             for name, value in (spec.get("attributes") or {}).items())
        counts[tag] = counts.get(tag, 0) + 1
        children = spec.get("children") or []
        if not children:
            lines.append(f"{pad}<{tag}{attributes} />")
            continue
        lines.append(f"{pad}<{tag}{attributes}>")
        for child in children:
            lines += render(child, scope, level + 1, indent, counts)
        lines.append(f"{pad}</{tag}>")
    return lines


def detect_indent(xml_content: str) -> str:
    """The file's indentation unit: the whitespace before its first indented tag."""
    match = re.search(r"\n([ \t]+)<", xml_content)
    return match.group(1) if match else "    "


def build_block(elements: list[dict], indent: str) -> tuple[str, dict]:
    """
    Renders every top-level element one level deep (inside the parent element).

    Returns:
        (the XML text, {tag: number of elements generated}).
    """
    counts, lines = {}, []
    for spec in elements:
        lines += render(spec, {}, 1, indent, counts)
    return "\n".join(lines), counts


def insert_block(xml_content: str, block: str, insert_before: str) -> str:
    """
    Inserts block on its own lines right before the first `insert_before` text.

    Raises:
        SystemExit: insert_before doesn't occur in the file.
    """
    if insert_before not in xml_content:
        raise SystemExit(f"Could not find {insert_before!r} in the input file.")
    return xml_content.replace(insert_before, f"{block}\n{insert_before}", 1)

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
    if not settings["input"].is_file():
        print(f"Input file not found: {settings['input']}")
        return 1
    if not settings["elements"]:
        print("Nothing to generate: `elements` in config.yaml is empty.")
        return 1
    # 4. Render
    with open(settings["input"], "r", encoding="utf-8") as file:
        xml_content = file.read()
    indent = settings["indent"]
    if indent == "auto":
        indent = detect_indent(xml_content)
    block, counts = build_block(settings["elements"], indent)
    print(f"Input : {settings['input']}")
    print("Generated: " + ", ".join(f"{n} <{tag}>" for tag, n in counts.items()))
    # 5. Insert and write
    updated_xml = insert_block(xml_content, block, settings["insert_before"])
    if settings["dry_run"]:
        preview = block.splitlines()
        print("\n".join(preview[:8] + (["    ..."] if len(preview) > 8 else [])))
        print("Dry run: nothing written.")
        return 0
    settings["output"].parent.mkdir(parents=True, exist_ok=True)
    with open(settings["output"], "w", encoding="utf-8") as file:
        file.write(updated_xml)
    print(f"Output: {settings['output']}")
    print("Done.")
    return 0


# -----------------------------------------------------------------------------------------
#                start
# -----------------------------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
