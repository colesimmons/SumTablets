import json
import re
from collections import Counter, defaultdict

import pandas as pd
from constants import OUTPUT_DIR
from tqdm import tqdm

tqdm.pandas()

# --------------------------------------------------------------------------------------
# ---------------------------- Constants -----------------------------------------------
# --------------------------------------------------------------------------------------
# INFILE
# OUTFILE
# SPECIAL_TOKENS
# UNK

# READING_TO_GLYPH_NAME
# GLYPH_NAME_TO_UNICODE
# GLYPH_NAMES
# GLYPH_NAME_TO_READINGS

# NUMBERS_TO_MORPHEMES

# SIGN_LIST_REPLACEMENTS
# SIGN_NAME_REPLACEMENTS
# READING_PLUS_SIGN_NAME_REPLACEMENTS
# READING_REPLACEMENTS
# NUM_REPLACEMENTS
# FINAL_REPLACEMENTS
# ALL_REPLACEMENTS

INFILE = f"{OUTPUT_DIR}/3_cleaned_transliterations.csv"
OUTFILE = f"{OUTPUT_DIR}/5_with_glyphs.csv"

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

# reading (str) -> list of glyph names (list[str])
with open(f"{OUTPUT_DIR}/morpheme_to_glyph_names.json", encoding="utf-8") as infile:
    READING_TO_GLYPH_NAME: dict[str, list[str]] = json.load(infile)

# glyph name (str) -> unicode (str)
with open(f"{OUTPUT_DIR}/glyph_name_to_glyph.json", encoding="utf-8") as infile:
    GLYPH_NAME_TO_UNICODE: dict[str, str] = json.load(infile)

# set of all glyph names
GLYPH_NAMES = set(GLYPH_NAME_TO_UNICODE.keys())

# glyph name (str) -> readings (list[str])
GLYPH_NAME_TO_READINGS: dict[str, list[str]] = defaultdict(list)
for reading, glyph_names in READING_TO_GLYPH_NAME.items():
    for glyph_name in glyph_names:
        GLYPH_NAME_TO_READINGS[glyph_name].append(reading)
for k, v in GLYPH_NAME_TO_READINGS.items():
    GLYPH_NAME_TO_READINGS[k] = list(set(v))

NUMBERS_TO_READINGS = {
    "1/2": "1/2(diš)",
    "1/3": "1/3(diš)",
    "1/4": "1/3(iku)",
    "2/3": "2/3(diš)",
    "5/6": "5/6(diš)",
    "1": "1(diš)",
    "2": "2(diš)",
    "3": "3(diš)",
    "4": "4(diš)",
    "5": "5(diš)",
    "6": "6(diš)",
    "7": "7(diš)",
    "8": "8(diš)",
    "9": "9(diš)",
    "10": "1(u)",
    "11": "1(u) 1(diš)",
    "12": "1(u) 2(diš)",
    "14": "1(u) 4(diš)",
    "18": "1(u) 8(diš)",
    "20": "2(u)",
    "21": "2(u) 1(diš)",
    "23": "2(u) 3(diš)",
    "24": "2(u) 4(diš)",
    "25": "2(u) 5(diš)",
    "30": "3(u)",
    "36": "3(u) 6(diš)",
    "40": "4(u)",
    "50": "5(u)",
    "60": "6(u)",
    "600": "1(gešʾu)",
    "900": "1(gešʾu) 5(geš₂)",
    "3600": "1(šarʾu@c)",
    "36000": "1(šar₂)",
}


