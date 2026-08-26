# Anki_Tagger

Anki_Tagger is a project that parses lecture guides (PDF, PPTX, and DOCX) and identifies the most relevant Anki cards within a premade Anki deck. It helps medical students align vast Anki decks with their specific preclinical curriculum.

## Installation

```bash
# Clone the repository
git clone https://github.com/Zediious95/Anki_Tagger.git
cd Anki_Tagger

# Install all required packages
pip install -r requirements.txt
```

## Setup

1. **Export Anki Data**:
   - Export the deck you wish to tag as `anki_deck.apkg`.
   - Export the deck using the "Notes as plain text" function, selecting to include a unique identifier: `anki.txt`.
2. **Prepare Data Folder**:
   - Create a folder titled `Data` in the root directory.
   - Place both `anki_deck.apkg` and `anki.txt` inside the `Data` folder.
3. **Prepare Lectures**:
   - Create a folder titled `Lectures`.
   - Create subfolders inside `Lectures` titled after the tags you want to use (e.g., `01.Vitamins_1`, `02.Vitamins_2`). Ensure subfolder names contain no spaces.
   - Place the corresponding lecture materials (`.pdf`, `.pptx`, or `.docx`) inside these subfolders.

## LLM Configuration

This project supports both local LLMs via **Ollama** and cloud LLMs via **OpenAI**.

To configure your provider and models, edit `Scripts/util/config.py`:
- **Provider**: Set `PROVIDER` to `'ollama'` or `'openai'`.
- **Models**: Update `CHAT_MODEL` (e.g., `ornith-1.5:9b`) and `EMBEDDING_MODEL` (e.g., `nomic-embed-text`).
- **API Key**: If using OpenAI, set your `OPENAI_API_KEY` environment variable.

## Workflow

### 1. Embed the Anki Deck
Create embeddings of your deck to enable a fast first-pass search and reduce API costs.
```bash
python embed_deck.py
```
*Returns: `anki_embeddings.csv`*

### 2. Run the Tagging Pipeline
You can run the entire process—generating learning objectives, selecting relevant cards, and tagging the deck—in one go:
```bash
python main.py
```

### Alternative: Manual Step-by-Step Execution
If you prefer to run each stage individually:

1. **Generate Learning Objectives**: Analyze lecture files and create summary questions.
   ```bash
   python Scripts/make_learning_objectives.py <pdf_or_pptx_file_or_dir>
   ```
2. **Select Cards**: Score cards based on their relevance to the objectives.
   ```bash
   python Scripts/select_cards.py <deck_embedding_csv> <learning_objectives_csv>
   ```
3. **Tag Deck**: Apply the tags to the `.apkg` file.
   ```bash
   python Scripts/tag_deck.py <anki_cards_csv> <anki_deck.apkg>
   ```

## Final Step
Import the resulting tagged `.apkg` file into Anki. You can use the **Special Fields Anki addon** (Addon# 1102281552) to manage the tags.
