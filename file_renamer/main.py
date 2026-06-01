# ----------------------------------------------------------------------------------------
#                 notes
# ----------------------------------------------------------------------------------------
"""
Kutay Coskuner, 2026
MIT License - use freely, no warranty

- description
    Simple batch renamer:
    - add folder name as prefix OR
    - remove folder name prefix from files

- metadata
    - config driven via YAML

- use case
    - normalize asset naming in folders
    - prepare game / blender / engine pipelines

- install
    pip install pyyaml

- config
    parameters defined in config.yaml
"""

# ----------------------------------------------------------------------------------------
#                 libraries
# ----------------------------------------------------------------------------------------
import glob
import os
import yaml


# ----------------------------------------------------------------------------------------
#                 functions
# ----------------------------------------------------------------------------------------


def load_config(path="config.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_folder_name(path):
    return os.path.basename(os.path.normpath(path))


def preview_and_rename(file_list, folder_name, mode):
    """
    Previews all planned changes first, handles and notifications virtual collisions,
    asks for confirmation, and then applies the changes if confirmed.
    """
    folder_lower = folder_name.lower()
    planned_changes = []
    idx = 1

    # This tracking set keeps track of filenames that WILL exist in the folder
    # during our virtual dry-run simulation
    virtual_existing_files = set()

    print(f"\n--- Calculating Planned Changes ({mode.upper()} mode) ---")

    for file_path in file_list:
        if not os.path.isfile(file_path):
            continue

        dir_path, file_name = os.path.split(file_path)
        name, ext = os.path.splitext(file_name)

        # 1. Calculate base target name based on mode
        if mode == "add":
            candidate_base = f"{folder_name}_{name}"
        elif mode == "remove":
            if not name.lower().startswith(folder_lower):
                continue

            new_name = name[len(folder_name) :]
            if new_name.startswith(("-", "_")):
                new_name = new_name[1:]

            if new_name == "":
                print(f"  [Skipping empty name generation]: {file_name}")
                continue
            candidate_base = new_name

        # 2. Check for real disk collisions AND virtual preview collisions
        candidate = f"{candidate_base}{ext}"
        candidate_path = os.path.join(dir_path, candidate)

        is_collision = False

        # If the file already exists on disk OR has been claimed by a previous file in this run
        if (
            os.path.exists(candidate_path)
            or candidate.lower() in virtual_existing_files
        ):
            is_collision = True
            i = 1
            while True:
                suffix = f"{i:02d}"
                candidate = f"{candidate_base}{suffix}{ext}"
                candidate_path = os.path.join(dir_path, candidate)

                if (
                    not os.path.exists(candidate_path)
                    and candidate.lower() not in virtual_existing_files
                ):
                    break
                i += 1

        # Add the finalized name to our virtual tracker so subsequent files check against it
        virtual_existing_files.add(candidate.lower())

        # 3. Print the preview with notification flags
        if file_name != candidate:
            planned_changes.append((file_path, candidate_path, file_name, candidate))

            # Highlight conflicts visually in the terminal preview
            notification = " [CONFLICT RESOLVED]" if is_collision else ""
            print(f"[{idx}] {file_name} -> {candidate}{notification}")
            idx += 1

    if not planned_changes:
        print("\nNo pending name changes detected.")
        return

    # --- THE CONFIRMATION STEP ---
    print(f"\nTotal operations planned: {len(planned_changes)}")
    confirm = input(
        f"\nDo you want to apply these {len(planned_changes)} changes? (y/n): "
    )

    if confirm.lower() != "y":
        print("Operation cancelled. No files were altered.")
        return

    # --- EXECUTION STEP ---
    print("\n--- Applying Changes ---")
    rename_count = 0
    for i, (old_path, new_path, old_name, new_name) in enumerate(
        planned_changes, start=1
    ):
        try:
            os.rename(old_path, new_path)
            print(f"[{i}/{len(planned_changes)}] Processed: {old_name} -> {new_name}")
            rename_count += 1
        except Exception as e:
            print(f"[{i}/{len(planned_changes)}] ERROR renaming {old_name}: {e}")

    print(f"\nSuccessfully renamed {rename_count} files.")


def resolve_collision(path, base_name, extension):
    """If file exists, append incremental number: 01, 02, 03..."""
    candidate = f"{base_name}{extension}"
    new_path = os.path.join(path, candidate)

    if not os.path.exists(new_path):
        return candidate

    i = 1
    while True:
        suffix = f"{i:02d}"
        candidate = f"{base_name}{suffix}{extension}"
        new_path = os.path.join(path, candidate)

        if not os.path.exists(new_path):
            return candidate

        i += 1


# ----------------------------------------------------------------------------------------
#                 main
# ----------------------------------------------------------------------------------------
def main():
    config = load_config()

    work_folder = config["paths"]["work_folder"]
    pattern = config["filters"]["pattern"]
    mode = config["mode"]  # "add" or "remove"

    folder_name = get_folder_name(work_folder)
    file_list = glob.glob(os.path.join(work_folder, pattern))

    if not file_list:
        print("No files found matching the configuration filters.")
        return

    if mode in ("add", "remove"):
        preview_and_rename(file_list, folder_name, mode)
    else:
        print("Invalid mode in config.yaml. Choose 'add' or 'remove'.")


# ----------------------------------------------------------------------------------------
#                 start
# ----------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
