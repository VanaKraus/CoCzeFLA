from enum import Enum

TAGGER_PATH: str = (
    "czech-morfflex2.0-pdtc1.0-220710/czech-morfflex2.0-pdtc1.0-220710.tagger"
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
    quotation_beginning = 4


# grammatical and lexical categories
class cats(Enum):
    case = 1
    person = 2
    number = 3
    mood = 4
    tense = 5
    voice = 6
    aspect = 7
    gender = 8
    negation = 9
    comp_deg = 10
    form_type = 11


# TODO: annotate
GRAMMATICAL_CATEGORY_ORDER: list[cats] = [
    cats.form_type,
    cats.case,
    cats.person,
    cats.number,
    cats.mood,
    cats.tense,
    cats.voice,
    cats.gender,
    cats.aspect,
]

# TODO: annotate
LEXICAL_CATEGORY_ORDER: list[cats] = [cats.comp_deg, cats.negation]

# default values for empty grammatical categories
EMPTY_GRAM_CAT_DEFAULT: dict[cats, str] = {
    cats.case: "x_pad",
    cats.person: "x_osoba",
    cats.number: "x_cislo",
    cats.mood: "x_zpusob",
    cats.tense: "x_cas",
    cats.voice: "x_slovesny_rod",
    cats.aspect: "x_vid",
    cats.gender: "x_jmenny_rod",
}
