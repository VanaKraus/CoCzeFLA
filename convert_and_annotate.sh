#!/usr/bin/bash

set -ueo pipefail

opts_short="p:s:c:a:h"
opts_long="prod:,src:,conv:,annot:,help"

getopt -Q -o "$opts_short" -l "$opts_long" -- "$@" || exit 1
eval set -- "$( getopt -o "$opts_short" -l "$opts_long" -- "$@" )"

PROD_D=""
SOURCE_D=""
CONV_D=""
ANNOT_D=""

while [ $# -gt 0 ] ; do
    case "$1" in
        -h|--help)
            echo "usage: convert_and_annotate.sh [-h] [-p PROD_D] [-s SOURCE_D] [-c CONV_D] [-a ANNOT_D]"
            echo ""
            echo "options:"
            echo "  -h, --help  show this help message and exit"
            echo "  -p, --prod  set production directory encompassing"
            echo "                  1. an \"orig\" directory with the original transcriptions"
            echo "                  2. a \"conv\" directory where the converted transcriptions will be stored"
            echo "                  3. an \"annot\" directory where the annotated files will be stored"
            echo "  -s, --src   set directory where the original transcriptions are stored"
            echo "  -c, --conv  set directory where the converted transcriptions will be stored"
            echo "  -a, --annot set directory where the annotated transcriptions will be stored"
            exit 0
            ;;
        -p|--prod)
            PROD_D="$2"
            shift
            ;;
        -s|--src)
            SOURCE_D="$2"
            shift
            ;;
        -c|--conv)
            CONV_D="$2"
            shift
            ;;
        -a|--annot)
            ANNOT_D="$2"
            shift
            ;;
        --)
            shift
            break
            ;;
        *)
            echo "Unrecognized option $1" >&2
            exit 2
            ;;
    esac
    shift
done


if [ "$PROD_D" = "" ] ; then
    if [ "$SOURCE_D" = "" ] ; then
        echo "Source directory not specified. Use -s or --src to specify it. See --help for more." >&2
        exit 3
    fi

    if [ "$CONV_D" = "" ] ; then
        echo "Directory for converted transcriptions not specified. Use -c or --conv to specify it. See --help for more." >&2
        exit 3
    fi

    if [ "$ANNOT_D" = "" ] ; then
        echo "Directory for annotated files not specified. Use -a or --annot to specify it. See --help for more." >&2
        exit 3
    fi
else
    if ! [ "$SOURCE_D" = "" ] ; then
        echo "Source directory specification clashes with the production directory specification." >&2
        exit 3
    fi

    if ! [ "$CONV_D" = "" ] ; then
        echo "Specification of the directory for converted transcriptions clashes with the production directory specification." >&2
        exit 3
    fi

    if ! [ "$ANNOT_D" = "" ] ; then
        echo "Specification of the directory for annotated files clashes with the production directory specification." >&2
        exit 3
    fi

    SOURCE_D="$PROD_D/orig"
    CONV_D="$PROD_D/conv"
    ANNOT_D="$PROD_D/annot"
fi

if [ "$SOURCE_D" = "$CONV_D" ] || [ "$CONV_D" = "$ANNOT_D" ] || [ "$SOURCE_D" = "$ANNOT_D" ] ; then
    echo "All directories must be unique." >&2
    exit 3
fi

LOG_D="logs/annot_$( date "+%Y-%m-%d" )"
LOGFILE="$LOG_D/log_$( date "+%Y-%m-%d_%H-%M-%S" ).log"

if ! [ -d "$LOG_D" ] ; then
    mkdir "$LOG_D"
fi

echo "Convert and annotate $( date "+%Y-%m-%d %H:%M:%S" )" | tee -a "$LOGFILE"

echo "Transctiption conversion ($SOURCE_D -> $CONV_D)" | tee -a "$LOGFILE"
python3 transcription_conversion.py -f -i "$SOURCE_D" -o "$CONV_D" 2>/dev/stdout | tee -a "$LOGFILE" || ( echo "Errors occurred while converting" | tee -a "$LOGFILE" )
echo "Tagging ($CONV_D -> $ANNOT_D)" | tee -a "$LOGFILE"
python3 annotation.py -g -i "$CONV_D" -o "$ANNOT_D" 2>/dev/stdout | tee -a "$LOGFILE" || ( echo "Errors occurred while annotating" | tee -a "$LOGFILE" )

echo "Done $( date "+%Y-%m-%d %H:%M:%S" )" | tee -a "$LOGFILE"

echo "See $LOGFILE"