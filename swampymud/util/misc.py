'''Miscellaneous (but useful) functions that don't fit in other modules'''
import math
import re
from collections.abc import Iterable

_cap_re = re.compile("(?<!^)(?<![A-Z])([A-Z])")
def camel_to_space(name):
    '''adds spaces before capital letters
    ex: "CamelCaseClass" => "Camel Case Class"
    '''
    return _cap_re.sub(r" \1", name)

# default base alphabet
__ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
def to_base(num, base, alphabet=__ALPHABET):
    '''convert an unsigned integer [num] to [base]. Provide an optional
[alphabet] for different encoding style.
Raises ValueError if base is out of appropriate range [2, len(alphabet)].'''
    # check that the base is in an appropriate range
    try:
        max_base = len(alphabet)
        if base > len(alphabet) or base < 2:
            raise ValueError("Expected base in range [2, %i], received %r"
                             % (max_base, base))
    except TypeError:
        raise TypeError("Expected base with <class 'int'>, received %r" % num)
    # check that the num is an unsigned integer
    try:
        if num < 1:
            if num == 0:
                return "0"
            else:
                raise ValueError("Expected unsigned integer, received %i"
                                 % num)
    except TypeError:
        raise TypeError("Expected num with <class 'int'>, received %r" % num)
    digits = []
    while num > 0:
        num, digit = divmod(num, base)
        digits.append(alphabet[digit])
    return "".join(digits[::-1])

# TODO: replace with itertools groupby
def group_and_count(items, format="%s\t[%i]", single_format="%s", sep="\n"):
    '''takes a list of items and a formatter,
    and produces a list with counts
    if items = ["apple", "apple", "banana", "cap", "cap", "cap"]
    then output =
        apple    [2]
        banana
        cap      [3]
    '''
    counts = {}
    for item in items:
        if item not in counts:
            counts[item] = items.count(item)
    unique_items = list(counts.keys())
    unique_items.sort()
    output = []
    for item in unique_items:
        if single_format and counts[item] == 1:
            output.append(single_format % (item,))
        else:
            output.append(format % (item, counts[item]))
    return sep.join(output)

def has_instance(iterable, class_or_tuple):
    """returns True if iterable contains an instance of cls"""
    for i in iterable:
        if isinstance(i, class_or_tuple):
            return True
    return False

def has_subclass(iterable, class_or_tuple):
    """returns True if iterable contains an subclass of cls"""
    for i in iterable:
        if isinstance(i, class_or_tuple):
            return True
    return False

def find(obj, names=None, types=None, maxdepth=0, char=None, **kwargs):
    '''find in-game objects inside of [obj]

    optional arguments
    names: str or iterable of strings -- only return objects when str(object) == names
    types: type or iterable of types -- only return objects that are instance of one of the provided types
    maxdepth: int -- descend at most [maxdepth] during recursive search. (default: search only local object)
    char: Character -- only look through objects that [char] has permission to look at

    additionally, you may provide other object attributes to match on
    as keywords
    '''
    # setting up the arguements
    # first, coerce names into a set of lowercase strings
    if isinstance(names, str):
        names = {names.lower()}
    elif isinstance(names, Iterable):
        names = set(map(str.lower, names))
    elif names is not None:
        raise TypeError("find: 'names' must be a str or iterable of strings")

    # do the same for types
    if isinstance(types, type):
        types = (types,)
    elif isinstance(types, Iterable):
        types = tuple(types)
    elif types is not None:
        raise TypeError("find: 'types' must be a type or iterable of types")

    # check that maxdepth is actually a number
    if maxdepth is None:
        # infinity makes for easier calculations
        maxdepth = math.inf
    elif not isinstance(maxdepth, (int, float)):
        raise TypeError("find 'maxdepth' must be int or float")

    if maxdepth < 0:
        return
    # visit the root object
    find_check(obj, names, types, **kwargs)

    # call the internal function
    find_child(obj, names, types, maxdepth-1, char, **kwargs)


def find_child(obj, names, types, maxdepth, char, **kwargs):
    # check that we haven't exceeded the maximum depth
    if maxdepth < 0:
        return
    # try to use a 'find_child' method first
    # developers can supply a 'find_child' to speed up the find process
    try:
        yield from obj.find_child(names, type, maxdepth - 1, char, **kwargs)
    # no 'find_child' method was supplied
    except AttributeError:
        # all in-game objects should have a 'children' method
        try:
            children = obj.children()
        except AttributeError:
            raise ValueError(f"find received {obj!r} of {type(obj)}, but "
                             "expected in-game object like Location, "
                             "Character, Item, or Entity")
        for child in children:
            # check each of the arguments
            if find_check(child, names, types, **kwargs):
                yield obj
            # recurse
            yield from find_child(child, names, type, maxdepth - 1, char, **kwargs)

def find_check(obj, names, types, **kwargs) -> bool:
    if names is not None and str(obj).lower() not in names:
        return False
    if types is not None and not isinstance(obj, types):
        return False
    # check for direct matches with any additional kwargs
    for key in kwargs:
        try:
            if obj.key != kwargs[key]:
                return False
        except AttributeError:
            pass
    return True
