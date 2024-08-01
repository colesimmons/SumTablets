"""
This module defines the Corpus class, which represents a corpus of texts.

The Corpus class provides methods for loading a corpus from a given path,
retrieving unique values for specific fields, and summarizing the properties of the corpus.

Example usage:
    corpus = Corpus.load(CorpusType.ADMIN_ED3A, "/path/to/corpus")
    unique_values = corpus.get_unique_values({"field1", "field2"})
    summary = corpus.summarize_corpus_properties()


    # catalogue.json # TODO
        # Very useful!

        # corpus.json
        # Not really useful. Just tells you what files are in corpusjson.

        # gloss-qpn.json
        # QPN: Oracc Linguistic Annotation for Proper Nouns
        # http://oracc.museum.upenn.edu/doc/help/languages/propernouns/index.html

        # gloss-sux.json
        # SUX: Oracc Linguistic Annotation for Sumerian
        # http://oracc.museum.upenn.edu/doc/help/languages/sumerian/index.html

        # "The index-xxx.json files are exports of a subset of the index data created and used by the Oracc search engine,
        # giving the keys the indexer has generated from the input words and the locations in which they occur in the corpus."
        # http://oracc.museum.upenn.edu/doc/opendata/json/index.html
        # index-cat.json
        # index-lem.json
        # index-qpn.json
        # index-sux.json
        # index-tra.json
        # index-txt.json

        # Tells you what formats are available
        # metadata.json
        # sortcodes.json

"""

from enum import Enum
from typing import Dict, Generic, List, Set, Type, TypeVar, Union

from pydantic import BaseModel

from src.models.text import Text

TextT = TypeVar("TextT")  # , bound=Text) TODO


class CorpusBase(BaseModel, Generic[TextT]):
    """
    Represents a corpus of texts.

    Attributes:
        texts (List[CorpusText]): A list of CorpusText objects representing the texts in the corpus.
    """

    texts: List[TextT] = []

    def load(self, texts: List[dict]):
        self.texts = [TextT(**text) for text in texts]

    def get_unique_values(self, whitelist) -> Dict[str, Set[str]]:
        """
        Useful for getting a list of all the unique values for a given field or fields.

        Args:
            whitelist (Set[str]): A set of field names to include in the unique values.

        Returns:
            Dict[str, Set[str]]: A dictionary where the keys are field names and the values are sets of unique values for each field.
        """
        unique_values = {}
        for text in self.texts:
            for field in text.model_fields:
                if field not in whitelist:
                    continue
                if field not in unique_values:
                    unique_values[field] = set()
                unique_values[field].add(getattr(text, field))
        return unique_values

    def summarize_corpus_properties(self):
        """Summarizes the properties of the corpus.

        Returns:
            dict: A dictionary where the key is the property name and the value is the percentage of texts that have a non-empty value for that property.
        """
        num_texts = len(self.texts)

        # Dict where key is property name and
        # value is number of texts that have a non-empty value for that property
        property_counts = {}
        for text in self.texts:
            for field in text.model_fields:
                if field not in property_counts:
                    property_counts[field] = 0

                value = getattr(text, field)
                if len(value):
                    property_counts[field] += 1

        # Now format it a percentage of the overall number of texts
        for property_name, count in property_counts.items():
            property_counts[property_name] = (count / num_texts) * 100

        return property_counts


class Corpus:
    class AdminEd1and2(CorpusBase[Text.AdminEd1and2]):
        pass

    class AdminEd3a(CorpusBase[Text.AdminEd3a]):
        pass

    class AdminEd3b(CorpusBase[Text.AdminEd3b]):
        pass

    class AdminOldAkk(CorpusBase[Text.AdminOldAkk]):
        pass

    class AdminLagash2(CorpusBase[Text.AdminLagash2]):
        pass

    class AdminUr3(CorpusBase[Text.AdminUr3]):
        pass

    class LiteraryEarly(CorpusBase[Text.LiteraryEarly]):
        pass

    class LiteraryOldBab(CorpusBase[Text.LiteraryOldBab]):
        pass

    class Incantations(CorpusBase[Text.Incantations]):
        pass

    class Liturgies(CorpusBase[Text.Liturgies]):
        pass

    class Royal(CorpusBase[Text.Royal]):
        pass

    class Udughul(CorpusBase[Text.Udughul]):
        pass

    class Varia(CorpusBase[Text.Varia]):
        pass


