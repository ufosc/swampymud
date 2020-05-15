# Pertaining to the indefinite_article() function:
# Copyright (c) 2009-2010, Michael Gorven, Stefano Rivera
# Released under terms of the MIT/X/Expat Licence. See COPYING for details.
#
# The indefinite_article function follows an algorithm by Damian Conway
# as published in CPAN package Lingua-EN-Inflect-1.891 under the GNU GPL
# (version 1 or later) and Artistic License 1.0.
import re

def indefinite_article(noun_phrase):
    # algorithm adapted from CPAN package Lingua-EN-Inflect-1.891 by Damian Conway
    m = re.search('\w+', noun_phrase, re.UNICODE)
    if m:
        word = m.group(0)
    else:
        return 'an'

    wordi = word.lower()
    for anword in ('euler', 'heir', 'honest', 'hono'):
        if wordi.startswith(anword):
            return 'an'

    if wordi.startswith('hour') and not wordi.startswith('houri'):
        return 'an'

    if len(word) == 1:
        if wordi in 'aedhilmnorsx':
            return 'an'
        else:
            return 'a'

    if re.match(r'(?!FJO|[HLMNS]Y.|RY[EO]|SQU|'
                  r'(F[LR]?|[HL]|MN?|N|RH?|S[CHKLMNPTVW]?|X(YL)?)[AEIOU])'
                  r'[FHLMNRSX][A-Z]', word):
        return 'an'

    for regex in (r'^e[uw]', r'^onc?e\b',
                    r'^uni([^nmd]|mo)','^u[bcfhjkqrst][aeiou]'):
        if re.match(regex, wordi):
            return 'a'

    # original regex was /^U[NK][AIEO]?/ but that matches UK, UN, etc.
    if re.match('^U[NK][AIEO]', word):
        return 'a'
    elif word == word.upper():
        if wordi[0] in 'aedhilmnorsx':
            return 'an'
        else:
            return 'a'

    if wordi[0] in 'aeiou':
        return 'an'

    if re.match(r'^y(b[lor]|cl[ea]|fere|gg|p[ios]|rou|tt)', wordi):
        return 'an'
    else:
        return 'a'

def english_list_no_article(phrase_list, oxford_comma=True):
    ''' Formats a list of strings correctly into an english
    gramatically correct list of phrases, with commas if the list
    has 3 or more elements. Uses the oxford comma by default.
    0 elements:
        phrase_list = []
        returns "" (empty string)
    1 element:
        phrase_list = ["dog"]
        returns "dog"
        This does than extract the string from the list, but is included for completion
    2 elements:
        phrase_list = ["dog", "cat"]
        returns "dog and cat"
    3 elements:
        if oxford_comma:
            phrase_list = ["dog", "cat", "fish"]
            returns "dog, cat, and fish"
        if not oxford_comma:
            phrase_list = ["dog", "cat", "fish"]
            returns "dog, cat and fish"
    '''
    if not phrase_list:
        return ""
    for phrase in phrase_list:
        if type(phrase) is not str:
            raise TypeError("All elements in phrase_list must be of type str")
    if len(phrase_list) == 1:
        return phrase_list[0]
    elif len(phrase_list) == 2:
        return " and ".join(phrase_list)
    else:
        output = []
        if oxford_comma:
            output.append(", ".join(phrase_list[:-1]))
            output.append(", and " + phrase_list[-1])
            return "".join(output)
        else:
            output.append(", ".join(phrase_list[:-2]))
            output.append(", " + " and ".join(phrase_list[-2:]))
            return "".join(output)


def english_list_indefinite_article(phrase_list, oxford_comma=True):
    ''' Formats a list of strings correctly into an english
    gramatically correct list of phrases preceded by an indefinite
    article, with commas if the list has 3 or more elements. 
    Uses the oxford comma by default.
    0 elements:
        phrase_list = []
        returns "" (empty string)
    1 element:
        phrase_list = ["dog"]
        returns "a dog"
        This does than extract the string from the list, but is included for completion
    2 elements:
        phrase_list = ["dog", "cat"]
        returns "a dog and a cat"
    3 elements:
        if oxford_comma:
            phrase_list = ["dog", "cat", "octopus"]
            returns "a dog, a cat, and an octopus"
        if not oxford_comma:
            phrase_list = ["dog", "cat", "octopus"]
            returns "a dog, a cat and an octopus"
    '''
    if not phrase_list:
        return ""
    for phrase in phrase_list:
        if type(phrase) is not str:
            raise TypeError("All elements in phrase_list must be of type str")
    if len(phrase_list) == 1:
        return indefinite_article(phrase_list[0]) + " " + phrase_list[0]
    elif len(phrase_list) == 2:
        return indefinite_article(phrase_list[0]) + " " + phrase_list[0] \
                + " and " + indefinite_article(phrase_list[1]) + " " + phrase_list[1]
    else:
        output = []
        if oxford_comma:
            for phrase in phrase_list[:-1]:
                output.append(indefinite_article(phrase) + " " + phrase + ",")
            output.append("and " + indefinite_article(phrase_list[-1]) + " " +phrase_list[-1])
            return " ".join(output)
        else:
            for phrase in phrase_list[:-2]:
                output.append(indefinite_article(phrase) + " " + phrase + ",")
            output.append(indefinite_article(phrase_list[-2]) + " " + phrase_list[-2] + " and " + \
                        indefinite_article(phrase_list[-1]) + " " + phrase_list[-1])
            return " ".join(output)
