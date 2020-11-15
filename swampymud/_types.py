"""
This module defines a base "GameObject" type, base classes for the 3
first-class (Characters, Items, and Entities), and Locations / Exits.

TL;DR: do not import this module. Do not follow the example that this
module sets.

Inheritance is widely overused. (This library is no exception.)
More modern languages like Go and Rust favor interfaces and traits,
which guide programmers to composition instead of inheritance.

However, in a language without interfaces/traits, inheritance is all
we have. More importantly, without good pattern matching, the best we
can do is look at an object's type.

So, it's not uncommon to do things like
> isinstance(game_obj, Character)

In fact, use this pattern a lot! location.py uses it for all of the
3 first-class items.
entity.py uses character.Filter, which does isinstance checks for
Character.
item.py uses character.Command and Character for type hints.
Finally, for our ergonomic parser-generator, we need ALL of the
types in order to link together things. But character also depends
on parser!

This creates a problem, because now our modules all depend on each other,
usually just because they need to know other's freakin' names!
Most compiled languages would allow you to declare a type so that other
modules can use it.

So here, we simply declare a few types just to avoid a circular dependency.
These classes add NO METHODS. They're just here to help with typing.
"""

class GameObject:
    """Base for all swampymud in-game objects"""

# the "first class" game objects and their metaclasses
class CharacterClass:
    """internal type, see swampymud.character.CharacterClass instead"""

class Character(GameObject):
    """internal type, see swampymud.character.Character instead"""

class EntityClass:
    """internal type, see swampymud.entity.EntityClass instead"""

class Entity(GameObject):
    """internal type, see swampymud.entity.Entity instead"""

class ItemClass:
    """internal type, see swampymud.entity.EntityClass instead"""

class Item(GameObject):
    """internal type, see swampymud.item.Item instead"""

# locations are considered second-class
class Location(GameObject):
    """internal type, see swampymud.location.Location instead"""

class Exit(GameObject):
    """internal type, see swampymud.location.Exit instead"""
