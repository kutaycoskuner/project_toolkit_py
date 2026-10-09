# -----------------------------------------------------------------------------------------
#   author          : Kutay Coskuner
#   ai-contributors : unknown (before 2026-10-04), Claude Opus 5.5 (claude-opus-5-5)
#   last update     : 2026-10-09
#   template        : 3.2.0
#   disclaimer      : Provided as is, without warranty of any kind; use at your own risk.
#                     Check outputs before relying on them.
# -----------------------------------------------------------------------------------------
"""
Time-log parser: calculates totals from hand-written Markdown time logs, CSV on request.

A session is one list line, `- <date> <start>-<end> [description]`, e.g.
    - 20250927      21.04-22.05 development: rendering test
    - 20-Feb-2025   22.20-00.36
Dates: any format in date_formats (config). Times: HH.MM or HH:MM, "-" or "–" between
them. An end before the start means the session ran past midnight; it counts for its
start date.

1. Without --run nothing is done: a bare run prints the same guide as --help, with
   the values config.yaml sets now (build_parser, no-args-usage-guide).
2. The first real run offers to create config.yaml from config.example.yaml
   (ensure_config); later runs compare its keys with config.example.yaml's and offer
   to update it when they differ (update_config).
3. Settings come from CLI flags > config.yaml > DEFAULTS (load_settings).
4. The input is one Markdown file, or every file in a folder matching the pattern
   (find_input_files).
5. Session lines become rows, filtered by date_from/date_to; lines that don't parse,
   unreadable files, duplicates, overlaps, empty, overlong and future sessions are
   collected as problems (read_logs).
6. The sessions (with --entries) and the problems are printed; with ignore_problems
   only their count (print_details).
7. Only with write_csv (--csv): sessions.csv, summary.csv and problems.csv are written
   to the output folder (summarize, write_results); a dry run writes nothing.
8. The results come last, each in its own "=== ..." block: TOTALS per period (day,
   week, month, year, all; print_totals), then SUM, one line per calendar window
   (this/last day, week, month, year, or all) counted from today over every session,
   ignoring date_from/date_to (print_sums).
9. Exit code 1 when there were problems, so a script calling the tool can notice;
   0 with ignore_problems.

Requires: this folder's .venv (pip install -r requirements.txt). config.yaml is
gitignored: your input/output paths go there. No .env: the tool needs no secrets.

Inputs -> outputs: a .md file or a folder of them -> totals and problems in the console;
with --csv also sessions.csv (one row per session), summary.csv (totals per period) and
problems.csv in the output folder, overwritten on every such run. As shipped,
config.example.yaml reads example/input/timelog.md.

Run: python main.py --run; the examples are in --help (USAGE).

Gotchas:
    - only list lines starting with "- " and a digit count as sessions; headings, text
      and lines like "- a note" are ignored, so notes can sit between sessions.
    - %b month names are English three-letter abbreviations (Jan, Feb, ... Dec).
    - weeks are ISO weeks (Monday to Sunday, 2025-W39); the week that holds 1 January
      can belong to the previous ISO year.
    - problems are reported, never fixed: duplicates and overlaps still count in the
      totals, so the totals match the log until you correct it. The exception: a
      session longer than max_session_hours is never counted (likely a typo), and the
      TOTALS and SUM blocks say so even with ignore_problems.
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
from datetime import date, datetime, timedelta
from pathlib import Path

import yaml

# -----------------------------------------------------------------------------------------
#                variables
# -----------------------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
PERIODS = ("day", "week", "month", "year", "all")
SUMS = ("this_day", "this_week", "this_month", "this_year", "all",
        "last_day", "last_week", "last_month", "last_year")
DEFAULTS = {"input": "example/input", "output": "example/output", "pattern": "*.md",
            "relative_to": "tool", "dry_run": False, "write_csv": False,
            "periods": list(PERIODS),
            "date_formats": ["%Y%m%d", "%d-%b-%Y", "%Y-%m-%d", "%d.%m.%Y"],
            "max_session_hours": 12, "show_entries": False, "ignore_problems": False,
            "date_from": None, "date_to": None,
            "sum": ["this_week", "last_week", "this_month", "last_month"]}
RELATIVE_TO = ("tool", "cwd")
# a list line that starts with a digit is meant to be a session
CANDIDATE_RE = re.compile(r"^\s*-\s+\d")
# "- <date> <HH.MM>-<HH.MM> [description]"; ":" also allowed in times, "–" between them
SESSION_RE = re.compile(r"^\s*-\s+(\S+)\s+(\d{1,2})[.:](\d{2})\s*[-–]\s*"
                        r"(\d{1,2})[.:](\d{2})(?:\s+(.*?))?\s*$")
SESSION_SHAPE = "- <date> <start>-<end> [description]"
# the usage guide's examples, shown by a bare run and --help (no-args-usage-guide)
USAGE = """examples (settings come from config.yaml; a flag overrides one for that run):
  python main.py --run                              print the totals and problems
  python main.py --run --csv                        also write the CSV files to output
  python main.py --run --entries                    print every session too
  python main.py --run --period week,month          only weekly and monthly totals
  python main.py --run --sum this_week,last_week    this week's and last week's total
  python main.py --run --from 2026-01-01 --to 2026-12-31
  python main.py --run --input D:/notes/timelog.md  another log, this run only
  python main.py --run --csv --dry-run              show the run, write nothing

