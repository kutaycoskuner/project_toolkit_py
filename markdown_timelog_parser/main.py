# -----------------------------------------------------------------------------------------
#   author          : Kutay Coskuner
#   ai-contributors : unknown (before 2026-10-04), Claude Opus 5.5 (claude-opus-5-5)
#   last update     : 2026-10-06
#   template        : 3.2.0
#   disclaimer      : Provided as is, without warranty of any kind; use at your own risk.
#                     Check outputs before relying on them.
# -----------------------------------------------------------------------------------------
"""
Time-log parser: turns hand-written Markdown time logs into structured data (CSV).

A session is one list line, `- <date> <start>-<end>`, e.g.
    - 20250927      21.04-22.05
    - 20-Feb-2025   22.20-00.36
Dates: YYYYMMDD or dd-Mon-yyyy. Times: HH.MM or HH:MM. An end before the start means
the session ran past midnight; it counts for its start date.

1. Bare run prints this guide and exits (no-args-usage-guide).
2. The first real run offers to create config.yaml from config.example.yaml
   (ensure_config); later runs compare its keys with config.example.yaml's and offer
   to update it when they differ (update_config).
3. Settings come from CLI flags > config.yaml > DEFAULTS (load_settings).
4. Every Markdown file matching the pattern is read; session lines become rows, lines
   that start like a session but don't parse are reported (parse_sessions).
5. Totals per month and per day are printed (summarize).
6. sessions.csv and summary.csv are written to the output folder (write_results);
   a dry run writes nothing.

Requires: this folder's .venv (pip install -r requirements.txt). config.yaml is
gitignored: your input/output folders go there. No .env: the tool needs no secrets.

Inputs -> outputs: *.md files in the input folder -> sessions.csv (one row per session)
and summary.csv (totals per month and day) in the output folder, overwritten on every
run. As shipped, config.example.yaml parses example/input/timelog.md.

Run:
    python main.py --run                         parse the example into example/output/
    python main.py --run --dry-run               print the totals, write nothing
    python main.py --input D:/notes --output D:/notes/csv
    python main.py --help                        all flags; see README.md

Gotchas:
    - only list lines starting with "- " and a digit count as sessions; headings, text
      and lines like "- a note" are ignored, so notes can sit between sessions.
    - month names are English three-letter abbreviations (Jan, Feb, ... Dec).
    - a session with equal start and end counts as 0 minutes, not 24 hours.
"""

# -----------------------------------------------------------------------------------------
#                libraries
# -----------------------------------------------------------------------------------------
import argparse
import csv
import json
import re
import shutil
import sys
from datetime import date, datetime
from pathlib import Path

import yaml

# -----------------------------------------------------------------------------------------
#                variables
# -----------------------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
DEFAULTS = {"input": "example/input", "output": "example/output", "pattern": "*.md",
            "relative_to": "tool", "dry_run": False}
RELATIVE_TO = ("tool", "cwd")
DATE_FORMATS = ("%Y%m%d", "%d-%b-%Y")
# a list line that starts with a digit is meant to be a session
CANDIDATE_RE = re.compile(r"^\s*-\s+\d")
# "- <date> <HH.MM>-<HH.MM>", ":" also allowed between hours and minutes
SESSION_RE = re.compile(r"^\s*-\s+(\S+)\s+(\d{1,2})[.:](\d{2})"
                        r"\s*-\s*(\d{1,2})[.:](\d{2})\s*$")

# -----------------------------------------------------------------------------------------
#                functions
# -----------------------------------------------------------------------------------------
def parse_args(argv: list[str]) -> argparse.Namespace:
    """Defines the CLI; flags default to None so unset ones don't override config."""
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--run", action="store_true", help="run with config defaults")
    parser.add_argument("--input",
                        help="folder with the Markdown logs (default: example/input/)")
    parser.add_argument("--output",
                        help="folder for the CSV files (default: example/output/)")
    parser.add_argument("--pattern", help='which files to read (default: "*.md")')
    parser.add_argument("--relative-to", choices=RELATIVE_TO,
                        help="base for relative paths: this tool's folder or the cwd")
    parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=None,
                        help="print the totals, write nothing")
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


