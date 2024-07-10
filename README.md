(Work in progress. More documentation coming soon.)

Scripts to acquire transliterations from [ePSD2](https://oracc.museum.upenn.edu/epsd2),
reverse-engineer the corresponding glyph names and Unicode glyphs,
and output a single CSV where the columns are
`id | transliteration | glyph_names | glyphs | period | genre`
and each row represents a tablet.

Scripts should be run from this path.

## Steps

#### (1) Download the ePSD2 json

`poetry run python 1_download_corpora.py`

* Downloads (or loads from `.corpusjson/`) the ePSD2 JSON files for each corpus
* For each corpus:
  * Loads `catalogue.json`, which gives metadata for each tablet.
  * For each tablet in the catalogue, loads the corresponding JSON file which contains its transliteration.
  * Creates a DataFrame where each row is a tablet.
    * Columns vary depending on the data provided for the corpus (this data is an aggregate of different projects with different aims)
  * Saves the DataFrame to a CSV in `./outputs/1_{corpus}.csv`
 
This section makes use of my [Sumeripy](https://github.com/colesimmons/sumeripy) library, which uses Pydantic models to parse and validate the JSON.

**Reproducibility**: The ePSD2 data is liable to be modified or made unavailable in the future.
I have preserved the version of the data used in my experiments [here](https://drive.google.com/file/d/1gCubNGMb9_R0QcCyl4JwVAd5b-YKjL2Z/view?usp=drive_link).
Unzipping it in this directory should create `.corpusdata/`. The script above will detect/use this data rather than redownloading.


#### (2) Collate corpora

`poetry run python 2_collate_tablets.py`

* Loads each corpus CSV file from `./outputs/1_{corpus}.csv`
* Concats them into a single DataFrame (inner join, so only common columns)
  * 94,178 rows
* Drops tablets that have non-Sumerian text
  * -> 93,615 rows
* Drops rows without transliterations
  * -> 92,908 rows
* Drops duplicate IDs (tablets that were included in multiple corpora)
  * -> 92,864 rows
* Drops all columns except `id | transliteration | period | genre`
* Standardizes period and genre names
  * e.g. collapse periods `Lexical; School` and `Lexical` into just `Lexical`
* Saves result to `./outputs/2_tablets.csv`


#### (3) Clean up transliterations

`poetry run python 3_clean_up_transliterations.py`

* Loads `./outputs/2_tablets.csv`
* Cleans/standardizes transliterations
  * Removes, to the greatest extent possible, editorialization. For example, when a section is broken away, a transliteration may include a suggestion for what was probably in that space by placing it in brackets, e.g. "[lugal\] kur-kur-ra". We want to get rid of that, as the aim is to create a dataset that best reflects what is present on the tablets.
* Drops tablets with identical transliterations
  * -> 92,831 rows
* Saves result to `./outputs/3_cleaned_transliterations.csv`
  * New column `transliteration_clean` (original transliteration kept for easy comparison)


#### (4) Create lookups

`poetry run python 4_create_lookups.py`

* Uses the Oracc Sign List and the ePSD2 sign lists to create lookups that will help us turn transliterations into parallel glyph sets
* Creates file `./outputs/morpheme_to_glyph_names.json` (str -> list[str])
  * Maps from an individual reading to all of the potential glyph names that could have represented it
* Creates file `./outputs/glyph_name_to_glyph.json` (str -> str)
  * Maps from a glyph name to the corresponding Unicode

**Reproducibility**: This script relies on Oracc Sign List data `osl.json`, which is liable to be modified or made unavailable in the future.
I have preserved the version of the data used in my experiments [here](https://drive.google.com/file/d/1qArSHeGsCHc3Fq6gdZiBLIvvObB5cIrU/view?usp=drive_link).


#### (5) Add glyphs

`poetry run python 5_add_glyphs.py`

* Loads `3_cleaned_transliterations.csv` and the lookup files from the previous step
* Find glyph names for each reading
  * Num morphemes unable to convert: 4,922 (0.07%)
  * Num morphemes successfully converted: 6,724,498 (99.93%)
* Find Unicode for each glyph name
  * Num names unable to convert: 2,975 (0.04%)
  * Num names successfully converted: 6,638,081 (99.96%)
* Drops rows with identical transliterations:
   * -> 91,667 rows
* Drops rows with identical glyphs:
   * -> 91,606 rows (6,970,407 total glyphs)
* Saves to `5_with_glyphs.csv` (columns=id|transliteration|glyph_names|glyphs|period|genre)


#### (6) Split

`poetry run python 6_split.py`

* Split 95%/5%/5% train/val/test
* Exclude Lexical tablets from val and test


### Special tokens
* `<SURFACE>`
* `<COLUMN>`
* `<BLANK_SPACE>`
* `<RULING>`
* `<unk>`
* `...`
* `\n`
