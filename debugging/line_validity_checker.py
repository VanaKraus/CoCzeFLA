#!/usr/bin/env python3

import sys
import os
import datetime


sys.path.append("../CoCzeFLA")

from nltk.corpus import PlaintextCorpusReader

import annotation as annot
from annot_util.conversions import ChatToPlainTextConversionError
import argument_handling as ahandling

_logging_fs = None


def _log(m: str):
    global _logging_fs

    print(m)
    print(m, file=_logging_fs)


def _handle_args(args) -> int:
    _ecode = 0

    # take input from stdin
    if args.std:
        for line in sys.stdin:
            try:
                for _ in annot.process_line(line):
                    pass
            except ChatToPlainTextConversionError as e:
                _ecode = 1
                print(
                    f"Error\t: ({e.__class__.__name__})\n{e}\n",
                    file=sys.stderr,
                )

    # take files as input
    else:
        files: list[str] = []

        # an input directory specified
        if args.indir:
            reader = PlaintextCorpusReader(
                args.indir[0], r".*\.(txt|cha)", encoding="utf-8"
            )
            files = [(os.path.join(args.indir[0], id)) for id in reader.fileids()]

        # individual files specified as input
        elif len(args.inputfiles) > 0:
            files = args.inputfiles
        else:
            print(
                "Please specify your input files. See --help for more.", file=sys.stderr
            )
            return 2

        # run file annotation
        for input_file in files:
            _log(input_file)

            with open(input_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        for _ in annot.process_line(line):
                            pass
                    except ChatToPlainTextConversionError as e:
                        _ecode = 1
                        _log(
                            f"Error\t: {input_file} ({e.__class__.__name__})\n{e}\n",
                        )

    return _ecode


if __name__ == "__main__":
    # get current time and open the .log file
    now = datetime.datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H-%M-%S")
    tfile_dir = os.path.join("validity-checks", date)
    tfile = os.path.join(tfile_dir, f"vcheck_{date}_{time}.log")

    if not os.path.exists(tfile_dir):
        os.makedirs(tfile_dir)

    _logging_fs = open(tfile, "w+", encoding="utf-8")

    # info about the run
    _log(f"Validate {now:%Y-%m-%d %H:%M:%S}")
    _log(f"{sys.argv[1:] = }")

    # set and parse CLI arguments
    req_arguments = ahandling.get_argument_subset("inputfiles", "std", "indir")

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

    # run the validator
    ECODE = _handle_args(arguments)

    # close the .log file
    _log(f"Done {datetime.datetime.now():%Y-%m-%d %H:%M:%S}")
    _logging_fs.close()

    print(f"See {tfile}")

    sys.exit(ECODE)
