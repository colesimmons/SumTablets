from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# External / downloaded inputs
SOURCE_DIR = PROJECT_ROOT / "data" / "source"
EPSD2_DATA_DIR = SOURCE_DIR / "epsd2"
EPSD2_SL_PATH = SOURCE_DIR / "epsd2-sl.json"
OSL_PATH = SOURCE_DIR / "osl.json"

# Version-controlled mapping files
MAPPINGS_DIR = PROJECT_ROOT / "data" / "mappings"
GENRE_NORMALIZATION_PATH = MAPPINGS_DIR / "genre_normalization.json"
SIGN_LIST_REPLACEMENTS_PATH = MAPPINGS_DIR / "sign_list_replacements.json"
GLYPH_NAME_REPLACEMENTS_PATH = MAPPINGS_DIR / "glyph_name_replacements.json"
READING_FIXES_PATH = MAPPINGS_DIR / "reading_fixes.json"

# Pipeline outputs
GENERATED_DIR = PROJECT_ROOT / "data" / "generated"
STEP1_PREFIX = GENERATED_DIR  # 1_{corpus_name}.csv
STEP2_OUTPUT = GENERATED_DIR / "2_tablets.csv"
STEP3_OUTPUT = GENERATED_DIR / "3_cleaned_transliterations.csv"
MORPHEME_TO_GLYPH_NAMES_PATH = GENERATED_DIR / "morpheme_to_glyph_names.json"
GLYPH_NAME_TO_GLYPH_PATH = GENERATED_DIR / "glyph_name_to_glyph.json"
STEP5_OUTPUT = GENERATED_DIR / "5_with_glyphs.csv"
TRAIN_OUTPUT = GENERATED_DIR / "train.csv"
VALIDATION_OUTPUT = GENERATED_DIR / "validation.csv"
TEST_OUTPUT = GENERATED_DIR / "test.csv"

# Verify cache
CACHE_DIR = PROJECT_ROOT / "data" / "cache"
