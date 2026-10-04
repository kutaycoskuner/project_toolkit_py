<h1 align="center">
    Pixel Matcher
</h1>

<p align="center">
    Compares images pixel by pixel: checks rendered frames against reference frames, measures how many pixels differ, or finds a small image inside a larger one. Built to catch unintended scene changes in a 3D renderer.
</p>

<p align="center">
    <img alt="Template" src="https://img.shields.io/badge/template-3.1.1-blue" />
    <img alt="Last Update" src="https://img.shields.io/github/last-commit/kutaycoskuner/project_toolkit_py?path=pixel_matcher" />
</p>

------------------------------------------------------------------------------------------

## Folders

```bash
pixel_matcher/
├── .venv/              # Virtual environment (gitignored)
├── example/
│   └── input/          # Sample images (committed)
│       ├── scenes/     # scene0 (identical pair) and scene1 (one pixel differs)
│       └── find/       # pattern*.jpg to look for, find_pattern*.jpg to search in
├── config.yaml         # Your settings and paths (gitignored, offered on the first run)
├── config.example.yaml # Defaults: checks the example scenes (committed)
├── main.py             # Entry point; its header docstring explains the modes and steps
├── README.md
└── requirements.txt    # Pinned dependencies
```

------------------------------------------------------------------------------------------

## Usage

```bash
python main.py                                   # Usage guide only, does nothing
python main.py --run                             # scenes: check the example scene pairs
python main.py --run --mode diff                 # diff: % of differing pixels in the example pair
python main.py --run --mode find                 # find: locate the example pattern (takes ~10 s)
python main.py --run --scenes D:/renders/frames --tolerance 30
python main.py --run --mode find --pattern D:/icon.png --search D:/screenshot.png
python main.py --help                            # All flags
```

- Modes (`mode`)
    - `scenes`: a regression check for rendered frames. For every pair `scene<N>_base.png` (the reference) / `scene<N>_test.png` (the new render) in the `scenes` folder, N = 0, 1, … until a pair is missing:
        - `MATCH` when every pixel is within the tolerance
        - `DIFFERENT` with the number of pixels above it, or with both sizes when they differ
        - a summary at the end, e.g. `2 of 3 scenes match.`
    - `diff`: how many pixels differ at all between `image_a` and `image_b` (same size), as a count and a percentage; no tolerance, any colour change counts
    - `find`: whether `pattern` appears somewhere in `search` within the tolerance, and where its top-left corner is (`x`, `y`, counted from the top-left of `search`)
- Example output
    ```text
    Mode: scenes, does every test frame still match its base frame?
      folder   : ...\pixel_matcher\example\input\scenes
      tolerance: 60 (per pixel |dR|+|dG|+|dB|, 0..765; pixels at or below it count as equal)
    Scene 0: MATCH      scene0_base.png vs scene0_test.png (458x557): every pixel within the tolerance
    Scene 1: MATCH      scene1_base.png vs scene1_test.png (458x557): every pixel within the tolerance
    2 of 2 scenes match.
    ```
    ```text
    Mode: diff, how many pixels differ at all (no tolerance)?
      scene1_base.png vs scene1_test.png (458x557)
    1 of 255,106 pixels differ: 0.00039199391625441976% (percentage difference)
    ```
    ```text
    Found pattern2.jpg at x=210, y=74 (its top-left corner, counted from the top-left of find_pattern3.jpg).
    ```
- Tolerance (`tolerance`, default 60)
    - how different two pixels' colours may be and still count as equal, measured as `|ΔR| + |ΔG| + |ΔB|`: 0 = identical, 765 = black vs. white
    - the default 60 absorbs small differences such as anti-aliasing or compression noise; lower it to catch subtler changes
    - used by `scenes` and `find`; `diff` counts every changed pixel, so a frame can match in `scenes` and still differ by a few pixels in `diff` (the example's scene1 does: one pixel)
- Results go to the console only; nothing is written
- Speed: the comparison runs pixel by pixel in Python, so `find` with a 50×50 pattern in a 460×560 image takes several seconds
- An image that can't be read is reported by name, and that comparison is skipped
- First run
    - `config.yaml` doesn't exist in a fresh checkout (it's gitignored); the first run asks whether to create it from `config.example.yaml`
    - on `n`, or without a terminal, nothing is created and `config.example.yaml` is used for that run
- Example data
    - `example/input/scenes/`: scene0 is an identical pair, scene1 differs in one pixel (both match at tolerance 60; `diff` shows 0.0004 %)
    - `example/input/find/`: `pattern2.jpg` is found in `find_pattern3.jpg` at (74, 210); `pattern.jpg` isn't found in the two small images
    - to check your own frames, point `scenes` (or the other paths) in `config.yaml` (or flags) elsewhere
- After an update (e.g. a `git pull` that changes `config.example.yaml`)
    - the next run notices the example is newer than your `config.yaml` and asks
        - `m`: new example, your values kept (new keys and comments come from the example; keys it dropped are listed)
        - `r`: fresh copy of the example, your values are lost
        - `k`: keep `config.yaml` as it is; asked again only after the next example change
    - before `m` or `r`, the old file is saved as `config.yaml.bak` (gitignored)
    - without a terminal, nothing is written
    - every run also warns when `config.yaml` lacks keys the example has (they use defaults) or has keys the tool doesn't read
- Paths (`scenes`, `image_a`, `image_b`, `pattern`, `search`)
    - what you type decides absolute vs. relative; `relative_to` only matters for relative paths

    | You write | `relative_to` | Resolves to |
    |---|---|---|
    | `scenes: C:/Users/me/frames` | ignored | exactly that folder |
    | `scenes: example/input/scenes` | `tool` (default) | `pixel_matcher/example/input/scenes`, from any folder you run it in |
    | `scenes: frames` | `cwd` | `<folder you run the command in>/frames` |

    - absolute on macOS / Linux: `scenes: /home/me/frames`
    - Windows: use `/`, or put a path with `\` in single quotes

------------------------------------------------------------------------------------------

## Settings

- Read in this order; later sources override earlier ones
    1. defaults in `main.py`
    2. `config.yaml` (offered on the first run; until then `config.example.yaml`)
    3. command-line flags
- No `.env`: this tool needs no secrets, so every setting, including your paths, goes in `config.yaml` (gitignored). Should it ever need a secret, add `.env` the way the template does.

| Setting | `config.yaml` | Flag |
|---|---|---|
| Mode | `mode` (`scenes` / `diff` / `find`) | `--mode` |
| Per-pixel tolerance | `tolerance` (`60`) | `--tolerance` |
| Scene pairs folder | `scenes` | `--scenes` |
| Images to diff | `image_a`, `image_b` | `--image-a`, `--image-b` |
| Pattern / image to search | `pattern`, `search` | `--pattern`, `--search` |
| Base for relative paths | `relative_to` (`tool` / `cwd`) | `--relative-to` |

------------------------------------------------------------------------------------------

## Setup Python Environment

### Prerequisites
- **Python 3.10+**: [Install Python](https://www.python.org/downloads/) (includes `pip`).

### Steps

```bash
# 1. Go to the tool's folder
cd project_toolkit_py/pixel_matcher

# 2. Create a virtual environment
python -m venv .venv

# 3. Activate it
#   Windows:
.venv\Scripts\activate
#   macOS / Linux:
source .venv/bin/activate

# 4. Install dependencies (OpenCV, NumPy, PyYAML)
pip install -r requirements.txt

# 5. Run it (config.yaml is offered on the first run)
python main.py --run

# 6. Deactivate the environment when done (optional)
deactivate
```
