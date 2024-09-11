"""Holds the FlaggedToken class."""

from typing import Any, Optional

from corpy.morphodita import Token

from annot_util.constants import tflag


class FlaggedToken(Token):
    """Token with flags associated.

    Attributes:
        flags (dict[tflag, Any]): Flags associated with the token.
    """

    flags: dict[tflag, Any]

    def __new__(
        cls, word: str, lemma: str, tag: str, flags: Optional[dict[tflag, Any]] = None
    ):
        instance = super(FlaggedToken, cls).__new__(cls, word, lemma, tag)
        instance.flags = {} if flags is None else flags
        return instance

    @classmethod
    def from_token(
        cls, token: Token, flags: Optional[dict[tflag, Any]] = None
    ) -> "FlaggedToken":
        """Create FlaggedToken from Token.

        Args:
            token (Token)
            flags (dict[tflag, Any], optional): Flags associated with given token. Defaults to None.
        """
        return cls(token.word, token.lemma, token.tag, flags)
