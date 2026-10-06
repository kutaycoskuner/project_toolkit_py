# -----------------------------------------------------------------------------------------
#   author          : Kutay Coskuner
#   ai-contributors : unknown (before 2026-10-04), Claude Opus 5.5 (claude-opus-5-5)
#   last update     : 2026-10-06
#   template        : 3.2.0
#   disclaimer      : Provided as is, without warranty of any kind; use at your own risk.
#                     Check outputs before relying on them.
# -----------------------------------------------------------------------------------------
"""
Timing-curve visualizer: plays a wait -> expand -> wait -> collapse value cycle in real
time and plots it, to find a timing function for animations.

The cycle (one sample every `sample_interval` seconds):
    waiting0  value 0 for `waiting_delay` s
    expand    |tan(t)| rises until it passes `cap`
    waiting1  value `cap` for `waiting_delay` s
    collapse  |tan(t)| falls until it drops below `floor`, then back to waiting0
With the defaults one full cycle takes about 5 s.

1. Bare run prints this guide and exits (no-args-usage-guide).
2. The first real run offers to create config.yaml from config.example.yaml
   (ensure_config); later runs compare its keys with config.example.yaml's and offer
   to update it when they differ (update_config).
3. Settings come from CLI flags > config.yaml > DEFAULTS (load_settings).
4. The cycle runs for `duration` seconds of wall-clock time, printing each sample as
   "<value> <unix seconds>" (simulate).
5. With `output` set, the samples are saved as samples.csv and the plot as graph.png
   (save_results); a dry run saves nothing.
6. With `plot` on, the plot opens in a window (show_plot).

Requires: this folder's .venv (pip install -r requirements.txt); a display for the plot
window (or --no-plot). config.yaml is gitignored. No .env: the tool needs no secrets.

Inputs -> outputs: config -> console samples, optional example/output/graph.png and
samples.csv, optional plot window. As shipped, config.example.yaml runs one ~6 s cycle
and writes into example/output/.

Run:
    python main.py --run                         one cycle, saved to example/output/
    python main.py --run --no-plot               same, without opening a window
    python main.py --run --duration 20 --dry-run 20 s, console only, nothing saved
    python main.py --run --output D:/graphs      save graph.png and samples.csv there
    python main.py --help                        all flags; see README.md

Gotchas:
    - it runs in real time: the command blocks for `duration` seconds.
    - the x axis is the Unix time of each sample, not seconds since start.
    - a cap far above ~2000 needs a smaller sample_interval, or expand can skip past it
      between samples and the curve looks flat.
"""

# -----------------------------------------------------------------------------------------
#                libraries
# -----------------------------------------------------------------------------------------
import argparse
import csv
import json
import math
import re
import shutil
import sys
import time
from pathlib import Path

import yaml

# -----------------------------------------------------------------------------------------
#                variables
# -----------------------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
DEFAULTS = {"duration": 20, "waiting_delay": 1, "cap": 2000, "floor": 0.1,
            "sample_interval": 0.1, "plot": True, "output": "", "relative_to": "tool",
            "dry_run": False}
RELATIVE_TO = ("tool", "cwd")

# -----------------------------------------------------------------------------------------
#                functions
# -----------------------------------------------------------------------------------------
def parse_args(argv: list[str]) -> argparse.Namespace:
    """Defines the CLI; flags default to None so unset ones don't override config."""
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--run", action="store_true", help="run with config defaults")
    parser.add_argument("--duration", type=float, help="seconds to run (default: 20)")
    parser.add_argument("--plot", action=argparse.BooleanOptionalAction, default=None,
                        help="open the plot window (--no-plot: console and files only)")
    parser.add_argument("--output",
                        help='folder for graph.png and samples.csv ("" = save nothing)')
    parser.add_argument("--relative-to", choices=RELATIVE_TO,
                        help="base for relative paths: this tool's folder or the cwd")
    parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=None,
                        help="run and print, but save nothing")
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

    Paths: an absolute "output" is used as-is; a relative one is resolved against this
    tool's folder (relative_to: tool) or the current working directory (relative_to: cwd).

    Returns:
        Settings; "output" is an absolute Path, or None when nothing is to be saved.

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
    output = Path(settings["output"]) if settings["output"] else None
    settings["output"] = None if output is None else (
        output if output.is_absolute() else base / output)
    return settings


def simulate(settings: dict) -> tuple[list[float], list[float]]:
    """
    Runs the cycle in real time, printing "<value> <unix seconds>" per sample.

    Returns:
        (sample times as Unix seconds, sample values).
    """
    cap, floor, delay = settings["cap"], settings["floor"], settings["waiting_delay"]
    graph_x, graph_y = [], []
    difference = -1
    time_pin = time.time()
    time_print_delay = time_pin
    end_time = time.time() + settings["duration"]
    mod = "waiting0"

    while time.time() < end_time:
        value = 0.0
        if mod == "waiting0":
            if time.time() > time_pin + delay:
                difference = time.time() - time_pin
                mod = "expand"
        elif mod == "expand":
            value = abs(math.tan(time.time() - difference))
            if value > cap:
                value = cap
                time_pin = time.time()
                mod = "waiting1"
        elif mod == "waiting1":
            value = cap
            if time.time() > time_pin + delay:
                difference = time.time() - time_pin
                mod = "collapse"
        elif mod == "collapse":
            value = abs(math.tan(time.time() - difference))
            if value < floor:
                value = 0.0
                time_pin = time.time()
                mod = "waiting0"

        if time.time() > time_print_delay + settings["sample_interval"]:
            time_print_delay = time.time()
            print(f"{value:.4f}", int(time.time()))
            graph_x.append(time.time())
            graph_y.append(value)

    return graph_x, graph_y


def draw(plt, x: list[float], y: list[float]) -> None:
    """Draws value over time onto the current matplotlib figure."""
    plt.plot(x, y, label="time - value")
    plt.xlabel("X-axis")
    plt.ylabel("Y-axis")


def save_results(x: list[float], y: list[float], output: Path) -> None:
    """Writes samples.csv (unix_time, value) and graph.png into output, overwriting."""
    import matplotlib
    matplotlib.use("Agg")  # file only: no window, works without a display
    import matplotlib.pyplot as plt

    output.mkdir(parents=True, exist_ok=True)
    with open(output / "samples.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["unix_time", "value"])
        writer.writerows((f"{t:.4f}", f"{v:.6f}") for t, v in zip(x, y))
    draw(plt, x, y)
    plt.savefig(output / "graph.png", dpi=120)
    plt.close()
    print(f"Saved {output / 'samples.csv'} and {output / 'graph.png'}")


def show_plot(x: list[float], y: list[float]) -> None:
    """Shows value over time in a blocking matplotlib window."""
    import matplotlib.pyplot as plt  # imported here so --no-plot runs without a display

    draw(plt, x, y)
    plt.show()

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
    # 4. Simulate
    x, y = simulate(settings)
    # 5. Save
    if settings["output"] is not None:
        if settings["dry_run"]:
            print(f"Dry run: nothing saved to {settings['output']}")
        else:
            save_results(x, y, settings["output"])
    # 6. Plot window
    if settings["plot"]:
        show_plot(x, y)
    return 0


# -----------------------------------------------------------------------------------------
#                start
# -----------------------------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
