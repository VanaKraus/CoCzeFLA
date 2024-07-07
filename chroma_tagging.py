#!/usr/bin/env python3

""" 
# TODO: module docstring and function docstrings
# TODO: check that docstrings are up-to-date

the script for the morphological analysis of the longitudinal corpus of spoken Czech child-adult interactions

MIT License

Copyright (c) 2023 Jakub Sláma
Copyright (c) 2024 Ivan Kraus

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

***

# TODO: this

fundamantelly, all the functions need to be run, but for analyzing a specific file, you need to run only the last function, 
file_to_file(), which incorporates all the other functions and from a file creates a new file with morphological tiers added

for details, explanations and the like, consult the paper submitted to the the journal Language Resources and Evaluation

Chromá, Anna – Sláma, Jakub – Matiasovitsová, Klára – Treichelová, Jolana (submitted): 
A morphologically annotated longitudinal corpus of spoken Czech child-adult interactions. 
Language Resources and Evaluation.

if you have any questions, feel free to contact me at slama@ujc.cas.cz, but please know that I'm a linguist, not a person 
who specializes in coding, Python etc., so this script is quite clearly not the optimal way to do its job (and processing 
files with this script is thus rather slow), even though it thus this job as well as it is supposed to

"""

import re
import sys
import os
from typing import Any, Generator

from corpy.morphodita import Tagger, Token, Tokenizer
from nltk.corpus import PlaintextCorpusReader

import argument_handling as ahandling
import constants
from constants import tflag, cats
import replacement_rules as rules

# cached taggers and tokenizers
_taggers: dict[str, Tagger] = {}
_tokenizers: dict[str, Tokenizer] = {}


def _get_tagger(path: str | None = None) -> Tagger:
    """Get tagger instance and cache it.

    Args:
        path (str | None, optional): Path to MorfFlex .tagger file. \
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


def _get_tokenizer(tokenizer_type: str | None = None) -> Tokenizer:
    """Get tokenizer instance and cache it.

    Args:
        tokenizer_type (str | None, optional): MorphoDiTa tokenizer type. \
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
    string: str, tagger: Tagger | None = None, guesser: bool = False
) -> list[Token]:
    """Tag string using MorphoDiTa tagger.

    Args:
        string (str): String to be tagged.
        tagger (Tagger | None, optional): Tagger to tag the string with. \
            When tagger == None, _get_tagger() is used. Defaults to None.

    Returns:
        list[Token]
    """
    if not tagger:
        tagger = _get_tagger()

    output = list(tagger.tag(string, convert="strip_lemma_id", guesser=guesser))
    return output


def tokenize_string(string: str, tokenizer: Tokenizer | None = None) -> list[str]:
    """Tokenize string using MorphoDiTa tokenizer.

    Args:
        string (str): String to be tokenized.
        tokenizer (Tokenizer | None, optional): Tokenizer to tokenize the string with. \
            When tokenizer == None, _get_tokenizer() is used. Defaults to None.

    Returns:
        list[str]: _description_
    """
    if not tokenizer:
        tokenizer = _get_tokenizer()

    return list(tokenizer.tokenize(string))


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


