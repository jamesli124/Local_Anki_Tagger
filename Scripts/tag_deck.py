import os, sys
import shutil
import pandas as pd
from anki.collection import Collection
from anki.import_export_pb2 import (
    ImportAnkiPackageOptions,
    ImportAnkiPackageRequest,
    ExportAnkiPackageOptions,
)
    #python3 Scripts/tag_deck.py learning_guide_cards.csv anki_deck.apkg

HIGH_RELEVANCE_CUTOFF = 70
MEDIUM_RELEVANCE_CUTOFF = 50
REMOVE_RELEVANCE_CUTOFF = 40

TEMP_DIR = "temp_folder"
TEMP_COLLECTION_PATH = os.path.join(TEMP_DIR, "collection.anki2")

def main(card_path, anki_apkg):

    # Load the csv file into a DataFrame
    df = pd.read_csv(card_path)
    df = df.fillna(0)

    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)

    # Group by 'guid' and keep only the row with the highest 'score' for each group
    df = df.loc[df.groupby('guid')['score'].idxmax()]

    # Import the .apkg into a fresh temporary collection via Anki's own
    # import API, rather than hand-unzipping and looking for a bare
    # ".anki21" file -- modern Anki exports store the collection as a
    # zstd-compressed "collection.anki21b" instead, which a plain
    # endswith(".anki21") check misses entirely.
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR)

    col = Collection(TEMP_COLLECTION_PATH)
    col.import_anki_package(ImportAnkiPackageRequest(
        package_path=os.path.abspath(anki_apkg),
        options=ImportAnkiPackageOptions(
            merge_notetypes=True,
            with_scheduling=True,
            with_deck_configs=True,
        ),
    ))
    tagged = set()

    # Iterate through all cards
    # For each row in the DataFrame

    for index, row in df.iterrows():

        guid = row['guid']
        tag = row['tag']
        score = int(row['score'])

        if score >= HIGH_RELEVANCE_CUTOFF:
            try:
                note_id,note_tags = col.db.all("SELECT id, tags FROM notes WHERE guid = ?",guid)[0]
                new_tag = note_tags + " " + tag+"::1_highly_relevant" + " "
                col.db.execute("UPDATE notes set tags = ? where id = ?", new_tag, note_id)
                tagged.add(guid)
            except:
                print(f"guid not found for card: {row['card']}")

        if score < HIGH_RELEVANCE_CUTOFF and score >= MEDIUM_RELEVANCE_CUTOFF:
            try:
                note_id,note_tags = col.db.all("SELECT id, tags FROM notes WHERE guid = ?",guid)[0]
                new_tag = note_tags + " " + tag+"::2_somewhat_relevant" + " "
                col.db.execute("UPDATE notes set tags = ? where id = ?", new_tag, note_id)
                tagged.add(guid)
            except:
                print(f"guid not found for card: {row['card']}")

        if score < MEDIUM_RELEVANCE_CUTOFF and score >= REMOVE_RELEVANCE_CUTOFF:
            try:
                note_id,note_tags = col.db.all("SELECT id, tags FROM notes WHERE guid = ?",guid)[0]
                new_tag = note_tags + " " + tag+"::3_minimally_relevant" + " "
                col.db.execute("UPDATE notes set tags = ? where id = ?", new_tag, note_id)
                tagged.add(guid)
            except:
                print(f"guid not found for card: {row['card']}")

    # Close and reopen so the raw SQL tag writes above are fully committed and
    # the backend's in-memory state is clean before exporting.
    col.close()
    col = Collection(TEMP_COLLECTION_PATH)

    # Re-create the .apkg file via Anki's own export API (handles the
    # zip layout, media remapping, and collection compression itself).
    col.export_anki_package(
        out_path=os.path.abspath(anki_apkg),
        options=ExportAnkiPackageOptions(
            with_scheduling=True,
            with_deck_configs=True,
            with_media=True,
            legacy=False,
        ),
        limit=None,
    )
    col.close()

    # Clean up the temporary folder
    print(f"Tagged {len(tagged)} cards. Process Complete")
    shutil.rmtree(TEMP_DIR)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: tag_deck.py <cards.csv> <anki_deck.apkg>")
        sys.exit(1)
    card_path = sys.argv[1]
    anki_apkg = sys.argv[2]
    main(card_path, anki_apkg)
