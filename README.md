
# SumTablets: A Transliteration Dataset of Sumerian Tablets

[![huggingface](https://img.shields.io/badge/🤗%20Hugging%20Face-Dataset-yellow)](https://huggingface.co/datasets/colesimmons/sumtablets) ![Version](https://img.shields.io/badge/version-1-blue) [![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

## Table of Contents
- [Dataset information](#dataset)
- [Publication](#publication)
- [Description](#description)
- [Acknowledgements](#acknowledgements)
- [Versioning](#versioning)
- [Contributing](#contributing)
- [Code structure](#code-structure)
- [License](#license)
  
## Dataset
- **Name**: SumTablets
- **Version**: 1
- **Size**: 91,606 tablets (altogether containing 6,970,407 glyphs)
- **Format**: CSV
- **Fields**: `id`, `glyphs`, `transliteration`, `glyph_names`, `period`, `genre`
- **Hugging Face**: https://huggingface.co/datasets/colesimmons/sumtablets

## Publication

> **📝 Forthcoming**: To be presented at the inaugural [ML4AL Workshop](https://www.ml4al.com/), ACL 2024
> 
> **👨‍💻 Authors**: [Cole Simmons](https://github.com/colesimmons), [Richard Diehl Martinez](https://github.com/rdiehlmartinez), and Prof. Dan Jurafsky

## Description
  
This repository contains the scripts and other resources used to create the [SumTablets](https://huggingface.co/datasets/colesimmons/sumtablets) dataset. Our dataset is designed for the task of Sumerian transliteration, a conventional system for rendering an interpretation of a tablet using the Latin alphabet. We build upon existing data with the aim of providing:

1. **Structure**. The transliterations provided by other projects are heavily annotated for a variety of symbolic search and analysis tasks. However, to be best suited for use with modern language models, it is best to strip this away so that the resulting transliteration best represents just what is present on a tablet. Moreover, given a transliteration, it is not obvious how to use it for any interesting task. So to that end, we use dictionaries to map each reading back into its corresponding cuneiform glyph, represented in Unicode. The result is a set of parallel examples, designed for modeling transliteration as a sequence-to-sequence task.

2. **Accessibility**. How can we make it as easy as possible for people to contribute to this problem? By designing/structuring the dataset for this task, we aim to take care of all of the data sourcing and preprocessing steps as a barrier to get started training models. By publishing on Hugging Face, we aim to make the dataset discoverable.
   
3. **Reproducibility**. There are two factors that govern the end state of a dataset: (1) the source data and (2) the steps taken during preprocessing. To ensure the reproducibility of any experiments built on top of this data, we intend to use versioning to reflect when either of these change. See more in the [Versioning](#versioning) section below.

## Acknowledgements

For nearly thirty years, Assyriologists have been manually typing and publishing transliterations online. These efforts began in 1996 with the [Electronic Text Corpus of Sumerian Literature](https://etcsl.orinst.ox.ac.uk/#), which became archival in 2006. It was soon followed by the [Cuneiform Digital Library Initiative (CDLI)](https://cdli.mpiwg-berlin.mpg.de/), the [Open Richly Annotated Cuneiform Corpus (Oracc)](https://oracc.museum.upenn.edu/), and others. Our work in particular pulls from the [Electronic Pennsylvania Sumerian Dictionary (ePSD2)](https://oracc.museum.upenn.edu/epsd2/index.html), which aggregates data from across the various Oracc projects. These projects have embraced the collaborative spirit and freely shared their data with each other and with the public.

This dataset is only possible thanks to the hard work and generosity of contributors to all of these projects. To continue the tradition, we release this dataset with a CC-BY license.

## Versioning

As noted above, we will use versioning to ensure that experiments based on these data are reproducible. We will use a simple incrementing integer system starting at `1`. Subsequent pushes to Hugging Face will be associated with a release here and an archive of the ePSD2 data used.

## Contributing

Contributions to improve the dataset are welcome! If there are any questions or issues, please file an issue in this repo. To submit changes to the code, please:

1. Fork the repository
2. Create a new branch (`git checkout -b fix/MyFix`)
3. Make your changes
4. Commit your changes (`git commit -m 'fix some really silly choices'`)
5. Push to the branch (`git push origin fix/MyFix`)
6. Open a Pull Request



## Code structure

We use [Poetry](https://python-poetry.org/) for dependency management. After installing Poetry, you can install dependencies by running `poetry install` and then run scripts by running `poetry run python src/scripts/<script_name>.py`.

All project code lives in the `src/` directory.

`src/models/` contains all of the Pydantic models used to parse and validate the ePSD2 JSON.

`src/scripts/` contains the scripts and notebooks used to transform the ePSD2 data into the final dataset.

> Note: I am currently in the process of turning the scripts into Jupyter notebooks for better documentation and reproducibility. In the meantime, the descriptions of the steps below is still directionally correct, even if the filenames are not.

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
* * `<RULING>`
* `<unk>`
* `...`
* `\n`

## License
This project is licensed under the Creative Commons Attribution 4.0 International. [See here](https://creativecommons.org/licenses/by/4.0/) for more information.
