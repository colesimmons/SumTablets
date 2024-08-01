"""
This script cleans the transliterations in a new "transliteration_clean" column
(for easy comparison) and saves the result to a new csv file.

All uncaught cases are printed, prefixed with "!!!".
"""

import re
from enum import Enum
from typing import Callable, List, Tuple

import pandas as pd

from src.constants import OUTPUT_DIR

INFILE = f"{OUTPUT_DIR}/2_tablets.csv"
OUTFILE = f"{OUTPUT_DIR}/3_cleaned_transliterations.csv"


class SpecialTokensBefore(Enum):
    MISSING = "#MISSING#"
    SURFACE = "#SURFACE#"
    COLUMN = "#COLUMN#"
    BLANK_SPACE = "#BLANK_SPACE#"
    RULING = "#RULING#"
    NEWLINE = "\n"


class SpecialTokensAfter(Enum):
    MISSING = "..."
    SURFACE = "<SURFACE>"
    COLUMN = "<COLUMN>"
    BLANK_SPACE = "<BLANK_SPACE>"
    RULING = "<RULING>"
    NEWLINE = "\n"


# for easier reference
MISSING = SpecialTokensBefore.MISSING.value

# key for new column
KEY = "transliteration_clean"

FunctionAndDesc = Tuple[Callable[[pd.Series], pd.Series], str]


def main():
    print("Loading data...")
    df = pd.read_csv(INFILE).fillna("")
    df[KEY] = df["transliteration"]

    collapse = (
        _collapse_whitespace_hyphens_missing,
        "Collapsing whitespace/hyphens/missing...",
    )

    fns: List[FunctionAndDesc] = [
        # ------ (1) easy wins -----
        (
            _double_angle_brackets,
            'Treating <<abc>> as normal text ("present but must be excised")...',
        ),
        (
            _upper_brackets,
            "Treating upper brackets as normal text (partial breakage)...",
        ),
        (_double_curly_braces, "Getting rid of {{abc}} (linguistic glosses)..."),
        collapse,
        (_sanity_check_1, "Performing first sanity check..."),
        #
        # ------ (2) enclosures out of order -----
        (_check_for_unmatched_brackets, "Checking for unmatched brackets..."),
        (
            _fix_enclosure_order,
            "Fixing enclosure order, e.g. ([abc)def] -> [(abc)def]...",
        ),
        #
        # ------ (3) other elements -----
        (
            _single_angle_brackets,
            'Getting rid of <abc> ("must be supplied but not present")...',
        ),
        (_semicolons, "Converting semicolons to newlines..."),
        (_single_curly_braces, "Removing hyphens like -} and {-..."),
        (_vertical_bars, "Adding hyphens after pairs of vertical bars..."),
        (_parentheses, "Adding hyphens after parentheses..."),
        collapse,
        (_sanity_check_2, "Performing second sanity check..."),
        #
        # ------ (4) MISSING -----
        (_single_square_brackets, "[abc] -> MISSING"),
        # run this a few times
        (_x_o_n, "x, o, and n -> MISSING"),
        (_x_o_n, "x, o, and n -> MISSING"),
        (_x_o_n, "x, o, and n -> MISSING"),
        (_dollar_signs, "$abc$ -> MISSING"),
        (_ellipses, "... -> MISSING"),
        (
            _standalone_parens,
            "Getting rid of standalone parens (may be present but not certain)",
        ),
        collapse,
        (_sanity_check_3, "Performing third sanity check..."),
        #
        # ------ (5) enclosures -----
        (_missing_alone_in_enclosure, "Getting rid of (#MISSING#) and {#MISSING#}"),
        (_empty_enclosures, "Removing empty {} and ()"),
        collapse,
        #
        # ------ (6) final -----
        (_sanity_check_final, "Performing final sanity check..."),
        (_convert_special_tokens, "Converting special tokens..."),
    ]
    for func, desc in fns:
        print("\n➡️ " + desc)
        df = df.apply(func, axis=1)

    # Remove tablets with no transliteration
    df = _remove_tablets_with_no_transliteration(df)

    print(f"Writing to {OUTFILE}...")
    df.to_csv(OUTFILE, index=False)
    print("Done!")


# --------------------------------------------------------------------------------------
# ---------------------------- easy wins -----------------------------------------------
# --------------------------------------------------------------------------------------
def _double_angle_brackets(row: pd.Series) -> pd.Series:
    """
    'The graphemes are present but must be excised for the sense.'
    From: https://oracc.museum.upenn.edu/doc/help/editinginatf/primer/inlinetutorial/index.html

    Get rid of the brackets but keep the text (i.e. treat it like normal text)
    """
    row[KEY] = row[KEY].replace("<<", "")
    row[KEY] = row[KEY].replace(">>", "")
    return row


