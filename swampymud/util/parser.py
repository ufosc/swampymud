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
(The old) [subject] (man) [verb] (the boat) [object].

Let's use a more MUD-related example.
Say that you have an item ("treasure") protected by enemies (multiple
"treasure guardians").
What does the following sentence evaluate to?
take treasure guardian
Does this mean take treasure (from) a treasure guardian?
Or is the user just trying to take the treasure guardian (invalid).

This means that many of the typical parser-generator strategies don't work
here.

In the grammar of these paraser-generators, we note the following:
"objects" are phrases that should match in-game objects. They are indicated
in parentheses, with the type indicated all caps.
pickup (ITEM)
If more than one type is accepted, you can specify like so:
attack (ITEM | ENTITY)

"keywords" are constant literal phrases. Most often, they are prepositions,
like the 'to' in the example below:
    give (ITEM) to (CHARACTER | ENTITY)
"""
import re
from abc import ABC, abstractmethod
from copy import deepcopy
from enum import Enum
from collections import namedtuple
from typing import Iterable, Mapping
from swampymud import _types
from swampymud._types import GameObject
from swampymud.util import color


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


class ParseError(Exception):
    """Exception class for all errors that arise when parsing user input
    from an existing grammar
    """
    def __init__(self, fails, **kwargs):
        self.fails = fails
        args = self.description()
        super().__init__(args, **kwargs)

    def description(self):
        """Return a human-readable description of this error"""
        # edge case (this shouldn't happen)
        if not self.fails:
            return "Unknown error (no fails provided)"
        # for now, simply take the last Fail and ignore rest of stack
        print(self.fails)
        expected, received = self.fails[-1][-1]

        # TODO: make this more human readable
        return f"Expected {expected!r}, received {received!r}"


class ContextError(ParseError):
    """Specific ParseError that occurs when input is syntactically
    correct, but references an object that cannot be found in the
    current context.
    """
    def __init__(self, fails, **kwargs):
        super().__init__(fails, **kwargs)

    def description(self):
        """Return a human-readable description of this error"""
        # for now, just grab the last error
        expected, received = self.fails[-1]

        # TODO: make this more human readable
        return f"Expected {expected!r}, received {received!r}"


class GrammarError(Exception):
    """Exception class for all errors that might arise when compiling a
    Grammar
    """
    # error types
    UNRECOGNIZED = 0  # foo Bar
    UNMATCH_OPEN = 1  # unmatched '(' / missing ')'
    UNMATCH_CLOSE = 2 # unmatched ')' / missing '('
    EXTRA_QUANT = 3   # foo+*
    NO_PREDICATE = 4  # foo | *
    EMPTY_ALT = 5     # | foo
    EMPTY_GRP = 6     # foo ()
    BAD_TYPE = 7 # foo BAR (if BAR is not a valid type)

    def __init__(self, etype, token_index, tokens, original,
                 parens=None, types = None,**kwargs):
        """Create a grammar error
        etype - type of error (see above)
        token_index - index of the token that triggered error
        tokens - list of tokens
        original - the original grammar string
        """
        self.etype = etype
        self.token_index = token_index
        self.tokens = tokens
        self.original = original
        self.parens = parens
        self.types = types
        # original
        # index of the original
        self.index = _string_index(token_index, tokens)
        args = self.description()
        super().__init__(args, **kwargs)

    def description(self):
        """Return a descriptive, human-readable description of this
        error
        """
        index = self.index
        token = self.tokens[self.token_index]
        if self.etype == GrammarError.UNRECOGNIZED:
            return f"Unrecognized token '{token}'"
        elif self.etype == GrammarError.UNMATCH_OPEN:
            return f"Unmatched '('"
        elif self.etype == GrammarError.UNMATCH_CLOSE:
            return f"Unmatched ')' at index {index}"
        elif self.etype == GrammarError.EXTRA_QUANT:
            return f"Unexpected quantifier '{token}' at {index}"
        elif self.etype == GrammarError.NO_PREDICATE:
            return f"Quantifier '{token}' has no preceding predicate"
        elif self.etype == GrammarError.EMPTY_ALT:
            return f"Expected an alternative before index {index}"
        elif self.etype == GrammarError.EMPTY_GRP:
            return f"Empty group at index {index}"
        elif self.etype == GrammarError.BAD_TYPE:
            return f"Unknown type '{token}' at index {index}"

    def hint(self):
        """Return a hint to help correct the error"""
        token = self.tokens[self.token_index]
        if self.etype == GrammarError.UNRECOGNIZED:
            if token in "{[":
                return "did you mean to use a '(' instead?"
            elif token in "]}":
                return "did you mean to use a ')' instead?"
            elif len(token) == 1:
                return "the only supported operations are |, *, +, and ?"
            elif token != token.lower() or token != token.upper():
                # token is a variable / keyword not following convention
                return "use lowercase for keywords and uppercase for variables"
        elif self.etype == GrammarError.UNMATCH_OPEN:
            if self.parens:
                return f"add {self.parens} ')' "
            else:
                return f"add some ')' "
        elif self.etype == GrammarError.UNMATCH_CLOSE:
            return "did you forget a '(' earlier in your grammar?"
        elif self.etype == GrammarError.EXTRA_QUANT:
            before = self.tokens[self.token_index - 1]
            return "you can only apply one quantifier (*, +, ?) to keyword/variable/group"
        elif self.etype == GrammarError.NO_PREDICATE:
            return "there should be a keyword/variable/group before this quantifier"
        elif self.etype == GrammarError.EMPTY_ALT:
            return ("alternatives cannot be empty. Grammars like (foo | ) "
                    "are invalid,\n       "
                    "there should be something before and after that '|'")
        elif self.etype == GrammarError.EMPTY_GRP:
            # edge case: grammar might be empty or just whitespace
            if not any(self.tokens):
                return "grammars must contain at least one keyword or variable"
            else:
                return "groups cannot be empty. '()' matches nothing"
        elif self.etype == GrammarError.BAD_TYPE:
            return (f"type must be one of {','.join(self.types)}")
            if self.types == Grammar.DEFAULT_TYPES:
                # TODO: pass in a hint about custom types
                pass
            else:
                # TODO: replace with nearest levenshtein distance
                pass

    def highlight(self):
        """Return the original grammar with the issue highlighted"""
        # in most cases, the token is the problem
        token = self.tokens[self.token_index]
        start = self.index
        end = self.index + len(token)

        if self.etype == GrammarError.UNMATCH_OPEN:
            # highlight all of the '(' and ')' instead
            chars = []
            for char in self.original:
                if char in "()":
                    chars.append(str(color.Red(color.Underline(char))))
                else:
                    chars.append(char)
            return "".join(chars)
        if self.etype in (self.NO_PREDICATE, self.EMPTY_ALT, self.EMPTY_GRP):
            # go from the previous non-empty token (if one exists)
            if self.token_index == 0:
                start = 0
            else:
                prev = self.token_index - 1
                while prev > 0 and not self.tokens[prev]:
                    prev -= 1
                start = _string_index(prev, self.tokens)
        return (self.original[:start] +
                color.Red(color.Underline(self.original[start:end])) +
                self.original[end:])


def _string_index(tok_index, tokens):
    """helper function for GrammarError"""
    # compute the cumulative length of the list of tokens up to token [index]
    cumsum = []
    prev = 0
    for s in tokens[:tok_index]:
        length = 1 if s is None else len(s)
        cumsum.append(length + prev)
        prev += length
    if cumsum:
        return cumsum[-1]
    # edge case: provided index is 0
    else:
        return 0

# this regex splits on (and captures) the supported ops:
# (, ), |, *, ?, and +
# it also grabs some other (unsupported) ops for better error handling:
# [ ] \ ^ $ { } - .
_grammar_token_re = re.compile(r"([()|*?+\[\],\\^${}\-.])|[ \t\r\n]")
def _parse_grammar(grammar: str, types: Mapping[str, type]) -> 'Grammar':
    """Parse the provided grammar into a set of nested Grammar rules"""
    # parse grammar into tokens
    tokens = _grammar_token_re.split(grammar)

    # stack of grammar components
    stack = [Group()]
    index = 0

    # wrapping this whole function in a try-except to catch any
    # ValueErrors as GrammarErrors
    try:
        for index, token in enumerate(tokens):
            if not token:
                # token is empty string or (whitespace)
                continue
            if token.islower() and token.isalnum():
                # it's a keyword
                stack[-1].add(Keyword(token))
            elif token.isupper() and token.isalnum():
                # do some kind of type checking here
                try:
                    obj_type = types[token]
                except KeyError:
                    raise GrammarError(GrammarError.BAD_TYPE, index,
                                       tokens, grammar, types=types)
                stack[-1].add(Variable(obj_type))
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
                    raise GrammarError(GrammarError.UNMATCH_CLOSE, index,
                                       tokens, grammar)
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
                raise GrammarError(GrammarError.UNRECOGNIZED, index,
                                   tokens, grammar)
        # do we have any unfinished capturing groups on the stack?
        if len(stack) > 1:
            count = len(stack) - 1
            raise GrammarError(GrammarError.UNMATCH_OPEN, index, tokens,
                               grammar, parens=count)

        stack[0].cleanup()
    except ValueError as ex:
        raise GrammarError(ex.args[0], index, tokens, grammar) from ex

    return stack[0]


class Grammar(ABC):
    """Abstract Base Class for all other grammar expressions
    Grammar provide high-level abstractions for a provided grammar.
    """

    DEFAULT_TYPES = {
        "OBJECT": _types.GameObject,
        "LOCATION": _types.Location,
        "EXIT": _types.Exit,
        "CHARACTER": _types.Character,
        "ITEM": _types.Item,
        "ENTITY": _types.Entity
    }

    def __init__(self, expr):
        self.inner = expr

    @abstractmethod
    def to_nfa(self):
        """Return a Nondeterministic Finite Automaton representing
        this Grammar
        """
        pass

    # lazily create the NFA
    @property
    def nfa(self):
        if not hasattr(self, "_nfa"):
            self._nfa = self.to_nfa()
        return self._nfa

    def __repr__(self):
        """overriding repr()"""
        return f"{type(self).__name__}({self.inner!r})"

    def __eq__(self, other):
        """Overriding == for convenient unit testing"""
        return isinstance(other, type(self)) and other.inner == self.inner

    def matches(self, inp: Iterable[str]):
        """Returns true if the provided input is syntactically valid."""
        return self.nfa.matches(inp)

    def annotate(self, inp: Iterable[str]):
        """Returns a list of all syntactically valid annotations of inp,
        based on this grammar.

        raises ParseError if no valid annotation found.
        (This means that the returned list is guaranteed to have at
        least one valid intepretation.)
        """
        return self.nfa.annotate(inp)

    def interpret(self, inp: Iterable[str], context: Iterable[GameObject]):
        """Returns a list of all syntactically and contextually valid
        interpretations of inp, based on this grammar.

        raises ParseError if no syntactically valid annotation found.
        raises ContextError if a syntatctically valid interpretation is
        found, but referenced objects cannot be found in the provided
        context.

        Thus, if this function executes normally, it is guaranteed to
        have at least one valid itnerpretation.
        """
        return self.nfa.interpret(inp, context)

    @staticmethod
    def from_string(inp: str, types: Mapping[str, type] = None) -> 'Grammar':
        """Parse a string into a Grammar.

        If you want to specify custom types, you can optionally pass a
        dict mapping (capitalized) strings to types. By default, the
        types OBJECT, LOCATION, EXIT, CHARACTER, ITEM, and ENTITY are
        supported.
        """
        if types is None:
            types = Grammar.DEFAULT_TYPES
        return _parse_grammar(inp, types)


class Group(Grammar):
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
                raise ValueError(GrammarError.EXTRA_QUANT)
        else:
            raise ValueError(GrammarError.NO_PREDICATE)

    def add_alternative(self):
        if not self.args:
            # if we haven't added anything, raise an error
            raise ValueError(GrammarError.EMPTY_ALT)
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
                raise ValueError(GrammarError.EMPTY_ALT)
            else:
                # the entire group is empty
                raise ValueError(GrammarError.EMPTY_GRP)
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
class Keyword(Grammar):
    def __init__(self, keyword):
        self.inner = keyword

    def to_nfa(self):
        return NFA.emitter(NFA.match_on(self.inner), self)


# TODO: join union of Variables into one variable
# UPDATE: yes, this helps reduce the number of exponential options
class Variable(Grammar):
    def __init__(self, *types):
        self.types = types
        self.inner = types

    def to_nfa(self):
        # this nfa matches one word exactly
        # however, variables can match an unlimited number of words
        return NFA.emitter(NFA.plus(NFA.match_on(Token.ANY)), self)


# three quantifiers
class Star(Grammar):
    """This Grammar rule represents the Kleene Star of the inner rule.
    https://en.wikipedia.org/wiki/Kleene_star
    """
    def __init__(self, expr):
        self.inner = expr

    def to_nfa(self):
        return NFA.star(self.inner.to_nfa())


class Plus(Grammar):
    """This Grammar rule represents the Kleene Plus of the inner rule.
    https://en.wikipedia.org/wiki/Kleene_star#Kleene_plus
    """

    def to_nfa(self):
        return NFA.plus(self.inner.to_nfa())


class Optional(Grammar):
    """This Grammar rule makes the inner operation optional."""

    def to_nfa(self):
        return NFA.optional(self.inner.to_nfa())


# Creating a few enums for simplicity
class Token(Enum):
    EPSILON = 0 # epsilon transition
    ANY = 1
    END = 2
    NOTHING = 3 # used in parse errors
    EMIT = 4 # internal value used in NFRs, do not use in token streams
    # do not mix up epsilon transitions with "nothing"

# annotation used for parsing grammar rules
Parsed = namedtuple("Parsed", ["rule", "tokens"])
# reason for a parse error failing
Fail = namedtuple("Fail", ["expected", "received"])

class Interp:
    """An Interp is a single interpretation that arises from a grammar,
    list of tokens, and some context of game objects.
    """
    __slots__ = ['state', 'stack', 'objects']
    def __init__(self, state=0, stack=None, objects=None):
        """Create a new (empty) interpretation to add rules to"""
        # state of the NFA that this item ended in
        self.state = state
        # stack of tokens / parse
        self.stack = [] if not stack else stack
        # game objects referenced by the token stream
        self.objects = [] if not objects else objects

    def __repr__(self):
        """return a pythonic representation of this Interp"""
        return f"Interp({self.state}, {self.stack}, {self.objects})"

    def consume_token(self, token):
        """add a token to the stack"""
        self.stack.append(token)

    def consume_rule(self, rule: Grammar):
        """apply rule to the unassigned tokens on the stack"""
        phrase = []
        while self.stack and isinstance(self.stack[-1], str):
            phrase.append(self.stack.pop())
        phrase = phrase[::-1]
        self.stack.append(Parsed(rule, phrase))

    def add_match(self, obj: _types.GameObject):
        self.objects.append(obj)

    def copy(self):
        """return a deep-ish copy of this interpretation"""
        return Interp(self.state, self.stack.copy(), self.objects.copy())


def _add_epsilon(from_state, to_index):
    """helper function that checks if a state can have an epsilon transition
    before adding to it"""
    # if any words are in from_state, we cannot add an epsilon
    for match in from_state:
        if match is not Token.EPSILON and match is not Token.EMIT:
            raise ValueError("Cannot add epsilon transition to state with matches")
    if Token.EPSILON not in from_state:
        from_state[Token.EPSILON] = []
    from_state[Token.EPSILON].append(to_index)


class NFA:
    """Class representing a nondeterministic finite automaton.
    I recommend using these static methods to build up your NFA from
    the bottom up:
        NFA.match_on() (for a basic matcher)
        NFA.star(), NFA.plus(), NFA.optional() (quantifiers)
        NFA.concat(), and NFA.union() (combining multiple rules)
        NFA.emitter() (for emitting signals when a rule is completed)

    Under the hood, we use a table to represent the states of the NFA.
    The first state (index 0) is always the beginning state.
    The last state (index len(table) - 1) is always the accepting state.
    Each state contains either epsilon transition to other states (a
    list of indices) or paths to other states given specific tokens (a
    dictionary).

    Much of the inspiration for this class comes from this blogpost from
    Denis Kyashif:
    https://deniskyashif.com/2019/02/17/implementing-a-regular-expression-engine/

    If you want to understand how this stage works, I highly recommend
    reading this blog post (maybe more than once).
    """
    def __init__(self, table=None):
        """Create an NFA based on the provided table.
        If no table is provided, a one-state NFA is created
        """
        if table is None:
            table = [{}]
        # the NFA is represented by a table
        # self._table[0] is always the beginning element,
        # and self._table[-1] is always the end (accepting) element
        self._table = table

    def __repr__(self):
        return f"NFA({self._table})"

    def copy(self):
        """Return a deep copy of this NFA"""
        return NFA(deepcopy(self._table))

    def _shift_table(self, shift_by: int):
        """Return a copy of table with all indices incremented"""
        new_table = []
        for state in self._table:
            # TODO: should regular match nodes be allowed to emit?
            new_state = {}
            if Token.EMIT in state:
                new_state[Token.EMIT] = state[Token.EMIT]
            if Token.EPSILON in state:
                shifted = [index + shift_by for index in state[Token.EPSILON]]
                new_state[Token.EPSILON] = shifted
            # if a state has epsilon transitions, then it only
            # has epsilon transitions
            else:
                for token, index in state.items():
                    if token is not Token.EMIT:
                        new_state[token] = index + shift_by
            new_table.append(new_state)
        return new_table

    def _concat_with(self, nxt):
        """Return a copy of this NFA joined to a copy of nxt"""
        table = deepcopy(self._table)
        nxt_table = nxt._shift_table(len(table))
        # index of nxt's start node will be length of this table
        _add_epsilon(table[-1], len(table))
        # update all of the indices in nxt
        table.extend(nxt_table)
        return NFA(table)

    @staticmethod
    def match_on(value):
        """Returns a simple NFA that matches on [value]"""
        table = [
            {value : 1}, # this is saying 'go to the next index'
            {} # since this is the last index, we win
        ]
        return NFA(table)

    @staticmethod
    def star(nfa):
        """Returns a NFA matching the Kleene Star of NFA"""
        # To implement the Klein Star operation, we simply
        # add a new state to the beginning and a new state to the end
        # This new state at the beginning can either transition to the
        # end or to the first node of the table.

        # shift one to account for new state at beginning
        shifted = nfa._shift_table(1)

        # old end can now loop to the old beginning
        _add_epsilon(shifted[-1], 1)
        # add an epsilon transition to the end of the future table
        _add_epsilon(shifted[-1], len(shifted) + 1)

        new_start = {Token.EPSILON : [ 1, len(shifted) + 1]}
        new_end = {}

        table = [new_start] + shifted
        table.append(new_end)

        return NFA(table)

    @staticmethod
    def plus(nfa):
        """Returns a NFA matching the Kleene Plus of NFA"""
        # this could easily be implemented as NFA.concat(nfa, NFA.star(nfa))
        # word+ is equivalent to word word*
        # NFA.concat(nfa, NFA.closure(nfa))
        # however, we can save one epsilon state with this implementation
        # TODO: implement in the more optimal fashion above
        table = nfa.copy()._table

        # add an epsilon from the last state in the table to the beginning,
        # to allow for a loop after entering things
        _add_epsilon(table[-1], 0)
        _add_epsilon(table[-1], len(table))

        # add a new end
        table.append({})
        return NFA(table)

    @staticmethod
    def optional(nfa):
        # this approach is essentially the same as NFA.star, except
        # we do not add an epsilon transition from the old end to the new start

        # shift one to account for new state at beginning
        shifted = nfa._shift_table(1)
        # add an epsilon transition to the end of the future table
        _add_epsilon(shifted[-1], len(shifted) + 1)

        # new start can either push to the new NFA or bypass entirely
        new_start = { Token.EPSILON : [ 1, len(shifted) + 1]}
        new_end = {}

        table = [new_start] + shifted
        table.append(new_end)
        return NFA(table)

    @staticmethod
    def union(*nfas):
        # for optimization purposes, avoid
        if not nfas:
            return NFA()
        elif len(nfas) == 1:
            return nfas[0].copy()

        start = {Token.EPSILON : []}
        table = [start]
        old_ends = []

        for nfa in nfas:
            # add an epsilon to the start of this table
            # we do the 'unsafe' version here, since we know
            # start is a proper epsilon state
            start[Token.EPSILON].append(len(table))
            table.extend(nfa._shift_table(len(table)))
            # the new index of the old end of the table is the new length of the table
            old_ends.append(len(table) - 1)

        # add a new end
        new_end = len(table)
        table.append({})
        for end in old_ends:
            # we use the checked version here, because we need to check
            # if the ends are not epsilon states
            _add_epsilon(table[end], new_end)
        return NFA(table)

    @staticmethod
    def concat(*nfas):
        """concatentate several NFAs together
        note, passing in zero NFAs will produce a single state
        that is already accepting
        """

        # If no NFAs provided, return an empty NFA (matches exactly nothing).
        # We do this to avoid excess states
        if not nfas:
            return NFA()
        # Get the first NFA's table
        table = deepcopy(nfas[0]._table)
        # start concatenating!
        for nxt_nfa in nfas[1:]:
            # this is similar to NFA._concat_with
            nxt_table = nxt_nfa._shift_table(len(table))
            _add_epsilon(table[-1], len(table))
            table.extend(nxt_table)
        return NFA(table)

    @staticmethod
    def emitter(nfa: 'NFA', rule: Grammar) -> 'NFA':
        """Return a copy of [nfa] that emits a rule on completion.
        We use this when we want to build NFAs that actually parse input
        instead of just returning 'True' or 'False' if it matches.
        """
        # check that the provided value is a Grammar
        if not isinstance(rule, Grammar):
            raise TypeError("Error. Expected Grammar for rule, got "
                             f"'{type(rule)}'")

        table = nfa.copy()._table
        emit_state = {
            Token.EMIT: rule
        }
        # point the old last state to the new emitting state
        _add_epsilon(table[-1], len(table))
        # add the state to the table
        table.append(emit_state)

        return NFA(table)

    def transition(self, state_index, token):
        """Iterate over the states produced by the current state
        [state_index] with [token] as input.
        Any epsilon transitions are crawled through until reaching
        a non-epsilon transition.
        """
        state = self._table[state_index]
        if Token.EPSILON in state:
            for next_state in state[Token.EPSILON]:
                yield from self.transition(next_state, token)
        else:
            if state_index == len(self._table) - 1:
                # edge case, we already reached the end, but we're
                # pushing through the rest of the epsilons
                # so, just re-yield the state_index
                if token is Token.END:
                    yield state_index
            elif Token.ANY in state and token is not Token.END:
                yield state[Token.ANY]
            elif token in state:
                yield state[token]

    def trans_emit(self, state_index, token, emits=()):
        state = self._table[state_index]
        if Token.EMIT in state:
            emits = emits + (state[Token.EMIT],)
        if Token.EPSILON in state:
            for next_state in state[Token.EPSILON]:
                yield from self.trans_emit(next_state, token, emits)
        else:
            if state_index == len(self._table) - 1:
                # edge case, we already reached the end, but we're
                # pushing through the rest of the epsilons
                # so, just re-yield the state_index
                if token is Token.END:
                    yield (emits, state_index)
            elif Token.ANY in state and token is not Token.END:
                yield (emits, state[Token.ANY])
            elif token in state:
                yield (emits, state[token])

    def trans_expected(self, state_index, token):
        """Iterate over the states that FAIL to produce a new state in
        response to tokens. This method produces a reason for each
        failure.
        """
        # follow the same approach as transition
        state = self._table[state_index]
        if Token.EPSILON in state:
            for next_state in state[Token.EPSILON]:
                yield from self.trans_expected(next_state, token)
        else:
            if state_index == len(self._table) - 1:
                # received an extra token at the end
                if token is not Token.END:
                    yield Token.NOTHING
            else:
                if token is Token.END:
                    # get all the possible tokens
                    expected = tuple(state)
                    yield from expected
                elif not (token in state or Token.ANY in state):
                    expected = tuple(state)
                    yield from expected

    def matches(self, tokens):
        # add Token.END to the list of tokens, this helps
        # push through any states that are still epsilons
        tokens = tokens + [Token.END]

        # we can use a set because we don't really care about the paths
        states = {0}

        for token in tokens:
            next_states = set()
            for state in states:
                next_states.update(self.transition(state, token))
            states = next_states
        # did we reach the final state?
        return (len(self._table) - 1) in states

    def annotate(self, tokens):
        """Produce a list of all possible annotations for this
        NFA on Grammar emissions.
        raises ParseError if no valid interpretation can be found.
        (This means that the returned list is guaranteed to have at
        least one valid intepretation.)
        """
        tokens = tokens + [Token.END]

        states = [0]
        stacks = [[]]

        for token in tokens:
            next_states = []
            next_stacks = []
            from pprint import pprint
            pprint(list(zip(states,stacks)))
            for (state, stack) in zip(states, stacks):
                for (emits, next_state) in self.trans_emit(state, token):
                    print(f"next_state: {next_state}")
                    next_states.append(next_state)
                    if emits:
                        # if you ever want nested grammar rules, modify
                        # this part
                        # until then, it's a safe assumption that one token =
                        # one grammar
                        rule, = emits

                        new_stack = stack.copy()

                        claimed = []
                        # start poppin off the stack until we reach a rule
                        while new_stack and isinstance(new_stack[-1], str):
                            claimed.append(new_stack.pop())
                        # group the rule and preceding tokens
                        new_stack.append(Parsed(rule, claimed[::-1]))

                        # add the new token to it for next round
                        new_stack.append(token)
                        next_stacks.append(new_stack)
                    else:
                        next_stacks.append(stack + [token])

            # if we ran out of states, we need to give an explanation
            if not next_states:
                failures = []
                for (state, stack) in zip(states, stacks):
                    # gather all the things that we could have expected
                    # using a set to remove duplicates
                    expected = tuple(set(self.trans_expected(state, token)))
                    failures.append(stack + [Fail(expected, received=token)])
                raise ParseError(failures)

            states = next_states
            stacks = next_stacks

        # if stacks have survived Token.END, then they are good
        return stacks

    def interpret(self, tokens, context):
        """Produce a list of all valid interpretations for the provided
        tokens, based on some context (an iterable that produces game
        objects).

        This is similar to the annotate method, but rather than just
        check the results syntactically, the function pairs variables
        with matching game_objs in the context.

        An input has a valid interpretation if it matches syntactically
        and each variable can be matched with some object in the context.
        """

        interpretations = [Interp()]
        ctx_fails = []
        tokens = tokens + [Token.END]
        for token in tokens:
            next_interps = []
            ctx_fails = []
            for interp in interpretations:
                for (emits, next_state) in self.trans_emit(interp.state, token):
                    # TODO: copy interp iff we are not on the last emission
                    new_interp = interp.copy()
                    new_interp.state = next_state
                    if emits:
                        # if you ever want nested grammar rules, modify
                        # this. until then, one token -> 1 rule
                        rule, = emits
                        new_interp.consume_rule(rule)

                        # if rule was a variable, we run a context check
                        if isinstance(rule, Variable):
                            # get the tokens assigned to this Variable
                            rule, phrase = new_interp.stack[-1]
                            matches = _check_context(phrase, rule.types,
                                                     context)
                            # if no matches, this interpretation fails
                            # and should make a note of that
                            if not matches:
                                ctx_fails.append((rule, phrase))

                            new_interp.consume_token(token)
                            for match in matches:
                                valid_interp = new_interp.copy()
                                valid_interp.add_match(match)
                                next_interps.append(valid_interp)
                        # if rule is not variable, then interp is valid
                        else:
                            new_interp.consume_token(token)
                            next_interps.append(new_interp)
                    else:
                        new_interp.consume_token(token)
                        next_interps.append(new_interp)

            # if we do not have any valid interpretations, explain why
            if not next_interps:
                # if we have some failures, then the token has correct
                # syntax, but nothing in the context matches
                if ctx_fails:
                    raise ContextError(ctx_fails)

                # otherwise, we have a syntax failure, time to backtrack
                # and find what was expecting
                syntax_fails = []
                for i in interpretations:
                    expected = tuple(set(self.trans_expected(i.state, token)))
                    syntax_fails.append(i.stack +
                                       [Fail(expected, received=token)])
                raise ParseError(syntax_fails)

            # we have more valid interpretations, time to move on
            interpretations = next_interps

        # if stacks have survived Token.END, then they are good
        return [interp.objects for interp in interpretations]


def _check_context(phrase, types, context):
    """Search context for all game_objs matching the input phrase and
    types
    """
    # lots of possible optimizations / features here like:
    # dropping articles (the, a, an) in case the user added some
    # how to handle things with multiple names?
    # (maybe split on whitespace and any overlap is considered a match)
    # cache the results of this code chunk
    identifier = " ".join(phrase).lower()
    matches = []
    for game_obj in context:
        if (str(game_obj).lower() == identifier and
            isinstance(game_obj, types)):
            matches.append(game_obj)
    return matches
