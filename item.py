'''
This module provides several base classes for items
EquippableBase:
    base class for items with "equip" and "unequip" methods
UsableBase
    base class for items with a "use" methods
MiscItemBase
    items with no methods requirements
'''
import inspect
from abc import ABC
from typing import List
from util import camel_to_space
from character import Command, Character, CharFilter
import inventory as inv

#TODO: add access and visibility filters
class ItemClass(type):
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


class Item(metaclass=ItemClass):
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
        # collect all of the commands
        self._commands = {}
        for obj in namespace.values():
            if isinstance(obj, Command):
                self._commands[str(obj)] = obj


class Equippable(Item, metaclass=EquippableClass):
    '''Base class for all Equippable items.
    You must define your own "target" like so:
        target = inv.EquipTarget("right arm")
    To trigger effects when the item is equipped or unequipped, override
    the 'on_equip' or 'on_unequip' methods.
    By default, any methods decorated with @character.Command will be
    added to the player's equip_dict when equipped.
    '''

    def on_equip(self, char: Character):
        pass

    def on_unequip(self, char: Character):
        pass

    def add_cmds(self, char: Character):
        '''add all the commands from this item to the char
        any conflicting commands are simply shadowed'''
        for cmd in self._commands.values():
            if cmd.filter.permits(char):
                cmd = cmd.specify(self, char)
                char.cmd_dict.add_cmd(cmd)

    def remove_cmds(self, char: Character):
        '''remove all the commands from this item from char'''
        for cmd in self._commands.values():
            cmd = cmd.specify(self, char)
            if char.cmd_dict.has_cmd(cmd):
                char.cmd_dict.remove_cmd(cmd)


class Usable(ABC):
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
