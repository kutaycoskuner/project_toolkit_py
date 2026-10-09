<h1 align="center">
    Posture Reminder
</h1>

<p align="center">
    Flashes a short text ("Dik dur!") on the screen every few minutes, as a reminder to sit or stand straight at the computer.
</p>

<p align="center">
    <img alt="Template" src="https://img.shields.io/badge/template-3.2.0-blue" />
    <img alt="Last Update" src="https://img.shields.io/github/last-commit/kutaycoskuner/python-toolbox?path=posture_reminder" />
</p>

------------------------------------------------------------------------------------------

## Folders

```bash
posture_reminder/
├── .venv/              # Virtual environment (gitignored)
├── assets/             # Tray icons: icon-four_cubes (shipped; .svelte original, .svg, .png used) and ring_void (alternative)
├── config.yaml         # Your settings (gitignored, created on first run)
├── config.example.yaml # Default settings with comments (committed)
├── main.py             # Entry point; its header docstring explains the steps
├── README.md
└── requirements.txt    # Pinned dependencies
```

- no `example/` folder and no `.env`: the tool reads no files and needs no secrets

------------------------------------------------------------------------------------------

## Usage

```bash
python main.py                  # Usage guide and your current settings, does nothing
python main.py --once           # Flash one reminder right now, to check the look
python main.py --run            # Remind every interval_minutes (as shipped: 8 min, 1 s), with a tray icon
python main.py --run --no-tray  # Same without the tray icon; stop with Ctrl+C
python main.py --run --interval 30 --duration 8 --message "Stand up!"
python main.py --run --count 6  # Stop after 6 reminders
python main.py --once --primary-only  # Only on the primary screen, not on every one
python main.py --once --anchor center --offset-x 40 --offset-y 40
                                # 40 px right of and 40 px above the center
python main.py --once --anchor top-right --offset-x -40 --offset-y -40 --background-opacity 0.5 --outline-width 0
                                # Half-faded red box with solid text, 40 px in from the top-right corner
python main.py --once --font-family Consolas --text-color yellow
python main.py --list-fonts     # Installed font names, for font_family
python main.py --help           # All flags, with the values your config.yaml sets now
```

- While it runs
    - the terminal prints the time of the next reminder
    - each reminder is borderless and always on top, on every screen (`all_screens`, Windows; elsewhere the primary screen), at `anchor` + `offset_x` / `offset_y` on each
        - screens are looked up at every reminder, so a monitor plugged in while it runs gets the next one
    - as shipped: white text in Linux Libertine G with a 2 px black outline, no box, centered 160 px above the bottom edge
    - click it or press `Esc` to hide it early (on every screen)
    - tray icon (as shipped three hexagon outlines, grey when off; your own image via `tray_icon`; hover shows the next reminder's time), right-click for the menu
        - **Active**: untick to turn reminders off, tick to turn them on again (blinks once, next reminder one interval later)
        - **Show now**: flash the reminder now (also: double-click the icon)
        - **Start with Windows**: tick to run at every login, untick to stop that (Windows only; see below)
        - **Quit**: stop the tool
    - `Ctrl+C` in the terminal also stops it
    - at start the text blinks 2 times (`start_blinks`), so you can see it's running; the first real reminder comes after one interval (use `--once` to see one right away)
- First run
    - `config.yaml` doesn't exist in a fresh checkout (it's gitignored); the first real run asks whether to create it from `config.example.yaml`
    - on `n` or without a terminal, nothing is created and `config.example.yaml` is used for that run
- After an update (e.g. a `git pull` that adds or removes settings in `config.example.yaml`)
    - every run compares the settings (top-level keys) in your `config.yaml` with the example's; when they differ, it lists missing keys (defaults used) and unknown keys (ignored) and asks
        - `m`: new example, your values kept (new keys and comments come from the example; keys it dropped are listed)
        - `r`: fresh copy of the example, your values are lost
        - `k`: keep `config.yaml` as it is; asked again on the next run
    - before `m` or `r`, the old file is saved as `config.yaml.bak` (gitignored)
