"""module for parser generator
The Grammar of Command Grammars:
(whitespace is ignored)
grammar = expression+
expression = '(' atom  ('|' atom )* ')' quantifer?
atom = identifier | keyword
quantifier = '?' | '*' | '+'
identifier = [A-Z]+
keyword = [A-Z]+


Technically speaking, parsing player input is *NOT* context free.
For instance, take the English sentence
"The old man the boat."
Often times, people read this as (The old man) [subject] (the boat) [object?].
This doesn't make sense, so people re-read it (searching for a verb).
(The old) [subject, using old as a substantive adjective] (man) [verb] (the boat) [object].

Let's use a more MUD-related example.
Say that you have an item ("treasure") protected by enemies (multiple "treasure guardian").
What does the following sentence evaluate to?
take treasure guardian
Does this mean take treasure (from) treasure guardian?
Or is the user just trying to take the treasure guardian (invalid).

This means that many of the typical parser-generator strategies don't
work here.

In the grammar of these paraser-generators, we note the following:
"objects" are phrases that should match in-game objects. They are indicated
in parentheses, with the type indicated all caps.
pickup (ITEM)
If more than one type is accepted, you can specify like so:
attack (ITEM | ENTITY)
You can provide multiple types (if desired):
attack (ITEM)

"keywords" are constant literal phrases. Most often, they are prepositions,
like the 'to' in the example below:
    give (ITEM) to (CHARACTER | ENTITY)

Parsing a list of tokens:
    work through the
"""
import re
from abc import ABC, abstractmethod

def split_args(string):
    """Split [string] on whitespace, respecting quotes.
    (Quotes are pruned in the process.)
    Examples:
        split_quotes('equip "epic sword"') -> ['equip', 'epic sword']
        split_quotes('say "oh no...    don\'t go!')) ->
            ['say', "oh no...    don't go!"]
    """
    in_quote = False # we will set this to ' or " as needed
    in_token = False # we are in the middle of a token (not whitespace)
    tokens = []
    # Note that reallocating strings is inefficient, so we store the
    # strings as lists and join them at the end.
    for char in string:
        if in_quote:
            if char == in_quote:
                # we are closing the quoted token
                in_quote = False
            else:
                # we are still inside a quoted token
                tokens[-1].append(char)
        elif char in "\"'":
            if in_token:
                # we're in a token (but not in a quoted token),
                # so go ahead and add this char
                tokens[-1].append(char)
            else:
                # we're making a new quoted token
                in_quote = char
                tokens.append([])
        # skip whitespace
        elif char in " \t\n\r":
            in_token = False
            continue
        else:
            # we're in a token
            if in_token:
                tokens[-1].append(char)
            # we just entered a new token
            else:
                tokens.append([char])
                in_token = True
    # TODO: should we catch if in_quote is still open?
    return ["".join(token) for token in tokens]


def string_index(tok_index, tokens):
    # compute the cumulative length of the list of tokens up to token [index]
    cumsum = []
    prev = 0
    for s in tokens[:tok_index]:
        length = len(s) if s else 0
        cumsum.append(length + prev)
        prev = length
    if cumsum:
        return cumsum[-1]
    # edge case: provided index is 0
    else:
        return 0


_grammar_token_re = re.compile(r"([()|*?+])|[ \t\r\n]")
def with_grammar(grammar: str):
    """Returns a parser based on the provided grammar."""
    # actually, it just returns a DFA
    # parse grammar into tokens
    tokens = _grammar_token_re.split(grammar)

    # stack of grammar components
    stack = [Group()]

    for tok_index, token in enumerate(tokens):
        if not token:
            # token is empty string or None (whitespace)
            continue
        if token.islower():
            # it's a keyword
            stack[-1].add(Keyword(token))
        elif token.isupper():
            # do some kind of type checking here
            stack[-1].add(Variable(token))
        elif token == "(":
            # start new capturing group
            stack.append(Group())
        elif token == ")":
            # end previous capturing group / union
            finished_group = stack.pop()
            finished_group.cleanup()
            if stack:
                stack[-1].add(finished_group)
            else:
                index = string_index(tok_index, tokens)
                raise ValueError(f"Unmatched ')' at index [{index}]")
        elif token == "|":
            stack[-1].add_alternative()
        # quantifiers
        elif token == "*":
            stack[-1].quantify_last(Star)
        elif token == "+":
            stack[-1].quantify_last(Plus)
        elif token == "?":
            stack[-1].quantify_last(Optional)
        else:
            index = string_index(tok_index, tokens)
            raise ValueError(f"Unrecognized token {token!r} starting at index [{index}]")
    # do we have any unfinished capturing groups on the stack?
    if len(stack) > 1:
        count = len(stack) - 1
        index = string_index(0, tokens)
        raise ValueError(f"Expected {count} ')', but input ended at [{index}]")
    stack[0].cleanup()
    return stack[0]

