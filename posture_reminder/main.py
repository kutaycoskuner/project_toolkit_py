# -----------------------------------------------------------------------------------------
#   author          : Kutay Coskuner
#   ai-contributors : Claude Opus 5.5 (claude-opus-5-5)
#   last update     : 2026-10-07
#   template        : 3.2.0
#   disclaimer      : Provided as is, without warranty of any kind; use at your own risk.
#                     Check outputs before relying on them.
# -----------------------------------------------------------------------------------------
"""
Posture reminder: flashes a text on the screen at a fixed interval.

Shows a short message (default "Dik dur!") in borderless, always-on-top windows for a
few seconds, every N minutes, as a reminder to sit or stand straight at the computer.
As shipped: outlined text only, no box, centered above the bottom edge of every screen
(all_screens; Windows, other systems use the primary screen).
Position, font, outline and an optional background box (color and opacity, which never
fades the text) are settings. Clicking it or pressing Esc hides it early. A tray icon
turns reminders off and on, shows one now, toggles the start at login (Windows) and
quits; Ctrl+C in the terminal also stops the tool.

1. Bare run prints this guide and exits (no-args-usage-guide).
2. The first real run offers to create config.yaml from config.example.yaml
   (ensure_config); later runs compare its keys with config.example.yaml's and offer
   to update it when they differ (update_config).
3. Settings come from CLI flags > config.yaml > DEFAULTS (load_settings).
4. The reminder loop runs until Ctrl+C or until `count` reminders were shown (run).

Requires: this folder's .venv (pip install -r requirements.txt: PyYAML, and pystray +
Pillow for the tray icon); tkinter, which ships with the python.org installers (on
Linux: the python3-tk package). config.yaml is
gitignored and personal; the committed defaults live in config.example.yaml.

Inputs -> outputs: settings -> a reminder on every screen (or the primary one); no files written
(except config.yaml, after asking).

Run:
    python main.py --run                     remind every interval_minutes, with a tray icon;
                                             run at every login: start_with_windows: true
                                             in config.yaml, or tray > Start with Windows
    python main.py --once                    flash once right now, to check the look
    python main.py --run --interval 30 --duration 8 --message "Stand up!"
    python main.py --once --primary-only     only on the primary screen, not on every one
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
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import tkinter as tk
import tkinter.font as tkfont
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:  # imported where used, so --no-tray runs without them
    import pystray
    from PIL import Image

# -----------------------------------------------------------------------------------------
#                variables
# -----------------------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
DEFAULTS = {"message": "Dik dur!", "interval_minutes": 8, "duration_seconds": 1,
            "count": 0, "start_blinks": 2, "tray": True,
            "tray_icon": "assets/icon-four_cubes.png",
            "start_with_windows": False, "all_screens": True,
            "anchor": "bottom", "offset_x": 0, "offset_y": 160,
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
BLINK_ON_MS, BLINK_OFF_MS = 400, 300  # start_blinks: visible / hidden time per blink
TRAY_NAME = "Posture reminder"
# Windows runs every shortcut in this folder at login; tray > Start with Windows
# creates or deletes this one
STARTUP_LINK = (Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows"
                / "Start Menu" / "Programs" / "Startup" / f"{TRAY_NAME}.lnk")

# -----------------------------------------------------------------------------------------
#                functions
# -----------------------------------------------------------------------------------------
def peek_settings() -> tuple[dict, str]:
    """
    Reads the current settings for the usage guide and --help: read-only, no prompts.

    Returns:
        (DEFAULTS merged with config.yaml, or with config.example.yaml until
        config.yaml exists; the name of the file they came from).
    """
    settings = dict(DEFAULTS)
    for name in ("config.yaml", "config.example.yaml"):
        path = HERE / name
        if path.exists():
            try:
                settings.update(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
            except yaml.YAMLError:
                return settings, f"{name} (unreadable, code defaults shown)"
            return settings, name
    return settings, "code defaults"


def usage_summary() -> str:
    """One paragraph with the current settings, appended to the bare-run usage guide."""
    s, source = peek_settings()
    return (f"Current settings ({source}):\n"
            f"    every {s['interval_minutes']} min, shown {s['duration_seconds']} s, "
            f"{s['start_blinks']} start blinks, tray {'on' if s['tray'] else 'off'}, "
            f"start with Windows {'on' if s['start_with_windows'] else 'off'}\n"
            f"    {s['message']!r} at {s['anchor']} {s['offset_x']:+d}/{s['offset_y']:+d} px, "
            f"{s['font_family']} {s['font_size']} pt, outline {s['outline_width']} px, "
            f"box opacity {s['background_opacity']}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    """
    Defines the CLI; flags default to None so unset ones don't override config.

    The help texts show each setting's current value from config.yaml (see
    peek_settings), so --help matches what a run would use.
    """
    now, source = peek_settings()
    now = {k: str(v).replace("%", "%%") for k, v in now.items()}  # argparse formats help
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0],
                                     epilog=f"'now' values come from {source}.")
    parser.add_argument("--run", action="store_true", help="run with config defaults")
    parser.add_argument("--once", action="store_true",
                        help="flash one reminder right away, then exit")
    parser.add_argument("--message", help=f"text to show (now: {now['message']})")
    parser.add_argument("--interval", dest="interval_minutes", type=float,
                        help=f"minutes between reminders (now: {now['interval_minutes']})")
    parser.add_argument("--duration", dest="duration_seconds", type=float,
                        help="seconds each reminder stays visible "
                             f"(now: {now['duration_seconds']})")
    parser.add_argument("--count", type=int,
                        help="stop after this many reminders; 0 = until Ctrl+C "
                             f"(now: {now['count']})")
    parser.add_argument("--start-blinks", dest="start_blinks", type=int,
                        help="quick blinks at start, to show it's running; 0 = none "
                             f"(now: {now['start_blinks']})")
    parser.add_argument("--no-tray", dest="tray", action="store_false", default=None,
                        help=f"no tray icon (stop with Ctrl+C) (now: tray {now['tray']})")
    parser.add_argument("--primary-only", dest="all_screens", action="store_false",
                        default=None, help="show on the primary screen only, not on "
                                           f"every one (now: all_screens {now['all_screens']})")
    parser.add_argument("--anchor", type=str.lower, choices=ANCHORS,
                        help="screen point the text is placed from "
                             f"(now: {now['anchor']})")
    parser.add_argument("--offset-x", dest="offset_x", type=int,
                        help="pixels from the anchor; positive = right "
                             f"(now: {now['offset_x']})")
    parser.add_argument("--offset-y", dest="offset_y", type=int,
                        help="pixels from the anchor; positive = up "
                             f"(now: {now['offset_y']})")
    parser.add_argument("--font-family", dest="font_family",
                        help=f"font name (now: {now['font_family']}); see --list-fonts")
    parser.add_argument("--font-size", dest="font_size", type=int,
                        help=f"text size in points (now: {now['font_size']})")
    parser.add_argument("--text-color", dest="text_color",
                        help=f"color name or #rrggbb (now: {now['text_color']})")
    parser.add_argument("--outline-width", dest="outline_width", type=int,
                        help="text outline in pixels; 0 = none "
                             f"(now: {now['outline_width']})")
    parser.add_argument("--outline-color", dest="outline_color",
                        help=f"color name or #rrggbb (now: {now['outline_color']})")
    parser.add_argument("--background-color", dest="background_color",
                        help=f"box color name or #rrggbb (now: {now['background_color']})")
    parser.add_argument("--background-opacity", dest="background_opacity", type=float,
                        help="box only, never the text: 0 = no box, 1 = solid "
                             f"(now: {now['background_opacity']})")
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
        except (EOFError, RuntimeError):  # RuntimeError: no console (pythonw at login)
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
    except (EOFError, RuntimeError):  # RuntimeError: no console (pythonw at login)
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
    if settings["start_blinks"] < 0:
        raise SystemExit("start_blinks must be 0 (no blinks) or more.")
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
    """Hides the reminder (all its windows, on every screen)."""
    for window in windows:
        window.withdraw()


def build_reminder(settings: dict) -> tuple[tk.Tk, dict]:
    """
    Creates the hidden root and the reminder's font; the windows come per screen.

    flash() adds a window set (add_window_set) for each screen it needs, so a screen
    plugged in while the tool runs gets one at the next reminder.

    Returns:
        (the hidden root that runs the event loop, the reminder: settings, font,
        "sets" = one window list per screen, "all" = every window, for hide()).
    """
    root = tk.Tk()
    root.withdraw()
    if settings["font_family"] not in tkfont.families(root):
        print(f"Font {settings['font_family']!r} not found; tkinter uses its default "
              "font instead. See: python main.py --list-fonts")
    font = tkfont.Font(root=root, family=settings["font_family"],
                       size=settings["font_size"],
                       weight="bold" if settings["font_bold"] else "normal",
                       slant="italic" if settings["font_italic"] else "roman")
    return root, {"root": root, "settings": settings, "font": font, "sets": [], "all": []}


def add_window_set(reminder: dict) -> list[tk.Toplevel]:
    """
    Creates the hidden windows for one screen: a background box with a text window on top.

    tkinter's opacity applies to a whole window, so fading only the background takes
    two borderless, always-on-top windows of the same size and place: the box, a plain
    color at background_opacity (none at 0), and the text window, solid, with its empty
    space see-through. The text is drawn on a canvas: first the outline (the text
    repeated at every offset within outline_width), then the text. Clicking any window
    or pressing Esc hides the reminder on every screen; flash() places and shows them.
    On X11, which can't make part of a window see-through, one solid box is used (with
    a warning rather than a silent fallback).

    Returns:
        The new set's windows, box first; also added to reminder["sets"] and ["all"].
    """
    root, settings, font = reminder["root"], reminder["settings"], reminder["font"]
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
        if not reminder["sets"]:  # once, not once per screen
            print("A see-through background isn't supported on this system (X11); "
                  "using a solid box instead.")
        background = box_color or "#000000"
        if box_color:
            windows.pop(0).destroy()
    elif box_color:
        windows[0].attributes("-alpha", opacity)
        windows[0].configure(bg=box_color)
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
    every = reminder["all"]  # grows with each new screen, so a click hides them all
    for widget in (*windows, canvas):
        widget.bind("<Button-1>", lambda _e: hide(every))
    text_window.bind("<Escape>", lambda _e: hide(every))
    reminder["sets"].append(windows)
    every.extend(windows)
    return windows


def screen_rects(root: tk.Tk, all_screens: bool) -> list[tuple[int, int, int, int]]:
    """
    Returns the screens to show the reminder on, as (left, top, width, height).

    With all_screens on Windows: every monitor, asked anew each time, so plugging one
    in or out while the tool runs is picked up. Otherwise, or when Windows can't list
    them (reported), only the primary screen, which starts at (0, 0).
    """
    primary = [(0, 0, root.winfo_screenwidth(), root.winfo_screenheight())]
    if not all_screens or sys.platform != "win32":
        return primary
    import ctypes
    from ctypes import wintypes
    rects: list[tuple[int, int, int, int]] = []

    def found(_monitor, _dc, rect, _data) -> int:
        r = rect.contents
        rects.append((r.left, r.top, r.right - r.left, r.bottom - r.top))
        return 1  # keep going

    callback = ctypes.WINFUNCTYPE(ctypes.c_int, wintypes.HMONITOR, wintypes.HDC,
                                  ctypes.POINTER(wintypes.RECT), wintypes.LPARAM)(found)
    if not ctypes.windll.user32.EnumDisplayMonitors(None, None, callback, 0) or not rects:
        print("Could not list the screens; showing on the primary screen only.")
        return primary
    return rects


def window_origin(anchor: str, offset: tuple[int, int], size: tuple[int, int],
                  screen: tuple[int, int]) -> tuple[int, int]:
    """
    Returns the window's top-left corner, relative to its screen's top-left corner.

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


