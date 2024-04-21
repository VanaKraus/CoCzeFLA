#!/usr/bin/env python3

import re
import sys


PHO_LINE_PREFIX = "%pho:\t"
COMMENT_PREFIX = "@"


def is_pho_line(line: str) -> bool:
    """If line is %pho (starts with `%pho:\t`)."""
    return line.startswith(PHO_LINE_PREFIX)


def is_comment(line: str) -> bool:
    """If line is a comment (starts with `@`)."""
    return line.startswith(COMMENT_PREFIX)


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

    # remove every non-ending character that isn't a space, letter, schwa or @
    # and every ending character that isn't a dot or a letter
    line = re.sub(
        r"[^ ə@a-zA-ZáčďéěíňóřšťůúýžÁČĎÉĚÍŇÓŘŠŤŮÚÝŽ](?!$)|[^\.a-zA-ZáčďéěíňóřšťůúýžÁČĎÉĚÍŇÓŘŠŤŮÚÝŽ]$",
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
    string = re.sub(r" *(,|“|”) *", r" \1 ", string).strip()
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

    if is_comment(line):
        return line

    if is_pho_line(line):
        line = clear_pho_line(line)

    line = convert_quotation_marks(line)
    line = horizontal_ellipsis(line)
    line = spaces_around_punctuation(line)

    return line


if __name__ == "__main__":
    # TODO: make it easier to run the script on multiple files

    for line in sys.stdin:
        converted = apply_new_standard(line)
        print(converted)