class Matcher(ABC):
    """A grammar is implicitly concatentation"""
    def __repr__(self):
        return f"{type(self).__name__}({self.args!r})"

    @abstractmethod
    def to_nfa(self):
        pass

    def match(self, inp):
        NFAState.next_id = 0
        return self.to_nfa().match(split_args(inp))

    def __eq__(self, other):
        return isinstance(other, type(self)) and other.args == self.args

class Group(Matcher):
    """Implictly, a group functions as a stack within our stack"""
    def __init__(self, *args, alts=None):
        alts = [] if alts is None else alts
        self.alts = list(alts)
        self.args = list(args)

    def add(self, arg):
        self.args.append(arg)
        return self

    def quantify_last(self, Quantifier):
        if self.args:
            if not isinstance(self.args[-1], (Star, Plus, Optional)):
                self.args[-1] = Quantifier(self.args[-1])
            else:
                raise ValueError("Predicate already has quantifier")
        else:
            raise ValueError("Expected predicate before quantifier")

    def add_alternative(self):
        if not self.args:
            # if we haven't added anything, raise an error
            raise ValueError("empty alternative")
        self.alts.append(self.args)
        self.args = []

    def __repr__(self):
        if self.alts:
            if self.args:
                return f"Group({repr(self.args)[1:-1]}, alts={self.alts})"
            else:
                return f"Group(alts={self.alts})"
        else:
            return f"Group({repr(self.args)[1:-1]})"

    def __eq__(self, other):
        return isinstance(other, Group) and other.args == self.args and other.alts == self.alts

    def cleanup(self):
        """This operation detects
        1) any empty alternates
        2) empty group
        It also closed out the most recent alternative and adds it to
        the stack
        """
        if not self.args:
            if self.alts:
                # the most recent alternate is empty
                raise ValueError("empty alternate")
            else:
                # the entire group is empty
                raise ValueError("empty group")
        else:
            if self.alts:
                self.alts.append(self.args)
                self.args = []

    def to_nfa(self):
        if self.args:
            return NFA.concat(*map(lambda e: e.to_nfa(), self.args))
        else:
            return NFA.union(*map(
                lambda alt: NFA.concat(*map(lambda e: e.to_nfa(), alt)),
                self.alts
            ))

# two types of basic grammar expressions
class Keyword(Matcher):
    def __init__(self, kw):
        self.args = kw

    def to_nfa(self):
        return NFA.match_on(self.args)

class Variable(Matcher):
    #TODO: possible optimization, join types in an alternate
    # together into one variable
    # UPDATE: yes, this helps reduce the number of exponential options
    def __init__(self, *types):
        self.args = types

    def to_nfa(self):
        # this nfa matches one word exactly
        # however, variables can match an unlimited number of words
        return NFA.plus(NFA.match_on(Token.ANY))

# three quantifiers
class Star(Matcher):
    def __init__(self, expr):
        self.args = expr

    def to_nfa(self):
        return NFA.star(self.args.to_nfa())

class Plus(Matcher):
    def __init__(self, expr):
        self.args = expr

    def to_nfa(self):
        # The 'plus' of an NFA is just that NFA concatenated to the
        # star / Kleene Star of itself
        return NFA.plus(self.args.to_nfa())

class Optional(Matcher):
    def __init__(self, expr):
        self.args = expr

    def to_nfa(self):
        return NFA.optional(self.args.to_nfa())

from enum import Enum
# Creating a few enums for simplicity
class Token(Enum):
    ANY = 0
    END = 0


class NFAState:
    """state of a non-deterministic finite state automaton"""
    next_id = 0
    states = []

    def __init__(self, accepting=False, epsilons=None, match_words=None):
        if epsilons and match_words:
            raise ValueError("State must have either epsilon transitions or match words, not both.")
        self.epsilons = epsilons if epsilons else []
        self.match_words = match_words if match_words else {}
        self.accepting = accepting
        self.id = NFAState.next_id
        NFAState.states.append(self)
        NFAState.next_id += 1

    def add_epsilon(self, to):
        if self.match_words:
            raise ValueError("Cannot add epsilon to state with words")
        self.epsilons.append(to)

    def add_word(self, word, to):
        if self.epsilons:
            raise ValueError("Cannot add word to state with epsilons")
        self.match_words[word] = to

    def __repr__(self):
        return f"NFAState[{self.id}]"

    def __getitem__(self, index):
        return self.states[index]

    def view(self):
        return (f"NFAState[{self.id}]("
                f"\n  accepting={self.accepting},"
                f"\n  epsilons={self.epsilons},"
                f"\n  match_words={self.match_words}"
                "\n)")

    def traverse(self, traversed=None, depth=0):
        if traversed is None:
            traversed = set()
        yield (self, depth)
        traversed.add(self)
        for state in self.epsilons:
            if state in traversed:
                continue
            traversed.add(state)
            yield from state.traverse(traversed, depth+1)
        for state in self.match_words.values():
            if state in traversed:
                continue
            traversed.add(state)
            yield from state.traverse(traversed, depth+1)

    def transitions(self, token):
        if self.epsilons:
            for state in self.epsilons:
                yield from state.transitions(token)
        elif self.match_words:
            if token is Token.END:
                # whoops, end of the line
                return
            if Token.ANY in self.match_words:
                yield self.match_words[Token.ANY]
            if token in self.match_words:
                yield self.match_words[token]
        # edge case:
        else:
            if token is Token.END and self.accepting:
                yield self
