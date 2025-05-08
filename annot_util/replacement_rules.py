from annot_util import constants
import annot_util.word_definitions as words

# list: tuple: (pattern, replacement)
CHAT_TO_PLAIN_TEXT: list[tuple[str, str]] = [
    # remove participant roles from the start of lines
    (r"\*[A-Z]{3}:\t", ""),
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
    (r"([a-zA-ZáäąčćďéěëęíłňńóöřšśťůúüýžźżÁÄĄČĆĎÉĚËĘÍŁŇŃÓÖŘŠŚŤŮÚÜÝŽŹŻ]):", r"\1"),
    # remove "^"
    (r"\^", r""),
    # words with a hyphen except for the conditional particle -li (e.g. "jsi-li")
    (
        r"((?:[ <]|^)[a-zA-ZáäąčćďéěëęíłňńóöřšśťůúüýžźżÁÄĄČĆĎÉĚËĘÍŁŇŃÓÖŘŠŚŤŮÚÜÝŽŹŻ]+)-(li[ >])",
        r"\1 \2",
    ),
    (
        r"((?:[ <]|^)[a-zA-ZáäąčćďéěëęíłňńóöřšśťůúüýžźżÁÄĄČĆĎÉĚËĘÍŁŇŃÓÖŘŠŚŤŮÚÜÝŽŹŻ]+)-([a-zA-ZáäąčćďéěëęíłňńóöřšśťůúüýžźżÁÄĄČĆĎÉĚËĘÍŁŇŃÓÖŘŠŚŤŮÚÜÝŽŹŻ]+[ >])",
        r"\1\2",
    ),
    # remove "<xyz>" followed by "[/]", "[//]", "[=! básnička]", "[=! zpěv]"
    # e.g. [básnička = poem]: *CHI:	<máme_tady_xxx_a_pěkný_bububínek_je_tam_jedno_kůzlátko_a_už_nevylezlo> [=! básnička].
    (
        r"<[ &+,'“”_a-zA-ZáäąčćďéěëęíłňńóöřšśťůúüýžźżÁÄĄČĆĎÉĚËĘÍŁŇŃÓÖŘŠŚŤŮÚÜÝŽŹŻ]*> \[(\/{1,2}|=! (básnička|zpěv))\]",
        "",
    ),
    # renove all material between "&=" and a space, including cases such as "&=imit:xxx"
    # e.g. "*CHI:	jenže ten traktor najednou &=imit:rána."
    (
        r"&=[_:a-zA-ZáäąčćďéěëęíłňńóöřšśťůúüýžźżÁÄĄČĆĎÉĚËĘÍŁŇŃÓÖŘŠŚŤŮÚÜÝŽŹŻ]+",
        "",
    ),
    # remove all material between "&=0" or "&+" and first non-letter character
    # e.g. "*MOT:	toho &vybavová vybarvování."; "*CHI:	koupu 0se 0ve vodě ."
    (
        r"(&\+|&=0)[_a-zA-ZáäąčćďéěëęíłňńóöřšśťůúüýžźżÁÄĄČĆĎÉĚËĘÍŁŇŃÓÖŘŠŚŤŮÚÜÝŽŹŻ]+",
        "",
    ),
    # remove uncertainty and repetition marking, [?] or e.g. [x 2]
    # an optional space after the number, because there was a line with "[x 4 ] ." at which the script broke down
    (
        r"<([ &+,“”_a-zA-ZáäąčćďéěëęíłňńóöřšśťůúüýžźżÁÄĄČĆĎÉĚËĘÍŁŇŃÓÖŘŠŚŤŮÚÜÝŽŹŻ]*)> \[(x [0-9]+ ?|\?)\]",
        r"\1",
    ),
    # "přišels [:přišel jsi]" is to be analyzed as "přišel jsi"
    (
        r"[a-zA-ZáäąčćďéěëęíłňńóöřšśťůúüýžźżÁÄĄČĆĎÉĚËĘÍŁŇŃÓÖŘŠŚŤŮÚÜÝŽŹŻ]+ \[:([ a-zA-ZáäąčćďéěëęíłňńóöřšśťůúüýžźżÁÄĄČĆĎÉĚËĘÍŁŇŃÓÖŘŠŚŤŮÚÜÝŽŹŻ]+)\]",
        r"\1",
    ),
    # interjections with underscores
    (r"_", r""),
    # remove "(.)", "[*]"
    (r"\(.\)", r""),
    (r"\[\*\]", r""),
    # remove "xxx"
    (r"xxx", r""),
    # remove "+<" from the beginning of lines
    (r"\+<", ""),
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
    r"^[ ,“”0a-zA-ZáäąčćďéěëęíłňńóöřšśťůúüýžźżÁÄĄČĆĎÉĚËĘÍŁŇŃÓÖŘŠŚŤŮÚÜÝŽŹŻ]*(\.|\?|\!|\+\.\.\.|\+\/\.)$"
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
    "bysem": "v:aux|být-1&SG&cond&akt&impf",
    "bys": "v:aux|být-2&SG&cond&akt&impf",
    "bysi": "v:aux|být-2&SG&cond&akt&impf",
    "by": "v:aux|být-3&x_cislo&cond&akt&impf",
    "bychom": "v:aux|být-1&PL&cond&akt&impf",
    "bysme": "v:aux|být-1&PL&cond&akt&impf",
    "byste": "v:aux|být-2&PL&cond&akt&impf",
    # double lemmatization for forms of "aby.*" and "kdyby.*"
    "abych": "conj:sub_v:aux|aby_být-1&SG&cond&akt&impf",
    "abysem": "conj:sub_v:aux|aby_být-1&SG&cond&akt&impf",
    "abys": "conj:sub_v:aux|aby_být-2&SG&cond&akt&impf",
    "abysi": "conj:sub_v:aux|aby_být-2&SG&cond&akt&impf",
    "aby": "conj:sub_v:aux|aby_být-3&x_cislo&cond&akt&impf",
    "abychom": "conj:sub_v:aux|aby_být-1&PL&cond&akt&impf",
    "abyste": "conj:sub_v:aux|aby_být-2&PL&cond&akt&impf",
    "abysme": "conj:sub_v:aux|aby_být-1&PL&cond&akt&impf",
    "kdybych": "conj:sub_v:aux|kdyby_být-1&SG&cond&akt&impf",
    "kdybysem": "conj:sub_v:aux|kdyby_být-1&SG&cond&akt&impf",
    "kdybys": "conj:sub_v:aux|kdyby_být-2&SG&cond&akt&impf",
    "kdybysi": "conj:sub_v:aux|kdyby_být-2&SG&cond&akt&impf",
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
    # tagged as subordinate conjunction by MorphoDiTa
    "li": "part|li",
    # to be tagged as interjections
    "emem": "int|emem",
    # with the guesser on, "hají" gets lemmatized as "hat"
    "hají": "int|hají",
}

