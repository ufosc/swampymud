"""module containing testcases for the inventory module"""
import unittest
import swampymud.inventory as inv
from swampymud.item import Usable, Equippable, Item
from swampymud.util import FindParams

class SilverCoin(Item):
    """example of a Miscellaneous Item"""
    def __repr__(self):
        return "SilverCoin()"

# some testing classes for items
class HealthPotion(Item):
    def __init__(self, hp):
        self.hp = hp

    def on_use(self, char, args):
        pass

    @classmethod
    def load(types, data):
        return types(data["hp"])

    def save(self):
        return {"hp": self.hp}

    def __repr__(self):
        return "HealthPotion(%s)" % self.hp

class BadPoison(Item):
    def __init__(self, dmg):
        self.dmg = dmg

    def on_use(self, char, args):
        pass

    @classmethod
    def load(types, data):
        return types(data["dmg"])

    def save(self):
        return {"dmg": self.dmg}

    def __repr__(self):
        return "BadPoison(%s)" % self.dmg

class Sword(Equippable):
    target = inv.EquipTarget("hand")

    def __init__(self, dmg, material):
        self.dmg = dmg
        self.material = material

    def equip(self, char):
        pass

    def unequip(self, char):
        pass

    @classmethod
    def load(types, data):
        """load Sword with [data]"""
        return types(data["dmg"], data["material"])

    def save(self):
        """provide a pythonic representation of this Sword"""
        return {
            "dmg": self.dmg,
            "material": self.material
        }

    def __repr__(self):
        return "Sword(%s, %r)" % (self.dmg, self.material)


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
        """test the the matching_subset function works correctly"""
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
        """test that ItemStacks create a proper representation"""
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
        """test that ItemStack equality works properly"""
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
        """test that the amount property works properly"""
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
        """exhaustive test that ItemStack.matches method works properly"""
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
        self.assertTrue(self.coin_stack.matches(exact={}))
        self.assertFalse(self.strong_potions.matches(exact={}))
        self.assertFalse(self.weak_potions.matches(exact={}))
        self.assertFalse(self.rare_stack.matches(exact={}))
        self.assertFalse(self.sword_stack.matches(exact={}))
        strong = {"hp": 25}
        self.assertFalse(self.coin_stack.matches(exact=strong))
        self.assertTrue(self.strong_potions.matches(exact=strong))
        self.assertFalse(self.weak_potions.matches(exact=strong))
        self.assertFalse(self.rare_stack.matches(exact=strong))
        self.assertFalse(self.sword_stack.matches(exact=strong))
        weak = {"hp": 5}
        self.assertFalse(self.coin_stack.matches(exact=weak))
        self.assertFalse(self.strong_potions.matches(exact=weak))
        self.assertTrue(self.weak_potions.matches(exact=weak))
        self.assertFalse(self.rare_stack.matches(exact=weak))
        self.assertFalse(self.sword_stack.matches(exact=weak))
        # only a 'full match' should work... this should match nothing
        almost = {"dmg": 10}
        self.assertFalse(self.coin_stack.matches(exact=almost))
        self.assertFalse(self.strong_potions.matches(exact=almost))
        self.assertFalse(self.weak_potions.matches(exact=almost))
        self.assertFalse(self.rare_stack.matches(exact=almost))
        self.assertFalse(self.sword_stack.matches(exact=almost))
        rare = {"dmg": 50, "material": "iron"}
        self.assertFalse(self.coin_stack.matches(exact=rare))
        self.assertFalse(self.strong_potions.matches(exact=rare))
        self.assertFalse(self.weak_potions.matches(exact=rare))
        self.assertTrue(self.rare_stack.matches(exact=rare))
        self.assertFalse(self.sword_stack.matches(exact=rare))

        # check the must_have feature
        # this works because coin stack doesn't have an hp field
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

        self.assertFalse(self.coin_stack.matches(Sword, exact=rare))
        self.assertFalse(self.strong_potions.matches(Sword, exact=rare))
        self.assertFalse(self.weak_potions.matches(Sword, exact=rare))
        self.assertTrue(self.rare_stack.matches(Sword, exact=rare))
        self.assertFalse(self.sword_stack.matches(Sword, exact=rare))

        self.assertFalse(self.coin_stack.matches(Sword, exact=rare,
                                                 material="iron"))
        self.assertFalse(self.strong_potions.matches(Sword, exact=rare,
                                                 material="iron"))
        self.assertFalse(self.weak_potions.matches(Sword, exact=rare,
                                                   material="iron"))
        self.assertTrue(self.rare_stack.matches(Sword, exact=rare,
                                                material="iron"))
        self.assertFalse(self.sword_stack.matches(Sword, exact=rare,
                                                  material="iron"))

        self.assertFalse(self.coin_stack.matches(Sword, exact=strong,
                                                 material="iron"))
        self.assertFalse(self.strong_potions.matches(Sword, exact=strong,
                                                     material="iron"))
        self.assertFalse(self.weak_potions.matches(Sword, exact=strong,
                                                   material="iron"))
        self.assertFalse(self.rare_stack.matches(Sword, exact=strong,
                                                 material="iron"))
        self.assertFalse(self.sword_stack.matches(Sword, exact=strong,
                                                  material="iron"))

        # however, optional should match even if all fields aren't provided
        # this works because coin stack doesn't have an hp field
        self.assertTrue(self.coin_stack.matches(optional={"hp": 5}))
        self.assertTrue(self.coin_stack.matches(optional=almost))
        self.assertTrue(self.strong_potions.matches(optional=almost))
        self.assertTrue(self.weak_potions.matches(optional=almost))
        self.assertFalse(self.rare_stack.matches(optional=almost)) # dmg is 50
        self.assertTrue(self.sword_stack.matches(optional=almost))

    def test_get_item(self):
        coin = self.coin_stack.copy()
        self.assertTrue(isinstance(coin, SilverCoin))
        self.assertFalse(coin is self.coin)

        sword = self.rare_stack.copy()
        self.assertTrue(isinstance(sword, Sword))
        self.assertEqual(sword.material, self.rare_sword.material)
        self.assertEqual(sword.dmg, self.rare_sword.dmg)

