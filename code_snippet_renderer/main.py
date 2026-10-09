# -----------------------------------------------------------------------------------------
#   author          : Kutay Coskuner
#   ai-contributors : unknown (before 2026-10-05), Claude Opus 5.5 (claude-opus-5-5)
#   last update     : 2026-10-06
#   template        : 3.2.0
#   disclaimer      : Provided as is, without warranty of any kind; use at your own risk.
#                     Check outputs before relying on them.
# -----------------------------------------------------------------------------------------
"""
Code snippet renderer: renders syntax-highlighted code snippets, written as coloured
text pieces in a JSON file, as an image (1920x1080 by default) for slides, posts or docs.

The JSON file (see example/input/):
    {"title": {"text": "windows powershell", "color": "#666666"},   <- optional
     "0": [["New-Item ", "#00FF00"], ["-Path ", "#00CCFF"]],        <- row 0: pieces
     "1": [["", "#FFFFFF"]]}                                        <- an empty row
Each row is a list of [text, colour] pieces drawn left to right; rows are numbered from
0. With a title, the rows get a rounded frame with the title in its top-left corner.

1. Bare run prints this guide and exits (no-args-usage-guide).
2. The first real run offers to create config.yaml from config.example.yaml
   (ensure_config); later runs compare its keys with config.example.yaml's and offer
   to update it when they differ (update_config).
3. Settings come from CLI flags > config.yaml > DEFAULTS (load_settings).
4. Every JSON file (a single file, or the files matching `pattern` in a folder) is
   rendered (render_file): the font size is fitted so the longest row fills the width
   inside the side margins, the rows are centred vertically, the frame and title drawn.
5. Each image is saved as <output>/<name>.png (a single file: <output>/<output_name>);
   a dry run only lists what would be rendered.

Requires: this folder's .venv (pip install -r requirements.txt); the font (`font`) is
looked up with matplotlib and falls back to its default font when it isn't installed.
config.yaml is gitignored: your paths go there. No .env: the tool needs no secrets.

Inputs -> outputs: JSON snippet files -> PNG images (overwritten; inputs never changed).
As shipped, config.example.yaml renders the three snippets in example/input/.

Run:
    python main.py --run                         render the example snippets
    python main.py --run --dry-run               list what would be rendered
    python main.py --input D:/posts/snippet.json --output D:/posts/images
    python main.py --run --width 1080 --height 1080   square images
    python main.py --help                        all flags; see README.md

Gotchas:
    - the font size follows the longest row (measured as that many "M"s), so one long
      row makes all text smaller; split long lines into two rows.
    - a monospace font keeps columns aligned; with a proportional one, indents drift.
"""

# -----------------------------------------------------------------------------------------
#                libraries
# -----------------------------------------------------------------------------------------
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

import yaml
from matplotlib import font_manager
from PIL import Image, ImageDraw, ImageFont

# -----------------------------------------------------------------------------------------
#                variables
# -----------------------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
DEFAULTS = {
    "input": "example/input",
    "output": "example/output",
    "pattern": "*.json",
    "output_name": "rendered.png",
    "width": 1920,
    "height": 1080,
    "bg_color": "#101010",
    "font": "Courier New",
    "line_spacing": 1.2,
    "v_margin": 0.05,
    "h_margin": 0.05,
    "frame_color": "#262626",
    "frame_width": 4,
    "frame_radius": 12,
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
    parser.add_argument("--input", help="a JSON file, or a folder of them")
    parser.add_argument("--output",
                        help="folder for the images (default: example/output/)")
    parser.add_argument("--width", type=int, help="image width in pixels (default: 1920)")
    parser.add_argument("--height", type=int,
                        help="image height in pixels (default: 1080)")
    parser.add_argument("--relative-to", choices=RELATIVE_TO,
                        help="base for relative paths: this tool's folder or the cwd")
    parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=None,
                        help="list what would be rendered, write nothing")
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


