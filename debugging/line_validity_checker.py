#!/usr/bin/env python3

import sys

import annotation as annot


if __name__ == "__main__":
    for line in sys.stdin:
        try:
            list(annot.process_line(line))
        except annot.ChatToPlainTextConversionError as e:
            print(e)
