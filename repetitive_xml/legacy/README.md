# Legacy

Superseded code, kept for reference. Nothing here is run, imported or maintained.

| File | What it was | Superseded | By | Not carried over |
|---|---|---|---|---|
| `main.py` | the original generator (2025, never committed): one hard-coded `<cooldownentry>` shape with one `<trigger>` per second, configured by a cooldown-specific `config.yaml` (`input_file`, `output_file`, `cooldown: {name, defaultcooldown, …, duration, trigger}`) | 2026-10-04 | `../main.py`: any tags and nesting from an `elements` pattern, several blocks, nested repeats | nothing functional. Deliberate differences: 0 s reads `0s` (was empty: `another  before`), whole minutes read `1m` (was `1m ` plus a double space), output indented like the input file (tabs) instead of 4 spaces, one line per element instead of attributes wrapped onto a second line, attribute values XML-escaped |

## Changes
- 2026-10-04 — `main.py` moved here when the tool was rewritten to a pattern-based generator; it was never in git, so this copy is the only one
