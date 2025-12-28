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
    - pip install python-dotenv (for using .env values)

- sources

- todo

'''


# ----------------------------------------------------------------------------------------
#                libraries
# ----------------------------------------------------------------------------------------
import os


# ----------------------------------------------------------------------------------------
#                variables
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
#                functions
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
#                main
# ----------------------------------------------------------------------------------------
def main():
    start = 7981
    end = 8044

    lines = [
        f"pushlist spellbook_scrolls {i}"
        for i in range(start, end + 1)
    ]

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "output.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Saved to {output_path}")


# ----------------------------------------------------------------------------------------
#                start
# ----------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
