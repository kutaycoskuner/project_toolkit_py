# -----------------------------------------------------------------------------------------
#   author      : Kutay Coskuner
#   last update : 2026-10-03
#   template    : 1.0.0
#   disclaimer  : Provided as is, without warranty of any kind; use at your own risk.
#                 Check outputs before relying on them.
# -----------------------------------------------------------------------------------------
"""
<One line: what this tool is.>

<What it does: 1-5 lines.>

Requires: this folder's .venv (pip install -r requirements.txt); config.yaml;
.env copied from .env.example (may stay empty).

Inputs -> outputs: input/ -> output/ (relative paths resolve against this folder).

Settings precedence: CLI flags > .env > config.yaml > DEFAULTS in main.py.

Run:
    python main.py --run                     process input/ into output/
    python main.py --run --dry-run           show what would happen, write nothing
    python main.py --input <dir> --output <dir>
    python main.py --help                    all flags; see README.md
"""

# -----------------------------------------------------------------------------------------
#                libraries
# -----------------------------------------------------------------------------------------
import argparse
import os
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

# -----------------------------------------------------------------------------------------
#                variables
# -----------------------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
DEFAULTS = {"input": "input", "output": "output", "dry_run": False}
ENV_KEYS = {"input": "INPUT_DIR", "output": "OUTPUT_DIR"}

# -----------------------------------------------------------------------------------------
#                functions
# -----------------------------------------------------------------------------------------
def parse_args(argv: list[str]) -> argparse.Namespace:
    """Defines the CLI; flags default to None so unset ones don't override config."""
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--run", action="store_true", help="run with config defaults")
    parser.add_argument("--input", help="input folder (default: input/)")
    parser.add_argument("--output", help="output folder (default: output/)")
    parser.add_argument("--dry-run", action="store_true", default=None,
                        help="show what would happen, write nothing")
    return parser.parse_args(argv)


def load_settings(args: argparse.Namespace) -> dict:
    """
    Merges settings: CLI flags > .env > config.yaml > DEFAULTS.

    Returns:
        Settings with "input"/"output" as absolute Paths (relative ones resolve
        against this folder, not the shell's cwd).
    """
    settings = dict(DEFAULTS)
    config_file = HERE / "config.yaml"
    if config_file.exists():
        settings.update(yaml.safe_load(config_file.read_text(encoding="utf-8")) or {})
    load_dotenv(HERE / ".env")
    settings.update({k: os.environ[e] for k, e in ENV_KEYS.items() if os.environ.get(e)})
    settings.update({k: v for k, v in vars(args).items() if v is not None and k != "run"})
    for key in ("input", "output"):
        path = Path(settings[key])
        settings[key] = path if path.is_absolute() else HERE / path
    return settings


def run(settings: dict) -> None:
    """<The tool's actual work.> Writes nothing when settings["dry_run"] is set."""
    print(f"input : {settings['input']}")
    print(f"output: {settings['output']}")
    if settings["dry_run"]:
        print("dry run: nothing written")
        return
    settings["input"].mkdir(exist_ok=True)
    settings["output"].mkdir(exist_ok=True)

# -----------------------------------------------------------------------------------------
#                main
# -----------------------------------------------------------------------------------------
def main(argv: list[str]) -> int:
    # 1. No arguments: usage guide only, never work (no-args-usage-guide)
    if not argv:
        print(__doc__.strip())
        return 0
    # 2. Settings from CLI, .env, config.yaml and defaults
    settings = load_settings(parse_args(argv))
    # 3. Work
    run(settings)
    return 0


# -----------------------------------------------------------------------------------------
#                start
# -----------------------------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
