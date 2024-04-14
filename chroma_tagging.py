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
    if _verbose:
        print(message, file=sys.stderr)


_tagger = None
_tokenizer = None


def _get_tagger() -> Tagger:
    global _tagger
    if _tagger is None:
        _tagger = Tagger(constants.TAGGER_PATH)
    return _tagger


def _get_tokenizer() -> Tokenizer:
    global _tokenizer
    if _tokenizer is None:
        _tokenizer = Tokenizer(constants.TOKENIZER_TYPE)
    return _tokenizer


def tag(text: str, tagger: Tagger = _get_tagger()) -> list[Token]:
    output = list(tagger.tag(text, convert="strip_lemma_id"))
    return output


"""
a function for using the MorphoDiTa tagger, see https://ufal.mff.cuni.cz/morphodita
the directory needs to be adjusted

example of use: tag("vidím Mařenku")
→ output = a list of Token objects: 
[Token(word='vidím', lemma='vidět', tag='VB-S---1P-AA---'),
 Token(word='Mařenku', lemma='Mařenka', tag='NNFS4-----A----')]

"""


def tokenize(text: str, tokenizer: Tokenizer = _get_tokenizer()) -> list[str]:
    return list(tokenizer.tokenize(text))


"""
this function takes a corpus line in the CHAT (CHILDES) format as the input and transforms it into plain text
if the line is not to be tagged (e.g. contains only a hesitation sound), the function returns None instead

example of input: "*MOT:	toho &vybavová vybarvování."
example of output: 'toho vybarvování .'

"""


def chat_to_plain_text(chat_line: str) -> str | None:
    if chat_line == "" or chat_line.startswith(("@", "%")):
        return None

    result = chat_line

    for rule in replacement_rules.CHAT_TO_PLAIN_TEXT:
        if result == "":
            break

        result = re.sub(rule[0], rule[1], result)

    return result


"""
input: (tag, word, lemma) provided in the Token object by tag()
extracts the POS information from the tag and returns the POS value in the MOR format
lemma in the input as well, because of the tagging of plural invariable nouns
word in the input as well, because of the tagging of proper names

For MorphoDiTa manual see: https://ufal.mff.cuni.cz/techrep/tr64.pdf

example of use: pos_mor("NNFS4-----A----", "Mařenku", "Mařenka")
→ output: 'n:prop'

"""


def pos_mor(tag: str, word: str, lemma: str):
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
    return constants.EMPTY_GRAM_CAT_DEFAULT[category]


""" 
input: (tag, word, lemma) provided in the Token object by tag()
extracts the morphological information from the tag and returns the morphological tag in the MOR format
lemma & word in the input as well, because of the tagging of negation and verbal aspect

example of use: transform_tag("NNFS4-----A----", "Mařenku", "Mařenka")
→ output: '4&SG&F'

"""


def transform_tag(tag, word, lemma):
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


def _construct_mor_word(token: Token, pos_label: str, flags: dict[constants.tflag,]):
    if pos_label == "Z":
        return token.lemma

    if constants.tflag.interjection in flags:
        return f"int|{token.word}"

    if token.word in replacement_rules.MOR_WORDS_OVERRIDES:
        return replacement_rules.MOR_WORDS_OVERRIDES[token.word]

    new_tag = (
        f"-{_tag}"
        if (_tag := transform_tag(token.tag, token.word, token.lemma)) != ""
        else ""
    )

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


"""
this function processes an input text
the input text is supposed to be the result of the function chat_to_plain_text()
the function uses the functions pos_mor() and transform_tag()
this function assures that tagged_tokens with the placeholders starting with the string "bacashooga" are treated as required

"""


def mor_line(
    text, tagger: Tagger = _get_tagger(), tokenizer: Tokenizer = _get_tokenizer()
):
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
    pos_labels: list[str] = [
        pos_mor(token.tag, token.word, token.lemma) for token in tagged_tokens
    ]
    result: list[str] = []

    for i in range(len(tagged_tokens)):
        result.append(_construct_mor_word(tagged_tokens[i], pos_labels[i], flags[i]))
    text = "%mor:\t" + " ".join(result)

    # formal adjustments to correct spaces created by tokenization
    text = text.replace("+ . . .", "+...").replace("+ / .", "+/.")

    return text


def annotate_filestream(
    source_fs,
    target_fs,
    tagger: Tagger = _get_tagger(),
    tokenizer: Tokenizer = _get_tokenizer(),
):
    for line in source_fs:
        line = line.strip(" \n")
        print(line, file=target_fs)
        line_plain_text = chat_to_plain_text(line)
        if line_plain_text and not line_plain_text in replacement_rules.SKIP_LINES:
            print(
                mor_line(line_plain_text, tagger, tokenizer),
                file=target_fs,
            )


""" 
this function takes a file ("path" in the input) and creates a new file ("path_goal"),
which includes the added morphological tiers

example of use: file_to_file("./test_files/aneta.txt", "./test_files/aneta_result.txt")

"""


def annotate_file(path, path_goal, tagger):
    with open(path, "r") as file:
        with open(path_goal, "a") as file_goal:
            annotate_filestream(file, file_goal, tagger)


"""
to process all corpus files within a folder with the function file_to_file(), the following code was used
(the folder here was named "Sara" and included all corpus files for the child nicknamed "Sara")
(all the new files will be found in a new folder, titled "Sara_tagged")

"""


def handle_args(args):
    global _verbose

    if args.verbose:
        _verbose = True

    if args.std:
        annotate_filestream(sys.stdin, sys.stdout, _get_tagger())
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
            annotate_file(file, target_path, _get_tagger())
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
    handle_args(args)


if __name__ == "__main__":
    main()
