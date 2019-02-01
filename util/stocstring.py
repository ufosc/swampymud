'''Module for dealing with stochastic strings'''
import re
from random import uniform, triangular, betavariate, expovariate, gammavariate, gauss, lognormvariate, normalvariate, vonmisesvariate, paretovariate, weibullvariate, randrange, choice
from util.distr import RandDist, ChoiceDist, weightedchoice


class StringMacro:
    '''Class that holds macros for StocStrings'''
    def __init__(self, input_string):
        # strip any lingering macro formatting
        self.original = input_string.lstrip("!{").rstrip("}")

    def execute(self):
        '''evaluate the macro and return the result'''
        # TODO: pass locals / globals dictionary to make this more safe
        return eval(self.original)

    def __str__(self):
        return str(self.execute())

    def __repr__(self):
        return "StringMacro(%s)" % self.original

# TODO: add names to the results of macros to allow them to be named later
class StocString:
    '''Class representing and processsing stochastic strings'''
    # regex that captures the macros
    # this regex cannot work, we need a LR parser to check open / closed parentheses
    token_regex = re.compile(r"((!{)(([^!{]*[?{]?)*)(}))")

    def __init__(self, input_string):
        # keeping a copy of the master string
        self.original = input_string
        #TODO: add some regexs to check unmatched braces
        self.tokens = StocString.token_regex.split(input_string)

        # removing all the unnecessary separators left by the split
        # (the best way to illustrate the need for this loop
        #  is to uncomment the line below)
        # print(self.tokens)
        # also converting the macros as appropriate
        
        i = 0
        while (i < len(self.tokens)):
            token = self.tokens[i]
            if token == "!{":
                del self.tokens[i:i+4]
            elif token == "":
                del self.tokens[i]
            else:
                # if the token starts with !{ then it is macro
                # thus, we must convert it as appopriate
                if token.startswith("!{"):
                    self.tokens[i] = StringMacro(token)
                i += 1

    def __repr__(self):
        output = ""
        for token in self.tokens:
            output += repr(token)
        return output

    def __str__(self):
        output = ""
        for token in self.tokens:
            output += str(token)
        return output

    @staticmethod
    def process(input_string):
        '''Directly process a string in the StocString format
        returns a normal string
        '''
        return str(StocString(input_string))

'''
Examples:

my_stoc = StocString("Johnny ate !{randrange(1, 10)} apple(s), !{ weightedchoice({'what the heck':1, 'wow': 50}) }! what a !{choice(['fella', 'guy'])}")
total = 0
for i in range(10):
    print(my_stoc)

Result:
Johnny ate 5 apple(s), wow! what a fella
Johnny ate 2 apple(s), wow! what a guy
Johnny ate 5 apple(s), wow! what a guy
Johnny ate 4 apple(s), wow! what a fella
Johnny ate 3 apple(s), wow! what a fella
Johnny ate 7 apple(s), what the heck! what a fella
Johnny ate 8 apple(s), wow! what a guy
Johnny ate 1 apple(s), wow! what a fella
Johnny ate 5 apple(s), wow! what a fella
Johnny ate 7 apple(s), wow! what a guy
'''
