'''
This module provides base classes for Items.
item.Item acts as a base class for all items. Besides providing a few
skeletal methods to help with serialization and user interaction, this
class is relatively straightforward.

item.Usable is an abstract class used for checking ItemClasses. A
developer may create a 'Usable' class by simply providing an 'on_use'
method.

item.Equippable is a subclass of Item that provides additional features,
including support for character.Command methods.
'''
import inspect
import abc
from typing import List
from swampymud import _types
from swampymud.util import camel_to_space
from swampymud.character import Command, Character
import swampymud.inventory as inv

#TODO: add interact and perceive filters
class ItemClass(type, _types.ItemClass):
    '''Metaclass establishing behavior for all items'''

    def __init__(self, cls, bases, namespace):
        if "classname" not in namespace:
            self.classname = camel_to_space(cls)
        if "description" not in namespace:
            if self.__doc__ is not None:
                self.description = inspect.cleandoc(self.__doc__)
            else:
                self.description = "[No description provided.]"
        super().__init__(cls, bases, namespace)

    def __str__(self):
        '''returns a string representation of this class'''
        return self.classname


class Item(_types.Item, metaclass=ItemClass):
    '''Base class for all Item classes.
    Implement 'on_use' to make a Usable item. To trigger certain code
    when this item is picked up or dropped, override 'on_pickup'
    or 'on_drop', respectively.
    '''

    # default label, can be overriden
    label = "Item"

    def __str__(self):
        """Return a simple representation of this item.
        By default, str(item) returns the name of the item's class.
        """
        return self.classname

    # these methods can be overriden
    def on_pickup(self, char: Character, args: List[str]):
        """override to trigger effects when this item is picked up"""
        pass

    def on_drop(self, char: Character, args: List[str]):
        """override to trigger effects when this item is dropped"""
        pass

    # serialization-related methods
    @classmethod
    def load(cls, data):
        '''default implementation of load, calls init with no args'''
        return cls()

    def post_load(self, data):
        '''no post-load actions required by default implementation'''

    def save(self):
        '''return a pythonic representation of this object
        this base class has no fields, so no data is returned'''
        return {}


class EquippableClass(ItemClass):
    '''Metaclass for all items that can be equipped'''

    def __init__(self, cls, bases, namespace):
        super().__init__(cls, bases, namespace)
        # ensure that developers have added an equip target
        if cls != "Equippable":
            if not hasattr(self, "target"):
                raise AttributeError(f"Attempted to define Equippable '{cls}'"
                                     " without defining a target.")
            if not isinstance(self.target, inv.EquipTarget):
                raise TypeError(f"When defining Euippable '{cls}' a target was"
                                " provided, but it wasn't an EquipTarget.")

        # note that this is essentially the same as CharacterClass
        # first gather the Commands defined in this class
        self._local_commands = {}
        for value in namespace.values():
            if isinstance(value, Command):
                value.label = "Equipped"
                self._local_commands[str(value)] = value

        # now gather all commands, with the most recent commands exposed
        self._commands = {}
        for base in reversed(self.__mro__):
            if not isinstance(base, EquippableClass):
                continue
            self._commands.update(base._local_commands)
        self._commands.update(self._local_commands)


class Equippable(Item, metaclass=EquippableClass):
    '''Base class for all Equippable items.
    You must define your own "target" like so:
        target = inv.EquipTarget("right arm")
    To trigger effects when the item is equipped or unequipped, override
    the 'on_equip' or 'on_unequip' methods.
    By default, any methods decorated with @character.Command will be
    added to the player's equip_dict when equipped.
    '''

    def add_cmds(self, char: Character):
        '''Add all the commands from this item to the char.
        Any conflicting commands are simply shadowed'''
        for cmd in self._commands.values():
            if cmd.filter.permits(char):
                cmd = cmd.specify(self, char)
                char.cmd_dict[str(cmd)] = cmd

    def remove_cmds(self, char: Character):
        '''remove all the commands from this item from char'''
        for cmd in self._commands.values():
            cmd = cmd.specify(self, char)
            try:
                char.cmd_dict.remove_value(str(cmd), cmd)
            # command was not in cmd_dict
            except KeyError:
                pass
            except ValueError:
                pass

    # these methods can be overriden
    def on_equip(self, char: Character):
        """override to trigger effects when this item is equipped"""
        pass

    def on_unequip(self, char: Character):
        """override to trigger effects when this item is unequipped"""
        pass


class Usable(abc.ABC):
    '''Use to Check if an item implements 'on_use' in a Pythonic way.
        isinstance(item_obj, Usable)
    is roughly equivalent to
        isinstance(item_obj, Item) and item_obj has an 'on_use' method
    Do not attempt to derive a new item type from this class!
    If you want to make a 'Usable' item, simply derive from Item and add
    an 'on_use' method yourself.
    '''

    @classmethod
    def __subclasshook__(cls, subclass):
        if cls is Usable:
            return (isinstance(subclass, ItemClass) and
                    hasattr(subclass, "on_use") and
                    callable(subclass.on_use))
        else:
            return NotImplemented
