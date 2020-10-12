"""unit tests for the swampymud.world module"""
import unittest
import importlib
import warnings
from swampymud import world as mudworld
from swampymud.character import CharacterClass
from swampymud.item import Item
from swampymud.location import Location
import swampymud.inventory as inv

def import_class(modname, classname):
    """function equivalent to from [mod] import [class]"""
    mod = importlib.import_module(modname)
    return getattr(mod, classname)

class TestLoad(unittest.TestCase):
    """test case for functions involving loading or parsing information"""

    def test_blank(self):
        """completely blank save should fail"""
        message = ("Received 'NoneType' instead of a dict in world file "
                   "'tests/saves/bad/blank.yaml'. (World files should contain "
                   "three sections: prelude, personae, tree.")

        with self.assertRaises(TypeError, msg=message):
            mudworld.read_worldfile('tests/saves/bad/blank.yaml')

    def test_unexpected(self):
        """test that unexpected fields are detected
        (unexpected fields should be detected before missing fields)"""
        msg = "Found unexpected section(s) {sects} in world file '{name}'"
        emsg = msg.format(sects=["groceries", "budget"],
                          name="bad_sections.yaml")
        with self.assertRaises(ValueError, msg=emsg):
            mudworld.read_worldfile("tests/saves/bad/bad_sections.yaml")

        emsg = msg.format(sects=["stocks"], name="unexpect_section.yaml")
        with self.assertRaises(ValueError, msg=emsg):
            mudworld.read_worldfile("tests/saves/bad/unexpect_section.yaml")

    def test_missing(self):
        """test that missing fields are detected"""
        msg = "Missing section(s) {lst} in world file 'tests/saves/bad/{name}'"
        emsg = msg.format(lst=["prelude"], name="missing_prelude.yaml")
        with self.assertRaises(ValueError, msg=emsg):
            mudworld.read_worldfile("tests/saves/bad/missing_prelude.yaml")


        emsg = msg.format(lst=["personae", "tree"],
                          name="missing_prelude.yaml")
        with self.assertRaises(ValueError, msg=emsg):
            mudworld.read_worldfile("tests/saves/bad/missing_2.yaml")

    def test_empty(self):
        """test a save file with 3 blank sections"""
        result = mudworld.read_worldfile('tests/saves/empty.yaml')
        self.assertEqual(result, {"prelude" : {}, "tree": {}, "personae": {}})

    def test_simple(self):
        """test loading a simple save"""
        self.maxDiff = 2000
        result = mudworld.read_worldfile('tests/saves/simple.yaml')
        expected = {
            "prelude": {
                "tests/script/basic_rpg.py": ["Wizard", "Warrior"],
                "tests/script/weapons.py": ["CursedRing"]
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
        self.assertEqual(mudworld.load_prelude({}),
                         {"Location": Location, "ItemStack": inv.ItemStack})

    def test_basic_import(self):
        """test a basic prelude with one file"""
        basic_prelude = {
            "tests/script/basic_rpg.py": ["Warrior", "Wizard", "HealthPotion"]
        }
        results = mudworld.load_prelude(basic_prelude)

        self.assertEqual(results, {
            "Location": Location,
            "ItemStack": inv.ItemStack,
            "Warrior": import_class("tests.script.basic_rpg", "Warrior"),
            "Wizard": import_class("tests.script.basic_rpg", "Wizard"),
            "HealthPotion":
                import_class("tests.script.basic_rpg", "HealthPotion")
        })


    def test_multi_import(self):
        """test an import with multiple files"""
        multi_prelude = {
            "tests/script/basic_rpg.py": ["HealthPotion", "DarkWizard", "Golem"],
            "tests/script/weapons.py": ["CursedRing", "WoodenStaff"]
        }
        classes = mudworld.load_prelude(multi_prelude)
        self.assertEqual(set(classes), set(["DarkWizard", "CursedRing",
                                            "HealthPotion", "WoodenStaff",
                                            "Golem", "Location", "ItemStack"]))

    def test_bad_class_import(self):
        """test if prelude fails with a class not one of the first-class types"""
        # note that golem riddle is not an CharClass, ItemClass, or EntityClass
        multi_prelude = {
            "tests/script/basic_rpg.py": ["HealthPotion", "DarkWizard", "GolemRiddle"],
            "tests/script/weapons.py": ["CursedRing", "WoodenStaff"]
        }
        with self.assertRaises(Exception):
            mudworld.load_prelude(multi_prelude)
        # prelude with invalid class should raise an exception
        prelude = {"tests/script/basic_rpg.py": ["HealthPotion", "Foo"]}
        with self.assertRaises(Exception):
            mudworld.load_prelude(prelude)


class TestPersonae(unittest.TestCase):
    """test case for personae-related functions"""

    def setUp(self):
        self.maxDiff = 1000
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
                "exits": [
                    {"name": "outside", "other_names": ["out"],
                     "destination": "$Boring House"}
                ]
            },
            "Abra": {"_type": "^Wizard", "name": "Abra"},
            "Grug": {"_type": "^Warrior", "name": "Grug"},
            "ring": {"_type": "^CursedRing"}
        }
        self.simple_classes = {
            "Location": Location,
            "Wizard": import_class("tests.script.basic_rpg", "Wizard"),
            "Warrior": import_class("tests.script.basic_rpg", "Warrior"),
            "CursedRing": import_class("tests.script.weapons", "CursedRing")
        }

    def test_check_types(self):
        """test that check_types filters out typeless objects"""
        warn_msg = "Object '{}' missing required field '_type'."
        unknown_msg = "Object '{}' has unknown type '{}'."
        type_names = {"Location": Location, "Item": Item}
        personae = {
            "good1": {"_type": "^Location", "name": "Tavern"},
            "good2": {"_type": "^Item", "value": 5},
            "unknown1": {"_type": "^Foo"},
            "unknown2": {"_type": "^ItEm"},
            # whoops, forgot a '^'
            "unknown3": {"_type": "Location"},
            # these items have no type
            "bad1": {"name": "Basement"},
            "bad2": {},
            # whoops, put 'type' instead of '_type'
            "bad3": {"type": "Foo"}
        }
        # first, check without checking if the types exist
        with warnings.catch_warnings(record=True) as warn_list:
            filtered = mudworld.check_types(personae)
        # bad objects should be filtered
        self.assertEqual(set(filtered), {
            "good1", "good2", "unknown1", "unknown2", "unknown3"
        })
        self.assertEqual([str(warn.message) for warn in warn_list], [
            warn_msg.format("bad1"),
            warn_msg.format("bad2"),
            (warn_msg.format("bad3") +
             " (Did you add a 'type' field instead of '_type'?)"),
            "Skipped 3 objects. (Unknown type.)"
        ])

        # now check with a valid set of type_names
        with warnings.catch_warnings(record=True) as warn_list:
            filtered = mudworld.check_types(personae, type_names=type_names)
        self.assertEqual(set(filtered), {"good1", "good2"})

        self.assertEqual([str(warn.message) for warn in warn_list], [
            unknown_msg.format('unknown1', 'Foo'),
            unknown_msg.format('unknown2', 'ItEm'),
            (unknown_msg.format('unknown3', 'ocation') +
             " (Did you remember to put '^' in front of your type?)"),
            warn_msg.format("bad1"),
            warn_msg.format("bad2"),
            (warn_msg.format("bad3") +
             " (Did you add a 'type' field instead of '_type'?)"),
            "Skipped 6 objects. (Unknown type.)"
        ])

    def test_check_symbols(self):
        # running a correct personae through check_symbols produces
        # no warnings and leaves all the fields intact
        with warnings.catch_warnings(record=True) as warn_list:
            checked = mudworld.check_symbols(self.simple,
                                             obj_names=self.simple,
                                             type_names=self.simple_classes)
        self.assertEqual(warn_list, [])
        self.assertEqual(self.simple, checked)

        # now add an unknown field to Abra
        checked["Abra"]["friend"] = "$Kadabra"
        with warnings.catch_warnings(record=True) as warn_list:
            checked = mudworld.check_symbols(checked,
                                             obj_names=self.simple,
                                             type_names=self.simple_classes)
        # field should be removed
        self.assertEqual(checked, self.simple)
        self.assertEqual([str(warn.message) for warn in warn_list], [
            "Unknown object symbol '$Kadabra'.",
            "Omitted 1 field(s). (Bad symbol.)"
        ])

        bad_type = {
            "sack": {
                "_type": "^ItemStack",
                "item_type": "^Gold",
                "amount": 3
            }
        }
        type_names = { "ItemStack": inv.ItemStack }
        with warnings.catch_warnings(record=True) as warn_list:
            checked = mudworld.check_symbols(bad_type, set(), type_names)
        del bad_type["sack"]["item_type"]
        self.assertEqual(checked, bad_type)
        self.assertEqual([str(warn.message) for warn in warn_list], [
            "Unknown type symbol '^Gold'.",
            "Omitted 1 field(s). (Bad symbol.)"
        ])

        # now check an example with several bad symbols
        social_types = {
            "Person": import_class("tests.script.social", "Person")
        }
        personae = {
            "John": {
                "_type": "^Person",
                "friends": [
                    "$MaRy",
                    "$Jane",
                    "$Bill"
                ],
                "spouse": "$Jane"
            },
            "Jane": {
                "_type": "^Whoops",
                "friends": [
                    "$Mary",
                    "$Bill",
                    "$Zach"
                ],
                "spouse": "$John"
            },
            "Bill": {
                "_type": "^Person",
                "spouse": "$imaginary"
            },
            "Mary": {
                "_type": "^Person",
                "friends": [
                    "$Jane"
                ],
                "nested": [
                    {"nested": "$bad_symbol"},
                    {"nested": "$Mary"}
                ]
            }
        }
        with warnings.catch_warnings(record=True) as warn_list:
            checked = mudworld.check_symbols(personae,
                                             obj_names=personae,
                                             type_names=social_types)
        # delete the wrong fields from personae
        personae["John"]["friends"].remove("$MaRy")
        del personae["Jane"]["_type"]
        personae["Jane"]["friends"].remove("$Zach")
        del personae["Bill"]["spouse"]
        del personae["Mary"]["nested"][0]["nested"]
        self.assertEqual(checked, personae)
        self.assertCountEqual([str(warn.message) for warn in warn_list], [
            "Unknown object symbol '$MaRy'.",
            "Unknown type symbol '^Whoops'.",
            "Unknown object symbol '$Zach'.",
            "Unknown object symbol '$imaginary'.",
            "Unknown object symbol '$bad_symbol'.",
            "Omitted 5 field(s). (Bad symbol.)"
        ])




    def test_skim_empty(self):
        """test that no locations are skimmed from empty personae"""
        self.assertEqual(mudworld.skim_for_locations(self.empty), {})

    def test_skim_warn(self):
        """test that skim_locations warns on bad locations"""
        warn_msg = ("Location '{}' missing required field '{}'. "
                    "All locations must provide a name and description.")
        locations = {
            'correct': {'_type': '^Location',
                        'description': 'Patrons are grumbling about their day '
                                       'over a few pints.',
                        'name': 'Tavern'},
            'wrong': {'_type': '^Location', 'name': 'Basement'}
        }
        with warnings.catch_warnings(record=True) as warn_list:
            result = mudworld.skim_for_locations(locations)
        # should only load unaffected Location
        self.assertEqual(len(result), 1)
        self.assertEqual(str(result['correct']), "Tavern")
        # should produce 2 warnings
        self.assertEqual([str(warn.message) for warn in warn_list], [
            warn_msg.format('wrong', 'description'),
            "Skipped 1 Location(s)."
        ])

        # only location 4 and 5 should succeed here
        locations = {
            'loc1': {'_type': '^Location', 'description': 'meme'},
            'loc2': {'_type': '^Location', 'name': 'meme'},
            'loc3': {'_type': '^Location'},
            'loc4': {'_type': '^Location', 'description': 'y', 'name': 'x'},
            'loc5': {'_type': '^Location', 'description': 'bar', 'name': 'foo'}
        }

        with warnings.catch_warnings(record=True) as warn_list:
            result = mudworld.skim_for_locations(locations)
        # should only load unaffected Location
        self.assertEqual(len(result), 2)
        self.assertEqual(str(result['loc4']), "x")
        self.assertEqual(str(result['loc5']), "foo")
        # should produce 4 warnings (3 specific + 1 summary)
        self.assertEqual([str(warn.message) for warn in warn_list], [
            warn_msg.format('loc1', 'name'),
            warn_msg.format('loc2', 'description'),
            warn_msg.format('loc3', 'name'),
            "Skipped 3 Location(s)."
        ])

    def test_skim_simple(self):
        """test that simple locations are constructed after a skim"""
        locations = mudworld.skim_for_locations(self.simple)
        # indirectly test the locations,
        # since we don't have a way of checking equality for Locations
        boring_house = locations["Boring House"]
        self.assertEqual(boring_house.name, "Boring House")
        self.assertEqual(boring_house.description, "A house with four walls and a roof.")
        self.assertTrue(isinstance(boring_house, Location))
        # exits are not loaded in when the locations are skimmed
        self.assertEqual(len(boring_house._exit_list), 0)

        interior = locations["Boring House Interior"]
        self.assertEqual(interior.name, "Boring House Interior")
        self.assertEqual(interior.description, "There is a chair. The walls are brown.")
        self.assertTrue(isinstance(interior, Location))
        # exits are not loaded in when the locations are skimmed
        self.assertEqual(len(interior._exit_list), 0)

    def test_load_simple(self):
        """test loading in the 'simple' personae example"""
        symbols = mudworld.load_personae(self.simple, self.simple_classes)
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
        self.assertEqual(len(boring_house._exit_list), 1)
        inside = boring_house._exit_list[0]
        self.assertTrue(inside.destination is interior)
        self.assertEqual(set(inside.names), set(("inside",)))

        self.assertEqual(len(interior._exit_list), 1)
        outside = interior._exit_list[0]
        self.assertTrue(outside.destination is boring_house)
        self.assertEqual(set(outside.names), set(("outside", "out")))

    def test_load_after_skim_simple(self):
        locations = {
            "Boring House":
                Location("Boring House", "A house with four walls and a roof."),
            "Boring House Interior":
                Location("Boring House Interior", "There is a chair. The walls are brown.")
        }
        # load the personae with the skimmed locations
        symbols = mudworld.load_personae(self.simple,
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
        self.assertEqual(len(boring_house._exit_list), 1)
        inside = boring_house._exit_list[0]
        self.assertTrue(inside.destination is interior)
        self.assertEqual(set(inside.names), set(("inside",)))
        self.assertEqual(str(inside), "inside")
        self.assertEqual(inside.view(), "inside -> Boring House Interior")

        self.assertEqual(len(interior._exit_list), 1)
        outside = interior._exit_list[0]
        self.assertTrue(outside.destination is boring_house)
        self.assertEqual(set(outside.names), set(("outside", "out")))

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
            # adding an interact filter that allows only Wizards and MrCool
            "interact": {
                "mode": "whitelist",
                "classes": ["^Wizard"],
                "include_chars": ["$MrCool"],
            },
            # forbid warriors from seeing the exit
            "perceive": {
                "mode": "blacklist",
                "classes": ["^Warrior"]
            }
        }
        self.simple["Boring House Interior"]["exits"].append(exit_data)
        # adding a character named MrCool
        # MrCool is not a Wizard but he can see the exit
        self.simple["MrCool"] = {"_type": "^Warrior"}

        symbols = mudworld.load_personae(self.simple, self.simple_classes)
        secret_exit = None
        for loc_exit in symbols["Boring House Interior"].exits:
            if "bookshelf" in loc_exit.names:
                secret_exit = loc_exit
        if secret_exit is None:
            raise Exception("Secret Exit not added properly")
        self.assertTrue(secret_exit.destination is symbols["Secret Room"])
        grug = symbols["Grug"]
        mrcool = symbols["MrCool"]
        abra = symbols["Abra"]
        # test that the character.Filter is properly working
        self.assertTrue(secret_exit.interact.permits(mrcool))
        self.assertTrue(secret_exit.interact.permits(abra))
        self.assertFalse(secret_exit.interact.permits(grug))
        self.assertFalse(secret_exit.perceive.permits(mrcool))
        self.assertTrue(secret_exit.perceive.permits(abra))
        self.assertFalse(secret_exit.perceive.permits(grug))