Without --run nothing is done. Log format and all settings: README.md"""

# -----------------------------------------------------------------------------------------
#                functions
# -----------------------------------------------------------------------------------------
def current_config() -> dict:
    """
    DEFAULTS merged with config.yaml (or config.example.yaml until it exists), read only.

    Feeds the "now:" values in --help, so it never prompts, writes or fails: a missing or
    broken file just leaves the defaults.
    """
    values = dict(DEFAULTS)
    for name in ("config.yaml", "config.example.yaml"):
        path = HERE / name
        if path.exists():
            try:
                values.update(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
            except (OSError, yaml.YAMLError):
                pass
            break
    return values


def build_parser(current: dict) -> argparse.ArgumentParser:
    """
    Defines the CLI; its help is the usage guide, showing the values --run would use.

    Flags default to None so unset ones don't override config.
    """
    def now(key: str) -> str:
        value = current.get(key)
        if isinstance(value, list):
            value = ",".join(str(v) for v in value)
        elif isinstance(value, bool):
            value = "on" if value else "off"
        return f" (now: {'none' if value in (None, '') else value})".replace("%", "%%")

    parser = argparse.ArgumentParser(
        description=__doc__.strip().splitlines()[0], epilog=USAGE,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run", action="store_true",
                        help="start a run with the settings below: config.yaml, "
                             "overridden by any flag given")
    parser.add_argument("--input",
                        help="a Markdown log, or a folder of them" + now("input"))
    parser.add_argument("--output",
                        help="folder for the CSV files" + now("output"))
    parser.add_argument("--pattern",
                        help="which files to read when input is a folder" + now("pattern"))
    parser.add_argument("--relative-to", choices=RELATIVE_TO,
                        help="base for relative paths: this tool's folder or the cwd"
                             + now("relative_to"))
    parser.add_argument("--period", dest="periods",
                        help=f"comma-separated totals: {', '.join(PERIODS)}"
                             + now("periods"))
    parser.add_argument("--sum",
                        help=f"comma-separated calendar windows to total from today, "
                             f"ignoring --from/--to: {', '.join(SUMS)}" + now("sum"))
    parser.add_argument("--date-formats",
                        help="comma-separated strptime formats" + now("date_formats"))
    parser.add_argument("--from", dest="date_from",
                        help="only sessions on or after this date" + now("date_from"))
    parser.add_argument("--to", dest="date_to",
                        help="only sessions on or before this date" + now("date_to"))
    parser.add_argument("--max-hours", dest="max_session_hours", type=float,
                        help="report sessions longer than this, 0 = never"
                             + now("max_session_hours"))
    parser.add_argument("--entries", dest="show_entries",
                        action=argparse.BooleanOptionalAction, default=None,
                        help="print every session with its duration" + now("show_entries"))
    parser.add_argument("--csv", dest="write_csv",
                        action=argparse.BooleanOptionalAction, default=None,
                        help="also write sessions/summary/problems.csv to the output "
                             "folder"
                             + now("write_csv"))
    parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=None,
                        help="write nothing, not even config.yaml (wins over --csv)"
                             + now("dry_run"))
    parser.add_argument("--ignore-problems", action=argparse.BooleanOptionalAction,
                        default=None,
                        help="print only the number of problems and exit 0; "
                             "problems.csv is still written" + now("ignore_problems"))
    return parser


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
    Merges settings: CLI flags > config.yaml > DEFAULTS, and checks them.

    Paths: an absolute "input"/"output" is used as-is; a relative one is resolved
    against this tool's folder (relative_to: tool) or the current working directory
    (relative_to: cwd).

    Returns:
        Settings with "input"/"output" as absolute Paths, "periods" as a list,
        "date_from"/"date_to" as dates or None.

    Raises:
        SystemExit: a setting has a value the tool can't use; the message names it.
    """
    settings = dict(DEFAULTS)
    config_file = ensure_config(bool(args.dry_run))
    if config_file:
        loaded = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
        settings.update(loaded)
    settings.update({k: v for k, v in vars(args).items() if v is not None and k != "run"})
    if settings["relative_to"] not in RELATIVE_TO:
        raise SystemExit(f"Invalid relative_to {settings['relative_to']!r}: "
                         "choose 'tool' or 'cwd'.")
    base = HERE if settings["relative_to"] == "tool" else Path.cwd()
    for key in ("input", "output"):
        path = Path(settings[key])
        settings[key] = path if path.is_absolute() else base / path
    formats = settings["date_formats"]
    if isinstance(formats, str):  # from --date-formats; a format never contains ","
        formats = settings["date_formats"] = [f.strip() for f in formats.split(",")
                                              if f.strip()]
    if not formats or not isinstance(formats, list):
        raise SystemExit("date_formats must be a list of formats, e.g. [\"%Y%m%d\"].")
    periods = settings["periods"]
    if isinstance(periods, str):
        periods = [p.strip() for p in periods.split(",") if p.strip()]
    unknown = [p for p in periods or [] if p not in PERIODS]
    if not periods or unknown:
        raise SystemExit(f"Invalid periods {unknown or periods!r}: "
                         f"choose from {', '.join(PERIODS)}.")
    settings["periods"] = [p for p in PERIODS if p in periods]  # fixed order, no repeats
    sums = settings["sum"] or []
    if isinstance(sums, str):
        sums = [s.strip() for s in sums.split(",") if s.strip()]
    unknown = [s for s in sums if s not in SUMS]
    if unknown:
        raise SystemExit(f"Invalid sum {unknown!r}: choose from {', '.join(SUMS)}.")
    settings["sum"] = list(dict.fromkeys(sums))  # your order, no repeats
    for key in ("date_from", "date_to"):
        value = settings[key]
        if value is None or isinstance(value, date):
            continue  # YAML already reads 2026-01-01 as a date
        settings[key] = parse_date(str(value), formats)
        if settings[key] is None:
            raise SystemExit(f"Invalid {key} {value!r}: use a format from date_formats.")
    return settings


