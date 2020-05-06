"""testcases for testing the item module"""
import unittest
import item
import inventory as inv

class TestItemMetas(unittest.TestCase):
    """testcase for the basic guarantees of the item metaclasses"""

    # a bunch of classes and instantiating for testing
    class Cup(item.Item):
        # no description or label provided
        pass
    cup = Cup()

    # a base class for other currencies
    class Money(item.Item):
        label = "Money"

    class GoldPiece(Money):
        """description provided (and overriding docstring)."""
        description = "The highest denomination in the empire."
        label = "Money"
    gold_piece = GoldPiece()

    # inheriting from GoldPiece, just to prove that names / descriptions
    # are not inherited like label
    class SilverPiece(GoldPiece):
        pass
    silver_piece = SilverPiece()

    # descriptions will be automatically generated from docstrings
    class CopperPiece(Money):
        """An even lesser currency, used only for small items."""
        # overriding the name with a new name
        classname = "Shilling"
    shilling = CopperPiece()

    # a class can still be Usable, even if it derives from non-Usable
    class UsableMoney(Money):
        def on_use(self, char, args):
            pass
    usable_money = UsableMoney()

    class Potion(item.Item):
        """a health potion"""
        label = "Potions"
        def on_use(self, char, args):
            pass
    potion = Potion()

    # a class that inherits from a Usable item will be Usable
    class FancyPotion(Potion):
        """a fancier health potion, works the same way"""
    fancy_potion = FancyPotion()

    # an Equippable derives from Item, and should have all the same
    # features (classname, description, etc.)
    class Sword(item.Equippable):
        """An equippable sword
        Here's another line
        """
        target = inv.EquipTarget("hand")
    sword = Sword()

    def test_item_name(self):
        """test that Item names are generated if not provided"""
        self.assertEqual(self.Cup.classname, "Cup")
        self.assertEqual(self.Money.classname, "Money")
        self.assertEqual(self.GoldPiece.classname, "Gold Piece")
        self.assertEqual(self.SilverPiece.classname, "Silver Piece")
        self.assertEqual(self.CopperPiece.classname, "Shilling")
        self.assertEqual(self.Sword.classname, "Sword")

    def test_item_description(self):
        """test that Item descriptions are generated if not provided"""
        self.assertEqual(self.Cup.description, "[No description provided.]")
        self.assertEqual(self.Money.description, "[No description provided.]")
        self.assertEqual(self.GoldPiece.description,
                         "The highest denomination in the empire.")
        self.assertEqual(self.SilverPiece.description,
                         "[No description provided.]")
        self.assertEqual(self.CopperPiece.description,
                         "An even lesser currency, used only for small items.")
        self.assertEqual(self.Sword.description, "An equippable sword\n"
                                                 "Here's another line")

    def test_item_labels(self):
        """test that Item labels are generated if not provided"""
        # labels should be inherited
        self.assertEqual(self.Cup.label, "Item")
        self.assertEqual(self.Money.label, "Money")
        self.assertEqual(self.GoldPiece.label, "Money")
        self.assertEqual(self.SilverPiece.label, "Money")
        self.assertEqual(self.CopperPiece.label, "Money")
        self.assertEqual(self.Potion.label, "Potions")
        self.assertEqual(self.FancyPotion.label, "Potions")
        self.assertEqual(self.Sword.label, "Item")


    def test_str(self):
        """by default str(instance) returns the class name"""
        self.assertEqual(str(self.cup), "Cup")
        self.assertEqual(str(self.gold_piece), "Gold Piece")
        self.assertEqual(str(self.silver_piece), "Silver Piece")
        self.assertEqual(str(self.shilling), "Shilling")
        self.assertEqual(str(self.potion), "Potion")
        self.assertEqual(str(self.fancy_potion), "Fancy Potion")
        self.assertEqual(str(self.sword), "Sword")


    def test_is_usable(self):
        """test that Usable ABC works with isinstance to find
        ItemClasses with an 'on_use' method"""
        self.assertFalse(isinstance(self.cup, item.Usable))
        self.assertFalse(isinstance(self.gold_piece, item.Usable))
        self.assertFalse(isinstance(self.silver_piece, item.Usable))
        self.assertFalse(isinstance(self.shilling, item.Usable))
        self.assertTrue(isinstance(self.usable_money, item.Usable))
        self.assertTrue(isinstance(self.potion, item.Usable))
        self.assertTrue(isinstance(self.fancy_potion, item.Usable))
        self.assertFalse(isinstance(self.sword, item.Usable))


class TestEquippableItem(unittest.TestCase):

    def test_commands(self):
        """test that character.Commands are added"""
        pass

    def test_target_check(self):
        """test that new Equippable classes are checked for a target"""
        # failing to provide a target raises an attribute error
        with self.assertRaises(AttributeError):
            class Helmet(item.Equippable):
                """whoops I forgot the target"""

        # providing a target with the wrong type raises an error
        with self.assertRaises(TypeError):
            class Helmet(item.Equippable):
                target = "whoops not proper target"

        # inheriting from a class with a valid EquipTarget is sufficient
        class Headwear(item.Equippable):
            target = inv.EquipTarget("Head")

        class Hat(Headwear):
            pass

        # inheriting from a class and overriding the target with a
        # value of the wrong type will cause an error
        with self.assertRaises(TypeError):
            class Helmet(item.Equippable):
                target = "whoops not a proper target"