class TestTree(unittest.TestCase):
    """test case for all tree-loading functions"""

    maxDiff = 10000
    def setUp(self):
        self.simple_classes = {
            "Wizard": import_class("tests.script.basic_rpg", "Wizard"),
            "Warrior": import_class("tests.script.basic_rpg", "Warrior"),
            "CursedRing": import_class("tests.script.weapons", "CursedRing")
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
        mudworld.load_tree({}, {}, {})

    def test_simple_tree(self):
        """test that load_tree can load in a simple tree"""
        mudworld.load_tree(self.simple_tree, self.simple_objs, {})

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
        self.Warrior = import_class("tests.script.basic_rpg", "Warrior")
        self.Wizard = import_class("tests.script.basic_rpg", "Wizard")
        self.CursedRing = import_class("tests.script.weapons", "CursedRing")

    def test_simple(self):
        """should successfully load in a simple world"""
        world = mudworld.World.from_file("tests/saves/simple.yaml")

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


class TestLocationScripts(unittest.TestCase):
    """integration tests for scripts that call mudscript.import_location"""

    def test_bad_location_import(self):
        """bad location imports should produce a KeyError"""
        with self.assertRaises(KeyError, msg="Cannot access location 'Epic Castle'"
                               " (no locations with that name)"):
            mudworld.World.from_file("tests/saves/bad/bad_loc_import.yaml")


    def test_good_location_import(self):
        """a valid location import should work properly"""
        world = mudworld.World.from_file("tests/saves/simple_import.yaml")
        # import the dark_lord module
        mod = importlib.import_module("tests.script.simple_import")
        # the locations in the module should be loaded directly
        # from the world
        self.assertTrue(mod.HOUSE is world.locations["Boring House"])
        self.assertTrue(mod.INTERIOR is \
                        world.locations["Boring House Interior"])

        # loading the world a second time will mess up the locations
        # this is because the modules have already been initalized,
        # thus the import_location statements are not called
        # PAY ATTENTION, THIS COULD CAUSE ERRORS
        world = mudworld.World.from_file("tests/saves/simple_import.yaml")
        self.assertFalse(mod.HOUSE is world.locations["Boring House"])
        self.assertFalse(mod.INTERIOR is \
                         world.locations["Boring House Interior"])



    def test_dark_lord(self):
        """test that the dark lord's abilities work (relies on
        functioning location, control, and character modules)
        """
        world = mudworld.World.from_file("tests/saves/dark_lord.yaml")
        # our two normal humans from the tavern
        human1, human2 = tuple(world.locations["Tavern"].characters)
        # get our evil dark_lord
        dark_lord = world.locations["tower"].characters[0]

        # move dark lord to the tavern
        dark_lord.set_location(world.locations["Tavern"])

        # now return to the castle
        dark_lord.cmd_retreat([])
        self.assertEqual(human1.msgs.get_nowait(),
                         "Vennicule disappeared in a plume of smoke!")
        self.assertEqual(human2.msgs.get_nowait(),
                         "Vennicule disappeared in a plume of smoke!")
        self.assertTrue(dark_lord in world.locations["tower"].characters)

        # now test the 'capture' command
        dark_lord.set_location(world.locations["Tavern"])
        dark_lord.cmd_capture(["capture", str(human1)])
        self.assertEqual(human1.msgs.get_nowait(),
                         "You have been captured!")
        self.assertTrue(human1 in world.locations["dungeon"].characters)
