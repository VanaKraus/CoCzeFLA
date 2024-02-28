#!/usr/bin/env python3

""" 
the script for the morphological analysis of the longitudinal corpus of spoken Czech child-adult interactions

MIT License

Copyright (c) 2023 Jakub Sláma
Copyright (c) 2024 Ivan Kraus

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

***

fundamantelly, all the functions need to be run, but for analyzing a specific file, you need to run only the last function, 
file_to_file(), which incorporates all the other functions and from a file creates a new file with morphological tiers added

for details, explanations and the like, consult the paper submitted to the the journal Language Resources and Evaluation

Chromá, Anna – Sláma, Jakub – Matiasovitsová, Klára – Treichelová, Jolana (submitted): 
A morphologically annotated longitudinal corpus of spoken Czech child-adult interactions. 
Language Resources and Evaluation.

if you have any questions, feel free to contact me at slama@ujc.cas.cz, but please know that I'm a linguist, not a person 
who specializes in coding, Python etc., so this script is quite clearly not the optimal way to do its job (and processing 
files with this script is thus rather slow), even though it thus this job as well as it is supposed to

"""

import constants

from corpy.morphodita import Tagger

import argparse
import re
import sys
import os

class CoCzeFLATaggerError(Exception):
    pass

"""
a function for using the MorphoDiTa tagger, see https://ufal.mff.cuni.cz/morphodita
the directory needs to be adjusted

example of use: tokenize("vidím Mařenku")
→ output = a list of Token objects: 
[Token(word='vidím', lemma='vidět', tag='VB-S---1P-AA---'),
 Token(word='Mařenku', lemma='Mařenka', tag='NNFS4-----A----')]

"""

def tokenize(text, tagger:Tagger):
    output = list(tagger.tag(text, convert="strip_lemma_id"))
    return output


"""
this function takes a corpus line in the CHAT (CHILDES) format as the input and transforms it into plain text
if the line is not to be tagged (e.g. contains only a hesitation sound), the function returns the value "NA" instead

example of input: "*MOT:	toho &vybavová vybarvování."
example of output: 'toho vybarvování .'

"""

