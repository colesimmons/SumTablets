"""
Defines the base class for all text models.

These are attributes shared by texts in all corpora.
"""

import json
import re
from typing import List, Union

from pydantic import BaseModel, ConfigDict, Field

from src.models.cdl import (
    CDLNode,
    crawl_cdl_for_text,
    parse_cdl_node,
)
from src.models.enums import (
    Genre,
    Language,
    ObjectType,
    Period,
    Status,
    Supergenre,
    XProject,
)
from src.models.special_token import SpecialToken


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dir_path: str

    cdl: List[CDLNode] = []

    # Metadata
    id_text: str = ""
    designation: str = ""  # almost always defined
    language: Language = Language.UNSPECIFIED
    object_type: ObjectType = ObjectType.UNSPECIFIED
    period: Period = Period.UNSPECIFIED

    # Genre
    genre: Genre = Genre.UNSPECIFIED
    subgenre: str = ""  # TODO use Subgenre enum
    supergenre: Supergenre = Supergenre.UNSPECIFIED

    # Provenience
    excavation_no: str = ""
    museum_no: str = ""
    primary_publication: str = ""
    provenience: str
    publication_history: str = ""

    # Other
    accession_no: str = ""
    bdtns_id: str = ""
    date_of_origin: str = ""
    designation: str
    images: List[str] = []
    langs: str = ""
    project: str
    public: str = ""  # '', 'no'
    status: Status = Status.UNSPECIFIED
    trans: List[str] = []
    uri: str = ""
    xproject: XProject = XProject.UNSPECIFIED

    @property
    def file_id(self) -> str:
        return self.id_text

    # TODO: are there members in catalogue that aren't in corpusjson/?
    # TODO: are there files in corpusjson/ that aren't in catalogue?
    # TODO: use timestamp
    def load_contents(self) -> None:
        """
        Load the contents of the text from a JSON file.

        If the `id_text` attribute is not set, the `cdl` attribute will be set to an empty list.

        Returns:
            None
        """

        if not self.file_id:
            raise ValueError("no file id: ", self.model_dump())

        text_path = f"{self.dir_path}/{self.file_id}.json"
        with open(text_path, "r", encoding="utf-8") as f:
            text_data = json.load(f)
        self.cdl = [parse_cdl_node(node) for node in text_data["cdl"]]

    def transliteration(self) -> str:
        """
        Return the transliteration of the text.

        Returns:
            str: The transliteration of the text.
        """

        special_token_format = r"#[\S]*?#"

        # TODO
        def without_special_tokens(text: str) -> str:
            text = re.sub(special_token_format, "", text)
            text = text.replace("\n", "")
            text = text.replace(" ", "")
            return text

        tokens, langs = crawl_cdl_for_text(self.cdl)
        self.langs = ", ".join(sorted(list(langs)))
        text = " ".join(tokens)

        # Only include surfaces if there are non-special tokens
        surfaces = text.split(SpecialToken.SURFACE.value)
        surfaces = [surface.strip() for surface in surfaces]
        surfaces = [surface for surface in surfaces if without_special_tokens(surface)]

        text = ""
        if surfaces:
            join_with = f"\n{SpecialToken.SURFACE.value}\n"
            text = f"{SpecialToken.SURFACE.value}\n" + join_with.join(surfaces)

        text = re.sub(r"\ *\n\ *", "\n", text)  # remove spaces around newlines
        text = re.sub(r"\n+", "\n", text)  # remove multiple newlines
        text = re.sub(r"\ +", " ", text)  # remove multiple spaces
        return text.strip()


class Text:
    class AdminEd1and2(_Base):
        pass

    class AdminEd3a(_Base):
        pass

    class AdminEd3b(_Base):
        pass

    class AdminOldAkk(_Base):
        pass

    class AdminLagash2(_Base):
        pass

    class AdminUr3(_Base):
        acquisition_history: str = ""
        ark_number: str = ""
        atf_source: str = ""
        atf_up: str = ""
        author: str = ""
        author_remarks: str = ""
        cdli_comments: str = ""
        citation: str = ""
        collection: str = ""
        date_entered: str = ""
        date_remarks: str = ""
        date_updated: str = ""
        dates_referenced: str = ""
        db_source: str = ""
        electronic_publication: str = ""
        external_id: str = ""
        google_earth_collection: str = ""
        height: str = ""
        id_: str = Field(default="", alias="id")
        id_text_int: str = ""
        lineart_up: str = ""
        material: str = ""
        object_remarks: str = ""
        photo_up: str = ""
        provenience_remarks: str = ""
        publication_date: str = ""
        published_collation: str = ""
        seal_id: str = ""
        seal_information: str = ""
        subgenre_remarks: str = ""
        thickness: str = ""
        translation_source: str = ""
        width: str = ""

    class LiteraryEarly(_Base):
        id_composite: str = ""
        keywords: str = ""
        place: str = ""

        @property
        def file_id(self) -> str:
            return self.id_composite if self.id_composite else self.id_text

    class LiteraryOldBab(_Base):
        id_composite: str = ""
        keywords: str = ""
        place: str = ""
        chap: str = ""
        distribution: str = ""
        provdist: str = ""
        sec1: str = ""
        sec2: str = ""
        sources: str = ""

        @property
        def file_id(self) -> str:
            return self.id_composite if self.id_composite else self.id_text

    class Incantations(_Base):
        pass

    class Liturgies(_Base):
        pass

    class Royal(_Base):
        id_composite: str = ""
        keywords: str = ""
        place: str = ""
        distribution: str = ""
        primary_edition: str = ""
        provdist: str = ""
        ruler: str = ""
        sources: str = ""

        @property
        def file_id(self) -> str:
            return self.id_composite if self.id_composite else self.id_text

    class Udughul(_Base):
        pass

    class Varia(_Base):
        pass


TextType = Union[
    Text.AdminEd1and2,
    Text.AdminEd3a,
    Text.AdminEd3b,
    Text.AdminOldAkk,
    Text.AdminLagash2,
    Text.AdminUr3,
    Text.LiteraryEarly,
    Text.LiteraryOldBab,
    Text.Incantations,
    Text.Liturgies,
    Text.Royal,
    Text.Udughul,
    Text.Varia,
]


__all__ = ["Text", "TextType"]
