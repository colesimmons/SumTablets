from enum import Enum


# can't use <...> because that already represents something in the translits
class SpecialToken(Enum):
    MISSING = "#MISSING#"
    BLANK_SPACE = "#BLANK_SPACE#"
    COLUMN = "#COLUMN#"
    RULING = "#RULING#"
    SURFACE = "#SURFACE#"
    LINE_START = "\n"


__all__ = ["SpecialToken"]