SIGN_LIST_REPLACEMENTS = {
    "BAU377": "GIŠ",  # technically GIŠ~v...
    "KWU147": "LIL",
    "KWU354": "LUM",
    "KWU636": "KU₄",
    "KWU777": "ŠITA",
    "KWU844": "|E₂×AŠ@t|",
    "LAK060": "|UŠ×TAK₄|",
    "LAK085": "|SI×TAK₄|",
    "LAK173": "KAD₅",
    "LAK175": "SANGA₂",
    "LAK218": "|ZU&ZU.SAR|",
    "LAK449": "|NUNUZ.AB₂|",
    "LAK524": "|ZUM×TUG₂|",
    "LAK589": "GISAL",
    "LAK672a": "UŠX",
    "LAK672b": "MUNSUB",
    "LAK720": "|LAK648×(PAP.PAP.LU₃)|",
    "LAK769": "|LAGAB×AN|",
    "LAK777": "|DAG.KISIM₅×UŠ|",
}

GLYPH_NAME_REPLACEMENTS = {
    "(ŠE.1(AŠ))": "(ŠE.AŠ)",
    "(ŠE.2(AŠ))": "(ŠE.AŠ.AŠ)",
    "|E₂.BALAG|": "|KID.BALAG|",
    "|SAHAR.DU₆.TAK₄|": "IŠ LAGAR@g TAK₄",
    "|ŠE.ŠE|": "ŠE ŠE",
    "(EN.ZU-TI.LA.BI-DU₁₁.GA)": "|EN.ZU| TI LA BI KA GA",
    "|EN₂.E₂|": "|ŠU₂.AN| E₂",
    "|TAB.BA|": "TAB BA",
    "|GAR.UD|": "GAR UD",
    "|NE.DAG|": "NE DAG",
    "|ŠU₂.DUN₃@g@g@s|": "|ŠU₂.DUN₃|",
    "BAD₃": "|EZEN×BAD|",
    "BIL₂": "NE@s",
    "DU₈": "DUH",
    "ERIM": "ERIN₂",
    "GAG": "KAK",
    "GIN₂": "DUN₃@g",
    "GU₄": "GUD",
    "GUB": "DU",
    "ITI": "|UD×(U.U.U)|",
    "MUNUS": "SAL",
    "NIG₂": "GAR",
    "ŠAG₄": "ŠA₃",
    "ŠE₃": "EŠ₂",
    "SILA₄": "|GA₂×PA|",
    "SIG₇": "IGI@g",
    "TUR₃": "|NUN.LAGAR|",
    "UH₃": "KUŠU₂",
    "U₈": "|LAGAB×(GUD&GUD)|",
}

# Remember that this comes after the above replacements,
# so some of the parenthetical values have already been replaced
READING_PLUS_SIGN_NAME_REPLACEMENTS = {
    "ad₆ ": "ad₆(|LU₂.LAGAB×U|) ",
    "dabₓ(|LAGAB×(GUD&GUD)|)": "dibₓ(|LAGAB×(GUD&GUD)|)",
    "erinₓ(KWU896)": "erenₓ(KWU896)",
    "gurₓ(|ŠE.KIN|)še₃": "gurₓ(|ŠE.KIN|)-še₃",
    "gurumₓ(|IGI.ERIN₂|)": "gurum₂",
    "ilduₓ(NAGAR)": "nagar",
    "itiₓ(|UD@s×BAD|)": "iti₂(|UD@s×BAD|)",
    "itiₓ(|UD@s×TIL|)": "iti₂(|UD@s×BAD|)",
    "kuₓ(KU₄)": "ku₄",
    "lumₓ(LUM)": "lum",
    "mudₓ(|NUNUZ.AB₂|)": "mud₃(|NUNUZ.AB₂|)",
    "sangaₓ(|ŠID.GAR|)": "saŋŋaₓ(|ŠID.GAR|)",
    "šaganₓ(AMA)": "daŋal",
    "šitaₓ(ŠITA)": "šita",
    "tabₓ(MAN)": "tab₄",
    "umbinₓ(|UR₂×KID₂|)": "umbin(|UR₂×KID₂|)",
    "ušurₓ(|LAL₂×TUG₂|)": "ušurₓ(|LAL₂.TUG₂|)",
    "ugaₓ(NAGA)": "uga₃",
    "zeₓ(SIG₇)": "ziₓ(IGI@g)",
    "zeₓ(IGI@g)": "ziₓ(IGI@g)",
}