def transform(input):
    if input.startswith("@"):
        result = "NA"
        return result
    elif input.startswith("%"):
        result = "NA"
        return result 
    elif input.startswith("*CHI:"):
        result = input.replace("*CHI:	","")
    elif input.startswith("*MOT:"):
        result = input.replace("*MOT:	","")
    elif input.startswith("*FAT:"):
        result = input.replace("*FAT:	","")
    elif input.startswith("*GRA:"):
        result = input.replace("*GRA:	","")
    elif input.startswith("*SIS:"):
        result = input.replace("*SIS:	","")
    elif input.startswith("*SIT:"):
        result = input.replace("*SIT:	","")
    elif input.startswith("*BRO:"):
        result = input.replace("*BRO:	","")
    elif input.startswith("*ADU:"):
        result = input.replace("*ADU:	","")
    else:
        result = input
    
    # interjections with underscores
    result = result.replace("_", "")
    
    # lengthened vowels
    result = result.replace("e:","e").replace("a:","a").replace("i:","i").replace("y:","y").replace("o:","o").replace("u:","u").replace("á:","á").replace("é:","é").replace("ě:","ě").replace("í:","í").replace("ý:","ý").replace("ó:","ó").replace("ú:","ú").replace("ů:","ů").replace("r:","r").replace("s:","s").replace("š:","š")
    
    # remove "^", "(.)", "[*]"
    result = result.replace("^", "").replace("(.)","").replace("[*]", "")
    
    # remove "xxx", "yyy"
    result = result.replace("xxx", "").replace("yyy", "")

    # remove "+<" from the beginning of lines
    result = result.replace("+<", "")

    # remove all material between "&" and ">", e.g. in "<v &po> [//] v postýlce"
    result = re.sub(r"&[aábcčdďeéěfghiíjklmnňoópqrřsštťuúůvwxyýzžAÁBCČDĎEÉĚFGHIÍJKLMNŇOÓPQRŘSŠTŤUÚŮVWXYÝZŽ]+>", ">", result)
        
    # remove "<xyz>" followed by "[/]", "[//]" or e.g. "[=! básnička]"
    # e.g. [básnička = poem]: *CHI:	<máme_tady_xxx_a_pěkný_bububínek_je_tam_jedno_kůzlátko_a_už_nevylezlo> [=! básnička].
    result = re.sub(r"<[ aábcčdďeéěfghiíjklmnňoópqrřsštťuúůvwxyýzžAÁBCČDĎEÉĚFGHIÍJKLMNŇOÓPQRŘSŠTŤUÚŮVWXYÝZŽ]+> \[//\]", "", result)
    result = re.sub(r"<[ aábcčdďeéěfghiíjklmnňoópqrřsštťuúůvwxyýzžAÁBCČDĎEÉĚFGHIÍJKLMNŇOÓPQRŘSŠTŤUÚŮVWXYÝZŽ]+> \[/\]", "", result)
    result = re.sub(r"<[ _aábcčdďeéěfghiíjklmnňoópqrřsštťuúůvwxyýzžAÁBCČDĎEÉĚFGHIÍJKLMNŇOÓPQRŘSŠTŤUÚŮVWXYÝZŽ]+> \[=! básnička\]", "", result)
    result = re.sub(r"<[ _aábcčdďeéěfghiíjklmnňoópqrřsštťuúůvwxyýzžAÁBCČDĎEÉĚFGHIÍJKLMNŇOÓPQRŘSŠTŤUÚŮVWXYÝZŽ]+> \[=! písnička\]", "", result)
    result = re.sub(r"<[ _aábcčdďeéěfghiíjklmnňoópqrřsštťuúůvwxyýzžAÁBCČDĎEÉĚFGHIÍJKLMNŇOÓPQRŘSŠTŤUÚŮVWXYÝZŽ]+> \[=! zpěv\]", "", result)
    
    # renove all material between "&=" and a space, including cases such as "&=imit:xxx"
    # e.g. "*CHI:	jenže ten traktor najednou &=imit:rána."
    result = re.sub(r"&=[aábcčdďeéěfghiíjklmnňoópqrřsštťuúůvwxyýzž:AÁBCČDĎEÉĚFGHIÍJKLMNŇOÓPQRŘSŠTŤUÚŮVWXYÝZŽ]+", "", result)
    
    # remove all material between "0" and a space
    result = re.sub(r"0[aábcčdďeéěfghiíjklmnňoópqrřsštťuúůvwxyýzžAÁBCČDĎEÉĚFGHIÍJKLMNŇOÓPQRŘSŠTŤUÚŮVWXYÝZŽ]+", "", result)
    
    # remove all material between "&" and a space, e.g. "*MOT:	toho &vybavová vybarvování."
    result = re.sub(r"&[aábcčdďeéěfghiíjklmnňoópqrřsštťuúůvwxyýzžAÁBCČDĎEÉĚFGHIÍJKLMNŇOÓPQRŘSŠTŤUÚŮVWXYÝZŽ]+", "", result)
    
    # <xyz> [=? xxx]
    result = re.sub("\[\=\? [ aábcčdďeéěfghiíjklmnňoópqrřsštťuúůvwxyýzžAÁBCČDĎEÉĚFGHIÍJKLMNŇOÓPQRŘSŠTŤUÚŮVWXYÝZŽ]+\]", "", result)
    
    # <xyz> [=! xxx]
    result = re.sub("\[\=\! [ aábcčdďeéěfghiíjklmnňoópqrřsštťuúůvwxyýzžAÁBCČDĎEÉĚFGHIÍJKLMNŇOÓPQRŘSŠTŤUÚŮVWXYÝZŽ]+\]", "", result)
    
    # remove all the remaining "<"s, "*"s, "[?]"s, and "[!]"s, e.g. "*CHI: chci  <žlutou> [?] kytku."
    result = result.replace("<", "").replace(">", "").replace("[?]", "").replace("[!]", "")
    
    # added: remove quote marks
    result = result.replace("\"", "").replace("“", "").replace("”", "")
    
    # remove repetition marking, e.g. [x 2]
    # an optional space after the number, because there was a line with "[x 4 ] ." at which the script broke down
    result = re.sub(r"\[x [0123456789]+ ?\]", "", result)
    
    # "přišels [:přišel jsi]" is to be analyzed as "přišel jsi"
    result = re.sub("[aábcčdďeéěfghiíjklmnňoópqrřsštťuúůvwxyýzžAÁBCČDĎEÉĚFGHIÍJKLMNŇOÓPQRŘSŠTŤUÚŮVWXYÝZŽ]+ \[:", "", result)
    result = result.replace("]", "")
    
    # token ending in @i, @z:ip, @z:ia, @z:in = to be tagged as an interjection
    # bacashooga is a random string not overlapping with any existing Czech words
    result = result.replace("@i", constants.PLACEHOLDER_INTERJECTION)
    result = result.replace("@z:ip", constants.PLACEHOLDER_INTERJECTION)
    result = result.replace("@z:ia", constants.PLACEHOLDER_INTERJECTION)
    result = result.replace("@z:in", constants.PLACEHOLDER_INTERJECTION)
    # token ending in @c, @n = tag is to end with -neo
    result = result.replace("@c", constants.PLACEHOLDER_NEOLOGISM)
    result = result.replace("@n", constants.PLACEHOLDER_NEOLOGISM)
    # token ending in @z:c = tag is to end with -ciz
    result = result.replace("@z:c", constants.PLACEHOLDER_CIZ)
    # the function zpracovat() will later re-tag these appropriately
    
    # if the result consists only of spaces or punctuation marks, return "NA"
    alt_result = result
    alt_result = re.sub("[ .,?!0+…]+", "", alt_result)
    if alt_result == "":
        result = "NA"
        
    # Nee > ne
    result = result.replace("Nee","ne").replace("nee","ne")
    
    # formatting adjustment
    result = result.replace("?", " ?").replace("!", " !").replace(".", " .").replace(",", " ,").replace("  ", " ")
    
    return result