_ADJ_ADV_COMPDEG_LEMMA_OVERRIDES: dict[str, str] = (
    {s: "dobrý" for s in ["lepší", "nejlepší"]}
    | {s: "špatný" for s in ["horší", "nejhorší"]}
    | {s: "dlouhý" for s in ["delší", "nejdelší"]}
    | {s: "malý" for s in ["menší", "nejmenší"]}
    | {s: "velký" for s in ["větší", "největší"]}
    | {s: "dobře" for s in ["lépe", "líp", "nejlépe", "nejlíp"]}
    | {s: "špatně" for s in ["hůře", "hůř", "nejhůře", "nejhůř"]}
    | {
        s: "brzy"
        for s in [
            "dříve",
            "dřív",
            "dřívěji",
            "dřívějc",
            "nejdříve",
            "nejdřív",
            "nejdřívěji",
            "nejdřívějc",
        ]
    }
    | {s: "dlouho" for s in ["déle", "dýl", "nejdéle", "nejdýl"]}
    | {s: "vysoko" for s in ["výše", "výš", "vejš", "nejvýše", "nejvýš", "nejvejš"]}
    | {s: "málo" for s in ["méně", "míň", "nejméně", "nejmíň"]}
    | {s: "hodně" for s in ["více", "víc", "nejvíce", "nejvíc"]}
    | {s: "těžce" for s in ["tíž", "tíže", "tížeji", "nejtíž", "nejtíže", " nejtížeji"]}
    | {
        s: "snadno"
        for s in [
            "snáz",
            "snáze",
            "snázeji",
            "snadněji",
            "snadnějc",
            "nejsnáz",
            "nejsnáze",
            "nejsnadněji",
            "nejsnadnějc",
        ]
    }
    | {
        s: "hluboko"
        for s in [
            "hloub",
            "hlouběji",
            "hloubějc",
            "nejhloub",
            "nejhlouběji",
            "nejhloubějc",
        ]
    }
    | {
        s: "široko"
        for s in [
            "šíře",
            "šíř",
            "šířeji",
            "šířejc",
            "nejšíře",
            "nejšíř",
            "nejšířeji",
            "nejšířejc",
        ]
    }
    | {s: "úzce" for s in ["úže", "úžeji", "úžejc", "nejúže", "nejúžeji", "nejúžejc"]}
)