class NFA:
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __repr__(self):
        from textwrap import indent
        return "\n".join(map(
                lambda x: indent(NFAState.view(x[0]), " " * (4 * x[1])),
                self.start.traverse()
            ))

    def _concat_with(self, nxt):
        """joins NFA nxt to this NFA"""
        self.end.accepting = False
        self.end.add_epsilon(nxt.start)
        self.end = nxt.end
        return self

    @staticmethod
    def match_on(value):
        """Returns a simple NFA that matches on [value]"""
        start = NFAState()
        end = NFAState(accepting=True)
        start.add_word(value, end)
        return NFA(start, end)

    @staticmethod
    def star(nfa):
        """Returns a NFA matching the Kleene Star of NFA"""
        new_start = NFAState()
        new_end = NFAState(accepting=True)

        # new start can either go to start of nfa or bypass it
        new_start.add_epsilon(nfa.start)
        new_start.add_epsilon(new_end)

        nfa.end.accepting = False
        nfa.end.add_epsilon(new_end)

        # nfa can loop back to the beginning
        nfa.end.add_epsilon(nfa.start)

        nfa.start = new_start
        nfa.end = new_end
        return nfa

    @staticmethod
    def plus(nfa):
        """Returns a NFA matching the Kleene Plus of NFA"""
        # this could easily be implemented with NFA.star
        # word+ is equivalent to word word*
        # NFA.concat(nfa, NFA.closure(nfa))
        # however, we can save one epsilon state with this implementation
        new_end = NFAState(accepting=True)

        nfa.end.accepting = False
        nfa.end.add_epsilon(new_end)

        # nfa can loop back to the beginning
        nfa.end.add_epsilon(nfa.start)

        nfa.end = new_end
        return nfa

    @staticmethod
    def optional(nfa):
        new_start = NFAState()
        new_start.add_epsilon(nfa.start)
        new_start.add_epsilon(nfa.end)
        new_end = NFAState(accepting=True)
        nfa.end.accepting = False
        nfa.end.add_epsilon(new_end)
        nfa.start = new_start
        nfa.end = new_end
        return nfa

    @staticmethod
    def union(*nfas):
        new_start = NFAState()
        new_end = NFAState(accepting=True)
        for nfa in nfas:
            new_start.add_epsilon(nfa.start)
            nfa.end.accepting = False
            nfa.end.add_epsilon(new_end)
        return NFA(new_start, new_end)

    @staticmethod
    def concat(*nfas):
        """concatentate several NFAs together
        note, passing in zero NFAs will produce a single state
        that is already accepting
        """
        # this looks ugly, but it helps optimize the number of states
        if not nfas:
            accepting = NFAState(accepting=True)
            return NFA(accepting, accepting)
        if len(nfas) == 1:
            return nfas[0]
        # we simply concatenate the NFAs in reverse
        nfa = nfas[-1]
        for next_nfa in reversed(nfas[:-1]):
            nfa = next_nfa._concat_with(nfa)
        return nfa

    def match(self, tokens):
        """Search for all possible paths through [self]"""
        states = [self.start]
        #print(self)
        for index, token in enumerate(tokens):
            next_states = []
            #print(states)
            #print(token)
            for state in states:
                for next_state in state.transitions(token):
                    next_states.append(next_state)
            states = next_states
        # give states one last chance to catch up (in case they have)
        # any empty epsilons leftover
        #print(states)
        next_states = []
        #print("END")
        for state in states:
            for next_state in state.transitions(Token.END):
                next_states.append(next_state)
        states = next_states

        #print(states)
        for state in states:
            if state.accepting:
                return True
        return False


"""
Prologue:
Worst thing that can happen is "token contention". In other words,
two variables fighting over a phrase. Say that our grammar is
"attack (ENTITY) (ITEM)"
and we get the input:
"attack evil zombie sword"


Workflow:
Parser:
Run the tokens through the matcher / finite-state automaton. (Each
grammar resolves to exactly one FSA).
This produces one or more valid paths.
A path is valid if the automaton ends in the FINAL state.
If this occurs, then all of the tokens should be associated with one
or more tokens.

Each path is then run through the "contextualizer".
The contextualizer makes heavy use of util.find to match objects to the
phrases.
If
"""