import argparse
import os
import sys
import subprocess
import shutil
import pandas as pd
from datetime import datetime
import glob


def parse_args():
    parser = argparse.ArgumentParser(description="Run the full lecture-tagging pipeline.")
    parser.add_argument(
        "--force", nargs="*", metavar="LECTURE_NAME", default=None,
        help="Reprocess lectures that already have output in Output/, bypassing the "
             "idempotency skip. Bare --force reprocesses every lecture; pass one or "
             "more lecture names (matching Lectures/<name>/) to force only those.",
    )
    return parser.parse_args()


args = parse_args()
force_all = args.force == []
forced_lecture_names = set(args.force) if args.force else set()

source_folder = 'Data/'
file_name = 'anki_deck.apkg'
script_dir = os.path.dirname(os.path.abspath(__file__))

source_file = os.path.join(source_folder, file_name)
destination_file = os.path.join(script_dir, file_name)
cards_copy_folder = os.path.join(script_dir, 'cards_for_merging')
output_dir = os.path.join(script_dir, 'Output')

if not os.path.exists(cards_copy_folder):
    os.makedirs(cards_copy_folder)
os.makedirs(output_dir, exist_ok=True)

if os.path.exists(source_file):
    shutil.copyfile(source_file, destination_file)
    print(f"File {file_name} has been copied from {source_folder} to {script_dir} and overwritten.")
else:
    print(f"Source file {source_file} does not exist.")

