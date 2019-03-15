'''
This module provides several base classes for items
Every item must provide a use() method.
This will be invoked when a user types "use [item name] ..."
It is up to the item to correctly

There are 3 major item families:
Equipables:
    Things that have an equip() and an unequip() method.
    Upon equip, they are bound to a character, and must be unequipped.
    
Consumables:
    Things that have a consume() method.
    Upon consume, they are removed from the inventory, and incur some
        effect to the player specifically.
Throwables:
    Things that have a throw() method.
    These items are consumed upon use, and a target must be specified.
'''
from util import camel_to_space

class Item(type):
    '''The metaclass establishing behavior for all items'''
    def __init__(self, cls, bases, dic):
        if "item_name" not in dic:
            self.item_name = camel_to_space(cls)
        if "item_type" not in dic:
            self.item_type = "Item"
        super().__init__(cls, bases, dic)


class Equippable(Item):
    def __init__(self, cls, bases, dic):
        super().__init__(cls, bases, dic)
        self.item_type = "Equippable"
        if cls != "EquippableBase": 
            assert "target" in dic or any([hasattr(base, "target") for base in bases])
            assert "equip" in dic or any([hasattr(base, "equip") for base in bases])
            assert "unequip" in dic or any([hasattr(base, "unequip") for base in bases])


class EquippableBase(metaclass=Equippable):
    def __str__(self):
        return self.item_name
    
    def __eq__(self, other):
        if type(other) is str:
            return self.item_name.lower() == item_name.lower()
        elif type(other) is type(self):
            return hash(self) == hash(other)
        return False 

    def __hash__(self):
        return hash((self.__class__, self.name))

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
            return self.target_id == other.target_id
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
        '''returns a dictionary mapping each name in [names] to an 
        EquipTarget with that name'''
        equip_dict = {}
        for name in names:
            equip_dict[EquipTarget(name)] = None
        return equip_dict


class Consumable(Item):
    def __init__(self, cls, bases, dic):
        super().__init__(cls, bases, dic)
        self.item_type = "Item"
        if cls != "ConsumableBase": 
            assert "target" in dic or any([hasattr(base, "target") for base in bases])
            assert "consume" in dic or any([hasattr(base, "consume") for base in bases])


class ConsumableBase(metaclass=Consumable):
    def use(self, character, *args):
        self.consume(self, character, *args)

    def __str__(self):
        return self.name
    
    def __eq__(self, other):
        if type(other) is str:
            return self.name.lower() == other.lower()
        elif type(other) is type(self):
            return hash(self) == hash(other)
        return False 

    def __hash__(self):
        return hash((self.__class__, self.name))


class Throwable(Item):
    def __init__(self, cls, bases, dic):
        super().__init__(cls, bases, dic)
        self.item_type = "Item"
        if cls != "ThrowableBase":
            assert "target" in dic or any([hasattr(base, "target") for base in bases])
            assert "throw" in dic or any([hasattr(base, "throw") for base in bases])


class ThrowableBase(metaclass=Throwable):
    def __str__(self):
        return self.name
    
    def __eq__(self, other):
        if type(other) is str:
            return self.name.lower() == other.lower()
        elif type(other) is type(self):
            return hash(self) == hash(other)
        return False

    def __hash__(self):
        return hash((self.__class__, self.name))