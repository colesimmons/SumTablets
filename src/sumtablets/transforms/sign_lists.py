"""Parse Oracc Sign List (OSL) and ePSD2 sign list into morpheme↔glyph lookup dicts."""

from collections import defaultdict


def build_lookups(
    osl_data: dict,
    epsd2_sl_data: dict,
) -> tuple[dict[str, list[str]], dict[str, str]]:
    """Parse sign list dicts into morpheme→glyph_names and glyph_name→glyph mappings.

    Args:
        osl_data: Parsed contents of osl.json (the full Oracc Sign List).
        epsd2_sl_data: Parsed contents of epsd2-sl.json (the "index" key only).

    Returns:
        Tuple of:
        - morpheme_to_glyph_names: str → list[str]
        - glyph_name_to_glyph: str → str (single Unicode char or empty)
    """
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
    for letter in osl_data["sl:signlist"]["j:letters"]:
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

    # Remove empty strings from both dicts
    morpheme_to_glyph_names = {
        key: [v for v in vals if v != ""] for key, vals in morpheme_to_glyph_names.items()
    }
    glyph_name_to_glyphs = {
        key: [v for v in vals if v != ""] for key, vals in glyph_name_to_glyphs.items()
    }

    # Add epsd2_sl_data mappings to morpheme_to_glyph_names
    for k, v in epsd2_sl_data.items():
        morpheme_to_glyph_names[k] = [v]

    # Each glyph name should map to at most one unicode representation.
    # Double check, convert to a single mapping.
    for glyph_name, unicodes in glyph_name_to_glyphs.items():
        if len(unicodes) > 1:
            print(f"Glyph {glyph_name} has more than one representation: {unicodes}")
    glyph_name_to_glyph = {
        key: vals[0] if vals else "" for key, vals in glyph_name_to_glyphs.items()
    }

    return morpheme_to_glyph_names, glyph_name_to_glyph
