'''Miscellaneous (but useful) functions that don't fit in other modules'''
import math
import re
from collections import namedtuple
from collections.abc import Iterable

__cap_re = re.compile("(?<!^)(?<![A-Z])([A-Z])")
def camel_to_space(name):
    '''adds spaces before capital letters
    ex: "CamelCaseClass" => "Camel Case Class"
    '''
    return __cap_re.sub(r" \1", name)

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


def has_instance(iterable, class_or_tuple):
    """returns True if iterable contains an instance of cls"""
    for i in iterable:
        if isinstance(i, class_or_tuple):
            return True
    return False

def has_subclass(iterable, class_or_tuple):
    """returns True if iterable contains an subclass of cls"""
    for i in iterable:
        if issubclass(i, class_or_tuple):
            return True
    return False

# creating a base class for FindParams
__base = namedtuple("FindParams",
                    field_names=["name", "type", "maxdepth", "pov",
                                 "optional"],
                    defaults=[None, None, 0, None, None])


# inheriting from FindParams to add a decrement method
class FindParams(__base):

    def decrement(self):
        return self._replace(maxdepth=self.maxdepth-1)

def find(obj, name=None, type=None, maxdepth=0, pov=None, optional=None, **other_fields):
    '''find in-game objects inside of [obj]

    optional arguments
    names: str or iterable of strings -- only return objects when
        str(object) == names
    types: type or iterable of types -- only return objects that are
        instances of one of the provided types
    maxdepth: int -- descend at most [maxdepth] during recursive search.
        (default: search only local object)
    pov: Character -- only look through objects that [pov] has
        permission to look at
    optional: dict -- optional fields that items may not have

    additionally, you may provide other object attributes to match on
    as keywords
    '''
    # It's generally bad form to override builtin functions / types.
    # I used "type" as an argument name just to make the interface
    # consistent with FindParams, but here I switch our argument's name to
    # 'typ' and brought the builtin back.
    (typ, type) = (type, __builtins__["type"])

    # Setting up the arguments.
    # First, coerce names into a set of lowercase strings.
    errmsg = ("util.find() names argument should be a str or "
              "iterable of strings, received type '{}'")
    if isinstance(name, str):
        name = {name.lower()}
    elif isinstance(name, Iterable):
        try:
            name = set(map(str.lower, name))
        except TypeError as ex:
            # find the offending type and raise an error
            for n in name:
                if not isinstance(n, str):
                    raise TypeError(errmsg.format(type(n)))
    elif name is not None:
        raise TypeError(errmsg.format(type(name)))
    # Next, we coerce the provided typ into a tuple of types.
    errmsg = ("util.find() types argument should be a type or "
              "iterable of types, received value '{}'")
    if typ is not None:
        # coerce types into a tuple
        if isinstance(typ, Iterable):
            typ = tuple(typ)
        else:
            typ = (typ,)
        # check that all the provided typ are a type
        for member_type in typ:
            if not isinstance(member_type, type):
                raise TypeError(errmsg.format(type(member_type)))

    # Check that maxdepth is actually a number
    if maxdepth is None:
        # infinity makes for easier calculations
        maxdepth = math.inf
    elif not isinstance(maxdepth, (int, float)):
        raise TypeError("util.find() maxdepth argument must be int or float, "
                        f"received type '{type(maxdepth)}'")
    # Check that optional is a dict
    if optional is not None and not isinstance(optional, dict):
        raise TypeError("util.find() optional argument must be dict, "
                        f"received type '{type(optional)}'")

    # Chunk the arguments into a FindParams object
    params = FindParams(name, typ, maxdepth, pov, optional)

    # call the internal function
    return list(find_child(obj, params, **other_fields))


def find_child(obj, params: FindParams, **other_fields):
    '''Recursively search [obj] for objects matching the provided
    parameters. Unless you are implementing a helper 'find_child'
    method on a class, you should use util.find instead.
    '''
    # we can skip all of the tedious input validation

    # check that we haven't exceeded the maximum depth
    if params.maxdepth < 0:
        return
    # developers can supply a 'find_child' to speed up the find process
    # we would use a try-except here, but AttributeErrors way downstream
    # can cause major problems
    if hasattr(obj, 'find_child'):
        yield from obj.find_child(params, **other_fields)
    # no 'find_child' method was supplied
    else:
        # all in-game objects should have a 'children' method
        try:
            children = obj.children()
        except AttributeError:
            raise ValueError(f"find received {obj!r} of {type(obj)}, but "
                             "expected in-game object like Location, "
                             "Character, Item, or Entity")
        for child in children:
            # check each of the arguments
            if find_check(child, params, **other_fields):
                yield obj
            # recurse
            # we call params.decrement() to lower the maxdepth
            yield from find_child(params.decrement(), **other_fields)


def find_check(obj, params: FindParams, **other_fields) -> bool:
    '''Returns true if the provided arguments (find parameters)
    hold true for the provided [obj].
    '''
    if params.name is not None and str(obj).lower() not in params.name:
        return False
    if params.type is not None and not isinstance(obj, params.type):
        return False
    # if other_fields are provided, then the items MUST provide those fields
    if not obj_does_have(obj, other_fields):
        return False
    # check for direct matches with other_fields
    # objects are necessarily required to have these fields,
    # but if they do have them, they better match
    if params.optional:
        for field, value in params.optional.items():
            try:
                if getattr(obj, field) != value:
                    return False
            except AttributeError:
                pass
    return True


def obj_does_have(obj, must_have) -> bool:
    for k, v in must_have.items():
        try:
            if getattr(obj, k) != v:
                return False
        except AttributeError:
            return False
    return True
