"""module testing the Character class"""
import unittest
from swampymud import item
import swampymud.character as char
from swampymud.character import Command
import swampymud.location as loc
import swampymud.inventory as inv


def qlist(q):
    """Convenience function that converts asyncio.Queues into lists.
    This is inefficient and should not be used in real code.
    """
    l = []
    # get the messages out
    while not q.empty():
        l.append(q.get_nowait())

    # now put the messages back (since we popped them out)
    for i in l[::-1]:
        q.put_nowait(item)

    return l

def qclear(q):
    """Convenience function to clear an asyncio.Queue.
    This is inefficient and should not be used in real code.
    """
    while not q.empty():
        q.get_nowait()

class TestCommand(unittest.TestCase):
    """testing the Command class and associated functions"""

    def setUp(self):

        # simple testing function
        def hi(person, greeter):
            return f"Hi {person}, I'm {greeter}"

        self.hi = hi
        self.hi_bill = Command(hi, "bill")
        self.hi_bill_kw = Command(hi, person="bill")
        self.hi_by_tom = Command(hi, greeter="tom")
        self.hi_bill_by_tom = Command(hi, "bill", "tom")
        self.hi_bill_by_tom_kw = Command(hi, person="bill", greeter="tom")
        self.hi_bill2 = Command(hi, "bill")

    def test_eq(self):
        """testing == operator"""
        # only equal if function, arguments, and keywords are equal
        self.assertEqual(self.hi_bill, self.hi_bill2)
        self.assertEqual(self.hi_bill2, self.hi_bill)
        self.assertNotEqual(self.hi_bill_by_tom, self.hi_bill)
        self.assertNotEqual(self.hi_by_tom, self.hi_bill)
        self.assertNotEqual(self.hi_bill, self.hi_bill_by_tom)
        self.assertNotEqual(self.hi_bill_by_tom, self.hi_bill_by_tom_kw)

        # can we apply the rest of the arguments?
        self.assertEqual(self.hi_bill("matt"), "Hi bill, I'm matt")
        self.assertEqual(self.hi_bill_kw(greeter="matt"), "Hi bill, I'm matt")
        self.assertEqual(self.hi_by_tom("matt"), "Hi matt, I'm tom")
        self.assertEqual(self.hi_by_tom(person="matt"), "Hi matt, I'm tom")
        self.assertEqual(self.hi_bill_by_tom(), "Hi bill, I'm tom")

        # no more arguments to apply to this function
        with self.assertRaises(TypeError):
            self.hi_bill_by_tom("matt")

    def test_hash(self):
        """indirectly testing __hash__ of Command using a set"""
        commands = set()
        commands.add(self.hi_bill)
        self.assertTrue(self.hi_bill in commands)
        self.assertTrue(self.hi_bill2 in commands)
        self.assertFalse(self.hi_bill_kw in commands)
        self.assertFalse(self.hi_bill_by_tom in commands)

        commands.add(Command(self.hi, "bill"))
        self.assertEqual(len(commands), 1)

        commands.add(Command(self.hi, greeter="tom"))
        self.assertTrue(self.hi_bill in commands)
        self.assertTrue(self.hi_bill2 in commands)
        self.assertFalse(self.hi_bill_kw in commands)
        self.assertTrue(self.hi_by_tom in commands)
        self.assertFalse(self.hi_bill_by_tom in commands)

    def test_specify(self):
        base = Command(self.hi)
        self.assertEqual(base.specify("bill"), self.hi_bill)
        self.assertNotEqual(base.specify("bill"), self.hi_bill_kw)
        self.assertNotEqual(base.specify(person="bill"), self.hi_bill)
        self.assertEqual(base.specify(person="bill"), self.hi_bill_kw)
        self.assertEqual(base.specify(greeter="tom"), self.hi_by_tom)

        # we can specify repeatedly with multiple arguments at once...
        self.assertEqual(base.specify("bill", "tom"), self.hi_bill_by_tom)
        self.assertNotEqual(base.specify("bill", "tom"), self.hi_bill_by_tom_kw)
        self.assertNotEqual(base.specify(person="bill", greeter="tom"),
                            self.hi_bill_by_tom)
        self.assertEqual(base.specify(person="bill", greeter="tom"),
                         self.hi_bill_by_tom_kw)

        # ...or repeatedly chain the method if necessary
        self.assertEqual(base.specify("bill").specify("tom"), self.hi_bill_by_tom)
        self.assertEqual(base.specify(person="bill").specify(greeter="tom"),
                         self.hi_bill_by_tom_kw)
        # keyword arguments can be supplied in any order
        self.assertEqual(base.specify(greeter="tom").specify(person="bill"),
                         self.hi_bill_by_tom_kw)

        # applying a keyword argument again will override the argument
        hi_by_matt = self.hi_by_tom.specify(greeter="matt")
        self.assertNotEqual(hi_by_matt, self.hi_by_tom)
        self.assertEqual(hi_by_matt, Command(self.hi, greeter="matt"))

