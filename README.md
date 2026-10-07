<h1 align="center">
    Python Toolbox Project
</h1>

<h3 align="center">
    A collection of Python-based toolbox projects for various tasks and utilities.
</h3>

<p align="center">
    <img alt="Python" src="https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white" />
    <img alt="Project Version" src="https://img.shields.io/badge/Version-0.38.1-blue" />
    <img alt="Project Start" src="https://img.shields.io/badge/project_start-17_Mar_2024-blue" />
    <img alt="Last Update" src="https://img.shields.io/github/last-commit/kutaycoskuner/python-toolbox" />
</p>

## Contents

- [Installation and Use](#installation-and-use)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
- [Tools](#tools): every tool has its own README
    - [Code Snippet Renderer](#code-snippet-renderer): styled images of code snippets
        - [code_snippet_renderer/README.md](code_snippet_renderer/README.md): [Folders](code_snippet_renderer/README.md#folders) · [Usage](code_snippet_renderer/README.md#usage) · [Settings](code_snippet_renderer/README.md#settings) · [Setup](code_snippet_renderer/README.md#setup-python-environment)
    - [File Renamer](#file-renamer): bulk-rename files (prefix, numbered rename, lowercase, extension)
        - [file_renamer/README.md](file_renamer/README.md): [Folders](file_renamer/README.md#folders) · [Usage](file_renamer/README.md#usage) · [Settings](file_renamer/README.md#settings) · [Setup](file_renamer/README.md#setup-python-environment)
    - [Graph Visualizer](#graph-visualizer): plot a timing cycle for animations
        - [graph_visualizer/README.md](graph_visualizer/README.md): [Folders](graph_visualizer/README.md#folders) · [Usage](graph_visualizer/README.md#usage) · [Settings](graph_visualizer/README.md#settings) · [Setup](graph_visualizer/README.md#setup-python-environment)
    - [ID-Name Mapper](#id-name-mapper): swap file names between IDs and readable names, from a mapping file
        - [id_name_mapper/README.md](id_name_mapper/README.md): [Folders](id_name_mapper/README.md#folders) · [Usage](id_name_mapper/README.md#usage) · [Settings](id_name_mapper/README.md#settings) · [Setup](id_name_mapper/README.md#setup-python-environment)
    - [Image Resizer](#image-resizer): resize every image in a folder to one size
        - [image_resizer/README.md](image_resizer/README.md): [Folders](image_resizer/README.md#folders) · [Usage](image_resizer/README.md#usage) · [Settings](image_resizer/README.md#settings) · [Setup](image_resizer/README.md#setup-python-environment)
    - [Markdown Tools](#markdown-tools): front matter migrator, PDF-text formatter, time-log parser
        - [markdown_frontmatter_migrator/README.md](markdown_frontmatter_migrator/README.md): [Folders](markdown_frontmatter_migrator/README.md#folders) · [Usage](markdown_frontmatter_migrator/README.md#usage) · [Settings](markdown_frontmatter_migrator/README.md#settings) · [Setup](markdown_frontmatter_migrator/README.md#setup-python-environment)
        - [markdown_formatter/README.md](markdown_formatter/README.md): [Folders](markdown_formatter/README.md#folders) · [Usage](markdown_formatter/README.md#usage) · [Settings](markdown_formatter/README.md#settings) · [Setup](markdown_formatter/README.md#setup-python-environment)
        - [markdown_timelog_parser/README.md](markdown_timelog_parser/README.md): [Folders](markdown_timelog_parser/README.md#folders) · [Usage](markdown_timelog_parser/README.md#usage) · [Settings](markdown_timelog_parser/README.md#settings) · [Setup](markdown_timelog_parser/README.md#setup-python-environment)
    - [Pixel Matcher](#pixel-matcher): compare frames, measure pixel differences, find an image in an image
        - [pixel_matcher/README.md](pixel_matcher/README.md): [Folders](pixel_matcher/README.md#folders) · [Usage](pixel_matcher/README.md#usage) · [Settings](pixel_matcher/README.md#settings) · [Setup](pixel_matcher/README.md#setup-python-environment)
    - [Posture Reminder](#posture-reminder): flash a reminder text on the screen at an interval
        - [posture_reminder/README.md](posture_reminder/README.md): [Folders](posture_reminder/README.md#folders) · [Usage](posture_reminder/README.md#usage) · [Settings](posture_reminder/README.md#settings) · [Setup](posture_reminder/README.md#setup-python-environment)
    - [Repetitive Text](#repetitive-text): write numbered command lines from a template
        - [repetitive_text/README.md](repetitive_text/README.md): [Folders](repetitive_text/README.md#folders) · [Usage](repetitive_text/README.md#usage) · [Settings](repetitive_text/README.md#settings) · [Setup](repetitive_text/README.md#setup-python-environment)
    - [Repetitive XML](#repetitive-xml): generate repetitive XML elements from a pattern
        - [repetitive_xml/README.md](repetitive_xml/README.md): [Folders](repetitive_xml/README.md#folders) · [Usage](repetitive_xml/README.md#usage) · [Settings](repetitive_xml/README.md#settings) · [Setup](repetitive_xml/README.md#setup-python-environment)
    - [Text Recognizer (PDF)](#text-recognizer-pdf): PDFs to Markdown, with OCR for scanned pages
        - [text_recognition_pdf/README.md](text_recognition_pdf/README.md): [Folders](text_recognition_pdf/README.md#folders) · [Usage](text_recognition_pdf/README.md#usage) · [Settings](text_recognition_pdf/README.md#settings) · [Setup](text_recognition_pdf/README.md#setup-python-environment)
- [Tool template](_template/README.md): the starting point for new and standardized tools
    - [Folders](_template/README.md#folders) · [Usage](_template/README.md#usage) · [Settings](_template/README.md#settings) · [Setup](_template/README.md#setup-python-environment) · [Template](_template/README.md#template-delete-this-section-in-a-copy)
    - [CHANGELOG.md](_template/CHANGELOG.md): template versions and how to upgrade a tool

------------------------------------------------------------------------------------------

# Installation and Use

### Prerequisites
- **Git**: [Install Git](https://git-scm.com/downloads) for cloning the repository.
- **Python 3.10+**: [Install Python](https://www.python.org/downloads/) (includes `pip`).
- A work environment: IDE, text editor or terminal.

### Installation

Each tool is self-contained, with its own virtual environment, settings and README. These steps use `file_renamer` as the example; swap in any tool's folder name.

```bash
# 1. Clone the repository
git clone https://github.com/kutaycoskuner/python-toolbox.git
cd python-toolbox

# 2. Go to the tool's folder
cd file_renamer

# 3. Create a virtual environment (once per tool)
python -m venv .venv

# 4. Activate it
#   Windows:
.venv\Scripts\activate
#   macOS / Linux:
source .venv/bin/activate

# 5. Install the tool's dependencies
pip install -r requirements.txt

# 6. Create your .env from the example; it holds secrets only (API keys, tokens) and may stay empty.
#    Paths and other settings go in the tool's config.yaml, offered on the first run.
#   Windows:
copy .env.example .env
#   macOS / Linux:
cp .env.example .env

# 7. Run it: without arguments it only prints its usage guide
python main.py
python main.py --run

# 8. Deactivate the environment when done (optional)
deactivate
```

Details for each tool, including its flags and settings, are in that tool's own `README.md`.

------------------------------------------------------------------------------------------

# Tools

Each tool lives in its own folder, with a `README.md` there for its usage, settings and setup.

### Code Snippet Renderer
Renders code snippets, written as coloured text pieces in a JSON file, as images (1920×1080 by default) with an auto-fitted monospace font and an optional rounded code-block frame with a title; size, colours, font and margins are set in `config.yaml`.
- **Use case**: Code snippets and documentation graphics for presentations, tutorials or social media.
- **Folder**: [code_snippet_renderer/](code_snippet_renderer/README.md)
- **Last update**: `2026-10-05`

### File Renamer
Bulk-renames the files in a folder: adds or removes a prefix (the folder's name by default), renames to a numbered template, lower-cases names and changes extensions, in place or as renamed copies. It previews every rename and asks for confirmation; `--dry-run` previews without changing anything.
- **Use case**: Organizing images, files and assets with consistent names.
- **Folder**: [file_renamer/](file_renamer/README.md)
- **Last update**: `2026-10-04`

### Graph Visualizer
Plays a wait → expand → wait → collapse value cycle in real time and plots it; timing, cap and sampling are set in `config.yaml`, and the graph and samples can be saved (`graph.png`, `samples.csv`).
- **Use case**: Finding the right timing function for animations.
- **Folder**: [graph_visualizer/](graph_visualizer/README.md)
- **Last update**: `2026-10-04`

### ID-Name Mapper
Swaps file names between an ID and a readable name: from a mapping file of `id: name` lines, `to_name` renames `0x0A3C.png` to `backpack-0x0A3C.png` (a `/` in a name sorts it into folders: `gump/button-0x00D4.png`) and `to_id` renames it back to the root folder; IDs match ignoring case, collisions and unmapped IDs are reported, in place or as renamed copies, with a preview and a y/n confirmation.
- **Use case**: Working with folders whose file names must stay IDs for a program to find them, while you need to tell the files apart.
- **Folder**: [id_name_mapper/](id_name_mapper/README.md)
- **Last update**: `2026-10-07`

### Image Resizer
Resizes every image in a folder to one fixed size (default 1024×1024, set in `config.yaml` or with `--size`) into an output folder; the originals are never changed.
- **Use case**: Preparing large texture sets for game development or 3D projects.
- **Folder**: [image_resizer/](image_resizer/README.md)
- **Last update**: `2026-10-04`

### Markdown Tools
Tools to automate and format Markdown documents.
- `markdown_frontmatter_migrator` (was `markdown_metadata_template_changer`): rewrites the `---` front matter of every Markdown file in a folder to a new template, carrying selected old values over; the template and mapping live in `config.yaml`; see [its README](markdown_frontmatter_migrator/README.md). Last update: `2026-10-04`.
- `markdown_formatter`: cleans text extracted from PDFs into readable Markdown (paragraphs joined, headings spaced, quotes with citations split); see [its README](markdown_formatter/README.md). Last update: `2026-10-04`.
- `markdown_timelog_parser`: turns hand-written Markdown time logs (`- 20250927 21.04-22.05`) into `sessions.csv` and `summary.csv` with totals per month and day; see [its README](markdown_timelog_parser/README.md). Last update: `2026-10-04`.
- **Use case**: Formatting and batch-revising Markdown files.
- **Folders**: [markdown_frontmatter_migrator/](markdown_frontmatter_migrator/), [markdown_formatter/](markdown_formatter/), [markdown_timelog_parser/](markdown_timelog_parser/)

### Pixel Matcher
Compares images pixel by pixel in three modes: `scenes` checks rendered frames against reference frames within a colour tolerance, `diff` gives the percentage of differing pixels, `find` locates a small image inside a larger one.
- **Use case**: A testing tool for 3D rendering projects, to detect unintended scene changes.
- **Folder**: [pixel_matcher/](pixel_matcher/README.md)
- **Last update**: `2026-10-04`

### Posture Reminder
Flashes a short text ("Dik dur!") on top of everything for a few seconds, every N minutes, until `Ctrl+C`; as shipped, white outlined text without a box near the bottom of the screen. Message, timing, position (anchor + offset), font, outline and an optional background box are set in `config.yaml` or with flags.
- **Use case**: A reminder to sit or stand straight during long sessions at the computer.
- **Folder**: [posture_reminder/](posture_reminder/README.md)
- **Last update**: `2026-10-06`

### Repetitive Text
Writes one line per number from `start` to `end` (counting by `step`) into a text file, from a line template such as `pushlist spellbook_scrolls {i}`; all set in `config.yaml` or with flags.
- **Use case**: Generating long, numbered command lists for scripts.
- **Folder**: [repetitive_text/](repetitive_text/README.md)
- **Last update**: `2026-10-05`

### Repetitive XML
Generates XML elements from a pattern in `config.yaml` (any tags, attributes and nesting, with repeated children such as one `<trigger>` per second and `{time}` placeholders like `1m 5s`) and inserts them into a copy of an XML file.
- **Use case**: Writing long, repetitive XML entries that would be error-prone by hand.
- **Folder**: [repetitive_xml/](repetitive_xml/README.md)
- **Last update**: `2026-10-05`

### Text Recognizer (PDF)
Turns PDFs into Markdown text files: each page is read from its text layer, and pages that are only an image (scans) are read with OCR (Tesseract).
- **Use case**: Pulling the text out of human-readable documents.
- **Folder**: [text_recognition_pdf/](text_recognition_pdf/README.md)
- **Last update**: `2026-10-05`

------------------------------------------------------------------------------------------

For bug reports, feature requests and suggestions, please use the [issue tracker](https://github.com/kutaycoskuner/python-toolbox/issues).