def hex_to_rgb(hex_color: str):
    """Convert hex string like '#1e88e5' to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


class TextImage:
    """
    A canvas that collects coloured text pieces per row and draws them as code.

    add_phrase() collects pieces; draw_code_block() draws the frame and title;
    save() fits the font, draws the rows and writes the PNG.
    """

    def __init__(self, settings: dict):
        self.width = settings["width"]
        self.height = settings["height"]
        self.v_margin = settings["v_margin"]  # vertical margin, share of height
        self.h_margin = settings["h_margin"]  # horizontal margin, share of width
        self.line_spacing = settings["line_spacing"]
        self.font_path = font_manager.findfont(settings["font"])
        self.img = Image.new("RGB", (self.width, self.height),
                             color=hex_to_rgb(settings["bg_color"]))
        self.draw = ImageDraw.Draw(self.img)
        self.rows = {}  # row_number -> list of (text, color)

    def add_phrase(self, row_number, text, color="#FFFFFF"):
        if row_number not in self.rows:
            self.rows[row_number] = []
        self.rows[row_number].append((text, color))

    def _adjust_font_size(self):
        """Scale font size so the longest row fits exactly within horizontal margins."""
        # Find max character count in any row
        max_chars = 0
        for row_parts in self.rows.values():
            row_text = "".join(text for text, _ in row_parts)
            max_chars = max(max_chars, len(row_text))

        available_width = self.width * (1 - 2 * self.h_margin)
        if max_chars == 0:
            return

        # Binary search optimal font size based on 'M' width
        low, high = 5, 500
        target_size = 100
        while low <= high:
            mid = (low + high) // 2
            font = ImageFont.truetype(self.font_path, mid)
            bbox = font.getbbox("M" * max_chars)
            row_width = bbox[2] - bbox[0]

            if row_width < available_width:
                target_size = mid
                low = mid + 1
            else:
                high = mid - 1

        self.font_size = target_size
        self.font = ImageFont.truetype(self.font_path, target_size)
        self.line_height = int(self.font_size * self.line_spacing)

    def draw_code_block(self, title, text_color, frame_color, width, radius):
        """Draw a rounded frame around the text rows with the title in its top left."""
        if not self.rows:
            return

        # Ensure font/line_height is ready
        if not hasattr(self, "line_height"):
            self._adjust_font_size()

        # Get first and last text row indices
        row_numbers = sorted(self.rows.keys())
        top_row = row_numbers[0]
        bottom_row = row_numbers[-1]

        # Total height of the text block
        row_count = bottom_row - top_row + 1
        available_height = self.height * (1 - 2 * self.v_margin)
        total_height = self.line_height * row_count
        offset_y = (available_height - total_height) / 2
        start_y = self.height * self.v_margin + offset_y

        # Frame: 3 rows above the text (title + gap) and 2 below
        frame_top_y = start_y - 3 * self.line_height
        frame_bottom_y = start_y + (row_count + 2) * self.line_height
        left_x = self.width * (self.h_margin * 0.5)
        right_x = self.width * (1 - self.h_margin * 0.5)

        # Draw rounded rectangle frame
        self.draw.rounded_rectangle(
            [left_x, frame_top_y, right_x, frame_bottom_y],
            outline=hex_to_rgb(frame_color),
            width=width,
            radius=radius,
            fill=None
        )

        # Title text (left-aligned inside the frame, horizontal padding = 50% of h_margin)
        title_padding = (self.width * self.h_margin * 0.5)
        title_x = left_x + title_padding
        title_y = frame_top_y + (self.line_height * 0.5)  # slight vertical padding
        self.draw.text((title_x, title_y), title, fill=hex_to_rgb(text_color),
                       font=self.font)

    def render_rows(self):
        """Draws every row's pieces left to right, the block centred vertically."""
        if not self.rows:
            return

        self._adjust_font_size()

        row_count = max(self.rows.keys()) + 1
        available_height = self.height * (1 - 2 * self.v_margin)
        total_height = self.line_height * row_count
        start_y = self.height * self.v_margin + (available_height - total_height) / 2

        for row_number in sorted(self.rows.keys()):
            row_parts = self.rows[row_number]
            y = start_y + row_number * self.line_height

            # Left alignment: always start from the left margin
            x = self.width * self.h_margin

            # Draw text sequentially
            for text, color in row_parts:
                self.draw.text((x, y), text, fill=hex_to_rgb(color), font=self.font)
                bbox = self.draw.textbbox((x, y), text, font=self.font)
                text_width = bbox[2] - bbox[0]
                x += text_width

    def save(self, out_path: Path):
        self.render_rows()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        self.img.save(out_path)
        print(f"Saved {out_path}")


def render_file(source: Path, target: Path, settings: dict) -> None:
    """Renders one JSON snippet file into target (see the module docstring)."""
    with open(source, "r", encoding="utf-8") as f:
        rows = json.load(f)
    ti = TextImage(settings)
    title = rows.pop("title", None)
    for row_number, row_parts in rows.items():
        for text, color in row_parts:
            ti.add_phrase(int(row_number), text, color)
    if title:
        ti.draw_code_block(title=title["text"], text_color=title["color"],
                           frame_color=settings["frame_color"],
                           width=settings["frame_width"], radius=settings["frame_radius"])
    ti.save(target)


def find_inputs(settings: dict) -> list[tuple[Path, Path]]:
    """
    Pairs each JSON file with its image path.

    Returns:
        [(json file, png file)]: a single file goes to <output>/<output_name>; files in
        a folder become <output>/<name>.png. Empty when nothing matches.
    """
    source, output = settings["input"], settings["output"]
    if source.is_file():
        return [(source, output / settings["output_name"])]
    return [(path, output / f"{path.stem}.png")
            for path in sorted(source.glob(settings["pattern"])) if path.is_file()]

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
    if not settings["input"].exists():
        print(f"File or folder not found: {settings['input']}")
        return 1
    # 4.-5. Render and save
    pairs = find_inputs(settings)
    if not pairs:
        print(f"No files matching {settings['pattern']!r} in {settings['input']}.")
        return 0
    for source, target in pairs:
        if settings["dry_run"]:
            print(f"Would render: {source.name} -> {target}")
            continue
        try:
            render_file(source, target, settings)
        except (OSError, ValueError, KeyError, TypeError) as error:
            print(f"Could not render {source.name}: {error!r}")
    if settings["dry_run"]:
        print("Dry run: nothing written.")
    return 0


# -----------------------------------------------------------------------------------------
#                start
# -----------------------------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
