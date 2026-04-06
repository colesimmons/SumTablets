"""Pipeline orchestrator — the only module that does file I/O."""

import hashlib
import json
from dataclasses import dataclass
from typing import Callable, Optional

import pandas as pd
import requests
from tqdm import tqdm

from sumtablets import paths
from sumtablets.oracc import Corpus, download, list_corpora, load, set_download_path
from sumtablets.transforms import cleaning, collation, glyphs, sign_lists


@dataclass
class Step:
    number: int
    name: str
    execute: Callable


# ---------------------------------------------------------------------------
# Step 1: Download corpora
# ---------------------------------------------------------------------------

def _download_corpus_and_extract_df(corpus_name: str) -> Optional[pd.DataFrame]:
    """Download a single corpus from ePSD2 and return as DataFrame."""
    output_path = paths.STEP1_PREFIX / f"1_{corpus_name}.csv"

    if output_path.exists():
        print(f"Already exists: {output_path}, skipping download")
        return pd.read_csv(output_path, index_col="id")

    print(f"\nDownloading {corpus_name}...")
    download(corpus_name)
    print(f"Loading {corpus_name}...")
    corpus = load(corpus_name)

    texts = []
    failed = []
    for text in tqdm(corpus.texts):
        try:
            text.load_contents()
        except Exception:
            failed.append(text.file_id)
            continue
        transliteration = text.transliteration()
        texts.append({
            "id": text.file_id,
            "transliteration": transliteration,
            **text.model_dump(exclude={"cdl"}),
        })

    if failed:
        print(f"Failed to load: {failed}")
    if not texts:
        print("No texts loaded from corpus")
        return None

    df = pd.DataFrame(texts).fillna("")
    df.set_index("id", inplace=True)
    print(f"Writing to {output_path}")
    df.to_csv(output_path)
    return df


def run_download() -> None:
    """Step 1: Download all ePSD2 corpora and save per-corpus CSVs."""
    set_download_path(paths.EPSD2_DATA_DIR)
    paths.GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    for corpus_name in list_corpora():
        _download_corpus_and_extract_df(corpus_name)


# ---------------------------------------------------------------------------
# Step 2: Collate tablets
# ---------------------------------------------------------------------------

def run_collate() -> None:
    """Step 2: Merge per-corpus CSVs, filter, standardize."""
    dfs = []
    for corpus_name in list_corpora():
        path = paths.STEP1_PREFIX / f"1_{corpus_name}.csv"
        dfs.append(pd.read_csv(path, low_memory=False).fillna(""))

    with open(paths.GENRE_NORMALIZATION_PATH, encoding="utf-8") as f:
        genre_normalization = json.load(f)

    result = collation.collate(dfs, genre_normalization)
    print(f"Collated tablets: {len(result)}")
    result.to_csv(paths.STEP2_OUTPUT, index=False)


# ---------------------------------------------------------------------------
# Step 3: Clean transliterations
# ---------------------------------------------------------------------------

def run_clean() -> None:
    """Step 3: Remove editorial markup from transliterations."""
    df = pd.read_csv(paths.STEP2_OUTPUT).fillna("")
    result = cleaning.clean(df)
    print(f"Cleaned tablets: {len(result)}")
    result.to_csv(paths.STEP3_OUTPUT, index=False)


# ---------------------------------------------------------------------------
# Step 4: Create lookups
# ---------------------------------------------------------------------------

def _download_osl_if_needed() -> None:
    """Download osl.json from Oracc if not present."""
    if paths.OSL_PATH.is_file():
        print(f"OSL already exists: {paths.OSL_PATH}")
        return

    url = "https://oracc.museum.upenn.edu/osl/downloads/sl.json"
    print(f"Downloading OSL from {url}...")
    response = requests.get(url)
    response.raise_for_status()
    paths.SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    with open(paths.OSL_PATH, "w", encoding="utf-8") as f:
        f.write(response.text)
    print(f"Saved to {paths.OSL_PATH}")


def run_create_lookups() -> None:
    """Step 4: Build morpheme→glyph_name and glyph_name→glyph mappings."""
    _download_osl_if_needed()

    with open(paths.OSL_PATH, encoding="utf-8") as f:
        osl_data = json.load(f)
    with open(paths.EPSD2_SL_PATH, encoding="utf-8") as f:
        epsd2_sl_data = json.load(f)["index"]

    morpheme_to_glyph_names, glyph_name_to_glyph = sign_lists.build_lookups(
        osl_data, epsd2_sl_data
    )

    with open(paths.MORPHEME_TO_GLYPH_NAMES_PATH, "w", encoding="utf-8") as f:
        json.dump(morpheme_to_glyph_names, f, ensure_ascii=False)
    with open(paths.GLYPH_NAME_TO_GLYPH_PATH, "w", encoding="utf-8") as f:
        json.dump(glyph_name_to_glyph, f, ensure_ascii=False)

    print(f"Wrote {len(morpheme_to_glyph_names)} morpheme mappings")
    print(f"Wrote {len(glyph_name_to_glyph)} glyph name mappings")


# ---------------------------------------------------------------------------
# Step 5: Add glyphs
# ---------------------------------------------------------------------------

