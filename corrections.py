#!/usr/bin/env python3

import argparse
import logging
import re
import sys
from typing import Self, TextIO, Callable

from nltk.corpus import PlaintextCorpusReader

import annot_util.replacement_rules as replrules
from annot_util.conversions import chat_to_plain_text

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ChatToken:
    word: str
    pos: str | None = None
    lemma: str | None = None
    cats: str | None = None

    def __init__(self, word: str, mor_word: str) -> None:
        self.word = word

        if word not in replrules.SKIP_LINES:
            m = re.match(
                r"([a-z:_]+)\|([a-zA-ZáäąčćďéěëęíłňńóöřšśťůúüýžźżÁÄĄČĆĎÉĚËĘÍŁŇŃÓÖŘŠŚŤŮÚÜÝŽŹŻ]+)(-([a-zA-Z0-9&]+))?",
                mor_word,
            )
            if not m:
                raise ValueError(f"{mor_word=} is not a valid MOR word")

            self.pos = m.group(1)
            self.lemma = m.group(2)
            self.cats = m.group(4)

    @property
    def mor_word(self) -> str:
        if not (self.pos or self.lemma):
            return self.word

        res = f"{self.pos}|{self.lemma}"
        if self.cats:
            res += f"-{self.cats}"
        return res


class AnnotFile:
    lines: list[str]

    def load(self, fs: TextIO) -> Self:
        self.lines = [l.strip("\n") for l in fs.readlines()]
        logging.info(f"loaded {len(self.lines)} lines")
        return self

    def save(self, fs: TextIO):
        logging.info(f"saving {len(self.lines)} lines")
        for line in self.lines:
            print(line, file=fs)

    def apply(self, *pred: Callable[[list[str]], list[str]]) -> Self:
        for p in pred:
            self.lines = p(self.lines)
        return self


def mor_parse(main_line: str, mor_line: str) -> list[ChatToken]:
    logger.debug("mor_parse called")

    if not re.match(r"\*[A-Z]{3}:\t", main_line):
        raise ValueError("Main line provided isn't a main line")
    if not mor_line.startswith("%mor:\t"):
        raise ValueError(f"MOR line provided isn't a MOR line ({mor_line=})")

    main_content = chat_to_plain_text(main_line)
    if not main_content:
        raise ValueError("main_line is empty")

    mor_content = mor_line.split("\t")[1]

    main_content_list = main_content.split(" ")
    mor_content_list = mor_content.split(" ")

    if len(main_content_list) != len(mor_content_list):
        raise ValueError("main line and MOR line length mismatch")

    res = []
    for i in range(len(main_content_list)):
        res += [ChatToken(main_content_list[i], mor_content_list[i])]

    logger.debug(f"mor_parse: {len(res)} tokens")

    return res


# CORRECTORS


def part_nogram(lines: list[str]) -> list[str]:
    res = []

    for line in lines:
        if line.startswith("%mor"):
            res += [re.sub(r"(\spart\|co)-[-&A-Za-z0-9]+", r"\1", line)]
        else:
            res += [line]

    return res


def _apply_token_modifier(
    lines: list[str], token_modifier: Callable[[ChatToken], ChatToken]
) -> list[str]:
    logger.debug(f"_apply_token_modifier called on {len(lines)} lines")

    res = []
    i = 0

    while i < len(lines):
        if re.match(r"\*[A-Z]{3}:\t", lines[i]):
            main_line = lines[i]
            mor_line = lines[i + 1]

            tokens = mor_parse(main_line, mor_line)

            for j in range(len(tokens)):
                tokens[j] = token_modifier(tokens[j])

            res += [lines[i]]
            res += [f"%mor:\t" + " ".join(t.mor_word for t in tokens)]

            i += 1
        else:
            res += [lines[i]]

        i += 1

    logger.debug(f"_apply_token_modifier: returning {len(res)} lines")
    return res


def vcop(lines: list[str]) -> list[str]:
    logger.debug("vcop: called")

    def _modif(token: ChatToken) -> ChatToken:
        if (
            token.lemma
            and token.lemma in replrules.MOR_POS_OVERRIDES
            and token.word in replrules.MOR_POS_OVERRIDES[token.lemma]
            and replrules.MOR_POS_OVERRIDES[token.lemma][token.word] == "v:cop"
        ):
            token.pos = replrules.MOR_POS_OVERRIDES[token.lemma][token.word]
        return token

    return _apply_token_modifier(lines, _modif)


def adj_adv_compdeg(lines: list[str]):
    logger.debug("adj_adv_compdeg: called")

    def _modif(token: ChatToken) -> ChatToken:
        if token.lemma and token.lemma in replrules._ADJ_ADV_COMPDEG_LEMMA_OVERRIDES:
            token.lemma = replrules._ADJ_ADV_COMPDEG_LEMMA_OVERRIDES[token.lemma]

        return token

    return _apply_token_modifier(lines, _modif)


# LOGIC


def build_predicate_list(args) -> list[Callable[[list[str]], list[str]]]:
    res = []

    if args.vcop:
        res += [vcop]
    if args.part_nogram:
        res += [part_nogram]
    if args.adj_adv_compdeg:
        res += [adj_adv_compdeg]

    return res


def main(args):
    predicates = build_predicate_list(args)

    if args.std:
        AnnotFile().load(sys.stdin).apply(*predicates).save(sys.stdout)

    # TODO: implement PlainTextCorpusReader


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--indir", type=str, nargs=1, help="input directory")
    parser.add_argument("-o", "--outdir", type=str, nargs=1, help="output directory")
    parser.add_argument(
        "-s",
        "--std",
        action="store_true",
        help="receive/print input/output on stdin/stdout",
    )

    parser.add_argument(
        "--vcop",
        action="store_true",
        help="annotate selected instances of the verb být as v:cop",
    )
    parser.add_argument(
        "--part-nogram",
        action="store_true",
        help="remove grammatical categories from the word co when annotated as part",
    )
    parser.add_argument(
        "--adj-adv-compdeg",
        action="store_true",
        help="use a positive form as lemma for adjectives and adverbs",
    )

    args = parser.parse_args(sys.argv[1:])

    logger.info(args)

    main(args)