def _upper_brackets(row: pd.Series) -> pd.Series:
    """
    ⸢abc⸣ is partially broken. Treat it as normal text.
    """
    row[KEY] = row[KEY].replace("⸢", "")
    row[KEY] = row[KEY].replace("⸣", "")
    return row


def _double_curly_braces(row: pd.Series) -> pd.Series:
    """
    'Linguistic glosses are defined for the purposes of this specification
     as glosses which give an alternative to the word(s) in question.
     Such alternatives are typically either variants or translations.'
    From: https://oracc.museum.upenn.edu/doc/help/editinginatf/primer/inlinetutorial/index.html

    Get rid of 'em.
    """
    pattern = r"\{\{[^\n]*?\}\}"
    matches = re.findall(pattern, row[KEY])
    for match in matches:
        print(">> ", match, f" ({row['id']})")
        row[KEY] = row[KEY].replace(match, "")

    pattern = r"\n[^\n]*?\}\}"
    matches = re.findall(pattern, row[KEY])
    for match in matches:
        print(">> ", match.replace("\n", ""), f" ({row['id']})")
        row[KEY] = row[KEY].replace(match, "\n")

    if "{{" in row[KEY] or "}}" in row[KEY]:
        print(f"Uncaught in {row['id']}")

    return row


def _collapse_whitespace_hyphens_missing(row: pd.Series) -> pd.Series:
    # Newlines
    row[KEY] = re.sub(r"([\ \-]*\n[\ \-]*)+", "\n", row[KEY])
    # Spaces
    row[KEY] = re.sub(r"([\-]*\ [\-]*)+", " ", row[KEY])
    # Hyphens
    row[KEY] = re.sub(r"\-+", "-", row[KEY])
    # MISSING
    row[KEY] = re.sub(r"([\ \-]*#MISSING#[\ \-]*)+", MISSING, row[KEY])
    row[KEY] = re.sub(r"(\n#MISSING#(?=\n))+", f"\n{MISSING}", row[KEY])
    return row


DISALLOWED_1 = ["<<", ">>", "⸢", "⸣", "{{", "}}"]


def _sanity_check_1(row: pd.Series) -> pd.Series:
    """Characters that should not be present at this point"""
    for char in DISALLOWED_1:
        if char in row[KEY]:
            print(f"!!! Disallowed character {char} in: {row['id']}")
    return row


# --------------------------------------------------------------------------------------
# ---------------------------- enclosures ----------------------------------------------
# --------------------------------------------------------------------------------------
def _check_for_unmatched_brackets(row: pd.Series) -> pd.Series:
    """A shortcoming of the EPSD data is that when I pull the transliterations,
    brackets that occur in tandem with an "n", a parenthesis, or a vertical bar
    are ommited.
    """

    # Currently the only case where this happens...
    if row["id"] == "P343022":
        row[KEY] = row[KEY].replace(" [x x x\n", f"{MISSING}\n")

    for line in row[KEY].split("\n"):
        # Get rid of everything except brackets
        bracket_seq = "".join([c for c in line if c in "[]"])
        # Get rid of all pairs of brackets
        while True:
            bracket_seq = bracket_seq.replace("[]", "")
            if "[]" not in bracket_seq:
                break
        if bracket_seq:
            print("!!! Uncaught in: ", row["id"])
            print(">> ", line)
            print()
        return row

    return row