# defining some test CharacterClasses
class Human(char.Character):
    """base class for all humans"""
    equip_slots = ["Head", "Right Hand"]

    # overriding the default constructor to use a list
    # instead of an asyncio.Queue for messages
    # this will make it easier for testing
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.msgs = []

    def message(self, msg):
        self.msgs.append(msg)

    # some commands for testing
    # this comman will be overriden in base classes
    @Command
    def hit(self, args):
        """hit an enemy"""
        self.message("You hit an enemy")

class Soldier(Human):
    """a soldier class"""

    command_label = "Soldier Abilities"
    # overriding Human.hit
    @Command
    def hit(self, args):
        """hit an enemy"""
        self.message("You punch an enemy")

    @Command
    def call(self, args):
        """call to a friend"""
        self.message("You call to your friend")

class Bureaucrat(Human):
    """a different kind of human class"""

    # overriding Human.hit
    @Command
    def hit(self, args):
        """strike an enemy"""
        self.message("You raise an enemy's taxes")

class Commander(Soldier, Bureaucrat):
    """inherits from both soldier and bureaucrat"""

    # overriding Human.call
    @Command
    def call(self, args):
        """epic battle cry"""
        self.message("Hold the line!")

class Slug(char.Character):
    """a non-human base class"""

class AlphaSlug(Slug):
    """a class derived from Slug"""

