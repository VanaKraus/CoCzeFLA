#!/usr/bin/env python3

""" 
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

import constants
import replacement_rules
import word_definitions as words

from corpy.morphodita import Tagger, Token, Tokenizer

import argparse
import re
import sys
import os

_verbose = False


def _log(message: str):
    """Log a message to stderr. Requires _verbose == True

    Args:
        message (str): message to be logged
    """
    if _verbose:
        print(message, file=sys.stderr)


# cached tagger and tokenizer
_taggers = {}
_tokenizers = {}


def _get_tagger(path: str = constants.TAGGER_PATH) -> Tagger:
    """Get tagger instance and cache it.

    Args:
        path (str, optional): Path to MorfFlex .tagger file. Defaults to constants.TAGGER_PATH.

    Returns:
        Tagger: Tagger instance.
    """
    global _taggers

    if path in _taggers:
        return _taggers[path]
    else:
        result = Tagger(path)
        _taggers[path] = result
        return result


def _get_tokenizer(type: str = constants.TOKENIZER_TYPE) -> Tokenizer:
    """Get tokenizer instance and cache it.

    Args:
        type (str, optional): MorphoDiTa tokenizer type. Defaults to constants.TOKENIZER_TYPE.

    Returns:
        Tokenizer: Tokenizer instance.
    """
    global _tokenizers

    if type in _tokenizers:
        return _tokenizers[type]
    else:
        result = Tokenizer(type)
        _taggers[type] = result
        return result


def tag(text: str, tagger: Tagger = _get_tagger()) -> list[Token]:
    """Tag text using MorphoDiTa tagger.

    Args:
        text (str): Text to be tagged.
        tagger (Tagger, optional): Tagger to tag the text with. Defaults to _get_tagger().

    Returns:
        list[Token]
    """
    output = list(tagger.tag(text, convert="strip_lemma_id"))
    return output


def tokenize(text: str, tokenizer: Tokenizer = _get_tokenizer()) -> list[str]:
    """Tokenize text using MorphoDiTa tokenizer.

    Args:
        text (str): Text to be tokenized.
        tokenizer (Tokenizer, optional): Tokenizer to tokenize the text with. Defaults to _get_tokenizer().

    Returns:
        list[str]: _description_
    """
    return list(tokenizer.tokenize(text))


def chat_to_plain_text(chat_line: str) -> str | None:
    """Transform a line in CHAT format to plain text.

    Args:
        chat_line (str): Line in CHAT format.

    Returns:
        str | None: Line in plain text. Return None when the line is a comment or annotation.
    """
    if chat_line == "" or chat_line.startswith(("@", "%")):
        return None

    result = chat_line

    for rule in replacement_rules.CHAT_TO_PLAIN_TEXT:
        if result == "":
            break

        result = re.sub(rule[0], rule[1], result)

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
    if lemma in replacement_rules.MOR_POS_OVERRIDES:
        return replacement_rules.MOR_POS_OVERRIDES[lemma]

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

    tag, word, lemma = token.tag, token.word, token.lemma

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
        # aspect
        if lemma in words.IMPERFECTIVE_VERBS:
            aspect = "impf"
        elif lemma in words.PERFECTIVE_VERBS:
            aspect = "pf"
        else:
            aspect = _get_default_gram_cat("aspect")

        # gender
        if tag[2] in ("I", "M", "Y"):
            gender = "M"
        elif tag[2] == "N":
            gender = "N"
        elif tag[2] == "F":
            gender = "F"
        elif tag[2] != "-":
            gender = _get_default_gram_cat("gender")

        # number
        if tag[3] == "S":
            number = "SG"
        elif tag[3] == "P":
            number = "PL"
        # else: the value "–": infinitive, auxiliary "být" in the conditional form

        # passive
        if tag[11] == "P":
            voice = "pas"
        # active
        elif tag[11] == "A":
            voice = "akt"

        match tag[1]:
            # infinitive
            case "f":
                form_type = "inf"

            # past participle
            case "p":
                tense = "past"

                if number is None:
                    number = _get_default_gram_cat("number")

            # passive participle
            case "s":
                if number is None:
                    number = _get_default_gram_cat("number")

            # if it's neither an infinitive nor a participle
            case _:
                if tag[7] in ("1", "2", "3"):
                    person = tag[7]

                if tag.startswith("Vc"):
                    mood = "cond"
                elif tag.startswith("Vi"):
                    mood = "imp"
                elif tag.startswith("VB"):
                    mood = "ind"
                    if tag[8] == "P":
                        tense = "pres"
                    elif tag[8] == "F":
                        tense = "futur"
                # else: transgressive

                if number is None:
                    number = _get_default_gram_cat("number")

    # nouns, adjectives, pronouns, numerals and not multiplicative numerals
    elif tag[0] in ("N", "A", "P", "C") and not tag.startswith("Cv"):
        if tag[3] == "S":
            number = "SG"
        elif tag[3] in ("P", "D"):
            number = "PL"
        else:
            number = _get_default_gram_cat("number")

        if tag[4] != "X":
            case = tag[4]
        else:
            case = _get_default_gram_cat("case")

        if tag.startswith("NNM"):
            gender = "MA"
        elif tag.startswith("NNI"):
            gender = "MI"
        elif tag[2] in ("I", "Y"):
            gender = "M"
        elif tag[2] != "-":
            gender = _get_default_gram_cat("gender")

    if tag[0] in ("A", "D"):
        if tag[9] == "2":  # comparative
            comp_deg = "CP"
        if tag[9] == "3":  # superlative
            comp_deg = "SP"

    # special cases
    if lemma == "co":
        gender = "N"

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


def construct_mor_word(token: Token, flags: dict[constants.tflag,] = {}) -> str:
    """Create an entire %mor morphological annotation for the given token.

    Args:
        token (Token): MorphoDiTa token.
        flags (dict[constants.tflag,]): Token flags of token.
        flags (dict[constants.tflag,], optional): Token flags of `token`. Defaults to {}.

    Returns:
        str
    """
    pos_label = pos_mor(token)

    if pos_label == "Z":
        return token.lemma

    if constants.tflag.interjection in flags:
        return f"int|{token.word}"

    if token.word in replacement_rules.MOR_WORDS_OVERRIDES:
        return replacement_rules.MOR_WORDS_OVERRIDES[token.word]

    new_tag = f"-{_tag}" if (_tag := transform_tag(token)) != "" else ""

    if constants.tflag.neologism in flags:
        new_tag += "-neo"
    elif constants.tflag.foreign in flags:
        new_tag += "-for"

    lemma = token.lemma

    # plural central pronouns to be lemmatized as e.g. "my" or "náš" rather than forms of "já" or "můj"
    if token.word in replacement_rules.MOR_WORDS_LEMMA_OVERRIDES:
        lemma = replacement_rules.MOR_WORDS_LEMMA_OVERRIDES[token.word]

    # neologisms not to be lemmatized
    elif constants.tflag.neologism in flags:
        lemma = token.word

    return f"{pos_label}|{lemma}{new_tag}"


def mor_line(
    text: str, tokenizer: Tokenizer = _get_tokenizer(), tagger: Tagger = _get_tagger()
) -> str:
    """Create a %mor line from an input text.

    Args:
        text (str): Plain line (stripped of the speaker ID and other annotation). Words with special annotation are expected to use their appropriate placeholders (`constants.PLACEHOLDER_*`).
        tokenizer (Tokenizer, optional): MorphoDiTa tokenizer to use. Defaults to _get_tokenizer().
        tagger (Tagger, optional): MorphoDiTa tagger to use. Defaults to _get_tagger().

    Returns:
        str: %mor line.
    """
    flags: list[dict[constants.tflag,]] = []
    for word in tokenize(text, tokenizer):
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

    tagged_tokens: list[Token] = tag(text, tagger)
    result: list[str] = []

    for i in range(len(tagged_tokens)):
        result.append(construct_mor_word(tagged_tokens[i], flags[i]))
    text = "%mor:\t" + " ".join(result)

    # formal adjustments to correct unwanted spaces created by tokenization
    text = text.replace("+ . . .", "+...").replace("+ / .", "+/.")

    return text


def annotate_filestream(
    source_fs,
    target_fs,
    tokenizer: Tokenizer = _get_tokenizer(),
    tagger: Tagger = _get_tagger(),
):
    """Add morphological annotation to filestream.

    Args:
        source_fs: Source filestream.
        target_fs: Target filestream.
        tokenizer (Tokenizer, optional): MorphoDiTa tokenizer to use. Defaults to _get_tokenizer().
        tagger (Tagger, optional): MorphoDiTa tagger to use. Defaults to _get_tagger().
    """
    for line in source_fs:
        line = line.strip(" \n")
        print(line, file=target_fs)
        line_plain_text = chat_to_plain_text(line)
        if line_plain_text and not line_plain_text in replacement_rules.SKIP_LINES:
            print(
                mor_line(line_plain_text, tokenizer, tagger),
                file=target_fs,
            )


def annotate_file(
    path: str,
    path_goal: str,
    tokenizer: Tokenizer = _get_tokenizer(),
    tagger: Tagger = _get_tagger(),
):
    """Add morphological annotation to single file.

    Args:
        path (str): Path to the source file.
        path_goal (str): Path to the target file. Existing files will be overwritten.
        tokenizer (Tokenizer, optional): MorphoDiTa tokenizer to use. Defaults to _get_tokenizer().
        tagger (Tagger, optional): MorphoDiTa tagger to use. Defaults to _get_tagger().
    """
    with open(path, "r") as file:
        with open(path_goal, "w") as file_goal:
            annotate_filestream(file, file_goal, tokenizer, tagger)


"""
to process all corpus files within a folder with the function file_to_file(), the following code was used
(the folder here was named "Sara" and included all corpus files for the child nicknamed "Sara")
(all the new files will be found in a new folder, titled "Sara_tagged")

"""


def _handle_args(args):
    global _verbose

    if args.verbose:
        _verbose = True

    if args.std:
        annotate_filestream(sys.stdin, sys.stdout)
    elif args.outdir:
        if len(args.inputfiles) == 0:
            print(
                "Please specify your input files. See --help for more.", file=sys.stderr
            )
            return

        if not os.path.isdir(args.outdir[0]):
            os.makedirs(args.outdir[0])

        for file in args.inputfiles:
            print(file, file=sys.stderr)
            target_path = os.path.join(args.outdir[0], os.path.basename(file))
            annotate_file(file, target_path)
    else:
        print(
            "An output directory needs to be specified. See --help for more.",
            file=sys.stderr,
        )


def main():
    # TODO: review
    parser = argparse.ArgumentParser(
        description="Add morphological annotation according to the CoCzeFLA standards to a text file. REVIEW"
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
    parser.add_argument("inputfiles", nargs="*", default=[])
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="print runtime messages to stderr; if disabled, no logging is done",
    )

    args = parser.parse_args(sys.argv[1:])
    _handle_args(args)


if __name__ == "__main__":
    main()
