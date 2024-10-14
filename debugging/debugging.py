import annot_util.replacement_rules as rules

import re


def chat_to_plain_text_replacement_rules(line: str):
    for rule in rules.CHAT_TO_PLAIN_TEXT:
        line = re.sub(rule[0], rule[1], line)
        print(rule)
        print(line)
        input()
