#!/usr/bin/env python3

""" 
# TODO: module docstring

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

import argparse
import re
import sys
import os
from typing import Any

from corpy.morphodita import Tagger, Token, Tokenizer
from nltk.corpus import PlaintextCorpusReader

import constants
import replacement_rules as rules

_ecode: int = 0

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


def tag_string(string: str, tagger: Tagger | None = None) -> list[Token]:
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

    output = list(tagger.tag(string, convert="strip_lemma_id"))
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
    if chat_line == "" or chat_line.startswith(("@", "%")):
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


def pos_mor(token: Token) -> str:
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
            if word == word.capitalize():  # proper noun
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


def _get_default_gram_cat(category: str) -> str:
    """Get default value for a grammatical category. Use when the category value is unclear.

    Args:
        category (str)

    Returns:
        str: Category value.
    """
    return constants.EMPTY_GRAM_CAT_DEFAULT[category]


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
    neg, comp_deg = None, None

    # grammatical categories
    form_type, case, person, number, mood, tense, voice, gender, aspect = (
        None for _ in range(9)
    )

    # negation
    if tag[10] == "N":
        neg = "neg"

    # verbs
    if tag[0] == "V":
        # gender
        match tag[2]:
            case "I" | "M" | "Y":
                gender = "M"
            case "F":
                gender = "F"
            case "N":
                gender = "N"
            case "-":
                pass
            case _:  # cases when MorphoDiTa wasn't sure
                gender = _get_default_gram_cat("gender")

        # number
        match tag[3]:
            case "S":
                number = "SG"
            case "P":
                number = "PL"

            # else: the value "–": infinitive, auxiliary "být" in the conditional form
            # "D" (dual), "W" (sg. for f., pl. for n.) and "X" (any) values also omitted

        # person
        if tag[7] in ("1", "2", "3"):
            person = tag[7]

        # tense
        match tag[8]:
            case "F":
                tense = "futur"
            case "P":
                tense = "pres"
            case "R":
                tense = "past"

        # voice
        match tag[11]:
            case "A":
                voice = "akt"
            case "P":
                voice = "pas"

        # aspect
        match tag[12]:
            case "P":
                aspect = "pf"
            case "I":
                aspect = "impf"
            case "B":
                aspect = "biasp"
            case _:
                aspect = _get_default_gram_cat("aspect")

        # form types specifics
        match tag[1]:
            # infinitive
            case "f":
                form_type = "inf"

            # past participle ("q" denotes its archaic form)
            case "p" | "q":
                if number is None:
                    number = _get_default_gram_cat("number")

                if voice is None:
                    voice = _get_default_gram_cat("voice")

            # passive participle
            case "s":
                if number is None:
                    number = _get_default_gram_cat("number")

                if voice is None:
                    voice = _get_default_gram_cat("voice")

            # conditional
            case "c":
                mood = "cond"

                if number is None:
                    number = _get_default_gram_cat("number")

                if person is None:
                    person = _get_default_gram_cat("person")

            # imperative
            case "i":
                mood = "imp"

                # passive imperatives expressed by an imperative aux and past participle
                voice = "akt"

                if number is None:
                    number = _get_default_gram_cat("number")

            # indicative ("t" denotes its archaic form)
            case "B" | "t":
                mood = "ind"

                if number is None:
                    number = _get_default_gram_cat("number")

                if voice is None:
                    voice = _get_default_gram_cat("voice")

            # transgressives (both present and past)
            case "e" | "m":
                form_type = "trans"

                # passive transgressives are expressed by a transgressive aux and past participle
                voice = "akt"

    # nouns, adjectives, pronouns, numerals and not multiplicative numerals
    elif tag[0] in ("N", "A", "P", "C") and not tag.startswith("Cv"):
        # gender
        match tag[2]:
            # discriminate animate and inanimate masculines for nouns only
            case "M":
                gender = "MA" if tag[0] == "N" else "M"
            case "I":
                gender = "MI" if tag[0] == "N" else "M"
            case "Y":
                gender = "M"
            case "F":
                gender = "F"
            case "N":
                gender = "N"
            case "-":
                pass
            case _:  # cases when MorphoDiTa wasn't sure
                gender = _get_default_gram_cat("gender")

        # number
        match tag[3]:
            case "S":
                number = "SG"
            case "P" | "D":
                number = "PL"
            case _:
                number = _get_default_gram_cat("number")

        # case
        if tag[4].isnumeric():
            case = tag[4]
        else:
            case = _get_default_gram_cat("case")

    # comparison degree for adjectives and adverbs
    if tag[0] in ("A", "D"):
        match tag[9]:
            case "2":  # comparative
                comp_deg = "CP"
            case "3":  # superlative
                comp_deg = "SP"

    # special cases
    if lemma == "co":
        gender = "N"
    if lemma == "kdo":
        gender = "M"

    if lemma in ("kdo", "co", "se"):
        number = "SG"

    # build strings
    gram_categories = (
        form_type,
        case,
        person,
        number,
        mood,
        tense,
        voice,
        gender,
        aspect,
    )

    # join non-empty grammatical categories into one string
    gr_joined = gr_delim.join([el for el in gram_categories if el])

    lex_categories = (comp_deg, neg, gr_joined)

    # join non-empty lexical categories into one string
    return lex_delim.join([el for el in lex_categories if el])


def construct_mor_word(token: Token, flags: dict[constants.tflag, Any] = None) -> str:
    """Create an entire %mor morphological annotation for the given token.

    Args:
        token (Token): MorphoDiTa token.
        flags (dict[constants.tflag, Any], optional): Token flags of `token`. Defaults to None.

    Returns:
        str
    """
    pos_label = pos_mor(token)

    if pos_label == "Z":
        return token.lemma

    if constants.tflag.interjection in flags:
        return f"int|{token.lemma}"

    if constants.tflag.neologism in flags:
        return f"x|{token.word}-neo"

    if constants.tflag.foreign in flags:
        return f"x|{token.word}-for"

    if token.word in rules.MOR_WORDS_OVERRIDES:
        return rules.MOR_WORDS_OVERRIDES[token.word]

    new_tag = f"-{_tag}" if (_tag := transform_tag(token)) != "" else ""

    lemma = token.lemma

    # plural central pronouns to be lemmatized
    # as e.g. "my" or "náš" rather than forms of "já" or "můj"
    if token.word in rules.MOR_WORDS_LEMMA_OVERRIDES:
        lemma = rules.MOR_WORDS_LEMMA_OVERRIDES[token.word]

    # neologisms not to be lemmatized
    elif constants.tflag.neologism in flags:
        lemma = token.word

    return f"{pos_label}|{lemma}{new_tag}"


def mor_line(
    text: str, tokenizer: Tokenizer | None = None, tagger: Tagger | None = None
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

    flags: list[dict[constants.tflag,]] = []
    for word in tokenize_string(text, tokenizer):
        flag = {}
        if word.endswith(constants.PLACEHOLDER_NEOLOGISM):
            flag[constants.tflag.neologism] = True
        elif word.endswith(constants.PLACEHOLDER_FOREIGN):
            flag[constants.tflag.foreign] = True
        elif word.endswith(constants.PLACEHOLDER_INTERJECTION):
            flag[constants.tflag.interjection] = True
        flags.append(flag)

    text = (
        text.replace(constants.PLACEHOLDER_NEOLOGISM, "")
        .replace(constants.PLACEHOLDER_FOREIGN, "")
        .replace(constants.PLACEHOLDER_INTERJECTION, "")
    )

    tagged_tokens: list[Token] = tag_string(text, tagger)
    result: list[str] = []

    for i, token in enumerate(tagged_tokens):
        result.append(construct_mor_word(token, flags[i]))
    text = "%mor:\t" + " ".join(result)

    # formal adjustments to correct unwanted spaces created by tokenization
    text = text.replace("+ . . .", "+...").replace("+ / .", "+/.")

    return text


def annotate_filestream(
    source_fs,
    target_fs,
    tokenizer: Tokenizer = None,
    tagger: Tagger = None,
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
        line = line.strip(" \n")
        print(line, file=target_fs)
        line_plain_text = chat_to_plain_text(line)
        if line_plain_text and not line_plain_text in rules.SKIP_LINES:
            print(
                mor_line(line_plain_text, tokenizer, tagger),
                file=target_fs,
            )


def annotate_file(
    path_source: str,
    path_target: str,
    tokenizer: Tokenizer | None = None,
    tagger: Tagger | None = None,
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

    try:
        with open(path_source, "r", encoding="utf-8") as source_fs:
            with open(path_target, "w", encoding="utf-8") as target_fs:
                print(f"Annotate: {path_source}", file=sys.stderr)
                annotate_filestream(source_fs, target_fs, tokenizer, tagger)
    except IsADirectoryError:
        print(f"Skip\t: {path_source} (directory)", file=sys.stderr)
    except FileNotFoundError:
        print(f"Skip\t: {path_source} (not found)", file=sys.stderr)


def _handle_args(args):
    global _ecode

    if args.tagger:
        constants.TAGGER_PATH = args.tagger[0]

    if args.tokenizer:
        constants.TOKENIZER_TYPE = args.tokenizer[0]

    # take input from stdin
    if args.std:
        annotate_filestream(sys.stdin, sys.stdout)
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
            return

        # run file annotation
        for input_file, output_file in files:
            if not os.path.isdir(dname := os.path.dirname(output_file)):
                os.makedirs(dname)

            try:
                annotate_file(input_file, output_file)
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Add morphological annotation to a CHAT text file \
            according to the CoCzeFLA standards."
    )
    parser.add_argument(
        "-s",
        "--std",
        action="store_true",
        help="receive/print input/output on stdin/stdout",
    )
    parser.add_argument(
        "-o",
        "--outdir",
        nargs=1,
        type=str,
        help="directory where output files should be stored",
    )
    parser.add_argument(
        "-i",
        "--indir",
        nargs=1,
        type=str,
        help="take all .txt files from this directory as the input; \
            enabling this option overrides all inputfiles",
    )
    parser.add_argument(
        "-d",
        "--tokenizer",
        nargs=1,
        type=str,
        help="configure MorphoDiTa tokenizer type; overrides any tokenizer type \
            specified in constants.TOKENIZER_TYPE",
    )
    parser.add_argument(
        "-t",
        "--tagger",
        nargs=1,
        type=str,
        help="configure MorphoDiTa tagger; overrides any tagger specified in constants.TAGGER_PATH",
    )
    parser.add_argument("inputfiles", nargs="*", default=[])

    arguments = parser.parse_args(sys.argv[1:])
    _handle_args(arguments)

    exit(_ecode)
