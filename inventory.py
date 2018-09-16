class Inventory:
    def __init__(self): 
        self._items = {}

    def add_item(self, item, quantity=1):
        '''adds an [item] of [quantity] to this inventory
        default quantity = 1
        '''
        print(item)
        print(type(type(item)))
        item_type = type(type(item))
        if item_type not in self._items:
            self._items[item_type] = {}
        if item not in self._items[item_type]:
            self._items[item_type][item] = quantity
        else:
            self._items[item_type][item] += quantity

    def remove_item(self, item, quantity=1):
        '''removes an [item] of [quantity] to this inventory
        raises KeyError if item not found
        raises an ArithmeticError if item is found, but [quantity] > item quanity 
        '''
        item_type = type(type(item))
        if item_type not in self._items:
            raise KeyError("Item %s not found" % item)
        if item not in self._items[item_type]:
            raise KeyError("Item %s not found" % item)
        if self._items[item_type][item] < quantity:
            raise ArithmeticError("Item quantity less than provided")
        self._items[item_type][item] -= quantity
        if self._items[item_type][item] == 0:
            del self._items[item_type][item]
        if len(self._items[item_type]) == 0:
            del self._items[item_type]

    def get_item(self, name):
        results = []
        for item in self:
            if item == name:
                results.append(item)
        return results

    def readable(self):
        output = ""
        for item_type in self._items:
            output += item_type.__name__ + "\n"
            for item, quantity in self._items[item_type].items():
                output += "\t%s: %s\n" % (item, quantity)
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
        for item_type in self._items:
            for item in self._items[item_type]:
                yield item

    def __repr__(self):
        return self._items.__repr__()
    
    def __contains__(self, item):
        if type(type(item)) in self._items:
            return item in self._items[type(type(item))]
        return False
