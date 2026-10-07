<h1 align="center">
    ID-Name Mapper
</h1>

<p align="center">
    Swaps file names between an ID (<code>0x0A3C.png</code>) and a readable name (<code>backpack-0x0A3C.png</code>), from a mapping file you keep.
</p>

<p align="center">
    <img alt="Template" src="https://img.shields.io/badge/template-3.2.0-blue" />
    <img alt="Last Update" src="https://img.shields.io/github/last-commit/kutaycoskuner/python-toolbox?path=id_name_mapper" />
</p>

------------------------------------------------------------------------------------------

- Some programs find files by an ID in the file name, which says nothing to a person
- you give each ID a name once, in a mapping file; then
    - `to_name` renames the files so you can tell them apart: `0x0A3C.png` -> `backpack-0x0A3C.png`
    - `to_id` renames them back, so the program finds them again: `backpack-0x0A3C.png` -> `0x0A3C.png`
- the ID stays in the readable name, so `to_id` needs no mapping and works for every name file
- folders you list under `ignore_folders` in the mapping file (e.g. a backup folder) are skipped in both directions

------------------------------------------------------------------------------------------

## Folders

```bash
id_name_mapper/
├── .venv/              # Virtual environment (gitignored)
├── example/            # Bundled demo data, processed by default
│   ├── input/          # Sample files with IDs (committed)
│   ├── output/         # Result of the demo run (gitignored)
│   └── mapping.yaml    # Sample mapping with ignore_folders (committed)
├── config.yaml         # Your settings, may hold personal paths (gitignored, created on first run)
├── config.example.yaml # Default settings with comments (committed)
├── main.py             # Entry point; its header docstring explains the steps
├── README.md
└── requirements.txt    # Pinned dependencies
```

- no `.env`: the tool needs no secrets

------------------------------------------------------------------------------------------

## Usage

```bash
python main.py                                  # Usage guide only, does nothing
python main.py --run                            # Example: named copies of example/input/ in example/output/
python main.py --run --direction to_id          # Example: name files back to IDs
python main.py --run --dry-run                  # Preview only, change nothing
python main.py --run --input-dir D:/files --mapping D:/files/names.yaml --in-place
python main.py --run --input-dir D:/files --direction to_id --in-place
python main.py --help                           # All flags
```

- Typical use on your own folder
    1. write your mapping file (see below) and set `input_dir`, `mapping` and `output_dir` in `config.yaml`: `""` or the same folder as `input_dir` renames in place
    2. `python main.py --run` gives the files readable names; work with them
    3. `python main.py --run --direction to_id` puts the ID names back before the program needs them
- Every run previews first
    - each planned rename or move, numbered, with paths relative to the input folder
    - files left alone, counted by reason: `already named`, `already an ID`, `in an ignored folder`, `not in the mapping` (these are listed by name, so a missing entry shows up)
    - collisions: a target that already exists (in place) or that two files would both get is skipped and reported, never given a number, since a number would break the ID
    - then `y` applies, anything else cancels; `--dry-run` stops after the preview
- What `to_name` does with each file
    - `0x0A3C.png` with `0x0A3C: backpack` in the mapping -> `backpack-0x0A3C.png`
    - IDs match ignoring case: `0x0a3d.png` finds `0x0A3D`, and the new name keeps the file's own spelling (`shield-0x0a3d.png`), so `to_id` gives back exactly the old name
    - an already named file whose mapping name changed gets the new name: `healthbar-0x0805.png` -> `health-bar-0x0805.png`
    - a `/` in the name sorts the file into folders: `0x00D4: gump/button` -> `gump/button-0x00D4.png` (folders are created as needed)
    - an already named file in a folder moves when its mapping name changes, e.g. to `ui/button`; folders left empty are removed
    - an ID that isn't in the mapping: left alone and listed
- What `to_id` does with each file
    - the part after the last separator is the ID: `backpack-0x0A3C.png` -> `0x0A3C.png`
    - name files in subfolders move back to the root folder (`gump/button-0x00D4.png` -> `0x00D4.png`); folders left empty are removed
    - files without the separator are already IDs and stay as they are, also inside a subfolder
    - the ID is the part after the last separator, so a name may contain it (`health-bar-0x0805.png`); with the default `-`, every file with a `-` in its name counts as a name file
