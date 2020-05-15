import unittest
from swampymud.util.shadowdict import ShadowDict

class TestShadowdict(unittest.TestCase):

    def setUp(self):
        self.empty = ShadowDict()
        self.starter_dict = {
            "wizard": "gandalf",
            "thief": "frodo",
            "archer": "legolas"
        }
        self.party = ShadowDict(self.starter_dict)

    def test_get_set_del_empty(self):
        self.empty["test"] = 1
        self.assertEqual(self.empty["test"], 1)
        self.empty["test"] = 2
        self.assertEqual(self.empty["test"], 2)
        del self.empty["test"]
        self.assertEqual(self.empty["test"], 1)
        del self.empty["test"]
        with self.assertRaises(KeyError):
            self.empty["test"]
        with self.assertRaises(KeyError):
            del self.empty["test"]

    def test_get_set_del_party(self):
        # check that the party has all the right starting members
        self.assertEqual(self.party["wizard"], "gandalf")
        self.assertEqual(self.party["thief"], "frodo")
        self.assertEqual(self.party["archer"], "legolas")
        # assign a new wizard, "gandalf" should be shadowed
        self.party["wizard"] = "dumbledore"
        # check that we have all the party members, including the new wizard
        self.assertEqual(self.party["wizard"], "dumbledore")
        self.assertEqual(self.party["thief"], "frodo")
        self.assertEqual(self.party["archer"], "legolas")
        # assign a new wizard and thief, with the old members being shadowed
        self.party["wizard"] = "merlin"
        self.party["thief"] = "springheel jack"
        # check the correct party members
        self.assertEqual(self.party["wizard"], "merlin")
        self.assertEqual(self.party["thief"], "springheel jack")
        self.assertEqual(self.party["archer"], "legolas")
        # try dimissing the current wizard and thief members...
        del self.party["wizard"]
        del self.party["thief"]
        # ...we should have the previous thief and wizard now
        self.assertEqual(self.party["wizard"], "dumbledore")
        self.assertEqual(self.party["thief"], "frodo")
        self.assertEqual(self.party["archer"], "legolas")
        # dimiss the party members again
        del self.party["wizard"]
        del self.party["thief"]
        # back to the original wizard (gandalf)
        self.assertEqual(self.party["wizard"], "gandalf")
        # we no longer have a thief, since we dismissed the original one
        with self.assertRaises(KeyError):
            self.party["thief"]
        # we should still have the original archer
        self.assertEqual(self.party["archer"], "legolas")
        # delete the wizard again
        del self.party["wizard"]
        # can't dismiss the thief, as we have none
        with self.assertRaises(KeyError):
            del self.party["thief"]
        # we no longer have a thief or wizard
        with self.assertRaises(KeyError):
            self.party["wizard"]
        with self.assertRaises(KeyError):
            self.party["thief"]
        # still have the original archer
        self.assertEqual(self.party["archer"], "legolas")

    def test_repr(self):
        self.assertEqual(repr(self.empty), "ShadowDict()")
        self.assertEqual(repr(self.party), "ShadowDict(%r)" % self.starter_dict)

    def test_len(self):
        self.assertEqual(len(self.empty), 0)
        self.assertEqual(len(self.party), 3)
        self.party["clown"] = "Lepuccio"
        self.assertEqual(len(self.party), 4)
        del self.party["wizard"]
        self.assertEqual(len(self.party), 3)
        self.party["thief"] = "madoff"
        self.assertEqual(len(self.party), 3)

    def test_iter(self):
        self.assertEqual(list(self.empty), [])
        self.assertEqual(list(self.party), ["wizard", "thief", "archer"])
        self.party["wizard"] = "dumbledore"
        self.assertEqual(list(self.party), ["wizard", "thief", "archer"])

    def test_items(self):
        self.assertEqual(list(self.empty.items()), [])
        self.assertEqual(list(self.party.items()), [("wizard", "gandalf"),
                                                    ("thief", "frodo"),
                                                    ("archer", "legolas")])
        self.party["wizard"] = "dumbledore"
        self.assertEqual(list(self.party.items()), [("wizard", "dumbledore"),
                                                    ("thief", "frodo"),
                                                    ("archer", "legolas")])

    def test_copy(self):
        self.copied = self.party.copy()
        self.assertEqual(self.copied._dict, {
                                             "wizard": ["gandalf"],
                                             "thief": ["frodo"],
                                             "archer": ["legolas"]
                                            })
        self.assertEqual(self.party._dict, {
                                             "wizard": ["gandalf"],
                                             "thief": ["frodo"],
                                             "archer": ["legolas"]
                                            })
        # should not effect the original dict
        self.copied["wizard"] = 0x0100
        self.assertEqual(self.copied._dict, {
                                             "wizard": ["gandalf", 0x0100],
                                             "thief": ["frodo"],
                                             "archer": ["legolas"]
                                            })
        self.assertEqual(self.party._dict, {
                                             "wizard": ["gandalf"],
                                             "thief": ["frodo"],
                                             "archer": ["legolas"]
                                            })
    def test_contains(self):
        self.assertFalse("meme" in self.empty)
        self.assertFalse("paladin" in self.party)
        self.assertTrue("wizard" in self.party)
        self.assertTrue("thief" in self.party)
        self.party["wizard"] = "gandalf"
        del self.party["thief"]
        self.assertTrue("wizard" in self.party)
        self.assertFalse("thief" in self.party)

    def test_remove_value(self):
        self.party["wizard"] = "dumbledore"
        self.assertEqual(self.party._dict, {
                                             "wizard": ["gandalf", "dumbledore"],
                                             "thief": ["frodo"],
                                             "archer": ["legolas"]
                                            })
        # remove the shadowed value "gandalf" with key "wizard"
        self.party.remove_value("wizard", "gandalf")
        self.assertEqual(self.party._dict, {
                                             "wizard": ["dumbledore"],
                                             "thief": ["frodo"],
                                             "archer": ["legolas"]
                                            })
        # removing the last value associated with a key
        # should remove the entire list
        # note that we can remove a value, even if it is already "exposed"
        self.party.remove_value("thief", "frodo")
        self.assertEqual(self.party._dict, {
                                             "wizard": ["dumbledore"],
                                             "archer": ["legolas"]
                                           })
        # expect a key error if provided a key that does not exist
        with self.assertRaises(KeyError):
            self.party.remove_value("knight", "lancelot")
        # expect a value error if the value is not in the dict,
        # but the key is
        with self.assertRaises(ValueError):
            self.party.remove_value("wizard", "merlin")
        # check that nothing was affected
        self.assertEqual(self.party._dict, {
                                             "wizard": ["dumbledore"],
                                             "archer": ["legolas"]
                                           })