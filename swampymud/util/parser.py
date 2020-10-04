"""module for parser generator
The Grammar of Command Grammars:
grammar =


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

In the grammar of these paraser-generators, we note the following.


"""

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

