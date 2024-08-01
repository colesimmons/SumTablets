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
from typing import Dict, Generic, List, Set, TypeVar, Union

from pydantic import BaseModel

from src.models.text import Text

TextT = TypeVar("TextT")


class _Base(BaseModel, Generic[TextT]):
    """
    Represents a corpus of texts.

    Attributes:
        texts (List[CorpusText]): A list of CorpusText objects representing the texts in the corpus.
    """

    texts: List[TextT] = []

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
    class CorpusAdminEd1and2(_Base[Text.AdminEd1and2]):
        pass

    class CorpusAdminEd3a(_Base[Text.AdminEd3a]):
        pass

    class CorpusAdminEd3b(_Base[Text.AdminEd3b]):
        pass

    class CorpusAdminOldAkk(_Base[Text.AdminOldAkk]):
        pass

    class CorpusAdminLagash2(_Base[Text.AdminLagash2]):
        pass

    class CorpusAdminUr3(_Base[Text.AdminUr3]):
        pass

    class CorpusLiteraryEarly(_Base[Text.LiteraryEarly]):
        pass

    class CorpusLiteraryOldBab(_Base[Text.LiteraryOldBab]):
        pass

    class CorpusIncantations(_Base[Text.Incantations]):
        pass

    class CorpusLiturgies(_Base[Text.Liturgies]):
        pass

    class CorpusRoyal(_Base[Text.Royal]):
        pass

    class CorpusUdughul(_Base[Text.Udughul]):
        pass

    class CorpusVaria(_Base[Text.Varia]):
        pass


CorpusType = Union[
    Corpus.CorpusAdminEd1and2,
    Corpus.CorpusAdminEd3a,
    Corpus.CorpusAdminEd3b,
    Corpus.CorpusAdminOldAkk,
    Corpus.CorpusAdminLagash2,
    Corpus.CorpusAdminUr3,
    Corpus.CorpusLiteraryEarly,
    Corpus.CorpusLiteraryOldBab,
    Corpus.CorpusIncantations,
    Corpus.CorpusLiturgies,
    Corpus.CorpusRoyal,
    Corpus.CorpusUdughul,
    Corpus.CorpusVaria,
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
            CorpusEnum.ADMIN_ED_1_2: "epsd2-admin-ed12",
            CorpusEnum.ADMIN_ED_3A: "epsd2-admin-ed3a",
            CorpusEnum.ADMIN_ED_3B: "epsd2-admin-ed3b",
            # CorpusType.ADMIN_EBLA: "epsd2-admin-ebla",
            CorpusEnum.ADMIN_OAKK: "epsd2-admin-oakk",
            CorpusEnum.ADMIN_LAGASH2: "epsd2-admin-lagash2",
            CorpusEnum.ADMIN_UR3: "epsd2-admin-ur3",
            # CorpusType.ADMIN_OLDBAB: "epsd2-admin/oldbab",
            CorpusEnum.LITERARY_EARLY: "epsd2-earlylit",
            CorpusEnum.LITERARY_OLDBAB: "epsd2-literary",
            CorpusEnum.ROYAL: "epsd2-royal",
            CorpusEnum.INCANTATIONS: "epsd2-praxis",
            CorpusEnum.UDUGHUL: "epsd2-praxis-udughul",
            CorpusEnum.LITURGIES: "epsd2-praxis-liturgy",
            CorpusEnum.PRACTICAL_VARIA: "epsd2-praxis-varia",
        }
        if self in type_to_filename:
            return f"{base}{type_to_filename[self]}.zip"
        raise ValueError("Invalid corpus")

    @property
    def model(self) -> CorpusType:
        return {
            CorpusEnum.ADMIN_ED_1_2: Corpus.CorpusAdminEd1and2,
            CorpusEnum.ADMIN_ED_3A: Corpus.CorpusAdminEd3a,
            CorpusEnum.ADMIN_ED_3B: Corpus.CorpusAdminEd3b,
            CorpusEnum.ADMIN_OAKK: Corpus.CorpusAdminOldAkk,
            CorpusEnum.ADMIN_LAGASH2: Corpus.CorpusAdminLagash2,
            CorpusEnum.ADMIN_UR3: Corpus.CorpusAdminUr3,
            CorpusEnum.LITERARY_EARLY: Corpus.CorpusLiteraryEarly,
            CorpusEnum.LITERARY_OLDBAB: Corpus.CorpusLiteraryOldBab,
            CorpusEnum.ROYAL: Corpus.CorpusRoyal,
            CorpusEnum.INCANTATIONS: Corpus.CorpusIncantations,
            CorpusEnum.LITURGIES: Corpus.CorpusLiturgies,
            CorpusEnum.UDUGHUL: Corpus.CorpusUdughul,
            CorpusEnum.PRACTICAL_VARIA: Corpus.CorpusVaria,
        }[self]


__all__ = [
    "Corpus",
    "CorpusType",
    "CorpusEnum",
]
