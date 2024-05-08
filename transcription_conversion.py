#!/usr/bin/env python3

# TODO: license

import argparse
import os
import re
import sys

from nltk.corpus import PlaintextCorpusReader

PHO_LINE_PREFIX = "%pho:\t"


def is_pho_line(line: str) -> bool:
    """If line is %pho (starts with `%pho:\t`)."""
    return line.startswith(PHO_LINE_PREFIX)


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


def spaces_around_punctuation(string: str) -> str:
    """Add spaces around punctuation (`,`, `“`, `”`, `.`, `?`, `!`, `+...`, `+/.`)."""
    # not end-of-line characters
    string = re.sub(r" *(,|“|”|;) *", r" \1 ", string).strip()
    # end-of-line characters
    string = re.sub(r" *(\.|\?|\!|\+\.\.\.|\+/\.)$", r" \1", string).strip()
    # correct for spaces before end-of-line characters that are the only tokens on their lines
    string = re.sub(r"\t *", r"\t", string)

    return string


def apply_new_standard(line: str) -> str:
    """Convert line to the new transcription standard.

    Args:
        line (str)

    Returns:
        str
    """
    line = line.strip("\n")

    if is_pho_line(line):
        line = clear_pho_line(line)

    line = convert_quotation_marks(line)
    line = horizontal_ellipsis(line)
    line = spaces_around_punctuation(line)

    return line


def convert_filestream(source_fs, target_fs):
    """Convert filestream.

    Args:
        source_fs: Source filestream.
        target_fs: Target filestream.
    """
    for line in source_fs:
        converted = apply_new_standard(line)
        print(converted, file=target_fs)


def convert_file(path_source: str, path_target: str):
    """Convert single file.

    Args:
        path_source (str): Path to the source file.
        path_target (str): Path to the target file. Existing files will be overwritten.
    """
    try:
        with open(path_source, "r", encoding="utf-8") as source_fs:
            with open(path_target, "w", encoding="utf-8") as target_fs:
                print(f"Convert\t: {path_source}", file=sys.stderr)
                convert_filestream(source_fs, target_fs)
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
            convert_file(input_file, output_file)
    else:
        print(
            "An output directory needs to be specified. See --help for more.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="convert CHAT text files to the v3.1 transcription standard."
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
        help="take all .txt files from this directory as the input; enabling this option overrides all inputfiles",
    )
    parser.add_argument("inputfiles", nargs="*", default=[])

    arguments = parser.parse_args(sys.argv[1:])
    _handle_args(arguments)
