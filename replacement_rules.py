import constants
import word_definitions as words

# list: tuple: (pattern, replacement)
CHAT_TO_PLAIN_TEXT: list[tuple[str, str]] = [
    # remove participant roles from the start of lines
    (r"\*[A-Z]{3}:\t", ""),
    # remove "<xyz>" followed by "[/]", "[//]", "[=! básnička]", "[=! zpěv]"
    # e.g. [básnička = poem]: *CHI:	<máme_tady_xxx_a_pěkný_bububínek_je_tam_jedno_kůzlátko_a_už_nevylezlo> [=! básnička].
    (
        r"<[ &,_a-zA-ZáčďéěíňóřšťůúýžÁČĎÉĚÍŇÓŘŠŤŮÚÝŽ]*> \[(\/{1,2}|=! (básnička|zpěv))\]",
        "",
    ),
    # renove all material between "&=" and a space, including cases such as "&=imit:xxx"
    # e.g. "*CHI:	jenže ten traktor najednou &=imit:rána."
    (
        r"&=[a-zA-ZáčďéěíňóřšťůúýžÁČĎÉĚÍŇÓŘŠŤŮÚÝŽ:]+",
        "",
    ),
    # remove all material between "0" or "&" and first non-letter character
    # e.g. "*MOT:	toho &vybavová vybarvování."; "*CHI:	koupu 0se 0ve vodě ."
    (
        r"[0&][a-zA-ZáčďéěíňóřšťůúýžÁČĎÉĚÍŇÓŘŠŤŮÚÝŽ]+",
        "",
    ),
    # remove uncertainty and repetition marking, [?] or e.g. [x 2]
    # an optional space after the number, because there was a line with "[x 4 ] ." at which the script broke down
    (r"<([ &,_a-zA-ZáčďéěíňóřšťůúýžÁČĎÉĚÍŇÓŘŠŤŮÚÝŽ]*)> \[(x [0-9]+ ?|\?)\]", r"\1"),
    # "přišels [:přišel jsi]" is to be analyzed as "přišel jsi"
    (
        r"[a-zA-ZáčďéěíňóřšťůúýžÁČĎÉĚÍŇÓŘŠŤŮÚÝŽ]+ \[:([ a-zA-ZáčďéěíňóřšťůúýžÁČĎÉĚÍŇÓŘŠŤŮÚÝŽ]+)\]",
        r"\1",
    ),
    # interjections with underscores
    (r"_", r""),
    # remove "^", "(.)", "[*]"
    (r"\^", r""),
    (r"\(.\)", r""),
    (r"\[\*\]", r""),
    # remove "xxx"
    (r"xxx", r""),
    # remove "+<" from the beginning of lines
    (r"\+<", ""),
    # remove quote marks
    (r"“|”", r""),
    # placeholders are strings not overlapping with any existing Czech words
    # token ending in @i, @z:ip, @z:ia, @z:in = to be marked as an interjection
    (r"@i|@z:ip|@z:ia|@z:in", constants.PLACEHOLDER_INTERJECTION),
    # token ending in @c, @n = tag is to be marked as neologism
    (r"@c|@n", constants.PLACEHOLDER_NEOLOGISM),
    # token ending in @z:f = tag is to be marked as foreign
    (r"@z:f", constants.PLACEHOLDER_FOREIGN),
    # token ending in @z:m is to be ignored
    (r"@z:m", r""),
    # lengthened sounds
    (r"([a-zA-ZáčďéěíňóřšťůúýžÁČĎÉĚÍŇÓŘŠŤŮÚÝŽ]):", r"\1"),
    # the function mor_line() will later re-tag these appropriately
    # Nee > ne
    (r"[Nn]ee", r"ne"),
    # remove excessive whitespaces from multi-character symbols
    (r"\+ \. \. \.", r"+..."),
    (r"\+\/ \.", r"+/."),
    (r" \[= ! ", r" [=! "),
    # remove excessive whitespaces and turn them into regular spaces
    (r"\s{1,}", r" "),
    # remove commas that are not separating anything
    (r"(, )+(\.|\?|\!|\+\.\.\.|\+\/\.|,)", r"\2"),
    (r"^\s+,", r""),
    # remove leading and trailing whitespaces
    (r"^\s+", r""),
    (r"\s+$", r""),
]

# when a string matches this pattern, we count it as plaintext
PLAIN_TEXT_CRITERIA: str = (
    r"^[ ,0a-zA-ZáčďéěíňóřšťůúýžÁČĎÉĚÍŇÓŘŠŤŮÚÝŽ]*(\.|\?|\!|\+\.\.\.|\+\/\.)$"
)

