# -----------------------------------------------------------------------------------------
#   author          : Kutay Coskuner
#   ai-contributors : unknown (before 2026-10-04), Claude Opus 5.5 (claude-opus-5-5)
#   last update     : 2026-10-04
#   template        : 3.1.1
#   disclaimer      : Provided as is, without warranty of any kind; use at your own risk.
#                     Check outputs before relying on them.
# -----------------------------------------------------------------------------------------
"""
Pixel matcher: compares images pixel by pixel, e.g. to catch unintended changes in the
frames a 3D renderer produces.

Three modes (`mode`):
    scenes  regression check for rendered frames: for every pair scene<N>_base.png
            (the reference) / scene<N>_test.png (the new render) in a folder, N = 0, 1,
            ..., prints MATCH when every pixel is within `tolerance`, else DIFFERENT
            with the number of pixels above it
    diff    how many pixels differ at all between two same-size images, as a count and
            a percentage (no tolerance: any colour change counts)
    find    whether a small `pattern` image appears somewhere in a `search` image,
            within `tolerance`, and where its top-left corner is (x, y)
Tolerance: how different two pixels' colours may be and still count as equal, measured
as |dR| + |dG| + |dB| (0 = identical, 765 = black vs. white). The default 60 absorbs
small differences such as anti-aliasing or compression noise.

1. Bare run prints this guide and exits (no-args-usage-guide).
2. The first real run offers to create config.yaml from config.example.yaml
   (ensure_config); later runs offer to update it when config.example.yaml has changed
   since (update_config) and warn when its keys differ from the example's
   (check_config_keys).
3. Settings come from CLI flags > config.yaml > DEFAULTS (load_settings).
4. The chosen mode runs and prints its result (run_scenes, run_diff, run_find).

Requires: this folder's .venv (pip install -r requirements.txt): OpenCV and NumPy.
config.yaml is gitignored: your folders and images go there. No .env: the tool needs no
secrets.

Inputs -> outputs: images -> console results only; nothing is written. As shipped,
config.example.yaml checks the two scene pairs in example/input/scenes/.

Run:
    python main.py --run                         check the example scenes
    python main.py --run --mode diff             % of differing pixels, example pair
    python main.py --run --mode find             find the example pattern (takes ~10 s)
    python main.py --run --scenes D:/renders/frames --tolerance 30
    python main.py --help                        all flags; see README.md

Gotchas:
    - scenes and find compare against the tolerance; diff counts every changed pixel, so
      a frame can MATCH in scenes and still differ by a few pixels in diff.
    - find compares pixel by pixel in Python: a 50x50 pattern in a 460x560 image takes
      several seconds.
    - scene pairs are read from N = 0 upwards until a pair is missing.
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

import cv2
import yaml

# -----------------------------------------------------------------------------------------
#                variables
# -----------------------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
DEFAULTS = {
    "mode": "scenes",
    "tolerance": 60,
    "scenes": "example/input/scenes",
    "image_a": "example/input/scenes/scene1_base.png",
    "image_b": "example/input/scenes/scene1_test.png",
    "pattern": "example/input/find/pattern2.jpg",
    "search": "example/input/find/find_pattern3.jpg",
    "relative_to": "tool",
}
MODES = ("scenes", "diff", "find")
PATH_KEYS = ("scenes", "image_a", "image_b", "pattern", "search")
RELATIVE_TO = ("tool", "cwd")

# -----------------------------------------------------------------------------------------
#                functions
# -----------------------------------------------------------------------------------------
def parse_args(argv: list[str]) -> argparse.Namespace:
    """Defines the CLI; flags default to None so unset ones don't override config."""
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--run", action="store_true", help="run with config defaults")
    parser.add_argument("--mode", choices=MODES, help="scenes, diff or find")
    parser.add_argument("--tolerance", type=int, help="per-pixel |dR|+|dG|+|dB| limit")
    parser.add_argument("--scenes", help="folder with scene<N>_base/_test.png pairs")
    parser.add_argument("--image-a", help="diff: first image")
    parser.add_argument("--image-b", help="diff: second image (same size)")
    parser.add_argument("--pattern", help="find: the small image to look for")
    parser.add_argument("--search", help="find: the image to search in")
    parser.add_argument("--relative-to", choices=RELATIVE_TO,
                        help="base for relative paths: this tool's folder or the cwd")
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

    Paths: an absolute path is used as-is; a relative one is resolved against this
    tool's folder (relative_to: tool) or the current working directory (cwd).

    Returns:
        Settings with every PATH_KEYS entry as an absolute Path.

    Raises:
        SystemExit: relative_to is neither "tool" nor "cwd".
    """
    settings = dict(DEFAULTS)
    config_file = ensure_config(False)  # the tool never writes, so there is no dry run
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
    for key in PATH_KEYS:
        path = Path(settings[key])
        settings[key] = path if path.is_absolute() else base / path
    return settings


def read_image(path: Path):
    """
    Loads an image as a NumPy array of shape (height, width, 3) in BGR channel order.

    Returns:
        The array, or None after printing why the file couldn't be read.
    """
    image = cv2.imread(str(path))
    if image is None:
        print(f"Could not read image: {path}")
    return image


def size(image) -> str:
    """An image's size as "width x height", e.g. "458x557"."""
    return f"{image.shape[1]}x{image.shape[0]}"