READING_REPLACEMENTS = {
    "babila": "babilim",
    "eri₁₃": "ere₁₃",
    "eriš₂": "ereš₂",
    "šu+nigin₂": "šuniŋin",
    "šu+nigin": "šuniŋin",
    "+...": "...",
    "...+": "...",
    "@c": "",
    "@t": "",
    "@v": "",
    "@90": "",
}

# As far as I can tell, there are at most 2 ways to do fractions
NUM_REPLACEMENTS = {
    "1/2(aš)": "1/2",
    "1/3(aš)": "1/3",
    "1/4(aš)": "1/4",
    "2/3(aš)": "2/3",
    "5/6(aš)": "5/6",
}

FINAL_REPLACEMENTS = {
    "||LAGAB×(GUD&GUD)|+HUL₂|": "|LAGAB×(GUD&GUD)+HUL₂|",
    "||EZEN×BAD|.AN|": "|EZEN×BAD.AN|",
    "|NINDA₂×(ŠE.2(AŠ@c))|": "|NINDA₂×(ŠE.AŠ.AŠ)|",
}

ALL_REPLACEMENTS = [
    SIGN_LIST_REPLACEMENTS,
    GLYPH_NAME_REPLACEMENTS,
    READING_PLUS_SIGN_NAME_REPLACEMENTS,
    READING_REPLACEMENTS,
    NUM_REPLACEMENTS,
    FINAL_REPLACEMENTS,
]

# --------------------------------------------------------------------------------------
# ---------------------------- Globals  ------------------------------------------------
# --------------------------------------------------------------------------------------
unk_readings_all = []
non_unk_readings_all = []

unk_readings_sign_name = []
unk_readings_num = []
unk_reading_other = []


glyph_names_not_in_map = []
glyph_names_no_unicode = []
glyph_names_found_unicode = []

glyph_to_observed_readings = {}


# --------------------------------------------------------------------------------------
# ------------------------------- Main  ------------------------------------------------
# --------------------------------------------------------------------------------------
def main():
    df = pd.read_csv(INFILE).fillna("")

    # Drop "transliteration" column
    df = df.drop(columns=["transliteration"])

    # Rename transliteration_clean to transliteration
    df = df.rename(columns={"transliteration_clean": "transliteration"})

    # Replace some of the glyph names already present in the transliteration
    # (used when reading is uncertain) with more standard equivalents.
    for replacements in ALL_REPLACEMENTS:
        for k, v in replacements.items():
            df["transliteration"] = df["transliteration"].str.replace(k, v, regex=False)

    df = _add_glyphs(df)
    _print_reading_to_glyph_name_stats()  # how successful?
    _print_glyph_name_to_unicode_stats()  # how successful?

    # (3) Postprocessing
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

    # Reorganize rows
    df = df[
        [
            "id",
            "period",
            "genre",
            "transliteration",
            "glyph_names",
            "glyphs",
        ]
    ]

    df = _drop_rows_with_identical_transliterations(df)
    df = _drop_rows_with_identical_glyphs(df)

    _print_glyph_count(df)
    _write(df, separate_genre_files=True)
    _save_glyph_to_observed_readings()


def _add_glyphs(df: pd.DataFrame) -> pd.DataFrame:
    print()
    print("Adding glyphs...")
    df = df.progress_apply(_add_glyphs_to_row, axis=1)
    print("Done!")
    return df


