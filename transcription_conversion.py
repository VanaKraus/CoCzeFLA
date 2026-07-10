#!/usr/bin/env python3

"""Conversion of older transcriptions to the v3.1 transcription standard.

Includes e.g. whitespace separation correction, standardization of quotation marks, \
or bracket code scope fixing.
"""

# TODO: license

import os

# import re
import regex
import sys
from typing import Callable, TextIO

from nltk.corpus import PlaintextCorpusReader

import argument_handling as ahandling

PHO_LINE_PREFIX = "%xpho:\t"
VERSIONS = ('1-0', '2-0', '3-0', '3-1', '3-2')

def is_pho_line(line: str) -> bool:
    """If line is %xpho (starts with `%xpho:\t`)."""
    return line.startswith(PHO_LINE_PREFIX)


def pho_to_xpho(line: str) -> str:
    """Convert old %pho line label to %xpho."""
    return line.replace("%pho", "%xpho")


def allow_amending(line: str) -> bool:
    """If general amending should be allowed for the line."""
    return bool(
        regex.match(
            r"(@(Comment|Situation)|\*[A-Z]{3}|%(err|add|tim|com|x?pho)):\t", line)
    )


def is_main_transcription_line(line: str) -> bool:
    """If the line contains the main-line transcription."""
    return bool(regex.match(r"\*[A-Z]{3}:\t", line))


def should_be_removed(line: str) -> bool:
    """If a line should be removed."""
    # empty %xpho lines should be removed
    return bool(regex.search(r"^%xpho:\t\.$", line))


def underscores_in_songs(line: str) -> str:
    """
    Replace underscores in <> brackets with spaces.
    
    Brackets containing letters and underscores only are affected.
    """
    for match in regex.findall(
        r'<[_a-záäąčćďéěëęíłňńóöřšśťůúüýžźż]+>', line
    ):
        line = line.replace(match, match.replace('_', ' '))

    return line


def scoped_comments(line: str) -> str:
    """
    Standardize scoped comments (`<scope> [=! comment]`). 

    Keep singing ("zpěv") and reciting ("básnička"),
    reword similar comments to match these.
    Remove all other comments.
    """
    # recursively match all "<foo> [bar]" patterns
    # contains 3 capture groups: 1st catches "<foo> [bar]", 2nd catches "foo", 3rd catches "bar"
    _PATTERN = r"(?:[^<>]|\+<|(<((?R))> \[([^\[\]]+)\]))*?"
    replacement_operations: list[tuple[str, str]] = []
    # a queue to enable recursive match finding
    matches = list(regex.findall(_PATTERN, line))

    while matches:
        match, scope_content, comment = matches.pop(0)

        # recursively add matches in the scope content
        if scope_content:
            matches += list(regex.findall(_PATTERN, scope_content))

        if not comment.startswith('=! '):
            continue

        comment = comment[3:]

        if comment in {'zpěv', 'básnička'}:
            continue

        elif comment in {'písnička'}:
            replacement_operations.append(
                (match, f'<{scope_content}> [=! zpěv]'))

        elif comment in {'říkanka', 'říkadlo', 'rozpočítadlo'}:
            replacement_operations.append(
                (match, f'<{scope_content}> [=! básnička]'))

        else:
            replacement_operations.append((match, scope_content))

    for op in replacement_operations:
        line = line.replace(*op)

    return line



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
        prefix = line[: len(PHO_LINE_PREFIX)]
        line = line[len(PHO_LINE_PREFIX):]

    # remove every non-ending character that isn't a space, letter or schwa (@)
    # and every ending character that isn't a dot or a letter
    line = regex.sub(
        r"[^ @a-zA-ZáäąčćďéěëęíłňńóöřšśťůúüýžźżÁÄĄČĆĎÉĚËĘÍŁŇŃÓÖŘŠŚŤŮÚÜÝŽŹŻ](?!$)|"
        + r"[^\.a-zA-ZáäąčćďéěëęíłňńóöřšśťůúüýžźżÁÄĄČĆĎÉĚËĘÍŁŇŃÓÖŘŠŚŤŮÚÜÝŽŹŻ]$",
        r"",
        line,
    )

    # add a dot to the end of each line if it's missing
    line = regex.sub(r"([^\.])$", r"\1 .", line)

    # remove excessive whitespaces
    line = regex.sub(r" {2,}|\t+", r" ", line.strip())

    return prefix + line


def convert_quotation_marks(string: str) -> str:
    """Convert any quotes („“; ""; '') to English upper double quotes (“”)."""
    return regex.sub(r"[„\"']([^“\"']*)[“\"']", r"“\1”", string)


def horizontal_ellipsis(string: str) -> str:
    """Replace the horizontal ellipsis character (`…`) with three dots (`...`)."""
    return string.replace("+…", "+...")


