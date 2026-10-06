# -----------------------------------------------------------------------------------------
#   author          : Kutay Coskuner
#   ai-contributors : Claude Opus 5.5 (claude-opus-5-5)
#   last update     : 2026-10-06
#   template        : 3.2.0
#   disclaimer      : Provided as is, without warranty of any kind; use at your own risk.
#                     Check outputs before relying on them.
# -----------------------------------------------------------------------------------------
"""
Posture reminder: flashes a text on the screen at a fixed interval.

Shows a short message (default "Dik dur!") in borderless, always-on-top windows for a
few seconds, every N minutes, as a reminder to sit or stand straight at the computer.
As shipped: outlined text only, no box, centered above the bottom edge of the screen.
Position, font, outline and an optional background box (color and opacity, which never
fades the text) are settings. Clicking it or pressing Esc hides it early; Ctrl+C in the
terminal stops the tool.

1. Bare run prints this guide and exits (no-args-usage-guide).
2. The first real run offers to create config.yaml from config.example.yaml
   (ensure_config); later runs compare its keys with config.example.yaml's and offer
   to update it when they differ (update_config).
3. Settings come from CLI flags > config.yaml > DEFAULTS (load_settings).
4. The reminder loop runs until Ctrl+C or until `count` reminders were shown (run).

Requires: this folder's .venv (pip install -r requirements.txt); tkinter, which ships
with the python.org installers (on Linux: the python3-tk package). config.yaml is
gitignored and personal; the committed defaults live in config.example.yaml.

Inputs -> outputs: settings -> a reminder window on the primary screen; no files written
(except config.yaml, after asking).

Run:
    python main.py --run                     remind every 20 minutes, until Ctrl+C
    python main.py --once                    flash once right now, to check the look
    python main.py --run --interval 30 --duration 8 --message "Stand up!"
    python main.py --once --anchor center --offset-x 40 --offset-y 40
                                             40 px right of and 40 px above the center
    python main.py --once --anchor top-right --offset-x -40 --offset-y -40
                   --background-opacity 0.5 --outline-width 0
                                             half-faded red box, 40 px in from the corner
    python main.py --list-fonts              installed font names for font_family
    python main.py --help                    all flags; see README.md
"""

# -----------------------------------------------------------------------------------------
#                libraries
# -----------------------------------------------------------------------------------------
import argparse
import json
import re
import shutil
import sys
import tkinter as tk
import tkinter.font as tkfont
from datetime import datetime, timedelta
from pathlib import Path

import yaml

# -----------------------------------------------------------------------------------------
#                variables
# -----------------------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
DEFAULTS = {"message": "Dik dur!", "interval_minutes": 20, "duration_seconds": 5,
            "count": 0, "anchor": "bottom", "offset_x": 0, "offset_y": 160,
            "font_family": "Linux Libertine G", "font_size": 72, "font_bold": True,
            "font_italic": False, "text_color": "#ffffff", "outline_width": 2,
            "outline_color": "#000000", "background_color": "#c0392b", "padding": 40,
            "background_opacity": 0}
ANCHORS = ("center", "top", "bottom", "left", "right",
           "top-left", "top-right", "bottom-left", "bottom-right")
# Painted where the text window should be see-through when there's no box. Anti-aliased
# text edges blend towards it, so it's near-black: the fringe reads as a shadow.
TRANSPARENT_KEY = "#010203"
POLL_MS = 250  # lets Python see Ctrl+C while tkinter's mainloop is waiting

