'''module containing testcases for the inventory module'''
import unittest
import inventory as inv
from item import Usable, Equippable, EquipTarget, MiscItem

class SilverCoin(MiscItem):
    '''example of a Miscellaneous Item'''

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
        '''load Sword with [data]'''
        return cls(data["dmg"], data["material"])

    def save(self):
        '''provide a pythonic representation of this Sword'''
        return {
            "dmg": self.dmg,
            "material": self.material
        }


class TestItemStack(unittest.TestCase):

    def setUp(self):
        self.coin = SilverCoin()
        self.weak = HealthPotion(5)
        self.potion = HealthPotion(10)
        self.strong = HealthPotion(25)
        self.iron_sword = Sword(10, "iron")
        self.bronze_sword = Sword(5, "bronze")
        self.rare_sword = Sword(50, "iron")
        self.coin_stack = inv.ItemStack.from_item(self.coin, 100)
        self.weak_potions = inv.ItemStack.from_item(self.weak, 3)
        self.strong_potions = inv.ItemStack.from_item(self.strong, 234)
        self.rare_stack = inv.ItemStack.from_item(self.rare_sword, 1)
        self.sword_stack = inv.ItemStack.from_item(self.iron_sword, 3)

    def test_matching_subset(self):
        '''test the the matching_subset function works correctly'''
        main = {"a": 3, "b": 4, "c": 10}
        sub1 = {"a": 3, "c": 10}
        sub2 = {"a": 3, "foo": 5}
        sub3 = {"a": 0, "b": 1}
        self.assertTrue(inv.matching_subset(main, sub1))
        self.assertFalse(inv.matching_subset(main, sub2))
        self.assertFalse(inv.matching_subset(main, sub3))
        # if the subset is {}, then it should match all cases
        self.assertTrue(inv.matching_subset(main, {}))
        self.assertTrue(inv.matching_subset({}, {}))

    def test_repr(self):
        '''test that ItemStacks create a proper representation'''
        self.assertEqual(repr(self.coin_stack),
                         "ItemStack(SilverCoin, 100)")
        self.assertEqual(repr(self.weak_potions),
                         "ItemStack(HealthPotion, 3, {'hp': 5})")
        self.assertEqual(repr(self.strong_potions),
                         "ItemStack(HealthPotion, 234, {'hp': 25})")
        self.assertEqual(repr(self.rare_stack),
                         "ItemStack(Sword, 1, " +
                         "{'dmg': 50, 'material': 'iron'})")

    def test_eq(self):
        '''test that ItemStack equality works properly'''
        self.assertTrue(self.coin_stack != "meme")
        self.assertTrue(self.coin_stack == self.coin_stack)
        other_coins = inv.ItemStack.from_item(self.coin, 100)
        self.assertTrue(self.coin_stack is not other_coins)
        self.assertTrue(self.coin_stack == other_coins)
        other_potions = inv.ItemStack.from_item(self.weak, 3)
        self.assertTrue(self.weak_potions == other_potions)
        self.assertTrue(self.strong_potions != other_potions)
        other_potions.amount = 234
        self.assertTrue(self.weak_potions != other_potions)
        self.assertTrue(self.strong_potions != other_potions)


    def test_amount(self):
        '''test that the amount property works properly'''
        self.assertEqual(self.coin_stack.amount, 100)
        self.assertEqual(self.weak_potions.amount, 3)
        self.assertEqual(self.strong_potions.amount, 234)
        self.assertEqual(self.rare_stack.amount, 1)
        # test that setter works properly
        self.rare_stack.amount -= 1
        self.assertEqual(self.rare_stack.amount, 0)
        self.strong_potions.amount = 100
        self.assertEqual(self.strong_potions.amount, 100)
        # setter should raise ValueError if amount drops below 0
        with self.assertRaises(ValueError):
            self.rare_stack.amount -= 1
        with self.assertRaises(ValueError):
            self.strong_potions.amount = -100

    def test_matches(self):
        '''exhaustive test that ItemStack.matches method works properly'''
        # match with no parameters should return true
        self.assertTrue(self.coin_stack.matches())
        self.assertTrue(self.strong_potions.matches())
        self.assertTrue(self.weak_potions.matches())
        self.assertTrue(self.rare_stack.matches())

        # check type matching
        self.assertFalse(self.coin_stack.matches(HealthPotion))
        self.assertTrue(self.strong_potions.matches(HealthPotion))
        self.assertTrue(self.weak_potions.matches(HealthPotion))
        self.assertFalse(self.rare_stack.matches(HealthPotion))

        self.assertFalse(self.coin_stack.matches(Sword))
        self.assertFalse(self.strong_potions.matches(Sword))
        self.assertFalse(self.weak_potions.matches(Sword))
        self.assertTrue(self.rare_stack.matches(Sword))

        # check with exact data
        self.assertTrue(self.coin_stack.matches(exact_data={}))
        self.assertFalse(self.strong_potions.matches(exact_data={}))
        self.assertFalse(self.weak_potions.matches(exact_data={}))
        self.assertFalse(self.rare_stack.matches(exact_data={}))
        self.assertFalse(self.sword_stack.matches(exact_data={}))
        strong = {"hp": 25}
        self.assertFalse(self.coin_stack.matches(exact_data=strong))
        self.assertTrue(self.strong_potions.matches(exact_data=strong))
        self.assertFalse(self.weak_potions.matches(exact_data=strong))
        self.assertFalse(self.rare_stack.matches(exact_data=strong))
        self.assertFalse(self.sword_stack.matches(exact_data=strong))
        weak = {"hp": 5}
        self.assertFalse(self.coin_stack.matches(exact_data=weak))
        self.assertFalse(self.strong_potions.matches(exact_data=weak))
        self.assertTrue(self.weak_potions.matches(exact_data=weak))
        self.assertFalse(self.rare_stack.matches(exact_data=weak))
        self.assertFalse(self.sword_stack.matches(exact_data=weak))
        # only full match should work... this should match nothing
        almost = {"dmg": 10}
        self.assertFalse(self.coin_stack.matches(exact_data=almost))
        self.assertFalse(self.strong_potions.matches(exact_data=almost))
        self.assertFalse(self.weak_potions.matches(exact_data=almost))
        self.assertFalse(self.rare_stack.matches(exact_data=almost))
        self.assertFalse(self.sword_stack.matches(exact_data=almost))
        rare = {"dmg": 50, "material": "iron"}
        self.assertFalse(self.coin_stack.matches(exact_data=rare))
        self.assertFalse(self.strong_potions.matches(exact_data=rare))
        self.assertFalse(self.weak_potions.matches(exact_data=rare))
        self.assertTrue(self.rare_stack.matches(exact_data=rare))
        self.assertFalse(self.sword_stack.matches(exact_data=rare))

        # check the field match feature
        self.assertFalse(self.coin_stack.matches(hp=5))
        self.assertFalse(self.strong_potions.matches(hp=5))
        self.assertTrue(self.weak_potions.matches(hp=5))
        self.assertFalse(self.rare_stack.matches(hp=5))
        self.assertFalse(self.sword_stack.matches(hp=5))

        self.assertFalse(self.coin_stack.matches(material="iron"))
        self.assertFalse(self.strong_potions.matches(material="iron"))
        self.assertFalse(self.weak_potions.matches(material="iron"))
        self.assertTrue(self.rare_stack.matches(material="iron"))
        self.assertTrue(self.sword_stack.matches(material="iron"))

        self.assertFalse(self.coin_stack.matches(material="iron", dmg=10))
        self.assertFalse(self.strong_potions.matches(material="iron", dmg=10))
        self.assertFalse(self.weak_potions.matches(material="iron", dmg=10))
        self.assertFalse(self.rare_stack.matches(material="iron", dmg=10))
        self.assertTrue(self.sword_stack.matches(material="iron", dmg=10))

        self.assertFalse(self.coin_stack.matches(material="iron", hp=5))
        self.assertFalse(self.strong_potions.matches(material="iron", hp=5))
        self.assertFalse(self.weak_potions.matches(material="iron", hp=5))
        self.assertFalse(self.rare_stack.matches(material="iron", hp=5))
        self.assertFalse(self.sword_stack.matches(material="iron", hp=5))

        # now check features in combination
        self.assertFalse(self.coin_stack.matches(HealthPotion, hp=5))
        self.assertFalse(self.strong_potions.matches(HealthPotion, hp=5))
        self.assertTrue(self.weak_potions.matches(HealthPotion, hp=5))
        self.assertFalse(self.rare_stack.matches(HealthPotion, hp=5))
        self.assertFalse(self.sword_stack.matches(HealthPotion, hp=5))

        self.assertFalse(self.coin_stack.matches(Sword, hp=5))
        self.assertFalse(self.strong_potions.matches(Sword, hp=5))
        self.assertFalse(self.weak_potions.matches(Sword, hp=5))
        self.assertFalse(self.rare_stack.matches(Sword, hp=5))
        self.assertFalse(self.sword_stack.matches(Sword, hp=5))

        self.assertFalse(self.coin_stack.matches(Sword, exact_data=rare))
        self.assertFalse(self.strong_potions.matches(Sword, exact_data=rare))
        self.assertFalse(self.weak_potions.matches(Sword, exact_data=rare))
        self.assertTrue(self.rare_stack.matches(Sword, exact_data=rare))
        self.assertFalse(self.sword_stack.matches(Sword, exact_data=rare))

        self.assertFalse(self.coin_stack.matches(Sword, exact_data=rare,
                                                 material="iron"))
        self.assertFalse(self.strong_potions.matches(Sword, exact_data=rare,
                                                 material="iron"))
        self.assertFalse(self.weak_potions.matches(Sword, exact_data=rare,
                                                   material="iron"))
        self.assertTrue(self.rare_stack.matches(Sword, exact_data=rare,
                                                material="iron"))
        self.assertFalse(self.sword_stack.matches(Sword, exact_data=rare,
                                                  material="iron"))

        self.assertFalse(self.coin_stack.matches(Sword, exact_data=strong,
                                                 material="iron"))
        self.assertFalse(self.strong_potions.matches(Sword, exact_data=strong,
                                                     material="iron"))
        self.assertFalse(self.weak_potions.matches(Sword, exact_data=strong,
                                                   material="iron"))
        self.assertFalse(self.rare_stack.matches(Sword, exact_data=strong,
                                                 material="iron"))
        self.assertFalse(self.sword_stack.matches(Sword, exact_data=strong,
                                                  material="iron"))

    def test_get_item(self):
        coin = self.coin_stack.copy()
        self.assertTrue(isinstance(coin, SilverCoin))
        self.assertFalse(coin is self.coin)

        sword = self.rare_stack.copy()
        self.assertTrue(isinstance(sword, Sword))
        self.assertEqual(sword.material, self.rare_sword.material)
        self.assertEqual(sword.dmg, self.rare_sword.dmg)

class TestInventory:
    '''test case for the inventory class'''

