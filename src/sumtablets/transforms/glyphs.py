"""Convert transliterations to Unicode cuneiform via glyph name lookups."""

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

import pandas as pd
from tqdm import tqdm

tqdm.pandas()


# --------------------------------------------------------------------------------------
# ---------------------------- Constants -----------------------------------------------
# --------------------------------------------------------------------------------------

SPECIAL_TOKENS = {
    "<SURFACE>",
    "<COLUMN>",
    "<BLANK_SPACE>",
    "<RULING>",
    "...",
    "\n",
    "<unk>",
}

UNK = "<unk>"

NUMERIC_PATTERN = re.compile(r"^\d+(/\d+)?(\.\d+)?(\s*\([^)]+\))?$")


# --------------------------------------------------------------------------------------
# ---------------------------- GlyphStats ----------------------------------------------
# --------------------------------------------------------------------------------------


@dataclass
class GlyphStats:
    """Accumulates stats during glyph conversion."""

    unk_readings_all: list = field(default_factory=list)
    non_unk_readings_all: list = field(default_factory=list)
    unk_readings_sign_name: list = field(default_factory=list)
    unk_readings_num: list = field(default_factory=list)
    unk_reading_other: list = field(default_factory=list)
    glyph_names_not_in_map: list = field(default_factory=list)
    glyph_names_no_unicode: list = field(default_factory=list)
    glyph_names_found_unicode: list = field(default_factory=list)
    glyph_to_observed_readings: dict = field(default_factory=dict)


# --------------------------------------------------------------------------------------
# ------------------------------- Public API -------------------------------------------
# --------------------------------------------------------------------------------------


def add_glyphs(
    df: pd.DataFrame,
    morpheme_to_glyph_names: dict[str, list[str]],
    glyph_name_to_glyph: dict[str, str],
    transliteration_replacements: list[tuple[str, str]],
    glyph_name_replacements: dict[str, str],
    number_readings: dict[str, str],
) -> tuple[pd.DataFrame, GlyphStats]:
    """Add Unicode cuneiform glyphs to a DataFrame of transliterations.

    Args:
        df: DataFrame with 'transliteration' and 'transliteration_clean' columns.
        morpheme_to_glyph_names: Mapping from reading to list of glyph names.
        glyph_name_to_glyph: Mapping from glyph name to Unicode character.
        transliteration_replacements: Ordered list of [old, new] replacement pairs.
        glyph_name_replacements: Mapping of glyph names to swap before Unicode lookup.
        number_readings: Mapping from number strings to their readings.

    Returns:
        Tuple of (processed DataFrame, conversion stats).
    """
    df = df.copy()

    # Drop raw transliteration, rename cleaned version
    df = df.drop(columns=["transliteration"])
    df = df.rename(columns={"transliteration_clean": "transliteration"})

    # Apply pre-processing replacements
    for old, new in transliteration_replacements:
        df["transliteration"] = df["transliteration"].str.replace(
            old, new, regex=False
        )

    # Build derived lookups
    glyph_names_set = set(glyph_name_to_glyph.keys())
    glyph_name_to_readings: dict[str, list[str]] = defaultdict(list)
    for reading, names in morpheme_to_glyph_names.items():
        for name in names:
            glyph_name_to_readings[name].append(reading)
    for k, v in glyph_name_to_readings.items():
        glyph_name_to_readings[k] = list(set(v))

    stats = GlyphStats()

    # Process rows
    def _process_row(row):
        return _add_glyphs_to_row(
            row,
            morpheme_to_glyph_names=morpheme_to_glyph_names,
            glyph_name_to_glyph=glyph_name_to_glyph,
            glyph_names_set=glyph_names_set,
            glyph_name_to_readings=glyph_name_to_readings,
            glyph_name_replacements=glyph_name_replacements,
            number_readings=number_readings,
            stats=stats,
        )

    print("\nAdding glyphs...")
    df = df.progress_apply(_process_row, axis=1)

    # Postprocessing
    df["transliteration"] = df["transliteration"].str.replace(
        r"\ *\n\ *", "\n", regex=True
    )
    df["transliteration"] = df["transliteration"].str.replace("-{", "{", regex=False)
    df["transliteration"] = df["transliteration"].str.replace("}-", "}", regex=False)
    df["transliteration"] = df["transliteration"].str.replace(
        "<unk>-", "<unk> ", regex=False
    )
    df["transliteration"] = df["transliteration"].str.replace(
        "-<unk>", " <unk>", regex=False
    )

    for key in ["transliteration", "glyph_names", "glyphs"]:
        df[key] = df[key].str.replace(r"(\ *\.{3,} *)+", "...", regex=True)

    df["glyphs"] = df["glyphs"].str.replace(" ", "", regex=False)

    # Reorganize columns
    df = df[["id", "period", "genre", "transliteration", "glyph_names", "glyphs"]]

    # Deduplication
    df = df.drop_duplicates(subset=["transliteration"])
    df = df.drop_duplicates(subset=["glyphs"])

    return df, stats


