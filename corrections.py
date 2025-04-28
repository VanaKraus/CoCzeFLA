#!/usr/bin/env python3

import argparse
import logging
import re
import os
import sys
from typing import TextIO, Callable

from nltk.corpus import PlaintextCorpusReader

import annot_util.replacement_rules as replrules
from annot_util.conversions import chat_to_plain_text
from annot_util.morphodita_tools import tag_string
from annotation import filter_tokens, FlaggedToken

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
                r"([a-z:_]+)\|([a-zA-Z0-9áäąčćďéěëęíłňńóöřšśťůúüýžźżÁÄĄČĆĎÉĚËĘÍŁŇŃÓÖŘŠŚŤŮÚÜÝŽŹŻ_]+)(-([a-zA-Z0-9&_\-]+))?",
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

    def load(self, fs: TextIO) -> "AnnotFile":
        self.lines = [l.strip("\n") for l in fs.readlines()]
        logging.info(f"loaded {len(self.lines)} lines")
        return self

    def save(self, fs: TextIO):
        logging.info(f"saving {len(self.lines)} lines")
        for line in self.lines:
            print(line, file=fs)

    def apply(self, *pred: Callable[[list[str]], list[str]]) -> "AnnotFile":
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

    # an ugly workaround to simulate how tokens from the main line would get removed
    main_fake_flagged_tokens = [FlaggedToken(s, "", "") for s in main_content_list]
    main_fake_flagged_tokens_filtered = filter_tokens(main_fake_flagged_tokens)

    # create a map telling which tokens to keep
    mp: list[bool] = []
    j = 0  # iterator for the filtered tokens
    for t in main_fake_flagged_tokens:
        matching = main_fake_flagged_tokens_filtered[j].word == t.word
        mp += [matching]
        j += int(matching)

    main_content_list = [main_content_list[i] for i in range(len(mp)) if mp[i]]

    if len(main_content_list) != len(mor_content_list):
        raise ValueError(
            f"main line and MOR line length mismatch\n\n"
            + f"{len(main_content_list)=}\n{len(mor_content_list)=}\n\n"
            + f"{main_line=}\n{mor_line=}\n\n{main_content_list=}\n{mor_content_list=}"
        )

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

    while i < len(lines) - 1:
        if re.match(r"\*[A-Z]{3}:\t", (main_line := lines[i])) and (
            mor_line := lines[i + 1]
        ).startswith("%mor:\t"):
            tokens = mor_parse(main_line, mor_line)

            for j in range(len(tokens)):
                tokens[j] = token_modifier(tokens[j])

            res += [lines[i]]
            res += [f"%mor:\t" + " ".join(t.mor_word for t in tokens)]

            i += 1
        else:
            res += [lines[i]]

        i += 1

    if i < len(lines):
        res += [lines[i]]

    logger.debug(f"_apply_token_modifier: returning {len(res)} lines")
    return res


def people_lemma(lines: list[str]) -> list[str]:
    logger.debug("people_lemma: called")

    def _modif(token: ChatToken) -> ChatToken:
        if token.lemma == "lidé":
            token.lemma = "člověk"
        return token

    return _apply_token_modifier(lines, _modif)


def demonstrative_variants(lines: list[str]) -> list[str]:
    logger.debug("determiner_variants: called")

    def _modif(token: ChatToken) -> ChatToken:
        if token.lemma == "ten":
            morph_tokens = tag_string(token.word)
            assert (
                len(morph_tokens) == 1
            ), f"tag_string produced {len(morph_tokens)} tokens instead of one"
            token.lemma = morph_tokens[0].lemma
        return token

    return _apply_token_modifier(lines, _modif)


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
    predicates: dict[str, Callable[[list[str]], list[str]]] = {
        "vcop": vcop,
        "part_nogram": part_nogram,
        "adj_adv_compdeg": adj_adv_compdeg,
        "dem_lemma": demonstrative_variants,
        "people_lemma": people_lemma,
    }

    res = (
        list(predicates.values())
        if args.all
        else [p for k, p in predicates.items() if args.__dict__[k]]
    )

    logger.debug(f"build_predicate_list:{res}")
    if len(res) == 0:
        logger.info(f"build_predicate_list:returning 0 predicates")

    return res


def main(args):
    predicates = build_predicate_list(args)

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    if args.std:
        AnnotFile().load(sys.stdin).apply(*predicates).save(sys.stdout)

    if args.indir and args.outdir:
        input_dir = args.indir[0]
        output_dir = args.outdir[0]

        reader = PlaintextCorpusReader(input_dir, r".*\.txt", encoding="utf-8")

        for fileid in reader.fileids():
            src_file = os.path.join(input_dir, fileid)
            target_file = os.path.join(output_dir, fileid)

            os.makedirs(os.path.dirname(target_file), exist_ok=True)

            logger.info(f"{src_file} -> {target_file}")

            annot_file = AnnotFile()

            with open(src_file, "r", encoding="utf-8") as f:
                annot_file.load(f)

            try:
                annot_file.apply(*predicates)
            except Exception as err:
                logger.error(f"main: error while correcting {fileid}")
                raise err

            with open(target_file, "w", encoding="utf-8") as f:
                annot_file.save(f)

    elif bool(args.indir) ^ bool(args.outdir):
        logger.warning("both input directory and output directory must be specified")


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
        "--verbose",
        action="store_true",
        help="make the output verbose (sets the logger into debug mode)",
    )

    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="perform all applicable corrections",
    )

    parser.add_argument(
        "--vcop",
        action="store_true",
        help="annotate selected instances of the verb 'být' as v:cop",
    )
    parser.add_argument(
        "--part-nogram",
        action="store_true",
        help="remove grammatical categories from the word 'co' when annotated as part",
    )
    parser.add_argument(
        "--adj-adv-compdeg",
        action="store_true",
        help="use a positive form as lemma for adjectives and adverbs",
    )
    parser.add_argument(
        "--dem-lemma",
        action="store_true",
        help="fix lemmatization of demonstratives",
    )
    parser.add_argument(
        "--people-lemma",
        action="store_true",
        help="fix lemmatization of the word 'lidé'",
    )

    args = parser.parse_args(sys.argv[1:])

    logger.info(args)

    main(args)
