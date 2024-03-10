from enum import Enum

TAGGER_PATH = (
    "_local/czech-morfflex2.0-pdtc1.0-220710/czech-morfflex2.0-pdtc1.0-220710.tagger"
)

TOKENIZER_TYPE = 'czech'

PLACEHOLDER_INTERJECTION = "bacashoogacit"
PLACEHOLDER_NEOLOGISM = "bacashoogachi"
# TODO: what does "ciz" stand for?
PLACEHOLDER_CIZ = "bacashoogaciz"


# token flags
class tflag(Enum):
    tag_extension = 1
    interjection = 2