def _add_glyphs_to_row(row: pd.Series) -> pd.Series:
    text = row["transliteration"]

    # (1) Get it ready for tokenization
    # --------------------------------
    text = text.replace("\n", " \n ")
    text = text.replace("...", " ... ")
    text = re.sub(r"\ +", " ", text)

    # (2) Split into wordforms (e.g. lugal-la-ka)
    # --------------------------------
    wordforms = [wf for wf in text.split(" ") if wf and wf != "|" and wf != ".|"]

    # (3) Get glyph names
    # --------------------------------
    transliteration = ""
    glyph_names = ""
    glyphs = ""

    for wordform in wordforms:
        data = _get_wordform_glyph_data(wordform)  # [(morpheme, glyph_name, glyph), ]
        transliteration += "-".join([morpheme for morpheme, _, _ in data]) + " "
        glyph_names += " ".join([glyph_name for _, glyph_name, _ in data]) + " "
        glyphs += "".join([glyph for _, _, glyph in data]) + " "

        # Record observed readings
        for item in data:
            morpheme, _, glyph = item
            if morpheme in SPECIAL_TOKENS:
                continue
            # morpheme_ = morpheme.replace("{", "").replace("}", "")
            if glyph not in glyph_to_observed_readings:
                glyph_to_observed_readings[glyph] = Counter()
            glyph_to_observed_readings[glyph][morpheme] += 1

    row["transliteration"] = transliteration.strip()
    row["glyph_names"] = glyph_names.strip()
    row["glyphs"] = glyphs.strip()
    return row


# --------------------------------------------------------------------------------------
# --------------------------- Glyph Names  ---------------------------------------------
# --------------------------------------------------------------------------------------
SWAP_GLYPH_NAMES = {
    "UN": "KALAM@g",
    "ŠITA₂": "|ŠITA.GIŠ|",
    "DE₂": "|UMUM×KASKAL|",
    "|ŠU₂.3xAN|": "|ŠU₂.3×AN|",
    "|ŠU₂.DUN₃@g@g@s|": "|ŠU₂.DUN₃|",
    "LAK212": "|A.TU.GABA.LIŠ|",
}


def _get_wordform_glyph_data(wordform: str) -> list[tuple[str, str, str]]:
    if wordform in SPECIAL_TOKENS:
        return [(wordform, wordform, wordform)]

    # Break wordform into morphemes
    morphemes: list[str] = _split_wordform_into_morphemes(wordform)

    # Get possible glyph names for each morpheme
    morphemes_and_possible_glyph_names: list[tuple[str, list[str]]] = [
        _get_morpheme_glyph_names(m) for m in morphemes
    ]

    # Only accept morphemes with exactly one glyph name
    morphemes_and_glyph_names: list[tuple[str, str]] = []
    for morpheme, possible_glyph_names in morphemes_and_possible_glyph_names:
        glyph_name = UNK if len(possible_glyph_names) != 1 else possible_glyph_names[0]
        morpheme = UNK if glyph_name == UNK else morpheme
        morphemes_and_glyph_names.append((morpheme, glyph_name))

        if glyph_name == UNK:
            unk_readings_all.append(morpheme)
        else:
            non_unk_readings_all.append(morpheme)

    # Now get the glyphs
    morphemes_glyph_names_and_glyphs: list[tuple[str, str, str]] = []
    for morpheme, glyph_name in morphemes_and_glyph_names:
        if glyph_name == "N":
            continue

        if glyph_name in SWAP_GLYPH_NAMES:
            glyph_name = SWAP_GLYPH_NAMES[glyph_name]

        if morpheme == UNK:
            morphemes_glyph_names_and_glyphs.append((UNK, UNK, UNK))
        else:
            unicode = _glyph_name_to_unicode(glyph_name)
            if unicode == UNK or "X" in unicode:
                morphemes_glyph_names_and_glyphs.append((UNK, UNK, UNK))
            else:
                morphemes_glyph_names_and_glyphs.append((morpheme, glyph_name, unicode))

    return morphemes_glyph_names_and_glyphs


def _split_wordform_into_morphemes(wf: str) -> list[str]:
    if wf in NUMBERS_TO_READINGS:
        wf_ = NUMBERS_TO_READINGS[wf]
    elif wf.split("-", 1)[0] in NUMBERS_TO_READINGS:
        # cases like "7-bi"
        split_ = wf.split("-", 1)
        wf_ = NUMBERS_TO_READINGS[split_[0]] + "-" + split_[1]
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


