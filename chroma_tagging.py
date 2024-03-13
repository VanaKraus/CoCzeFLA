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


"""
a function for using the MorphoDiTa tagger, see https://ufal.mff.cuni.cz/morphodita
the directory needs to be adjusted

example of use: tag("vidím Mařenku")
→ output = a list of Token objects: 
[Token(word='vidím', lemma='vidět', tag='VB-S---1P-AA---'),
 Token(word='Mařenku', lemma='Mařenka', tag='NNFS4-----A----')]

"""


def tag(text: str, tagger: Tagger = _get_tagger()) -> list[Token]:
    output = list(tagger.tag(text, convert="strip_lemma_id"))
    return output


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

example of use: pos_mor("NNFS4-----A----", "Mařenku", "Mařenka")
→ output: 'n:prop'

"""


def pos_mor(tag: str, word: str, lemma: str):
    if lemma in replacement_rules.MOR_POS_OVERRIDES:
        return replacement_rules.MOR_POS_OVERRIDES[lemma]

    result = ""
    if tag.startswith("Z"):
        result = "Z"
    elif tag.startswith("X"):
        result = "x"
    elif tag.startswith("N"):
        result = "n"
        if word == word.capitalize():  # proper nouns
            result = "n:prop"
    elif tag.startswith("A"):
        result = "adj"
        if tag.startswith("AC"):
            result = "adj:short"
        elif tag.startswith("AU"):
            result = "adj:poss"
    elif tag.startswith("P"):
        result = "pro"
        if tag.startswith("PD"):
            result = "pro:dem"
        elif tag.startswith("PP") or tag.startswith("PH") or tag.startswith("P5"):
            result = "pro:pers"
        elif (
            tag.startswith("P1")
            or tag.startswith("P9")
            or tag.startswith("PE")
            or tag.startswith("PJ")
        ):
            result = "pro:rel"
        elif tag.startswith("PS"):
            result = "pro:poss"
        elif tag.startswith("P4") or tag.startswith("PK") or tag.startswith("PQ"):
            result = "pro:rel/int"
        elif tag.startswith("PW"):
            result = "pro:neg"
        elif tag.startswith("PL") or tag.startswith("PZ"):
            result = "pro:indef"
        elif tag.startswith("P6") or tag.startswith("P7"):  # relfexive se, si...
            result = "pro:refl"

    elif tag.startswith("C"):
        result = "num"
        if tag.startswith("Cl") or tag.startswith("Cn"):
            result = "num:card"
        elif tag.startswith("Cr"):
            result = "num:ord"
        elif tag.startswith("Cv") or (word.endswith("krát") and lemma.endswith("krát")):
            result = "num:mult"
        elif tag.startswith("Ca"):
            result = "num:indef"

    elif tag.startswith("V"):
        result = "v"

    elif tag.startswith("D"):
        result = "adv"

    elif tag.startswith("R"):
        result = "prep"
    elif tag.startswith("J^"):
        result = "conj:coord"
    elif tag.startswith("J,"):
        result = "conj:sub"
    elif tag.startswith("J*"):
        result = "conj:coord"
    elif tag.startswith("T"):
        result = "part"
    elif tag.startswith("I"):
        result = "int"

    return result


def _get_default_gram_cat(
    category: str, tag: str = None, word: str = None, lemma: str = None
) -> str:
    _log(
        f"transform_tag: request default for {category} (tag: {tag}, word: {word}, lemma: {lemma})"
    )
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
    if (tag.startswith("V") and tag[10] == "N") or (
        word.startswith("ne") and not lemma.startswith("ne")
    ):
        neg = "neg"

    # verbs
    if tag.startswith("V"):
        if lemma in words.IMPERFECTIVE_VERBS:
            aspect = "impf"
        elif lemma in words.PERFECTIVE_VERBS:
            aspect = "pf"
        else:
            aspect = _get_default_gram_cat("aspect", tag, word, lemma)

        if tag[3] == "S":
            number = "SG"
        elif tag[3] == "P":
            number = "PL"
        # else: the value "–": infinitive, auxiliary "být" in the conditional form

        if tag.startswith("Vs"):
            voice = "pas"
        elif tag[11] == "A":
            voice = "akt"

        if tag[2] != "-":
            if tag[2] == "Y" or tag[2] == "M":
                gender = "M"
            elif tag[2] == "N":
                gender = "N"
            elif tag[2] == "F":
                gender = "F"
            else:
                gender = _get_default_gram_cat("gender", tag, word, lemma)

        # infinitive
        if tag.startswith("Vf"):
            form_type = "inf"

        # past participle
        elif tag.startswith("Vp"):
            tense = "past"
            # feminine participles in -la obligatorily singular
            if word.endswith("la") and gender == "F":
                number = "SG"

            if number is None:
                number = _get_default_gram_cat("number", tag, word, lemma)
            if voice is None:
                voice = _get_default_gram_cat("voice", tag, word, lemma)

        # passive participle
        elif tag.startswith("Vs"):
            if number is None:
                number = _get_default_gram_cat("number", tag, word, lemma)
            if voice is None:
                voice = _get_default_gram_cat("voice", tag, word, lemma)

        # if it is neither an infinitive nor a participle
        else:
            if tag[7] == "1" or tag[7] == "2" or tag[7] == "3":
                person = tag[7]

            if tag.startswith("Vc"):
                mood = "cond"
                voice = "akt"
            elif tag.startswith("Vi"):
                mood = "imp"
                voice = "akt"
            else:
                mood = "ind"
                if tag[8] == "P":
                    tense = "pres"
                elif tag[8] == "F":
                    tense = "futur"

            if number is None:
                number = _get_default_gram_cat("number", tag, word, lemma)

    elif (
        (
            tag.startswith("N")
            or tag.startswith("A")
            or tag.startswith("P")
            or tag.startswith("C")
        )
        and not tag.startswith("Cv")
        and not word.endswith("krát")
        and not lemma.endswith("krát")
    ):
        if tag[3] == "S" or lemma in ["kdo", "co", "se"]:
            number = "SG"
        elif tag[3] == "P" or tag[3] == "D":
            number = "PL"
        else:
            number = _get_default_gram_cat("number", tag, word, lemma)

        if tag[4] != "X":
            case = tag[4]
        else:
            case = _get_default_gram_cat("case", tag, word, lemma)

        if tag.startswith("NNM"):
            gender = "MA"
        elif tag.startswith("NNI"):
            gender = "MI"
        elif lemma == "co":
            gender = "N"
        elif tag[2] == "I" or tag[2] == "Y":
            gender = "M"
        elif tag[2] == "X":
            gender = _get_default_gram_cat("gender", tag, word, lemma)
        elif tag[2] != "-":
            gender = tag[2]

    if tag.startswith("A") or tag.startswith("D"):
        if tag[9] == "2":
            comp_deg = "CP"
        if tag[9] == "3":
            comp_deg = "SP"

    gram_categories = [
        form_type,
        case,
        person,
        number,
        mood,
        tense,
        voice,
        gender,
        aspect,
    ]

    # join grammatical categories into one string
    gr_joined = (
        _jnd
        if (_jnd := gr_delim.join([el for el in gram_categories if not el is None]))
        != ""
        else None
    )

    lex_categories = [comp_deg, neg, gr_joined]

    return lex_delim.join([el for el in lex_categories if not el is None])


def _construct_mor_word(token: Token, pos_label: str, flags: dict[constants.tflag,]):
    if pos_label == "Z":
        return token.lemma

    if constants.tflag.interjection in flags:
        return f"int|{token.word}"

    if token.word in replacement_rules.MOR_WORDS_HARDCODED:
        return replacement_rules.MOR_WORDS_HARDCODED[token.word]

    new_tag = (
        f"-{_tag}"
        if (_tag := transform_tag(token.tag, token.word, token.lemma)) != ""
        else ""
    )

    if constants.tflag.tag_extension in flags:
        new_tag += flags[constants.tflag.tag_extension]

    lemma = token.lemma

    # plural central pronouns to be lemmatized as e.g. "my" or "náš" rather than forms of "já" or "můj"
    if token.word in replacement_rules.MOR_WORDS_LEMMA_OVERRIDES:
        lemma = replacement_rules.MOR_WORDS_LEMMA_OVERRIDES[token.word]

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
            flag[constants.tflag.tag_extension] = "-neo"
        elif word.endswith(constants.PLACEHOLDER_CIZ):
            flag[constants.tflag.tag_extension] = "-ciz"
        elif word.endswith(constants.PLACEHOLDER_INTERJECTION):
            flag[constants.tflag.interjection] = True
        flags.append(flag)

    text = (
        text.replace(constants.PLACEHOLDER_NEOLOGISM, "")
        .replace(constants.PLACEHOLDER_CIZ, "")
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

    # small formal adjustments
    text = text.replace(", .", ".")
    text = text.replace("\t, ", "\t")
    text = text.replace("+ . . .", "+…").replace("+ …", "+…").replace("+ / .", "+/.")

    return text


"""
a function for small formal adjustments WITHIN THE MAIN LINE, i.e., this is not a necessary part of the morphological analysis
→ adds a space before ".", "!" and "?" on the main line
→ changes +... to +…