class TestFilter(unittest.TestCase):
    """basic testcase for the pervasive Filter class"""

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
        """test that repr(Filter) works as expected"""
        filt = char.Filter(mode=False)
        self.assertEqual(repr(filt),
                         "Filter(False, set(), set(), set())")
        filt = char.Filter(mode=True)
        self.assertEqual(repr(filt),
                         "Filter(True, set(), set(), set())")
        filt = char.Filter(False, [Slug, AlphaSlug])
        # testing further is difficult due to set order changing

    def test_mode(self):
        """test that __init__'s mode keyword works as expected"""
        # creating a whitelist and blacklist with strings
        whitelist = char.Filter(mode="whitelist")
        blacklist = char.Filter(mode="blacklist")
        self.assertEqual(self.filter_test(whitelist), self.no_chars)
        self.assertEqual(self.filter_test(blacklist), self.all_chars)
        # creating a whitelist and blacklist with booleans
        whitelist = char.Filter(mode=True)
        blacklist = char.Filter(mode=False)
        self.assertEqual(self.filter_test(whitelist), self.no_chars)
        self.assertEqual(self.filter_test(blacklist), self.all_chars)
        # creating a whitelist and blacklist with enum values
        whitelist = char.Filter(char.Filter.WHITELIST)
        blacklist = char.Filter(char.Filter.BLACKLIST)
        self.assertEqual(self.filter_test(whitelist), self.no_chars)
        self.assertEqual(self.filter_test(blacklist), self.all_chars)

    def test_include_classes(self):
        """test that including CharacterClasses allows them through"""
        whitelist = char.Filter(mode="whitelist")
        whitelist.include(AlphaSlug)
        # only AlphaSlugs are allowed through
        expected = self.no_chars.copy()
        expected[self.vloobuk] = True
        expected[AlphaSlug] = True
        self.assertEqual(self.filter_test(whitelist), expected)
        # test that AlphaSlug was added to the set
        self.assertEqual(whitelist._classes, {AlphaSlug})
        # now all soldier and soldier-derived classes should be permited
        whitelist.include(Soldier)
        expected[self.chad] = True
        expected[self.zeke] = True
        expected[self.dwight] = True
        expected[Soldier] = True
        expected[Commander] = True
        self.assertEqual(self.filter_test(whitelist), expected)
        # test that Soldier was added to the set
        self.assertEqual(whitelist._classes, {AlphaSlug, Soldier})

        # now test including with a blacklist
        blacklist = char.Filter(mode="blacklist")
        blacklist.include(AlphaSlug)
        expected = self.all_chars.copy()
        # it's a blacklist, and nobody was excluded, so all are permitted
        self.assertEqual(self.filter_test(blacklist), expected)
        # no classes should be added to set
        self.assertEqual(blacklist._classes, set())

    def test_exclude_classes(self):
        """test that excluding CharacterClasses does not allow them through"""
        whitelist = char.Filter(mode="whitelist")
        # excluding a class from a whitelist should have no effect
        # since whitelists only track included classes
        whitelist.exclude(Human)
        expected = self.no_chars.copy()
        self.assertEqual(self.filter_test(whitelist), expected)
        # no classes should be added to set
        self.assertEqual(whitelist._classes, set())

        # now testing a blacklist
        blacklist = char.Filter(mode="blacklist")
        blacklist.exclude(AlphaSlug)
        expected = self.all_chars
        expected[self.vloobuk] = False
        expected[AlphaSlug] = False
        self.assertEqual(self.filter_test(blacklist), expected)
        # AlphaSlug should be added to set
        self.assertEqual(blacklist._classes, {AlphaSlug})
        # excluding another class
        blacklist.exclude(Bureaucrat)
        expected[self.bill] = False
        expected[self.dwight] = False
        expected[Bureaucrat] = False
        expected[Commander] = False
        self.assertEqual(self.filter_test(blacklist), expected)
        # Bureaucrat should be added to set
        self.assertEqual(blacklist._classes, {AlphaSlug, Bureaucrat})

    def test_whitelist_chars(self):
        """including/excluding Characters should overrides any class
        permissions for whitelists"""
        whitelist = char.Filter(mode="whitelist")
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
        self.assertEqual(whitelist._classes, {Soldier})
        self.assertEqual(set(whitelist._include_chars), set())
        self.assertEqual(set(whitelist._exclude_chars), {self.dwight})
        # now include dwight
        whitelist.include(self.dwight)
        expected[self.dwight] = True
        self.assertEqual(self.filter_test(whitelist), expected)
        self.assertEqual(whitelist._classes, {Soldier})
        self.assertEqual(set(whitelist._include_chars), {self.dwight})
        self.assertEqual(set(whitelist._exclude_chars), set())
        # now exclude the Soldier class
        whitelist.exclude(Soldier)
        expected = self.no_chars.copy()
        expected[self.dwight] = True
        self.assertEqual(self.filter_test(whitelist), expected)
        self.assertEqual(whitelist._classes, set())
        self.assertEqual(set(whitelist._include_chars), {self.dwight})
        self.assertEqual(set(whitelist._exclude_chars), set())

    def test_blacklist_chars(self):
        """including/excluding Characters should overrides any class
        permissions for blacklists"""
        blacklist = char.Filter(mode="blacklist")
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
        self.assertEqual(blacklist._classes, {Slug})
        self.assertEqual(set(blacklist._include_chars), {self.bloog})
        self.assertEqual(set(blacklist._exclude_chars), {self.vloobuk})
        # now include the Slug class in general again
        blacklist.include(Slug)
        expected[Slug] = True
        expected[AlphaSlug] = True
        expected[self.plubb] = True
        self.assertEqual(self.filter_test(blacklist), expected)
        self.assertEqual(blacklist._classes, set())
        self.assertEqual(set(blacklist._include_chars), {self.bloog})
        self.assertEqual(set(blacklist._exclude_chars), {self.vloobuk})
        # now include vloobuk and exclude bloog
        blacklist.include(self.vloobuk)
        blacklist.exclude(self.bloog)
        expected[self.vloobuk] = True
        expected[self.bloog] = False
        self.assertEqual(self.filter_test(blacklist), expected)
        self.assertEqual(blacklist._classes, set())
        self.assertEqual(set(blacklist._include_chars), {self.vloobuk})
        self.assertEqual(set(blacklist._exclude_chars), {self.bloog})


# some test locations
TEST_ROOM = loc.Location("Room", "This is just a room for testing.")
TEST_OUT = loc.Location("Outside", "This room is outside.")
TEST_EXIT = loc.Exit(TEST_OUT, "out", ["outside", "test out"])
TEST_ROOM.add_exit(TEST_EXIT)

