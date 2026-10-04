# Legacy

Superseded code, kept for reference. Nothing here is run, imported or maintained, and it may need packages the tool's `requirements.txt` no longer pins.

| File | What it was | Superseded | By | Not carried over |
|---|---|---|---|---|
| `old_main.py` | the original renamer (2024), configured by editing variables and `.env` | 2026-06-01 (`e001e9f`, "rework on file renamer") | `../main.py` (prefix add/remove, later in place or copies) | nothing since 2026-10-04: numbered renames, lowercase, extension and custom prefix were ported back as `rename`/`digits`, `lowercase`, `extension`, `prefix`. Differences: a prefix plus a rename gives `<prefix>_<rename>_<NN>` (old: `<prefix>_<rename><NN>`), and every step now shares one preview, confirmation and collision check |

## Changes
- 2026-10-04 — its features ported to `main.py` (`rename`, `digits`, `lowercase`, `extension`, `prefix`); its `.env` template `..example-env` removed from the tool folder, git history keeps it
- 2026-10-04 — `old_main.py` moved here from the tool folder instead of being deleted
