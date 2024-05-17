# Automatic morphological annotation for CoCzeFLA

Scripts intended for automatic morphological annotation and transcription standard managing of [CoCzeFLA](https://coczefla.ff.cuni.cz/), Corpora of Czech as the First Language in Acquisition.

Developed on Python 3.12 and [MorfFlex CZ 2.0 + PDT-C 1.0](https://lindat.cz/repository/xmlui/handle/11234/1-4794) MorphoDiTa model.

## Set up

1. Make sure you downloaded all the files (the entire repository; click *Code* > *Download ZIP*).
2. Install required Python packages (execute `python3 -m pip install -r requirements.txt` from the command line or see [Required packages](#required-packages)).
3. Download the [MorfFlex CZ 2.0 + PDT-C 1.0 MorphoDiTa tagger](https://lindat.cz/repository/xmlui/handle/11234/1-4794). We recommend to set `TAGGER_PATH` in `constants.py` to link to the location of the regular model version (with MorfFlex 2 this would be the location of `czech-morfflex2.0-pdtc1.0-220710.tagger`).
4. Run `python3 chroma_tagging.py` or `python3 transcription_conversion.py`.

## Required packages

| Package | Version |
| ------- | ------- |
| `corpy` | 0.6.1   |
| `nltk`  | 3.8.1   |

## Example usage

```bash
python3 chroma_tagging.py
python3 transcription_conversion.py

# directory as input with the output directory set
python3 chroma_tagging.py -i my_directory/with_unannotated_files/ -o my_directory/with_annotated_files/
# individual files as input with the output directory set
python3 chroma_tagging.py unannotated_file_1.txt unannotated_file_2.txt -o my_directory/with_annotated_files/
# input and output on stdin and stdout
python3 chroma_tagging.py -s
# see help
python3 chroma_tagging.py --help

# directory as input with the output directory set
python3 transcription_conversion.py -i my_directory/with_old_files/ -o my_directory/with_converted_files/
# individual files as input with the output directory set
python3 transcription_conversion.py old_file_1.txt old_file_2.txt -o my_directory/with_converted_files/
# input and output on stdin and stdout
python3 transcription_conversion.py -s
# see help
python3 transcription_conversion.py --help
```

## Arguments

Below is a list of arguments that can be used when executing the scripts from the command line.

- positional arguments: list of individual input files
- `-s`, `--std`: take input from stdin, print output to stdout
- `-i`, `--indir`: set directory with input files; overrides all positional arguments
- `-o`, `--outdir`: set output directory
- `-d`, `--tokenizer`: configure MorphoDiTa tokenizer type; overrides any tokenizer type specified in `constants.TOKENIZER_TYPE` (relevant for `chroma_tagging` only)
- `-t`, `--tagger`: configure MorphoDiTa tagger; overrides any tagger specified in `constants.TAGGER_PATH` (relevant for `chroma_tagging` only)
- `-h`, `--help`: see help

## Morphological annotation

Use `chroma_tagging.py` to run morphological annotation on your CHAT files.

We use [MorphoDiTa](https://ufal.mff.cuni.cz/morphodita) for tokenization and morphological disambiguation. We then convert its output to MOR.

We developed the script on the [MorfFlex CZ 2.0 + PDT-C 1.0](https://lindat.cz/repository/xmlui/handle/11234/1-4794) MorphoDiTa model. The model is required to run the script.

You can amend basic MorphoDiTa configuration used by the script by altering corresponding constants in `constants.py`. This includes:

- `constants.TOKENIZER_TYPE`: `type` parameter of the MorphoDiTa tokenizer
- `constants.TAGGER_PATH`: path to your MorphoDiTa tagger model

You can provide all relevant functions with your own tagger and tokenizer instances if you need finer control.

## Conversion to v3.1 transcription standard

Use `transcription_conversion.py` to convert a CHAT file to the v3.1 CoCzeFLA transcription standard.

## Contact

<ivakra@centrum.cz>

#TODO: ADD