# some test items
class Coin(item.Item):
    """a simple coin"""


class HealthPotion(item.Item):
    """a health potion with vary strength"""
    def __init__(self, hp):
        self.hp = 5

    @classmethod
    def load(cls, data):
        return cls(data["hp"])

    def save(self):
        return {"hp": 5}


class Potion(item.Item):
    """simple Usable item"""

    def on_use(self, char, args):
        char.message(f"used potion")


class TestApparel(item.Equippable):
    """a base class for other test equippables"""

    target = inv.EquipTarget("Head")

    def on_equip(self, char):
        char.message(f"equip {self}")

    def on_unequip(self, char):
        char.message(f"unequip {self}")


class Hat(TestApparel):
    target = inv.EquipTarget("Head")


class Helmet(TestApparel):
    target = inv.EquipTarget("Head")


class Sword(TestApparel):
    target = inv.EquipTarget("Right Hand")


class Mace(TestApparel):
    target = inv.EquipTarget("Right Hand")


class Bow(TestApparel):
    target = inv.EquipTarget("Left hand")


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
        self.ref = inv.EquipTarget.make_dict(*Human.equip_slots)

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
        self.ref[inv.EquipTarget("Right Hand")] = sword, False
        self.assertEqual(self.finn.equip_dict, self.ref)
        # item's equip method should be called
        self.assertEqual(self.finn.msgs[-1], "equip Sword")

        # try to equip an item that cannot be equipped
        self.finn.equip(HealthPotion(5), False)
        self.assertEqual(self.finn.msgs.pop(),
                         "Health Potion cannot be equipped.")

        # try to equip an item for which we don't have proper slots
        self.finn.equip(Bow(), False)
        self.assertEqual(self.finn.msgs[-1],
                         "Cannot equip item Bow to Left hand.")


        # try to equip a hat, but this time pull it from the inventory
        hat = Hat()
        self.finn.equip(hat, True)
        self.assertEqual(self.finn.msgs.pop(),
                         "Cannot equip Hat-not found in inventory.")
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
        self.ref[inv.EquipTarget("Head")] = hat, True
        self.assertEqual(self.finn.equip_dict, self.ref)
        # item's equip method should be called
        self.assertEqual(self.finn.msgs[-1], "equip Hat")

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
        self.ref[inv.EquipTarget("Right Hand")] = mace, False
        self.assertEqual(self.finn.equip_dict, self.ref)
        # item's equip method should be called
        self.assertEqual(self.finn.msgs[-1], "equip Mace")

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
        self.finn.unequip(inv.EquipTarget("Foo"))
        self.assertEqual(self.finn.msgs.pop(),
                         "Human does not possess equip slot 'Foo'.")

        # unequip the item in the "Head" slot
        self.finn.unequip(inv.EquipTarget("head"))
        # hat should not be added to inventory since from_inv=False
        self.assertEqual(self.finn.inv, inv.Inventory())
        # equip dict should be updated
        ref[inv.EquipTarget("head")] = None
        self.assertEqual(self.finn.equip_dict, ref)
        # item's equip method should be called
        self.assertEqual(self.finn.msgs[-1], "unequip Hat")

        # unequip the item in the "Right Hand" slot
        self.finn.unequip(inv.EquipTarget("right hand"))
        # mace should be added to inventory since from_inv=False
        self.assertEqual(self.finn.inv, inv.Inventory((Mace(), 1)))
        # equip dict should be updated
        ref[inv.EquipTarget("right hand")] = None
        self.assertEqual(self.finn.equip_dict, ref)
        # item's equip method should be called
        self.assertEqual(self.finn.msgs[-1], "unequip Mace")

        # try to unequip from an empty slot
        self.finn.unequip(inv.EquipTarget("hEAD"))
        self.assertEqual(self.finn.msgs.pop(),
                         "No item equipped on target Head.")


class Scout(Soldier):
    """a class for Command inheritance testing"""

    # the method names are different, but the Command
    # names are the same... method should be overriden
    @Command.with_traits("hit")
    def do_hit(self, args):
        """poison an enemy"""
        self.message("You poison an enemy")


    # this should NOT override the previous command
    # since the Command decorator was not used
    def call(self, args):
        """this should not be the help message"""
        self.message("You should not see this message")


