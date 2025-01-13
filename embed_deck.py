import os
import openai
import pandas as pd
import tiktoken
from Scripts.util.embeddings_utils import get_embedding
from tqdm import tqdm

# OpenAI Configuration
OPENAI_API_KEY_ENV_VAR = 'OPENAI_API_KEY'
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_ENCODING = "cl100k_base"
MAX_TOKENS = 8000

# Define the source folder and input file relative to the script directory
script_dir = os.path.dirname(os.path.abspath(__file__))  # Directory where the script is located
source_folder = os.path.join(script_dir, 'Data')  # Path to the Data folder
input_datapath = os.path.join(source_folder, 'anki.txt')  # Full path to the anki.txt file


def set_api_key(api_key):
    openai.api_key = api_key


def load_dataset(input_datapath):
    assert os.path.exists(input_datapath), f"{input_datapath} does not exist. Please check your file path."
    df = pd.read_csv(input_datapath, sep='\t', header=None, usecols=[0, 1], names=["guid", "card"],
                     comment='#').dropna()
    return df


def filter_by_tokens(df, encoding):
    df["tokens"] = df.card.apply(lambda x: len(encoding.encode(x)))
    return df[df.tokens <= MAX_TOKENS]


def calculate_embeddings(df):
    return [get_embedding(card, model=EMBEDDING_MODEL) for card in
            tqdm(df.card, desc="Calculating embeddings", dynamic_ncols=True)]


def save_embeddings(df, output_prefix):
    df.to_csv(f"./{output_prefix}_embeddings.csv", index=False)


def main():
    api_key = os.environ.get(OPENAI_API_KEY_ENV_VAR)
    assert api_key, f"Set your OpenAI API key as an environment variable named '{OPENAI_API_KEY_ENV_VAR}'"

    # Set OpenAI API key
    set_api_key(api_key)

    # Define output file prefix
    output_prefix = "anki"  # EDIT AS NEEDED

    # Load and preprocess dataset
    df = load_dataset(input_datapath)
    encoding = tiktoken.get_encoding(EMBEDDING_ENCODING)
    df = filter_by_tokens(df, encoding)

    # Calculate embeddings for cards
    df["emb"] = calculate_embeddings(df)

    # Save embeddings to file
    save_embeddings(df, output_prefix)


if __name__ == "__main__":
    main()
