#!/usr/bin/env python3

"""Conversion of older transcriptions to the v3.1 transcription standard.

Includes e.g. whitespace separation correction, standardization of quotation marks, \
or bracket code scope fixing.
"""

# TODO: license

import os
import re
import sys
from typing import Callable, TextIO

from nltk.corpus import PlaintextCorpusReader

import argument_handling as ahandling

PHO_LINE_PREFIX = "%xpho:\t"


def is_pho_line(line: str) -> bool:
    """If line is %xpho (starts with `%xpho:\t`)."""
    return line.startswith(PHO_LINE_PREFIX)


def pho_to_xpho(line: str) -> str:
    """Convert old %pho line label to %xpho."""
    return line.replace("%pho", "%xpho")


def allow_amending(line: str) -> bool:
    """If general amending should be allowed for the line."""
    return bool(
        re.match(r"(@(Comment|Situation)|\*[A-Z]{3}|%(err|add|tim|com)):\t", line)
    )


def should_be_removed(line: str) -> bool:
    """If a line should be removed."""
    # empty %xpho lines should be removed
    return bool(re.search(r"^%xpho:\t\.$", line))


def clear_pho_line(line: str) -> str:
    """Clear all characters from a %xpho line except for spaces, letters, schwas and @s.

    The `%xpho:\t` prefix is kept if present.

    Args:
        line (str)

    Returns:
        str
    """
    prefix = ""
    if is_pho_line(line):
        prefix, line = line[: len(PHO_LINE_PREFIX)], line[len(PHO_LINE_PREFIX) :]

    # remove every non-ending character that isn't a space, letter or schwa (@)
    # and every ending character that isn't a dot or a letter
    line = re.sub(
        r"[^ @a-zA-ZáčďéěíňóřšťůúýžÁČĎÉĚÍŇÓŘŠŤŮÚÝŽ](?!$)|"
        + r"[^\.a-zA-ZáčďéěíňóřšťůúýžÁČĎÉĚÍŇÓŘŠŤŮÚÝŽ]$",
        r"",
        line,
    )

    # add a dot to the end of each line if it's missing
    line = re.sub(r"([^\.])$", r"\1 .", line)

    # remove excessive whitespaces
    line = re.sub(r" {2,}|\t+", r" ", line.strip())

    return prefix + line


def convert_quotation_marks(string: str) -> str:
    """Convert any quoters („“; "") to English upper double quotes (“”)."""
    return re.sub(r"[„\"]([^“\"]*)[“\"]", r"“\1”", string)


def horizontal_ellipsis(string: str) -> str:
    """Replace the horizontal ellipsis character (`…`) with three dots (`...`)."""
    return string.replace("+…", "+...")


def fix_bracket_code_scope(string: str) -> str:
    """Mark token preceding unmarked bracket codes as their scope. \
        Bracket codes beginning with either '/', '=', '?', or 'x' affected."""

    return re.sub(
        r"([ \t]|^)([&,=:_a-zA-ZáčďéěíňóřšťůúýžÁČĎÉĚÍŇÓŘŠŤŮÚÝŽ]+) (\[[\/=x\?].*?\])",
        r"\1<\2> \3",
        string,
    )


def spaces_around_punctuation(string: str) -> str:
    """Add spaces around punctuation (`,`, `“`, `”`, `.`, `?`, `!`, `+...`, `+/.`)."""
    # not end-of-line characters
    string = re.sub(r" *(,|“|”|;) *", r" \1 ", string).strip()
    # end-of-line characters
    string = re.sub(r" *(\.|\?|\!|\+\.\.\.|\+/\.)$", r" \1", string).strip()
    # remove excessive whitespaces
    string = re.sub(r" {2,}", r" ", string)
    # correct for spaces before end-of-line characters that are the only tokens on their lines
    string = re.sub(r"\t *", r"\t", string)

    return string


def word_fragments(string: str) -> str:
    """Convert word fragment markings from & to &+."""
    return re.sub(r"&([a-zA-ZáčďéěíňóřšťůúýžÁČĎÉĚÍŇÓŘŠŤŮÚÝŽ]+)", r"&+\1", string)


def missing_words(string: str) -> str:
    """Convert missing word markings from 0 to &=0."""
    return re.sub(
        r"(?<!&=)0([a-zA-ZáčďéěíňóřšťůúýžÁČĎÉĚÍŇÓŘŠŤŮÚÝŽ]+)", r"&=0\1", string
    )