CorpusType = Union[
    Corpus.AdminEd1and2,
    Corpus.AdminEd3a,
    Corpus.AdminEd3b,
    Corpus.AdminOldAkk,
    Corpus.AdminLagash2,
    Corpus.AdminUr3,
    Corpus.LiteraryEarly,
    Corpus.LiteraryOldBab,
    Corpus.Incantations,
    Corpus.Liturgies,
    Corpus.Royal,
    Corpus.Udughul,
    Corpus.Varia,
]


class CorpusEnum(str, Enum):
    """
    Enum representing the available corpora.

    http://oracc.museum.upenn.edu/epsd2/json/
    """

    # Early Dynastic I-II
    ADMIN_ED_1_2 = "admin_ed12"

    # Early Dynastic IIIa
    ADMIN_ED_3A = "admin_ed3a"

    # Early Dynastic IIIb
    ADMIN_ED_3B = "admin_ed3b"

    # Old Akkadian
    ADMIN_OAKK = "admin_oakk"

    # Second Dynasty of Lagaš
    ADMIN_LAGASH2 = "admin_lagash2"

    # Third Dynasty of Ur
    ADMIN_UR3 = "admin_ur3"

    # Old Babylonian
    # ADMIN_OLDBAB = "admin_oldbab"

    # ------------------------
    # Other
    # ------------------------
    # pre-OB
    LITERARY_EARLY = "early_lit"

    # Old Babylonian
    LITERARY_OLDBAB = "oldbab_lit"

    # Other
    ROYAL = "royal"
    INCANTATIONS = "incantations"
    LITURGIES = "liturgies"
    UDUGHUL = "udughul"
    PRACTICAL_VARIA = "varia"

    @classmethod
    def list(cls) -> List[str]:
        return [member.value for member in cls]

    @property
    def url(self) -> str:
        """
        Returns the download URL for the given corpus.

        Defined at: http://oracc.museum.upenn.edu/epsd2/json/

        Raises:
          ValueError: If the corpus is invalid.
        """

        base = "http://oracc.museum.upenn.edu/json/"
        type_to_filename = {
            CorpusType.ADMIN_ED_1_2: "epsd2-admin-ed12",
            CorpusType.ADMIN_ED_3A: "epsd2-admin-ed3a",
            CorpusType.ADMIN_ED_3B: "epsd2-admin-ed3b",
            # CorpusType.ADMIN_EBLA: "epsd2-admin-ebla",
            CorpusType.ADMIN_OAKK: "epsd2-admin-oakk",
            CorpusType.ADMIN_LAGASH2: "epsd2-admin-lagash2",
            CorpusType.ADMIN_UR3: "epsd2-admin-ur3",
            # CorpusType.ADMIN_OLDBAB: "epsd2-admin/oldbab",
            CorpusType.LITERARY_EARLY: "epsd2-earlylit",
            CorpusType.LITERARY_OLDBAB: "epsd2-literary",
            CorpusType.ROYAL: "epsd2-royal",
            CorpusType.INCANTATIONS: "epsd2-praxis",
            CorpusType.UDUGHUL: "epsd2-praxis-udughul",
            CorpusType.LITURGIES: "epsd2-praxis-liturgy",
            CorpusType.PRACTICAL_VARIA: "epsd2-praxis-varia",
        }
        if self in type_to_filename:
            return f"{base}{type_to_filename[self]}.zip"
        raise ValueError("Invalid corpus")

    @property
    def model(self) -> Type[CorpusBase]:
        return {
            CorpusEnum.ADMIN_ED_1_2: Corpus.AdminEd1and2,
            CorpusEnum.ADMIN_ED_3A: Corpus.AdminEd3a,
            CorpusEnum.ADMIN_ED_3B: Corpus.AdminEd3b,
            CorpusEnum.ADMIN_OAKK: Corpus.AdminOldAkk,
            CorpusEnum.ADMIN_LAGASH2: Corpus.AdminLagash2,
            CorpusEnum.ADMIN_UR3: Corpus.AdminUr3,
            CorpusEnum.LITERARY_EARLY: Corpus.LiteraryEarly,
            CorpusEnum.LITERARY_OLDBAB: Corpus.LiteraryOldBab,
            CorpusEnum.ROYAL: Corpus.Royal,
            CorpusEnum.INCANTATIONS: Corpus.Incantations,
            CorpusEnum.LITURGIES: Corpus.Liturgies,
            CorpusEnum.UDUGHUL: Corpus.Udughul,
            CorpusEnum.PRACTICAL_VARIA: Corpus.Varia,
        }[self]


__all__ = [
    "Corpus",
    "CorpusType",
    "CorpusEnum",
]