def _fix_enclosure_order(row: pd.Series) -> pd.Series:
    # Note: only allowing x, space, and hyphen characters in the first case
    # because double parens can really mess things up

    text = row[KEY]

    # Case 1: ([...)...] -> [(...)...]
    matches = re.findall(
        r"(\(\["  # ([
        + r"[\-\ x]*?"  # any character except: \n ) ]
        + r"\)"  # )
        + r"[\-\ x]*?"  # any character except: \n ) ]
        + r"\])",  # ]
        text,
    )
    for match in matches:
        after = match.replace("([", "[(")
        print(f">> 1. {match} -> {after}")
        text = text.replace(match, after)

    # Case 2: [...(...]) -> [...(...)]
    matches = re.findall(
        r"(\["  # [
        + r"[^\n(\]]*?"  # any character except: \n ( ]
        + r"\("  # (
        + r"[^\n)\]]*?"  # any character except: \n ) ]
        + r"\]\))",  # ]
        text,
    )
    for match in matches:
        after = match.replace("])", ")]")
        print(f">> 2. {match} -> {after}")
        text = text.replace(match, after)

    # Case 3: {[...}...] -> [{...}...]
    matches = re.findall(
        r"(\{\["  # {[
        + r"[^\n}\]]*?"  # any character except: \n } ]
        + r"\}"  # }
        + r"[^\n\]]*?"  # any character except: \n ]
        + r"\])",  # closing bracket
        text,
    )
    for match in matches:
        after = match.replace("{[", "[{")
        print(f">> 3. {match} -> {after}")
        text = text.replace(match, after)

    # Case 4: [...{...]} -> [...{...}]
    matches = re.findall(
        r"(\["  # [
        + r"[^\n{\]]*?"  # any character except: \n { ]
        + r"\{"  # {
        + r"[^\n\]]*?"  # any character except: \n ]
        + r"\]\})",  # }]
        text,
    )
    for match in matches:
        after = match.replace("]}", "}]")
        print(f">> 4. {match} -> {after}")
        text = text.replace(match, after)

    # Case 5: <...{...>} -> <...{...}>
    matches = re.findall(
        r"(\<"  # <
        + r"[^\n{\>]*?"  # any character except: \n { >
        + r"\{"  # {
        + r"[^\n}\>]*?"  # any character except: \n } >
        + r"\>\})",  # >}
        text,
    )
    for match in matches:
        after = match.replace(">}", "}>")
        print(f">> 5. {match} -> {after}")
        text = text.replace(match, after)

    # Case 6: {<...}...> -> <{...}...>
    matches = re.findall(
        r"(\{\<" + r"[^\n\}\>]*?" + r"\})",
        text,
    )
    for match in matches:
        after = match.replace("{<", "<{")
        print(f">> 6. {match} -> {after}")
        text = text.replace(match, after)

    if row["id"] == "P324221":
        text = text.replace("[ma-da za-ab-ša-li{<ki]>}", "[ma-da za-ab-ša-li<{ki}>]")

    row[KEY] = text
    return row


# --------------------------------------------------------------------------------------
# -------------------------- other elements --------------------------------------------
# --------------------------------------------------------------------------------------
def _single_angle_brackets(row: pd.Series) -> pd.Series:
    """
    'The graphemes must be supplied for the sense but are not present.'
    From: https://oracc.museum.upenn.edu/doc/help/editinginatf/primer/inlinetutorial/index.html

    Get rid of 'em.
    """
    text = row[KEY]

    # Normal case
    text = re.sub(r"<[^\n]*?>", "", text)
    # Unmatched opening: <abc\n. Get rid of rest of line
    text = re.sub(r"(<[^\n>]*?(\n|$))", f"{MISSING}\n", text)
    # Unmatched closing: \n abc>. Get rid of start of line
    text = re.sub(r"((\n|^)[^\n<]*?>)", f"\n{MISSING}", text)

    row[KEY] = text
    return row


def _semicolons(row: pd.Series) -> pd.Series:
    """Semicolons are used to separate lines in the transliteration."""
    row[KEY] = row[KEY].replace(";", "\n")
    return row


def _single_curly_braces(row: pd.Series) -> pd.Series:
    """
    'Determinatives include semantic and phonetic modifiers,
     which may be single graphemes or several hyphenated graphemes,
     which are part of the current word.

     Determinatives are enclosed in single brackets {...};
     semantic determinatives require no special marking,
     but phonetic glosses and determinatives should be indicated by adding
     a plus sign (+) immediately after the opening brace, e.g., AN{+e}.

     Multiple separate determinatives must be enclosed in their own brackets,
     but a single determinative may consist of more than one sign
     (as is the case with Early Dynastic pronunciation glosses).'
    From: https://oracc.museum.upenn.edu/doc/help/editinginatf/primer/inlinetutorial/index.html
    """
    # TODO: needed?
    row[KEY] = row[KEY].replace("{-", "{")
    row[KEY] = row[KEY].replace("-}", "}")
    return row


def _vertical_bars(row: pd.Series) -> pd.Series:
    # Add hyphen after vertical bars
    matches = re.findall(r"(\|[^|a-z]*?\|)", row[KEY])
    for match in matches:
        if "-" in match:
            print(f"!!! Uncaught hyphen in vertical bars: {match} ({row['id']})")
            match = match.replace("-", "")
        after = match + "-"
        row[KEY] = row[KEY].replace(match, after)
        print(f">> {match} -> {after} ({row['id']})")
    return row


