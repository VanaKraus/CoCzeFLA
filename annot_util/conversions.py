"""Holds conversion functions."""

import re

from corpy.morphodita import Token

from annot_util import constants
from annot_util.constants import cats, tflag
from annot_util.flagged_token import FlaggedToken
import annot_util.replacement_rules as rules


class ChatToPlainTextConversionError(Exception):
    """CHAT line that cannot be converted to plaintext."""

    def __init__(self, chat_line: str, result: str, *args: object) -> None:
        self.chat_line = chat_line
        self.result = result

        super().__init__(
            f"Failed to convert chat_line: chat_line likely isn't valid\
                \n\n{chat_line = }\n{result = }",
            *args,
        )


def chat_to_plain_text(chat_line: str) -> str | None:
    """Transform a line in CHAT format to plain text.

    Args:
        chat_line (str): Line in CHAT format.

    Raises:
        ChatToPlainTextConversionError: When chat_line cannot be converted to plaintext. \
            This means that the line is likely invalid.

    Returns:
        str | None: Line in plain text. Return None when the line is a comment or annotation.
    """
    if chat_line == "":
        return None

    result = chat_line

    # loops runs for the first time, result has changed in the last iteration
    first_iteration, needs_review = True, True

    # while the loops runs for the first time
    # or result isn't empty and doesn't match plaintext criteria
    while first_iteration or (
        result and not re.search(rules.PLAIN_TEXT_CRITERIA, result)
    ):
        # result hasn't changed in the last iteration
        # yet it stil doesn't match the criteria
        if not needs_review:
            raise ChatToPlainTextConversionError(chat_line, result)

        result_intermediate = result
        for rule in rules.CHAT_TO_PLAIN_TEXT:
            if result_intermediate == "":
                result = result_intermediate
                break

            result_intermediate = re.sub(rule[0], rule[1], result_intermediate)

        needs_review = result_intermediate != result
        result = result_intermediate

        first_iteration = False

    return result


def generate_mor_pos_label(token: FlaggedToken) -> str:
    """Generate a %mor POS code for given token.

    Args:
        token (Token): MorphoDiTa token.

    Returns:
        str: POS code.
    """
    word, lemma, tag = token.word, token.lemma, token.tag

    # POS values of certain lemmas are pre-defined
    if lemma in rules.MOR_POS_OVERRIDES:
        return rules.MOR_POS_OVERRIDES[lemma]

    result = ""

    match tag[0]:
        # noun
        case "N":
            result = "n"
            if (
                tflag.quotation_beginning not in token.flags
                and word == word.capitalize()
            ):  # proper noun
                result = "n:prop"

        # adjective
        case "A":
            match tag[1]:
                # short (nominal)
                case "C":
                    result = "adj:short"
                # possessive
                case "U":
                    result = "adj:poss"

                case _:
                    result = "adj"

        # pronoun
        case "P":
            match tag[1]:
                # demonstrative
                case "D":
                    result = "pro:dem"
                # personal
                case "5" | "E" | "H" | "P":
                    result = "pro:pers"
                # relative
                case "1":
                    result = "pro:rel"
                # relative or interrogative
                case "4" | "Q":
                    result = "pro:rel/int"
                # possesive
                case "S" | "9":
                    result = "pro:poss"
                # negative
                case "W" | "Y":
                    result = "pro:neg"
                # indefinite
                case "K" | "L" | "Z":
                    result = "pro:indef"
                # reflexive se, si...
                # P8 (svůj) in rules.MOR_POS_OVERRIDES
                case "6" | "7":
                    result = "pro:refl"

                case _:
                    result = "pro"

        # numeral
        case "C":
            match tag[1]:
                case "l" | "n" | "z" | "a" | "y":
                    result = "num:card"
                case "r" | "w":
                    result = "num:ord"
                case "v" | "o":
                    result = "num:mult"

                case _:
                    result = "num"

        # verb; v:aux and v:cop overriden in rules.MOR_POS_OVERRIDES and rules.MOR_WORDS_OVERRIDES
        case "V":
            result = "v"

        # adverb; adv:pro and adv:pro:neg overriden in rules.MOR_POS_OVERRIDES
        case "D":
            result = "adv"

        # preposition
        case "R":
            result = "prep"

        case "J":
            match tag[1]:
                # coordinating conjunction (incl. binary math. operations)
                case "^" | "*":
                    result = "conj:coord"
                # subordinate conjunction
                case ",":
                    result = "conj:sub"

        # particle
        case "T":
            result = "part"

        # interjection
        case "I":
            result = "int"

        # punctuation
        case "Z":
            result = "Z"

        # abbreviations, foreign words, letters, segments, unknowns
        case _:
            result = "x"

    # special cases
    if lemma in ("tak", "proto") and result == "adv":
        result = "adv:pro"

    return result


def _get_default_cat(category: cats) -> str:
    """Get default value for a grammatical category. Use when the category value is unclear.

    Args:
        category (cats)

    Returns:
        str: Category value.
    """
    return constants.EMPTY_GRAM_CAT_DEFAULT[category]


def _require_cats(categories: dict[cats, str], *requirements: cats) -> dict[cats, str]:
    """Add default entries for selected categories which aren't present in the dictionary.

    Args:
        categories (dict[cats, str]): Categories dictionary.
        *requirements (Optional[cats]): Categories required.

    Returns:
        dict[str, str]: New dictionary with default entries filled in if required.
    """
    result = dict(categories)

    for req in requirements:
        if not req in result:
            result[req] = _get_default_cat(req)

    return result