"""
input: (tag, word, lemma) provided in the Token object by tokenize()
extracts the POS information from the tag and returns the POS value in the MOR format
lemma in the input as well, because of the tagging of plural invariable nouns
word in the input as well, because of the tagging of proper names

example of use: pos("NNFS4-----A----", "Mařenku", "Mařenka")
→ output: 'n:prop'

"""

def pos(tag, word, lemma):
    result = ""
    if tag.startswith("Z"):
        result = "Z"
    if tag.startswith("X"):
        result = "x"
    elif tag.startswith("N"):
        result = "n"
        if lemma in constants.PLURAL_INVARIABLE_NOUNS: # pomnožná
            result = "n:pt" # plural invariable nouns
        if word == word.capitalize(): # proper nouns
            result = "n:prop"
            if lemma in constants.PLURAL_INVARIABLE_PROPER_NOUNS: # a proper noun that is also a plural invariable noun
                result = "n:prop:pt"
    elif tag.startswith("A"):
        result = "adj"
        if tag.startswith("AC"):
            result = "adj:short"
        elif tag.startswith("AU"):
            result = "adj:poss"
    elif tag.startswith("P"):
        result = "pro"
        if tag.startswith("PD"):
            result = "pro:dem"
        elif tag.startswith("PP") or tag.startswith("PH") or tag.startswith("P5"):
            result = "pro:pers"
        elif tag.startswith("P1") or tag.startswith("P9") or tag.startswith("PE") or tag.startswith("PJ"):
            result = "pro:rel"
        elif tag.startswith("PS"):
            result = "pro:poss"
        elif tag.startswith("P8"): # svůj
            result = "pro:poss"
        elif tag.startswith("P4") or tag.startswith("PK") or tag.startswith("PQ"):
            result = "pro:rel/int"
        elif tag.startswith("PW"):
            result = "pro:neg"
        elif tag.startswith("PL") or tag.startswith("PZ"):
            result = "pro:indef"
        elif tag.startswith("P6") or tag.startswith("P7"): # zvratná se, si...
            result = "pro:refl"
        if lemma == "svůj":
            result = "pro:refl:poss"
        if lemma == "čí":
            result = "pro:int:poss"

    elif tag.startswith("C"):
        result = "num"
        if tag.startswith("Cl") or tag.startswith("Cn"):
            result = "num:card"
        elif tag.startswith("Cr"):
            result = "num:ord"
        elif tag.startswith("Cv"):
            result = "num:mult"
        elif tag.startswith("Ca"):
            result = "num:indef"
        if word.endswith("krát") and lemma.endswith("krát"):
            result = "num:mult"
        
    elif tag.startswith("V"):
        result = "v"
        if lemma in constants.MODAL_VERBS: # modal verbs
            result = "v:mod"
        if lemma == constants.AUX:
            result = "v:aux/cop"

    elif tag.startswith("D"):
        result = "adv"
        if lemma in constants.PRONOMINAL_ADVERBS:
            result = "adv:pro"
        if lemma in constants.NEGATIVE_PRONOMINAL_ADVERBS: # zájmenná záporná příslovce
            result = "adv:pro:neg"
    
    elif tag.startswith("R"):
        result = "prep"
    elif tag.startswith("J^"):
        result = "conj:coord"
    elif tag.startswith("J,"):
        result = "conj:sub"
    elif tag.startswith("J*"):
        result = "conj:coord"
    elif tag.startswith("T"):
        result = "part"
    elif tag.startswith("I"):
        result = "int"
    
    if lemma == "každý":
        result = "pro:indef"
        
    return result


