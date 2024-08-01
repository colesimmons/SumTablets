"""
list()
download()
load()
"""

import json
import os
import zipfile
from pathlib import Path
from typing import List

import requests

from src.models.corpus import Corpus, CorpusType
from src.models.exceptions import DownloadError, ExtractionError

_CORPUS_DOWNLOAD_PATH = "./.corpusdata"


def list() -> List[str]:
    """
    Returns:
        corpora - a list of available corpora in Oracc
    """
    return [corpus.value for corpus in CorpusType]


def download(corpus_name: str) -> None:
    """
    Downloads and extracts a corpus from the Oracc website.

    Args:
        corpus_name (str): The corpus to download.

    Raises:
        DownloadError: If the download fails.
        ExtractionError: If the extraction fails.
    """

    # Get the corpus type
    try:
        corpus_type = CorpusType(corpus_name)
    except ValueError:
        corpus_names = list()
        raise ValueError(
            f"Invalid corpus: {corpus_name}. Valid options: {corpus_names}"
        ) from None

    # Make the download directory if it doesn't exist
    os.makedirs(_CORPUS_DOWNLOAD_PATH, exist_ok=True)

    zip_file_name = os.path.basename(corpus_type.url)
    zip_file_path = os.path.join(_CORPUS_DOWNLOAD_PATH, zip_file_name)
    extracted_folder_path = os.path.join(_CORPUS_DOWNLOAD_PATH, corpus_type.value)

    if os.path.exists(extracted_folder_path):
        print(f"Corpus {corpus_name} has already been downloaded.")
        return

    # Download the .zip
    try:
        response = requests.get(corpus_type.url, timeout=240)
        response.raise_for_status()  # Raise HTTPError for bad responses

        with open(zip_file_path, "wb") as f:
            f.write(response.content)
    except requests.RequestException as e:
        raise DownloadError(
            f"Failed to download .zip for {corpus_name}. Reason: {str(e)}"
        ) from e

    # Extract the .zip
    try:
        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            zip_ref.extractall(extracted_folder_path)
    except zipfile.BadZipFile as e:
        raise ExtractionError(
            f"Failed to extract .zip for {corpus_name}. Reason: {str(e)}"
        ) from e

    # Remove the .zip
    os.remove(zip_file_path)


def load(corpus_name: str) -> Corpus:
    """
    Load a corpus by its name.

    Args:
        corpus_name (str): The name of the corpus to load.

    Returns:
        Corpus: The loaded corpus.

    Raises:
        ValueError: If the specified corpus is invalid or has not been downloaded yet.
    """
    try:
        corpus = CorpusType(corpus_name)
    except ValueError:
        corpus_names = list()
        raise ValueError(
            f"Invalid corpus: {corpus_name}. Valid options: {corpus_names}"
        ) from None

    extracted_folder_path = os.path.join(_CORPUS_DOWNLOAD_PATH, corpus.value)

    if not os.path.exists(extracted_folder_path):
        raise ValueError(f"Corpus {corpus} has not been downloaded yet.")

    dirs = _find_corpusjson_dirs(extracted_folder_path)
    path = dirs[0]
    catalogue_path = Path(path) / "catalogue.json"

    with open(catalogue_path, "r", encoding="utf-8") as f:
        catalogue = json.load(f)

    texts_path = str(Path(path) / "corpusjson/")
    texts = [
        {"dir_path": texts_path, **text_data}
        for text_data in catalogue["members"].values()
    ]
    model = corpus.model()
    model.load(texts)
    return model


def _find_corpusjson_dirs(root_dir: str):
    """Search for the 'corpusjson' dir paths"""
    return [
        root
        for root, _, filenames in os.walk(root_dir)
        if "catalogue.json" in filenames
    ]