def print_stats(stats: GlyphStats) -> None:
    """Print conversion success/failure stats."""
    _print_reading_to_glyph_name_stats(stats)
    _print_glyph_name_to_unicode_stats(stats)


# --------------------------------------------------------------------------------------
# ------------------------------- Row Processing ---------------------------------------
# --------------------------------------------------------------------------------------


def _add_glyphs_to_row(
    row: pd.Series,
    *,
    morpheme_to_glyph_names: dict[str, list[str]],
    glyph_name_to_glyph: dict[str, str],
    glyph_names_set: set[str],
    glyph_name_to_readings: dict[str, list[str]],
    glyph_name_replacements: dict[str, str],
    number_readings: dict[str, str],
    stats: GlyphStats,
) -> pd.Series:
    text = row["transliteration"]

    # (1) Get it ready for tokenization
    text = text.replace("\n", " \n ")
    text = text.replace("...", " ... ")
    text = re.sub(r"\ +", " ", text)

    # (2) Split into wordforms (e.g. lugal-la-ka)
    wordforms = [wf for wf in text.split(" ") if wf and wf != "|" and wf != ".|"]

    # (3) Get glyph names
    transliteration = ""
    glyph_names = ""
    glyphs = ""

    for wordform in wordforms:
        data = _get_wordform_glyph_data(
            wordform,
            morpheme_to_glyph_names=morpheme_to_glyph_names,
            glyph_name_to_glyph=glyph_name_to_glyph,
            glyph_names_set=glyph_names_set,
            glyph_name_to_readings=glyph_name_to_readings,
            glyph_name_replacements=glyph_name_replacements,
            number_readings=number_readings,
            stats=stats,
        )
        transliteration += "-".join([morpheme for morpheme, _, _ in data]) + " "
        glyph_names += " ".join([glyph_name for _, glyph_name, _ in data]) + " "
        glyphs += "".join([glyph for _, _, glyph in data]) + " "

        # Record observed readings
        for item in data:
            morpheme, _, glyph = item
            if morpheme in SPECIAL_TOKENS:
                continue
            if glyph not in stats.glyph_to_observed_readings:
                stats.glyph_to_observed_readings[glyph] = Counter()
            stats.glyph_to_observed_readings[glyph][morpheme] += 1

    row["transliteration"] = transliteration.strip()
    row["glyph_names"] = glyph_names.strip()
    row["glyphs"] = glyphs.strip()
    return row


# --------------------------------------------------------------------------------------
# --------------------------- Glyph Names  ---------------------------------------------
# --------------------------------------------------------------------------------------