def generate_mor_tag(token: Token) -> str:
    """Generate a %mor tag for given token.

    Args:
        token (Token): MorphoDiTa token.

    Returns:
        str: %mor tag.
    """

    tag, _, lemma = token.tag, token.word, token.lemma

    # delimiters for grammatical categories and for lexical categories
    gr_delim, lex_delim = "&", "-"

    # lexical categories
    lxcats: dict[cats, str] = {}

    # grammatical categories
    grcats: dict[cats, str] = {}

    # negation
    if tag[10] == "N":
        lxcats[cats.negation] = "neg"

    # verbs
    if tag[0] == "V":
        # gender
        match tag[2]:
            case "I" | "M" | "Y":
                grcats[cats.gender] = "M"
            case "F":
                grcats[cats.gender] = "F"
            case "N":
                grcats[cats.gender] = "N"

        # number
        match tag[3]:
            case "S":
                grcats[cats.number] = "SG"
            case "P":
                grcats[cats.number] = "PL"

            # else: the value "–": infinitive, auxiliary "být" in the conditional form
            # "D" (dual), "W" (sg. for f., pl. for n.) and "X" (any) values also omitted

        # person
        if tag[7] in ("1", "2", "3"):
            grcats[cats.person] = tag[7]

        # tense
        match tag[8]:
            case "F":
                grcats[cats.tense] = "futur"
            case "P":
                grcats[cats.tense] = "pres"
            case "R":
                grcats[cats.tense] = "past"

        # voice
        match tag[11]:
            case "A":
                grcats[cats.voice] = "akt"
            case "P":
                grcats[cats.voice] = "pas"

        # aspect
        match tag[12]:
            case "P":
                grcats[cats.aspect] = "pf"
            case "I":
                grcats[cats.aspect] = "impf"
            case "B":
                grcats[cats.aspect] = "biasp"

        # form types specifics
        match tag[1]:
            # infinitive
            case "f":
                grcats[cats.form_type] = "inf"

                grcats = _require_cats(grcats, cats.form_type, cats.aspect)

            # past participle ("q" denotes its archaic form)
            case "p" | "q":
                grcats = _require_cats(
                    grcats,
                    cats.number,
                    cats.tense,
                    cats.voice,
                    cats.gender,
                    cats.aspect,
                )

            # passive participle
            case "s":
                grcats = _require_cats(
                    grcats, cats.number, cats.voice, cats.gender, cats.aspect
                )

            # conditional
            case "c":
                grcats[cats.mood] = "cond"

                grcats = _require_cats(
                    grcats, cats.person, cats.number, cats.mood, cats.voice, cats.aspect
                )

            # imperative
            case "i":
                grcats[cats.mood] = "imp"

                # passive imperatives expressed by an imperative aux and past participle
                grcats[cats.voice] = "akt"

                grcats = _require_cats(
                    grcats,
                    cats.person,
                    cats.number,
                    cats.mood,
                    cats.voice,
                    cats.aspect,
                )

            # indicative ("t" denotes its archaic form)
            case "B" | "t":
                grcats[cats.mood] = "ind"

                grcats = _require_cats(
                    grcats,
                    cats.person,
                    cats.number,
                    cats.mood,
                    cats.tense,
                    cats.voice,
                    cats.aspect,
                )

            # transgressives (both present and past)
            case "e" | "m":
                grcats[cats.form_type] = "trans"

                # passive transgressives are expressed by a transgressive aux and past participle
                grcats[cats.voice] = "akt"

                grcats = _require_cats(
                    grcats,
                    cats.form_type,
                    cats.number,
                    cats.voice,
                    cats.gender,
                    cats.aspect,
                )

    # nouns, adjectives, pronouns, numerals and not multiplicative numerals
    elif tag[0] in ("N", "A", "P", "C") and not tag.startswith("Cv"):
        # gender
        match tag[2]:
            # discriminate animate and inanimate masculines for nouns only
            case "M":
                grcats[cats.gender] = "MA" if tag[0] == "N" else "M"
            case "I":
                grcats[cats.gender] = "MI" if tag[0] == "N" else "M"
            case "Y":
                grcats[cats.gender] = "M"
            case "F":
                grcats[cats.gender] = "F"
            case "N":
                grcats[cats.gender] = "N"

        # number
        match tag[3]:
            case "S":
                grcats[cats.number] = "SG"
            case "P" | "D":
                grcats[cats.number] = "PL"

        # case
        if tag[4].isnumeric():
            grcats[cats.case] = tag[4]

        grcats = _require_cats(grcats, cats.gender, cats.number, cats.case)

    # comparison degree for adjectives and adverbs
    if tag[0] in ("A", "D"):
        match tag[9]:
            case "2":  # comparative
                lxcats[cats.comp_deg] = "CP"
            case "3":  # superlative
                lxcats[cats.comp_deg] = "SP"

    # special cases
    if lemma in ("co", "něco", "nic"):
        grcats[cats.gender] = "N"
    if lemma in ("kdo", "někdo", "nikdo", "kdokoli", "kdokoliv", "kdosi", "kdopak"):
        grcats[cats.gender] = "M"

    if lemma in (
        "kdo",
        "co",
        "něco",
        "nic",
        "někdo",
        "nikdo",
        "kdokoli",
        "kdokoliv",
        "kdosi",
        "kdopak",
        "se",
    ):
        grcats[cats.number] = "SG"

    if lemma in ("já", "my", "ty", "vy", "se"):
        del grcats[cats.gender]

    # build strings

    # join non-empty grammatical categories into one string
    gr_joined = gr_delim.join(
        [grcats[cat] for cat in constants.GRAMMATICAL_CATEGORY_ORDER if cat in grcats]
    )

    # join non-empty lexical categories into one string
    lex_join = lex_delim.join(
        [lxcats[cat] for cat in constants.LEXICAL_CATEGORY_ORDER if cat in lxcats]
        + [gr_joined]
    )

    return lex_join
