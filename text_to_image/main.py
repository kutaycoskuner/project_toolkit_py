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
from PIL import Image, ImageDraw, ImageFont
from matplotlib import font_manager
import os
from dotenv import load_dotenv
import argparse

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


def hex_to_rgb(hex_color: str):
    """Convert hex string like '#1e88e5' to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

class TextImage:
    def __init__(
        self,
        width=1920,
        height=1080,
        bg_color="#000000",
        font_size=80,
        v_margin=0.1,  # vertical margin % of height
        h_margin=0.1,  # horizontal margin % of width
        alignment="center"  # "left", "center", "right"
    ):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.font_size = font_size
        self.v_margin = v_margin
        self.h_margin = h_margin
        self.alignment = alignment
        self.img = Image.new("RGB", (width, height), color=hex_to_rgb(bg_color))
        self.draw = ImageDraw.Draw(self.img)
        try:
            font_path = font_manager.findfont("Courier New")
            self.font = ImageFont.truetype(font_path, font_size)
        except:
            self.font = ImageFont.load_default()
        self.rows = {}  # row_number -> list of (text, color)

    def add_phrase(self, row_number, text, color="#FFFFFF"):
        if row_number not in self.rows:
            self.rows[row_number] = []
        self.rows[row_number].append((text, color))
    def _adjust_font_size(self):
        """Scale font size so the longest row fits exactly within horizontal margins."""
        # Find max character count in any row
        max_chars = 0
        for row_parts in self.rows.values():
            row_text = "".join(text for text, _ in row_parts)
            max_chars = max(max_chars, len(row_text))

        available_width = self.width * (1 - 2 * self.h_margin)
        if max_chars == 0:
            return

        # Binary search optimal font size based on 'M' width
        low, high = 5, 500
        target_size = self.font_size
        font_path = font_manager.findfont("Courier New")

        while low <= high:
            mid = (low + high) // 2
            try:
                font = ImageFont.truetype(font_path, mid)
            except:
                font = ImageFont.load_default()
            bbox = font.getbbox("M" * max_chars)
            row_width = bbox[2] - bbox[0]

            if row_width < available_width:
                target_size = mid
                low = mid + 1
            else:
                high = mid - 1

        self.font_size = target_size
        self.font = ImageFont.truetype(font_path, target_size)
        self.line_height = int(self.font_size * 1.2)
        
    def draw_frame(self, top_row, bottom_row, color="#555555", width=3):
        """Draw a frame around rows with padding: 2 rows up/down, 50% side margins."""
        # Ensure font/line_height is ready
        if not hasattr(self, "line_height"):
            self._adjust_font_size()

        top_y = self.height * self.v_margin + (top_row - 2) * self.line_height
        bottom_y = self.height * self.v_margin + (bottom_row + 3) * self.line_height
        left_x = self.width * (self.h_margin * 0.5)
        right_x = self.width * (1 - self.h_margin * 0.5)

        self.draw.rectangle(
            [left_x, top_y, right_x, bottom_y],
            outline=hex_to_rgb(color),
            width=width
        )

        
    def add_heading(self, text, color="#FFFFFF", bg_color="#222222"):
        """Draw a heading bar above the frame, like a terminal tab."""
        heading_height = int(self.line_height * 1.5)
        left_x = self.width * (self.h_margin * 0.5)
        right_x = self.width * (1 - self.h_margin * 0.5)

        # Draw background bar
        self.draw.rectangle(
            [left_x, self.v_margin * self.height - heading_height,
            right_x, self.v_margin * self.height],
            fill=hex_to_rgb(bg_color)
        )

        # Center text
        bbox = self.draw.textbbox((0, 0), text, font=self.font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        y = int(self.v_margin * self.height - heading_height * 0.75)

        self.draw.text((x, y), text, fill=hex_to_rgb(color), font=self.font)

    def render_rows(self):
        if not self.rows:
            return

        self._adjust_font_size()

        row_count = max(self.rows.keys()) + 1
        available_height = self.height * (1 - 2 * self.v_margin)
        total_height = self.line_height * row_count
        start_y = self.height * self.v_margin + (available_height - total_height) / 2

        for row_number in sorted(self.rows.keys()):
            row_parts = self.rows[row_number]
            y = start_y + row_number * self.line_height

            # LEFT alignment: always start from left margin
            x = self.width * self.h_margin

            # Draw text sequentially
            for text, color in row_parts:
                self.draw.text((x, y), text, fill=hex_to_rgb(color), font=self.font)
                bbox = self.draw.textbbox((x, y), text, font=self.font)
                text_width = bbox[2] - bbox[0]
                x += text_width

    def save(self, out_name="text_image.png"):
        self.render_rows()
        out_path = os.path.join(OUTPUT_DIR, out_name)
        self.img.save(out_path)
        print(f"Saved {out_path}")
        
def test01(ti):
        # Row 0
        ti.add_phrase(0, "def ", "#66bb6a")
        ti.add_phrase(0, "hello_world():", "#1e88e5")
        # Row 1
        ti.add_phrase(1, "    print(", "#fdd835")
        ti.add_phrase(1, "'Hello, World!'", "#ab47bc")
        ti.add_phrase(1, ")", "#fdd835")
        # Row 2
        ti.add_phrase(2, "    return True", "#66bb6a")

        ti.save("syntax_highlight_margin_alignment.png")
        
def test02(ti):
        # Row 0
        ti.add_phrase(0, "class ", "#66bb6a")
        ti.add_phrase(0, "Person:", "#1e88e5")

        # Row 1
        ti.add_phrase(1, "    def ", "#66bb6a")
        ti.add_phrase(1, "__init__", "#e53935")
        ti.add_phrase(1, "(self, name, age):", "#fdd835")

        # Row 2
        ti.add_phrase(2, "        self.name = ", "#fdd835")
        ti.add_phrase(2, "name", "#ab47bc")

        # Row 3
        ti.add_phrase(3, "        self.age = ", "#fdd835")
        ti.add_phrase(3, "age", "#ab47bc")

        # Row 4
        ti.add_phrase(4, "    def ", "#66bb6a")
        ti.add_phrase(4, "greet", "#1e88e5")
        ti.add_phrase(4, "(self):", "#fdd835")

        # Row 5
        ti.add_phrase(5, "        print(", "#fdd835")
        ti.add_phrase(5, "'Hello, my name is '", "#ab47bc")
        ti.add_phrase(5, ", self.name)", "#fdd835")

        # Save
        ti.save("class_test.png")

def enter_your_text(ti):
    # Row 0
    ti.add_phrase(0, "# ", "#AAAAAA")
    ti.add_phrase(0, "Create a symlink to a file", "#FFFFFF")

    # Row 1
    ti.add_phrase(1, "New-Item ", "#00FF7F")       # command
    ti.add_phrase(1, "-ItemType ", "#00E5FF")      # parameter
    ti.add_phrase(1, "SymbolicLink ", "#FF66FF")   # special keyword
    ti.add_phrase(1, "-Path ", "#00E5FF")
    ti.add_phrase(1, '"C:\\symlinks\\config.txt" ', "#FFFF66")  # string
    ti.add_phrase(1, "-Target ", "#00E5FF")
    ti.add_phrase(1, '"C:\\realdata\\config.txt"', "#FFFF66")

    # Row 2 (empty spacer)
    ti.add_phrase(2, "", "#FFFFFF")

    # Row 3
    ti.add_phrase(3, "# ", "#AAAAAA")
    ti.add_phrase(3, "Create a symlink to a folder", "#FFFFFF")

    # Row 4
    ti.add_phrase(4, "New-Item ", "#00FF7F")
    ti.add_phrase(4, "-ItemType ", "#00E5FF")
    ti.add_phrase(4, "SymbolicLink ", "#FF66FF")
    ti.add_phrase(4, "-Path ", "#00E5FF")
    ti.add_phrase(4, '"C:\\symlinks\\ProjectData" ', "#FFFF66")
    ti.add_phrase(4, "-Target ", "#00E5FF")
    ti.add_phrase(4, '"D:\\Projects\\BigProject"', "#FFFF66")
    
    # # Draw frame around rows 0 → 4
    # ti.draw_frame(0, 4, color="#00E5FF", width=4)

    # # Add heading
    # ti.add_heading("PowerShell – symlink_example.ps1", color="#FFFFFF", bg_color="#1E1E1E")

    # Save
    ti.save("20250927-devlog-symlinks.png")

        
        
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
        print("> normal mode")
        ti = TextImage(
        width=1920,
        height=1080,
        bg_color="#101010",
        font_size=100,
        v_margin=0.05,
        h_margin=0.05,
        alignment="center"  # try "left", "center", "right"
        )
        enter_your_text(ti)




# ----------------------------------------------------------------------------------------
#                start
# ----------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