def _parentheses(row: pd.Series) -> pd.Series:
    text = row[KEY]
    # -) -> )-
    text = re.sub(r"\-+\)", ")-", text)
    # Insert a hyphen after each closing parenthesis if the next character is not whitespace
    # (abc)def -> (abc)-def
    text = re.sub(r"\)([a-zA-Z])", r")-\1", text)
    # (- -> (
    text = text.replace("(-", "(")
    row[KEY] = text
    return row


DISALLOWED_2 = ["<", ">", "(-", "-)", "{-", "-}"]


def _sanity_check_2(row: pd.Series) -> pd.Series:
    """Characters that should not be present at this point"""
    for char in DISALLOWED_2:
        if char in row[KEY]:
            print(f"!!! Disallowed character {char} in: {row['id']}")
    return row


# --------------------------------------------------------------------------------------
# ----------------------------- MISSING ------------------------------------------------
# --------------------------------------------------------------------------------------
def _single_square_brackets(row: pd.Series) -> pd.Series:
    """
    [abc def] is conjecture on what has been broken away.
    Convert to SpecialToken.MISSING
    """
    # [abc def] -> <MISSING>
    row[KEY] = re.sub(r"\[[^\[\]\n]*?\]", MISSING, row[KEY])
    # Do it twice because of nested brackets
    row[KEY] = re.sub(r"\[[^\[\]\n]*?\]", MISSING, row[KEY])

    # we made sure there were no unmatched brackets eariler,
    # but then converted semicolons to newlines

    # abc [def..\n -> abc <MISSING>\n
    row[KEY] = re.sub(r"\[[^\[\]\n]*?\n", f"{MISSING}\n", row[KEY])
    # \n ...abc] def -> \n<MISSING> def
    row[KEY] = re.sub(r"\n[^\[\]\n]*?\]", f"\n{MISSING}", row[KEY])
    return row


def _x_o_n(row: pd.Series) -> pd.Series:
    """
    Both "x" and "o" are used to indicate missing text.
    Convert sequences to SpecialToken.MISSING.

    "n" on its own means that the quantity cannot be determined.
    """
    row[KEY] = re.sub(r"([\ \-\n])([xXnNo])(?=[\ \-\n]|$)", r"\1" + MISSING, row[KEY])

    for char in ["x", "o", "n", "X", "O", "N"]:
        row[KEY] = row[KEY].replace(f"({char})", MISSING)
        row[KEY] = row[KEY].replace(f"[{char}]", MISSING)
        row[KEY] = row[KEY].replace(f"({char})", MISSING)
        row[KEY] = row[KEY].replace(f"[{char}]", MISSING)
        row[KEY] = row[KEY].replace(f"-{char}-", f" {MISSING} ")
        row[KEY] = row[KEY].replace(f" {char}-", f" {MISSING} ")
        row[KEY] = row[KEY].replace(f"-{char} ", f" {MISSING} ")
        row[KEY] = row[KEY].replace(f" {char} ", f" {MISSING} ")
        row[KEY] = row[KEY].replace(f"\n{char} ", f"\n{MISSING} ")
        row[KEY] = row[KEY].replace(f" {char}\n", f" {MISSING}\n")
        row[KEY] = row[KEY].replace(rf" {char}$", MISSING)
        row[KEY] = row[KEY].replace(rf"-{char}$", MISSING)
        row[KEY] = row[KEY].replace(rf"{MISSING}{char} ", MISSING)
        row[KEY] = row[KEY].replace(rf"{MISSING}{char}-", MISSING)
        row[KEY] = row[KEY].replace(rf" {char}{MISSING}", MISSING)
        row[KEY] = row[KEY].replace(rf"-{char}{MISSING}", MISSING)

    if row["id"] == "P010855":
        row[KEY] = row[KEY].replace("x:ur", f"ur{MISSING}")
    if row["id"] == "P278368":
        row[KEY] = row[KEY].replace("-x/EREN", MISSING)
    if row["id"] == "P323466":
        row[KEY] = row[KEY].replace("|3xAN|", "|AN.AN.AN|")
    if row["id"] == "P467714":
        row[KEY] = row[KEY].replace("x)", MISSING + ")")

    return row