# Run combine_documents.py
print("Running combine_documents.py to combine lecture documents into PDFs...")
combine_command = ["python3", os.path.join(script_dir, "Scripts/combine_documents.py")]
process = subprocess.run(combine_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
if process.returncode == 0:
    print("combine_documents.py completed successfully.")
else:
    print(f"Error running combine_documents.py: {process.stderr}")
    sys.exit(1)

def find_lecture_files():
    # combine_documents.py flattens each Lectures/ subfolder into a single
    # root-level .pdf, so that is the only extension that appears here.
    files = glob.glob(os.path.join(script_dir, '*.pdf'))
    if len(files) == 0:
        raise FileNotFoundError(f"No PDF files found in {script_dir}.")
    return files

lecture_files = find_lecture_files()

def move_files_to_new_folder(files_to_move, subfolder_path, lecture_name):
    """
    Moves specified files and folders to a new timestamped subfolder.

    :param files_to_move: List of files or folders to move.
    :param subfolder_path: Path to the parent folder to create the subfolder in.
    :param lecture_name: The base name of the file being processed.
    """
    new_folder_name = f"{lecture_name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    new_folder_path = os.path.join(subfolder_path, new_folder_name)
    os.makedirs(new_folder_path, exist_ok=True)

    for file_path in files_to_move:
        full_file_path = os.path.abspath(file_path)

        if os.path.isdir(full_file_path):
            shutil.move(full_file_path, os.path.join(new_folder_path, os.path.basename(full_file_path)))
        elif os.path.isfile(full_file_path):
            shutil.move(full_file_path, new_folder_path)
        else:
            print(f"Path not found or invalid: {full_file_path}")


for lecture_file in lecture_files:
    lecture_name = os.path.splitext(os.path.basename(lecture_file))[0]

    already_processed = glob.glob(os.path.join(output_dir, f"{lecture_name}_*"))
    forced = force_all or lecture_name in forced_lecture_names
    if already_processed and not forced:
        print(f"Lecture '{lecture_name}' already has output in {output_dir} "
              f"({os.path.basename(already_processed[0])}); skipping. Re-run with "
              f"--force (optionally naming this lecture) to reprocess it, or delete "
              f"that folder.")
        continue
    elif already_processed and forced:
        print(f"Lecture '{lecture_name}' already has output in {output_dir}, but "
              f"--force was given; reprocessing (a new timestamped folder will be "
              f"created alongside the existing one).")

    script_file_pairs = [
        ("Scripts/make_learning_objectives.py", lecture_file),
        ("Scripts/select_cards.py", "Data/anki_embeddings.csv", f"{lecture_name}_learning_objectives.csv"),
    ]

    lecture_succeeded = True

    for pair in script_file_pairs:
        script = pair[0]
        files = pair[1:]

        missing_files = [file for file in files if not os.path.exists(file)]
        if missing_files:
            print(f"Skipping {script} due to missing files: {missing_files}")
            lecture_succeeded = False
            break

        command = ["python3", "-u", script] + list(files)

        print(f"Running {script} with {files}")
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        with process.stdout:
            for line in iter(process.stdout.readline, ''):
                print(line, end='', flush=True)
        with process.stderr:
            for line in iter(process.stderr.readline, ''):
                print(line, end='', flush=True)
        process.wait()

        if process.returncode != 0:
            print(f"{script} exited with code {process.returncode}; aborting this lecture.")
            lecture_succeeded = False
            break

    if not lecture_succeeded:
        print(f"Lecture '{lecture_name}' did not complete successfully; leaving its "
              f"intermediate files and Lectures/{lecture_name}/ source materials in "
              f"place. Fix the issue above and re-run python main.py to retry.")
        continue

    cards_csv = f"{lecture_name}_cards.csv"
    shutil.copy(cards_csv, os.path.join(cards_copy_folder, cards_csv))
    print(f"Copied {cards_csv} to {cards_copy_folder} for merging.")

    # Move this lecture's generated outputs into Output/ once it succeeds.
    # Lectures/<lecture_name>/ (the source materials) is intentionally never
    # moved -- a lecture being tagged shouldn't separate it from its source,
    # and leaving it in place is what lets the already_processed check above
    # skip re-tagging it on a future run without needing to dig it back out
    # of an archive.
    outputs_to_move = [
        cards_csv,
        f"{lecture_name}_learning_objectives.csv",
        f"{lecture_name}_progress.csv",
        lecture_file,
    ]
    move_files_to_new_folder(outputs_to_move, output_dir, lecture_name)

print(f"All lecture files have been processed.")

# List to hold DataFrames for each CSV file
dfs = []

# Loop through each file in the cards_copy_folder
for file_name in os.listdir(cards_copy_folder):
    if file_name.endswith('.csv'):  # Only process files with the .csv extension
        file_path = os.path.join(cards_copy_folder, file_name)

        # Read the current CSV file into a DataFrame
        df = pd.read_csv(file_path)

        # Append the DataFrame to the list
        dfs.append(df)

if not dfs:
    print("No lecture produced a cards CSV to merge (see skip/error messages above). Exiting without tagging.")
    sys.exit(1)

# Concatenate all DataFrames into a single DataFrame
merged_df = pd.concat(dfs, ignore_index=True)

# Save the merged DataFrame to a new CSV file
output_file_path = os.path.join(script_dir, 'Merged.csv')
merged_df.to_csv(output_file_path, index=False)

print(f'Merged CSV has been created at: {output_file_path}')

# Run tag_deck.py script on the merged CSV and anki_deck.apkg
print(f"Running Scripts/tag_deck.py with Merged.csv and anki_deck.apkg")

tag_deck_command = ["python3", "Scripts/tag_deck.py", "Merged.csv", "anki_deck.apkg"]
process = subprocess.Popen(tag_deck_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
with process.stdout:
    for line in iter(process.stdout.readline, ''):
        print(line, end='', flush=True)
with process.stderr:
    for line in iter(process.stderr.readline, ''):
        print(line, end='', flush=True)
process.wait()

if process.returncode == 0:
    print(f"Scripts/tag_deck.py finished successfully.\n")
else:
    print(f"Scripts/tag_deck.py encountered an error (exit code: {process.returncode}).\n")

# Cleanup: Delete all {pdf_name}_cards.csv files in cards_copy_folder after merging and tagging
for file_name in os.listdir(cards_copy_folder):
    file_path = os.path.join(cards_copy_folder, file_name)
    if file_name.endswith('_cards.csv'):
        os.remove(file_path)
        print(f"Deleted {file_path}")

print("All temporary cards CSV files have been deleted. Process complete.")
