#!/usr/bin/bash

set -ueo pipefail

SOURCE_D="production/orig"
CONV_D="production/conv"
ANNOT_D="production/annot"

LOG_D="logs/annot-$( date "+%Y-%m-%d" )"
LOGFILE="$LOG_D/log-$( date "+%H-%M-%S" ).log"

if ! [ -d "$LOG_D" ] ; then
    mkdir "$LOG_D"
fi

echo "Transctiption conversion ($SOURCE_D -> $CONV_D)" | tee -a "$LOGFILE"
python3 transcription_conversion.py -f -i "$SOURCE_D" -o "$CONV_D" 2>/dev/stdout | tee -a "$LOGFILE"
echo "Tagging ($CONV_D -> $ANNOT_D)" | tee -a "$LOGFILE"
python3 annotation.py -g -i "$CONV_D" -o "$ANNOT_D" 2>/dev/stdout | tee -a "$LOGFILE"

echo "See $LOGFILE"