""" 
input: (tag, word, lemma) provided in the Token object by tokenize()
extracts the morphological information from the tag and returns the morphological tag in the MOR format
lemma & word in the input as well, because of the tagging of negation and verbal aspect

example of use: transform_tag("NNFS4-----A----", "Mařenku", "Mařenka")
→ output: '4&SG&F'

"""

def transform_tag(tag, word, lemma):
    mark = "&"
    result = ""
    
    if tag.startswith("V") and tag[10] == "N": # negation
        result += "neg-"
    elif (word.startswith("ne") == True) and (lemma.startswith("ne") == False):
        result += "neg-"
            
    if tag.startswith("V"):
        vid = "x_vid"
        if lemma in constants.IMPERFECTIVE_VERBS:
            vid = "impf" 
        if lemma in constants.PERFECTIVE_VERBS:
            vid = "pf"

        if tag[3] == "S":
            cislo = "SG"
        elif tag[3] == "P":
            cislo = "PL"
        else: # the value "–": infinitive, auxiliary "být" in the conditional form
            cislo = "x_cislo"

        if tag.startswith("Vs"):
            rod = "pas"
        elif tag[11] == "A":
            rod = "akt"
        else:
            rod = "x_slovesny_rod"

        if tag[2] != "-":
            if tag[2] == "Y" or tag[2] == "M":
                jmrod = "M"
            elif tag[2] == "N":
                jmrod = "N"
            else:
                jmrod = "F"
        else:
            jmrod = "x_jmenny_rod"

        if tag.startswith("Vf"): # infinitive
            result += "inf" + mark + vid
        elif tag.startswith("Vp"): # past participle
            if word.endswith("la") and jmrod == "F": # feminine participles in -la obligatorily singular
                cislo = "SG"
            result += cislo + mark + "past" + mark + rod + mark + jmrod + mark + vid
        elif tag.startswith("Vs"): # passive participle
            result += cislo + mark + "pas" + mark + jmrod + mark + vid
        
        else: # if it is neither an infinitive nor a participle
            if tag[7] == "1" or tag[7] == "2" or tag[7] == "3":
                result += tag[7]
            else: # person not specified: infinitive, transgressive
                result += "x_osoba"
            result += mark + cislo
            if tag.startswith("Vc"):
                result += mark + "cond"
                rod = "akt"
            elif tag.startswith("Vi"):
                result += mark + "imp"
                rod = "akt"
            else:
                result += mark + "ind"
                if tag[8] == "P":
                    result += mark + "pres"
                elif tag[8] == "F":
                    result += mark + "futur" 
            result += mark + rod
            result += mark + vid

    elif tag.startswith("N") or tag.startswith("A") or tag.startswith("P") or tag.startswith("C"):
        if tag[3] == "P":
            number = "PL"
        elif tag[3] == "S":
            number = "SG"
        elif tag[3] == "D":
            number = "PL"
        else:
            number = "x_cislo"
        if lemma in ["kdo", "co", "se"]:
            number = "SG"
            
        if tag[4] != "X":
            pad = tag[4]
        else:
            pad = "x_pad"
        result += pad + mark + number
        
        if tag.startswith("NNM"):
            result += mark + "MA"
        elif tag.startswith("NNI"):
            result += mark + "MI"
        elif lemma == "co":
            result += mark + "N"
        else:        
            if tag[2] == "I" or tag[2] == "Y":
                result += mark + "M"
            elif tag[2] == "X":
                result += mark + "x_jmenny_rod"
            else:
                if tag[2] != "-":
                    result += mark + tag[2]
    
        if tag.startswith("Cv"):
            result = ""
        if word.endswith("krát") and lemma.endswith("krát"):
            result = ""
    
    else: 
        if result == "neg-":
            result = "neg"
        else:
            result = ""

    if tag.startswith("A"):
        if tag[9] == "2":
            result = "CP-" + result
        if tag[9] == "3":
            result = "SP-" + result
    
    if tag.startswith("D"):
        if tag[9] == "2":
            result = "CP"
        if tag[9] == "3":
            result = "SP"
            
    if tag.startswith("Cv"):
        result = ""
    
    return result