def find_input_files(settings: dict) -> list[Path] | None:
    """The input file, or the folder's files matching the pattern; None if absent."""
    source = settings["input"]
    if source.is_file():
        return [source]
    if source.is_dir():
        return sorted(p for p in source.glob(settings["pattern"]) if p.is_file())
    return None


def parse_date(text: str, formats: list[str]) -> date | None:
    """A date in the first of the formats that fits (and 2026-01-01 always), or None."""
    for fmt in [*formats, "%Y-%m-%d"]:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None


def problem(path: Path, line: int, kind: str, message: str,
            day: date | None = None) -> dict:
    """
    One entry of the problem report; line 0 means the whole file.

    day: the line's date, if readable, so date_from/date_to can leave it out; a problem
    without one is always reported.
    """
    return {"file": path.name, "line": line, "kind": kind, "message": message, "date": day}


def parse_sessions(path: Path, formats: list[str]) -> tuple[list[dict], list[dict]]:
    """
    Reads one Markdown file.

    Returns:
        (sessions as dicts with file, line, date, start, end, minutes, description,
        begin; start/end in minutes after midnight, begin as a datetime),
        (problems: unreadable file, lines that look like sessions but don't parse).
    """
    try:
        # utf-8-sig: logs saved by Windows editors may start with a BOM
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeDecodeError) as error:
        return [], [problem(path, 0, "unreadable", f"file skipped: {error}")]
    sessions, problems = [], []
    for number, line in enumerate(lines, start=1):
        if not CANDIDATE_RE.match(line):
            continue
        match = SESSION_RE.match(line)
        if not match:
            words = line.split()
            day = parse_date(words[1], formats) if len(words) > 1 else None
            problems.append(problem(path, number, "malformed",
                                    f"not '{SESSION_SHAPE}': {line.strip()}", day))
            continue
        token, description = match.group(1), match.group(6) or ""
        day = parse_date(token, formats)
        times = [int(g) for g in match.groups()[1:5]]
        if day is None:
            problems.append(problem(path, number, "malformed",
                                    f"unknown date {token!r} (date_formats: "
                                    f"{', '.join(formats)}): {line.strip()}"))
            continue
        if times[0] > 23 or times[2] > 23 or times[1] > 59 or times[3] > 59:
            problems.append(problem(path, number, "malformed",
                                    f"invalid time: {line.strip()}", day))
            continue
        start, end = times[0] * 60 + times[1], times[2] * 60 + times[3]
        begin = datetime.combine(day, datetime.min.time()) + timedelta(minutes=start)
        sessions.append({"file": path.name, "line": number, "date": day, "start": start,
                         "end": end, "minutes": (end - start) % (24 * 60),
                         "description": description, "begin": begin})
    return sessions, problems