def fix_bracket_code_scope(string: str) -> str:
    """Mark token preceding unmarked bracket codes as their scope. \
        Bracket codes beginning with either '/', '=', '?', or 'x' affected."""

    # add scope to bracket codes following a regular token
    result = regex.sub(
        r"([ \t<]|^)([&+@,=:_a-zA-ZáäąčćďéěëęíłňńóöřšśťůúüýžźżÁÄĄČĆĎÉĚËĘÍŁŇŃÓÖŘŠŚŤŮÚÜÝŽŹŻ]+) (\[[\/=x\?].*?\])",
        r"\1<\2> \3",
        string,
    )

    # add scope to bracket codes following another bracket code
    # e.g. "<ťapu> [x 2] [?]" turns to "<<ťapu> [x 2]> [?]"

    # while there's a bracket code following another bracket code without scope added
    while m := regex.fullmatch(
        r".*?((<(?:(?:[^<>]*(?2))*[^<>]*)> \[[\/=x\?].*?\]) (\[[\/=x\?].*?\])).*",
        result,
    ):
        allcaptures = m.allcaptures()
        result = result.replace(
            allcaptures[1][0],  # type: ignore
            f"<{allcaptures[2][-1]}> {allcaptures[3][0]}",  # type: ignore
        )

    return result


def spaces_around_punctuation(string: str) -> str:
    """Add spaces around punctuation (`,`, `“`, `”`, `.`, `?`, `!`, `+...`, `+/.`)."""
    # not end-of-line characters
    string = regex.sub(r" *(,|“|”|;) *", r" \1 ", string).strip()
    # end-of-line characters
    string = regex.sub(r" *(\.|\?|\!|\+\.\.\.|\+/\.)$", r" \1", string).strip()
    # other characters requiring a preceding space
    string = regex.sub(r" *(\[)", r" \1", string).strip()
    # remove excessive whitespaces
    string = regex.sub(r" {2,}", r" ", string)
    # correct for spaces before end-of-line characters that are the only tokens on their lines
    string = regex.sub(r"\t *", r"\t", string)

    return string


def word_fragments(string: str) -> str:
    """Convert word fragment markings from & to &+."""
    return regex.sub(
        r"&([a-zA-ZáäąčćďéěëęíłňńóöřšśťůúüýžźżÁÄĄČĆĎÉĚËĘÍŁŇŃÓÖŘŠŚŤŮÚÜÝŽŹŻ]+)",
        r"&+\1",
        string,
    )


def missing_words(string: str) -> str:
    """Convert missing word markings from 0 to &=0."""
    return regex.sub(
        r"(?<!&=)0([a-zA-ZáäąčćďéěëęíłňńóöřšśťůúüýžźżÁÄĄČĆĎÉĚËĘÍŁŇŃÓÖŘŠŚŤŮÚÜÝŽŹŻ]+)",
        r"&=0\1",
        string,
    )


def repetition_to_false_starts(string: str) -> str:
    """Convert repetition-markers notation to a false-start notation."""
    result = string

    # recursively match all "<foo> [bar]" patterns
    # contains 3 capture groups: 1st catches "<foo> [bar]", 2nd catches "foo", 3rd catches "bar"
    matches = regex.fullmatch(r"(?:[^<>]|\+<|(<((?R))> \[([^\[\]]+)\]))*",
                              result)

    # unable to match the regex pattern indicates defective syntax
    if not matches:
        raise ValueError(f'defective "<> []" syntax in "{string}"')

    # used to store which strings should be replaced by which ones
    replacement_operations: list[tuple[str, str]] = []
    allcaptures = matches.allcaptures()

    # iterate through all matched patterns
    for i, pattern in enumerate(allcaptures[1]):  # type: ignore
        content = allcaptures[2][i]  # type: ignore
        modifier = allcaptures[3][i]  # type: ignore

        # catch up with already computed replacements
        for operation in replacement_operations:
            pattern = pattern.replace(*operation)
            content = content.replace(*operation)

        # if the pattern is a repetition one
        if modif_match := regex.match(r"x ([0-9]+)", modifier):
            count = int(modif_match[1])
            replacement = ""

            # create the replacement string
            for _ in range(count - 1):
                replacement += f"<{content}> [/] "
            replacement += content

            # store the replacement instructions
            replacement_operations += [(pattern, replacement)]

    # apply replacement operations
    for operation in replacement_operations:
        result = result.replace(*operation)

    # check if we've missed a repetition marker
    if marker := regex.search(r"\[x [0-9]+\]", result):
        raise ValueError(
            f'Unable to remove "{marker.group(0)}" from "{string}"')

    return result


