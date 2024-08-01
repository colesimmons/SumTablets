"""
This script:
- takes the dataframes from step 1
- concatenates them into single dataframe
- drops rows that are not Sumerian
- drops rows w/o transliteration
- drops excess columns (only keep id, transliteration, period, and genre)
- standardizes periods and genres
- saves result to ./outputs/2_tablets.csv
"""

import pandas as pd
from sumeripy import corpora as corpora_
from tqdm import tqdm

from src.constants import OUTPUT_DIR

tqdm.pandas()

OUTFILE = f"{OUTPUT_DIR}/2_tablets.csv"


def _load_corpus(corpus_name):
    return pd.read_csv(
        f"{OUTPUT_DIR}/1_{corpus_name}.csv",
        low_memory=False,
    ).fillna("")


def main():
    df = None

    for corpus_name in corpora_.list():
        print(f"Loading {corpus_name}...")

        corpus_df = _load_corpus(corpus_name)
        df = corpus_df if df is None else pd.concat([df, corpus_df], join="inner")

    # Print number of texts
    print()
    print(f"Starting number of texts: {len(df)}")
    print()

    # language is "Sumerian" or ""
    print("Dropping rows that are not Sumerian...")
    df = df[df["language"].isin(["Sumerian", ""])]
    df = df[~df["langs"].str.contains("akk")]
    df = df[df["period"] != "Ebla"]
    df = df[df["period"] != "fake"]
    df = df[df["period"] != "Pre-Uruk V"]
    df = df[df["genre"] != "fake (modern)"]
    print(f"Updated number of texts: {len(df)}")
    print()

    # Print number of texts without transliteration
    print("Dropping rows without transliteration...")
    df = df[df["transliteration"] != ""]
    print(f"Updated number of texts: {len(df)}")
    print()

    # Drop duplicates based on id
    print("Drop duplicates...")
    df = df.drop_duplicates(subset="id")
    print(f"Updated number of texts: {len(df)}")
    print()

    # Drop unnecessary columns
    df = df[["id", "transliteration", "period", "genre"]]

    # Standardize periods
    df.loc[df["period"].isin({"", "Uncertain"}), "period"] = "Unknown"

    # Standardize genres
    df.loc[df["genre"].isin({"", "uncertain"}), "genre"] = "Unknown"
    df.loc[df["genre"].isin({"Royal/Monumental", "Royal Inscription"}), "genre"] = (
        "Royal Inscription"
    )
    df.loc[df["genre"].isin({"Lexical; School", "Lexical"}), "genre"] = "Lexical"
    df.loc[df["genre"].isin({"Liturgy", "Ritual", "Hymn-Prayer"}), "genre"] = "Liturgy"
    df.loc[
        df["genre"].isin({"Mathematical", "Scientific", "Astronomical"}), "genre"
    ] = "Math/Science"

    print(df["period"].value_counts())
    print()
    print(df["genre"].value_counts())

    print()
    print("Saving to csv...")
    df.to_csv(OUTFILE, index=False)
    print()
    print("Done!")


if __name__ == "__main__":
    main()