def repetition_to_false_starts(string: str) -> str:
    """Convert repetition-markers notation to a false-start notation."""
    result = string

    # TODO: what if embedded?
    while m := re.search(
        r"<([ ,_&@:=\^a-zA-ZáčďéěíňóřšťůúýžÁČĎÉĚÍŇÓŘŠŤŮÚÝŽ]+?)> \[x ([0-9]+)\]", result
    ):
        orig, pattern, count = m[0], m[1], int(m[2])
        replacement = ""

        for _ in range(count - 1):
            replacement += f"<{pattern}> [/] "
        replacement += pattern

        result = result.replace(orig, replacement)

    if marker := re.search(r"\[x [0-9]+\]", result):
        print(f'Unable to remove "{marker.group(0)}" from "{string}"', file=sys.stderr)

    return result


def apply_new_standard(line: str, fix_errors: bool = False) -> str | None:
    """Convert line to the new transcription standard.

    Args:
        line (str)

    Returns:
        str | None: the modified line. None when the line should be removed.
    """
    line = line.strip("\r\n")

    line = pho_to_xpho(line)

    if is_pho_line(line):
        line = clear_pho_line(line)

    if allow_amending(line):
        line = convert_quotation_marks(line)
        line = horizontal_ellipsis(line)
        line = spaces_around_punctuation(line)
        line = word_fragments(line)
        line = missing_words(line)

        if fix_errors:
            line = fix_bracket_code_scope(line)

        line = repetition_to_false_starts(line)

    return None if should_be_removed(line) else line


class LineComposer:
    """Convert single CHAT lines spread out into multiple plaintext lines \
    into a single line.

    Attributes:
        predicate (Callable[[str], str  |  None]): Gets called onto a CHAT line when \
                it's finished.
        target_fs (TextIO): Target filestream.
    """

    predicate: Callable[[str], str | None]
    target_fs: TextIO
    line: str

    def __init__(
        self, predicate: Callable[[str], str | None], target_fs: TextIO
    ) -> None:
        """Initialize new LineComposer instance.

        Args:
            predicate (Callable[[str], str  |  None]): Gets called onto a CHAT line when \
                it's finished.
            target_fs (TextIO): Target filestream.
        """
        self.target_fs = target_fs
        self.predicate = predicate
        self.line = ""

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.close_line()

    def add(self, string: str):
        """Add a plaintext line. If the plaintext line doesn't continue the CHAT line \
            currently being built, the CHAT line gets closed and a new one is started.

        Args:
            string (str): Plaintext line.
        """
        if not self.line:
            self.line = string.strip("\r\n")
        # if line starts with a whitespace, it's meant to be appended to the previous one
        elif re.match(r"\s", string):
            self.line += re.sub(r"$\s+|\t+", " ", string.strip("\r\n"))
        else:
            self.close_line()
            self.line = string.strip("\r\n")

    def close_line(self):
        """Close the CHAT line currently being built and call `self.predicate` onto it."""
        if completed := self.predicate(self.line):
            print(completed, file=self.target_fs)

        self.line = ""


def convert_filestream(source_fs: TextIO, target_fs: TextIO, fix_errors: bool = False):
    """Convert filestream.

    Args:
        source_fs: Source filestream.
        target_fs: Target filestream.
    """
    with LineComposer(
        lambda s: apply_new_standard(s, fix_errors), target_fs
    ) as composer:
        for line in source_fs:
            composer.add(line)


def convert_file(path_source: str, path_target: str, fix_errors: bool = False):
    """Convert single file.

    Args:
        path_source (str): Path to the source file.
        path_target (str): Path to the target file. Existing files will be overwritten.
    """
    try:
        with open(path_source, "r", encoding="utf-8") as source_fs:
            with open(path_target, "w", encoding="utf-8") as target_fs:
                print(f"Convert\t: {path_source} -> {path_target}", file=sys.stderr)
                convert_filestream(source_fs, target_fs, fix_errors)
    except IsADirectoryError:
        print(f"Skip\t: {path_source} (directory)", file=sys.stderr)
    except FileNotFoundError:
        print(f"Skip\t: {path_source} (not found)", file=sys.stderr)


def _handle_args(args):
    # take input from stdin
    if args.std:
        convert_filestream(sys.stdin, sys.stdout, args.fix)
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

        # run file conversion
        for input_file, output_file in files:
            if not os.path.isdir(dname := os.path.dirname(output_file)):
                os.makedirs(dname)
            convert_file(input_file, output_file, args.fix)
    else:
        print(
            "An output directory needs to be specified. See --help for more.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    req_arguments = ahandling.get_argument_subset(
        "inputfiles", "std", "indir", "outdir", "fix"
    )

    if len(sys.argv) > 1:
        parser = ahandling.get_argument_parser(
            req_arguments,
            description="convert CHAT text files to the v3.1 transcription standard.",
        )
        arguments = parser.parse_args(sys.argv[1:])

        print(f"arguments: {arguments}", file=sys.stderr)
    else:
        arguments = ahandling.argument_walkthrough(req_arguments)

    _handle_args(arguments)
