"""
Genre: Enum class representing the genre of a text.
Language: Enum class representing the language of a text.
ObjectType: Enum class representing the type of object that a text appears upon.
Period: Enum class representing the period of a text.
Status: Enum class representing the status of a text.
Supergenre: Enum class representing the supergenre of a text.
XProject: Enum class representing other projects of which a text is a part.
Subgenre: Enum class representing the subgenre of a text.
"""

from enum import Enum


class Genre(str, Enum):
    """
    Enum class representing the genre of a text.
    """

    ADMINISTRATIVE = "Administrative"
    ASTRONOMICAL = "Astronomical"
    HYMN_PRAYER = "Hymn-Prayer"
    FAKE = "fake (modern)"
    LEGAL = "Legal"
    LETTER = "Letter"
    LEXICAL = "Lexical"
    LEXICAL_SCHOOL = "Lexical; School"
    LITERARY = "Literary"
    LITURGY = "Liturgy"
    MATHEMATICAL = "Mathematical"
    RITUAL = "Ritual"
    ROYAL_INSCRIPTION = "Royal Inscription"
    ROYAL_OR_MONUMENTAL = "Royal/Monumental"
    SCIENTIFIC = "Scientific"
    UNCERTAIN = "uncertain"
    UNSPECIFIED = ""


class Language(str, Enum):
    """
    Enum class representing the language of a text.
    """

    AKKADIAN = "Akkadian"
    NON_SUMERIAN_EBLAITE = "non-Sumerian (Eblaite)"
    NON_SUMERIAN_UNDET = "non-Sumerian (undetermined)"
    SUMERIAN = "Sumerian"
    SUX_AKK_BILINGUAL = "S-A bilingual"
    UNSPECIFIED = ""


class ObjectType(str, Enum):
    """
    Enum class representing the type of object that a text appears upon.
    """

    BARREL = "barrel"
    BRAND = "Brand"
    BRICK = "brick"
    BULLA = "bulla"
    BULLA_2 = "Bulla"
    BULLA_UNCERTAIN = "Bulla (?)"
    CLAY_SEALING = "Clay sealing"
    CONE = "cone"
    CYLINDER = "cylinder"
    CYLINDER_SEAL = "Cylinder Seal"
    CYLINDRICAL_TABLET = "Cylindrical tablet"
    DOOR_SEALING = "Door sealing"
    ENVELOPE_UNCERTAIN = "Envelope (?)"
    ENVELOPE_CLOSED = "Envelope - Closed"
    ENVELOPE_CLOSED_UNCERTAIN = "Envelope - Closed (?)"
    ENVELOPE_FRAGMENT = "Envelope - Fragment"
    ENVELOPE_FRAGMENT_UNCERTAIN = "Envelope - Fragment (?)"
    FAKE = "Fake"
    FAKE_UNCERTAIN = "Fake (?)"
    JAR_SEALING = "Jar sealing"
    LABEL = "Label"
    LABEL_UNCERTAIN = "Label (?)"
    OTHER = "Other"
    OTHER_SEE_REMARKS = "other (see object remarks)"
    PRISM = "prism"
    REPRODUCTION_OR_CAST = "Reproduction or cast"
    REPRODUCTION_OR_CAST_UNCERTAIN = "Reproduction or cast (?)"
    ROUND_TABLET = "Round tablet"
    SEAL = "seal (not impression)"
    SEALING = "sealing"
    TABLET = "tablet"
    TABLET_2 = "Tablet"
    TABLET_AND_ENVELOPE = "tablet & envelope"
    TABLET_AND_ENVELOPE_2 = "Tablet and envelope"
    TABLET_AND_ENVELOPE_3 = "Tablet and Envelope"
    TAG = "tag"
    UNCERTAIN = "Uncertain"
    UNSPECIFIED = ""


class Period(str, Enum):
    """
    Enum class representing the period of a text.
    """

    EARLY_DYNASTIC_I_II = "Early Dynastic I-II"
    EARLY_DYNASTIC_III_A = "Early Dynastic IIIa"
    EARLY_DYNASTIC_III_B = "Early Dynastic IIIb"
    EBLA = "Ebla"
    FAKE = "fake"
    LAGASH_II = "Lagash II"
    MIDDLE_BABYLONIAN = "Middle Babylonian"
    NEO_ASSYRIAN = "Neo-Assyrian"
    NEO_BABYLONIAN = "Neo-Babylonian"
    OLD_AKKADIAN = "Old Akkadian"
    OLD_BABYLONIAN = "Old Babylonian"
    PRE_URUK_V = "Pre-Uruk V"
    UR_III = "Ur III"
    UNCERTAIN = "Uncertain"
    UNKNOWN = "Unknown"
    UNSPECIFIED = ""


