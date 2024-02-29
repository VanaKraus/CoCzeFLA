import constants

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
    # the function zpracovat() will later re-tag these appropriately

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