def _dollar_signs(row: pd.Series) -> pd.Series:
    """
    $erasure$ or $ traces $ -> SpecialToken.MISSING

    The other instances precede a sign name to indicate that the reading is uncertain.
    Since we will take the presence of a sign name to mean that the reading is uncertain,
    we can remove the $ signs and treat the text as normal.
    e.g. $AN -> AN
    """

    for str_ in [
        "$ traces $",
        "($erasure$)",
        "$erasure$",
        "$AN",
        "$MU",
        "$UŠ",
        "$KID",
        "$DI",
        "$GA₂",
        "$HAR",
    ]:
        row[KEY] = row[KEY].replace(str_, MISSING)
    if "$" in row[KEY]:
        print(f"!!! Uncaught $ in {row['id']}")
    return row


def _ellipses(row: pd.Series) -> pd.Series:
    row[KEY] = row[KEY].replace("...", MISSING)
    return row


def _standalone_parens(row: pd.Series) -> pd.Series:
    """
    'The enclosed graphemes may be present but this is not certain;
    normally used within [...] as in [x (x) x].'

    https://oracc.museum.upenn.edu/doc/help/editinginatf/primer/inlinetutorial/index.html
    """
    matches = re.findall(r"(?:^|\n|\ |\-)(\([^\n\)]+\))(?:$|\n|\ |\-)", row[KEY])
    for match in matches:
        print(">> ", match, f" ({row['id']})")
        row[KEY] = row[KEY].replace(match, "")
    return row


DISALLOWED_3 = ["[", "]", "$", "..."]


def _sanity_check_3(row: pd.Series) -> pd.Series:
    """Characters that should not be present at this point"""
    for char in DISALLOWED_3:
        if char in row[KEY]:
            print(f"!!! Disallowed character {char} in: {row['id']}")
    return row


# --------------------------------------------------------------------------------------
# ---------------------------- enclosures ----------------------------------------------
# --------------------------------------------------------------------------------------
def _missing_alone_in_enclosure(row: pd.Series) -> pd.Series:
    patterns = [
        # Alone in parens
        r"(\(" + r"[\ \-]*" + MISSING + r"[\ \-]*" + r"\))",
        # Alone in brackets
        r"(\{" + r"[\ \-]*" + MISSING + r"[\ \-]*" + r"\})",
    ]
    for pattern in patterns:
        row[KEY] = re.sub(
            pattern,
            MISSING,
            row[KEY],
        )

    return row


def _empty_enclosures(row: pd.Series) -> pd.Series:
    row[KEY] = row[KEY].replace("{}", "")
    row[KEY] = row[KEY].replace("()", "")
    return row


# --------------------------------------------------------------------------------------
# ---------------------------- final cleanup -------------------------------------------
# --------------------------------------------------------------------------------------
DISALLOWED_FINAL = (
    DISALLOWED_1
    + DISALLOWED_2
    + DISALLOWED_3
    + [" {MISSING}", f"{MISSING} ", "\n ", " \n", "  "]
)


def _sanity_check_final(row: pd.Series) -> pd.Series:
    """Check for characters that should not be present at this point."""
    for char in DISALLOWED_FINAL:
        if char in row[KEY]:
            print(f"Disallowed character {char} in: {row['id']}")

    return row


def _convert_special_tokens(row: pd.Series) -> pd.Series:
    text = row[KEY]
    text = text.replace(
        SpecialTokensBefore.MISSING.value, SpecialTokensAfter.MISSING.value
    )
    text = text.replace(
        SpecialTokensBefore.SURFACE.value, SpecialTokensAfter.SURFACE.value
    )
    text = text.replace(
        SpecialTokensBefore.COLUMN.value, SpecialTokensAfter.COLUMN.value
    )
    text = text.replace(
        SpecialTokensBefore.BLANK_SPACE.value, SpecialTokensAfter.BLANK_SPACE.value
    )
    text = text.replace(
        SpecialTokensBefore.RULING.value, SpecialTokensAfter.RULING.value
    )
    text = text.replace(
        SpecialTokensBefore.NEWLINE.value, SpecialTokensAfter.NEWLINE.value
    )

    row[KEY] = text
    return row


# --------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------


def _remove_tablets_with_no_transliteration(df: pd.DataFrame) -> pd.DataFrame:
    # Filter out tablets where transliteration without special tokens is empty
    print(
        "Filtering out tablets with empty transliterations (beside special tokens)..."
    )
    print(f"Initial number of tablets: {len(df)}")

    special_tokens = [token.value for token in SpecialTokensAfter]

    def _without_special_tokens(x: str) -> str:
        for token in special_tokens:
            x = x.replace(token, "")
        return x

    df = df[df[KEY].apply(_without_special_tokens) != ""]
    print(f"Updated number of tablets: {len(df)}")
    return df


# =============================================================================
# =============================================================================

if __name__ == "__main__":
    main()
