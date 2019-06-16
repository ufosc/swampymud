'''
This module provides several base classes for items
EquippableBase:
    base class for items with "equip" and "unequip" methods
UsableBase
    base class for items with a "use" methods
MiscItemBase
    items with no methods requirements
'''
from util import camel_to_space
from command import SpecificCommand
import character

class Item(type):
    '''Metaclass establishing behavior for all items'''
    def __init__(self, cls, bases, namespace):
        if "_item_name" not in namespace:
            self._item_name = camel_to_space(cls)
        if "_item_type" not in namespace:
            self.item_type = "Item"
        super().__init__(cls, bases, namespace)

    def __str__(self):
        '''return str(self)'''
        return self._item_name


class EquipCommand(SpecificCommand):
    """SpecificCommand with the type set to 'Equipped'"""
    def __init__(self, name, func, type_name="Equipped", filter=None, 
                 source=None, char=None):
        if filter is None:
            # if no filter is provided, use an empty blacklist 
            # to let everyone use it
            filter = character.CharFilter("blacklist")
        super().__init__(name, func, type_name, filter, source, char)


def filtered_command(filt):
    '''decorator for methods with CharFilters'''
    def inner(func):
        return EquipCommand(func.__name__, func, filter=filt)
    return inner


def equip_command(func):
    '''decorator for methods without CharFilters'''
    return EquipCommand(func.__name__, func)


class Equippable(Item):
    '''Metaclass for all items that can be equipped'''
    def __init__(self, cls, bases, namespace):
        super().__init__(cls, bases, namespace)
        self.item_type = "Equippable"
        if cls != "EquippableBase": 
            #TODO: assert that target is an EquipTarget
            assert "target" in namespace or any([hasattr(base, "target") for base in bases])
            assert "equip" in namespace or any([hasattr(base, "equip") for base in bases])
            assert "unequip" in namespace or any([hasattr(base, "unequip") for base in bases])
        self._commands = {}
        for obj in namespace.values():
            if isinstance(obj, EquipCommand):
                self._commands[obj.name] = obj


class EquippableBase(metaclass=Equippable):
    '''Base class for all Equippable items
    You must define your own "target", "equip", and "unequip" methods
    '''
    _description = "An equippable item"
    @property
    def name(self):
        '''Creating a readonly "name" property'''
        return self._item_name

    def describe(self):
        return self._description

    def __str__(self):
        '''Return a string representing the object
        this will be how the item appears to the player'''
        return self._item_name

    def __eq__(self, other):
        '''Test if the other item is equivalent, based on
        the item_name and the item_type being the same
        '''
        try:
            return (self.name == other.name and
                    self.item_type == other.item_type)
        except:
            return False

    def add_cmds(self, char):
        '''add all the commands from this item to the char
        any conflicting commands are simply shadowed'''
        for cmd in self._commands.values():
            if cmd.filter.permits(char):
                cmd = cmd.specify(self, char)
                char.cmd_dict.add_cmd(cmd)

    def remove_cmds(self, char):
        '''remove all the commands from this char that belong to the item'''
        for cmd in self._commands.values():
            cmd = cmd.specify(self, char)
            if char.cmd_dict.has_cmd(cmd):
                char.cmd_dict.remove_cmd(cmd)




class EquipTarget:
    '''Class for identifying specific slots that an equippable item
    may be equipped to
    Each CharacterClass has a field, 'equip_slots', that specifies what
    types of items they can equip'''
    # next id to be used
    next_id = 0
    # all targets mapped by name
    _targets = {}

    def __new__(cls, name):
        '''Create a new EquipTarget'''
        name = name.capitalize()
        # if the target name has already been registered,
        # return the existing object
        # this is done to save memory
        if name in cls._targets:
            return cls._targets[name]
        return super().__new__(cls)

    def __init__(self, name):
        '''initialize an equip target with [name]'''
        name = name.capitalize()
        if name not in self._targets:
            '''obtain a new id and and register it under _targets'''
            self.name = name
            self.target_id = EquipTarget.next_id
            EquipTarget.next_id += 1
            self._targets[name] = self

    def __str__(self):
        '''Return target's name'''
        return self.name 

    def __eq__(self, value):
        '''Return self.target_id == other.target_id
        (if value is not an EquipTarget, returns False)
        '''
        try:
            return self.target_id == value.target_id
        except AttributeError:
            # other item is not an EquipTarget
            return False

    def __hash__(self):
        '''Return hash based on name and id'''
        return hash((self.name, self.target_id))

    def __repr__(self):
        '''Return repr(self)'''
        return "EffectTarget(%s)" % (self.name)

    @staticmethod
    def make_dict(*names):
        '''create an equip_dict containing EquipTargets generated
        from the list of names. An equip_dict in use might look like:
        {EquipTarget("Torso") : "Cuirass", EquipTarget("Feet") : "Boots"}
        '''
        equip_dict = {}
        for name in names:
            equip_dict[EquipTarget(name)] = None
        return equip_dict


class Usable(Item):
    def __init__(self, cls, bases, namespace):
        super().__init__(cls, bases, namespace)
        self.item_type = "Usable"
        if cls != "UsableBase": 
            #TODO: assert that target is an EquipTarget
            assert "use" in namespace or any([hasattr(base, "use") for base in bases])


class UsableBase(metaclass=Usable):
    '''Base class for all Usable items
    You must define your own "use" methods
    '''
    _description = "A usable item"

    @property
    def name(self):
        '''Creating a readonly "name" property'''
        return self._item_name

    def __str__(self):
        '''Return a string representing the object
        this will be how the item appears to the player'''
        return self._item_name
    
    def describe(self):
        ''' Describes the object '''
        return self._description

    def __eq__(self, other):
        '''Test if the other item is equivalent, based on
        the item_name and the item_type being the same
        '''
        try:
            return (self.name == other.name and
                    self.item_type == other.item_type)
        except:
            return False


class MiscItemBase(metaclass=Item):
    '''Base class for all MiscItems
    These items cannot be used, and will be typically
    used to store value (e.g. money, gold, building materials)
    '''
    _description = "A miscellaneous item"

    @property
    def name(self):
        '''Creating a readonly "name" property'''
        return self._item_name

    def __str__(self):
        '''Return a string representing the object
        this will be how the item appears to the player'''
        return self._item_name

    def __eq__(self, other):
        '''Test if the other item is equivalent, based on
        the item_name and the item_type being the same
        '''
        try:
            return (self.name == other.name and
                    self.item_type == other.item_type)
        except:
            return False

    def describe(self):
        '''Describes the item '''
        return self._description

#TODO: add a class wrapper that allows the item to function as a 
# singleton (even if this may not be pythonic)