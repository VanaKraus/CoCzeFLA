#!/usr/bin/bash

set -ueo pipefail

LOG_D="logs/annot-$( date "+%Y-%m-%d" )"

if ! [ -d "$LOG_D" ] ; then
    mkdir "$LOG_D"
fi

./transcription_conversion.py -f -i "production/orig" -o "production/conv"
./chroma_tagging.py -i "production/conv" -o "production/annot" 2>/dev/stdout | tee "$LOG_D/annot-$( date "+%H-%M-%S" ).log"