"""


def mezera_interpunkce(line):
    if line.endswith("+..."):
        line = line[:-4] + "+…"
    elif line.endswith("+…"):
        pass
    elif line.endswith("+/."):
        pass
    elif line.endswith(".") and line.endswith(" .") == False:
        line = line[:-1] + " ."
    elif line.endswith("?") and line.endswith(" ?") == False:
        line = line[:-1] + " ?"
    elif line.endswith("!") and line.endswith(" !") == False:
        line = line[:-1] + " !"
    return line


""" 
this function takes a file ("path" in the input) and creates a new file ("path_goal"),
which includes the added morphological tiers

example of use: file_to_file("./test_files/aneta.txt", "./test_files/aneta_result.txt")

"""


def annotate_file(path, path_goal, tagger):
    with open(path, "r") as file:
        with open(path_goal, "a") as file_goal:
            annotate_filestream(file, file_goal, tagger)


def annotate_filestream(
    source_fs,
    target_fs,
    tagger: Tagger = _get_tagger(),
    tokenizer: Tokenizer = _get_tokenizer(),
):
    for line in source_fs:
        line = line.strip(" \n")
        print(mezera_interpunkce(line), file=target_fs)
        line_plain_text = chat_to_plain_text(line)
        if not line_plain_text in [
            None,
            ".",
            "0 .",
            "nee .",
            "emem .",
            "mhm .",
            "hm .",
        ]:
            print(
                mor_line(line_plain_text, tagger, tokenizer),
                file=target_fs,
            )


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
