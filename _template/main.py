# -----------------------------------------------------------------------------------------
#   author          : Kutay Coskuner
#   ai-contributors : Claude Opus 5.5 (claude-opus-5-5)
#   last update     : 2026-10-04
#   template        : 2.0.0
#   disclaimer      : Provided as is, without warranty of any kind; use at your own risk.
#                     Check outputs before relying on them.
# -----------------------------------------------------------------------------------------
"""
<One line: what this tool is.>

<What it does: 1-5 lines.> As shipped, run() is a demo: it writes an upper-cased copy of
every .txt file in the input folder to the output folder.

1. Bare run prints this guide and exits (no-args-usage-guide).
2. The first real run offers to create config.yaml from config.example.yaml
   (ensure_config).
3. Settings come from CLI flags > .env > config.yaml > DEFAULTS (load_settings).
4. The input folder is processed into the output folder (run).

Requires: this folder's .venv (pip install -r requirements.txt); .env copied from
.env.example (may stay empty). config.yaml and .env are gitignored: personal paths go
there, never into the committed config.example.yaml.

Inputs -> outputs: example/input/ -> example/output/ until config.yaml points elsewhere
(relative paths resolve against this folder).

Run:
    python main.py --run                     process example/input/ into example/output/
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
DEFAULTS = {"input": "example/input", "output": "example/output", "dry_run": False}
ENV_KEYS = {"input": "INPUT_DIR", "output": "OUTPUT_DIR"}

# -----------------------------------------------------------------------------------------
#                functions
# -----------------------------------------------------------------------------------------
def parse_args(argv: list[str]) -> argparse.Namespace:
    """Defines the CLI; flags default to None so unset ones don't override config."""
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--run", action="store_true", help="run with config defaults")
    parser.add_argument("--input", help="input folder (default: example/input/)")
    parser.add_argument("--output", help="output folder (default: example/output/)")
    parser.add_argument("--dry-run", action="store_true", default=None,
                        help="show what would happen, write nothing")
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
            config.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"Created {config.name}; edit it to use your own data.")
            return config
    print("Using config.example.yaml for this run; config.yaml was not created.")
    return example


def load_settings(args: argparse.Namespace) -> dict:
    """
    Merges settings: CLI flags > .env > config.yaml > DEFAULTS.

    Returns:
        Settings with "input"/"output" as absolute Paths (relative ones resolve
        against this folder, not the shell's cwd).
    """
    settings = dict(DEFAULTS)
    config_file = ensure_config(bool(args.dry_run))
    if config_file:
        settings.update(yaml.safe_load(config_file.read_text(encoding="utf-8")) or {})
    load_dotenv(HERE / ".env")
    settings.update({k: os.environ[e] for k, e in ENV_KEYS.items() if os.environ.get(e)})
    settings.update({k: v for k, v in vars(args).items() if v is not None and k != "run"})
    for key in ("input", "output"):
        path = Path(settings[key])
        settings[key] = path if path.is_absolute() else HERE / path
    return settings


def run(settings: dict) -> None:
    """
    Demo work, replace with the tool's own: upper-cases every .txt file into output.

    Writes nothing when settings["dry_run"] is set.
    """
    dry_run = settings["dry_run"]
    print(f"input : {settings['input']}")
    print(f"output: {settings['output']}")
    files = sorted(settings["input"].glob("*.txt"))
    if not files:
        print("No .txt files in the input folder.")
        return
    if not dry_run:
        settings["output"].mkdir(parents=True, exist_ok=True)
    for src in files:
        dst = settings["output"] / src.name
        if dry_run:
            print(f"would write: {dst.name}")
            continue
        dst.write_text(src.read_text(encoding="utf-8").upper(), encoding="utf-8")
        print(f"processed: {src.name} -> {dst}")
    if dry_run:
        print("dry run: nothing written")

# -----------------------------------------------------------------------------------------
#                main
# -----------------------------------------------------------------------------------------
def main(argv: list[str]) -> int:
    # 1. No arguments: usage guide only, never work (no-args-usage-guide)
    if not argv:
        print(__doc__.strip())
        return 0
    # 2.-3. Settings from CLI, .env, config.yaml (created on the first real run), defaults
    settings = load_settings(parse_args(argv))
    if not settings["input"].is_dir():
        print(f"Input folder not found: {settings['input']}")
        return 1
    # 4. Work
    run(settings)
    return 0


# -----------------------------------------------------------------------------------------
#                start
# -----------------------------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