def _get_wordform_glyph_data(
    wordform: str,
    *,
    morpheme_to_glyph_names: dict[str, list[str]],
    glyph_name_to_glyph: dict[str, str],
    glyph_names_set: set[str],
    glyph_name_to_readings: dict[str, list[str]],
    glyph_name_replacements: dict[str, str],
    number_readings: dict[str, str],
    stats: GlyphStats,
) -> list[tuple[str, str, str]]:
    if wordform in SPECIAL_TOKENS:
        return [(wordform, wordform, wordform)]

    # Break wordform into morphemes
    morphemes: list[str] = _split_wordform_into_morphemes(wordform, number_readings)

    # Get possible glyph names for each morpheme
    morphemes_and_possible_glyph_names: list[tuple[str, list[str]]] = [
        _get_morpheme_glyph_names(
            m,
            morpheme_to_glyph_names=morpheme_to_glyph_names,
            glyph_names_set=glyph_names_set,
            glyph_name_to_readings=glyph_name_to_readings,
            number_readings=number_readings,
            stats=stats,
        )
        for m in morphemes
    ]

    # Only accept morphemes with exactly one glyph name
    morphemes_and_glyph_names: list[tuple[str, str]] = []
    for morpheme, possible_glyph_names in morphemes_and_possible_glyph_names:
        glyph_name = UNK if len(possible_glyph_names) != 1 else possible_glyph_names[0]
        morpheme = UNK if glyph_name == UNK else morpheme
        morphemes_and_glyph_names.append((morpheme, glyph_name))

        if glyph_name == UNK:
            stats.unk_readings_all.append(morpheme)
        else:
            stats.non_unk_readings_all.append(morpheme)

    # Now get the glyphs
    morphemes_glyph_names_and_glyphs: list[tuple[str, str, str]] = []
    for morpheme, glyph_name in morphemes_and_glyph_names:
        if glyph_name == "N":
            continue

        if glyph_name in glyph_name_replacements:
            glyph_name = glyph_name_replacements[glyph_name]

        if morpheme == UNK:
            morphemes_glyph_names_and_glyphs.append((UNK, UNK, UNK))
        else:
            unicode = _glyph_name_to_unicode(glyph_name, glyph_name_to_glyph, stats)
            if unicode == UNK or "X" in unicode:
                morphemes_glyph_names_and_glyphs.append((UNK, UNK, UNK))
            else:
                morphemes_glyph_names_and_glyphs.append((morpheme, glyph_name, unicode))

    return morphemes_glyph_names_and_glyphs


def _split_wordform_into_morphemes(
    wf: str, number_readings: dict[str, str]
) -> list[str]:
    if wf in number_readings:
        wf_ = number_readings[wf]
    elif wf.split("-", 1)[0] in number_readings:
        # cases like "7-bi"
        split_ = wf.split("-", 1)
        wf_ = number_readings[split_[0]] + "-" + split_[1]
    else:
        wf_ = wf

    # uri₅{ki} -> [uri₅, {ki}]
    split_ = re.split(r"(\{.*?\})", wf_)

    # Split on space, which should only happen if it
    # is one of the number replacements below
    split_ = [s.split(" ") for s in split_ if s]
    split_ = [s for sublist in split_ for s in sublist if s]  # Flatten

    # Split on hyphens, but not within parentheses
    split_ = [re.split(r"-(?![^(]*\))", s) for s in split_ if s]
    split_ = [s for sublist in split_ for s in sublist if s]  # Flatten

    # split and reverse any morphemes with colons
    # e.g. "mu-lu:gal-e" -> ["mu", "gal", "lu", "e"]
    # split_ = [s.split(":")[::-1] if ":" in s else [s] for s in split_ if s]
    # split_ = [s for sublist in split_ for s in sublist if s]  # Flatten

    return [s for s in split_ if s]


def _get_morpheme_glyph_names(
    morpheme: str,
    *,
    morpheme_to_glyph_names: dict[str, list[str]],
    glyph_names_set: set[str],
    glyph_name_to_readings: dict[str, list[str]],
    number_readings: dict[str, str],
    stats: GlyphStats,
) -> tuple[str, list[str]]:
    # only want to do this when it stands on its own
    morpheme = "ŋeš₂" if morpheme == "geš₂" else morpheme

    if morpheme in ["x", "n", "X", "N"]:
        return "...", ["..."]

    # Numbers
    if NUMERIC_PATTERN.match(morpheme):
        return _get_number_glyph_names(
            morpheme,
            morpheme_to_glyph_names=morpheme_to_glyph_names,
            glyph_names_set=glyph_names_set,
            stats=stats,
        )

    # Already glyph name (reading uncertain)
    if morpheme in glyph_names_set:
        return UNK, [morpheme]

    # layup
    morpheme_ = morpheme.replace("{", "").replace("}", "")  # {ki} -> ki
    if morpheme_ in morpheme_to_glyph_names:
        return morpheme, morpheme_to_glyph_names[morpheme_]

    # Sign name but that sign is not in the list.
    # But since sign names are based on a valid reading,
    # we can lowercase it and check again to get the more standard glyph name.
    # Note: the lowercase version may not be the right reading,
    # but we'll use it anyway...
    # It is the highest probability and introduces, I think,
    # a desirable amount of noise
    if morpheme.isupper():
        morpheme_ = morpheme.lower()
        if morpheme_.lower() in morpheme_to_glyph_names:
            return UNK, morpheme_to_glyph_names[morpheme_]
        # give up hope :/
        stats.unk_readings_sign_name.append(morpheme)
        return UNK, []

    if "(" in morpheme and ")" in morpheme:
        split_ = morpheme.split("(")
        morpheme_, glyph_name_ = split_[0], split_[1].replace(")", "")

        if morpheme_ in morpheme_to_glyph_names:
            possible_glyph_names = morpheme_to_glyph_names[morpheme_]
            if len(possible_glyph_names) == 1:
                return morpheme_, possible_glyph_names
            if glyph_name_ in possible_glyph_names:
                return morpheme_, [glyph_name_]

        if glyph_name_ in glyph_name_to_readings:
            possible_readings = glyph_name_to_readings[glyph_name_]
            if len(possible_readings) == 1:
                return possible_readings[0], [glyph_name_]

    stats.unk_reading_other.append(morpheme)
    return morpheme, []


