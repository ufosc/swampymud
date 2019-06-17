import unittest
import util

class TestMisc(unittest.TestCase):
    '''Test Case for miscelleneous functions in the util module'''

    def test_camel_to_space(self):
        self.assertEqual(util.camel_to_space("CamelCaseClass"), "Camel Case Class")
        self.assertEqual(util.camel_to_space("Gandalf"), "Gandalf")
        self.assertEqual(util.camel_to_space("frodo"), "frodo")
    
    def test_group_and_count(self):
        self.assertEqual(util.group_and_count(["apple", "apple", "banana", "cap", "cap", "cap"]),
                        "apple\t[2]\nbanana\ncap\t[3]")
        self.assertEqual(util.group_and_count(range(3)), "0\n1\n2")
        test3 = util.group_and_count(
            ["apple", "apple", "banana", "cap", "cap", "cap"],
            format="%s: %i", single_format="%s: 0", sep=", "
        )
        self.assertEqual(test3, "apple: 2, banana: 0, cap: 3")