"""
this function processes an input text
the input text is supposed to be the result of the function transform()
the function uses the functions pos() and transform_tag()
this function assures that tokens with the placeholders starting with the string "bacashooga" are treated as required

"""

def zpracovat(text, tagger):
    if (constants.PLACEHOLDER_NEOLOGISM in text) or (constants.PLACEHOLDER_CIZ in text):
        caution = True
        chi = []
        ciz = []
        seznam_slov = []
        for word in text.split(" "):
            if word.endswith(constants.PLACEHOLDER_NEOLOGISM):
                chi.append(True)
                ciz.append(False)
                seznam_slov.append(word.replace(constants.PLACEHOLDER_NEOLOGISM, ""))
            elif word.endswith(constants.PLACEHOLDER_CIZ):
                ciz.append(True)
                chi.append(False)
                seznam_slov.append(word.replace(constants.PLACEHOLDER_CIZ, ""))
            else:
                chi.append(False)
                ciz.append(False)
                seznam_slov.append(word)
        text = text.replace(constants.PLACEHOLDER_NEOLOGISM, "").replace(constants.PLACEHOLDER_CIZ, "")
    else:
        caution = False

    result = tokenize(text, tagger)
    word_list = []
    pos_list = []
    tag_list = []
    lemma_list = []
    for item in result:
        word_list.append(item[0])
        lemma_list.append(item[1])
        tag_list.append(item[2])
        pos_list.append(pos(item[2], item[0], item[1]))
    i = 0
    result = []
    while i < len(word_list):
        if pos_list[i] != "Z":
            new_tag = transform_tag(tag_list[i], word_list[i], lemma_list[i])
            if new_tag == "":
                mark2 = ""
            else:
                mark2 = "-"
            
            if caution == True: 
                if word_list[i] in seznam_slov:
                    index = seznam_slov.index(word_list[i])
                    if chi[index] == True:
                        new_tag += "-neo"
                    if ciz[index] == True:
                        new_tag += "-ciz"
            
            # lexically specified "exceptions": "mami" always to be tagged as "n|máma-5&SG&F" etc.
            if word_list[i] == "mami":
                result.append("n|máma-5&SG&F")
            elif word_list[i] == "no":
                result.append("part|no")
            elif word_list[i] == "koukej":
                result.append("v|koukat-2&SG&imp&akt&impf")
            elif word_list[i] == "zzz":
                result.append("x|zzz")
            
            # forms of "rád" to be tagged as follows
            elif word_list[i] == "rád":
                result.append("adj:short|rád-1&SG&M")
            elif word_list[i] == "ráda":
                result.append("adj:short|rád-1&SG&F")
            elif word_list[i] == "rádo":
                result.append("adj:short|rád-1&SG&N")
            elif word_list[i] == "rádi":
                result.append("adj:short|rád-1&PL&M")
            elif word_list[i] == "rády":
                result.append("adj:short|rád-1&PL&F")

            # reflexive pronouns "se" and "si" to be tagged as follows
            elif word_list[i] == "se":
                result.append("pro:refl|se-4&SG")
            elif word_list[i] == "si":
                result.append("pro:refl|se-3&SG")
                
            # the uninflected "jejichž" to be tagged as follows
            elif word_list[i] == "jejichž":
                result.append("pro:rel:poss|jejichž-x_pad&x_cislo&x_jmenny_rod")
                
            # double lemmatization for forms of "aby.*" and "kdyby.*" + "ses", "sis", and "zač"
            elif word_list[i] == "abych":
                result.append("conj:sub_v:aux|aby_být-1&SG&cond&akt&impf")
            elif word_list[i] == "abys":
                result.append("conj:sub_v:aux|aby_být-2&SG&cond&akt&impf")
            elif word_list[i] == "aby":
                result.append("conj:sub_v:aux|aby_být-1&x_cislo&cond&akt&impf")
            elif word_list[i] == "abychom":
                result.append("conj:sub_v:aux|aby_být-1&PL&cond&akt&impf")
            elif word_list[i] == "abyste":
                result.append("conj:sub_v:aux|aby_být-2&PL&cond&akt&impf")
            elif word_list[i] == "abysme":
                result.append("conj:sub_v:aux|aby_být-1&PL&cond&akt&impf")
            elif word_list[i] == "kdybych":
                result.append("conj:sub_v:aux|aby_být-1&SG&cond&akt&impf")
            elif word_list[i] == "kdybys":
                result.append("conj:sub_v:aux|aby_být-2&SG&cond&akt&impf")
            elif word_list[i] == "kdyby":
                result.append("conj:sub_v:aux|aby_být-1&x_cislo&cond&akt&impf")
            elif word_list[i] == "kdybychom":
                result.append("conj:sub_v:aux|aby_být-1&PL&cond&akt&impf")
            elif word_list[i] == "kdybysme":
                result.append("conj:sub_v:aux|aby_být-1&PL&cond&akt&impf")
            elif word_list[i] == "kdybyste":
                result.append("conj:sub_v:aux|aby_být-2&PL&cond&akt&impf")
            elif word_list[i] == "ses":
                result.append("pro:refl_v:aux|se_být-4&SG_2&SG&ind&pres&akt&impf")
            elif word_list[i] == "sis":
                result.append("pro:refl_v:aux|se_být-3&SG_2&SG&ind&pres&akt&impf")
            elif word_list[i] == "zač":
                result.append("prep_pro:int|za_co-4&SG&N")
            
            elif word_list[i].endswith(constants.PLACEHOLDER_INTERJECTION):
                new_word = word_list[i].replace(constants.PLACEHOLDER_INTERJECTION, "")
                result.append("int|" + new_word)

            else: 
                # lemmatizace my/náš/... ne jako já/můj/...
                list_my = constants.PERS_PRONOUN_1PL
                list_náš = constants.POSS_PRONOUN_1PL
                list_vy = constants.PERS_PRONOUN_2PL
                list_váš = constants.POSS_PRONOUN_2PL
                list_její = constants.POSS_PRONOUN_F_3SG
                list_sum = list_my + list_náš + list_vy + list_váš + list_její + [constants.POSS_PRONOUN_M_N_3SG, constants.POSS_PRONOUN_3PL]
                if word_list[i] not in list_sum:
                    result.append(pos_list[i] + "|" + lemma_list[i] + mark2 + new_tag)
                else:
                # plural central pronouns to be lemmatized as e.g. "my" or "náš" rather than forms of "já" or "můj"
                    if word_list[i] in list_my:
                        new_lemma = "my"
                    if word_list[i] in list_náš:
                        new_lemma = "náš"
                    if word_list[i] in list_vy:
                        new_lemma = "vy"
                    if word_list[i] in list_váš:
                        new_lemma = "váš"
                    if word_list[i] in list_její:
                        new_lemma = "její"
                    if word_list[i] == constants.POSS_PRONOUN_M_N_3SG:
                        new_lemma = "jeho"
                    if word_list[i] == constants.POSS_PRONOUN_3PL:
                        new_lemma = "jejich"
                    result.append(pos_list[i] + "|" + new_lemma + mark2 + new_tag)
        if pos_list[i] == "Z":
            result.append(lemma_list[i])
        i += 1 
    text = "%mor:\t" + " ".join(result) + "\n"
    
    # small formal adjustments
    text = text.replace(", .", ".")
    text = text.replace("\t, ", "\t")
    text = text.replace("+ . . .", "+…").replace("+ …", "+…").replace("+ / .", "+/.")
    
    return text


