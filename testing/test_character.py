"""module testing the Character class"""
import unittest
import item
import character as char
import location as loc
import inventory as inv

# defining some test CharacterClasses
class Human(char.Character):
    """base class for all humans"""
    equip_slots = ["Head", "Right Hand"]

class Soldier(Human):
    """a soldier class"""

class Bureaucrat(Human):
    """a different kind of human class"""

class Commander(Soldier, Bureaucrat):
    """inherits from both soldier and bureaucrat"""

class Slug(char.Character):
    """a non-human base class"""

class AlphaSlug(Slug):
    """a class derived from Slug"""

class TestCharFilter(unittest.TestCase):
    """basic testcase for the pervasive CharFilter class"""

    # defining several CharacterClasses for testing

    def setUp(self):
        self.maxDiff = 1000
        # a boring human
        self.gary = Human("Gary")
        # some soldiers
        self.chad = Soldier("Chad")
        self.zeke = Soldier("Zeke")
        # a bureaucrat
        self.bill = Bureaucrat("Bill")
        # a commander
        self.dwight = Commander("Dwight")
        # simple slugs
        self.bloog = Slug("Bloog")
        self.plubb = Slug("Plubb")
        # an intimidating alpha slug
        self.vloobuk = AlphaSlug("Vloobuk")
        # lists of each character / CharacterClass to avoid repetition
        self.char_list = [
            self.gary, self.chad, self.zeke, self.bill, self.dwight,
            self.bloog, self.plubb, self.vloobuk
        ]
        self.classes = [
            Human, Soldier, Bureaucrat, Commander, Slug, AlphaSlug
        ]
        # some typical test results
        self.all_chars = {
            char: True for char in self.char_list + self.classes
        }
        self.no_chars = {
            char: False for char in self.char_list + self.classes
        }

    def filter_test(self, filt):
        """helper function that returns a dict mapping Characters to a boolean
        representing whether or not [filt] allows them through
        """
        return {
            char: filt.permits(char) for char in self.char_list + self.classes
        }

    def test_repr(self):
        """test that repr(CharFilter) works as expected"""
        filt = char.CharFilter(mode=False)
        self.assertEqual(repr(filt),
                         "CharFilter(False, set(), set(), set())")
        filt = char.CharFilter(mode=True)
        self.assertEqual(repr(filt),
                         "CharFilter(True, set(), set(), set())")
        filt = char.CharFilter(False, [Slug, AlphaSlug])
        # testing further is difficult due to set order changing

    def test_mode(self):
        """test that __init__'s mode keyword works as expected"""
        # creating a whitelist and blacklist with strings
        whitelist = char.CharFilter(mode="whitelist")
        blacklist = char.CharFilter(mode="blacklist")
        self.assertEqual(self.filter_test(whitelist), self.no_chars)
        self.assertEqual(self.filter_test(blacklist), self.all_chars)
        # creating a whitelist and blacklist with booleans
        whitelist = char.CharFilter(mode=True)
        blacklist = char.CharFilter(mode=False)
        self.assertEqual(self.filter_test(whitelist), self.no_chars)
        self.assertEqual(self.filter_test(blacklist), self.all_chars)
        # creating a whitelist and blacklist with enum values
        whitelist = char.CharFilter(char.FilterMode.WHITELIST)
        blacklist = char.CharFilter(char.FilterMode.BLACKLIST)
        self.assertEqual(self.filter_test(whitelist), self.no_chars)
        self.assertEqual(self.filter_test(blacklist), self.all_chars)

    def test_include_classes(self):
        """test that including CharacterClasses allows them through"""
        whitelist = char.CharFilter(mode="whitelist")
        whitelist.include(AlphaSlug)
        # only AlphaSlugs are allowed through
        expected = self.no_chars.copy()
        expected[self.vloobuk] = True
        expected[AlphaSlug] = True
        self.assertEqual(self.filter_test(whitelist), expected)
        # test that AlphaSlug was added to the set
        self.assertEqual(whitelist._classes, set([AlphaSlug]))
        # now all soldier and soldier-derived classes should be permited
        whitelist.include(Soldier)
        expected[self.chad] = True
        expected[self.zeke] = True
        expected[self.dwight] = True
        expected[Soldier] = True
        expected[Commander] = True
        self.assertEqual(self.filter_test(whitelist), expected)
        # test that Soldier was added to the set
        self.assertEqual(whitelist._classes, set([AlphaSlug, Soldier]))

        # now test including with a blacklist
        blacklist = char.CharFilter(mode="blacklist")
        blacklist.include(AlphaSlug)
        expected = self.all_chars.copy()
        # it's a blacklist, and nobody was excluded, so all are permitted
        self.assertEqual(self.filter_test(blacklist), expected)
        # no classes should be added to set
        self.assertEqual(blacklist._classes, set())

    def test_exclude_classes(self):
        """test that excluding CharacterClasses does not allow them through"""
        whitelist = char.CharFilter(mode="whitelist")
        # excluding a class from a whitelist should have no effect
        # since whitelists only track included classes
        whitelist.exclude(Human)
        expected = self.no_chars.copy()
        self.assertEqual(self.filter_test(whitelist), expected)
        # no classes should be added to set
        self.assertEqual(whitelist._classes, set())

        # now testing a blacklist
        blacklist = char.CharFilter(mode="blacklist")
        blacklist.exclude(AlphaSlug)
        expected = self.all_chars
        expected[self.vloobuk] = False
        expected[AlphaSlug] = False
        self.assertEqual(self.filter_test(blacklist), expected)
        # AlphaSlug should be added to set
        self.assertEqual(blacklist._classes, set([AlphaSlug]))
        # excluding another class
        blacklist.exclude(Bureaucrat)
        expected[self.bill] = False
        expected[self.dwight] = False
        expected[Bureaucrat] = False
        expected[Commander] = False
        self.assertEqual(self.filter_test(blacklist), expected)
        # Bureaucrat should be added to set
        self.assertEqual(blacklist._classes, set([AlphaSlug, Bureaucrat]))

    def test_whitelist_chars(self):
        """including/excluding Characters should overrides any class
        permissions for whitelists"""
        whitelist = char.CharFilter(mode="whitelist")
        whitelist.include(Soldier)
        whitelist.exclude(self.dwight)
        expected = self.no_chars.copy()
        # add all soldiers, except Dwight who we excluded
        expected[self.chad] = True
        expected[self.zeke] = True
        expected[Soldier] = True
        expected[Commander] = True
        self.assertEqual(self.filter_test(whitelist), expected)
        # check that the classes and include chars work as expected
        self.assertEqual(whitelist._classes, set([Soldier]))
        self.assertEqual(whitelist._include_chars, set())
        self.assertEqual(whitelist._exclude_chars, set([self.dwight]))
        # now include dwight
        whitelist.include(self.dwight)
        expected[self.dwight] = True
        self.assertEqual(self.filter_test(whitelist), expected)
        self.assertEqual(whitelist._classes, set([Soldier]))
        self.assertEqual(whitelist._include_chars, set([self.dwight]))
        self.assertEqual(whitelist._exclude_chars, set())
        # now exclude the Soldier class
        whitelist.exclude(Soldier)
        expected = self.no_chars.copy()
        expected[self.dwight] = True
        self.assertEqual(self.filter_test(whitelist), expected)
        self.assertEqual(whitelist._classes, set())
        self.assertEqual(whitelist._include_chars, set([self.dwight]))
        self.assertEqual(whitelist._exclude_chars, set())

    def test_blacklist_chars(self):
        """including/excluding Characters should overrides any class
        permissions for blacklists"""
        blacklist = char.CharFilter(mode="blacklist")
        # exclude Slug in general, but include bloog
        blacklist.exclude(Slug)
        blacklist.exclude(self.vloobuk)
        blacklist.include(self.bloog)
        expected = self.all_chars.copy()
        expected[Slug] = False
        expected[AlphaSlug] = False
        expected[self.vloobuk] = False
        expected[self.plubb] = False
        self.assertEqual(self.filter_test(blacklist), expected)
        self.assertEqual(blacklist._classes, set([Slug]))
        self.assertEqual(blacklist._include_chars, set([self.bloog]))
        self.assertEqual(blacklist._exclude_chars, set([self.vloobuk]))
        # now include the Slug class in general again
        blacklist.include(Slug)
        expected[Slug] = True
        expected[AlphaSlug] = True
        expected[self.plubb] = True
        self.assertEqual(self.filter_test(blacklist), expected)
        self.assertEqual(blacklist._classes, set())
        self.assertEqual(blacklist._include_chars, set([self.bloog]))
        self.assertEqual(blacklist._exclude_chars, set([self.vloobuk]))
        # now include vloobuk and exclude bloog
        blacklist.include(self.vloobuk)
        blacklist.exclude(self.bloog)
        expected[self.vloobuk] = True
        expected[self.bloog] = False
        self.assertEqual(self.filter_test(blacklist), expected)
        self.assertEqual(blacklist._classes, set())
        self.assertEqual(blacklist._include_chars, set([self.vloobuk]))
        self.assertEqual(blacklist._exclude_chars, set([self.bloog]))