def parse_date(text: str) -> date | None:
    """A date in one of DATE_FORMATS (20250927, 20-Feb-2025), or None."""
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None


def parse_sessions(path: Path) -> tuple[list[dict], list[str]]:
    """
    Reads one Markdown file.

    Returns:
        (sessions as dicts with file, line, date, start, end, minutes; start/end in
        minutes after midnight), (malformed lines as "file:line: text").
    """
    sessions, malformed = [], []
    lines = path.read_text(encoding="utf-8").splitlines()
    for number, line in enumerate(lines, start=1):
        if not CANDIDATE_RE.match(line):
            continue
        match = SESSION_RE.match(line)
        day = parse_date(match.group(1)) if match else None
        times = [int(g) for g in match.groups()[1:]] if match else []
        if day is None or times[0] > 23 or times[2] > 23 or times[1] > 59 or times[3] > 59:
            malformed.append(f"{path.name}:{number}: {line.strip()}")
            continue
        start, end = times[0] * 60 + times[1], times[2] * 60 + times[3]
        sessions.append({"file": path.name, "line": number, "date": day, "start": start,
                         "end": end, "minutes": (end - start) % (24 * 60)})
    return sessions, malformed


def hours(minutes: int) -> str:
    """Minutes as "h:mm", e.g. 135 -> "2:15"."""
    return f"{minutes // 60}:{minutes % 60:02d}"


def summarize(sessions: list[dict]) -> list[tuple[str, str, int, int]]:
    """Totals as (kind, period, sessions, minutes): months first, then days, sorted."""
    totals: dict[tuple[str, str], list[int]] = {}
    for s in sessions:
        month, day = s["date"].strftime("%Y-%m"), s["date"].isoformat()
        for key in (("month", month), ("day", day)):
            total = totals.setdefault(key, [0, 0])
            total[0] += 1
            total[1] += s["minutes"]
    order = {"month": 0, "day": 1}
    ranked = sorted(totals.items(), key=lambda item: (order[item[0][0]], item[0][1]))
    return [(kind, period, n, m) for (kind, period), (n, m) in ranked]


def write_results(sessions: list[dict], summary: list[tuple], output: Path) -> None:
    """Writes sessions.csv and summary.csv into output, overwriting both."""
    output.mkdir(parents=True, exist_ok=True)
    with open(output / "sessions.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "start", "end", "minutes", "file", "line"])
        for s in sessions:
            writer.writerow([s["date"].isoformat(), hours(s["start"]).zfill(5),
                             hours(s["end"]).zfill(5), s["minutes"], s["file"], s["line"]])
    with open(output / "summary.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["kind", "period", "sessions", "minutes", "hours"])
        writer.writerows((k, p, n, m, hours(m)) for k, p, n, m in summary)
    print(f"Saved {output / 'sessions.csv'} and {output / 'summary.csv'}")

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
    if not settings["input"].is_dir():
        print(f"Input folder not found: {settings['input']}")
        return 1
    # 4. Parse
    files = sorted(settings["input"].glob(settings["pattern"]))
    sessions, malformed = [], []
    for path in files:
        found, bad = parse_sessions(path)
        sessions += found
        malformed += bad
    sessions.sort(key=lambda s: (s["date"], s["start"]))
    for line in malformed:
        print(f"Skipped, not a valid session: {line}")
    if not sessions:
        print(f"No sessions found in {len(files)} file(s) "
              f"matching {settings['pattern']!r}.")
        return 0
    # 5. Totals
    summary = summarize(sessions)
    total = sum(s["minutes"] for s in sessions)
    print(f"{len(sessions)} sessions in {len(files)} file(s), total {hours(total)}")
    for kind, period, count, minutes in summary:
        if kind == "month":
            label = "session" if count == 1 else "sessions"
            print(f"  {period}: {hours(minutes):>6}  ({count} {label})")
    # 6. Write
    if settings["dry_run"]:
        print("Dry run: nothing written.")
        return 0
    write_results(sessions, summary, settings["output"])
    return 0


# -----------------------------------------------------------------------------------------
#                start
# -----------------------------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
