import unittest
from importlib import import_module
import mudworld as mudimport
from character import CharacterClass
from item import Item
from location import Location
import inventory as inv

def import_class(modname, classname):
    """function equivalent to from [mod] import [class]"""
    mod = import_module(modname)
    return getattr(mod, classname)

class TestLoad(unittest.TestCase):
    """test case for functions involving loading or parsing information"""

    def test_blank(self):
        """completely blank save should fail"""
        with self.assertRaises(Exception):
            mudimport.read_worldfile('testing/test_saves/blank.yaml')

    def test_empty(self):
        """test a save file with 3 blank sections"""
        result = mudimport.read_worldfile('testing/test_saves/empty.yaml')
        self.assertEqual(result, {"prelude" : None, "tree": None, "personae": None})

    def test_simple(self):
        """test loading a simple save"""
        self.maxDiff = 2000
        result = mudimport.read_worldfile('testing/test_saves/simple.yaml')
        expected = {
            "prelude": {
                "testing/script/basic_rpg.py": ["Wizard", "Warrior"],
                "testing/script/weapons.py": ["CursedRing"]
            },
            "personae": {
                "Boring House" : {
                    "_type": "^Location",
                    "name": "Boring House",
                    "description": "A house with four walls and a roof.",
                    "exits": [{"name": "inside", "destination": "$Boring House Interior"}]
                },
                "Boring House Interior" : {
                    "_type": "^Location",
                    "name": "Boring House Interior",
                    "description": "There is a chair. The walls are brown.",
                    "exits": [{"name": "outside", "destination": "$Boring House"}]
                },
                "Abra": {"_type": "^Wizard", "name": "Abra"},
                "Grug": {"_type": "^Warrior", "name": "Grug"},
                "ring": {"_type": "^CursedRing"}
            },
            "tree": {
                "Boring House": "Grug",
                "Boring House Interior": {
                    "Abra": "ring"
                }
            }
        }
        self.assertEqual(result, expected)


class TestPrelude(unittest.TestCase):
    """test case for prelude-related functions"""

    def test_empty(self):
        """test an empty prelude"""
        self.assertEqual(mudimport.load_prelude({}), {})

    def test_basic_import(self):
        """test a basic prelude with one file"""
        basic_prelude = {
            "testing/script/basic_rpg.py": ["Warrior", "Wizard", "HealthPotion"]
        }
        results = mudimport.load_prelude(basic_prelude)

        self.assertEqual(set(results), set(["Warrior", "Wizard", "HealthPotion"]))

    def test_multi_import(self):
        """test an import with multiple files"""
        multi_prelude = {
            "testing/script/basic_rpg.py": ["HealthPotion", "DarkWizard", "Golem"],
            "testing/script/weapons.py": ["CursedRing", "WoodenStaff"]
        }
        classes = mudimport.load_prelude(multi_prelude)
        self.assertEqual(set(classes), set(["DarkWizard", "CursedRing",
                                            "HealthPotion", "WoodenStaff",
                                            "Golem"]))

    def test_bad_class_import(self):
        """test if prelude fails with a class not one of the first-class types"""
        # note that golem riddle is not an CharClass, ItemClass, or EntityClass
        multi_prelude = {
            "testing/script/basic_rpg.py": ["HealthPotion", "DarkWizard", "GolemRiddle"],
            "testing/script/weapons.py": ["CursedRing", "WoodenStaff"]
        }
        with self.assertRaises(Exception):
            mudimport.load_prelude(multi_prelude)
        # prelude with invalid class should raise an exception
        prelude = {"testing/script/basic_rpg.py": ["HealthPotion", "Foo"]}
        with self.assertRaises(Exception):
            mudimport.load_prelude(prelude)
        #TODO: test loading a prelude with mudscript.get_location


