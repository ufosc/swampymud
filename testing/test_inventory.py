'''module containing testcases for the inventory module'''
import unittest
import inventory as inv
from item import Usable, Equippable, EquipTarget, MiscItem

class SilverCoin(MiscItem):
    pass

# some testing classes for items
class HealthPotion(Usable):
    def __init__(self, hp):
        self.hp = hp

    def use(self, char):
        pass

    @classmethod
    def load(cls, data):
        cls(data["hp"])
    
    def save(self):
        return {"hp": self.hp}


class Sword(Equippable):
    target = EquipTarget("hand")
    
    def __init__(self, dmg, material):
        self.dmg = dmg
        self.material = material

    def equip(self, char):
        pass
    
    def unequip(self, char):
        pass
    
    @classmethod
    def load(cls, data):
        cls(data["dmg"], data["material"])
    
    def save(self):
        return {
            "dmg": self.dmg,
            "material": self.material
        }


class TestItemStack(unittest.TestCase):

    def test_matching_subset(self):
        '''test the the matching_subset function works correctly'''
        main = {"a": 3, "b": 4, "c": 10}
        sub1 = {"a": 3, "c": 10}
        sub2 = {"a": 3, "foo": 5}
        sub3 = {"a": 0, "b": 1}
        empty = {}

        self.assertTrue(inv.matching_subset(main, sub1))
        self.assertFalse(inv.matching_subset(main, sub2))
        self.assertFalse(inv.matching_subset(main, sub3))
        # if the subset is {}, then it should match all cases
        self.assertTrue(inv.matching_subset(main, {}))
        self.assertTrue(inv.matching_subset({}, {}))
    
    def test_repr(self):
        '''test that ItemStacks create a proper representation'''