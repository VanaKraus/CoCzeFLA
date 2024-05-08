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
    interjection = 1
    neologism = 2
    foreign = 3


# default values for empty grammatical categories
EMPTY_GRAM_CAT_DEFAULT: dict[str, str] = {
    "case": "x_pad",
    "person": "x_osoba",
    "number": "x_cislo",
    "mood": "x_zpusob",
    "tense": "x_cas",
    "voice": "x_slovesny_rod",
    "aspect": "x_vid",
    "gender": "x_jmenny_rod",
}