# dict: {word, MOR word}
MOR_WORDS_OVERRIDES: dict[str, str] = {
    # lexically specified "exceptions": "mami" always to be tagged as "n|máma-5&SG&F" etc.
    "mami": "n|máma-5&SG&F",
    "koukej": "v|koukat-2&SG&imp&akt&impf",
    "zzz": "x|zzz",
    # forms of "rád" to be tagged as follows
    "rád": "adj:short|rád-1&SG&M",
    "ráda": "adj:short|rád-1&SG&F",
    "rádo": "adj:short|rád-1&SG&N",
    "rádi": "adj:short|rád-1&PL&M",
    "rády": "adj:short|rád-1&PL&F",
    # reflexive pronouns "se" and "si" to be tagged as follows
    "se": "pro:refl|se-4&SG",
    "si": "pro:refl|se-3&SG",
    # the uninflected "jejichž" to be tagged as follows
    "jejichž": "pro:rel:poss|jejichž-x_pad&x_cislo&x_jmenny_rod",
    # conditional auxiliaries as MorfFlex2 doesn't assign person and number to them
    "bych": "v:aux|být-1&SG&cond&akt&impf",
    "bys": "v:aux|být-2&SG&cond&akt&impf",
    "by": "v:aux|být-3&x_cislo&cond&akt&impf",
    "bychom": "v:aux|být-1&PL&cond&akt&impf",
    "bysme": "v:aux|být-1&PL&cond&akt&impf",
    "byste": "v:aux|být-2&PL&cond&akt&impf",
    # double lemmatization for forms of "aby.*" and "kdyby.*"
    "abych": "conj:sub_v:aux|aby_být-1&SG&cond&akt&impf",
    "abys": "conj:sub_v:aux|aby_být-2&SG&cond&akt&impf",
    "aby": "conj:sub_v:aux|aby_být-3&x_cislo&cond&akt&impf",
    "abychom": "conj:sub_v:aux|aby_být-1&PL&cond&akt&impf",
    "abyste": "conj:sub_v:aux|aby_být-2&PL&cond&akt&impf",
    "abysme": "conj:sub_v:aux|aby_být-1&PL&cond&akt&impf",
    "kdybych": "conj:sub_v:aux|kdyby_být-1&SG&cond&akt&impf",
    "kdybys": "conj:sub_v:aux|kdyby_být-2&SG&cond&akt&impf",
    "kdyby": "conj:sub_v:aux|kdyby_být-3&x_cislo&cond&akt&impf",
    "kdybychom": "conj:sub_v:aux|kdyby_být-1&PL&cond&akt&impf",
    "kdybysme": "conj:sub_v:aux|kdyby_být-1&PL&cond&akt&impf",
    "kdybyste": "conj:sub_v:aux|kdyby_být-2&PL&cond&akt&impf",
    # reflexive pronouns "se" and "si" to be tagged as follows
    "ses": "pro:refl_v:aux|se_být-4&SG_2&SG&ind&pres&akt&impf",
    "sis": "pro:refl_v:aux|se_být-3&SG_2&SG&ind&pres&akt&impf",
    # zač/nač/oč
    "zač": "prep_pro:int|za_co-4&SG&N",
    "nač": "prep_pro:int|na_co-4&SG&N",
    "oč": "prep_pro:int|o_co-4&SG&N",
    # to be tagged as interjections
    "emem": "int|emem",
}

# dict: {MorfFlex lemma: target lemma}
MOR_MLEMMAS_LEMMA_OVERRIDES: dict[str, str] = {"tento": "ten", "tenhle": "ten"}

# dict: {word form: target lemma}
MOR_WORDS_LEMMA_OVERRIDES: dict[str, str] = {
    word: word_list[0]
    for word_list in [
        words.POSS_PRONOUN_3PL,
        words.POSS_PRONOUN_M_N_3SG,
        words.POSS_PRONOUN_F_3SG,
    ]
    for word in word_list
}

# dict: {lemma: pos}
MOR_POS_OVERRIDES: dict[str, str] = (
    {lemma: "adv:pro" for lemma in words.PRONOMINAL_ADVERBS}
    | {lemma: "adv:pro:neg" for lemma in words.NEGATIVE_PRONOMINAL_ADVERBS}
    | {lemma: "n:pt" for lemma in words.PLURAL_INVARIABLE_NOUNS}
    | {lemma: "n:prop:pt" for lemma in words.PLURAL_INVARIABLE_PROPER_NOUNS}
    | {lemma: "v:mod" for lemma in words.MODAL_VERBS}
    | {
        "každý": "pro:indef",
        "svůj": "pro:refl:poss",
        "čí": "pro:int:poss",
        "být": "v:aux/cop",
    }
)

# lines not to be annotated
SKIP_LINES: list[str] = [".", "0 ."]
