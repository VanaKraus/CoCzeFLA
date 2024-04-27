from enum import Enum

TAGGER_PATH: str = (
    "_local/czech-morfflex2.0-pdtc1.0-220710/czech-morfflex2.0-pdtc1.0-220710.tagger"
)

TOKENIZER_TYPE: str = "czech"

PLACEHOLDER_INTERJECTION: str = "bacashoogacit"
PLACEHOLDER_NEOLOGISM: str = "bacashoogachi"
PLACEHOLDER_FOREIGN: str = "bacashoogaciz"


# token flags
class tflag(Enum):
    tag_extension = 1
    interjection = 2
    neologism = 3
    foreign = 4


# default values for empty grammatical categories
EMPTY_GRAM_CAT_DEFAULT: dict[str, str] = {
    "case": "x_pad",
    "person": "x_osoba",
    "number": "x_cislo",
    "voice": "x_slovesny_rod",
    "gender": "x_jmenny_rod",
    "aspect": "x_vid",
}
