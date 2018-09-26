'''
This module provides several base classes for items
Every item must provide a use() method. 
This will be invoked when a user types \"use [item name] ...\"
It is up to the item to correctly 

There are 3 major item families:
Equipables - things that have an equip() method. Upon equip, they are bound to a character, and must be unequipped.
Consumables - things that have a consume() method. Upon consume, they are removed from the inventory, and incur some effect to the player specifically.
Throwables - things that have a "throw" method. These items are consumed upon use, and a target must be specified. 
'''

class Item(type):
    '''The metaclass establishing behavior for all items'''
    
    def __init__(self, cls, bases, dict):
        if "name" not in dict:
            self.name = cls
        # detect if an item has any use method
        assert "use" in dict or any([hasattr(base, "use") for base in bases])
        self.item_type = "Item"
        super().__init__(cls, bases, dict)

    def __str__(self):
        return self.name


class Equippable(Item):
    def __init__(self, cls, bases, dict):
        super().__init__(cls, bases, dict)
        self.item_type = "Equippable"
        if cls != "EquippableBase": 
            assert "target" in dict or any([hasattr(base, "target") for base in bases])
            assert "equip" in dict or any([hasattr(base, "equip") for base in bases])
            assert "unequip" in dict or any([hasattr(base, "unequip") for base in bases])


#TODO: make it so that metaclass automatically detects KEY attributes
class EquippableBase(metaclass=Equippable):
    def __init__(self):
        self.is_equipped = False
        
    def use(self, character, *args):
        self.equip(self, character, *args)

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

class EquipTarget:
    next_id = 0
    _target_list = []
    def __init__(self, name):
        if name.lower() in self._target_list:
            self.target_id = self._target_list.index(name.lower())
        else:
            self.target_id = EquipTarget.next_id
            EquipTarget.next_id += 1
            self._target_list.append(name.lower())
        self.name = name

    @staticmethod
    def make_dict(*names):
        #TODO: make support for default items?
        equip_dict = {}
        for name in names:
            equip_dict[EquipTarget(name)] = None
        return equip_dict

    def __str__(self):
        return self.name 

    def __eq__(self, other):
        try:
            return self.target_id == other.target_id
        except AttributeError:
            # other item is not an EquipTarget
            return False
    
    def __hash__(self):
        return self.target_id
    
    def __repr__(self):
        return str(self) + "[%s]" % self.target_id 

class Consumable(Item):
    def __init__(self, cls, bases, dict):
        super().__init__(cls, bases, dict)
        self.item_type = "Item"
        if cls != "ConsumableBase": 
            assert "target" in dict or any([hasattr(base, "target") for base in bases])
            assert "consume" in dict or any([hasattr(base, "consume") for base in bases])

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

# this is highly repetive. Should we make a metaclass for the metaclass?

class Throwable(Item):
    def __init__(self, cls, bases, dict):
        super().__init__(cls, bases, dict)
        self.item_type = "Item"
        if cls != "ThrowableBase": 
            assert "target" in dict or any([hasattr(base, "target") for base in bases])
            assert "throw" in dict or any([hasattr(base, "throw") for base in bases])

class ThrowableBase(metaclass=Throwable):
    def use(self, character, *args):
        self.throw(self, character, sender, *args)

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