class TestInventory(unittest.TestCase):
    """test case for the inventory class"""

    def setUp(self):
        self.empty = inv.Inventory()
        self.coins = inv.Inventory(
            (SilverCoin(), 10)
        )
        self.rich = inv.Inventory(
            (SilverCoin(), 15),
            (HealthPotion(10), 5),
            (Sword(15, "steel"), 2)
        )
        self.potion_seller = inv.Inventory(
            (SilverCoin(), 20),
            (HealthPotion(hp=10), 5),
            (HealthPotion(hp=3), 7),
            (HealthPotion(hp=100), 2),
            (HealthPotion(hp=50), 3)
        )

    def test_repr(self):
        """testing the __repr__ method"""
        self.assertEqual(repr(self.empty), 'Inventory()')
        self.assertEqual(repr(self.coins), 'Inventory((SilverCoin(), 10))')
        expected = "Inventory((SilverCoin(), 15), (HealthPotion(10), 5), (Sword(15, 'steel'), 2))"
        self.assertEqual(repr(self.rich), expected)

    def test_bool(self):
        """testing the __bool__ method"""
        self.assertFalse(bool(self.empty))
        self.assertTrue(bool(self.coins))
        self.assertTrue(bool(self.rich))
        self.assertTrue(bool(self.potion_seller))

        # create a dumb, destructive function to count items with bool
        def count_items(inventory):
            count = 0
            while inventory:
                count += 1
                try:
                    item, amount = tuple(inventory.find_child(FindParams()))[0]
                except TypeError:
                    continue
                inventory.remove_item(item, amount)
            return count

        self.assertEqual(count_items(self.empty), 0)
        self.assertEqual(count_items(self.coins), 1)
        self.assertEqual(count_items(self.rich), 3)
        self.assertEqual(count_items(self.potion_seller), 5)

    def test_eq(self):
        """testing the __eq__ method (mostly used for testing)"""
        # test equality with an empty list
        self.assertTrue(self.empty is not inv.Inventory())
        self.assertTrue(self.empty == inv.Inventory())
        self.assertTrue(inv.Inventory() == self.empty)
        # test with object of wrong type
        self.assertTrue(self.empty != "oops wrong type")
        # test with filled inventories
        other = inv.Inventory((SilverCoin(), 10))
        self.assertTrue(other is not self.coins)
        self.assertTrue(self.coins == other)
        rich = inv.Inventory(
            (HealthPotion(10), 5),
            (SilverCoin(), 15),
            (Sword(15, "steel"), 2)
        )
        self.assertTrue(rich is not self.rich)
        self.assertTrue(rich == self.rich)
        self.assertTrue(self.rich != self.coins)

    def test_add_item(self):
        """test that the add_item property works correctly"""
        coin_inv = inv.Inventory()
        self.assertEqual(coin_inv, self.empty)
        coin_inv.add_item(SilverCoin(), 7)
        self.assertTrue(coin_inv != self.coins)
        self.assertEqual(coin_inv, inv.Inventory((SilverCoin(), 7)))
        coin_inv.add_item(SilverCoin(), 3)
        self.assertEqual(coin_inv, self.coins)
        coin_inv.add_item(HealthPotion(3), 1)
        coin_inv.add_item(SilverCoin(), 10)
        self.assertTrue(coin_inv != self.coins)
        # test that items are always put into correct buckets
        # regardless of time of insert
        coin_inv.add_item(HealthPotion(50), 3)
        coin_inv.add_item(HealthPotion(10), 4)
        coin_inv.add_item(HealthPotion(100))
        coin_inv.add_item(HealthPotion(3), 2)
        coin_inv.add_item(HealthPotion(10), 1)
        coin_inv.add_item(HealthPotion(3), 2)
        coin_inv.add_item(HealthPotion(3), 2)
        coin_inv.add_item(HealthPotion(100))
        self.assertEqual(coin_inv, self.potion_seller)
        # check that the 'Health Potion' bucket is correct
        bucket = coin_inv._items["health potion"]
        self.assertEqual(len(bucket), 4)
        self.assertTrue(inv.ItemStack(HealthPotion, 7, {"hp":3}) in bucket)
        self.assertTrue(inv.ItemStack(HealthPotion, 5, {"hp":10}) in bucket)
        self.assertTrue(inv.ItemStack(HealthPotion, 3, {"hp":50}) in bucket)
        self.assertTrue(inv.ItemStack(HealthPotion, 2, {"hp":100}) in bucket)
        #TODO: add some tests with the sword

    def test_remove_item(self):
        """test that removing an item works"""
        with self.assertRaises(KeyError):
            self.empty.remove_item(SilverCoin())
        self.coins.remove_item(SilverCoin())
        self.assertEqual(self.coins, inv.Inventory((SilverCoin(), 9)))
        self.coins.remove_item(SilverCoin(), 3)
        self.assertEqual(self.coins, inv.Inventory((SilverCoin(), 6)))
        # Removing more coins than we have should cause a value error
        with self.assertRaises(ValueError):
            self.coins.remove_item(SilverCoin(), 10)
        # Stack should be removed once amount = 0
        self.coins.remove_item(SilverCoin(), 6)
        self.assertEqual(self.coins, self.empty)
        # testing with a more diverse inventory
        # items that almost match should not be removed
        with self.assertRaises(KeyError):
            self.rich.remove_item(Sword(15, "platinum"))
        # this should work correctly
        self.rich.remove_item(Sword(15, "steel"))
        self.assertEqual(self.rich, inv.Inventory(
            (HealthPotion(10), 5),
            (SilverCoin(), 15),
            (Sword(15, "steel"), 1)
        ))
        self.rich.remove_item(Sword(15, "steel"))
        self.assertEqual(self.rich, inv.Inventory(
            (HealthPotion(10), 5),
            (SilverCoin(), 15),
        ))
        # manually check that bucket has been removed
        self.assertEqual(len(self.rich._items), 2)
        with self.assertRaises(KeyError):
            self.rich.remove_item(HealthPotion(3))
        # we can remove 4 potions...
        self.rich.remove_item(HealthPotion(10), 4)
        # ...but we can't remove 4 more
        with self.assertRaises(ValueError):
            self.rich.remove_item(HealthPotion(10), 4)
        # check the state of the inventory
        self.assertEqual(self.rich, inv.Inventory(
            (SilverCoin(), 15),
            (HealthPotion(10), 1),
        ))
        # now let's try to remove everything else
        self.rich.remove_item(HealthPotion(10))
        self.rich.remove_item(SilverCoin(), 15)
        self.assertEqual(self.rich, self.empty)
        self.assertEqual(self.rich._items, {})

    def hash_item_amt(self, item_amt):
        """returns a hash for tuples of the form (Item, int)
this function is inefficient and fragile, do not use outside simple testing"""
        item, amt = item_amt
        return hash((str(type(item)), (tuple(item.save()), amt)))

    def cmp_contents(self, list1, list2):
        """
        returns true if and only if all (item, amt) pairs that appear in
        list1 also appear in list2, and visa versa
        this function is inefficient and fragile, do not use outside simple testing
        """
        set1 = {self.hash_item_amt(x) for x in list1}
        set2 = {self.hash_item_amt(x) for x in list2}
        return len(set1) == len(list2) and len(set1) == len(list2) and set1 == set2

    def test_iter(self):
        """test that __iter__ works properly"""
        self.assertEqual(len(list(self.empty)), 0)
        coin_list = list(self.coins)
        self.assertEqual(len(coin_list), 1)
        self.assertEqual(coin_list[0][1], 10)
        self.assertTrue(isinstance(coin_list[0][0], SilverCoin))
        inv_items = list(self.rich)
        cloned_inv = inv.Inventory(*inv_items)
        self.assertEqual(self.rich, cloned_inv)

    def test_stack_iter(self):
        self.assertEqual(list(self.coins.stacks()),
                         [inv.ItemStack(SilverCoin, 10)])
        results = list(self.potion_seller.stacks())
        results.sort(key=lambda x: x.amount)
        self.assertEqual(results, [
            inv.ItemStack(HealthPotion, 2, data={"hp": 100}),
            inv.ItemStack(HealthPotion, 3, data={"hp": 50}),
            inv.ItemStack(HealthPotion, 5, data={"hp": 10}),
            inv.ItemStack(HealthPotion, 7, data={"hp": 3}),
            inv.ItemStack(SilverCoin, 20),
        ])

    def test_find(self):
        """test that find method can be used to find items"""
        # no results for an item names Silver Coin in self.empty
        results = list(self.empty.find_child(FindParams(name=("silver coin",))))
        self.assertEqual(results, [])
        # really, nothing should work for self.empty
        results = list(self.empty.find_child(FindParams()))
        self.assertEqual(results, [])

        # testing find for self.coins
        results = list(self.coins.find_child(FindParams()))
        self.assertEqual(len(results), 1)
        # checking that the item yielded is indeed a SilverCoin
        self.assertTrue(isinstance(results[0][0], SilverCoin))
        # checking the quantity
        self.assertEqual(results[0][1], 10)

        # test results should be the same if a name is provided
        results = list(self.coins.find_child(FindParams(name=("silver coin",))))
        self.assertTrue(isinstance(results[0][0], SilverCoin))
        self.assertEqual(results[0][1], 10)

        # ...or if exact data is provided
        results = list(self.coins.find_child(FindParams(), exact={}))
        self.assertTrue(isinstance(results[0][0], SilverCoin))
        self.assertEqual(results[0][1], 10)

        # ...or both
        results = list(self.coins.find_child(FindParams(name=("silver coin",)), exact={}))
        self.assertTrue(isinstance(results[0][0], SilverCoin))
        self.assertEqual(results[0][1], 10)

        # but if we provide non-matching data, we expect nothing
        results = list(self.coins.find_child(FindParams(), value=10))
        self.assertEqual(results, [])

        # testing find for potion_seller
        # first, add a few "BadPoisons" to
        # calling find with no arguments should yield everything
        results = list(self.potion_seller.find_child(FindParams()))
        self.assertTrue(self.cmp_contents(results, [
            (SilverCoin(), 20),
            (HealthPotion(hp=10), 5),
            (HealthPotion(hp=3), 7),
            (HealthPotion(hp=100), 2),
            (HealthPotion(hp=50), 3)
        ]))
        # test for type Health Potion
        results = list(self.potion_seller.find_child(FindParams(type=(HealthPotion,))))
        self.assertTrue(self.cmp_contents(results, [
            (HealthPotion(hp=10), 5),
            (HealthPotion(hp=3), 7),
            (HealthPotion(hp=100), 2),
            (HealthPotion(hp=50), 3)
        ]))
        # test for fields 'hp=10'
        results = list(self.potion_seller.find_child(FindParams(), hp=10))
        self.assertTrue(self.cmp_contents(results, [
            (HealthPotion(hp=10), 5),
        ]))
        # test for fields 'hp=5'
        results = list(self.potion_seller.find_child(FindParams(),hp=5))
        self.assertTrue(self.cmp_contents(results, [
        ]))
        # test for fields 'hp=10' and type=HealthPotion
        results = list(self.potion_seller.find_child(FindParams(type=HealthPotion), hp=10))
        self.assertTrue(self.cmp_contents(results, [
            (HealthPotion(hp=10), 5),
        ]))
        # test with exact data
        results = list(self.potion_seller.find_child(FindParams(), hp=100))
        self.assertTrue(self.cmp_contents(results, [
            (HealthPotion(hp=100), 2),
        ]))
        # test with exact data and redundant 'hp=100'
        results = list(self.potion_seller.find_child(FindParams(), exact={"hp": 100}, hp=100))
        self.assertTrue(self.cmp_contents(results, [
            (HealthPotion(hp=100), 2),
        ]))
        # test with must_have and contradictory 'hp=5'
        results = list(self.potion_seller.find_child(FindParams(), exact={"hp": 100}, hp=5))
        self.assertTrue(self.cmp_contents(results, [
        ]))
        self.potion_seller.add_item(BadPoison(dmg=10), 5)
        self.potion_seller.add_item(BadPoison(dmg=3), 5)
        self.potion_seller.add_item(Sword(dmg=10, material="steel"), 3)
        self.potion_seller.add_item(Sword(dmg=7, material="steel"), 3)
        # testing on dmg=10 should yield sword and BadPoison
        results = list(self.potion_seller.find_child(FindParams(), dmg=10))
        self.assertTrue(self.cmp_contents(results, [
            (BadPoison(dmg=10), 5),
            (Sword(dmg=10, material="steel"), 3)
        ]))
        # testing with exact {"dmg": 10} should only yield BadPoison
        results = list(self.potion_seller.find_child(FindParams(), exact={"dmg": 10}))
        self.assertTrue(self.cmp_contents(results, [
            (BadPoison(dmg=10), 5),
        ]))
        # testing with multiple field arguments
        results = list(self.potion_seller.find_child(FindParams(), dmg=10, material="steel"))
        self.assertTrue(self.cmp_contents(results, [
            (Sword(dmg=10, material="steel"), 3)
        ]))
        # good name should return something
        results = list(self.potion_seller.find_child(FindParams(name=("sword",)), dmg=7, material="steel"))
        self.assertTrue(self.cmp_contents(results, [
            (Sword(dmg=7, material="steel"), 3)
        ]))
        # bad name should return nothing
        results = list(self.potion_seller.find_child(FindParams(name=("swor",)), dmg=10, material="steel"))
        self.assertTrue(self.cmp_contents(results, [
        ]))

    def test_readable(self):
        """test that readable view of inventory works properly"""
        self.assertEqual(self.empty.readable(), "")
        self.assertEqual(self.coins.readable(), "Silver Coin: 10")
        self.assertEqual(self.rich.readable(),
                         "Health Potion: 5\n"
                         "Silver Coin: 15\n"
                         "Sword: 2")
        # TODO: add self.potion_seller testcase after you update this method
