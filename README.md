# Automatic morphological annotation for CoCzeFLA

Scripts intended for automatic morphological annotation and transcription standard managing of [CoCzeFLA](https://coczefla.ff.cuni.cz/), Corpora of Czech as the First Language in Acquisition.

Developed on Python 3.12 and [MorfFlex CZ 2.0 + PDT-C 1.0](https://lindat.cz/repository/xmlui/handle/11234/1-4794) MorphoDiTa model.

## Morphological annotation

Use `chroma_tagging.py` to run morphological annotation on your CHAT files.

We use [MorphoDiTa](https://ufal.mff.cuni.cz/morphodita) for tokenization and morphological disambiguation. We then convert its output to MOR.

You can amend basic MorphoDiTa configuration used by the script by altering corresponding constants in `constants.py`. This includes:

- `constants.TOKENIZER_TYPE`: `type` parameter of the MorphoDiTa tokenizer
- `constants.TAGGER_PATH`: path to your MorphoDiTa tagger model

You can provide all relevant functions with your own tagger and tokenizer instances if you need finer control.

## Conversion to v3.1 transcription standard

Use `transcription_conversion.py` to convert a CHAT file to the v3.1 CoCzeFLA transcription standard.

## Set up

1. Install required Python packages (`python3 -m pip install -r requirements.txt`)
2. Run `python3 chroma_tagging.py` or `python3 transcription_conversion.py`

## Example usage

```bash
# directory as input
python3 chroma_tagging.py -i my_directory/with_unannotated_files/ -o my_directory/with_annotated_files/
# individual files as input
python3 chroma_tagging.py unannotated_file_1.txt unannotated_file_2.txt -o my_directory/with_annotated_files/
# input on stdin
python3 chroma_tagging.py -s

# directory as input
python3 transcription_conversion.py -i my_directory/with_old_files/ -o my_directory/with_converted_files/
# individual files as input
python3 transcription_conversion.py old_file_1.txt old_file_2.txt -o my_directory/with_converted_files/
# input on stdin
python3 transcription_conversion.py -s
```

## Contact

<ivakra@centrum.cz>

#TODO: ADD