def calc_tolerance(pixel1, pixel2) -> int:
    """
    How different two pixels' colours are: |dB| + |dG| + |dR|.

    0 means identical; the maximum is 765 (black vs. white). Each channel is cast to
    int first, because uint8 arithmetic would wrap around below 0.
    """
    tolerance    = 0
    tolerance    = abs(int(pixel1[0]) - int(pixel2[0]))
    tolerance   += abs(int(pixel1[1]) - int(pixel2[1]))
    tolerance   += abs(int(pixel1[2]) - int(pixel2[2]))
    return tolerance


def find_pattern(pattern, search, tolerance_limit: int) -> tuple[int, int] | None:
    """
    Slides pattern over search and returns the first place where it fits.

    Every position (y, x) where the whole pattern fits inside search is tried, row by
    row from the top left. A position is only checked in full when its top-left pixel
    is below the tolerance (a cheap pre-filter); it fits when no pixel of the pattern
    is above the tolerance there.

    For two images of the same size there is exactly one position, (0, 0), so this
    becomes "are the two images equal within the tolerance?" (scenes mode).

    Returns:
        (y, x) of the pattern's top-left corner in search, or None when it fits nowhere
        (also when the pattern is larger than search).
    """
    search_height, search_width, _ = search.shape
    p_height, p_width, _ = pattern.shape
    for y in range(search_height-p_height+1):
        for x in range(search_width-p_width+1):
            # Compare pixel RGB values
            pixel1 = pattern[0, 0]
            pixel2 = search[y, x]
            # try to negate
            if calc_tolerance(pixel1, pixel2) < tolerance_limit:
                exists = True
                for k in range(p_height):
                    for i in range(p_width):
                        pixel1 = pattern[k, i]
                        pixel2 = search[y+k, x+i]
                        if calc_tolerance(pixel1, pixel2) > tolerance_limit:
                            exists = False
                            break
                    if not exists:
                        break
                # if not negated
                if exists:
                    return y, x
    return None


def count_pixels(image1, image2, tolerance_limit: int = 0) -> int | None:
    """
    Counts the pixels whose colours differ by more than tolerance_limit.

    With the default 0 every changed pixel counts (diff mode); with the scenes
    tolerance it counts the pixels that make a frame fail (shown for mismatches).

    Returns:
        The count, or None (with a message) when the images differ in size.
    """
    # Check if the images have the same dimensions
    if image1.shape != image2.shape:
        print(f"Images have different dimensions: {size(image1)} vs {size(image2)}")
        return None

    # Compare each pixel
    height, width, _ = image1.shape
    difference = 0
    for y in range(height):
        for x in range(width):
            # Compare pixel RGB values
            pixel1 = image1[y, x]
            pixel2 = image2[y, x]
            if tolerance_limit == 0:
                if not all(pixel1 == pixel2):
                    difference += 1
            elif calc_tolerance(pixel1, pixel2) > tolerance_limit:
                difference += 1
    return difference


