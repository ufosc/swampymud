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

    def test_to_base(self):
        '''test that to_base(int, base) works with several bases'''
        # test type checks work
        with self.assertRaises(TypeError):
            util.to_base("foo", 3)
        with self.assertRaises(TypeError):
            util.to_base(3, "foo")
        # test that negative num raises a value error
        with self.assertRaises(ValueError):
            util.to_base(-1, 10)
        # test that out of range base raises a value error
        with self.assertRaises(ValueError):
            util.to_base(42, 1)
        with self.assertRaises(ValueError):
            util.to_base(42, 69)
        test_values = [0, 32, 43243, 999999]
        # base 10 converstion should work just like str() method
        for value in test_values:
            self.assertEqual(util.to_base(value, 10), str(value))
        # conversion to base 2 should be fully reversible
        for value in test_values:
            converted = int(util.to_base(value, 2), base=2)
            self.assertEqual(converted, value)
        # conversion to base 36 should be fully reversible
        for value in test_values:
            converted = int(util.to_base(value, 36), base=36)
            self.assertEqual(converted, value)