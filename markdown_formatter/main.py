# ----------------------------------------------------------------------------------------
#                notes
# ----------------------------------------------------------------------------------------
'''
Kutay Coskuner, 2025
This code is licensed under the MIT License. You can use, modify, and distribute it freely.
However, it is provided "as is," without any warranties or guarantees of any kind.
For details, visit: https://opensource.org/licenses/MIT

- description
    This script reads a text file, processes it by removing unwanted line breaks,
    trims unnecessary spaces, and preserves formatting in markdown structures.

- use case
    - Useful for cleaning text extracted from PDFs or markdown files while keeping important formatting.

- install
    - pip install python-dotenv (for using .env values)

- todo
'''

# ----------------------------------------------------------------------------------------
#                libraries
# ----------------------------------------------------------------------------------------

import os
import re
import sys
from dotenv import load_dotenv

# ----------------------------------------------------------------------------------------
#                functions
# ----------------------------------------------------------------------------------------

def clean_text(text):
    """
    - Preserves metadata (--- blocks) exactly as they are, removing unnecessary blank lines.
    - Ensures two before and one after line breaks after titles (#, ##, etc.).
    - Wraps indented text inside plaintext block, removes unnecessary indent, line, breaks and white space inside.
    - Removes unnecessary single line breaks but maintains paragraph separation.
    - Preserves markdown elements like tables and lists.
    - Trims excessive spaces.
    - Adds line breaks before in-text references within plaintext blocks in a second pass.
    """
    lines = text.split("\n")
    cleaned_lines = []
    inside_metadata = False
    metadata_found = False
    last_line_was_blank = True
    inside_code_block = False
    indented_text = []

    # First pass: General formatting
    for i, line in enumerate(lines):
        stripped_line = line.rstrip()

        if stripped_line == "---":
            if not metadata_found:
                metadata_found = True
                inside_metadata = True
            elif inside_metadata:
                inside_metadata = False

            if cleaned_lines and cleaned_lines[-1] == "":
                cleaned_lines.pop()

            cleaned_lines.append("---")
            last_line_was_blank = False
            continue

        if inside_metadata:
            cleaned_lines.append(line)
            last_line_was_blank = False
            continue

        if stripped_line.startswith("```"):
            inside_code_block = not inside_code_block
            cleaned_lines.append(stripped_line)
            if not inside_code_block:
                cleaned_lines.append("")  # Ensure one empty line after code block
            continue

        if inside_code_block:
            cleaned_lines.append(line)
            continue

        if stripped_line.startswith("#"):
            if cleaned_lines and cleaned_lines[-1] != "---":
                cleaned_lines.append("")
            if len(cleaned_lines) > 1 and cleaned_lines[-2] != "":
                cleaned_lines.append("")
            cleaned_lines.append(stripped_line)
            cleaned_lines.append("")
            last_line_was_blank = True
            continue

        if line.startswith("    ") or line.startswith("\t"):
            indented_text.append(stripped_line.lstrip())  # Remove leading spaces
            last_line_was_blank = False
            continue
        elif indented_text:
            # Join indented text with spaces and trim leading/trailing spaces
            plaintext_content = " ".join(indented_text).strip()
            cleaned_lines.append("```plaintext")
            cleaned_lines.append(plaintext_content)
            cleaned_lines.append("```")
            cleaned_lines.append("")
            indented_text = []
            last_line_was_blank = True  # Ensure only one blank line is added
            continue

        if stripped_line:
            if cleaned_lines and not last_line_was_blank:
                cleaned_lines[-1] += " " + stripped_line
            else:
                cleaned_lines.append(stripped_line)
            last_line_was_blank = False
        else:
            if not last_line_was_blank:
                cleaned_lines.append("")
            last_line_was_blank = True

    if cleaned_lines[-1] == "---":
        cleaned_lines.append("")

    # Second pass: Handle in-text references within plaintext blocks
    inside_plaintext_block = False
    final_lines = []

    for line in cleaned_lines:
        if line.startswith("```plaintext"):
            inside_plaintext_block = True
            final_lines.append(line)
            continue
        elif line.startswith("```") and inside_plaintext_block:
            inside_plaintext_block = False
            final_lines.append(line)
            continue

        if inside_plaintext_block:
            # Add line breaks before in-text references
            modified_line = re.sub(r"(\s)(\([^)]+, \d{4}\))", r"\n\2", line)
            final_lines.append(modified_line)
        else:
            final_lines.append(line)

    return "\n".join(final_lines).strip()


def process_file(input_path, output_path):
    if not os.path.isfile(input_path):
        print(f"Error: The file '{input_path}' was not found.")
        return

    if not os.path.isdir(output_path):
        os.makedirs(output_path, exist_ok=True)

    output_file = os.path.join(output_path, "processed_text.md")

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            text = f.read()

        cleaned_text = clean_text(text)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(cleaned_text)

        print(f"Processed text saved to: {output_file}")

    except Exception as e:
        print(f"An error occurred: {e}")


# ----------------------------------------------------------------------------------------
#                main
# ----------------------------------------------------------------------------------------

def main():
    load_dotenv()  # Load environment variables from .env

    input_path = os.getenv("INPUT_PATH") or (sys.argv[1] if len(sys.argv) > 1 else None)
    output_path = os.getenv("OUTPUT_PATH") or (sys.argv[2] if len(sys.argv) > 2 else None)

    if not input_path or not output_path:
        print("Error: Missing input file or output folder.")
        print("Usage: python script.py <input_file> <output_folder>")
        return

    process_file(input_path, output_path)

# ----------------------------------------------------------------------------------------
#                start
# ----------------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