# -----------------------------------------------------------------------------------------
#                functions
# -----------------------------------------------------------------------------------------
def parse_args(argv: list[str]) -> argparse.Namespace:
    """Defines the CLI; flags default to None so unset ones don't override config."""
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--run", action="store_true", help="run with config defaults")
    parser.add_argument("--once", action="store_true",
                        help="flash one reminder right away, then exit")
    parser.add_argument("--message", help="text to show (default: Dik dur!)")
    parser.add_argument("--interval", dest="interval_minutes", type=float,
                        help="minutes between reminders (default: 20)")
    parser.add_argument("--duration", dest="duration_seconds", type=float,
                        help="seconds each reminder stays visible (default: 5)")
    parser.add_argument("--count", type=int,
                        help="stop after this many reminders; 0 = until Ctrl+C")
    parser.add_argument("--anchor", type=str.lower, choices=ANCHORS,
                        help="screen point the text is placed from (default: bottom)")
    parser.add_argument("--offset-x", dest="offset_x", type=int,
                        help="pixels from the anchor; positive = right (default: 0)")
    parser.add_argument("--offset-y", dest="offset_y", type=int,
                        help="pixels from the anchor; positive = up (default: 160)")
    parser.add_argument("--font-family", dest="font_family",
                        help="font name (default: Linux Libertine G); see --list-fonts")
    parser.add_argument("--font-size", dest="font_size", type=int,
                        help="text size in points (default: 72)")
    parser.add_argument("--text-color", dest="text_color",
                        help="color name or #rrggbb (default: #ffffff)")
    parser.add_argument("--outline-width", dest="outline_width", type=int,
                        help="text outline in pixels; 0 = none (default: 2)")
    parser.add_argument("--outline-color", dest="outline_color",
                        help="color name or #rrggbb (default: #000000)")
    parser.add_argument("--background-color", dest="background_color",
                        help="box color name or #rrggbb (default: #c0392b)")
    parser.add_argument("--background-opacity", dest="background_opacity", type=float,
                        help="box only, never the text: 0 = no box, 1 = solid (default: 0)")
    parser.add_argument("--list-fonts", action="store_true",
                        help="print the installed font names, then exit")
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
            print(f"Created {config.name}; edit it to use your own settings.")
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

    Returns:
        Settings, with --once turned into count 1 and no initial wait.

    Raises:
        SystemExit: a number is out of range or the anchor is unknown.
    """
    settings = dict(DEFAULTS)
    config_file = ensure_config(dry_run=False)  # this tool has no dry run
    if config_file:
        loaded = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
        settings.update(loaded)
    settings.update({k: v for k, v in vars(args).items()
                     if v is not None and k not in ("run", "once", "list_fonts")})
    settings["once"] = args.once
    if args.once:
        settings["count"] = 1
    if settings["interval_minutes"] <= 0 or settings["duration_seconds"] <= 0:
        raise SystemExit("interval_minutes and duration_seconds must be greater than 0.")
    if settings["duration_seconds"] >= settings["interval_minutes"] * 60:
        raise SystemExit("duration_seconds must be shorter than the interval.")
    if settings["count"] < 0:
        raise SystemExit("count must be 0 (until Ctrl+C) or more.")
    if str(settings["background_color"]).lower() == "transparent":
        settings["background_opacity"] = 0  # the older spelling of "no box"
    if not 0 <= settings["background_opacity"] <= 1:
        raise SystemExit("background_opacity must be between 0 (no box) and 1 (solid).")
    if min(settings["padding"], settings["outline_width"]) < 0:
        raise SystemExit("padding and outline_width must be 0 or more.")
    settings["anchor"] = str(settings["anchor"]).lower()
    if settings["anchor"] not in ANCHORS:
        raise SystemExit(f"Invalid anchor {settings['anchor']!r}: use "
                         f"{', '.join(ANCHORS)}.")
    for key in ("offset_x", "offset_y"):
        if not isinstance(settings[key], int) or isinstance(settings[key], bool):
            raise SystemExit(f"{key} must be a whole number of pixels, "
                             f"not {settings[key]!r}.")
    return settings


def list_fonts() -> None:
    """Prints the font families tkinter can use, one per line."""
    root = tk.Tk()
    root.withdraw()
    # Windows also lists vertical variants as "@Name"; they're not useful here
    for family in sorted({f for f in tkfont.families(root) if not f.startswith("@")}):
        print(family)
    root.destroy()


def see_through_color(window: tk.Toplevel, box_color: str | None) -> str | None:
    """
    Makes one color of a window see-through, where the windowing system allows it.

    On Windows the key color is the box's color when there is a box, so the letters'
    anti-aliased edges blend towards it and show no dark fringe on the box; without a
    box it's TRANSPARENT_KEY.

    Returns:
        The color to paint the window's empty space with, or None on X11, which can't
        make part of a window see-through.
    """
    system = window.tk.call("tk", "windowingsystem")
    if system == "win32":
        key = box_color or TRANSPARENT_KEY
        window.attributes("-transparentcolor", key)
        return key
    if system == "aqua":
        window.attributes("-transparent", True)
        return "systemTransparent"
    return None


def hide(windows: list[tk.Toplevel]) -> None:
    """Hides the reminder (all its windows)."""
    for window in windows:
        window.withdraw()


def build_window(settings: dict) -> tuple[tk.Tk, list[tk.Toplevel]]:
    """
    Creates the hidden reminder: a background box with a solid text window on top.

    tkinter's opacity applies to a whole window, so fading only the background takes
    two borderless, always-on-top windows of the same size and place: the box, a plain
    color at background_opacity (none at 0), and the text window, solid, with its empty
    space see-through. The text is drawn on a canvas: first the outline (the text
    repeated at every offset within outline_width), then the text. Clicking either
    window or pressing Esc hides both early; flash() places and shows them. On X11,
    which can't make part of a window see-through, one solid box is used (with a
    warning rather than a silent fallback).

    Returns:
        (the hidden root that runs the event loop, the windows to show, box first).
    """
    root = tk.Tk()
    root.withdraw()
    opacity = settings["background_opacity"]
    box_color = settings["background_color"] if opacity > 0 else None
    windows: list[tk.Toplevel] = []
    for _ in range(2 if box_color else 1):
        window = tk.Toplevel(root)
        window.withdraw()
        window.overrideredirect(True)  # no title bar or border
        window.attributes("-topmost", True)
        windows.append(window)
    text_window = windows[-1]
    background = see_through_color(text_window, box_color)
    if background is None:
        print("A see-through background isn't supported on this system (X11); "
              "using a solid box instead.")
        background = box_color or "#000000"
        if box_color:
            windows.pop(0).destroy()
    elif box_color:
        windows[0].attributes("-alpha", opacity)
        windows[0].configure(bg=box_color)
    if settings["font_family"] not in tkfont.families(root):
        print(f"Font {settings['font_family']!r} not found; tkinter uses its default "
              "font instead. See: python main.py --list-fonts")
    font = tkfont.Font(root=root, family=settings["font_family"],
                       size=settings["font_size"],
                       weight="bold" if settings["font_bold"] else "normal",
                       slant="italic" if settings["font_italic"] else "roman")
    message, outline = str(settings["message"]), settings["outline_width"]
    lines = message.splitlines() or [""]
    pad = settings["padding"] if box_color else 0
    width = max(font.measure(line) for line in lines) + 2 * (pad + outline)
    height = font.metrics("linespace") * len(lines) + 2 * (pad + outline)
    canvas = tk.Canvas(text_window, width=width, height=height, bg=background,
                       highlightthickness=0)
    canvas.pack()
    text_window.configure(bg=background)
    text = {"text": message, "font": font, "justify": "center"}
    for dx in range(-outline, outline + 1):
        for dy in range(-outline, outline + 1):
            if (dx or dy) and dx * dx + dy * dy <= outline * outline:  # round outline
                canvas.create_text(width / 2 + dx, height / 2 + dy,
                                   fill=settings["outline_color"], **text)
    canvas.create_text(width / 2, height / 2, fill=settings["text_color"], **text)
    for widget in (*windows, canvas):
        widget.bind("<Button-1>", lambda _e: hide(windows))
    text_window.bind("<Escape>", lambda _e: hide(windows))
    return root, windows


def window_origin(anchor: str, offset: tuple[int, int], size: tuple[int, int],
                  screen: tuple[int, int]) -> tuple[int, int]:
    """
    Returns the window's top-left corner on the primary screen.

    The anchor is a point on the screen, and the window's matching point sits on it:
    "center" puts the window's center on the screen's center, "top-left" its top-left
    corner on the screen's top-left corner, "top" its top edge's middle on the screen's.
    The offset then moves it from there: positive x = right, positive y = up, for every
    anchor (so from "top-right", (-40, -40) moves 40 px inwards on both axes).
    """
    (offset_x, offset_y), (width, height), (screen_w, screen_h) = offset, size, screen
    x = (0 if "left" in anchor else
         screen_w - width if "right" in anchor else (screen_w - width) // 2)
    y = (0 if "top" in anchor else
         screen_h - height if "bottom" in anchor else (screen_h - height) // 2)
    return x + offset_x, y - offset_y  # screen y grows downwards, offset_y upwards


def flash(windows: list[tk.Toplevel], duration_ms: int, settings: dict) -> None:
    """Shows the reminder at its anchor and offset, then hides it after duration_ms."""
    text_window = windows[-1]
    text_window.update_idletasks()
    width, height = text_window.winfo_reqwidth(), text_window.winfo_reqheight()
    x, y = window_origin(settings["anchor"], (settings["offset_x"], settings["offset_y"]),
                         (width, height),
                         (text_window.winfo_screenwidth(), text_window.winfo_screenheight()))
    for window in windows:  # box first, so the text window ends up on top
        window.geometry(f"{width}x{height}{x:+d}{y:+d}")  # e.g. +-40: negative x is valid
        window.deiconify()
        window.lift()
    text_window.focus_force()  # so Esc reaches it
    text_window.after(duration_ms, hide, windows)


def run(settings: dict) -> None:
    """
    Shows the reminder every interval_minutes, for duration_seconds each time.

    Stops after `count` reminders (0 = never) or on Ctrl+C. With --once the single
    reminder is shown right away instead of after the first interval.
    """
    interval_ms = round(settings["interval_minutes"] * 60_000)
    duration_ms = round(settings["duration_seconds"] * 1000)
    count = settings["count"]
    root, windows = build_window(settings)
    shown = 0

    def next_reminder(delay_ms: int) -> None:
        at = datetime.now() + timedelta(milliseconds=delay_ms)
        print(f"next reminder at {at:%H:%M:%S}")
        root.after(delay_ms, remind)

    def remind() -> None:
        nonlocal shown
        shown += 1
        print(f"[{datetime.now():%H:%M:%S}] reminder {shown}"
              + (f"/{count}" if count else ""))
        flash(windows, duration_ms, settings)
        if count and shown >= count:
            root.after(duration_ms + 100, root.quit)  # let the last one finish showing
            return
        next_reminder(interval_ms)

    def poll() -> None:
        root.after(POLL_MS, poll)

    print(f"message : {settings['message']}")
    if settings["once"]:
        print(f"once    : now, shown for {settings['duration_seconds']} s")
        root.after(0, remind)
    else:
        print(f"every   : {settings['interval_minutes']} min, "
              f"shown for {settings['duration_seconds']} s")
        print("stop    : Ctrl+C" + (f" (or after {count} reminder"
                                     f"{'s' if count > 1 else ''})" if count else ""))
        next_reminder(interval_ms)
    poll()
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        root.destroy()

# -----------------------------------------------------------------------------------------
#                main
# -----------------------------------------------------------------------------------------
def main(argv: list[str]) -> int:
    # 1. No arguments: usage guide only, never work (no-args-usage-guide)
    if not argv:
        print(__doc__.strip())
        return 0
    args = parse_args(argv)
    if args.list_fonts:  # a lookup, not a run: no config prompt
        list_fonts()
        return 0
    # 2.-3. Settings from CLI, config.yaml (offered on the first real run), defaults
    settings = load_settings(args)
    # 4. Work
    run(settings)
    return 0


# -----------------------------------------------------------------------------------------
#                start
# -----------------------------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
