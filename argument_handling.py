"""Provides arguments for transcription_conversion and annotation."""

from argparse import ArgumentParser, Namespace
from typing import Any
import re

from annot_util import constants


class Argument:
    """Argument specification.

    Attributes:
        flags (tuple[str, ...]): Flags used to envoke the argument.
        arguments (dict[str, Any]): Other arguments used in the argument construction in argparse.
    """

    flags: tuple[str, ...]
    arguments: dict[str, Any]

    def __init__(self, *flags: str, **args) -> None:
        self.flags = flags
        self.arguments = args


_PROMPT = "> "

# argument definitions
ARGUMENTS: dict[str, Argument] = {
    "std": Argument(
        "-s",
        "--std",
        action="store_true",
        help="receive/print input/output on stdin/stdout",
    ),
    "outdir": Argument(
        "-o",
        "--outdir",
        nargs=1,
        type=str,
        help="directory where output files should be stored",
    ),
    "indir": Argument(
        "-i",
        "--indir",
        nargs=1,
        type=str,
        help="take all .txt files from this directory as the input; \
        enabling this option overrides all inputfiles",
    ),
    "tokenizer": Argument(
        "-d",
        "--tokenizer",
        nargs=1,
        type=str,
        default=[constants.TOKENIZER_TYPE],
        help="configure MorphoDiTa tokenizer type; overrides any tokenizer type \
        specified in constants.TOKENIZER_TYPE",
    ),
    "tagger": Argument(
        "-t",
        "--tagger",
        nargs=1,
        type=str,
        default=[constants.TAGGER_PATH],
        help="configure MorphoDiTa tagger; overrides any tagger specified in constants.TAGGER_PATH",
    ),
    "inputfiles": Argument("inputfiles", nargs="*", default=[]),
    "fix": Argument(
        "-f",
        "--fix",
        action="store_true",
        help="fix possibly untrivial syntax errors",
    ),
    "guess": Argument(
        "-g",
        "--guess",
        action="store_true",
        help="enable MorphoDiTa morphological guesser",
    ),
}


def get_argument_subset(*argument_ids: str) -> dict[str, Argument]:
    """Subset `ARGUMENTS`.

    Args:
        argument_ids (Optional[str]): Keys of `ARGUMENTS` that should be \
            included in the subset.

    Returns:
        dict[str, Argument]: Subset; a new dictionary.
    """
    res = {}

    for aid in argument_ids:
        res |= {aid: ARGUMENTS[aid]}

    return res


def get_argument_parser(
    args: dict[str, Argument], **parser_init_args
) -> ArgumentParser:
    """Create an ArgumentParser instance from an Argument dictionary.

    Args:
        args (dict[str, Argument]): Dictionary of arguments.
        parser_init_args (dict): Additional arguments for the ArgumentParser \
            constructor.

    Returns:
        ArgumentParser: ArgumentParser instance.
    """
    parser = ArgumentParser(**parser_init_args)

    for arg in args.values():
        parser.add_argument(*arg.flags, **arg.arguments)

    return parser


def _get_boolean_input(prompt: str) -> bool:
    """Display a prompt asking for a boolean [y/n] answer on stdin.

    Args:
        prompt (str): Prompt text.

    Returns:
        bool: Result of the prompt.
    """
    while True:
        res = input(f"{prompt} [y/n] ")
        if res in ("y", "Y"):
            return True
        if res in ("n", "N"):
            return False


def _get_string_input(prompt: str, allow_empty: bool = False) -> str:
    """Display a prompt asking for a string answer on stdin.

    Args:
        prompt (str): Prompt text.
        allow_empty (bool): Allow empty string as a return value.

    Returns:
        str: Answer.
    """
    print(prompt)
    while True:
        if (res := input(_PROMPT)) or allow_empty:
            if re.search(r"^'.+'$", res):
                res = res.strip("'")
            elif re.search(r'^".+"$', res):
                res = res.strip('"')

            return res


def argument_walkthrough(args: dict[str, Argument]) -> Namespace:
    """Create an interactive CLI argument setup for the user. The result mimics \
        results of ArgumentParser.parse_args.

    Args:
        args (dict[str, Argument]): Arguments to be included in the walkthrough \
            and the resulting Namespace.

    Returns:
        Namespace: Arguments with their values set-up.
    """
    result = Namespace(**{id: None for id in args.keys()})

    print("--- Configuration walkthrough ---")

    if "indir" in args:
        indir = _get_string_input(
            "Set directory with input files. "
            + "Leave empty if you wish to provide individual files as input "
            + "or don't want to provide any input file at all:",
            allow_empty=True,
        )

        if indir:
            result.indir = [indir]
        else:
            inputfiles = []

            while True:
                file = _get_string_input(
                    (
                        "Add an additional input file. Leave empty to finish the list:"
                        if inputfiles
                        else "Add an input file. Leave empty to provide utterances line-by-line:"
                    ),
                    allow_empty=True,
                )

                if file:
                    inputfiles += [file]
                else:
                    break

            result.inputfiles = inputfiles
            result.std = not bool(inputfiles)

    if not result.std:
        if "outdir" in args:
            result.outdir = [_get_string_input("Set output directory:")]

    if "tokenizer" in args:
        result.tokenizer = [
            _get_string_input(
                "Configure tokenizer type. Leave empty if you want to use "
                + f"the default value ('{constants.TOKENIZER_TYPE}'):",
                allow_empty=True,
            )
        ]

    if "tagger" in args:
        result.tagger = [
            _get_string_input(
                "Configure path to your tagger. Leave empty if you want to "
                + f"use the default value ('{constants.TAGGER_PATH}'):",
                allow_empty=True,
            )
        ]

    if "fix" in args:
        result.fix = _get_boolean_input(
            "Would you like potential syntax errors to be fixed automatically?"
        )

    if "guess" in args:
        result.guess = _get_boolean_input(
            "Would you like to enable the MorphoDiTa morphological guesser?"
        )

    if result.std:
        if "tagger" in args:
            print("You can start providing input after the tagger loads.")
        else:
            print("You can start providing input now.")

    print("--- Configuration walkthrough completed ---")

    return result
