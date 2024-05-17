from argparse import ArgumentParser, Namespace

import constants


class Argument:
    def __init__(self, *flags: list[str], **args) -> None:
        self.flags = flags
        self.arguments = args


_PROMPT = "> "

arguments: dict[str, Argument] = {
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
}


def get_argument_subset(*argument_ids: list[str]) -> dict[str, Argument]:
    res = {}

    for aid in argument_ids:
        res |= {aid: arguments[aid]}

    return res


def get_argument_parser(
    args: dict[str, Argument], **parser_init_args
) -> ArgumentParser:
    parser = ArgumentParser(**parser_init_args)

    for _, arg in args.items():
        parser.add_argument(*arg.flags, **arg.arguments)

    return parser


def _get_yes_no_input(prompt: str) -> bool:
    while True:
        res = input(f"{prompt} [y/n] ")
        if res in ("y", "Y"):
            return True
        if res in ("n", "N"):
            return False


def _get_string_input(prompt: str) -> str:
    print(prompt)
    while True:
        if res := input(_PROMPT):
            return res


def argument_walkthrough(args: dict[str, Argument]) -> Namespace:
    result = Namespace(**{id: None for id in args.keys()})

    print("--- Configuration walkthrough ---")

    if "indir" in args:
        print(
            "Set directory with input files. "
            + "Leave empty if you wish to provide individual files as input "
            + "or don't want to provide any input file at all:"
        )
        indir = input(_PROMPT)

        if indir:
            result.indir = [indir]
        else:
            inputfiles = []

            while True:
                print(
                    "Add an additional input file. Leave empty to finish the list:"
                    if inputfiles
                    else "Add an input file. Leave empty to provide utterances line-by-line:"
                )
                file = input(_PROMPT)

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
        print(
            "Configure tokenizer type. Leave empty if you want to use "
            + f"the default value ('{constants.TOKENIZER_TYPE}'):"
        )
        if res := input(_PROMPT):
            result.tokenizer = [res]

    if "tagger" in args:
        print(
            "Configure path to your tagger. Leave empty if you want to "
            + f"use the default value ('{constants.TAGGER_PATH}'):"
        )
        if res := input(_PROMPT):
            result.tagger = [res]

    if result.std:
        if "tagger" in args:
            print("You can start providing input after the tagger loads.")
        else:
            print("You can start providing input now.")

    print("--- Configuration walkthrough completed ---")

    return result
