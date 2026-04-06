"""Filter, deduplicate, and standardize tablet metadata from per-corpus DataFrames."""

import pandas as pd


def collate(dfs: list[pd.DataFrame], genre_normalization: dict[str, str]) -> pd.DataFrame:
    """Merge per-corpus DataFrames, filter non-Sumerian/duplicates, standardize metadata.

    Args:
        dfs: List of per-corpus DataFrames (one per ePSD2 corpus).
        genre_normalization: Mapping of raw genre strings to canonical names.

    Returns:
        Filtered, deduplicated DataFrame with columns: id, transliteration, period, genre.
    """
    df = pd.concat(dfs, join="inner")

    # Filter to Sumerian texts only
    df = df[df["language"].isin(["Sumerian", ""])]
    df = df[~df["langs"].str.contains("akk", na=False)]
    df = df[df["period"] != "Ebla"]
    df = df[df["period"] != "fake"]
    df = df[df["period"] != "Pre-Uruk V"]
    df = df[df["genre"] != "fake (modern)"]

    # Drop rows without transliteration
    df = df[df["transliteration"] != ""]

    # Deduplicate by ID
    df = df.drop_duplicates(subset="id")

    # Keep only the columns we need
    df = df[["id", "transliteration", "period", "genre"]]

    # Standardize periods
    df.loc[df["period"].isin({"", "Uncertain"}), "period"] = "Unknown"

    # Standardize genres using the normalization map
    for raw, canonical in genre_normalization.items():
        df.loc[df["genre"] == raw, "genre"] = canonical

    return df
