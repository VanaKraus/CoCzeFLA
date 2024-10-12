#!/usr/bin/env python3

"""the script for the morphological analysis of the longitudinal corpus of \
    spoken Czech child-adult interactions

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

import sys
import os
from typing import Any, Generator, Optional, TextIO

from corpy.morphodita import Tagger, Tokenizer
from nltk.corpus import PlaintextCorpusReader

import argument_handling as ahandling
from annot_util import constants, replacement_rules as rules
from annot_util.constants import tflag
from annot_util.conversions import (
    generate_mor_pos_label,
    generate_mor_tag,
    chat_to_plain_text,
    ChatToPlainTextConversionError,
)
from annot_util.flagged_token import FlaggedToken
from annot_util.morphodita_tools import (
    get_tagger,
    get_tokenizer,
    tag_string,
    tokenize_string,
)


def construct_mor_word(token: FlaggedToken) -> str:
    """Create an entire %mor morphological annotation for the given token.

    Args:
        token (Token): MorphoDiTa token.

    Returns:
        str
    """
    pos_label = generate_mor_pos_label(token)

    if pos_label == "Z":
        return "cm|cm" if token.lemma == "," else token.lemma

    if tflag.interjection in token.flags:
        return f"int|{token.word}"

    if tflag.neologism in token.flags:
        return f"x|{token.word}-neo"

    if tflag.foreign in token.flags:
        return f"x|{token.word}-for"

    if token.word in rules.MOR_WORDS_OVERRIDES:
        return rules.MOR_WORDS_OVERRIDES[token.word]

    new_tag = f"-{_tag}" if (_tag := generate_mor_tag(token)) != "" else ""

    lemma = token.lemma

    # some MorfFlex lemmas to be replaced by ours
    if token.lemma in rules.MOR_MLEMMAS_LEMMA_OVERRIDES:
        lemma = rules.MOR_MLEMMAS_LEMMA_OVERRIDES[token.lemma]

    # some words have their lemmas hardcoded
    if token.word in rules.MOR_WORDS_LEMMA_OVERRIDES:
        lemma = rules.MOR_WORDS_LEMMA_OVERRIDES[token.word]

    # neologisms not to be lemmatized
    elif tflag.neologism in token.flags:
        lemma = token.word

    return f"{pos_label}|{lemma}{new_tag}"


def filter_tokens(tokens: list[FlaggedToken]) -> list[FlaggedToken]:
    """Filter for tokens which should appear on the MOR line.

    Args:
        tokens (list[FlaggedToken])

    Returns:
        list[FlaggedToken]: A new list. Sublist of `tokens`.
    """
    res: list[FlaggedToken] = []
    for token in tokens:
        if not token.word in ("“", "”"):
            res.append(token)
    return res


def mor_line(
    text: str,
    tokenizer: Optional[Tokenizer] = None,
    tagger: Optional[Tagger] = None,
    guesser: bool = False,
) -> str:
    """Create a %mor line from an input text.

    Args:
        text (str): Plain line (stripped of the speaker ID and other annotation). \
            Words with special annotation are expected to use their appropriate \
            placeholders (`constants.PLACEHOLDER_*`).
        tokenizer (Tokenizer, optional): MorphoDiTa tokenizer to use. \
            When tokenizer == None, _get_tokenizer() is used. Defaults to None.
        tagger (Tagger, optional): MorphoDiTa tagger to use. \
            When tagger == None, _get_tagger() is used. Defaults to None.
        guesser (bool, optional): use MorphoDiTa's morphological guesser. \
            Defaults to False.

    Returns:
        str: %mor line.
    """
    if not tokenizer:
        tokenizer = get_tokenizer()
    if not tagger:
        tagger = get_tagger()

    flags: list[dict[tflag, Any]] = []
    for i, word in enumerate(
        tokens := [str(token) for token in tokenize_string(text, tokenizer)]
    ):
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

    tagged_tokens: list[FlaggedToken] = [
        FlaggedToken.from_token(token, flags[i])
        for i, token in enumerate(tag_string(text, tagger, guesser))
    ]
    tagged_tokens = filter_tokens(tagged_tokens)
    result: list[str] = []

    for i, token in enumerate(tagged_tokens):
        result.append(construct_mor_word(token))
    text = "%mor:\t" + " ".join(result)

    # formal adjustments to correct unwanted spaces created by tokenization
    text = text.replace("+ . . .", "+...").replace("+ / .", "+/.")

    return text


def process_line(
    line: str,
    tokenizer: Optional[Tokenizer] = None,
    tagger: Optional[Tagger] = None,
    guesser: bool = False,
) -> Generator[str, None, None]:
    """Process single line.

    Args:
        line (str)
        tokenizer (Tokenizer, optional): MorphoDiTa tokenizer to use. \
            When tokenizer == None, _get_tokenizer() is used. Defaults to None.
        tagger (Tagger, optional): MorphoDiTa tagger to use. \
            When tagger == None, _get_tagger() is used. Defaults to None.
        guesser (bool, optional): use MorphoDiTa's morphological guesser. \
            Defaults to False.

    Yields:
        Generator[str, None, None]: Output line(s) generated.
    """
    if not tokenizer:
        tokenizer = get_tokenizer()
    if not tagger:
        tagger = get_tagger()

    line = line.strip(" \n")
    yield line

    if line.startswith(("@", "%")):
        return

    line_plain_text = chat_to_plain_text(line)
    if line_plain_text and not line_plain_text in rules.SKIP_LINES:
        yield mor_line(line_plain_text, tokenizer, tagger, guesser)


def annotate_filestream(
    source_fs: TextIO,
    target_fs: TextIO,
    tokenizer: Optional[Tokenizer] = None,
    tagger: Optional[Tagger] = None,
    guesser: bool = False,
):
    """Add morphological annotation to filestream.

    Args:
        source_fs (TextIO): Source filestream.
        target_fs (TextIO): Target filestream.
        tokenizer (Tokenizer, optional): MorphoDiTa tokenizer to use. \
            Defaults to _get_tokenizer().
        tagger (Tagger, optional): MorphoDiTa tagger to use. Defaults to _get_tagger().
        guesser (bool, optional): use MorphoDiTa's morphological guesser. \
            Defaults to False.
    """
    if not tokenizer:
        tokenizer = get_tokenizer()
    if not tagger:
        tagger = get_tagger()

    for line in source_fs:
        for out in process_line(line, tokenizer, tagger, guesser):
            print(out, file=target_fs)


def annotate_file(
    path_source: str,
    path_target: str,
    tokenizer: Optional[Tokenizer] = None,
    tagger: Optional[Tagger] = None,
    guesser: bool = False,
):
    """Add morphological annotation to single file.

    Args:
        path_source (str): Path to the source file.
        path_target (str): Path to the target file. Existing files will be overwritten.
        tokenizer (Tokenizer, optional): MorphoDiTa tokenizer to use. \
            When tokenizer == None, _get_tokenizer() is used. Defaults to None.
        tagger (Tagger, optional): MorphoDiTa tagger to use. \
            When tagger == None, _get_tagger() is used. Defaults to None.
        guesser (bool, optional): use MorphoDiTa's morphological guesser. \
            Defaults to False.
    """

    if not tokenizer:
        tokenizer = get_tokenizer()
    if not tagger:
        tagger = get_tagger()

    with open(path_source, "r", encoding="utf-8") as source_fs:
        with open(path_target, "w", encoding="utf-8") as target_fs:
            print(f"Annotate: {path_source} -> {path_target}", file=sys.stderr)
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

        print(f"arguments: {arguments}", file=sys.stderr)
    else:
        arguments = ahandling.argument_walkthrough(req_arguments)

    ECODE = _handle_args(arguments)

    sys.exit(ECODE)
