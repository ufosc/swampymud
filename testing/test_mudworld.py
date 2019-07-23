import unittest
import mudworld as mudimport
from character import CharacterClass
from item import Item


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
            "testing/script/weapons.py": ["CursedRing", "WoodenBow"]
        }
        classes = mudimport.load_prelude(multi_prelude)
        self.assertEqual(set(classes), set(["DarkWizard", "CursedRing", 
                                            "HealthPotion", "WoodenBow", 
                                            "Golem"]))
    
    def test_bad_class_import(self):
        # note that golem riddle is not an CharClass, ItemClass, or EntityClass
        multi_prelude = {
            "testing/script/basic_rpg.py": ["HealthPotion", "DarkWizard", "GolemRiddle"],
            "testing/script/weapons.py": ["CursedRing", "WoodenBow"]
        }
        with self.assertRaises(Exception):
            mudimport.load_prelude(multi_prelude)
    

    #TODO: test loading a prelude with mudscript.get_location 
    

class TestPersonae(unittest.TestCase):
    '''test case for personae-related functions'''

    def setUp(self):
        pass
    
    def test_empty_personae(self):
        pass