class Status(str, Enum):
    """
    Enum class representing the status of a text.
    """

    A = "A"  # TODO
    D = "D"
    I_STATUS = "I"
    UNSPECIFIED = ""


class Supergenre(str, Enum):
    """
    Enum class representing the supergenre of a text.
    """

    ELA = "ELA"  # TODO
    LEXICAL = "LEX"
    LIT = "LIT"
    STL = "STL"
    UNKNOWN = "unknown"
    UNKNOWN_2 = "UNK"
    UNSPECIFIED = ""


class XProject(str, Enum):
    """
    Enum class representing other projects of which a text is a part.
    """

    CDLI = "CDLI"
    UNSPECIFIED = ""


# TODO
class Subgenre(str, Enum):
    """
    Enum class representing the subgenre of a text.
    """

    ADMINISTRATIVE = "administrative"
    ADMINISTRATIVE_2 = "Administrative"
    ASJ = "ASJ 8, 107 27"
    BUILDING_FLOOR_PLAN = "building floor plan"
    BULLA = "bulla"
    CONTRACT = "contract"
    CONTRACT_UNCERTAIN = "contract ?"
    DITILLA = "ditilla"
    COMPOSITE = "composite"
    COMPOSITE_SEAL_ROYAL = "composite seal, royal"
    DEBATE_POEMS = "Debate poems"
    EXERCISE = "exercise"
    EXERCISE_2 = "Exercise"
    FIELD_PLAN = "field plan (drawing)"
    JUDGEMENT = "judgement"
    GABA_RI = "gaba-ri"
    HYMNS_TO_DEITIES = "Hymns addressed to deities//Inana"
    HOUSE_PURCHASE = "house purchase"
    LEGAL_DOCUMENT = "Legal document"
    LEGAL_DOCUMENT_ORDAL = 'Legal document: ""Ordal'
    LEGAL_DOCUMENT_GUARANTEE = "Legal document: guarantee"
    LEGAL_DOCUMENT_PURCHASE = "Legal document: purchase"
    LEGAL_DOCUMENT_UNCERTAIN = "Legal document?"
    LETTER_ORDER = "letter order"
    LIST_OF_OFFERINGS = "List of offerings"
    LIST_OF_OFFERINGS_UNCERTAIN = "List of offerings?"
    LOAN = "Loan"
    LOAN_2 = "loan"
    MAEKAWA = "Maekawa, ASJ 17, 184, no. 108"
    MESSENGER = "messenger"
    MESSENGER_TEXT = "messenger text"
    MESSENGER_TEXT_2 = "Messenger text"
    MESSENGER_TEXT_W_GABA_RI = "messenger text w/ gaba-ri"
    METRO_MATHEMATICAL = "metro-mathematical"
    MODEL_CONTRACTS = "model contracts"
    OTHER_LETTERS = "Other letters and letter-prayers"
    PHYSICAL_CYLINDER_SEAL = "physical cylinder seal"
    PHYSICAL_SEAL_ROYAL = "physical seal, royal"
    PISAN_DUB = "pisan-dub"
    PISAN_DUB_BA = "pisan-dub-ba"
    PISAN_DUB_BA_W_GABA_RI = "pisan-dub-ba w/ gaba-ri"
    PROVERB_COLLECTIONS = "Proverb collections"
    SALE_CONTRACT = "sale contract"
    SALE_CONTRACT_FIELD = "sale contract, field"
    SALE_CONTRACT_HOUSE = "sale contract, house"
    SALE_CONTRACT_UNCERTAIN = "sale contract ?"
    SIA_ARCHIVE = "SI.A-a archive"
    STRINGED_BULLA = "stringed bulla"
    SURUPPAK_LIST = "Šuruppak List of Personal Names and Professions"
    TABULAR_ACCOUNT = "tabular account"
    TRIANGLE_TAG = "triangle tag"
    UNSPECIFIED = ""
