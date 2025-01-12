# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
#                notes
# ----------------------------------------------------------------------------------------
'''
Kutay Coskuner, 2025
This code is licensed under the MIT License. You can use, modify, and distribute it freely.
However, it is provided "as is," without any warranties or guarantees of any kind.
For details, visit: https://opensource.org/licenses/MIT

- description: Update metadata in Markdown files using a new template structure.
- metadata: Merges old metadata with new defaults.
- use case: For bulk updating metadata in Markdown files.
- install:
    - pip install pyyaml python-dotenv
'''

# ----------------------------------------------------------------------------------------
#                libraries
# ----------------------------------------------------------------------------------------
import os
import re
import yaml
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ----------------------------------------------------------------------------------------
#                variables
# ----------------------------------------------------------------------------------------
new_metadata_defaults = {
    'template': '1.6',
    'revision': '1.3',
    'title': '',
    'description': '',
    'category': ['repository'],
    'tags': [],
    'created': '2023-03-01',
    'updated': '2023-03-01',
    'author': 'lichzelg',
    'translator': None,
    'editor': None,
    'image': 'first-blog-post.jpg',
    'image_credit': None,
    'language': 'en',
    'visibility': True,
    'sort_order': 1,
}

input_directory_full_path = os.getenv('INPUT_DIR', '/absolute/path/to/input')
output_directory_full_path = os.getenv(
    'OUTPUT_DIR', '/absolute/path/to/output')


# ----------------------------------------------------------------------------------------
#                functions
# ----------------------------------------------------------------------------------------
class NoQuotesDumper(yaml.Dumper):
    """Custom YAML Dumper to remove quotes and manage spacing"""

    def increase_indent(self, flow=False, indentless=False):
        return super(NoQuotesDumper, self).increase_indent(flow, indentless)


def load_file_content(file_path):
    """Load content from a file"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def extract_metadata(content):
    """Extract metadata from file content using YAML pattern"""
    yaml_pattern = re.compile(r"---\n(.*?)\n---", re.DOTALL)
    match = yaml_pattern.match(content)
    if match:
        old_metadata = yaml.safe_load(match.group(1))
        body = content[match.end():].lstrip()
        return old_metadata, body
    return {}, content


def merge_metadata(old_metadata, default_metadata):
    """Merge old metadata with new defaults"""
    tags = old_metadata.get('tags', [])
    if isinstance(tags, str):  # If it's a string, split by ';' and strip any spaces
        tags = [tag.strip() for tag in tags.split(';') if tag.strip()]
    elif isinstance(tags, list):  # If it's already a list, just strip any spaces
        tags = [tag.strip() for tag in tags if tag.strip()]
    return {
        'template': default_metadata['template'],
        'revision': old_metadata.get('version', default_metadata['revision']),
        'title': old_metadata.get('title', default_metadata['title']),
        'description': old_metadata.get('description', default_metadata['description']),
        'category': default_metadata['category'],
        'tags': tags,
        'created': old_metadata.get('date', default_metadata['created']),
        'updated': datetime.now().strftime('%Y-%m-%d').strip(),
        'author': default_metadata['author'],
        'translator': default_metadata['translator'],
        'editor': default_metadata['editor'],
        'image': default_metadata['image'],
        'image_credit': default_metadata['image_credit'],
        'language': old_metadata.get('language', default_metadata['language']),
        'visibility': old_metadata.get('isVisible', default_metadata['visibility']),
        'sort_order': default_metadata['sort_order'],
    }


def dump_metadata_to_yaml(new_metadata):
    """Convert new metadata to YAML format without quotes"""
    new_metadata_yaml = yaml.dump(
        new_metadata,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
        width=float('inf'),
        Dumper=NoQuotesDumper
    )

    # Remove any remaining quotes around strings
    return new_metadata_yaml.replace('"', '').replace("'", "")


def save_file(content, file_path):
    """Save content to the specified file"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)


def process_markdown_file(file_path, input_directory, output_directory, default_metadata):
    """Process a single markdown file and update its metadata"""
    print(f"Processing file: {file_path}")

    # Load file content and extract metadata
    content = load_file_content(file_path)
    old_metadata, body = extract_metadata(content)

    # Merge old metadata with new defaults
    new_metadata = merge_metadata(old_metadata, default_metadata)

    # Convert new metadata back to YAML format
    new_metadata_yaml = dump_metadata_to_yaml(new_metadata)

    # Prepare the final content with updated metadata
    relative_path = os.path.relpath(file_path, input_directory)
    output_file_path = os.path.join(output_directory, relative_path)

    print(f"Writing updated file to: {output_file_path}")

    # Save updated content to output file
    save_file(f"---\n{new_metadata_yaml}---\n\n{body}", output_file_path)


def update_metadata(input_directory, output_directory, default_metadata):
    """Update metadata in all markdown files in the input directory"""
    print(f"Checking if input directory exists: {input_directory}")
    if not os.path.exists(input_directory):
        raise FileNotFoundError(
            f"Input directory does not exist: {input_directory}")

    print(f"Ensuring output directory exists: {output_directory}")
    os.makedirs(output_directory, exist_ok=True)

    for root, _, files in os.walk(input_directory):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                process_markdown_file(
                    file_path, input_directory, output_directory, default_metadata)


def main():
    """Main function to execute the metadata update process"""
    print("Starting metadata update process.")
    update_metadata(input_directory_full_path,
                    output_directory_full_path, new_metadata_defaults)
    print("Metadata update process completed.")


# ----------------------------------------------------------------------------------------
#                start
# ----------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
