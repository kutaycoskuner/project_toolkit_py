# Template changelog

Each tool copied from `_template/` records the template version it's on in its `main.py` header (`template        : X.Y.Z`) and in its README's template badge. To upgrade a tool, apply every entry newer than its version, then bump both.

Versions: **major** = the structure or settings contract changed, **minor** = something was added, **patch** = wording or a fix.

## 3.0.0 — 2026-10-04
- `.env` holds secrets only (API keys, tokens), read in code with `os.getenv`; it is no longer a settings source. The README ("`.env` or `config.yaml`?"), `config.example.yaml` and `.env.example` spell out what goes where, with a rule of thumb (would leaking it grant access or cost money? then `.env`) and examples. Paths and settings live only in `config.yaml`, so the two can't silently override each other (a path in `.env` used to beat `config.yaml`). Precedence is now: CLI flags > `config.yaml` > `DEFAULTS`.
- `ensure_config()` creates `config.yaml` as a byte-identical file copy (`shutil.copyfile`), not re-written text, so it diffs cleanly against a later `config.example.yaml`.
- `check_config_keys()`: every run with a `config.yaml` warns when its keys differ from `config.example.yaml` (missing keys use defaults, unknown keys are ignored), because the one-time copy goes stale when the example changes.
- `relative_to` setting (`config.example.yaml`, `--relative-to`): relative paths resolve against the tool's folder (`tool`, default, the previous behaviour) or the current working directory (`cwd`); absolute paths are used as-is; an invalid value stops with a clear message.
- `config.example.yaml` documents absolute and relative path examples; the README has a "Paths" section.
- Tools that change their input files themselves (e.g. renaming) offer `output`: empty = in place, a folder = write changed copies there and leave the originals; their example config writes copies, so the committed example data never changes (see the `tool-settings` skill).
- Major, because `.env` path keys stop working: move them into `config.yaml`.
- How to upgrade a 2.0.0 tool:
  1. remove `ENV_KEYS` and its `settings.update(...)` line; keep `load_dotenv()` for secrets
  2. move every path key from `.env.example` into `config.example.yaml`; tell the user to move their `.env` paths into `config.yaml`
  3. add `relative_to` (`DEFAULTS`, `RELATIVE_TO`, `--relative-to`, the base-path lines in `load_settings()`) and the paths block in `config.example.yaml` and the README
  4. add `check_config_keys()` and call it in `load_settings()` for `config.yaml`
  5. update the README's `.env` mentions, then set both versions to 3.0.0

## 2.0.0 — 2026-10-04
- `config.yaml` is personal and gitignored (root `.gitignore`: `**/config.yaml`); the committed defaults live in `config.example.yaml`, so personal paths never reach git.
- `main.py`:
  - new `ensure_config()`: the first real run asks whether to create `config.yaml` from `config.example.yaml`; on "no", without a terminal, or in a dry run, nothing is written and the example is used for that run; a bare run still writes nothing
  - defaults point at the bundled example data (`example/input/` → `example/output/`)
  - `run()` is a working demo (upper-cased copies of `.txt` files) to replace with the tool's own work
  - a missing input folder is reported with exit code 1 instead of being created
- `example/`: every tool ships sample input that the default config processes (root `.gitignore`: `!**/example/input/`; `example/output/` stays ignored).
- `README.md`: `Folders` tree, first-run and example-data notes, `Settings` table and setup steps updated.
- Major, because the settings contract changed: a copy's committed `config.yaml` has to move to `config.example.yaml`, and its defaults should process its own example data.
- How to upgrade a 1.1.0 tool:
  1. copy `config.yaml` to `config.example.yaml`, strip personal paths, and point it at `example/input/`
  2. add `example/input/` with sample data for the tool
  3. add `ensure_config()` and call it in `load_settings()`
  4. update the README, then set both versions to 2.0.0

## 1.1.0 — 2026-10-04
- `main.py` header: new `ai-contributors` field after `author` (AI model name plus model ID; `unknown (before YYYY-MM-DD)` when it's unclear whether a file had AI help before). All keys are padded to the new width, following `code-file-header` 5.0.0.
- `README.md` uses a new layout based on the user's sample:
  - a centered title and description
  - badges for the template version and the last commit to the tool's folder (`?path=<tool folder>`)
  - 90-character dividers between sections
  - sections: `Folders` (a commented tree), `Usage`, `Settings`, and `Setup Python Environment` (`Prerequisites` and commented `Steps`)
  - the copy instructions moved into a final section that you delete in a copy
- How to upgrade a 1.0.0 tool: add the header field, rebuild the README in the new layout, then set both versions to 1.1.0.

## 1.0.0 — 2026-10-03
- First versioned template. It replaces the unversioned `template.py`, so tools without a `template` field count as pre-1.0.
- `main.py`:
  - Header and module docstring follow `code-file-header`, with 91-character separators and `"""` alone on its first line.
  - Running with no arguments prints usage. `--run` runs with the defaults. `--dry-run`, `--input` and `--output` are available.
  - Settings precedence: command-line flags > `.env` > `config.yaml` > `DEFAULTS`. Relative paths resolve against the tool's own folder.
- `config.yaml` holds behaviour and is committed. `.env.example` lists the keys for secrets and machine-specific paths; the real `.env` is gitignored.
- `requirements.txt` pins `PyYAML==6.0.3` and `python-dotenv==1.0.1`.
- `README.md` covers setup, usage, and where each setting lives.
