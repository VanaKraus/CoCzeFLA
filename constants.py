from enum import Enum

TAGGER_PATH = (
    "_local/czech-morfflex2.0-pdtc1.0-220710/czech-morfflex2.0-pdtc1.0-220710.tagger"
)

TOKENIZER_TYPE = "czech"

PLACEHOLDER_INTERJECTION = "bacashoogacit"
PLACEHOLDER_NEOLOGISM = "bacashoogachi"
PLACEHOLDER_FOREIGN = "bacashoogaciz"


# token flags
class tflag(Enum):
    tag_extension = 1
    interjection = 2


# default values for empty grammatical categories
EMPTY_GRAM_CAT_DEFAULT = {
    "case": "x_pad",
    "person": "x_osoba",
    "number": "x_cislo",
    "voice": "x_slovesny_rod",
    "gender": "x_jmenny_rod",
    "aspect": "x_vid",
}