# some test locations
TEST_ROOM = loc.Location("Room", "This is just a room for testing.")
TEST_OUT = loc.Location("Outside", "This room is outside.")
TEST_EXIT = loc.Exit(TEST_OUT, "out", ["outside", "test out"])
TEST_ROOM.add_exit(TEST_EXIT)

# some test items
class Coin(item.MiscItem):
    """a simple coin"""


class HealthPotion(item.MiscItem):
    """a health potion with vary strength"""
    def __init__(self, hp):
        self.hp = 5

    @classmethod
    def load(cls, data):
        return cls(data["hp"])

    def save(self):
        return {"hp": 5}


class TestApparel(item.Equippable):
    """a base class for other test equippables"""

    target = item.EquipTarget("Head")

    def equip(self, char):
        char.message(f"equip {self}")

    def unequip(self, char):
        char.message(f"unequip {self}")


class Hat(TestApparel):
    target = item.EquipTarget("Head")


class Helmet(TestApparel):
    target = item.EquipTarget("Head")


class Sword(TestApparel):
    target = item.EquipTarget("Right Hand")


class Mace(TestApparel):
    target = item.EquipTarget("Right Hand")


class Bow(TestApparel):
    target = item.EquipTarget("left Hand")


class TestCharacterInventory(unittest.TestCase):
    """test that Character inventory methods work properly"""
    def setUp(self):
        # a default character
        self.default = char.Character("Default")
        # a human
        self.finn = Human("Finn")
        self.finn.add_item(Sword())
        self.finn.add_item(Coin(), 5)
        self.finn.add_item(HealthPotion(10), 3)
        # create an EquipDict for comparison
        self.ref = item.EquipTarget.make_dict(*Human.equip_slots)

    def add_item_stack(self):
        """test that either items or ItemStacks can be given to players"""
        self.default.add_item(inv.ItemStack.from_item(Sword(), 5))
        self.assertEqual(self.default.inv, inv.Inventory((Sword(), 5)))

    def test_equip(self):
        """test that the equip method throws proper exceptions and
        works as expected"""
        #TODO: test that all equip_commands are added!
        # Finn's equip dict should be empty to start with
        self.assertEqual(self.finn.equip_dict, self.ref)
        # equip Sword without removing one from the inventory
        sword = Sword()
        self.finn.equip(sword, from_inv=False)
        # sword should not be removed from inventory
        self.assertEqual(self.finn.inv, inv.Inventory(
            (Sword(), 1),
            (Coin(), 5),
            (HealthPotion(10), 3)
        ))
        # equip dict should be updated
        self.ref[item.EquipTarget("Right Hand")] = sword, False
        self.assertEqual(self.finn.equip_dict, self.ref)
        # item's equip method should be called
        self.assertEqual(self.finn.last_msg, "equip Sword")

        # try to equip an item that cannot be equipped
        with self.assertRaises(char.CharException,
                               msg="Health Potion cannot be equipped."):
            self.finn.equip(HealthPotion(5), False)

        # try to equip an item for which we don't have proper slots
        with self.assertRaises(char.CharException,
                               msg="Cannot equip Bow to Left Hand."):
            self.finn.equip(Bow(), False)

        # try to equip a hat, but this time pull it from the inventory
        hat = Hat()
        with self.assertRaises(char.CharException,
                               msg="Cannot equip Hat-not found in inventory."):
            self.finn.equip(hat, True)
        # give finn a hat and try again
        self.finn.add_item(Hat())
        self.finn.equip(hat)
        # hat should be removed from inventory
        self.assertEqual(self.finn.inv, inv.Inventory(
            (Sword(), 1),
            (Coin(), 5),
            (HealthPotion(10), 3)
        ))
        # equip dict should be updated
        self.ref[item.EquipTarget("Head")] = hat, True
        self.assertEqual(self.finn.equip_dict, self.ref)
        # item's equip method should be called
        self.assertEqual(self.finn.last_msg, "equip Hat")

        # try to equip a Mace, which implicitly unequips the Sword
        mace = Mace()
        self.finn.equip(mace, from_inv=False)
        # mace should not be removed from inventory and
        # old sword should NOT be returned since from_inv=False
        self.assertEqual(self.finn.inv, inv.Inventory(
            (Sword(), 1),
            (Coin(), 5),
            (HealthPotion(10), 3)
        ))
        # equip dict should be updated
        self.ref[item.EquipTarget("Right Hand")] = mace, False
        self.assertEqual(self.finn.equip_dict, self.ref)
        # item's equip method should be called
        self.assertEqual(self.finn.last_msg, "equip Mace")

    def test_unequip(self):
        """test that the Character.unequip method performs proper error
        checking and works as expected"""
        # TODO test that all EquipCommands are removed!
        # manually equip the hat and the mace
        # we mark the hat as from_inv=False, so it should not be returned
        # while the mace should be added back to inventory
        hat = Hat()
        mace = Mace()
        self.finn.equip_dict[hat.target] = hat, False
        self.finn.equip_dict[mace.target] = mace, True
        # copy a reference for comparisons
        ref = self.finn.equip_dict.copy()
        # clear finn's inventory for convenience
        self.finn.inv = inv.Inventory()

        # try unequipping a slot that does not exist
        with self.assertRaises(char.CharException,
                               msg="Human does not possess equip slot 'Foo'."):
            self.finn.unequip(item.EquipTarget("Foo"))

        # unequip the item in the "Head" slot
        self.finn.unequip(item.EquipTarget("head"))
        # hat should not be added to inventory since from_inv=False
        self.assertEqual(self.finn.inv, inv.Inventory())
        # equip dict should be updated
        ref[item.EquipTarget("head")] = None
        self.assertEqual(self.finn.equip_dict, ref)
        # item's equip method should be called
        self.assertEqual(self.finn.last_msg, "unequip Hat")

        # unequip the item in the "Right Hand" slot
        self.finn.unequip(item.EquipTarget("right hand"))
        # mace should be added to inventory since from_inv=False
        self.assertEqual(self.finn.inv, inv.Inventory((Mace(), 1)))
        # equip dict should be updated
        ref[item.EquipTarget("right hand")] = None
        self.assertEqual(self.finn.equip_dict, ref)
        # item's equip method should be called
        self.assertEqual(self.finn.last_msg, "unequip Mace")

        # try to unequip from an empty slot
        with self.assertRaises(char.CharException,
                               msg="No item equipped on target 'Head'."):
            self.finn.unequip(item.EquipTarget("hEAD"))