def check_sessions(sessions: list[dict], today: date) -> list[dict]:
    """
    Finds sessions that parse but are probably wrong; they still count in the totals.

    Args:
        sessions: the counted ones (overlong sessions already left out), sorted by begin.
        today: later dates are reported as future.
    """
    problems, seen, latest = [], {}, None

    def where(s: dict) -> str:
        span = f"{clock(s['start'])}-{clock(s['end'])}"
        return f"{s['file']}:{s['line']} ({s['date']} {span})"

    for s in sessions:
        path = Path(s["file"])
        key = (s["date"], s["start"], s["end"])
        finish = s["begin"] + timedelta(minutes=s["minutes"])
        if key in seen:
            problems.append(problem(path, s["line"], "duplicate",
                                    f"same as {where(seen[key])}"))
        elif latest and s["begin"] < latest[1]:
            problems.append(problem(path, s["line"], "overlap",
                                    f"overlaps {where(latest[0])}"))
        seen.setdefault(key, s)
        if latest is None or finish > latest[1]:
            latest = (s, finish)
        if s["minutes"] == 0:
            problems.append(problem(path, s["line"], "empty",
                                    "start equals end, counted as 0 minutes"))
        if s["date"] > today:
            problems.append(problem(path, s["line"], "future",
                                    f"{s['date']} is after today"))
    return problems


