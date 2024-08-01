"""
Functions:
    parse_cdl_node

Classes:
    DiscontinuityType
    Discontinuity
    ParaClass
    ParaType
    Para
    Lemma
    LLNode
    LinkbaseNode
    CDLNode
    ChunkType
    Chunk
"""

from enum import Enum
from typing import Any, Dict, List, Literal, Union

from pydantic import BaseModel, ConfigDict, Extra, Field, Tag
from typing_extensions import Annotated

# ---------------  CLASSES ---------------


# ====================
# == Discontinuity ===
# ====================
class DiscontinuityType(Enum):
    """ """

    CELL_START = "cell-start"
    CELL_END = "cell-end"
    COLUMN = "column"
    FIELD_START = "field-start"
    FIELD_END = "field-end"
    LINE_START = "line-start"
    NONW = "nonw"  # TODO ?
    NONX = "nonx"  # TODO ?
    OBJECT = "object"
    SURFACE = "surface"


class Discontinuity(BaseModel):
    """ """

    model_config = ConfigDict(extra=Extra.forbid)

    # Required
    node: Literal["d"]
    type_: DiscontinuityType = Field(..., alias="type")

    # Optional
    ref: str = Field("")
    label: str = Field("")
    n: str = Field("")
    subtype: str = Field("")
    strict: str = Field("")
    state: str = Field("")
    extent: str = Field("")
    scope: str = Field("")
    frag: str = Field("")
    lang: str = Field("")
    delim: str = Field("")
    queried: str = Field("")
    flags: str = Field("")
    o: str = Field("")


# ====================
# ====   Lemma    ====
# ====================
class ParaClass(Enum):
    """ """

    SYNTAX = "syntax"
    BOUNDARY = "boundary"
    POINTER = "pointer"


class ParaType(Enum):
    """ """

    AND = "and"
    BRACK_OPEN = "brack_o"
    BRACK_CLOSE = "brack_c"
    SENTENCE = "sentence"
    NO_SENTENCE = "no sentence"
    NO_SENTENCE_2 = "no_sentence"
    LABEL = "label"
    POINTER_REF = "pointer_ref"


class Para(BaseModel):
    """ """

    model_config = ConfigDict(extra=Extra.forbid)

    class_: ParaClass = Field(..., alias="class")
    type_: ParaType = Field(..., alias="type")
    text: str = Field(...)
    val: str = Field(...)  # empty str
    bracketing_level: str = Field(...)  # "0"


class Lemma(BaseModel):
    """ """

    model_config = ConfigDict(extra=Extra.forbid)

    # Required
    node: Literal["l"]
    id_: str = Field(..., alias="id")
    ref: str
    inst: str

    # [{'name': 'field', 'group': 'env', 'ngram': '-1', 'ref': 'P010055.4.1'}, {'name': 'discourse', 'group': 'env', 'value': 'body', 'ngram': '-1', 'ref': 'P010055.4.1'}]
    f: Dict[str, Any]  # TODO

    # [{'name': 'field', 'group': 'env', 'ngram': '-1', 'ref': 'P010055.4.1'}, {'name': 'discourse', 'group': 'env', 'value': 'body', 'ngram': '-1', 'ref': 'P010055.4.1'}]
    props: List[Dict[str, str]]  # TODO

    # Optional
    frag: str = Field("")
    sig: str = Field("")
    exoprj: str = Field("")
    exolng: str = Field("")
    exosig: str = Field("")
    ftype: str = Field("")
    cof_tails: str = Field("", alias="cof-tails")
    cof_head: str = Field("", alias="cof-head")
    tail_sig: str = Field("", alias="tail-sig")

    para: List[Para] = Field("")
    bad: str = Field("")


# ====================
# ====   Other    ====
# ====================
class LLNode(BaseModel):  # only 50 of these
    """ """

    model_config = ConfigDict(extra=Extra.forbid)

    # Required
    node: Literal["ll"]
    id_: str = Field(alias="id")

    # [{'node': 'l', 'frag': 'šagan', 'ref': 'P020281.27.2', 'inst': '%sux:šagan=amagan[child-bearing mother]',
    # 'sig': "@epsd2/admin/ed3b%sux:šagan=amagan[mother//child-bearing mother]N'N$amagan/šagan#~",
    # 'f': {'lang': 'sux', 'form': 'šagan', 'delim': '', 'gdl': [{'v': 'šagan', 'id': 'P020281.27.2.0'}]
    choices: List[Dict[str, Any]]


class LinkbaseNode(BaseModel):  # only 50 of these
    """ """

    linkbase: Any


# ====================
# ====  CDLNode   ====
# ====================
def _get_node_type(node: Any):
    if "node" in node:
        return node["node"]
    if "linkbase" in node:
        return "linkbase"
    return None


# ====================
# ====   Chunk    ====
# ====================
class ChunkType(Enum):
    """ """

    DISCOURSE = "discourse"
    PHRASE = "phrase"
    SENTENCE = "sentence"
    TEXT = "text"


class Chunk(BaseModel):
    """ """

    model_config = ConfigDict(extra=Extra.forbid)

    # Required
    node: Literal["c"]
    type_: ChunkType = Field(..., alias="type")
    id_: str = Field(..., alias="id")

    # Optional
    cdl: List["CDLNode"] = []
    implicit: bool = False
    label: str = Field("")
    ref: str = Field("")
    subtype: str = Field("")
    tag: str = Field("")


CDLNode = Annotated[
    Union[
        Annotated[Chunk, Tag("c")],
        Annotated[Discontinuity, Tag("d")],
        Annotated[Lemma, Tag("l")],
        Annotated[LLNode, Tag("ll")],
        Annotated[LinkbaseNode, Tag("linkbase")],
    ],
    Field(_get_node_type),
]

Chunk.model_rebuild()


# ---------------  FUNCTIONS ---------------


def parse_cdl_node(node):
    node_type = node.get("node", "")

    if "cdl" in node:
        node["cdl"] = [parse_cdl_node(n) for n in node["cdl"]]

    if node_type == "c":
        return Chunk(**node)
    if node_type == "d":
        return Discontinuity(**node)
    if node_type == "l":
        return Lemma(**node)
    if node_type == "ll":
        return LLNode(**node)
    if "linkbase" in node:
        return LinkbaseNode(**node)

    raise ValueError(f"Unknown node type: {node_type}")
