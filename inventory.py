'''this module contains the Inventory, the class for storing all items,
and ItemStack, a class for efficiently storing items of the same type
'''
from collections import defaultdict

def matching_subset(main, sub):
    '''check that all the keys in a dictionary are in sub and agree with main
Example:
    main = {"a": 3, "b": 4, "c": 10}
    sub1 = {"a": 3, "c": 10}
    sub2 = {"a": 3, "foo": 5}
    sub3 = {"a": 0, "b": 1}
sub1 is a "matching subset" of main since all its keys match with main
sub2 is not a "matching subset" of main since the field "foo" is not in main
sub3 is not a "matching subset" since sub3["a"] = 0 but main["a"] == 3
'''
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
    def __init__(self, item, amount):
        '''create a new ItemStack with Item class [item_type], integer [amount]
Optionally, you can provide [data], where [data] is compatible with the .load
method provided by [item_type]
'''
        # for sake of memory, store None instead of empty dict
        data = item.save()
        if data == {}:
            data = None
        self._type = type(item)
        self._amount = amount
        self._data = data
        self._item = item

    @property
    def amount(self):
        '''returns amount of items in this stack'''
        return self._amount

    @amount.setter
    def amount(self, new_amt):
        '''set the amount of items in this stack to ['''
        if not isinstance(new_amt, int):
            raise TypeError("Problem setting ItemStack amount:\
                              expected type int, received %s" % type(new_amt))
        if new_amt < 0:
            raise ValueError("Problem setting ItemStack amount:\
                              expected non-negative value, received %s"
                              % type(new_amt))
        else:
            self._amount = new_amt

    def __repr__(self):
        if self._data:
            return "ItemStack(%s, %s, %s)" % (self._type.__name__,
                                              self._amount, self._data)
        return "ItemStack(%s, %s)" % (self._type.__name__, self._amount)
    
    def matches(self, item_type=None, exact_data=None, **fields):
        '''check that [item_type] and data agree with both arguments are optional'''
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


# make the common case fast
# this structure is optimized for name-based lookups
class Inventory:
    def __init__(self):
        self._items = defaultdict(list)
    
    def add_item(self, item, quantity=1):
        '''add [quantity] of [item] to this inventory
raises ValueError if quantity < 1'''
        if not isinstance(quantity, int) or quantity < 1:
            raise ValueError("Expected integer quantity > 0, received %s"
                             % quantity)
        name = str(item)
        for stack in self._items[name]:
            if stack.matches(type(item), item_data):
                stack.amount += quantity
                break
        # otherwise, create a new stack
        else:
            new_stack = ItemStack(item, quantity)
            self._items[name].append(new_stack)
    
    def remove_item(self, item):
        '''remove [item] from this dictionary
raises ValueError if item is not found'''
        name = str(item)
        item_type = type(item)
        item_data = item.save()
        for stack in self._items[item]:
            if stack.matches(item_type, item_data):
                stack.amount -= 1
                break
        # if nothing was found, raise an error
        else:
            raise ValueError("Item not found in inventory: %r" % item)
        # if stack is empty, remove it from the list
        if stack.amount == 0:
            self._items[item].remove(stack)


    def find(self, name=None, cls=None, exact_data=None, **other_fields):
        if name:
            # if name provided, get the corresponding bucket
            if name in self._items:
                for stack in self._items[name]:
                    if stack.matches(cls, exact_data, other_fields):
                        yield tuple(stack)
        else:
            # if not, search through every bucket
            for name, bucket in self._items.items():
                for stack in bucket:
                    pass


class Inventory:
    '''Inventory for containing items, stacking by quantity
    all items are stored in _items, which follows this layout
    {
        item_type : { item_key : quantity }
    }
    '''
    def __init__(self, *items): 
        self._items = {}
        for item in items:
            self.add_item(item)

    def add_item(self, item, quantity=1):
        '''adds an [item] of [quantity] to this inventory
        default quantity = 1
        '''
        item_type = item.item_type
        name = item.name
        if item_type not in self._items:
            self._items[item_type] = {}
        if name not in self._items[item.item_type]:
            self._items[item_type][name] = [item] * quantity
        else:
            self._items[item_type][name] += [item] * quantity

    def remove_item(self, item, quantity=1):
        '''removes an [item] of [quantity] to this inventory
        raises KeyError if item not found
        raises an ArithmeticError if item is found, but [quantity] > item quanity
        '''
        item_type = item.item_type
        name = item.name
        if item_type not in self._items:
            raise KeyError("Item %s not found" % item)
        if name not in self._items[item_type]:
            raise KeyError("Item %s not found" % item)
        if len(self._items[item_type][name]) < quantity:
            raise ArithmeticError("Attempted to remove too many items")
        self._items[item_type][name]
        del self._items[item_type][name][-quantity:]
        if not self._items[item_type][name]:
            del self._items[item_type][name]
        if not self._items[item_type]:
            del self._items[item_type]
        return item

    def find(self, name):
        '''Return all items with a matching name'''
        for name_list in self._items.values():
            for item_name, item_list in name_list.items():
                if name.lower() == item_name.lower():
                    return item_list[-1]

    def readable(self):
        output = ""
        for item_type in self._items:
            output += item_type + "\n"
            for item, lst in self._items[item_type].items():
                output += "\t%s: %s\n" % (item, len(lst))
        return output

    def __iadd__(self, item):
        '''overloading += with add_item'''
        self.add_item(item)
        return self

    def __isub__(self, item):
        '''overloading -= with remove_item'''
        self.remove_item(item)
        return self

    def __iter__(self):
        '''iterate over item in _items'''
        for name_dict in self._items.values():
            for item_list in name_dict.values():
                for item in item_list:
                    yield item

    def __repr__(self):
        return "Inventory(%s)" % " ,".join(map(repr,self))

    def __contains__(self, item):
        if type(type(item)) in self._items:
            return item in self._items[type(type(item))]
        return False