- Start at login (Windows)
    - turn it on either way; both stay in sync
        - `start_with_windows: true` in `config.yaml`, then run `python main.py --run` once
        - or run `python main.py --run`, right-click the tray icon, tick **Start with Windows** (saves `start_with_windows: true` in `config.yaml`)
    - every run makes the shortcut match the setting: creates it when `true` and missing, removes it when `false`
    - the shortcut is `Posture reminder.lnk` in your Startup folder (Win+R, `shell:startup`); it runs this folder's `.venv\Scripts\pythonw.exe main.py --run`, so no console window, settings from `config.yaml`
    - at login the text blinks (`start_blinks`) and the tray icon appears; control it from the tray from then on
    - to stop starting at login: untick **Start with Windows**, or set `start_with_windows: false` (deleting the shortcut by hand doesn't last while the setting is `true`: the next run recreates it)
    - moved the folder or recreated `.venv`? untick and tick again, so the shortcut points at the new place
    - without a console there's no one to answer the config prompt: it keeps `config.yaml` as it is and asks on the next run from a terminal
    - each start is its own copy: starting it by hand while the login copy runs gives two icons and double reminders; quit one from its tray menu

------------------------------------------------------------------------------------------

## Settings

- Read in this order; later sources override earlier ones
    1. defaults in `main.py`
    2. `config.yaml` (offered on the first real run; until then `config.example.yaml`)
    3. command-line flags

| Setting | Flag | Default | Meaning |
|---|---|---|---|
| `message` | `--message` | `Dik dur!` | text to flash; `"\n"` in double quotes starts a new line |
| `interval_minutes` | `--interval` | `8` | minutes between reminders (decimals allowed) |
| `duration_seconds` | `--duration` | `1` | seconds each reminder stays visible; shorter than the interval |
| `count` | `--count` | `0` | stop after this many reminders; `0` = until `Ctrl+C` |
| `start_blinks` | `--start-blinks` | `2` | quick blinks right at start (0.4 s on, 0.3 s off), to show it's running; `0` = none; not counted as reminders |
| `tray` | `--no-tray` | `true` | tray icon with Active / Show now / Start with Windows / Quit; needs `pystray` and `Pillow` (in `requirements.txt`) |
| `tray_icon` | — | `assets/icon-four_cubes.png` | tray icon image: a `.png` / `.ico` / `.jpg` path (not `.svg`: Pillow can't read it), absolute or relative to this folder; `""` = built-in drawing (white figure in a green disc); when off, a grey version of it; a missing or unreadable file warns and uses the built-in one; square images look best |
| `start_with_windows` | — | `false` | run at every login (Windows); each run creates or removes the Startup shortcut to match; the tray item saves its choice here |
| `all_screens` | `--primary-only` | `true` | show the reminder on every screen, same anchor and offset on each (Windows); `false` = primary screen only; on macOS / Linux always the primary screen |
| **Position** | | | |
| `anchor` | `--anchor` | `bottom` | `center`, `top`, `bottom`, `left`, `right`, `top-left`, `top-right`, `bottom-left`, `bottom-right`: the screen point the text box's matching point sits on |
| `offset_x` | `--offset-x` | `0` | pixels from the anchor; positive = right, negative = left |
| `offset_y` | `--offset-y` | `160` | pixels from the anchor; positive = up, negative = down |
| **Font** | | | |
| `font_family` | `--font-family` | `Linux Libertine G` | an installed font; list them with `--list-fonts` |
| `font_size` | `--font-size` | `72` | points |
| `font_bold` | — | `true` | |
| `font_italic` | — | `false` | |
| `text_color` | `--text-color` | `#ffffff` | a color name (`white`) or `#rrggbb` |
| **Outline** | | | |
| `outline_width` | `--outline-width` | `2` | pixels around each letter; `0` = none |
| `outline_color` | `--outline-color` | `#000000` | same format as `text_color` |
| **Background box** | | | |
| `background_opacity` | `--background-opacity` | `0` | the box only, never the text: `0` = no box (text only), `0.5` = half see-through, `1` = solid |
| `background_color` | `--background-color` | `#c0392b` | box color; unused at opacity `0` |
| `padding` | — | `40` | pixels between the text and the box edge; unused at opacity `0` |

- `--once` and `--list-fonts` are flags only: one reminder right away / print font names, then exit
- out-of-range values (interval or duration `0`, duration longer than the interval, negative count, padding or outline, `background_opacity` outside `0`–`1`, an unknown anchor, a non-whole offset) stop the run with a message
- position examples
    - the anchor puts the box's matching point on the screen's: `center` on center, `top-left` corner on corner, `top` edge middle on the top edge's middle
    - then the offset moves it; the directions are the same for every anchor, so from a right or bottom anchor, move inwards with negative values

    | `anchor` | `offset_x` | `offset_y` | Result |
    |---|---|---|---|
    | `center` | `40` | `40` | 40 px right of and 40 px above the center |
    | `top-right` | `-40` | `-40` | 40 px in from the top-right corner |
    | `bottom` | `0` | `60` | centered, 60 px above the bottom edge |
    | `top-left` | `100` | `-200` | box's top-left corner at screen pixel (100, 200) |
- an unknown `font_family` only warns: tkinter then uses its default font
    - Linux Libertine G is a free font ([SourceForge](https://sourceforge.net/projects/linuxlibertine/)); on a machine without it, set another `font_family`
- how the background works
    - tkinter can only fade a whole window, so the box and the text are two windows of the same size and place: the box at `background_opacity`, the text solid on top, with see-through space around the letters
    - works on Windows and macOS; on Linux (X11) the run warns and uses one solid box (black at opacity `0`)
    - clicks on the see-through part go to the window below; click the text or the box, or press `Esc`, to hide it early
    - without a box, letter edges may show a thin dark fringe; the default outline hides it and keeps the text readable on any wallpaper
- older configs: `opacity` was renamed to `background_opacity` (the run lists it as unknown and offers the update); `background_color: transparent` still works and means opacity `0`

------------------------------------------------------------------------------------------

## Setup Python Environment

### Prerequisites
- **Python 3.10+**: [Install Python](https://www.python.org/downloads/) (includes `pip` and `tkinter`).
- On Linux, `tkinter` may be a separate package, e.g. `sudo apt install python3-tk`.

### Steps

```bash
# Go to the tool's folder
cd python-toolbox/posture_reminder

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
#   Windows:
.venv\Scripts\activate
#   macOS / Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Deactivate the environment when done (optional)
deactivate
```
