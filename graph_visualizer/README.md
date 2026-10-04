<h1 align="center">
    Graph Visualizer
</h1>

<p align="center">
    Plays a wait → expand → wait → collapse value cycle in real time and plots it, to find a timing function for animations. The samples and the graph can be saved.
</p>

<p align="center">
    <img alt="Template" src="https://img.shields.io/badge/template-3.1.0-blue" />
    <img alt="Last Update" src="https://img.shields.io/github/last-commit/kutaycoskuner/project_toolkit_py?path=graph_visualizer" />
</p>

------------------------------------------------------------------------------------------

## Folders

```bash
graph_visualizer/
├── .venv/              # Virtual environment (gitignored)
├── example/
│   └── output/         # graph.png and samples.csv from the example run (gitignored)
├── config.yaml         # Your settings (gitignored, offered on the first run)
├── config.example.yaml # Defaults: one ~6 s cycle, saved to example/output/ (committed)
├── main.py             # Entry point; its header docstring explains the steps
├── README.md
└── requirements.txt    # Pinned dependencies
```

------------------------------------------------------------------------------------------

## Usage

```bash
python main.py                                   # Usage guide only, does nothing
python main.py --run                             # One cycle, saved to example/output/, then the plot window
python main.py --run --no-plot                   # Same, without opening a window
python main.py --run --duration 20 --dry-run     # 20 s, console only, nothing saved
python main.py --run --output D:/graphs          # Save graph.png and samples.csv there
python main.py --help                            # All flags
```

- The cycle
    1. `waiting0`: value 0 for `waiting_delay` seconds
    2. `expand`: `|tan(t)|` rises until it passes `cap`
    3. `waiting1`: value `cap` for `waiting_delay` seconds
    4. `collapse`: `|tan(t)|` falls until it drops below `floor`, then back to `waiting0`
    - with the defaults one full cycle takes about 5 seconds
- Output
    - console: one `<value> <unix seconds>` line every `sample_interval` seconds
    - with `output` set: `samples.csv` (`unix_time,value`) and `graph.png`, overwritten on every run
    - with `plot` on: the graph in a window at the end (the x axis is Unix time)
- It runs in real time: the command blocks for `duration` seconds.
- A `cap` far above ~2000 needs a smaller `sample_interval`, or `expand` can jump past it between samples.
- First run
    - `config.yaml` doesn't exist in a fresh checkout (it's gitignored); the first real run asks whether to create it from `config.example.yaml`
    - on `n`, without a terminal, or with `--dry-run`, nothing is created and `config.example.yaml` is used for that run
- Example data
    - this tool has no input files: `config.example.yaml` itself is the example
    - as shipped it runs one cycle and saves it to `example/output/`, so you can see the result before configuring anything
- After an update (e.g. a `git pull` that changes `config.example.yaml`)
    - the next run notices the example is newer than your `config.yaml` and asks
        - `m`: new example, your values kept (new keys and comments come from the example; keys it dropped are listed)
        - `r`: fresh copy of the example, your values are lost
        - `k`: keep `config.yaml` as it is; asked again only after the next example change
    - before `m` or `r`, the old file is saved as `config.yaml.bak` (gitignored)
    - without a terminal, or with `--dry-run`, nothing is written
    - every run also warns when `config.yaml` lacks keys the example has (they use defaults) or has keys the tool doesn't read
- Paths (`output`)
    - what you type decides absolute vs. relative; `relative_to` only matters for relative paths

    | You write | `relative_to` | Resolves to |
    |---|---|---|
    | `output: C:/Users/me/graphs` | ignored | exactly that folder |
    | `output: example/output` | `tool` (default) | `graph_visualizer/example/output`, from any folder you run it in |
    | `output: graphs` | `cwd` | `<folder you run the command in>/graphs` |

    - absolute on macOS / Linux: `output: /home/me/graphs`
    - Windows: use `/`, or put a path with `\` in single quotes

------------------------------------------------------------------------------------------

## Settings

- Read in this order; later sources override earlier ones
    1. defaults in `main.py`
    2. `config.yaml` (offered on the first real run; until then `config.example.yaml`)
    3. command-line flags
- No `.env`: this tool needs no secrets, so every setting goes in `config.yaml` (gitignored). Should it ever need a secret, add `.env` the way the template does.

| Setting | `config.yaml` | Flag |
|---|---|---|
| Run time (s) | `duration` (`20` in code, `6` in the example) | `--duration` |
| Waiting phases (s) | `waiting_delay` | — |
| Top value | `cap` | — |
| Collapse end value | `floor` | — |
| Sample interval (s) | `sample_interval` | — |
| Plot window | `plot` | `--plot` / `--no-plot` |
| Save folder | `output` (`""` = save nothing) | `--output` |
| Base for relative paths | `relative_to` (`tool` / `cwd`) | `--relative-to` |
| Run but save nothing | `dry_run` | `--dry-run` / `--no-dry-run` |

------------------------------------------------------------------------------------------

## Setup Python Environment

### Prerequisites
- **Python 3.10+**: [Install Python](https://www.python.org/downloads/) (includes `pip`).
- A display for the plot window (or use `--no-plot`).

### Steps

```bash
# 1. Go to the tool's folder
cd project_toolkit_py/graph_visualizer

# 2. Create a virtual environment
python -m venv .venv

# 3. Activate it
#   Windows:
.venv\Scripts\activate
#   macOS / Linux:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run it (config.yaml is offered on the first run)
python main.py --run

# 6. Deactivate the environment when done (optional)
deactivate
```
