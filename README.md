<h1 align="center">
    Python Toolkit Projects
</h1>

<h3 align="center">
    A collection of Python-based toolkit projects for various tasks and utilities.
</h3>

<p align="right">
    <img alt="Python" src="https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white" />
    <img alt="Project Version" src="https://img.shields.io/badge/Version-0.20.2-blue" />
    <img alt="Project Start" src="https://img.shields.io/badge/project_start-17_Mar_2024-blue" />
    <img alt="Last Update" src="https://img.shields.io/github/last-commit/kutaycoskuner/project_toolkit_py" />
</p>

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
git clone https://github.com/kutaycoskuner/project_toolkit_py.git
cd project_toolkit_py

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
#   tools not yet standardized have no requirements.txt: install the packages listed in their main.py header instead
pip install -r requirements.txt

# 6. Create your .env from the example, then fill in its values (e.g. paths on this machine)
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

Each tool lives in its own folder; standardized tools have a `README.md` there with usage and settings.

### File Renamer
Bulk-renames the files in a folder, adding the folder's name as a prefix or removing it. It previews every rename and asks for confirmation; `--dry-run` previews without changing anything.
- **Use case**: Organizing images, files and assets with consistent names.
- **Folder**: [file_renamer/](file_renamer/README.md)
- **Last update**: `2026-06-01`

### Graph Visualizer
Runs a wait → expand → wait → collapse value cycle in real time and plots it; timing, cap and sampling are set in `config.yaml`.
- **Use case**: Finding the right timing function for animations.
- **Folder**: [graph_visualizer/](graph_visualizer/README.md)
- **Last update**: `2024-04-19`

### Image Resizer
Resizes every image in a folder to one fixed size (default 1024×1024, set in `config.yaml` or with `--size`); the input and output folders come from `.env` or flags.
- **Use case**: Preparing large texture sets for game development or 3D projects.
- **Folder**: [image_resizer/](image_resizer/README.md)
- **Last update**: `2025-02-21`

### Markdown Tools
Tools to automate and format Markdown documents.
- `markdown_metadata_template_changer`: converts a file's `---` frontmatter block from one template to another; the conversion rules have to be declared first. Last update: `2025-01-12`.
- `markdown_formatter`: formats Markdown essays (experimental). Last update: `2025-02-21`.
- `markdown_data_parser`: meant to build structured data from hand-written Markdown files such as time logs (tool skeleton ready, parsing not implemented yet; see [its README](markdown_data_parser/README.md)). Last update: `2024-04-19`.
- **Use case**: Formatting and batch-revising Markdown files.
- **Folders**: [markdown_metadata_template_changer/](markdown_metadata_template_changer/), [markdown_formatter/](markdown_formatter/), [markdown_data_parser/](markdown_data_parser/)

### Pixel Matcher
Compares two images by analyzing pixel color differences.
- **Use case**: A testing tool for 3D rendering projects, to detect unintended scene changes.
- **Folder**: [pixel_matcher/](pixel_matcher/)
- **Last update**: `2024-07-03`

### Repetitive XML
Generates a complete `<cooldownentry>` block from a YAML config (one trigger per second of the configured duration, with minutes, seconds and singular/plural wording calculated) and inserts it into the `<cooldowns>` element of an input XML file.
- **Use case**: Writing long, repetitive XML entries that would be error-prone by hand.
- **Folder**: [repetitive_xml/](repetitive_xml/)
- **Last update**: `not committed yet`

### Text Hardcode
Writes one line per number from `start` to `end` into `output/output.txt`, using a line template such as `pushlist spellbook_scrolls {i}` (all set in `config.yaml` or with flags).
- **Use case**: Generating long, numbered command lists for scripts.
- **Folder**: [text_hardcode/](text_hardcode/README.md)
- **Last update**: `2025-12-28`

### Text Recognizer (PDF)
An OCR (optical character recognition) tool that extracts text from PDFs or images into raw `.txt` or `.md` files.
- **Use case**: Pulling the text out of human-readable documents.
- **Folder**: [text_recognition_pdf/](text_recognition_pdf/)
- **Last update**: `2024-07-10`

### Text to Image (syntax highlighter)
Converts code or text snippets into styled images with customizable syntax highlighting, alignment, margins and framing. Supports titles, headings, and color themes for different platforms (e.g. PowerShell, Python).
- **Use case**: Code snippets and documentation graphics for presentations, tutorials or social media.
- **Folder**: [text_to_image/](text_to_image/)
- **Last update**: `2025-09-27`

------------------------------------------------------------------------------------------

For bug reports, feature requests and suggestions, please use the [issue tracker](https://github.com/kutaycoskuner/project_toolkit_py/issues).