NUMERIC_PATTERN = re.compile(r"^\d+(/\d+)?(\.\d+)?(\s*\([^)]+\))?$")


def _get_morpheme_glyph_names(morpheme: str) -> tuple[str, list[str]]:
    # only want to do this when it stands on its own
    morpheme = "ŋeš₂" if morpheme == "geš₂" else morpheme

    if morpheme in ["x", "n", "X", "N"]:
        return "...", ["..."]

    # Numbers
    if NUMERIC_PATTERN.match(morpheme):
        return _get_number_glyph_names(morpheme)

    # Already glyph name (reading uncertain)
    if morpheme in GLYPH_NAMES:
        return UNK, [morpheme]

    # layup
    morpheme_ = morpheme.replace("{", "").replace("}", "")  # {ki} -> ki
    if morpheme_ in READING_TO_GLYPH_NAME:
        return morpheme, READING_TO_GLYPH_NAME[morpheme_]

    # Sign name but that sign is not in the list.
    # But since sign names are based on a valid reading,
    # we can lowercase it and check again to get the more standard glyph name.
    # Note: the lowercase version may not be the right reading,
    # but we'll use it anyway...
    # It is the highest probability and introduces, I think,
    # a desirable amount of noise
    if morpheme.isupper():
        morpheme_ = morpheme.lower()
        if morpheme_.lower() in READING_TO_GLYPH_NAME:
            return UNK, READING_TO_GLYPH_NAME[morpheme_]
        # give up hope :/
        unk_readings_sign_name.append(morpheme)
        return UNK, []

    if "(" in morpheme and ")" in morpheme:
        split_ = morpheme.split("(")
        morpheme_, glyph_name_ = split_[0], split_[1].replace(")", "")

        if morpheme_ in READING_TO_GLYPH_NAME:
            possible_glyph_names = READING_TO_GLYPH_NAME[morpheme_]
            if len(possible_glyph_names) == 1:
                return morpheme_, possible_glyph_names
            if glyph_name_ in possible_glyph_names:
                return morpheme_, [glyph_name_]

        if glyph_name_ in GLYPH_NAME_TO_READINGS:
            possible_readings = GLYPH_NAME_TO_READINGS[glyph_name_]
            if len(possible_readings) == 1:
                return possible_readings[0], [glyph_name_]

    unk_reading_other.append(morpheme)
    return morpheme, []


def _get_number_glyph_names(morpheme: str) -> tuple[str, list[str]]:
    if morpheme in READING_TO_GLYPH_NAME:
        return morpheme, READING_TO_GLYPH_NAME[morpheme]
    if morpheme.lower() in READING_TO_GLYPH_NAME:
        return morpheme.lower(), READING_TO_GLYPH_NAME[morpheme.lower()]
    if morpheme in GLYPH_NAMES:
        return morpheme, [morpheme]

    unk_readings_num.append(morpheme)
    return morpheme, []


# --------------------------------------------------------------------------------------
# ------------------------------- Glyphs -----------------------------------------------
# --------------------------------------------------------------------------------------
def _glyph_name_to_unicode(glyph_name: str) -> str:
    if glyph_name in SPECIAL_TOKENS:
        return glyph_name

    if glyph_name not in GLYPH_NAME_TO_UNICODE:
        glyph_names_not_in_map.append(glyph_name)
        return UNK

    unicode = GLYPH_NAME_TO_UNICODE[glyph_name]
    if not unicode:
        glyph_names_no_unicode.append(glyph_name)
        return UNK

    glyph_names_found_unicode.append(glyph_name)
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


