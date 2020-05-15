import unittest
from swampymud.util.biject import Biject

class TestBiject(unittest.TestCase):
    '''test case for bijection'''

    def setUp(self):
        self.empty = Biject()
        self.hundred_dict = {x: x*100 for x in range(10)}
        self.hundred_biject = Biject(self.hundred_dict)
        self.greek = Biject()
        self.greek["alpha"] = "a"
        self.greek["beta"] = "b"
        self.greek["mu"] = "m"

    def test_len(self):
        self.assertEqual(len(self.empty), 0)
        self.assertEqual(len(self.greek), 3)

    def test_repr(self):
        self.assertEqual(repr(self.empty), "Biject()")
        self.assertEqual(repr(self.hundred_biject),
                         "Biject(%r)" % self.hundred_dict)

    def test_get(self):
        self.assertEqual(self.greek["beta"], "b")
        self.assertEqual(self.greek["a"], "alpha")
        self.assertEqual(self.hundred_biject[200], 2)
        # should fail due to not key not being in the biject
        with self.assertRaises(KeyError):
            self.greek["lambda"]

    def test_set(self):
        self.greek["lambda"] = "l"
        self.assertEqual(self.greek["l"], "lambda")
        self.assertEqual(self.greek["lambda"], "l")
        # should fail since value is already in Biject
        with self.assertRaises(ValueError):
            self.greek["alpha"] = "A"
        # should fail since value is already in Biject
        with self.assertRaises(ValueError):
            self.hundred_biject[100] = 3
        # setting the same value over again should be fine
        self.greek["lambda"] = "l"

    def test_del(self):
        del self.greek["mu"]
        # cannot get the value
        with self.assertRaises(KeyError):
            self.greek["m"]
        # cannot delete the value
        with self.assertRaises(KeyError):
            del self.greek["m"]
        # cannot get the value
        with self.assertRaises(KeyError):
            self.greek["mu"]
        # cannot delete the value
        with self.assertRaises(KeyError):
            del self.greek["mu"]
        # can now set the value
        self.greek["mu"] = "M"

    def test_contains(self):
        self.assertFalse("x" in self.empty)
        self.assertTrue("beta" in self.greek)
        self.assertTrue("b" in self.greek)