import unittest
import mudworld as mudimport
from character import CharacterClass
from item import Item
from location import Location
from importlib import import_module

def import_class(modname, classname):
    '''function equivalent to from [mod] import [class]'''
    mod = import_module(modname)
    return getattr(mod, classname)

class TestLoad(unittest.TestCase):
    '''test case for functions involving loading or parsing information'''

    def test_blank(self):
        '''completely blank save should fail'''
        with self.assertRaises(Exception):
            mudimport.read_savefile('testing/test_saves/blank.yaml')
    
    def test_empty(self):
        '''test a save file with 3 blank sections'''
        result = mudimport.read_savefile('testing/test_saves/empty.yaml')
        self.assertEqual(result, {"prelude" : None, "tree": None, "personae": None})

    def test_simple(self):
        '''test loading a simple save'''
        result = mudimport.read_savefile('testing/test_saves/simple.yaml')
        expected = {
            "prelude": {
                "testing/script/basic_rpg.py": ["Wizard", "Warrior"],
                "testing/script/weapons.py": ["GoldenNugget"]
            },
            "personae": {
                "Boring House" : {
                    "_type": "Location",
                    "description": "A house with four walls and a roof.",
                    "exits": [{"name": "inside", "destination": "Boring House Interior"}]
                },
                "Boring House Interior" : {
                    "_type": "Location",
                    "description": "There is a chair. The walls are brown.",
                    "exits": [{"name": "outside", "destination": "Boring House"}]
                },
                "Abra": {"_type": "Wizard"},
                "Grug": {"_type": "Warrior"},
            },
            "tree": {
                "Boring House Interior": {
                    "Grug": None,
                    "Abra": None,
                }
            }
        }
        self.assertEqual(result, expected)
    

class TestPrelude(unittest.TestCase):
    '''test case for prelude-related functions'''

    def test_empty(self):
        '''test an empty prelude'''
        self.assertEqual(mudimport.load_prelude({}), {})

    def test_basic_import(self):
        '''test a basic prelude with one file'''
        basic_prelude = {
            "testing/script/basic_rpg.py": ["Warrior", "Wizard", "HealthPotion"]
        }
        results = mudimport.load_prelude(basic_prelude)

        self.assertEqual(set(results), set(["Warrior", "Wizard", "HealthPotion"]))

    def test_multi_import(self):
        '''test an import with multiple files'''
        multi_prelude = {
            "testing/script/basic_rpg.py": ["HealthPotion", "DarkWizard", "Golem"],
            "testing/script/weapons.py": ["CursedRing", "WoodenStaff"]
        }
        classes = mudimport.load_prelude(multi_prelude)
        self.assertEqual(set(classes), set(["DarkWizard", "CursedRing",
                                            "HealthPotion", "WoodenStaff",
                                            "Golem"]))
    
    def test_bad_class_import(self):
        '''test if prelude fails with a class not one of the first-class types'''
        # note that golem riddle is not an CharClass, ItemClass, or EntityClass
        multi_prelude = {
            "testing/script/basic_rpg.py": ["HealthPotion", "DarkWizard", "GolemRiddle"],
            "testing/script/weapons.py": ["CursedRing", "WoodenStaff"]
        }
        with self.assertRaises(Exception):
            mudimport.load_prelude(multi_prelude)
    
    #TODO: test with an invalid class name in a file
    #TODO: test loading a prelude with mudscript.get_location 
    

class TestPersonae(unittest.TestCase):
    '''test case for personae-related functions'''
    
    def setUp(self):
        self.empty = {}
        # up these as necessary
        self.simple = {
            "Boring House" : {
                "_type": "Location",
                "description": "A house with four walls and a roof.",
                "exits": [{"name": "inside", "destination": "Boring House Interior"}]
            },
            "Boring House Interior" : {
                "_type": "Location",
                "description": "There is a chair. The walls are brown.",
                "exits": [{"name": "outside", "other_names": ["out"], "destination": "Boring House"}]
            },
            "Abra": {"_type": "Wizard"},
            "Grug": {"_type": "Warrior"},
        }
        self.simple_classes = {
            "Location": Location,
            "Wizard": import_class("testing.script.basic_rpg", "Wizard"),
            "Warrior": import_class("testing.script.basic_rpg", "Warrior")
        }
        self.complex = {

        }

    def test_skim_empty(self):
        '''test that no locations are skimmed from empty personae'''
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
        '''test loading in the 'simple' personae example'''
        symbols = mudimport.load_personae(self.simple, self.simple_classes)
        # we expect 4 items from this personae
        self.assertEqual(len(symbols), 4)
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
                                starter=locations)
        
        # this should yield the same results, so the results below are copied

        # we expect 4 items from this personae
        self.assertEqual(len(symbols), 4)
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
        '''testing if charfilters are correctly loaded in'''
        # making a few modifications to the simple scenario
        # adding a secret room
        self.simple["Secret Room"] = {
            "_type": "Location",
            "description": "Maybe this house isn't boring after all!"
        }
        # adding an exit to the secret room
        exit_data = {
            "name": "bookshelf",
            "destination": "Secret Room",
            "hide_des": True,
            # adding an access filter that allows only Wizards and MrCool
            "access": {
                "mode": "whitelist",
                "classes": ["Wizard"],
                "include_chars": ["MrCool"],
            },
            # forbid warriors from seeing the exit
            "visibility": {
                "mode": "blacklist",
                "classes": ["Warrior"]
            }
        }
        self.simple["Boring House Interior"]["exits"].append(exit_data)
        # adding a character named MrCool
        # MrCool is not a Wizard but he can see the exit
        self.simple["MrCool"] = {"_type": "Warrior"}

        symbols = mudimport.load_personae(self.simple, self.simple_classes)
        secret_exit = None
        for loc_exit in symbols["Boring House Interior"].exits:
            if "bookshelf" in loc_exit:
                secret_exit = loc_exit
        if secret_exit is None:
            raise Exception("Secret Exit not added properly")
        self.assertTrue(secret_exit.destination is symbols["Secret Room"])
        print(secret_exit.visibility)
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
        