class TestPersonae(unittest.TestCase):
    """test case for personae-related functions"""

    def setUp(self):
        self.empty = {}
        # up these as necessary
        self.simple = {
            "Boring House" : {
                "_type": "^Location",
                "name": "Boring House",
                "description": "A house with four walls and a roof.",
                "exits": [{"name": "inside", "destination": "$Boring House Interior"}]
            },
            "Boring House Interior" : {
                "_type": "^Location",
                "name": "Boring House Interior",
                "description": "There is a chair. The walls are brown.",
                "exits": [{"name": "outside", "other_names": ["out"], "destination": "$Boring House"}]
            },
            "Abra": {"_type": "^Wizard", "name": "Abra"},
            "Grug": {"_type": "^Warrior", "name": "Grug"},
            "ring": {"_type": "^CursedRing"}
        }
        self.simple_classes = {
            "Location": Location,
            "Wizard": import_class("testing.script.basic_rpg", "Wizard"),
            "Warrior": import_class("testing.script.basic_rpg", "Warrior"),
            "CursedRing": import_class("testing.script.weapons", "CursedRing")
        }

    def test_skim_empty(self):
        """test that no locations are skimmed from empty personae"""
        self.assertEqual(mudimport.skim_for_locations(self.empty), {})

    def test_skim_simple(self):
        locations = mudimport.skim_for_locations(self.simple)
        # indirectly test the locations, since we don't have a way of checking equality for Locations
        boring_house = locations["Boring House"]
        self.assertEqual(boring_house.name, "Boring House")
        self.assertEqual(boring_house.description, "A house with four walls and a roof.")
        self.assertTrue(isinstance(boring_house, Location))
        # exits are not loaded in when the locations are skimmed
        self.assertEqual(len(boring_house.exits), 0)

        interior = locations["Boring House Interior"]
        self.assertEqual(interior.name, "Boring House Interior")
        self.assertEqual(interior.description, "There is a chair. The walls are brown.")
        self.assertTrue(isinstance(interior, Location))
        # exits are not loaded in when the locations are skimmed
        self.assertEqual(len(interior.exits), 0)

    #TODO: test_skim_complex

    def test_load_simple(self):
        """test loading in the 'simple' personae example"""
        symbols = mudimport.load_personae(self.simple, self.simple_classes)
        # we expect 5 items from this personae
        self.assertEqual(len(symbols), 5)
        # check the ring
        ring = symbols["ring"]
        self.assertEqual(str(ring.target), "Left hand")
        self.assertTrue(isinstance(ring, self.simple_classes["CursedRing"]))
        # check the characters
        grug = symbols["Grug"]
        self.assertTrue(isinstance(grug, self.simple_classes["Warrior"]))
        self.assertEqual(str(grug), "Grug")
        abra = symbols["Abra"]
        self.assertTrue(isinstance(abra, self.simple_classes["Wizard"]))
        self.assertEqual(str(abra), "Abra")

        # check the locations
        boring_house = symbols["Boring House"]
        interior = symbols["Boring House Interior"]
        self.assertEqual(boring_house.description,
                         "A house with four walls and a roof.")
        self.assertTrue(isinstance(boring_house, Location))
        self.assertEqual(interior.description,
                        "There is a chair. The walls are brown.")
        self.assertTrue(isinstance(interior, Location))

        # locations should be fully loaded, so they should have exits now
        self.assertEqual(len(boring_house.exits), 1)
        inside = boring_house.exits[0]
        self.assertTrue(inside.destination is interior)
        self.assertEqual(set(inside), set(("inside",)))

        self.assertEqual(len(interior.exits), 1)
        outside = interior.exits[0]
        self.assertTrue(outside.destination is boring_house)
        self.assertEqual(set(outside), set(("outside", "out")))

    def test_load_after_skim_simple(self):
        locations = {
            "Boring House":
                Location("Boring House", "A house with four walls and a roof."),
            "Boring House Interior":
                Location("Boring House Interior", "There is a chair. The walls are brown.")
        }
        # load the personae with the skimmed locations
        symbols = mudimport.load_personae(self.simple,
                                self.simple_classes,
                                obj_names=locations)

        # this should yield the same results, so the results below are copied

        # we expect 5 items from this personae
        self.assertEqual(len(symbols), 5)
        # check the ring
        ring = symbols["ring"]
        self.assertEqual(str(ring.target), "Left hand")
        self.assertTrue(isinstance(ring, self.simple_classes["CursedRing"]))
        # check the characters
        grug = symbols["Grug"]
        self.assertTrue(isinstance(grug, self.simple_classes["Warrior"]))
        self.assertEqual(str(grug), "Grug")
        abra = symbols["Abra"]
        self.assertTrue(isinstance(abra, self.simple_classes["Wizard"]))
        self.assertEqual(str(abra), "Abra")

        # check the locations
        boring_house = symbols["Boring House"]
        interior = symbols["Boring House Interior"]
        self.assertEqual(boring_house.description,
                         "A house with four walls and a roof.")
        self.assertTrue(isinstance(boring_house, Location))
        self.assertEqual(interior.description,
                        "There is a chair. The walls are brown.")
        self.assertTrue(isinstance(interior, Location))

        # locations should be fully loaded, so they should have exits now
        self.assertEqual(len(boring_house.exits), 1)
        inside = boring_house.exits[0]
        self.assertTrue(inside.destination is interior)
        self.assertEqual(set(inside), set(("inside",)))
        self.assertEqual(str(inside), "inside -> Boring House Interior")

        self.assertEqual(len(interior.exits), 1)
        outside = interior.exits[0]
        self.assertTrue(outside.destination is boring_house)
        self.assertEqual(set(outside), set(("outside", "out")))

    def test_char_filter(self):
        """testing if charfilters are correctly loaded in"""
        # making a few modifications to the simple scenario
        # adding a secret room
        self.simple["Secret Room"] = {
            "_type": "^Location",
            "name": "Secret Room",
            "description": "Maybe this house isn't boring after all!"
        }
        # adding an exit to the secret room
        exit_data = {
            "name": "bookshelf",
            "destination": "$Secret Room",
            "hide_des": True,
            # adding an access filter that allows only Wizards and MrCool
            "access": {
                "mode": "whitelist",
                "classes": ["^Wizard"],
                "include_chars": ["$MrCool"],
            },
            # forbid warriors from seeing the exit
            "visibility": {
                "mode": "blacklist",
                "classes": ["^Warrior"]
            }
        }
        self.simple["Boring House Interior"]["exits"].append(exit_data)
        # adding a character named MrCool
        # MrCool is not a Wizard but he can see the exit
        self.simple["MrCool"] = {"_type": "^Warrior"}

        symbols = mudimport.load_personae(self.simple, self.simple_classes)
        secret_exit = None
        for loc_exit in symbols["Boring House Interior"].exits:
            if "bookshelf" in loc_exit:
                secret_exit = loc_exit
        if secret_exit is None:
            raise Exception("Secret Exit not added properly")
        self.assertTrue(secret_exit.destination is symbols["Secret Room"])
        grug = symbols["Grug"]
        mrcool = symbols["MrCool"]
        abra = symbols["Abra"]
        # test that the CharFilter is properly working
        self.assertTrue(secret_exit.access.permits(mrcool))
        self.assertTrue(secret_exit.access.permits(abra))
        self.assertFalse(secret_exit.access.permits(grug))
        self.assertFalse(secret_exit.visibility.permits(mrcool))
        self.assertTrue(secret_exit.visibility.permits(abra))
        self.assertFalse(secret_exit.visibility.permits(grug))