class TestDefaultCommands(unittest.TestCase):
    """test that all the default Character commands work properly"""
    def setUp(self):
        self.room = loc.Location("Room", "This is just a room for testing.")
        self.bill = Human("Bill")
        self.bill.set_location(TEST_ROOM)
        self.phil = char.Character("Phil")
        self.phil.set_location(TEST_ROOM)
        self.dana = char.Character("Dana")
        self.dana.set_location(TEST_OUT)

    def tearDown(self):
        self.bill.despawn()
        self.phil.despawn()
        self.dana.despawn()
        # clear the inventories for TEST_ROOM and TEST_EXIT
        TEST_ROOM.inv = inv.Inventory()
        TEST_OUT.inv = inv.Inventory()

    def test_help(self):
        """test for the help command"""
        # using help by itself should produce a list of commands
        self.bill.command("help")
        self.assertEqual(self.bill.msgs.pop(), self.bill.cmd_dict.help())

        # using help with other commands should produce their docstring
        self.bill.command("help help")
        help_msg = self.bill.msgs.pop()
        # check that help message agrees with the CommandDict
        self.assertEqual(help_msg, self.bill.cmd_dict.get_cmd("help").help())
        self.assertEqual(help_msg,
                         "Show relevant help information for a particular command.\n"
                         "usage: help [command]\n"
                         "If no command is supplied, a list of all commands is shown.")
        self.bill.command("help say")
        help_msg = self.bill.msgs.pop()
        self.assertEqual(help_msg,
                         "Say a message aloud, sent to all players in your "
                         "current locaton.\nusage: say [msg]")
        # invalid command should cause an error
        self.bill.command("help invalid_cmd")
        help_msg = self.bill.msgs.pop()
        self.assertEqual(help_msg, "Command 'invalid_cmd' not recognized.")

    def test_say(self):
        """test that the say command works properly"""
        # test with a simple message
        self.bill.command("say hey, what's up?")
        self.assertEqual(self.bill.msgs,
                         ["Bill the Human: hey, what's up?"])
        self.assertEqual(self.phil.msgs,
                         ["Bill the Human: hey, what's up?"])
        self.bill.msgs.clear()
        self.phil.msgs.clear()
        self.bill.command("say spam")
        self.bill.command("say spam")
        self.bill.command("say spam")
        self.assertEqual(self.bill.msgs,
                         ["Bill the Human: spam"] * 3)
        self.assertEqual(self.phil.msgs,
                         ["Bill the Human: spam"] * 3)
        self.bill.msgs.clear()
        self.phil.msgs.clear()
        # empty messages should not be sent
        self.bill.command("say")
        self.assertEqual(self.bill.msgs, [])
        self.assertEqual(self.phil.msgs, [])
        self.bill.command("say      ")
        self.assertEqual(self.bill.msgs, [])
        self.assertEqual(self.phil.msgs, [])
        # consecutive spaces will be treated as one separator
        self.bill.command("say  whoops   extra  spaces")
        self.assertEqual(self.bill.msgs,
                         ["Bill the Human: whoops extra spaces"])
        self.assertEqual(self.phil.msgs,
                         ["Bill the Human: whoops extra spaces"])

    def test_go_err(self):
        """test that the 'go' sends an error with a bad exit name"""
        self.bill.command("go")
        self.assertEqual(self.bill.msgs, ["No exit with name ''."])
        self.bill.msgs.clear()
        self.assertTrue(self.bill.location is TEST_ROOM)
        self.bill.command("go foobar")
        self.assertEqual(self.bill.msgs, ["No exit with name 'foobar'."])
        self.assertTrue(self.bill.location is TEST_ROOM)

    def test_go_basic(self):
        """test that basic use of the 'go' command works properly"""
        self.bill.command("go outside")
        self.assertEqual(self.bill.msgs, [])
        self.assertEqual(self.phil.msgs,
                         ["Bill left through exit 'outside'."])
        self.assertEqual(self.dana.msgs, ["Bill entered."])
        self.assertTrue(self.bill.location is TEST_OUT)
        self.tearDown()
        self.setUp()
        self.bill.command("go out")
        self.assertEqual(self.bill.msgs, [])
        self.assertEqual(self.phil.msgs,
                         ["Bill left through exit 'out'."])
        self.assertEqual(self.dana.msgs, ["Bill entered."])
        self.assertTrue(self.bill.location is TEST_OUT)
        self.tearDown()
        self.setUp()
        self.bill.command("go test  out")
        self.assertEqual(self.bill.msgs, [])
        self.assertEqual(self.phil.msgs,
                         ["Bill left through exit 'test out'."])
        self.assertEqual(self.dana.msgs, ["Bill entered."])
        self.assertTrue(self.bill.location is TEST_OUT)

    def test_go_filtered(self):
        """test that 'go' command respects CharFilters"""
        # set access for exit to an empty whitelist
        # i.e. nobody is allowed through
        TEST_EXIT.access = char.CharFilter(mode=True)
        self.bill.command("go outside")
        self.assertEqual(self.bill.msgs, ["Exit 'outside' is unaccessible to you."])
        self.assertEqual(self.phil.msgs, [])
        self.assertEqual(self.dana.msgs, [])
        self.assertTrue(self.bill.location is TEST_ROOM)
        self.bill.msgs.clear()
        # set visibility for exit to an empty whitelist
        # i.e. nobody can see this exit or go through now
        # so Bill should not be informed that this exit even exists
        TEST_EXIT.visibility = char.CharFilter(mode=True)
        self.bill.command("go outside")
        self.assertEqual(self.bill.msgs, ["No exit with name 'outside'."])
        self.assertEqual(self.phil.msgs, [])
        self.assertEqual(self.dana.msgs, [])
        self.assertTrue(self.bill.location is TEST_ROOM)
        self.bill.msgs.clear()
        # BUT, if we set access to empty blacklist (allowing anyone in)
        # Bill should be allowed through, even though he can't see the exit
        TEST_EXIT.access = char.CharFilter(mode=False)
        self.bill.command("go outside")
        self.assertEqual(self.bill.msgs, [])
        self.assertEqual(self.phil.msgs,
                         ["Bill left through exit 'outside'."])
        self.assertEqual(self.dana.msgs, ["Bill entered."])
        self.assertTrue(self.bill.location is TEST_OUT)

    def test_cmd_equip(self):
        """test that the equip command works properly"""
        self.bill.inv.add_item(Mace())
        self.bill.inv.add_item(Sword())
        # try a nonexistant item
        self.bill.command("equip fwwrsd")
        self.assertEqual(self.bill.msgs.pop(),
                        "Could not find item 'fwwrsd'.")
        self.bill.command("equip mace")
        # mace should be equipped
        self.assertEqual(self.bill.msgs.pop(),
                         "equip Mace")
        mace, from_inv = self.bill.equip_dict[item.EquipTarget("Right Hand")]
        self.assertTrue(isinstance(mace, Mace))
        self.assertTrue(from_inv)
        # now we cannot equip the mace again, because it cannot be found
        self.bill.command("equip mace")
        self.assertEqual(self.bill.msgs.pop(),
                         "Could not find item 'mace'.")
        # mace should still be equipped
        mace, from_inv = self.bill.equip_dict[item.EquipTarget("Right Hand")]
        self.assertTrue(isinstance(mace, Mace))
        self.assertTrue(from_inv)
        # try equipping a sword
        self.bill.command("equip sword")
        self.assertEqual(self.bill.msgs, [
            "unequip Mace",
            "equip Sword"
        ])
        self.bill.msgs.clear()
        sword, from_inv = self.bill.equip_dict[item.EquipTarget("Right Hand")]
        self.assertTrue(isinstance(sword, Sword))
        self.assertTrue(from_inv)
        # we should be messaged if we equip an item we don't have a slot for
        self.bill.inv.add_item(Bow())
        self.bill.command("equip Bow")
        self.assertEqual(self.bill.msgs.pop(),
                         "Cannot equip item Bow to Left hand.")
        # equipping an un-equippable item should give us a message
        self.bill.inv.add_item(Coin())
        self.bill.command("equip Coin")
        self.assertEqual(self.bill.msgs.pop(),
                         "Coin cannot be equipped.")
        # TODO: test ambiguity handling once added

    def test_cmd_unequip(self):
        """test that the unequip command works properly"""
        self.bill.inv.add_item(Sword())
        self.bill.inv.add_item(Hat())
        # equip the sword and hat
        self.bill.equip(Sword(), from_inv=True)
        self.bill.equip(Hat(), from_inv=True)
        # purge the equip messages
        self.bill.msgs.clear()
        # create a reference copy of the equip_dict for testing
        ref = self.bill.equip_dict.copy()
        # try to unequip a non-existent item
        self.bill.command("unequip flesh")
        self.assertEqual(self.bill.msgs.pop(),
                         "Could not find equipped item 'flesh'.")
        # equipped items should be unaffected
        self.assertEqual(ref, self.bill.equip_dict)
        # now try unequipping the hat
        self.bill.command("unequip hat")
        self.assertEqual(self.bill.msgs.pop(),
                         "unequip Hat")
        # hat should be removed from our equip_dict
        ref[item.EquipTarget("head")] = None
        self.assertEqual(self.bill.equip_dict, ref)
        # hat should be added back to inventory
        self.assertEqual(self.bill.inv, inv.Inventory((Hat(), 1)))

        # now try unequipping the hat again
        self.bill.command("unequip hat")
        self.assertEqual(self.bill.msgs.pop(),
                         "Could not find equipped item 'hat'.")
        self.assertEqual(ref, self.bill.equip_dict)

        # try unequipping the sword (should be case-insensitive)
        self.bill.command("unequip SwOrD")
        self.assertEqual(self.bill.msgs.pop(),
                         "unequip Sword")
        # sword should be removed from our equip_dict
        ref[item.EquipTarget("right hand")] = None
        self.assertEqual(self.bill.equip_dict, ref)
        # sword should be added back to inventory
        inv_items = [(Hat(), 1), (Sword(), 1)]
        self.assertEqual(self.bill.inv, inv.Inventory(*inv_items))

    def test_cmd_inv(self):
        """test that the 'inv' command works properly"""
        self.bill.command("inv")
        self.assertEqual(self.bill.msgs.pop(),
                         "Head: none\nRight hand: none")
        # add some stuff to the inventory
        self.bill.add_item(Coin(), 30)
        self.bill.add_item(Sword(), 2)
        self.bill.command("inv")
        self.assertEqual(self.bill.msgs, [
            "Head: none\nRight hand: none",
            self.bill.inv.readable()
        ])
        self.bill.msgs.clear()
        # add more items
        self.bill.add_item(Mace(), 2)
        self.bill.add_item(Bow(), 2)
        self.bill.add_item(Hat(), 1)
        self.bill.command("inv")
        self.assertEqual(self.bill.msgs, [
            "Head: none\nRight hand: none",
            self.bill.inv.readable()
        ])
        self.bill.msgs.clear()
        # equip some items
        self.bill.equip(Hat(), from_inv=False)
        self.bill.command("inv")
        self.assertEqual(self.bill.msgs, [
            "equip Hat",
            "Head: Hat\nRight hand: none",
            self.bill.inv.readable()
        ])
        self.bill.msgs.clear()
        # equip more items
        self.bill.equip(Sword(), from_inv=False)
        self.bill.command("inv")
        self.assertEqual(self.bill.msgs, [
            "equip Sword",
            "Head: Hat\nRight hand: Sword",
            self.bill.inv.readable()
        ])

    def test_cmd_pickup(self):
        """test that the 'pickup' command works properly"""
        # try to pickup an item when there are none available
        self.bill.command("pickup coin")
        self.assertEqual(self.bill.msgs.pop(),
                         "Could not find item 'coin' to pick up.")
        # now add a coin and some swords
        TEST_ROOM.add_item(Coin(), 5)
        TEST_ROOM.add_item(Sword(), 1)
        # create a copy of TEST_ROOM's inv for reference
        loc_ref = inv.Inventory(*TEST_ROOM.inv)
        # create a copy of Bill's inv for reference
        bill_ref = inv.Inventory(*self.bill.inv)
        # try to pickup an item with a bad name
        self.bill.command("pickup foo")
        self.assertEqual(self.bill.msgs.pop(),
                         "Could not find item 'foo' to pick up.")
        # try looting a coin
        self.bill.command("pickup coin")
        self.assertEqual(self.bill.msgs, [])
        # coin should be removed from location
        loc_ref.remove_item(Coin())
        self.assertEqual(TEST_ROOM.inv, loc_ref)
        # coin should be added to character
        bill_ref.add_item(Coin())
        self.assertEqual(self.bill.inv, bill_ref)

        # try looting a sword
        self.bill.command("pickup sword")
        self.assertEqual(self.bill.msgs, [])
        # coin should be removed from location
        loc_ref.remove_item(Sword())
        self.assertEqual(TEST_ROOM.inv, loc_ref)
        # coin should be added to character
        bill_ref.add_item(Sword())
        self.assertEqual(self.bill.inv, bill_ref)

    def test_cmd_drop(self):
        """test that the 'drop' command works properly"""
        # try to drop an item when inventory is empty
        self.bill.command("drop coin")
        self.assertEqual(self.bill.msgs.pop(),
                         "Could not find item 'coin' to drop.")
        # now add a coin and some swords to bill's inventory
        self.bill.add_item(Coin(), 5)
        self.bill.add_item(Sword(), 1)
        # create a copy of TEST_ROOM's inv for reference
        loc_ref = inv.Inventory(*TEST_ROOM.inv)
        # create a copy of Bill's inv for reference
        bill_ref = inv.Inventory(*self.bill.inv)

        # try dropping a coin
        self.bill.command("drop coin")
        self.assertEqual(self.bill.msgs, [])
        # coin should be added to location's inventory
        loc_ref.add_item(Coin())
        self.assertEqual(TEST_ROOM.inv, loc_ref)
        # coin should be removed from bill's inventory
        bill_ref.remove_item(Coin())
        self.assertEqual(self.bill.inv, bill_ref)

        # try dropping a sword
        self.bill.command("drop sWORD")
        self.assertEqual(self.bill.msgs, [])
        # sword should be added to the location's inventory
        loc_ref.add_item(Sword())
        self.assertEqual(TEST_ROOM.inv, loc_ref)
        # sword should to be removed from bill's inventory
        bill_ref.remove_item(Sword())
        self.assertEqual(self.bill.inv, bill_ref)

        # try dropping a sword (when none are left)
        self.bill.command("drop Sword")
        self.assertEqual(self.bill.msgs.pop(),
                         "Could not find item 'sword' to drop.")


