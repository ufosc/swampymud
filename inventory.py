class Inventory:
    def __init__(self):  
        self._items = {}

    def add_item(self, item, quantity=1):
        '''adds an [item] of [quantity] to this inventory
        default quantity = 1
        '''
        if item not in self._items:
            self._items[item] = quantity
        else:
            self._items[item] += quantity

    def remove_item(self, item, quantity=1):
        if item not in self._items:
            raise Exception("Item %s not found" % item)
        if self._items[item] < quantity:
            raise Exception("Item quantity less than provided")
        self._items[item] -= quantity
        if self._items[item] == 0:
            del self._items[item]

    def __iadd__(self, item):
        self.add_item(item)
        return self
    
    def __isub__(self, item):
        self.remove_item(item)
        return self

wilson_inv = Inventory()
wilson_inv.add_item("popcorn")
wilson_inv.add_item("popcorn")
wilson_inv.add_item("popcorn", 5)
print(wilson_inv._items)

wilson_inv += "flamethrower"
print(wilson_inv._items)

wilson_inv -= "popcorn"
print(wilson_inv._items)