# dict: {MorfFlex lemma: target lemma}
MOR_MLEMMAS_LEMMA_OVERRIDES: dict[str, str] = {
    "lidé": "člověk"
} | _ADJ_ADV_COMPDEG_LEMMA_OVERRIDES

# dict: {word form: target lemma}
MOR_WORDS_LEMMA_OVERRIDES: dict[str, str] = {
    word: word_list[0]
    for word_list in [
        words.POSS_PRONOUN_3PL,
        words.POSS_PRONOUN_M_N_3SG,
        words.POSS_PRONOUN_F_3SG,
    ]
    for word in word_list
} | {"zem": "zem"}

# dict: {lemma: pos} | dict: {lemma: word: pos}
# if word == '_' denotes the default value
MOR_POS_OVERRIDES: dict[str, dict[str, str]] = (
    {lemma: {"_": "adv:pro"} for lemma in words.PRONOMINAL_ADVERBS}
    | {lemma: {"_": "adv:pro:neg"} for lemma in words.NEGATIVE_PRONOMINAL_ADVERBS}
    | {
        lemma: {"_": "n:pt"}
        for lemma in words.PLURAL_INVARIABLE_NOUNS
        + words.PLURAL_INVARIABLE_PROPER_NOUNS
    }
    | {lemma: {"_": "v:mod"} for lemma in words.MODAL_VERBS}
    | {
        "každý": {"_": "pro:indef"},
        "svůj": {"_": "pro:refl:poss"},
        "čí": {"_": "pro:int:poss"},
        "být": {
            "je": "v:cop",
            "jsou": "v:cop",
            "seš": "v:cop",
            "nejsem": "v:cop",
            "nejsi": "v:cop",
            "není": "v:cop",
            "nejsme": "v:cop",
            "nejste": "v:cop",
            "nejsou": "v:cop",
            "buď": "v:cop",
            "buďme": "v:cop",
            "buďte": "v:cop",
            "nebuď": "v:cop",
            "nebuďme": "v:cop",
            "nebuďte": "v:cop",
            "být": "v:cop",
            "nebýt": "v:cop",
            "byl": "v:cop",
            "byla": "v:cop",
            "bylo": "v:cop",
            "byli": "v:cop",
            "byly": "v:cop",
            "nebyl": "v:cop",
            "nebyla": "v:cop",
            "nebylo": "v:cop",
            "nebyli": "v:cop",
            "nebyly": "v:cop",
            "_": "v:x",
        },
        "chtít": {"_": "v:x"},
        "mít": {"_": "v:x"},
    }
)

# lines not to be annotated
SKIP_LINES: list[str] = [".", "0 .", "+/.", "+...", "!", "?"]


# verify integrity
for key in MOR_POS_OVERRIDES:
    if "_" not in MOR_POS_OVERRIDES[key]:
        raise ValueError(f"MOR_POS_OVERRIDE config: no default value for lemma '{key}'")