def in_range(day: date | None, settings: dict) -> bool:
    """Whether a date lies within date_from/date_to; no date can't be placed, so True."""
    low, high = settings["date_from"], settings["date_to"]
    if day is None:
        return True
    return (low is None or day >= low) and (high is None or day <= high)


def read_logs(files: list[Path],
              settings: dict) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """
    Parses every file, sets overlong sessions aside, keeps the rest inside
    date_from/date_to and checks them.

    A session longer than max_session_hours is most likely a typo, so it is never
    counted (totals, sums, sessions.csv); it is reported as a "long" problem instead.
    Problems follow the date range, so a filtered run isn't flooded with old ones: a
    malformed line with a readable date outside it is left out too. Lines whose date
    can't be read and unreadable files can't be placed, so they are always reported.

    Returns:
        (counted sessions inside the range sorted by begin, problems sorted by file and
        line, every counted session, for the sums that ignore the range, every
        overlong session, for the "not counted" notes).
    """
    sessions, problems = [], []
    for path in files:
        found, bad = parse_sessions(path, settings["date_formats"])
        sessions += found
        problems += bad
    limit = settings["max_session_hours"]
    too_long = [s for s in sessions if limit and s["minutes"] > limit * 60]
    counted = [s for s in sessions if not (limit and s["minutes"] > limit * 60)]
    kept = sorted((s for s in counted if in_range(s["date"], settings)),
                  key=lambda s: (s["begin"], s["file"], s["line"]))
    problems = [p for p in problems if in_range(p["date"], settings)]
    problems += [problem(Path(s["file"]), s["line"], "long",
                         f"{hours(s['minutes'])} is longer than max_session_hours "
                         f"({limit:g}), not counted")
                 for s in too_long if in_range(s["date"], settings)]
    problems += check_sessions(kept, date.today())
    problems.sort(key=lambda p: (p["file"], p["line"]))
    return kept, problems, counted, too_long


def hours(minutes: int) -> str:
    """Minutes as "h:mm", e.g. 135 -> "2:15"."""
    return f"{minutes // 60}:{minutes % 60:02d}"


def clock(minutes: int) -> str:
    """Minutes after midnight as "HH:MM", e.g. 75 -> "01:15"."""
    return hours(minutes).zfill(5)


def period_of(day: date, kind: str) -> str:
    """The period label a date falls in, e.g. 2025-09-27 -> 2025-W39 for "week"."""
    if kind == "day":
        return day.isoformat()
    if kind == "week":
        iso = day.isocalendar()
        return f"{iso.year}-W{iso.week:02d}"
    if kind == "month":
        return day.strftime("%Y-%m")
    if kind == "year":
        return str(day.year)
    return "all"


def summarize(sessions: list[dict], periods: list[str]) -> list[tuple[str, str, int, int]]:
    """Totals as (kind, period, sessions, minutes), grouped in the order of periods."""
    totals: dict[tuple[str, str], list[int]] = {}
    for s in sessions:
        for kind in periods:
            total = totals.setdefault((kind, period_of(s["date"], kind)), [0, 0])
            total[0] += 1
            total[1] += s["minutes"]
    order = {kind: i for i, kind in enumerate(periods)}
    ranked = sorted(totals.items(), key=lambda item: (order[item[0][0]], item[0][1]))
    return [(kind, period, n, m) for (kind, period), (n, m) in ranked]


def sum_window(name: str, today: date) -> tuple[date | None, date | None]:
    """
    First and last day of a calendar window around today; (None, None) for "all".

    Weeks run Monday to Sunday; "this_" is the current day, week, month or year,
    "last_" the whole previous one.
    """
    if name == "all":
        return None, None
    last = name.startswith("last_")
    unit = name.split("_", 1)[1]  # this_week / last_week -> week
    if unit == "day":
        first = today - timedelta(days=1 if last else 0)
        return first, first
    if unit == "week":
        first = today - timedelta(days=today.weekday() + (7 if last else 0))
        return first, first + timedelta(days=6)
    if unit == "month":
        first = today.replace(day=1)
        if last:
            first = (first - timedelta(days=1)).replace(day=1)
        after = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
        return first, after - timedelta(days=1)
    year = today.year - (1 if last else 0)
    return date(year, 1, 1), date(year, 12, 31)