def run_scenes(settings: dict) -> int:
    """
    Checks each scene<N>_base.png / scene<N>_test.png pair: does the test frame still
    look like the base frame?

    Returns:
        The number of pairs checked.
    """
    folder, tolerance = settings["scenes"], settings["tolerance"]
    print("Mode: scenes, does every test frame still match its base frame?")
    print(f"  folder   : {folder}")
    print(f"  tolerance: {tolerance} (per pixel |dR|+|dG|+|dB|, 0..765; "
          "pixels at or below it count as equal)")
    i, matches = 0, 0
    while True:
        base_path, test_path = folder / f"scene{i}_base.png", folder / f"scene{i}_test.png"
        if not (base_path.exists() and test_path.exists()):
            break
        base, test = read_image(base_path), read_image(test_path)
        if base is not None and test is not None:
            pair = f"{base_path.name} vs {test_path.name} ({size(base)})"
            if base.shape != test.shape:
                print(f"Scene {i}: DIFFERENT  {base_path.name} is {size(base)}, "
                      f"{test_path.name} is {size(test)}")
            elif find_pattern(base, test, tolerance) is not None:
                matches += 1
                print(f"Scene {i}: MATCH      {pair}: every pixel within the tolerance")
            else:
                over = count_pixels(base, test, tolerance)
                print(f"Scene {i}: DIFFERENT  {pair}: "
                      f"{over:,} pixels above the tolerance")
        i += 1
    if i == 0:
        print(f"No scene0_base.png / scene0_test.png pair in {folder}")
    else:
        print(f"{matches} of {i} scenes match.")
    return i


def run_diff(settings: dict) -> None:
    """Prints how many pixels differ at all between image_a and image_b."""
    print("Mode: diff, how many pixels differ at all (no tolerance)?")
    image1, image2 = read_image(settings["image_a"]), read_image(settings["image_b"])
    if image1 is None or image2 is None:
        return
    print(f"  {settings['image_a'].name} vs {settings['image_b'].name} ({size(image1)})")
    count = count_pixels(image1, image2)
    if count is not None:
        total = image1.shape[0] * image1.shape[1]
        print(f"{count:,} of {total:,} pixels differ: "
              f"{count / total * 100}% (percentage difference)")


def run_find(settings: dict) -> None:
    """Prints whether pattern appears in search, and where its top-left corner is."""
    tolerance = settings["tolerance"]
    print("Mode: find, does the pattern image appear somewhere in the search image?")
    pattern, search = read_image(settings["pattern"]), read_image(settings["search"])
    if pattern is None or search is None:
        return
    name, where = settings["pattern"].name, settings["search"].name
    print(f"  pattern  : {name} ({size(pattern)})")
    print(f"  search in: {where} ({size(search)})")
    print(f"  tolerance: {tolerance} (per pixel |dR|+|dG|+|dB|)")
    position = find_pattern(pattern, search, tolerance)
    if position is None:
        print(f"Not found: no position where every pixel of {name} "
              "is within the tolerance.")
    else:
        y, x = position
        print(f"Found {name} at x={x}, y={y} (its top-left corner, counted from the "
              f"top-left of {where}).")

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
    if settings["mode"] not in MODES:
        print("Invalid mode in config.yaml. Choose 'scenes', 'diff' or 'find'.")
        return 1
    # 4. Run the mode
    {"scenes": run_scenes, "diff": run_diff, "find": run_find}[settings["mode"]](settings)
    return 0


# -----------------------------------------------------------------------------------------
#                start
# -----------------------------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