class TestCommandInheritance(unittest.TestCase):
    """test that characters are initialized with proper commands"""

    def setUp(self):
        # note that this default will require special treatment,
        # since real Characters use an asyncio.Queue for their
        # messages, not a list
        self.default = char.Character("default")
        self.human = Human("tim")
        self.soldier = Soldier("max")
        self.bureaucrat = Bureaucrat("thaddeus")
        self.commander = Commander("george")
        self.scout = Scout("edward")

    def tearDown(self):
        self.default.despawn()
        self.human.despawn()
        self.soldier.despawn()
        self.bureaucrat.despawn()
        self.commander.despawn()
        self.scout.despawn()

    def test_cmd(self):
        """test that all inherited commands work as expected"""
        # default Character should not have access to hit
        self.default.command("hit")
        self.assertEqual(self.default.msgs.get_nowait(),
                         "Command 'hit' not recognized.")
        with self.assertRaises(AttributeError):
            self.default.hit(["hit"])
        # all other CharacterClasses should have some form of hit available
        self.human.command("hit")
        self.assertEqual(self.human.msgs.pop(), "You hit an enemy")
        self.human.hit(["hit"])
        self.assertEqual(self.human.msgs.pop(), "You hit an enemy")
        self.soldier.command("hit")
        self.assertEqual(self.soldier.msgs.pop(), "You punch an enemy")
        self.soldier.hit(["hit"])
        self.assertEqual(self.soldier.msgs.pop(), "You punch an enemy")
        self.bureaucrat.command("hit")
        self.assertEqual(self.bureaucrat.msgs.pop(),
                         "You raise an enemy's taxes")
        self.bureaucrat.hit(["hit"])
        self.assertEqual(self.bureaucrat.msgs.pop(),
                         "You raise an enemy's taxes")
        # commander should inherit from soldier, which is earlier in MRO
        self.commander.command("hit")
        self.assertEqual(self.commander.msgs.pop(), "You punch an enemy")
        self.commander.hit(["hit"])
        self.assertEqual(self.commander.msgs.pop(), "You punch an enemy")
        self.scout.command("hit")
        self.assertEqual(self.scout.msgs.pop(), "You poison an enemy")
        self.scout.do_hit(["hit"])
        self.assertEqual(self.scout.msgs.pop(), "You poison an enemy")

        # default Character, Human, and Bureaucrat should not have access to call
        self.default.command("call")
        self.assertEqual(self.default.msgs.get_nowait(),
                         "Command 'call' not recognized.")
        with self.assertRaises(AttributeError):
            self.default.call(["call"])
        self.human.command("call")
        self.assertEqual(self.human.msgs.pop(),
                         "Command 'call' not recognized.")
        with self.assertRaises(AttributeError):
            self.human.call(["call"])
        self.bureaucrat.command("call")
        self.assertEqual(self.bureaucrat.msgs.pop(),
                         "Command 'call' not recognized.")
        with self.assertRaises(AttributeError):
            self.bureaucrat.call(["call"])
        # all other CharacterClasses should have some form of 'hit' available
        self.soldier.command("call")
        self.assertEqual(self.soldier.msgs.pop(), "You call to your friend")
        self.soldier.call(["call"])
        self.assertEqual(self.soldier.msgs.pop(), "You call to your friend")
        self.commander.command("call")
        self.assertEqual(self.commander.msgs.pop(), "Hold the line!")
        self.commander.call(["call"])
        self.assertEqual(self.commander.msgs.pop(), "Hold the line!")
        self.scout.command("call")
        self.assertEqual(self.scout.msgs.pop(), "You call to your friend")
        self.scout.call(["call"])
        self.assertEqual(self.scout.msgs.pop(), "You should not see this message")

    def test_cmd_help(self):
        """test that help entries are generated properly"""
        self.assertEqual(self.human.hit.help_entry(),
                         "hit [from Human Commands]:\nhit an enemy")
        self.assertEqual(self.soldier.hit.help_entry(),
                         "hit [from Soldier Abilities]:\nhit an enemy")
        # try from the command dict, just to be safe
        self.assertEqual(self.soldier.cmd_dict["hit"].help_entry(),
                         "hit [from Soldier Abilities]:\nhit an enemy")
        self.assertEqual(self.bureaucrat.hit.help_entry(),
                         "hit [from Bureaucrat Commands]:\nstrike an enemy")
        self.assertEqual(self.commander.hit.help_entry(),
                         "hit [from Soldier Abilities]:\nhit an enemy")
        self.assertEqual(self.scout.do_hit.help_entry(),
                         "hit [from Scout Commands]:\npoison an enemy")
        self.assertEqual(self.scout.cmd_dict["hit"].help_entry(),
                         "hit [from Scout Commands]:\npoison an enemy")

        self.assertEqual(self.soldier.call.help_entry(),
                         "call [from Soldier Abilities]:\ncall to a friend")
        # try from the command dict, just to be safe
        self.assertEqual(self.soldier.cmd_dict["call"].help_entry(),
                         "call [from Soldier Abilities]:\ncall to a friend")
        self.assertEqual(self.commander.call.help_entry(),
                         "call [from Commander Commands]:\nepic battle cry")
        with self.assertRaises(AttributeError):
            self.scout.call.help_entry() # call method is not a Command
        self.assertEqual(self.scout.cmd_dict["call"].help_entry(),
                         "call [from Soldier Abilities]:\ncall to a friend")


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
        self.phil.command("help")
        self.assertEqual(self.phil.msgs.get_nowait(),
                         "---Default Commands---\n"
                         "help look say go equip unequip pickup drop inv use")

        # using help with other commands should produce their docstring
        self.phil.command("help help")
        help_msg = self.phil.msgs.get_nowait()
        # check that help message agrees with the CommandDict
        self.assertEqual(help_msg, self.phil.cmd_dict["help"].help_entry())
        self.assertEqual(help_msg,
                         "help [from Default Commands]:\n"
                         "Show relevant help information for a particular command.\n"
                         "usage: help [command]\n"
                         "If no command is supplied, a list of all commands is shown.")
        self.phil.command("help say")
        help_msg = self.phil.msgs.get_nowait()
        self.assertEqual(help_msg,
                         "say [from Default Commands]:\n"
                         "Send a message to all players in your current"
                         " location.\nusage: say [msg]\nNote that you can drop"
                         " the 'say' and just type your message\n"
                         'in quotes:\n"Hello, how are you?"')
        # invalid command should cause an error
        self.phil.command("help invalid_cmd")
        help_msg = self.phil.msgs.get_nowait()
        self.assertEqual(help_msg, "Command 'invalid_cmd' not recognized.")

    def test_say(self):
        """test that the say command works properly"""
        # test with a simple message
        self.bill.command("say hey, what's up?")
        self.assertEqual(self.bill.msgs,
                         ["Bill the Human: hey, what's up?"])
        self.assertEqual(qlist(self.phil.msgs),
                         ["Bill the Human: hey, what's up?"])
        self.bill.msgs.clear()
        # we have to use special function since default Character has
        # has an asyncio.Queue() instead of a list
        qclear(self.phil.msgs)
        self.bill.command("say spam")
        self.bill.command("say spam")
        self.bill.command("say spam")
        self.assertEqual(self.bill.msgs,
                         ["Bill the Human: spam"] * 3)
        self.assertEqual(qlist(self.phil.msgs),
                         ["Bill the Human: spam"] * 3)
        self.bill.msgs.clear()
        qclear(self.phil.msgs)
        # empty messages should not be sent
        self.bill.command("say")
        self.assertEqual(self.bill.msgs, [])
        self.assertEqual(qlist(self.phil.msgs), [])
        self.bill.command("say      ")
        self.assertEqual(self.bill.msgs, [])
        self.assertEqual(qlist(self.phil.msgs), [])
        # consecutive spaces will be treated as one separator
        self.bill.command("say  whoops   extra  spaces")
        self.assertEqual(self.bill.msgs,
                         ["Bill the Human: whoops extra spaces"])
        self.assertEqual(qlist(self.phil.msgs),
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
        self.assertEqual(qlist(self.phil.msgs),
                         ["Bill left through exit 'outside'."])
        self.assertEqual(qlist(self.dana.msgs), ["Bill entered."])
        self.assertTrue(self.bill.location is TEST_OUT)
        self.tearDown()
        self.setUp()
        self.bill.command("go out")
        self.assertEqual(self.bill.msgs, [])
        self.assertEqual(qlist(self.phil.msgs),
                         ["Bill left through exit 'out'."])
        self.assertEqual(qlist(self.dana.msgs), ["Bill entered."])
        self.assertTrue(self.bill.location is TEST_OUT)
        self.tearDown()
        self.setUp()
        self.bill.command("go test  out")
        self.assertEqual(self.bill.msgs, [])
        self.assertEqual(qlist(self.phil.msgs),
                         ["Bill left through exit 'test out'."])
        self.assertEqual(qlist(self.dana.msgs), ["Bill entered."])
        self.assertTrue(self.bill.location is TEST_OUT)

    def test_go_filtered(self):
        """test that 'go' command respects Filters"""
        # set interact for exit to an empty whitelist
        # i.e. nobody is allowed through
        TEST_EXIT.interact = char.Filter(mode=True)
        self.bill.command("go outside")
        self.assertEqual(self.bill.msgs, ["Exit 'outside' is inaccessible to you."])
        self.assertEqual(qlist(self.phil.msgs), [])
        self.assertEqual(qlist(self.dana.msgs), [])
        self.assertTrue(self.bill.location is TEST_ROOM)
        self.bill.msgs.clear()
        # set perceive for exit to an empty whitelist
        # i.e. nobody can see this exit or go through now
        # so Bill should not be informed that this exit even exists
        TEST_EXIT.perceive = char.Filter(mode=True)
        self.bill.command("go outside")
        self.assertEqual(self.bill.msgs, ["No exit with name 'outside'."])
        self.assertEqual(qlist(self.phil.msgs), [])
        self.assertEqual(qlist(self.dana.msgs), [])
        self.assertTrue(self.bill.location is TEST_ROOM)
        self.bill.msgs.clear()
        # BUT, if we set interact to empty blacklist (allowing anyone in)
        # Bill should be allowed through, even though he can't see the exit
        TEST_EXIT.interact = char.Filter(mode=False)
        self.bill.command("go outside")
        self.assertEqual(self.bill.msgs, [])
        self.assertEqual(qlist(self.phil.msgs),
                         ["Bill left through exit 'outside'."])
        self.assertEqual(qlist(self.dana.msgs), ["Bill entered."])
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
        mace, from_inv = self.bill.equip_dict[inv.EquipTarget("Right Hand")]
        self.assertTrue(isinstance(mace, Mace))
        self.assertTrue(from_inv)
        # now we cannot equip the mace again, because it cannot be found
        self.bill.command("equip mace")
        self.assertEqual(self.bill.msgs.pop(),
                         "Could not find item 'mace'.")
        # mace should still be equipped
        mace, from_inv = self.bill.equip_dict[inv.EquipTarget("Right Hand")]
        self.assertTrue(isinstance(mace, Mace))
        self.assertTrue(from_inv)
        # try equipping a sword
        self.bill.command("equip sword")
        self.assertEqual(self.bill.msgs, [
            "unequip Mace",
            "equip Sword"
        ])
        self.bill.msgs.clear()
        sword, from_inv = self.bill.equip_dict[inv.EquipTarget("Right Hand")]
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
        ref[inv.EquipTarget("head")] = None
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
        ref[inv.EquipTarget("right hand")] = None
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

    def test_cmd_use(self):
        self.bill.command("use potion")
        self.assertEqual(self.bill.msgs.pop(),
                         "Could not find item 'potion' to use.")
        self.bill.add_item(Potion())
        self.bill.command("use potion")
        self.assertEqual(self.bill.msgs.pop(),
                         "used potion")


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
            "Welcome to our SwampyMud! You are a Human",
            "What should we call you?"
        ])
        self.new_player.msgs.clear()
        self.assertEqual(self.bill.msgs, [])
        self.assertTrue(self.new_player._parser == self.new_player._join_parser)

        # test the different error messages
        self.new_player.command("name with spaces")
        self.assertEqual(self.new_player.msgs.pop(), "Names must be alphanumeric.")
        self.new_player.command("name_with_underscores")
        self.assertEqual(self.new_player.msgs.pop(), "Names must be alphanumeric.")
        self.new_player.command("43243-2144;")
        self.assertEqual(self.new_player.msgs.pop(), "Names must be alphanumeric.")
        self.new_player.command("")
        self.assertEqual(self.new_player.msgs, [])
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