def run_add_glyphs() -> None:
    """Step 5: Convert transliterations to Unicode cuneiform via lookups."""
    df = pd.read_csv(paths.STEP3_OUTPUT).fillna("")

    with open(paths.MORPHEME_TO_GLYPH_NAMES_PATH, encoding="utf-8") as f:
        morpheme_to_glyph_names = json.load(f)
    with open(paths.GLYPH_NAME_TO_GLYPH_PATH, encoding="utf-8") as f:
        glyph_name_to_glyph = json.load(f)
    with open(paths.SIGN_LIST_REPLACEMENTS_PATH, encoding="utf-8") as f:
        transliteration_replacements = json.load(f)
    with open(paths.GLYPH_NAME_REPLACEMENTS_PATH, encoding="utf-8") as f:
        glyph_name_replacements = json.load(f)
    with open(paths.READING_FIXES_PATH, encoding="utf-8") as f:
        number_readings = json.load(f)

    result, stats = glyphs.add_glyphs(
        df,
        morpheme_to_glyph_names=morpheme_to_glyph_names,
        glyph_name_to_glyph=glyph_name_to_glyph,
        transliteration_replacements=transliteration_replacements,
        glyph_name_replacements=glyph_name_replacements,
        number_readings=number_readings,
    )

    glyphs.print_stats(stats)
    result.to_csv(paths.STEP5_OUTPUT, index=False, encoding="utf-8")
    print(f"Wrote {len(result)} rows to {paths.STEP5_OUTPUT}")


# ---------------------------------------------------------------------------
# Step 6: Split
# ---------------------------------------------------------------------------

def run_split() -> None:
    """Step 6: 95/5/5 train/val/test split (Lexical in train only)."""
    from sklearn.model_selection import train_test_split

    df = pd.read_csv(paths.STEP5_OUTPUT, low_memory=False, encoding="utf-8")

    lexical_df = df[df["genre"] == "Lexical"]
    non_lexical_df = df[df["genre"] != "Lexical"]

    train_val_df, test_df = train_test_split(
        non_lexical_df,
        stratify=non_lexical_df["period"],
        test_size=0.05,
        random_state=42,
    )
    train_df, val_df = train_test_split(
        train_val_df,
        stratify=train_val_df["period"],
        test_size=(5 / 95),
        random_state=42,
    )
    train_df = pd.concat([train_df, lexical_df])

    # Shuffle
    train_df = train_df.sample(frac=1).reset_index(drop=True)
    test_df = test_df.sample(frac=1).reset_index(drop=True)
    val_df = val_df.sample(frac=1).reset_index(drop=True)

    train_df.to_csv(paths.TRAIN_OUTPUT, index=False, encoding="utf-8")
    val_df.to_csv(paths.VALIDATION_OUTPUT, index=False, encoding="utf-8")
    test_df.to_csv(paths.TEST_OUTPUT, index=False, encoding="utf-8")

    print(f"Train: {len(train_df)}  Val: {len(val_df)}  Test: {len(test_df)}")

    # Compute and print SHA-256 + stats for VERSION.yaml comparison
    _print_final_stats()


# ---------------------------------------------------------------------------
# Final stats
# ---------------------------------------------------------------------------

def _print_final_stats() -> None:
    """Compute output hash and glyph count for comparison with VERSION.yaml."""
    dfs = []
    for path in [paths.TRAIN_OUTPUT, paths.VALIDATION_OUTPUT, paths.TEST_OUTPUT]:
        dfs.append(pd.read_csv(path, low_memory=False, encoding="utf-8"))
    combined = pd.concat(dfs, ignore_index=True)

    total_rows = len(combined)

    # Glyph count (excluding special tokens and spaces)
    special = {"<SURFACE>", "<COLUMN>", "<BLANK_SPACE>", "<RULING>", "...", "<unk>"}

    def _count_glyphs(glyph_str: str) -> int:
        for tok in special:
            glyph_str = glyph_str.replace(tok, "")
        return len(glyph_str.replace(" ", ""))

    total_glyphs = combined["glyphs"].fillna("").map(_count_glyphs).sum()

    # SHA-256 of sorted combined output
    sorted_df = combined.sort_values("id").reset_index(drop=True)
    sha = hashlib.sha256(
        pd.util.hash_pandas_object(sorted_df).values.tobytes()
    ).hexdigest()

    print(f"\n{'=' * 50}")
    print(f"Total rows:   {total_rows}")
    print(f"Total glyphs: {total_glyphs}")
    print(f"Output SHA-256: {sha}")
    print(f"{'=' * 50}")


# ---------------------------------------------------------------------------
# Pipeline runner
# ---------------------------------------------------------------------------

STEPS = [
    Step(1, "Download corpora", run_download),
    Step(2, "Collate tablets", run_collate),
    Step(3, "Clean transliterations", run_clean),
    Step(4, "Create lookups", run_create_lookups),
    Step(5, "Add glyphs", run_add_glyphs),
    Step(6, "Split dataset", run_split),
]


def run(from_step: int = 1) -> None:
    """Run the pipeline from the given step number (1-6)."""
    for step in STEPS:
        if step.number < from_step:
            continue
        print(f"\n{'=' * 50}")
        print(f"Step {step.number}: {step.name}")
        print(f"{'=' * 50}")
        step.execute()

    print("\nPipeline complete.")