def flash(reminder: dict, duration_ms: int) -> None:
    """
    Shows the reminder on each screen at its anchor and offset; hides it after duration_ms.

    A screen without a window set yet gets one; sets for screens that are gone stay
    hidden.
    """
    settings = reminder["settings"]
    rects = screen_rects(reminder["root"], settings["all_screens"])
    while len(reminder["sets"]) < len(rects):
        add_window_set(reminder)
    for windows, (left, top, screen_w, screen_h) in zip(reminder["sets"], rects):
        text_window = windows[-1]
        text_window.update_idletasks()
        width, height = text_window.winfo_reqwidth(), text_window.winfo_reqheight()
        x, y = window_origin(settings["anchor"],
                             (settings["offset_x"], settings["offset_y"]),
                             (width, height), (screen_w, screen_h))
        for window in windows:  # box first, so the text window ends up on top
            # e.g. +-40: negative positions are valid (a screen left of the primary)
            window.geometry(f"{width}x{height}{left + x:+d}{top + y:+d}")
            window.deiconify()
            window.lift()
    reminder["sets"][0][-1].focus_force()  # so Esc reaches it (it hides every screen)
    reminder["root"].after(duration_ms, hide, reminder["all"])


def tray_images(icon_path: str) -> dict[bool, "Image.Image"]:
    """
    Returns the tray icon for on (True) and off (False).

    `icon_path` empty: the built-in drawing, a white standing figure in a green disc.
    Otherwise an image file (.png, .ico, .jpg ...; not .svg, which Pillow can't read),
    absolute or relative to this tool's folder, e.g. the shipped assets/icon-four_cubes.png;
    a missing or unreadable file warns and falls back to the built-in one. The
    off icon is the on icon in grey, darkened and at 60 % opacity, so on and off stay
    distinguishable with any image, a white one included.
    """
    from PIL import Image, ImageDraw
    on = None
    if icon_path:
        path = Path(icon_path)
        path = path if path.is_absolute() else HERE / path
        try:
            on = Image.open(path).convert("RGBA")
        except (OSError, ValueError) as error:
            print(f"tray_icon {icon_path!r} can't be used ({error}); "
                  "using the built-in icon.")
    if on is None:
        on = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(on)
        draw.ellipse((2, 2, 62, 62), fill=(46, 160, 67))
        draw.ellipse((26, 10, 38, 22), fill="white")      # head
        draw.rectangle((28, 24, 36, 54), fill="white")    # straight back
    # off: grey, darkened and faded to 60 %, so even a white icon visibly changes
    grey = on.convert("L").point(lambda v: v * 6 // 10)
    alpha = on.getchannel("A").point(lambda a: a * 6 // 10)
    return {True: on, False: Image.merge("RGBA", (grey, grey, grey, alpha))}


def set_startup(enable: bool) -> None:
    """
    Creates or deletes the Startup-folder shortcut that runs this tool at login.

    The shortcut runs this venv's pythonw.exe (no console window) with
    `main.py --run` in this folder, so settings come from config.yaml. Windows only;
    called from the tray menu, so the user's click is the go-ahead for the write.
    """
    if not enable:
        STARTUP_LINK.unlink(missing_ok=True)
        print(f"start at login: off (removed {STARTUP_LINK.name})")
        return
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    script = ("$l = (New-Object -ComObject WScript.Shell).CreateShortcut($env:LINK); "
              "$l.TargetPath = $env:TARGET; $l.Arguments = 'main.py --run'; "
              "$l.WorkingDirectory = $env:FOLDER; $l.Save()")
    # paths go in as environment variables, so quotes or spaces in them can't break it
    env = dict(os.environ, LINK=str(STARTUP_LINK), TARGET=str(pythonw), FOLDER=str(HERE))
    result = subprocess.run(["powershell", "-NoProfile", "-Command", script], env=env,
                            capture_output=True, text=True, check=False,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if result.returncode or not STARTUP_LINK.exists():
        print(f"start at login: could not create the shortcut: {result.stderr.strip()}")
    else:
        print(f"start at login: on ({STARTUP_LINK})")


def sync_startup(enabled: bool) -> None:
    """
    Makes the Startup shortcut match start_with_windows: creates or removes it.

    config.yaml is the source of truth, so a run started any way (terminal, login)
    brings the shortcut in line with it. Not Windows: a true value is reported, not
    silently ignored.
    """
    if sys.platform != "win32":
        if enabled:
            print("start_with_windows only works on Windows; ignored.")
        return
    if enabled != STARTUP_LINK.exists():
        set_startup(enabled)


def save_setting(key: str, value: bool | float | str) -> bool:
    """
    Writes one top-level setting into config.yaml, keeping its comments and layout.

    Replaces the value on the `key:` line (padded to the old width, so a trailing
    comment stays aligned), or appends `key: value` when the key isn't there yet.

    Returns:
        False when there's no config.yaml to write to (the example is never changed).
    """
    config = HERE / "config.yaml"
    if not config.exists():
        return False
    with open(config, encoding="utf-8", newline="") as f:
        text = f.read()
    new_value = json.dumps(value, ensure_ascii=False)  # valid YAML: true, 3, "text"
    match = re.search(rf"^{re.escape(key)}:[ \t]*([^#\r\n]*?)[ \t]*(?:#[^\r\n]*)?\r?$",
                      text, re.MULTILINE)
    if match:
        old = match.group(1)
        text = text[:match.start(1)] + new_value.ljust(len(old)) + text[match.end(1):]
    else:
        newline = "\r\n" if "\r\n" in text else "\n"
        text += ("" if text.endswith(("\n", "\r\n")) or not text else newline)
        text += f"{key}: {new_value}{newline}"
    with open(config, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    return True


def start_tray(commands: queue.Queue, state: dict,
               icon_path: str) -> tuple["pystray.Icon", dict[bool, "Image.Image"]]:
    """
    Shows the tray icon and its menu in a background thread.

    Menu clicks only put a command on the queue; run()'s poll handles it in tkinter's
    thread, since tkinter may only be used from the thread that created it. The
    checkmarks read `state` (Active) and the shortcut's existence (Start with Windows).

    Returns:
        (the icon, its on/off images from tray_images(icon_path)).

    Raises:
        SystemExit: pystray or Pillow isn't installed.
    """
    try:
        import pystray
    except ImportError:
        raise SystemExit("The tray icon needs pystray and Pillow: "
                         "pip install -r requirements.txt, or run with --no-tray.")
    images = tray_images(icon_path)
    item = pystray.MenuItem
    menu = pystray.Menu(
        item("Active", lambda: commands.put("toggle"),
             checked=lambda _i: state["active"]),
        item("Show now", lambda: commands.put("show"), default=True),  # = double-click
        item("Start with Windows", lambda: commands.put("startup"),
             checked=lambda _i: STARTUP_LINK.exists(),
             visible=sys.platform == "win32"),
        pystray.Menu.SEPARATOR,
        item("Quit", lambda: commands.put("quit")))
    icon = pystray.Icon("posture_reminder", images[True], TRAY_NAME, menu)
    threading.Thread(target=icon.run, daemon=True).start()
    return icon, images


def run(settings: dict) -> None:
    """
    Shows the reminder every interval_minutes, for duration_seconds each time.

    Stops after `count` reminders (0 = never), on Ctrl+C or on tray > Quit. With --once
    the single reminder is shown right away instead of after the first interval.
    Otherwise the text first blinks start_blinks times, so a start at login is visibly
    working (the blinks don't count as reminders), and with `tray` a tray icon turns
    reminders off and on, shows one now, or toggles the start at login.
    """
    interval_ms = round(settings["interval_minutes"] * 60_000)
    duration_ms = round(settings["duration_seconds"] * 1000)
    count = settings["count"]
    root, reminder = build_reminder(settings)
    shown = 0
    # Shared with the tray thread, which only reads it; commands go the other way
    state = {"active": True, "job": None, "next": datetime.now()}
    commands: queue.Queue[str] = queue.Queue()
    tray, images = None, {}

    def next_reminder(delay_ms: int) -> None:
        state["next"] = datetime.now() + timedelta(milliseconds=delay_ms)
        print(f"next reminder at {state['next']:%H:%M:%S}")
        state["job"] = root.after(delay_ms, remind)

    def remind() -> None:
        nonlocal shown
        shown += 1
        print(f"[{datetime.now():%H:%M:%S}] reminder {shown}"
              + (f"/{count}" if count else ""))
        flash(reminder, duration_ms)
        if count and shown >= count:
            root.after(duration_ms + 100, root.quit)  # let the last one finish showing
            return
        next_reminder(interval_ms)
        update_tray()

    def blink(times: int) -> None:
        for i in range(times):
            root.after(i * (BLINK_ON_MS + BLINK_OFF_MS), flash, reminder, BLINK_ON_MS)

    def update_tray() -> None:
        if tray:
            tray.icon = images[state["active"]]
            tray.title = (f"{TRAY_NAME}: next at {state['next']:%H:%M}" if state["active"]
                          else f"{TRAY_NAME}: off")
            tray.update_menu()

    def handle(command: str) -> None:
        """Runs a tray menu command in tkinter's thread (see poll)."""
        if command == "toggle" and state["active"]:
            root.after_cancel(state["job"])
            state["active"] = False
            print(f"[{datetime.now():%H:%M:%S}] off (tray)")
        elif command == "toggle":
            state["active"] = True
            print(f"[{datetime.now():%H:%M:%S}] on (tray)")
            blink(1)
            next_reminder(interval_ms)
        elif command == "show":
            flash(reminder, duration_ms)
        elif command == "startup":
            enabled = not STARTUP_LINK.exists()
            set_startup(enabled)
            if save_setting("start_with_windows", enabled):
                print(f"saved start_with_windows: {str(enabled).lower()} in config.yaml")
            else:
                print("No config.yaml to save start_with_windows in: the next run "
                      "follows config.example.yaml (create config.yaml to keep it).")
        elif command == "quit":
            root.quit()
        update_tray()

    def poll() -> None:
        while not commands.empty():
            handle(commands.get_nowait())
        root.after(POLL_MS, poll)

    print(f"message : {settings['message']}")
    print("screens : " + ("every screen" if settings["all_screens"] else "primary only"))
    if settings["once"]:
        print(f"once    : now, shown for {settings['duration_seconds']} s")
        root.after(0, remind)
    else:
        print(f"every   : {settings['interval_minutes']} min, "
              f"shown for {settings['duration_seconds']} s")
        print("stop    : Ctrl+C" + (", or tray icon > Quit" if settings["tray"] else "")
              + (f" (or after {count} reminder{'s' if count > 1 else ''})"
                 if count else ""))
        sync_startup(settings["start_with_windows"])
        blink(settings["start_blinks"])
        next_reminder(interval_ms)
        if settings["tray"]:
            tray, images = start_tray(commands, state, settings["tray_icon"])
            update_tray()
    poll()
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        if tray:
            tray.stop()
        root.destroy()

# -----------------------------------------------------------------------------------------
#                main
# -----------------------------------------------------------------------------------------
def main(argv: list[str]) -> int:
    # 1. No arguments: usage guide only, never work (no-args-usage-guide)
    if not argv:
        print(__doc__.strip())
        print()
        print(usage_summary())  # the values a run would use, from config.yaml
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
