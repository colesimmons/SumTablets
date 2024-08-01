"""
This script checks if the raw ePSD2 data is present.
If it is not, it prompts the user to download it, either from one of the backups or the most recent version from the ePSD2 website.
"""

import os
import zipfile
from pathlib import Path

import requests
from colorama import Fore, init

from src.models.corpus import CorpusEnum

# Initialize colorama
init(autoreset=True)

BACKUPS_URL = "https://drive.google.com/drive/folders/1znv6nggubCPoJIcsUCHJnejnb9oRaofE?usp=sharing"


def _check_corpus_data_present(path: Path) -> bool:
    """
    Checks if the raw ePSD2 data is present at the given path.
    """
    print("Corpora present:")
    for corpus in CorpusEnum:
        corpus_path = path / corpus.value
        if not corpus_path.is_dir():
            print(f"{Fore.RED}\u2716 {corpus.value}")
        else:
            print(f"{Fore.GREEN}\u2714 {corpus.value}")
    return True


def _download_corpus_data(path: Path) -> bool:
    """
    Downloads the raw ePSD2 data from the Oracc website for each corpus
    and extracts it to the given path.
    """

    # Make the download directory if it doesn't exist
    os.makedirs(path, exist_ok=True)

    for corpus in CorpusEnum:
        print(f"Downloading {corpus.value}...")
        zip_file_name = os.path.basename(corpus.url)
        zip_file_path = os.path.join(path, zip_file_name)
        extracted_folder_path = os.path.join(path, corpus.value)

        if os.path.exists(extracted_folder_path):
            print(f"Corpus {corpus.value} has already been downloaded.")
            return

        # Download the .zip
        try:
            response = requests.get(corpus.url, timeout=240)
            response.raise_for_status()  # Raise HTTPError for bad responses
            with open(zip_file_path, "wb") as f:
                f.write(response.content)

        except requests.RequestException as e:
            raise Exception(
                f"Failed to download .zip for {corpus.value}. Reason: {str(e)}"
            ) from e

        # Extract the .zip
        try:
            with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
                zip_ref.extractall(extracted_folder_path)
        except zipfile.BadZipFile as e:
            raise Exception(
                f"Failed to extract .zip for {corpus.value}. Reason: {str(e)}"
            ) from e

        # Remove the .zip
        os.remove(zip_file_path)
        print(f"Downloaded {corpus.value}.")

    return True


def main():
    project_root = Path(__file__).resolve().parents[2]
    epsd2_data_path = project_root / "epsd2_data"

    if epsd2_data_path.is_dir():
        print(
            f"\n{Fore.GREEN}\u2714 ./epsd2_data present! (location: {epsd2_data_path})"
        )
        _check_corpus_data_present(epsd2_data_path)
        return

    print(f"\n{Fore.YELLOW}\u26A0 Data not found. Please download the data.\n")
    print("----------------------------------------------------------")
    print(
        "To ensure long-term reproducibility, we retain snapshots of the ePSD2 data.\n"
    )
    print(
        "If you would like to work from one of these snapshots, download a .zip from the following link:"
    )
    print(BACKUPS_URL)
    print("Then unzip it in the project root directory.")
    print("The resulting path should be: ", epsd2_data_path)
    print("\nYou can re-run this script to verify that the data is present.")
    print("----------------------------------------------------------\n")

    print("\nAlternatively, you can download the most recent data provided by ePSD2.\n")
    print("Would you like to download the most recent data from ePSD2? (y/n)")
    user_input = input().strip().lower()

    if user_input == "y":
        print("Downloading data from ePSD2...")
        _download_corpus_data(epsd2_data_path)
        print("Download complete. Data saved to:", epsd2_data_path)
    elif user_input == "n":
        return
    else:
        print("Invalid input. Please run the script again and enter 'y' or 'n'.")


if __name__ == "__main__":
    main()