def section(title: str) -> None:
    """A blank line and a "=== TITLE ===...===" header, so each output block stands out."""
    print(f"\n=== {title} ".ljust(60, "="))


def print_details(sessions: list[dict], problems: list[dict], settings: dict) -> None:
    """Prints the sessions (if asked) and the problems, or only their count."""
    if settings["show_entries"]:
        print("Sessions:")
        for s in sessions:
            print(f"  {s['date']}  {clock(s['start'])}-{clock(s['end'])}  "
                  f"{hours(s['minutes']):>6}  {s['description']}".rstrip())
    if problems and settings["ignore_problems"]:
        print(f"{len(problems)} problem(s) ignored (ignore_problems; "
              "--no-ignore-problems lists them)")
    elif problems:
        print(f"Problems ({len(problems)}):")
        for p in problems:
            print(f"  {p['file']}:{p['line']}: {p['kind']}: {p['message']}")


def ignored_note(sessions: list[dict]) -> str:
    """
    "1 ignored: 19:33 over max_session_hours, possible mistake", or "" if there are none.

    Lists up to three durations, so the gap in a total can be traced back to the log.
    """
    if not sessions:
        return ""
    listed = ", ".join(hours(s["minutes"]) for s in sessions[:3])
    more = f", +{len(sessions) - 3} more" if len(sessions) > 3 else ""
    return (f"{len(sessions)} ignored: {listed}{more} over max_session_hours, "
            "possible mistake")


def print_totals(sessions: list[dict], summary: list[tuple], file_count: int,
                 skipped: int, too_long: list[dict], settings: dict) -> None:
    """
    Prints the TOTALS block: what was counted, then the totals per period.

    Its first lines name the date range, how many sessions it left out and which
    overlong ones were ignored; each period row says what it ignored too, and a period
    holding only ignored sessions still gets a row. So a low or empty total reads as
    "filtered" or "possible mistake", not as "broken"; shown even with ignore_problems.
    """
    low, high = settings["date_from"], settings["date_to"]
    scope = (f" from {low} to {high}" if low and high else f" from {low}" if low
             else f" up to {high}" if high else "")
    section("TOTALS")
    total = sum(s["minutes"] for s in sessions)
    print(f"{len(sessions)} sessions in {file_count} file(s){scope}, total {hours(total)}")
    if skipped:
        print(f"({skipped} outside the range skipped)")
    ignored = [s for s in too_long if in_range(s["date"], settings)]
    if ignored:
        dates = ", ".join(f"{s['date']} {hours(s['minutes'])}" for s in ignored[:3])
        more = f", +{len(ignored) - 3} more" if len(ignored) > 3 else ""
        print(f"({len(ignored)} ignored as a possible mistake, over max_session_hours: "
              f"{dates}{more})")
    rows = {(kind, period): (n, m) for kind, period, n, m in summary}
    ignored_in: dict[tuple[str, str], list[dict]] = {}
    for s in ignored:
        for kind in settings["periods"]:
            key = (kind, period_of(s["date"], kind))
            ignored_in.setdefault(key, []).append(s)
            rows.setdefault(key, (0, 0))
    order = {kind: i for i, kind in enumerate(settings["periods"])}
    kind_shown = None
    for kind, period in sorted(rows, key=lambda key: (order[key[0]], key[1])):
        count, minutes = rows[(kind, period)]
        label = "session" if count == 1 else "sessions"
        note = ignored_note(ignored_in.get((kind, period), []))
        detail = f"({count} {label}{'; ' + note if note else ''})"
        if kind == "all":
            print(f"  {'all':<12} {hours(minutes):>7}  {detail}")
            continue
        if kind != kind_shown:
            print(f"  per {kind}:")
            kind_shown = kind
        print(f"    {period:<10} {hours(minutes):>7}  {detail}")