class TestSpawn(unittest.TestCase):

    def setUp(self):
        self.new_player = Human() # no name
        self.bill = Human("Bill")

    def tearDown(self):
        self.bill.despawn()
        self.new_player.despawn()

    def test_name_at_spawn(self):
        self.assertEqual(self.new_player._name, None)
        self.assertEqual(self.bill._name, "Bill")

    def test_spawn(self):
        self.assertEqual(self.new_player.msgs, [])
        self.assertEqual(self.bill.msgs, [])
        self.assertEqual(self.new_player.location, None)
        self.assertEqual(self.bill.location, None)
        self.bill.set_location(TEST_ROOM)
        self.assertEqual(self.bill.location, TEST_ROOM)

        # bill should be in normal parsing mode
        self.bill.command("oops")
        self.assertEqual(self.bill.msgs.pop(), "Command 'oops' not recognized.")
        # new player should also be in normal parsing mode
        self.new_player.command("oops")
        self.assertEqual(self.new_player.msgs.pop(), "Command 'oops' not recognized.")

        self.new_player.spawn(TEST_ROOM)
        # new player should not be moved yet
        self.assertEqual(self.new_player.location, TEST_ROOM)
        self.assertEqual(TEST_ROOM.characters, [self.bill])
        self.assertEqual(self.new_player.msgs, [
            "Welcome to MuddySwamp! You are a Human",
            "What should we call you?"
        ])
        self.new_player.msgs.clear()
        self.assertEqual(self.bill.msgs, [])
        self.assertTrue(self.new_player._parser == self.new_player._greeter)

        # test the different error messages
        self.new_player.command("name with spaces")
        self.assertEqual(self.new_player.msgs.pop(), "Names must be alphanumeric.")
        self.new_player.command("name_with_underscores")
        self.assertEqual(self.new_player.msgs.pop(), "Names must be alphanumeric.")
        self.new_player.command("43243-2144;")
        self.assertEqual(self.new_player.msgs.pop(), "Names must be alphanumeric.")
        self.new_player.command("")
        self.assertEqual(self.new_player.msgs.pop(), "Names must have at least 2 characters.")
        self.new_player.command("a")
        self.assertEqual(self.new_player.msgs.pop(), "Names must have at least 2 characters.")
        self.new_player.command("Tim") # finally, a valid name
        self.assertEqual(self.new_player.msgs, [])

        # player should be added to location
        self.assertEqual(TEST_ROOM.characters, [self.bill, self.new_player])

        self.assertEqual(self.bill.msgs, [])
        self.assertEqual(self.new_player.msgs, [])

        # new player should switch to default parser
        self.new_player.command("tim")
        self.assertEqual(self.new_player.msgs.pop(), "Command 'tim' not recognized.")
