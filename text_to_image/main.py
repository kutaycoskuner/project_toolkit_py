# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
#                notes
# ----------------------------------------------------------------------------------------
'''
Kutay Coskuner, 2025
This code is licensed under the MIT License. You can use, modify, and distribute it freely.
However, it is provided "as is," without any warranties or guarantees of any kind.
For details, visit: https://opensource.org/licenses/MIT

- description

- metadata

- use case

- install
    - python -m venv .venv
    .venv\Scripts\Activate
    pip freeze > requirements.txt
    - pip install python-dotenv (for using .env values)

- sources

- todo

'''


# ----------------------------------------------------------------------------------------
#                libraries
# ----------------------------------------------------------------------------------------
from PIL import Image
from dotenv import load_dotenv
import argparse
import os

# ----------------------------------------------------------------------------------------
#                variables
# ----------------------------------------------------------------------------------------
load_dotenv()  # Load .env file
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "_output")  # global variable

ENV_TEMPLATE = """
# ------------------------------
# Project Environment Variables
# ------------------------------

OUTPUT_DIR=_output
"""

# ----------------------------------------------------------------------------------------
#                functions
# ----------------------------------------------------------------------------------------
def setup_env():
    if os.path.exists(".env"):
        print(".env already exists. Skipping.")
    else:
        with open(".env", "w") as f:
            f.write(ENV_TEMPLATE)
        print("Created .env file from template.")


def make_black_image(width=1920, height=1080, out_name="black.png"):
    # Ensure the OUTPUT_DIR exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    # Construct full path in OUTPUT_DIR
    out_path = os.path.join(OUTPUT_DIR, out_name)

    # Create black image
    img = Image.new("RGB", (width, height), color=(0, 0, 0))
    img.save(out_path)
    print(f"Saved {out_path}")

# ----------------------------------------------------------------------------------------
#                main
# ----------------------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--setup", action="store_true", help="Create .env file from template")
    args = parser.parse_args()

    if args.setup:
        print("- setup mode")
        setup_env()
    else:
        make_black_image()
        print("> normal mode")



# ----------------------------------------------------------------------------------------
#                start
# ----------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