"""
a function for small formal adjustments WITHIN THE MAIN LINE, i.e., this is not a necessary part of the morphological analysis
→ adds a space before ".", "!" and "?" on the main line
→ changes +... to +…

"""

def mezera_interpunkce(line):
    if line.endswith("+..."):
        line = line[:-4] + "+…"
    elif line.endswith("+…"):
        pass
    elif line.endswith("+/."):
        pass
    elif line.endswith(".") and line.endswith(" .") == False:
        line = line[:-1] + " ."
    elif line.endswith("?") and line.endswith(" ?") == False:
        line = line[:-1] + " ?"
    elif line.endswith("!") and line.endswith(" !") == False:
        line = line[:-1] + " !"
    return line


""" 
this function takes a file ("path" in the input) and creates a new file ("path_goal"),
which includes the added morphological tiers

example of use: file_to_file("./test_files/aneta.txt", "./test_files/aneta_result.txt")

"""

def annotate_file(path, path_goal, tagger):
    with open(path, "r") as file:
        with open(path_goal, "a") as file_goal:
            annotate_filestream(file, file_goal, tagger)

def annotate_filestream(source_fs, target_fs, tagger:Tagger):
    for line in source_fs:
        target_fs.write(mezera_interpunkce(line))
        if line!= "":
            if transform(line) != "NA":
                if transform(line) == "." or transform(line) == "0 ." or transform(line) == "nee ." or transform(line) == "emem ." or transform(line) == "mhm ." or transform(line) == "hm .":
                    target_fs.write("\n")
                else:
                    target_fs.write("\n")
                    target_fs.write(zpracovat(transform(line), tagger))
            elif transform(line) == "NA":
                target_fs.write("\n")