def print_sums(sessions: list[dict], too_long: list[dict], names: list[str],
               today: date) -> None:
    """
    Prints the SUM block, last: one line per window with its dates, total and count.

    A window that holds overlong sessions says which it ignored.
    """
    if not names:
        return
    section(f"SUM (calendar, today {today}, ignores range)")
    for name in names:
        first, final = sum_window(name, today)

        def inside(group: list[dict]) -> list[dict]:
            return [s for s in group if (first is None or s["date"] >= first)
                    and (final is None or s["date"] <= final)]

        counted, note = inside(sessions), ignored_note(inside(too_long))
        span = f"{first} to {final}" if first else "every session"
        label = "session" if len(counted) == 1 else "sessions"
        print(f"  {name:<11} {span:<24} "
              f"{hours(sum(s['minutes'] for s in counted)):>7}  "
              f"({len(counted)} {label}{'; ' + note if note else ''})")


def write_results(sessions: list[dict], summary: list[tuple], problems: list[dict],
                  output: Path) -> None:
    """
    Writes sessions.csv, summary.csv and problems.csv into output, overwriting them.

    problems.csv is written even when empty, so one left by an earlier run never
    suggests problems that are already fixed.
    """
    output.mkdir(parents=True, exist_ok=True)
    with open(output / "sessions.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "start", "end", "minutes", "hours", "description",
                         "file", "line"])
        for s in sessions:
            writer.writerow([s["date"].isoformat(), clock(s["start"]), clock(s["end"]),
                             s["minutes"], hours(s["minutes"]), s["description"],
                             s["file"], s["line"]])
    with open(output / "summary.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["kind", "period", "sessions", "minutes", "hours"])
        writer.writerows((k, p, n, m, hours(m)) for k, p, n, m in summary)
    with open(output / "problems.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "line", "kind", "message"],
                                extrasaction="ignore")  # "date" is only for the range
        writer.writeheader()
        writer.writerows(problems)
    print(f"Saved sessions.csv, summary.csv and problems.csv in {output}")

# -----------------------------------------------------------------------------------------
#                main
# -----------------------------------------------------------------------------------------
def main(argv: list[str]) -> int:
    # 1. Without --run: the usage guide (same as --help), never work
    parser = build_parser(current_config())
    args = parser.parse_args(argv)
    if not args.run:
        parser.print_help()
        if argv:
            print("\nNothing run: add --run to start, e.g. python main.py --run "
                  + " ".join(argv))
        return 2 if argv else 0
    # 2.-3. Settings (config.yaml offered on the first real run)
    settings = load_settings(args)
    # 4. Input files
    files = find_input_files(settings)
    if files is None:
        print(f"Input not found: {settings['input']}")
        return 1
    # 5. Parse and check
    sessions, problems, every_session, too_long = read_logs(files, settings)
    # 6. Sessions (if asked) and problems
    print_details(sessions, problems, settings)
    # 7. CSV files, only on request
    summary = summarize(sessions, settings["periods"])
    if not settings["write_csv"]:
        print("No CSV written (use --csv or write_csv: true to save them).")
    elif settings["dry_run"]:
        print("Dry run: nothing written.")
    else:
        write_results(sessions, summary, problems, settings["output"])
    # 8. Totals, then the sums last
    print_totals(sessions, summary, len(files), len(every_session) - len(sessions),
                 too_long, settings)
    print_sums(every_session, too_long, settings["sum"], date.today())
    # 9. Exit code
    return 1 if problems and not settings["ignore_problems"] else 0


# -----------------------------------------------------------------------------------------
#                start
# -----------------------------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
