"""
This script uses the Oracc Sign List (OSL) data to create two JSON files:

1) `./outputs/morpheme_to_glyph_names.json` str -> list[str]
- maps from an individual morpheme to a set of glyph names that could represent it.
- e.g. "lil₂" -> ["AN", "E₂"]

2) `./outputs/glyph_name_to_glyph.json` str -> str
- maps from glyph names to their Unicode representations or an empty string.

This script does not rely on the previous scripts.
It will be essential for turning the readings into glyph names / Unicode.
"""

import json
import os
from collections import defaultdict

import requests

from src.constants import OUTPUT_DIR

MORPHEME_TO_GLYPH_NAMES_OUTFILE = f"{OUTPUT_DIR}/morpheme_to_glyph_names.json"
GLYPH_NAME_TO_GLYPH_OUTFILE = f"{OUTPUT_DIR}/glyph_name_to_glyph.json"

with open("epsd2-sl.json", encoding="utf-8") as infile:
    EPSD2_SL = json.load(infile)["index"]


def main():
    _download_osl_json()
    morpheme_to_glyph_names, glyph_name_to_glyphs = _process_json()
    morpheme_to_glyph_names = _remove_empty_strings(morpheme_to_glyph_names)
    glyph_name_to_glyphs = _remove_empty_strings(glyph_name_to_glyphs)

    # Add EPSD2_SL mappings to morpheme_to_glyph_names and write.
    for k, v in EPSD2_SL.items():
        morpheme_to_glyph_names[k] = [v]
    with open(MORPHEME_TO_GLYPH_NAMES_OUTFILE, "w", encoding="utf-8") as f:
        json.dump(morpheme_to_glyph_names, f, ensure_ascii=False)

    # Each glyph name should map to at most one unicode representation.
    # Double check, convert to a single mapping, and write.
    for glyph_name, unicodes in glyph_name_to_glyphs.items():
        if len(unicodes) > 1:
            print(f"Glyph {glyph_name} has more than one representation: {unicodes}")
    glyph_name_to_glyph = {
        key: vals[0] if vals else "" for key, vals in glyph_name_to_glyphs.items()
    }
    with open(GLYPH_NAME_TO_GLYPH_OUTFILE, "w", encoding="utf-8") as f:
        json.dump(glyph_name_to_glyph, f, ensure_ascii=False)


# --------------------------------------------------------------------------------------
# ---------------------------- Download OSL JSON ---------------------------------------
# --------------------------------------------------------------------------------------
def _download_osl_json():
    # Saved a copy at
    # https://drive.google.com/file/d/1qArSHeGsCHc3Fq6gdZiBLIvvObB5cIrU/view?usp=drive_link
    url = "https://oracc.museum.upenn.edu/osl/downloads/sl.json"
    filename = "osl.json"

    if os.path.isfile(filename):
        print(f"File '{filename}' already exists in the current directory.")
    else:
        try:
            # Send a GET request to the URL
            response = requests.get(url)

            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                # Save the JSON content to a file
                with open(filename, "w") as file:
                    file.write(response.text)
                print(f"File '{filename}' downloaded successfully.")
            else:
                print(
                    f"Failed to download the file. Status code: {response.status_code}"
                )
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while downloading the file: {str(e)}")


# --------------------------------------------------------------------------------------
# ----------------------------- Process OSL JSON ---------------------------------------
# --------------------------------------------------------------------------------------
def _process_json():
    # ----------------------------------
    # -- Morpheme -> set(Glyph Names) --
    # ----------------------------------
    # e.g.  šab₄ -> {MI}
    morpheme_to_glyph_names = defaultdict(set)

    def _add_reading(*, glyph_name: str, reading: str) -> None:
        glyph_name = glyph_name.replace("&amp;", "&")
        morpheme_to_glyph_names[reading].add(glyph_name)

    # ----------------------------------
    # ------ Glyph Name -> Unicode -----
    # ----------------------------------
    # e.g. MI -> {𒈪}
    glyph_name_to_glyphs = defaultdict(set)

    def _add_glyph(*, glyph_name: str, unicode: str) -> None:
        glyph_name = glyph_name.replace("&amp;", "&")
        glyph_name_to_glyphs[glyph_name].add(unicode)

    # ----------------------------------------
    # ---------- Process json ----------------
    # ----------------------------------------
    with open("osl.json") as f:
        osl = json.load(f)

    for letter in osl["sl:signlist"]["j:letters"]:
        for glyph in letter["sl:letter"]["j:signs"]:
            glyph_data = glyph["sl:sign"]
            glyph_name = glyph_data["n"]
            # Glyph Name -> Unicode
            glyph_unicode = glyph_data.get("sl:ucun", "")
            _add_glyph(glyph_name=glyph_name, unicode=glyph_unicode)

            for aka in glyph_data.get("j:aka", []):
                aka_name = aka["sl:aka"]["n"]
                _add_glyph(glyph_name=aka_name, unicode=glyph_unicode)

            # Glyph Readings
            for glyph_reading_data in glyph_data.get("j:values", []):
                if "sl:v" not in glyph_reading_data:
                    continue
                # Morpheme -> Glyph Name
                glyph_reading_data = glyph_reading_data["sl:v"]
                _add_reading(glyph_name=glyph_name, reading=glyph_reading_data["n"])

            # Glyph Forms (variants, not to be confused with wordforms)
            for form in glyph_data.get("j:forms", []):
                form_data = form["sl:form"]
                form_name = form_data["n"]
                # Form Name -> Unicode
                form_unicode = form_data.get("sl:ucun", "")
                _add_glyph(glyph_name=form_name, unicode=form_unicode)

                for aka in form_data.get("j:aka", []):
                    aka_name = aka["sl:aka"]["n"]
                    _add_glyph(glyph_name=aka_name, unicode=form_unicode)

                # Form Readings
                for form_reading_data in form_data.get("j:values", []):
                    if "sl:v" not in form_reading_data:
                        continue
                    # Morpheme -> Form Name
                    form_reading_data = form_reading_data["sl:v"]
                    _add_reading(glyph_name=form_name, reading=form_reading_data["n"])

    return morpheme_to_glyph_names, glyph_name_to_glyphs


def _remove_empty_strings(d: dict) -> dict:
    return {key: [v for v in vals if v != ""] for key, vals in d.items()}


if __name__ == "__main__":
    main()
