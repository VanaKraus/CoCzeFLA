import constants
import word_definitions as words

TRANSFORM_REGEX = [
    # remove participant roles from the start of lines
    (r'\*(CHI|MOT|FAT|GRA|SIS|SIT|BRO|ADU):\t', ''),

    # remove all material between "&" and ">", e.g. in "<v &po> [//] v postýlce"
    (r"&[aábcčdďeéěfghiíjklmnňoópqrřsštťuúůvwxyýzžAÁBCČDĎEÉĚFGHIÍJKLMNŇOÓPQRŘSŠTŤUÚŮVWXYÝZŽ]+>", ">"),

    # remove "<xyz>" followed by "[/]", "[//]" or e.g. "[=! básnička]"
    # e.g. [básnička = poem]: *CHI:	<máme_tady_xxx_a_pěkný_bububínek_je_tam_jedno_kůzlátko_a_už_nevylezlo> [=! básnička].
    (r"<[ aábcčdďeéěfghiíjklmnňoópqrřsštťuúůvwxyýzžAÁBCČDĎEÉĚFGHIÍJKLMNŇOÓPQRŘSŠTŤUÚŮVWXYÝZŽ]+> \[/{1,2}\]", ""),
    (r"<[ _aábcčdďeéěfghiíjklmnňoópqrřsštťuúůvwxyýzžAÁBCČDĎEÉĚFGHIÍJKLMNŇOÓPQRŘSŠTŤUÚŮVWXYÝZŽ]+> \[=! (básnička|písnička|zpěv)\]", ""),
    
    # renove all material between "&=" and a space, including cases such as "&=imit:xxx"
    # e.g. "*CHI:	jenže ten traktor najednou &=imit:rána."
    (r"&=[aábcčdďeéěfghiíjklmnňoópqrřsštťuúůvwxyýzž:AÁBCČDĎEÉĚFGHIÍJKLMNŇOÓPQRŘSŠTŤUÚŮVWXYÝZŽ]+", ""),
    
    # remove all material between "0" or "&" and a space, e.g. "*MOT:	toho &vybavová vybarvování."
    (r"[0&][aábcčdďeéěfghiíjklmnňoópqrřsštťuúůvwxyýzžAÁBCČDĎEÉĚFGHIÍJKLMNŇOÓPQRŘSŠTŤUÚŮVWXYÝZŽ]+", ""),
    
    # <xyz> [=? xxx] or <xyz> [=! xxx]
    (r"\[\=[\?\!] [ aábcčdďeéěfghiíjklmnňoópqrřsštťuúůvwxyýzžAÁBCČDĎEÉĚFGHIÍJKLMNŇOÓPQRŘSŠTŤUÚŮVWXYÝZŽ]+\]", ""),

    # remove repetition marking, e.g. [x 2]
    # an optional space after the number, because there was a line with "[x 4 ] ." at which the script broke down
    (r"\[x [0123456789]+ ?\]", ""),

    # "přišels [:přišel jsi]" is to be analyzed as "přišel jsi"
    (r"[aábcčdďeéěfghiíjklmnňoópqrřsštťuúůvwxyýzžAÁBCČDĎEÉĚFGHIÍJKLMNŇOÓPQRŘSŠTŤUÚŮVWXYÝZŽ]+ \[:([ aábcčdďeéěfghiíjklmnňoópqrřsštťuúůvwxyýzžAÁBCČDĎEÉĚFGHIÍJKLMNŇOÓPQRŘSŠTŤUÚŮVWXYÝZŽ]+)\]", r"\1"),

    # lengthened vowels
    (r"([eaiyouáéěíýóúůrsš]):", r"\1")
]