def _get_number_glyph_names(
    morpheme: str,
    *,
    morpheme_to_glyph_names: dict[str, list[str]],
    glyph_names_set: set[str],
    stats: GlyphStats,
) -> tuple[str, list[str]]:
    if morpheme in morpheme_to_glyph_names:
        return morpheme, morpheme_to_glyph_names[morpheme]
    if morpheme.lower() in morpheme_to_glyph_names:
        return morpheme.lower(), morpheme_to_glyph_names[morpheme.lower()]
    if morpheme in glyph_names_set:
        return morpheme, [morpheme]

    stats.unk_readings_num.append(morpheme)
    return morpheme, []


# --------------------------------------------------------------------------------------
# ------------------------------- Glyphs -----------------------------------------------
# --------------------------------------------------------------------------------------


def _glyph_name_to_unicode(
    glyph_name: str, glyph_name_to_glyph: dict[str, str], stats: GlyphStats
) -> str:
    if glyph_name in SPECIAL_TOKENS:
        return glyph_name

    if glyph_name not in glyph_name_to_glyph:
        stats.glyph_names_not_in_map.append(glyph_name)
        return UNK

    unicode = glyph_name_to_glyph[glyph_name]
    if not unicode:
        stats.glyph_names_no_unicode.append(glyph_name)
        return UNK

    stats.glyph_names_found_unicode.append(glyph_name)
    return unicode


# --------------------------------------------------------------------------------------
# ------------------------------- Reports  ---------------------------------------------
# --------------------------------------------------------------------------------------


def _print_report(x, title):
    print()
    print(f"----- {title} -----")
    counter = Counter(x)
    top_ = counter.most_common(20)
    for token, count in top_:
        print(f" > {token} – {count}")
    print("Total: ", len(x))


def _print_reading_to_glyph_name_stats(stats: GlyphStats) -> None:
    num_unk_readings = len(stats.unk_readings_all)
    num_non_unk_readings = len(stats.non_unk_readings_all)
    num_all_morphemes = num_unk_readings + num_non_unk_readings
    pct_unk = round(num_unk_readings / num_all_morphemes * 100, 2)
    pct_non_unk = round(num_non_unk_readings / num_all_morphemes * 100, 2)
    print()
    print(f"# of morphemes unable to convert: {num_unk_readings} ({pct_unk}%)")
    print(
        f"# of morphemes successfully converted: {num_non_unk_readings} ({pct_non_unk}%)"
    )
    print()
    _print_report(stats.unk_readings_sign_name, "UNK SIGN NAMES")
    _print_report(stats.unk_readings_num, "UNK NUMBERS")
    _print_report(stats.unk_reading_other, "UNK OTHER")
    print()


def _print_glyph_name_to_unicode_stats(stats: GlyphStats) -> None:
    num_unable_to_convert = len(stats.glyph_names_not_in_map) + len(
        stats.glyph_names_no_unicode
    )
    num_converted = len(stats.glyph_names_found_unicode)
    num_total = num_unable_to_convert + num_converted
    pct_unable_to_convert = round(num_unable_to_convert / num_total * 100, 2)
    pct_converted = round(num_converted / num_total * 100, 2)
    print()
    print(
        f"# of names unable to convert: {num_unable_to_convert} ({pct_unable_to_convert}%)"
    )
    print(f"# of names successfully converted: {num_converted} ({pct_converted}%)")
    print()
    _print_report(stats.glyph_names_not_in_map, "NAME NOT IN glyph_name_to_glyph.json")
    _print_report(stats.glyph_names_no_unicode, "NO UNICODE")
    print()
