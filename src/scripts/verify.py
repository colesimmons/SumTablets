"""
Verify that locally generated data matches the published HuggingFace dataset.

Downloads and caches the HF dataset on first run (as parquet for fast reloads).
Subsequent runs compare against the cached copy.

Usage:
    uv run python -m src.scripts.verify
    uv run python -m src.scripts.verify --redownload   # force fresh download
"""

import argparse
import hashlib
import io
import urllib.request
import pandas as pd

from sumtablets.paths import CACHE_DIR, GENERATED_DIR
HF_CACHE_PATH = CACHE_DIR / "hf_combined.csv"
HF_BASE_URL = "https://huggingface.co/datasets/colesimmons/SumTablets/resolve/main"
SPLITS = ["train", "validation", "test"]
COMPARE_COLS = ["id", "period", "genre", "transliteration", "glyph_names", "glyphs"]


def download_hf_dataset() -> pd.DataFrame:
    """Download all splits from HuggingFace and return as a single DataFrame."""
    dfs = []
    for split in SPLITS:
        url = f"{HF_BASE_URL}/{split}.csv"
        print(f"  Downloading {split}.csv ...")
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
        df = pd.read_csv(io.BytesIO(raw), low_memory=False, encoding="utf-8")
        print(f"    {len(df)} rows")
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)


def get_hf_data(redownload: bool = False) -> pd.DataFrame:
    """Get HF data, using parquet cache if available."""
    if HF_CACHE_PATH.exists() and not redownload:
        print(f"Using cached HF data: {HF_CACHE_PATH}")
        return pd.read_csv(HF_CACHE_PATH, low_memory=False, encoding="utf-8")

    print("Downloading HF dataset ...")
    df = download_hf_dataset()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(HF_CACHE_PATH, index=False, encoding="utf-8")
    print(f"Cached to {HF_CACHE_PATH}")
    return df


def load_local_data() -> pd.DataFrame:
    """Load and combine local split CSVs."""
    dfs = []
    for split in SPLITS:
        path = GENERATED_DIR / f"{split}.csv"
        df = pd.read_csv(path, low_memory=False, encoding="utf-8")
        print(f"  Local {split}: {len(df)} rows")
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)


def df_hash(df: pd.DataFrame) -> str:
    """Deterministic SHA-256 of a DataFrame's content."""
    return hashlib.sha256(
        pd.util.hash_pandas_object(df).values.tobytes()
    ).hexdigest()


def compare(hf: pd.DataFrame, local: pd.DataFrame) -> bool:
    """Compare HF and local datasets. Returns True if they match."""
    ok = True

    # --- Row counts ---
    print(f"\n{'=' * 60}")
    print(f"Row counts  —  HF: {len(hf)}  |  Local: {len(local)}")
    if len(hf) != len(local):
        print("  FAIL  Row count mismatch")
        ok = False
    else:
        print("  PASS")

    # --- Column check ---
    hf_cols = set(hf.columns)
    local_cols = set(local.columns)
    if hf_cols != local_cols:
        print(f"\nColumn sets differ:")
        if hf_cols - local_cols:
            print(f"  HF only:    {hf_cols - local_cols}")
        if local_cols - hf_cols:
            print(f"  Local only: {local_cols - hf_cols}")
    cols = [c for c in COMPARE_COLS if c in hf_cols and c in local_cols]
    hf = hf[cols]
    local = local[cols]

    # --- Sort by ID for deterministic comparison ---
    hf = hf.sort_values("id").reset_index(drop=True)
    local = local.sort_values("id").reset_index(drop=True)

    # --- ID set comparison ---
    hf_ids = set(hf["id"])
    local_ids = set(local["id"])
    only_hf = hf_ids - local_ids
    only_local = local_ids - hf_ids

    if only_hf or only_local:
        ok = False
        if only_hf:
            sample = sorted(only_hf)[:10]
            print(f"\n  FAIL  {len(only_hf)} IDs only in HF: {sample}{'...' if len(only_hf) > 10 else ''}")
        if only_local:
            sample = sorted(only_local)[:10]
            print(f"\n  FAIL  {len(only_local)} IDs only in local: {sample}{'...' if len(only_local) > 10 else ''}")
    else:
        print(f"  PASS  ID sets identical ({len(hf_ids)} IDs)")

    # --- Row-by-row comparison on shared IDs ---
    shared = sorted(hf_ids & local_ids)
    hf_s = hf[hf["id"].isin(shared)].sort_values("id").reset_index(drop=True)
    local_s = local[local["id"].isin(shared)].sort_values("id").reset_index(drop=True)

    diff_cols = []
    for col in cols:
        if col == "id":
            continue
        mismatches = hf_s[col].fillna("") != local_s[col].fillna("")
        n = mismatches.sum()
        if n > 0:
            ok = False
            diff_cols.append((col, n))
            print(f"\n  FAIL  Column '{col}': {n} rows differ")
            # Show first 3 examples
            idxs = mismatches[mismatches].index[:3]
            for i in idxs:
                print(f"    ID {hf_s.loc[i, 'id']}:")
                print(f"      HF:    {repr(str(hf_s.loc[i, col])[:120])}")
                print(f"      Local: {repr(str(local_s.loc[i, col])[:120])}")

    if not diff_cols:
        print(f"  PASS  All {len(shared)} rows match across columns {cols[1:]}")

    # --- Overall hash ---
    h_hf = df_hash(hf_s)
    h_local = df_hash(local_s)
    print(f"\nSorted hash  —  HF:    {h_hf}")
    print(f"                Local: {h_local}")
    if h_hf == h_local:
        print("  PASS  Hashes match")
    else:
        print("  FAIL  Hashes differ")
        ok = False

    print(f"{'=' * 60}")
    return ok


def main():
    parser = argparse.ArgumentParser(description="Verify local data against HuggingFace dataset")
    parser.add_argument("--redownload", action="store_true", help="Force re-download of HF data")
    args = parser.parse_args()

    hf = get_hf_data(redownload=args.redownload)
    local = load_local_data()
    match = compare(hf, local)
    raise SystemExit(0 if match else 1)


if __name__ == "__main__":
    main()
