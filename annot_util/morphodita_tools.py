"""Holds corpy.morphodita helper functions."""

import sys
from typing import Optional

from corpy.morphodita import Tagger, Tokenizer, Token

from annot_util import constants

# cached taggers and tokenizers
_taggers: dict[str, Tagger] = {}
_tokenizers: dict[str, Tokenizer] = {}


def get_tagger(path: Optional[str] = None) -> Tagger:
    """Get tagger instance and cache it.

    Args:
        path (str, optional): Path to MorfFlex .tagger file. \
            When path == None, constants.TAGGER_PATH is used. Defaults to None.

    Returns:
        Tagger: Tagger instance.
    """

    if not path:
        path = constants.TAGGER_PATH

    if path in _taggers:
        return _taggers[path]

    print(f"Load MorphoDiTa tagger from {path = }", file=sys.stderr)
    result = Tagger(path)
    print("MorphoDiTa tagger loaded", file=sys.stderr)
    _taggers[path] = result
    return result


def get_tokenizer(tokenizer_type: Optional[str] = None) -> Tokenizer:
    """Get tokenizer instance and cache it.

    Args:
        tokenizer_type (str, optional): MorphoDiTa tokenizer type. \
            When tokenizer_type == None, constants.TOKENIZER_TYPE is used. Defaults to None.

    Returns:
        Tokenizer: Tokenizer instance.
    """

    if not tokenizer_type:
        tokenizer_type = constants.TOKENIZER_TYPE

    if tokenizer_type in _tokenizers:
        return _tokenizers[tokenizer_type]

    print(f"Load MorphoDiTa tokenizer ({tokenizer_type = })", file=sys.stderr)
    result = Tokenizer(tokenizer_type)
    print("MorphoDiTa tokenizer loaded", file=sys.stderr)
    _tokenizers[tokenizer_type] = result
    return result


def tag_string(
    string: str, tagger: Optional[Tagger] = None, guesser: bool = False
) -> list[Token]:
    """Tag string using MorphoDiTa tagger.

    Args:
        string (str): String to be tagged.
        tagger (Tagger, optional): Tagger to tag the string with. \
            When tagger == None, _get_tagger() is used. Defaults to None.
        guesser (bool, optional): use MorphoDiTa's morphological guesser. \
            Defaults to False.

    Returns:
        list[Token]
    """
    if not tagger:
        tagger = get_tagger()

    output = list(tagger.tag(string, convert="strip_lemma_id", guesser=guesser))
    return output


def tokenize_string(
    string: str, tokenizer: Optional[Tokenizer] = None
) -> list[str | list[str]]:
    """Tokenize string using MorphoDiTa tokenizer.

    Args:
        string (str): String to be tokenized.
        tokenizer (Tokenizer, optional): Tokenizer to tokenize the string with. \
            When tokenizer == None, _get_tokenizer() is used. Defaults to None.

    Returns:
        list[str]: _description_
    """
    if not tokenizer:
        tokenizer = get_tokenizer()

    return list(tokenizer.tokenize(string))
