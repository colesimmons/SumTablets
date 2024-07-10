"""
This script:
- Downloads the ePSD2 JSON files for each corpus
- For each corpus:
    - Loads the metadata for each tablet from the catalogue.json file
    - Generates a transliteration for each tablet from its particular JSON file
    - Formats the data into a DataFrame, where each row is a tablet
    - Saves the DataFrame to a csv file: {OUTPUT_DIR}/1_{corpus_name}.csv
"""

import os
from typing import Optional

import pandas as pd
from constants import OUTPUT_DIR
from sumeripy import corpora as corpora_
from tqdm import tqdm


def _download_corpus_json_from_epsd2(
    corpus_name: str,
) -> Optional[corpora_.corpus.Corpus]:
    """
    Download the epsd2 files for a corpus

    Parameters:
    -----------
    corpus_name: str
        The name of the corpus to download. Must be one of the available corpora.

    Returns:
    --------
    corpus: corpora_.corpus.Corpus | None
        The corpus object if the download was successful, None otherwise.
    """
    corpus_names = corpora_.list()
    if corpus_name not in corpus_names:
        print(f"Corpus {corpus_name} not found. Available: {corpus_names}")
        return None
    print()
    print(f"Downloading {corpus_name}...")
    corpora_.download(corpus_name)
    print(f"Loading {corpus_name}...")
    return corpora_.load(corpus_name)


def _load_transliterations_and_convert_to_df(
    corpus: corpora_.corpus.Corpus,
) -> Optional[pd.DataFrame]:
    """
    Load the transliterations for each text in the corpus.

    Parameters:
    -----------
    corpus: corpora_.corpus.Corpus
        The corpus object to load the transliterations from.
    limit_ids: dict
        If not empty, only the texts with file_id in this dict will be loaded.

    Returns:
    --------
    df: pd.DataFrame
        A DataFrame where each row is a text.
        Columns will vary depending on the corpus. We add:
        - file_id: str
        - transliteration: str
    """

    texts = []
    failed = []
    for text in tqdm(corpus.texts):

        try:
            text.load_contents()
        except Exception:
            print(text)
            failed.append(text.file_id)
            continue

        transliteration = text.transliteration()
        texts.append(
            {
                "id": text.file_id,
                "transliteration": transliteration,
                **text.model_dump(exclude={"cdl"}),
            }
        )

    if failed:
        print("Failed to load: ", failed)

    if not texts:
        print("No texts loaded from corpus")
        return None

    df = pd.DataFrame(texts).fillna("")
    df.set_index("id", inplace=True)
    return df


def _load_epsd2_data_into_df(corpus_name: str) -> Optional[pd.DataFrame]:
    """
    Load a corpus from the ORACC files and save it to a new csv file.
    If the file already exists, it will be loaded from there.

    Parameters:
    -----------
    corpus_name: str
        The name of the corpus to load. Must be one of the available corpora.

    Returns:
    --------
    df: pd.DataFrame | None
        The DataFrame with the corpus data if successful, None otherwise.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    path = f"{OUTPUT_DIR}/1_{corpus_name}.csv"

    # If it doesn't, download it
    corpus = _download_corpus_json_from_epsd2(corpus_name)
    if corpus is None:
        return None
    df = _load_transliterations_and_convert_to_df(corpus)
    if df is None:
        return None

    # Save the DataFrame to a csv file
    print(f"Writing to {path}")
    df.to_csv(path)
    return df


def main():
    """
    Load all corpora from the ePSD2 data and save them to csv files.
    """
    for corpus_name in corpora_.list():
        _load_epsd2_data_into_df(corpus_name)


if __name__ == "__main__":
    main()