- The mapping file
    - YAML, one `id: name` per line; comments with `#`

        ```yaml
        0x0A3C: backpack
        0x0A3D: shield
        0x0805: health-bar
        0x00D4: gump/button
        ```

    - read as plain text, so `0x0A3C` stays `0x0A3C` (plain YAML would turn it into the number 2620) and no quotes are needed
    - `/` (or `\`) in a name makes folders; every part between them becomes a folder or file name, so a part with `<>:"|?*`, a trailing dot or space, an empty part (`a//b`), `.` or `..`, and an ID listed twice (ignoring case), is reported and left out
    - `ignore_folders`: folder names to skip, in both directions; a reserved key, not an ID

        ```yaml
        ignore_folders: [backup, old]
        ```

        - names, not paths: each matches a folder with that name at any depth, ignoring case (`backup` also skips `Backup/` and `gump/backup/`)
        - files in them are neither renamed nor moved (`to_id` would otherwise flatten them into the root, e.g. `backup/old-0x0A3C.png` -> `0x0A3C.png`)
        - an entry with `/` is reported and left out; a mapping name that would put a file into an ignored folder (`0x0B00: backup/thing`) is reported and left out
        - `to_id` reads the mapping file only for this list; without a mapping file it runs anyway and ignores no folders
    - the mapping file may sit inside the folder being renamed (e.g. `_mapping.yaml`); it's never renamed itself
- First run
    - `config.yaml` doesn't exist in a fresh checkout (it's gitignored); the first real run asks whether to create it from `config.example.yaml`
    - on `n`, without a terminal, or with `--dry-run`, nothing is created and `config.example.yaml` is used for that run
- After an update (e.g. a `git pull` that adds or removes settings in `config.example.yaml`)
    - every run compares the settings (top-level keys) in your `config.yaml` with the example's; when they differ, it lists missing keys (defaults used) and unknown keys (ignored) and asks
        - `m`: new example, your values kept (new keys and comments come from the example; keys it dropped are listed)
        - `r`: fresh copy of the example, your values are lost
        - `k`: keep `config.yaml` as it is; asked again on the next run
    - before `m` or `r`, the old file is saved as `config.yaml.bak` (gitignored)
    - without a terminal, or with `--dry-run`, nothing is written
- Example data
    - as shipped, the tool writes named copies of `example/input/` into `example/output/`, so the samples never change
    - the samples cover the cases above: a mapped ID, a lower-case ID, an ID missing from the mapping, a name file whose name changed, a name with a folder, a file in an ignored folder (`backup/`)
- Paths (`input_dir`, `output_dir`, `mapping`)
    - what you type decides absolute vs. relative; `relative_to` only matters for relative paths

    | You write | `relative_to` | Resolves to |
    |---|---|---|
    | `input_dir: C:/Users/me/images` | ignored | exactly that folder |
    | `input_dir: example/input` | `tool` (default) | `id_name_mapper/example/input`, from any folder you run it in |
    | `input_dir: images` | `cwd` | `<folder you run the command in>/images` |

    - absolute on macOS / Linux: `input_dir: /home/me/images`
    - Windows: use `/`, or put a path with `\` in single quotes

------------------------------------------------------------------------------------------

## Settings

- Read in this order; later sources override earlier ones
    1. defaults in `main.py`
    2. `config.yaml` (offered on the first real run; until then `config.example.yaml`)
    3. command-line flags

| Setting | Flag | Default | Meaning |
|---|---|---|---|
| `relative_to` | `--relative-to` | `tool` | base for relative paths: this tool's folder (`tool`) or the folder you run the command in (`cwd`) |
| `input_dir` | `--input-dir` | `example/input` | folder whose files are renamed; its subfolders are searched too, since named files may sit in folders (skipped: `ignore_folders`, an `output_dir` inside it, the mapping file) |
| `output_dir` | `--output-dir`, `--in-place` | `example/output` | renamed copies go here in the same folder layout, originals stay unchanged (only files that get a new name are copied; existing files there are overwritten); `""`, `--in-place` or the same folder as `input_dir` = rename the files themselves (the preview says so) |
| `mapping` | `--mapping` | `example/mapping.yaml` | mapping file: `id: name` per line, plus `ignore_folders`; `to_id` reads it only for `ignore_folders` and runs without it |
| `direction` | `--direction` | `to_name` | `to_name`: ID -> `name-ID`; `to_id`: `name-ID` -> ID |
| `separator` | `--separator` | `-` | between name and ID; can't be empty or contain `<>:"/\|?*`; a name may contain it, the ID may not |
| `pattern` | `--pattern` | `*` | glob pattern of files inside the folder, e.g. `*.png` |
| `dry_run` | `--dry-run`, `--no-dry-run` | `false` | preview only, change nothing |

- an invalid `relative_to`, `direction` or `separator`, a missing input folder or mapping file, or a mapping that isn't `id: name` lines stops the run with a message
- changing `separator` later: run `to_id` with the old one first, then `to_name` with the new one

------------------------------------------------------------------------------------------

## Setup Python Environment

### Prerequisites
- **Python 3.10+**: [Install Python](https://www.python.org/downloads/) (includes `pip`).

### Steps

```bash
# Go to the tool's folder
cd python-toolbox/id_name_mapper

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
