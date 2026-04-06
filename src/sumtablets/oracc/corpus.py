from enum import Enum
from typing import Generic, List, TypeVar, Union

from pydantic import BaseModel

from sumtablets.oracc.text import (
    Text,
    TextAdminEd1and2,
    TextAdminEd3a,
    TextAdminEd3b,
    TextAdminLagash2,
    TextAdminOldAkk,
    TextAdminUr3,
    TextIncantations,
    TextLiteraryEarly,
    TextLiteraryOldBab,
    TextLiturgies,
    TextRoyal,
    TextUdughul,
    TextVaria,
)

T = TypeVar("T", bound=Text)


class CorpusBase(BaseModel, Generic[T]):
    texts: List[T] = []


# ---------------------------------------------------------------------------
# Admin corpora
# ---------------------------------------------------------------------------

class CorpusAdminEd1and2(CorpusBase[TextAdminEd1and2]):
    def load(self, texts):
        self.texts = [TextAdminEd1and2(**text) for text in texts]


class CorpusAdminEd3a(CorpusBase[TextAdminEd3a]):
    def load(self, texts):
        self.texts = [TextAdminEd3a(**text) for text in texts]


class CorpusAdminEd3b(CorpusBase[TextAdminEd3b]):
    def load(self, texts):
        self.texts = [TextAdminEd3b(**text) for text in texts]


class CorpusAdminOldAkk(CorpusBase[TextAdminOldAkk]):
    def load(self, texts):
        self.texts = [TextAdminOldAkk(**text) for text in texts]


class CorpusAdminLagash2(CorpusBase[TextAdminLagash2]):
    def load(self, texts):
        self.texts = [TextAdminLagash2(**text) for text in texts]


class CorpusAdminUr3(CorpusBase[TextAdminUr3]):
    def load(self, texts):
        self.texts = [TextAdminUr3(**text) for text in texts]


# ---------------------------------------------------------------------------
# Literary corpora
# ---------------------------------------------------------------------------

class CorpusLiteraryEarly(CorpusBase[TextLiteraryEarly]):
    def load(self, texts):
        self.texts = [TextLiteraryEarly(**text) for text in texts]


class CorpusLiteraryOldBab(CorpusBase[TextLiteraryOldBab]):
    def load(self, texts):
        self.texts = [TextLiteraryOldBab(**text) for text in texts]


# ---------------------------------------------------------------------------
# Other corpora
# ---------------------------------------------------------------------------

class CorpusIncantations(CorpusBase[TextIncantations]):
    def load(self, texts):
        self.texts = [TextIncantations(**text) for text in texts]


class CorpusLiturgies(CorpusBase[TextLiturgies]):
    def load(self, texts):
        self.texts = [TextLiturgies(**text) for text in texts]


class CorpusRoyal(CorpusBase[TextRoyal]):
    def load(self, texts):
        self.texts = [TextRoyal(**text) for text in texts]


class CorpusUdughul(CorpusBase[TextUdughul]):
    def load(self, texts):
        self.texts = [TextUdughul(**text) for text in texts]


class CorpusVaria(CorpusBase[TextVaria]):
    def load(self, texts):
        self.texts = [TextVaria(**text) for text in texts]


# ---------------------------------------------------------------------------
# CorpusType enum — maps names to download URLs and model classes
# ---------------------------------------------------------------------------

class CorpusType(str, Enum):
    ADMIN_ED_1_2 = "admin_ed12"
    ADMIN_ED_3A = "admin_ed3a"
    ADMIN_ED_3B = "admin_ed3b"
    ADMIN_OAKK = "admin_oakk"
    ADMIN_LAGASH2 = "admin_lagash2"
    ADMIN_UR3 = "admin_ur3"
    LITERARY_EARLY = "early_lit"
    LITERARY_OLDBAB = "oldbab_lit"
    ROYAL = "royal"
    INCANTATIONS = "incantations"
    LITURGIES = "liturgies"
    UDUGHUL = "udughul"
    PRACTICAL_VARIA = "varia"

    @property
    def url(self) -> str:
        base = "http://oracc.museum.upenn.edu/json/"
        type_to_filename = {
            CorpusType.ADMIN_ED_1_2: "epsd2-admin-ed12",
            CorpusType.ADMIN_ED_3A: "epsd2-admin-ed3a",
            CorpusType.ADMIN_ED_3B: "epsd2-admin-ed3b",
            CorpusType.ADMIN_OAKK: "epsd2-admin-oakk",
            CorpusType.ADMIN_LAGASH2: "epsd2-admin-lagash2",
            CorpusType.ADMIN_UR3: "epsd2-admin-ur3",
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
    def model(self):
        type_to_model = {
            CorpusType.ADMIN_ED_1_2: CorpusAdminEd1and2,
            CorpusType.ADMIN_ED_3A: CorpusAdminEd3a,
            CorpusType.ADMIN_ED_3B: CorpusAdminEd3b,
            CorpusType.ADMIN_OAKK: CorpusAdminOldAkk,
            CorpusType.ADMIN_LAGASH2: CorpusAdminLagash2,
            CorpusType.ADMIN_UR3: CorpusAdminUr3,
            CorpusType.LITERARY_EARLY: CorpusLiteraryEarly,
            CorpusType.LITERARY_OLDBAB: CorpusLiteraryOldBab,
            CorpusType.ROYAL: CorpusRoyal,
            CorpusType.INCANTATIONS: CorpusIncantations,
            CorpusType.UDUGHUL: CorpusUdughul,
            CorpusType.LITURGIES: CorpusLiturgies,
            CorpusType.PRACTICAL_VARIA: CorpusVaria,
        }
        if self in type_to_model:
            return type_to_model[self]
        raise ValueError("Invalid corpus")


# ---------------------------------------------------------------------------
# Union type
# ---------------------------------------------------------------------------

Corpus = Union[
    CorpusAdminEd1and2,
    CorpusAdminEd3a,
    CorpusAdminEd3b,
    CorpusAdminLagash2,
    CorpusAdminOldAkk,
    CorpusAdminUr3,
    CorpusLiteraryEarly,
    CorpusLiteraryOldBab,
    CorpusIncantations,
    CorpusLiturgies,
    CorpusRoyal,
    CorpusUdughul,
    CorpusVaria,
]