def pos_mor(token: Token, flags: dict[tflag, Any] = None) -> str:
    """Generate a %mor POS code for given token.

    Args:
        token (Token): MorphoDiTa token.

    Returns:
        str: POS code.
    """
    if not flags:
        flags = {}

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
                tflag.quotation_beginning not in flags and word == word.capitalize()
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
        category (str)

    Returns:
        str: Category value.
    """
    return constants.EMPTY_GRAM_CAT_DEFAULT[category]


def _require_cats(
    categories: dict[cats, str], *requirements: list[cats]
) -> dict[str, str]:
    result = dict(categories)

    for req in requirements:
        if not req in result:
            result[req] = _get_default_cat(req)

    return result


def transform_tag(token: Token) -> str:
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
    lxcats: dict[str, str] = {}

    # grammatical categories
    grcats: dict[str, str] = {}

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


def construct_mor_word(token: Token, flags: dict[tflag, Any] = None) -> str:
    """Create an entire %mor morphological annotation for the given token.

    Args:
        token (Token): MorphoDiTa token.
        flags (dict[tflag, Any], optional): Token flags of `token`. Defaults to None.

    Returns:
        str
    """
    pos_label = pos_mor(token, flags)

    if pos_label == "Z":
        return token.lemma

    if tflag.interjection in flags:
        return f"int|{token.lemma}"

    if tflag.neologism in flags:
        return f"x|{token.word}-neo"

    if tflag.foreign in flags:
        return f"x|{token.word}-for"

    if token.word in rules.MOR_WORDS_OVERRIDES:
        return rules.MOR_WORDS_OVERRIDES[token.word]

    new_tag = f"-{_tag}" if (_tag := transform_tag(token)) != "" else ""

    lemma = token.lemma

    # some MorfFlex lemmas to be replaced by ours
    if token.lemma in rules.MOR_MLEMMAS_LEMMA_OVERRIDES:
        lemma = rules.MOR_MLEMMAS_LEMMA_OVERRIDES[token.lemma]

    # some words have their lemmas hardcoded
    if token.word in rules.MOR_WORDS_LEMMA_OVERRIDES:
        lemma = rules.MOR_WORDS_LEMMA_OVERRIDES[token.word]

    # neologisms not to be lemmatized
    elif tflag.neologism in flags:
        lemma = token.word

    return f"{pos_label}|{lemma}{new_tag}"


def mor_line(
    text: str,
    tokenizer: Tokenizer | None = None,
    tagger: Tagger | None = None,
    guesser: bool = False,
) -> str:
    """Create a %mor line from an input text.

    Args:
        text (str): Plain line (stripped of the speaker ID and other annotation). \
            Words with special annotation are expected to use their appropriate \
            placeholders (`constants.PLACEHOLDER_*`).
        tokenizer (Tokenizer | None, optional): MorphoDiTa tokenizer to use. \
            When tokenizer == None, _get_tokenizer() is used. Defaults to None.
        tagger (Tagger | None, optional): MorphoDiTa tagger to use. \
            When tagger == None, _get_tagger() is used. Defaults to None.

    Returns:
        str: %mor line.
    """
    if not tokenizer:
        tokenizer = _get_tokenizer()
    if not tagger:
        tagger = _get_tagger()

    flags: list[dict[tflag,]] = []
    for i, word in enumerate(tokens := tokenize_string(text, tokenizer)):
        flag = {}
        if word.endswith(constants.PLACEHOLDER_NEOLOGISM):
            flag[tflag.neologism] = True
        elif word.endswith(constants.PLACEHOLDER_FOREIGN):
            flag[tflag.foreign] = True
        elif word.endswith(constants.PLACEHOLDER_INTERJECTION):
            flag[tflag.interjection] = True

        if i > 0 and tokens[i - 1] == "“":
            flag[tflag.quotation_beginning] = True

        flags.append(flag)

    text = (
        text.replace(constants.PLACEHOLDER_NEOLOGISM, "")
        .replace(constants.PLACEHOLDER_FOREIGN, "")
        .replace(constants.PLACEHOLDER_INTERJECTION, "")
    )

    tagged_tokens: list[Token] = tag_string(text, tagger, guesser)
    result: list[str] = []

    for i, token in enumerate(tagged_tokens):
        result.append(construct_mor_word(token, flags[i]))
    text = "%mor:\t" + " ".join(result)

    # formal adjustments to correct unwanted spaces created by tokenization
    text = text.replace("+ . . .", "+...").replace("+ / .", "+/.")

    return text


def process_line(
    line: str, tokenizer: Tokenizer = None, tagger: Tagger = None, guesser: bool = False
) -> Generator[str, None, None]:
    if not tokenizer:
        tokenizer = _get_tokenizer()
    if not tagger:
        tagger = _get_tagger()

    line = line.strip(" \n")
    yield line

    if line.startswith(("@", "%")):
        return

    line_plain_text = chat_to_plain_text(line)
    if line_plain_text and not line_plain_text in rules.SKIP_LINES:
        yield mor_line(line_plain_text, tokenizer, tagger, guesser)


def annotate_filestream(
    source_fs,
    target_fs,
    tokenizer: Tokenizer = None,
    tagger: Tagger = None,
    guesser: bool = False,
):
    """Add morphological annotation to filestream.

    Args:
        source_fs: Source filestream.
        target_fs: Target filestream.
        tokenizer (Tokenizer, optional): MorphoDiTa tokenizer to use. \
            Defaults to _get_tokenizer().
        tagger (Tagger, optional): MorphoDiTa tagger to use. Defaults to _get_tagger().
    """
    if not tokenizer:
        tokenizer = _get_tokenizer()
    if not tagger:
        tagger = _get_tagger()

    for line in source_fs:
        for out in process_line(line, tokenizer, tagger, guesser):
            print(out, file=target_fs)


def annotate_file(
    path_source: str,
    path_target: str,
    tokenizer: Tokenizer | None = None,
    tagger: Tagger | None = None,
    guesser: bool = False,
):
    """Add morphological annotation to single file.

    Args:
        path_source (str): Path to the source file.
        path_target (str): Path to the target file. Existing files will be overwritten.
        tokenizer (Tokenizer | None, optional): MorphoDiTa tokenizer to use. \
            When tokenizer == None, _get_tokenizer() is used. Defaults to None.
        tagger (Tagger | None, optional): MorphoDiTa tagger to use. \
            When tagger == None, _get_tagger() is used. Defaults to None.
    """

    if not tokenizer:
        tokenizer = _get_tokenizer()
    if not tagger:
        tagger = _get_tagger()

    with open(path_source, "r", encoding="utf-8") as source_fs:
        with open(path_target, "w", encoding="utf-8") as target_fs:
            print(f"Annotate: {path_source}", file=sys.stderr)
            annotate_filestream(source_fs, target_fs, tokenizer, tagger, guesser)


def _handle_args(args) -> int:
    _ecode = 0

    if args.tagger:
        constants.TAGGER_PATH = args.tagger[0]

    if args.tokenizer:
        constants.TOKENIZER_TYPE = args.tokenizer[0]

    # take input from stdin
    if args.std:
        annotate_filestream(sys.stdin, sys.stdout, guesser=args.guess)
    # take files as input
    elif args.outdir:
        files: list[tuple[str, str]] = []

        # an input directory specified
        if args.indir:
            reader = PlaintextCorpusReader(args.indir[0], r".*\.txt", encoding="utf-8")
            files = [
                (os.path.join(args.indir[0], id), os.path.join(args.outdir[0], id))
                for id in reader.fileids()
            ]

        # individual files specified as input
        elif len(args.inputfiles) > 0:
            files = [
                (file, os.path.join(args.outdir[0], os.path.basename(file)))
                for file in args.inputfiles
            ]
        else:
            print(
                "Please specify your input files. See --help for more.", file=sys.stderr
            )
            return 2

        # run file annotation
        for input_file, output_file in files:
            if not os.path.isdir(dname := os.path.dirname(output_file)):
                os.makedirs(dname)

            try:
                annotate_file(input_file, output_file, guesser=args.guess)

            except IsADirectoryError:
                _ecode = 1
                print(f"Skip\t: {input_file} (directory)", file=sys.stderr)
            except FileNotFoundError:
                _ecode = 1
                print(f"Skip\t: {input_file} (not found)", file=sys.stderr)
            except ChatToPlainTextConversionError as e:
                _ecode = 1
                print(
                    f"Error\t: {input_file} ({e.__class__.__name__})\n{e}\n",
                    file=sys.stderr,
                )
    else:
        print(
            "An output directory needs to be specified. See --help for more.",
            file=sys.stderr,
        )
        return 2

    return _ecode


if __name__ == "__main__":
    req_arguments = ahandling.get_argument_subset(
        "inputfiles", "std", "indir", "outdir", "tokenizer", "tagger", "guess"
    )

    if len(sys.argv) > 1:
        parser = ahandling.get_argument_parser(
            req_arguments,
            description="Add morphological annotation to a CHAT text file \
                according to the CoCzeFLA standards.",
        )
        arguments = parser.parse_args(sys.argv[1:])
    else:
        arguments = ahandling.argument_walkthrough(req_arguments)

    ECODE = _handle_args(arguments)

    sys.exit(ECODE)
