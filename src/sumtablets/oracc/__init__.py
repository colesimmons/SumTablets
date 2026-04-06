"""
Oracc corpus data models — corpus download, loading, and transliteration.

Public API:
    list_corpora()          → list of corpus name strings
    download(name)          → download + extract corpus zip from Oracc
    load(name)              → parse catalogue + CDL into a Corpus object
    set_download_path(path) → override where corpora are stored on disk
"""

import json
import os
import zipfile
from pathlib import Path
from typing import List, Union

import requests

from sumtablets.oracc.corpus import Corpus, CorpusType

_download_path: str = "./.corpusdata"


class DownloadError(Exception):
    pass


class ExtractionError(Exception):
    pass


def set_download_path(path: Union[str, Path]) -> None:
    global _download_path
    _download_path = str(path)


def list_corpora() -> List[str]:
    return [corpus.value for corpus in CorpusType]


def download(corpus_name: str) -> None:
    try:
        corpus_type = CorpusType(corpus_name)
    except ValueError:
        raise ValueError(
            f"Invalid corpus: {corpus_name}. Valid options: {list_corpora()}"
        ) from None

    os.makedirs(_download_path, exist_ok=True)

    zip_file_name = os.path.basename(corpus_type.url)
    zip_file_path = os.path.join(_download_path, zip_file_name)
    extracted_folder_path = os.path.join(_download_path, corpus_type.value)

    if os.path.exists(extracted_folder_path):
        print(f"Corpus {corpus_name} has already been downloaded.")
        return

    try:
        response = requests.get(corpus_type.url, timeout=240)
        response.raise_for_status()
        with open(zip_file_path, "wb") as f:
            f.write(response.content)
    except requests.RequestException as e:
        raise DownloadError(
            f"Failed to download .zip for {corpus_name}. Reason: {str(e)}"
        ) from e

    try:
        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            zip_ref.extractall(extracted_folder_path)
    except zipfile.BadZipFile as e:
        raise ExtractionError(
            f"Failed to extract .zip for {corpus_name}. Reason: {str(e)}"
        ) from e

    os.remove(zip_file_path)


def load(corpus_name: str) -> Corpus:
    try:
        corpus_type = CorpusType(corpus_name)
    except ValueError:
        raise ValueError(
            f"Invalid corpus: {corpus_name}. Valid options: {list_corpora()}"
        ) from None

    extracted_folder_path = os.path.join(_download_path, corpus_type.value)

    if not os.path.exists(extracted_folder_path):
        raise ValueError(f"Corpus {corpus_name} has not been downloaded yet.")

    dirs = [
        root
        for root, _, filenames in os.walk(extracted_folder_path)
        if "catalogue.json" in filenames
    ]
    path = dirs[0]
    catalogue_path = Path(path) / "catalogue.json"

    with open(catalogue_path, "r", encoding="utf-8") as f:
        catalogue = json.load(f)

    texts_path = str(Path(path) / "corpusjson/")
    texts = [
        {"dir_path": texts_path, **text_data}
        for text_data in catalogue["members"].values()
    ]
    model = corpus_type.model()
    model.load(texts)
    return model
