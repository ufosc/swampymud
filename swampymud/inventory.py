"""this module contains the Inventory, the class for storing all items,
and ItemStack, a class for efficiently storing items of the same type
"""
from collections import defaultdict

def matching_subset(main, sub):
    """check that all the keys in a dictionary are in sub and agree with main
    Example:
        main = {"a": 3, "b": 4, "c": 10}
        sub1 = {"a": 3, "c": 10}
        sub2 = {"a": 3, "foo": 5}
        sub3 = {"a": 0, "b": 1}
    sub1 is a "matching subset" of main since all its keys match with main
    sub2 is not a "matching subset" of main since the field "foo" is not in main
    sub3 is not a "matching subset" since sub3["a"] = 0 but main["a"] == 3
    """
    # check that all keys of sub are in main
    main_keys = set(main)
    sub_keys = set(sub)
    if not sub_keys.issubset(main_keys):
        return False
    # check that all values of sub match with main
    for key in sub_keys:
        if main[key] != sub[key]:
            return False
    return True


class ItemStack:
    def __init__(self, item_type, amount, data=None):
        """create a new ItemStack with Item class [item_type], integer [amount]
        Optionally, you can provide [data], where [data] is compatible with the .load
        method provided by [item_type]
        """
        # for sake of memory, store None instead of empty dict
        if data == {}:
            data = None
        self._type = item_type
        self._amount = amount
        self._data = data

    @property
    def amount(self):
        """returns amount of items in this stack"""
        return self._amount

    @amount.setter
    def amount(self, new_amt):
        """set the amount of items in this stack to ["""
        if not isinstance(new_amt, int):
            raise TypeError("Problem setting ItemStack amount: expected"
                            f" type int, received {type(new_amt)}")
        if new_amt < 0:
            raise ValueError("Problem setting ItemStack amount: expected non-"
                             f"-negative value, received {new_amt}")
        else:
            self._amount = new_amt

    def __repr__(self):
        if self._data:
            return (f"ItemStack({self._type.__name__}, {self._amount},"
                    f" {self._data})")
        return f"ItemStack({self._type.__name__}, {self._amount})"

    # this makes ItemStacks unhashable
    # however, since ItemStacks are mutable, they should be unhashable
    def __eq__(self, other_stack):
        """overriding =="""
        try:
            return (self._type == other_stack._type and
                    self.amount == other_stack.amount and
                    self._data == other_stack._data)
        # if the other_stack isn't really an ItemStack
        except AttributeError:
            return False

    def matches(self, item_type=None, exact_data=None, **fields):
        """check that [item_type] and data agree with both arguments are optional"""
        if item_type is not None and self._type is not item_type:
            return False
        if exact_data is not None and exact_data != self._data:
            # edge case: this ItemStack has no data and exact_data is {}
            # in this case exact_data are not equal but have same meaning
            if self._data is not None or exact_data != {}:
                return False
        # check any remaining fields and return the result
        # edge case: self._data is None but fields are provided
        if self._data is None:
            return fields == {}
        return matching_subset(self._data, fields)

    def copy(self):
        """returns a copy of an item stored in the stack"""
        item = self._type.load(self._data)
        item.post_load(self._data)
        return item

    @staticmethod
    def from_item(item, amount=1):
        """create an ItemStack from an existing item"""
        return ItemStack(type(item), amount, item.save())

    @staticmethod
    def load(data):
        """load an ItemStack from a Pythonic representation"""
        return ItemStack(**data)

    def save(self):
        """save a Pythonic representation of this ItemStack"""
        stack = {
            "_type": ItemStack,
            "item_type": self._type,
            "amount": self.amount
        }
        if self._data:
            stack["data"] = self._data.copy()
        return stack


