'''defining the inventory module'''

#TODO: make internal implementation faster and more elegant
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