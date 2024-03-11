from enum import Enum

TAGGER_PATH = (
    "_local/czech-morfflex2.0-pdtc1.0-220710/czech-morfflex2.0-pdtc1.0-220710.tagger"
)

TOKENIZER_TYPE = "czech"

PLACEHOLDER_INTERJECTION = "bacashoogacit"
PLACEHOLDER_NEOLOGISM = "bacashoogachi"
# TODO: what does "ciz" stand for?
PLACEHOLDER_CIZ = "bacashoogaciz"


# token flags
class tflag(Enum):
    tag_extension = 1
    interjection = 2


# default values for empty grammatical categories
EMPTY_GRAM_CAT_DEFAULT = {
    "aspect": "x_vid",
    "number": "x_cislo",
    "voice": "x_slovesny_rod",
    "gender": "x_jmenny_rod",
    "person": "x_osoba",
}
