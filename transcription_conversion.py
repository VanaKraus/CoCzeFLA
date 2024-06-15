#!/usr/bin/env python3

# TODO: license

import os
import re
import sys
from typing import Callable

from nltk.corpus import PlaintextCorpusReader

import argument_handling as ahandling

PHO_LINE_PREFIX = "%pho:\t"


def is_pho_line(line: str) -> bool:
    """If line is %pho (starts with `%pho:\t`)."""
    return line.startswith(PHO_LINE_PREFIX)


def allow_amending(line: str) -> bool:
    """If general amending should be allowed for the line."""
    return bool(
        re.match(r"(@(Comment|Situation)|\*[A-Z]{3}|%(err|add|tim|com)):\t", line)
    )


def should_be_removed(line: str) -> bool:
    """If a line should be removed."""
    # empty %pho lines should be removed
    return bool(re.search(r"^%pho:\t\.$", line))


def clear_pho_line(line: str) -> str:
    """Clear all characters from a %pho line except for spaces, letters, schwas and @s.

    The `%pho:\t` prefix is kept if present.

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
        r"[^ @a-zA-ZáčďéěíňóřšťůúýžÁČĎÉĚÍŇÓŘŠŤŮÚÝŽ](?!$)|[^\.a-zA-ZáčďéěíňóřšťůúýžÁČĎÉĚÍŇÓŘŠŤŮÚÝŽ]$",
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
    """Mark token preceding unmarked bracket codes as their scope. Bracket codes beginning with either '/', '=', '?', or 'x' affected."""

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


def apply_new_standard(line: str, fix_errors: bool = False) -> str | None:
    """Convert line to the new transcription standard.

    Args:
        line (str)

    Returns:
        str | None: the modified line. None when the line should be removed.
    """
    line = line.strip("\r\n")

    if is_pho_line(line):
        line = clear_pho_line(line)

    if allow_amending(line):
        line = convert_quotation_marks(line)
        line = horizontal_ellipsis(line)
        line = spaces_around_punctuation(line)

        if fix_errors:
            line = fix_bracket_code_scope(line)

    return None if should_be_removed(line) else line


class LineComposer:
    def __init__(self, predicate: Callable[[str], str | None], target_fs) -> None:
        self.target_fs = target_fs
        self.predicate = predicate
        self.line = None

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.complete_line()

    def add(self, string: str):
        if not self.line:
            self.line = string.strip("\r\n")
        # if line starts with a whitespace, it's meant to be appended to the previous one
        elif re.match(r"\s", string):
            self.line += re.sub(r"$\s+|\t+", " ", string.strip("\r\n"))
        else:
            self.complete_line()
            self.line = string.strip("\r\n")

    def complete_line(self):
        if completed := self.predicate(self.line):
            print(completed, file=self.target_fs)

        self.line = None


def convert_filestream(source_fs, target_fs, fix_errors: bool = False):
    """Convert filestream.

    Args:
        source_fs: Source filestream.
        target_fs: Target filestream.
    """

    predicate = lambda s: apply_new_standard(s, fix_errors)

    with LineComposer(predicate, target_fs) as composer:
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
                print(f"Convert\t: {path_source}", file=sys.stderr)
                convert_filestream(source_fs, target_fs, fix_errors)
    except IsADirectoryError:
        print(f"Skip\t: {path_source} (directory)", file=sys.stderr)
    except FileNotFoundError:
        print(f"Skip\t: {path_source} (not found)", file=sys.stderr)


def _handle_args(args):
    # take input from stdin
    if args.std:
        convert_filestream(sys.stdin, sys.stdout)
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
    else:
        arguments = ahandling.argument_walkthrough(req_arguments)

    _handle_args(arguments)