def apply_new_standard(line: str, tver: str,
                       fix_errors: bool = False) -> str | None:
    """Convert line to the new transcription standard.

    Args:
        line (str)
        tver (str): Target transcription version

    Returns:
        str | None: the modified line. None when the line should be removed.
    """
    line = line.strip("\r\n")

    if should_be_removed(line):
        return None

    if not allow_amending(line):
        return line

    if allow_amending(line):
        line = convert_quotation_marks(line)
        line = horizontal_ellipsis(line)
        line = spaces_around_punctuation(line)

    if VERSIONS.index(tver) >= VERSIONS.index('2-0'):
        if is_main_transcription_line(line):
            line = fix_bracket_code_scope(line)
            line = underscores_in_songs(line)
            line = scoped_comments(line)

            # all other changes do not appear relevant to Chroma anymore

    if VERSIONS.index(tver) >= VERSIONS.index('3-2'):
        line = pho_to_xpho(line)

        if is_pho_line(line):
            line = clear_pho_line(line)

        elif is_main_transcription_line(line):
            line = word_fragments(line)
            line = missing_words(line)
            try:
                line = repetition_to_false_starts(line)
            except ValueError as e:
                print(e, file=sys.stderr)

    return line


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
        elif regex.match(r"\s", string):
            self.line += regex.sub(r"$\s+|\t+", " ", string.strip("\r\n"))
        else:
            self.close_line()
            self.line = string.strip("\r\n")

    def close_line(self):
        """Close the CHAT line currently being built and call `self.predicate` onto it."""
        if completed := self.predicate(self.line):
            print(completed, file=self.target_fs)

        self.line = ""


def convert_filestream(source_fs, target_fs, tver: str,
                       fix_errors: bool = False):
    """Convert filestream.

    Args:
        source_fs: Source filestream.
        target_fs: Target filestream.
        tver: Target transcription version.
    """
    with LineComposer(
        lambda s: apply_new_standard(s, tver, fix_errors), target_fs
    ) as composer:
        for line in source_fs:
            composer.add(line)


def convert_file(path_source: str, path_target: str, tver: str,
                 fix_errors: bool = False):
    """Convert single file.

    Args:
        path_source (str): Path to the source file.
        path_target (str): Path to the target file. Existing files will be overwritten.
        tver: Target transcription version.
    """
    try:
        with open(path_source, "r", encoding="utf-8") as source_fs:
            with open(path_target, "w", encoding="utf-8") as target_fs:
                print(f"Convert\t: {path_source} -> {path_target}",
                      file=sys.stderr)
                convert_filestream(source_fs, target_fs, tver, fix_errors)
    except IsADirectoryError:
        print(f"Skip\t: {path_source} (directory)", file=sys.stderr)
    except FileNotFoundError:
        print(f"Skip\t: {path_source} (not found)", file=sys.stderr)


def _handle_args(args):
    tver = args.target_version
    if tver not in VERSIONS:
        raise ValueError(f'target transcription version was expected '
                         f'to be {' or '.join(VERSIONS)}, received \'{tver}\'.')

    # take input from stdin
    if args.std:
        convert_filestream(sys.stdin, sys.stdout, tver, args.fix)
    # take files as input
    elif args.outdir:
        files: list[tuple[str, str]] = []

        # an input directory specified
        if args.indir:
            reader = PlaintextCorpusReader(
                args.indir[0],
                args.mask if args.mask else r".*\.(txt|cha)",
                encoding="utf-8"
            )
            files = [
                (os.path.join(args.indir[0], id),
                 os.path.join(args.outdir[0], id))
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
        fs_skipped = 0
        for input_file, output_file in files:
            if not os.path.isdir(dname := os.path.dirname(output_file)):
                os.makedirs(dname)

            # skip already transcribed files
            if ((not args.force_all) and 
                os.path.exists(output_file) and 
                os.path.getmtime(input_file) < os.path.getmtime(output_file)):
                fs_skipped += 1
                continue

            convert_file(input_file, output_file, tver, args.fix)

        if fs_skipped > 0:
            print(f'Skipped {fs_skipped} file(s). Run with --force-all to disable.')

    else:
        print(
            "An output directory needs to be specified. See --help for more.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    req_arguments = ahandling.get_argument_subset(
        "inputfiles", "std", "indir", "outdir", "fix", "target_version", "mask", "force_all"
    )

    if len(sys.argv) > 1:
        parser = ahandling.get_argument_parser(
            req_arguments,
            description="convert CHAT text files to a newer transcription standard.",
        )
        arguments = parser.parse_args(sys.argv[1:])

        print(f"arguments: {arguments}", file=sys.stderr)
    else:
        arguments = ahandling.argument_walkthrough(req_arguments)

    _handle_args(arguments)
