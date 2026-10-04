<h1 align="center">
    Repetitive XML
</h1>

<p align="center">
    Generates XML elements from a pattern (any tags, attributes and nesting, with repeated children) and inserts them into an XML file: for long, repetitive entries such as one cooldown trigger per second, which would be error-prone by hand.
</p>

<p align="center">
    <img alt="Template" src="https://img.shields.io/badge/template-3.1.1-blue" />
    <img alt="Last Update" src="https://img.shields.io/github/last-commit/kutaycoskuner/project_toolkit_py?path=repetitive_xml" />
</p>

------------------------------------------------------------------------------------------

## Folders

```bash
repetitive_xml/
├── .venv/              # Virtual environment (gitignored)
├── example/
│   ├── input/          # cooldowns.xml: a small Razor-style cooldown file (committed)
│   └── output/         # The generated copy from the example run (gitignored)
├── legacy/             # The original cooldown-only generator, kept for reference; see legacy/README.md
├── config.yaml         # Your files and patterns (gitignored, offered on the first run)
├── config.example.yaml # Defaults: adds two cooldown entries to the example (committed)
├── main.py             # Entry point; its header docstring explains the pattern and steps
├── README.md
└── requirements.txt    # Pinned dependencies
```

------------------------------------------------------------------------------------------

## Usage

```bash
python main.py                                   # Usage guide only, does nothing
python main.py --run                             # Generate into example/output/
python main.py --run --dry-run                   # Preview the generated XML, write nothing
python main.py --input D:/razor/cooldowns.xml --output D:/razor/cooldowns_new.xml
python main.py --help                            # All flags
```

- The pattern (`elements` in `config.yaml`): a list of elements, each with
    - `tag`: the element name
    - `attributes`: `name: value` pairs; values may use `{placeholders}`; `true`/`false` are written as `True`/`False`
    - `children`: a list of elements, nested the same way
    - `repeat` (optional): `{name: duration, from: 0, to: 120, step: 1}` generates the element once per value
        - `{duration}` (the repeat's `name`) holds the value
        - `{time}`, `{minutes}`, `{seconds}` read it as seconds: `65` → `1m 5s`, `1`, `5`; `60` → `1m`; `0` → `0s`
        - placeholders come from every repeat around an element, so repeats can be nested
- Example: one trigger per second, as in the shipped config
    ```yaml
    elements:
      - tag: cooldownentry
        attributes: {name: Rope, defaultcooldown: 120, cooldownbartype: Regular, hue: 188, hidewheninactive: false}
        children:
          - tag: trigger
            repeat: {name: duration, from: 0, to: 120}
            attributes:
              triggertype: SysMessage
              duration: "{duration}"
              triggertext: "You must wait another {time} before you may cast that spell again while in combat."
    ```
    generates
    ```xml
    <cooldownentry name="Rope" defaultcooldown="120" cooldownbartype="Regular" hue="188" hidewheninactive="False">
        <trigger triggertype="SysMessage" duration="0" triggertext="You must wait another 0s before ..." />
        <trigger triggertype="SysMessage" duration="1" triggertext="You must wait another 1s before ..." />
        ...
        <trigger triggertype="SysMessage" duration="65" triggertext="You must wait another 1m 5s before ..." />
        ...
    </cooldownentry>
    ```
- Example: any other XML, with nested repeats
    ```yaml
    insert_before: "</shop>"
    elements:
      - tag: shelf
        repeat: {name: row, from: 1, to: 2}
        attributes: {id: "shelf-{row}"}
        children:
          - tag: item
            repeat: {name: slot, from: 1, to: 3}
            attributes: {code: "R{row}-S{slot}"}
    ```
    gives two `<shelf id="shelf-1">` … `<shelf id="shelf-2">` elements with three `<item code="R1-S1" />` … children each
- Inserting
    - the elements go on their own lines right before the first `insert_before` text (use the parent's closing tag, e.g. `</cooldowns>`, which appears once)
    - `indent: auto` indents like the input file (its first indented line: tabs, 2 or 4 spaces), or set it, e.g. `"    "`
    - the rest of the file is copied unchanged into `output`; the input is never changed
- Values
    - attribute values are XML-escaped (`&`, `<`, `>`, `"`), so write them as plain text
    - a `{placeholder}` no repeat defines stops the run and names it; write a literal brace as `{{` or `}}`
- First run
    - `config.yaml` doesn't exist in a fresh checkout (it's gitignored); the first real run asks whether to create it from `config.example.yaml`
    - on `n`, without a terminal, or with `--dry-run`, nothing is created and `config.example.yaml` is used for that run
- Example data
    - as shipped, the tool adds a `Rope` entry (121 triggers, one per second) and a `Bandage` entry (two fixed triggers) to `example/input/cooldowns.xml`
    - to use your own file, point `input` / `output` in `config.yaml` (or flags) at it, and write your `elements`
- After an update (e.g. a `git pull` that changes `config.example.yaml`)
    - the next run notices the example is newer than your `config.yaml` and asks
        - `m`: new example, your values kept, including your `elements` pattern
        - `r`: fresh copy of the example, your values are lost
        - `k`: keep `config.yaml` as it is; asked again only after the next example change
    - before `m` or `r`, the old file is saved as `config.yaml.bak` (gitignored)
    - without a terminal, or with `--dry-run`, nothing is written
    - every run also warns when `config.yaml` lacks keys the example has (they use defaults) or has keys the tool doesn't read
- Paths (`input`, `output`)
    - what you type decides absolute vs. relative; `relative_to` only matters for relative paths

    | You write | `relative_to` | Resolves to |
    |---|---|---|
    | `input: C:/Users/me/razor/cooldowns.xml` | ignored | exactly that file |
    | `input: example/input/cooldowns.xml` | `tool` (default) | `repetitive_xml/example/input/cooldowns.xml`, from any folder you run it in |
    | `input: cooldowns.xml` | `cwd` | `<folder you run the command in>/cooldowns.xml` |

    - absolute on macOS / Linux: `input: /home/me/razor/cooldowns.xml`
    - Windows: use `/`, or put a path with `\` in single quotes

------------------------------------------------------------------------------------------

## Settings

- Read in this order; later sources override earlier ones
    1. defaults in `main.py`
    2. `config.yaml` (offered on the first real run; until then `config.example.yaml`)
    3. command-line flags
- No `.env`: this tool needs no secrets, so every setting, including your files and patterns, goes in `config.yaml` (gitignored). Should it ever need a secret, add `.env` the way the template does.

| Setting | `config.yaml` | Flag |
|---|---|---|
| XML file to add to | `input` | `--input` |
| File to write | `output` | `--output` |
| Insert before this text | `insert_before` (`"</cooldowns>"`) | — |
| Indentation | `indent` (`auto`) | — |
| The pattern | `elements` | — |
| Base for relative paths | `relative_to` (`tool` / `cwd`) | `--relative-to` |
| Preview only | `dry_run` | `--dry-run` / `--no-dry-run` |

------------------------------------------------------------------------------------------

## Setup Python Environment

### Prerequisites
- **Python 3.10+**: [Install Python](https://www.python.org/downloads/) (includes `pip`).

### Steps

```bash
# 1. Go to the tool's folder
cd project_toolkit_py/repetitive_xml

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