# make the common case fast
# this structure is optimized for name-based lookups
class Inventory:
    """data structure for storing stacks of in-game objects
    often accessed using a name"""

    def __init__(self, *items):
        self._items = defaultdict(list)
        for (item, amt) in items:
            self.add_item(item, amt)

    def __repr__(self):
        return "Inventory(%s)" % (", ".join(map(repr, self)))

    def __bool__(self):
        """returns True if the inventory contains any items"""
        for _ in self:
            return True
        return False

    def add_item(self, item, amount=1):
        """add [quantity] of [item] to this inventory
        raises ValueError if quantity < 1"""
        if not isinstance(amount, int) or amount < 1:
            raise ValueError("Expected integer quantity > 0, received %s"
                             % amount)
        name = str(item).lower()
        item_type = type(item)
        data = item.save()
        for stack in self._items[name]:
            if stack.matches(item_type, data):
                stack.amount += amount
                break
        # otherwise, create a new stack
        else:
            new_stack = ItemStack(item_type, amount, data)
            self._items[name].append(new_stack)

    def remove_item(self, item, amount=1):
        """remove [item] from this dictionary
        raises KeyError if item is not found"""
        name = str(item).lower()
        item_type = type(item)
        item_data = item.save()
        # raise an error if the key is not found
        # this is to avoid creating an empty list at that key
        if name not in self._items:
            raise KeyError("Item not found in inventory: %r" % item)
        # check all the stacks in the bucket
        for index, stack in enumerate(self._items[name]):
            if stack.matches(item_type, item_data):
                # item found, remove [amount] of items
                stack.amount -= amount
                # if the stack is empty, remove it from the bucket
                if stack.amount == 0:
                    del self._items[name][index]
                break
        # if nothing was found, raise an error
        else:
            raise KeyError("Item not found in inventory: %r" % item)
        # if the bucket is empty, remove it from the dictionary
        if not self._items[name]:
            del self._items[name]

    def find(self, name=None, cls=None, exact_data=None, **other_fields):
        if name:
            name = name.lower()
            # if name provided, get the corresponding bucket
            if name in self._items:
                for stack in self._items[name]:
                    if stack.matches(cls, exact_data, **other_fields):
                        yield stack.copy(), stack.amount
        else:
            # if not, search through every bucket
            for name, bucket in self._items.items():
                for stack in bucket:
                    if stack.matches(cls, exact_data, **other_fields):
                        yield stack.copy(), stack.amount

    def __iter__(self):
        """iterate over each Item, Amount pair in the list"""
        for bucket in self._items.values():
            for stack in bucket:
                yield stack.copy(), stack.amount

    def stacks(self):
        """iterate directly over the stacks of this list"""
        for bucket in self._items.values():
            for stack in bucket:
                yield stack

    # this makes inventories unhashable
    # but this is ok, because inventories are mutable
    def __eq__(self, other):
        """overriding =="""
        try:
            # first check that the keys are the same
            if set(self._items) != set(other._items):
                return False
            for item_name, self_bucket in self._items.items():
                other_bucket = other._items[item_name]
                if len(other_bucket) != len(self_bucket):
                    return False
                # TODO: make this not quadratic
                # consider adding hash method to ItemStack
                for self_stack in self_bucket:
                    for other_stack in other_bucket:
                        if self_stack == other_stack:
                            break
                    # if no matching stack is found, return False
                    else:
                        return False
            return True
        except AttributeError:
            return False

    def readable(self):
        """returns a string representation of this inventory"""
        # get a tuple list of form (item_name, amount)
        #TODO: call another method other than 'string' to better represent object?
        items = list(map(lambda x: f"{x[0]}: {x[1]}", self))
        # sort by name
        items.sort(key=lambda x: x[0])
        return "\n".join(items)


class EquipTarget:
    '''Class for identifying specific slots that an equippable item
    may be equipped to. In some sense, this acts as a second inventory.
    Each CharacterClass has a field, 'equip_slots', that specifies what
    types of items they can equip.'''
    # next id to be used
    _next_id = 0
    # all targets mapped by name
    _targets = {}

    def __new__(cls, name: str):
        '''Create a new EquipTarget'''
        name = name.capitalize()
        # if the target name has already been registered,
        # return the existing object
        # this is done to save memory
        if name in cls._targets:
            return cls._targets[name]
        return super().__new__(cls)

    def __init__(self, name: str):
        '''initialize an equip target with [name]'''
        name = name.capitalize()
        if name not in self._targets:
            '''obtain a new id and and register it under _targets'''
            self._name = name
            self._target_id = EquipTarget._next_id
            EquipTarget._next_id += 1
            self._targets[name] = self

    def __str__(self):
        '''Return target's name'''
        return self._name

    def __hash__(self):
        '''Return hash based on name and id'''
        return hash((self._name, self._target_id))

    def __repr__(self):
        '''Return repr(self)'''
        return "EquipTarget({!r})".format(self._name)

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