TRANSFORM_STR_REPLACE = [
    # interjections with underscores
    ("_", ""),
    
    # remove "^", "(.)", "[*]"
    ("^", ""),
    ("(.)",""),
    ("[*]", ""),
    
    # remove "xxx", "yyy"
    ("xxx", ""),
    ("yyy", ""),

    # remove "+<" from the beginning of lines
    ("+<", ""),

    # remove all the remaining "<"s, "*"s, "[?]"s, and "[!]"s, e.g. "*CHI: chci  <žlutou> [?] kytku."
    ("<", ""),
    (">", ""),
    ("[?]", ""),
    ("[!]", ""),
    
    # added: remove quote marks
    ("\"", ""),
    ("“", ""),
    ("”", ""),

    # token ending in @i, @z:ip, @z:ia, @z:in = to be tagged as an interjection
    # bacashooga is a random string not overlapping with any existing Czech words
    ("@i", constants.PLACEHOLDER_INTERJECTION),
    ("@z:ip", constants.PLACEHOLDER_INTERJECTION),
    ("@z:ia", constants.PLACEHOLDER_INTERJECTION),
    ("@z:in", constants.PLACEHOLDER_INTERJECTION),
    # token ending in @c, @n = tag is to end with -neo
    ("@c", constants.PLACEHOLDER_NEOLOGISM),
    ("@n", constants.PLACEHOLDER_NEOLOGISM),
    # token ending in @z:c = tag is to end with -ciz
    ("@z:c", constants.PLACEHOLDER_CIZ),
    # the function mor_line() will later re-tag these appropriately

    # Nee > ne
    ("Nee","ne"),
    ("nee","ne"),
    
    # formatting adjustment
    ("?", " ?"),
    ("!", " !"),
    (".", " ."),
    (",", " ,"),
    ("  ", " ")
]

MOR_WORDS_HARDCODED = {
    # lexically specified "exceptions": "mami" always to be tagged as "n|máma-5&SG&F" etc.
    "mami": "n|máma-5&SG&F",
    "no": "part|no",
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
        
    # double lemmatization for forms of "aby.*" and "kdyby.*" + "ses", "sis", and "zač"
    "abych": "conj:sub_v:aux|aby_být-1&SG&cond&akt&impf",
    "abys": "conj:sub_v:aux|aby_být-2&SG&cond&akt&impf",
    "aby": "conj:sub_v:aux|aby_být-1&x_cislo&cond&akt&impf",
    "abychom": "conj:sub_v:aux|aby_být-1&PL&cond&akt&impf",
    "abyste": "conj:sub_v:aux|aby_být-2&PL&cond&akt&impf",
    "abysme": "conj:sub_v:aux|aby_být-1&PL&cond&akt&impf",
    "kdybych": "conj:sub_v:aux|aby_být-1&SG&cond&akt&impf",
    "kdybys": "conj:sub_v:aux|aby_být-2&SG&cond&akt&impf",
    "kdyby": "conj:sub_v:aux|aby_být-1&x_cislo&cond&akt&impf",
    "kdybychom": "conj:sub_v:aux|aby_být-1&PL&cond&akt&impf",
    "kdybysme": "conj:sub_v:aux|aby_být-1&PL&cond&akt&impf",
    "kdybyste": "conj:sub_v:aux|aby_být-2&PL&cond&akt&impf",
    "ses": "pro:refl_v:aux|se_být-4&SG_2&SG&ind&pres&akt&impf",
    "sis": "pro:refl_v:aux|se_být-3&SG_2&SG&ind&pres&akt&impf",
    "zač": "prep_pro:int|za_co-4&SG&N"
}

# tuple: (list of forms, target lemma)
MOR_WORDS_LEMMA_OVERRIDES = [
    (l_list, l_list[0]) for l_list in [
        words.PERS_PRONOUN_1PL,
        words.PERS_PRONOUN_2PL,
        words.POSS_PRONOUN_1PL,
        words.POSS_PRONOUN_2PL,
        words.POSS_PRONOUN_3PL,
        words.POSS_PRONOUN_M_N_3SG,
        words.POSS_PRONOUN_F_3SG
    ]
]