_tagger = None                    
def _get_tagger():
    global _tagger
    if _tagger is None:
        _tagger = Tagger(constants.TAGGER_PATH)
    return _tagger
                        
"""
to process all corpus files within a folder with the function file_to_file(), the following code was used
(the folder here was named "Sara" and included all corpus files for the child nicknamed "Sara")
(all the new files will be found in a new folder, titled "Sara_tagged")

"""


def main():
    # TODO: review
    parser = argparse.ArgumentParser(
        description='Add morphological annotation according to the CoCzeFLA standards to a text file. REVIEW'
    )
    parser.add_argument('-s', '--std', action='store_true', help='receive/print input/output on stdin/stdout')
    parser.add_argument('-o', '--outdir', nargs=1, type=str, help='directory where output files should be stored')
    parser.add_argument('inputfiles', nargs='*', default=[])

    args = parser.parse_args(sys.argv[1:])

    if args.std:
        annotate_filestream(sys.stdin, sys.stdout, _get_tagger())
    elif args.outdir:
        if len(args.inputfiles) == 0:
            print('Please specify your input files. See --help for more.', file=sys.stderr)
            return
        
        if not os.path.isdir(args.outdir[0]):
            os.makedirs(args.outdir[0])
        
        for file in args.inputfiles:
            print(file)
            target_path = os.path.join(args.outdir[0], os.path.basename(file))
            annotate_file(file, target_path, _get_tagger())
    else:
        print('An output directory needs to be specified. See --help for more.', file=sys.stderr)
        
if __name__ == '__main__':
    main()