class TestTree(unittest.TestCase):
    """test case for all tree-loading functions"""

    maxDiff = 10000
    def setUp(self):
        self.simple_classes = {
            "Wizard": import_class("testing.script.basic_rpg", "Wizard"),
            "Warrior": import_class("testing.script.basic_rpg", "Warrior"),
            "CursedRing": import_class("testing.script.weapons", "CursedRing")
        }
        self.simple_objs = {
            "Boring House":
                Location("Boring House", "A house with four walls and a roof."),
            "Boring House Interior":
                Location("Boring House Interior",
                         "There is a chair. The walls are brown."),
            "Abra": self.simple_classes["Wizard"]("Abra"),
            "Grug": self.simple_classes["Warrior"]("Grug"),
            "ring": self.simple_classes["CursedRing"]()
        }
        self.simple_tree = {
            "Boring House": {
                "Grug": None
            },
            "Boring House Interior": {
                "Abra": {
                    "ring": None
                }
            }
        }

    def test_empty(self):
        """should load in an empty tree without issue"""
        mudimport.load_tree({}, {}, {})

    def test_simple_tree(self):
        """test that load_tree can load in a simple tree"""
        mudimport.load_tree(self.simple_tree, self.simple_objs, {})

        abra = self.simple_objs["Abra"]
        grug = self.simple_objs["Grug"]
        ring = self.simple_objs["ring"]
        house = self.simple_objs["Boring House"]
        interior = self.simple_objs["Boring House Interior"]

        # check that abra and grug are in the proper places
        self.assertEqual([abra], list(interior.characters))
        self.assertEqual([grug], list(house.characters))

        # no entities should have been added to the houses
        self.assertEqual([], list(house.entities))
        self.assertEqual([], list(interior.entities))

        # grug should have nothing in his inventory
        self.assertEqual([], list(grug.inv))
        # abra should have one thing (the cursed ring)
        self.assertEqual(abra.inv, inv.Inventory(
            (self.simple_classes["CursedRing"](), 1)
        ))


class TestWorld(unittest.TestCase):
    """testcase for the 'World' class, which integrates all the functionality
    above"""
    maxDiff = 10000
    def setUp(self):
        self.Warrior = import_class("testing.script.basic_rpg", "Warrior")
        self.Wizard = import_class("testing.script.basic_rpg", "Wizard")
        self.CursedRing = import_class("testing.script.weapons", "CursedRing")

    def test_simple(self):
        """should successfully load in a simple world"""
        world = mudimport.World.from_file("testing/test_saves/simple.yaml")

        self.assertEqual(set(world.locations),
                         set(("Boring House", "Boring House Interior")))
        house = world.locations["Boring House"]
        interior = world.locations["Boring House Interior"]

        # should be only 1 character in house.characters, Grug
        grug, = tuple(house.characters)
        self.assertTrue(isinstance(grug, self.Warrior))
        # grug's inventory should be empty
        self.assertEqual(list(grug.inv), [])

        # should be only 1 character in interior.characters, Abra
        abra, = tuple(interior.characters)
        self.assertTrue(isinstance(abra, self.Wizard))
        # should be only 1 item in abra's inventory, the ring
        ring, = tuple(abra.inv.stacks())
        self.assertEqual(ring, inv.ItemStack.from_item(self.CursedRing(), 1))

        # test that the exits are working
        # interior should only have 1 exit, to the outside
        outside, = tuple(interior.exits)
        self.assertTrue(outside.destination is house)
        # house should only have 1 exit, to the inside
        inside, = tuple(house.exits)
        self.assertTrue(inside.destination is interior)