def _print_reading_to_glyph_name_stats():
    num_unk_readings = len(unk_readings_all)
    num_non_unk_readings = len(non_unk_readings_all)
    num_all_morphemes = num_unk_readings + num_non_unk_readings
    pct_unk = round(num_unk_readings / num_all_morphemes * 100, 2)
    pct_non_unk = round(num_non_unk_readings / num_all_morphemes * 100, 2)
    print()
    print(f"# of morphemes unable to convert: {num_unk_readings} ({pct_unk}%)")
    print(
        f"# of morphemes successfully converted: {num_non_unk_readings} ({pct_non_unk}%)"
    )
    print()
    _print_report(unk_readings_sign_name, "UNK SIGN NAMES")
    _print_report(unk_readings_num, "UNK NUMBERS")
    _print_report(unk_reading_other, "UNK OTHER")
    print()


def _print_glyph_name_to_unicode_stats():
    num_unable_to_convert = len(glyph_names_not_in_map) + len(glyph_names_no_unicode)
    num_converted = len(glyph_names_found_unicode)
    num_total = num_unable_to_convert + num_converted
    pct_unable_to_convert = round(num_unable_to_convert / num_total * 100, 2)
    pct_converted = round(num_converted / num_total * 100, 2)
    print()
    print(
        f"# of names unable to convert: {num_unable_to_convert} ({pct_unable_to_convert}%)"
    )
    print(f"# of names successfully converted: {num_converted} ({pct_converted}%)")
    print()
    _print_report(glyph_names_not_in_map, "NAME NOT IN glyph_name_to_glyph.json")
    _print_report(glyph_names_no_unicode, "NO UNICODE")
    print()


# --------------------------------------------------------------------------------------
# -------------------------- Postprocessing  -------------------------------------------
# --------------------------------------------------------------------------------------
def _drop_rows_with_identical_transliterations(df: pd.DataFrame) -> pd.DataFrame:
    print()
    print("Dropping rows with identical transliterations...")
    # uncomment below to see which rows
    # print(df[df["transliteration"].map(df["transliteration"].value_counts() > 1)])
    prev_num_rows = len(df)
    df = df.drop_duplicates(subset=["transliteration"])
    num_rows = len(df)
    print(f"Rows dropped: {prev_num_rows - num_rows}")
    print(f"New number of rows: {num_rows}")
    print()
    return df


def _drop_rows_with_identical_glyphs(df: pd.DataFrame) -> pd.DataFrame:
    print()
    print("Dropping rows with identical glyphs...")
    # uncomment below to see which rows
    # print(df[df["glyphs"].map(df["glyphs"].value_counts() > 1)])
    prev_num_rows = len(df)
    df = df.drop_duplicates(subset=["glyphs"])
    num_rows = len(df)
    print(f"Rows dropped: {prev_num_rows - num_rows}")
    print(f"New number of rows: {num_rows}")
    print()
    return df


# --------------------------------------------------------------------------------------
# -------------------------- Stats / Out  ----------------------------------------------
# --------------------------------------------------------------------------------------
def _print_glyph_count(df: pd.DataFrame):
    # Count glyphs
    def _count_glyph(glyphs):
        for special in SPECIAL_TOKENS:
            glyphs = glyphs.replace(special, "")
        glyphs = glyphs.replace(" ", "")
        return len(glyphs)

    # print total glyph count
    print()
    print("Total glyphs:", df["glyphs"].map(_count_glyph).sum())
    print()


def _write(df: pd.DataFrame, separate_genre_files=False):
    if separate_genre_files:
        for genre in df["genre"].unique():
            genre_name = genre.replace("/", "")
            outfile_ = OUTFILE.replace(".csv", f"_{genre_name}.csv")
            print(f"Writing to {outfile_}...")
            df[df["genre"] == genre].to_csv(outfile_, index=False, encoding="utf-8")

    print(f"Writing to {OUTFILE}...")
    df.to_csv(OUTFILE, index=False, encoding="utf-8")


def _save_glyph_to_observed_readings():
    with open(
        f"{OUTPUT_DIR}/glyph_to_observed_readings.json", "w", encoding="utf-8"
    ) as outfile:
        json.dump(glyph_to_observed_readings, outfile, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
