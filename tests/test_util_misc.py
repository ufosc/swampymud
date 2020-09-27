import unittest
from swampymud import util, location, character as char
from swampymud.item import Item
from swampymud.util import find

class TestMisc(unittest.TestCase):
    '''Test Case for miscelleneous functions in the util module'''

    def test_camel_to_space(self):
        self.assertEqual(util.camel_to_space("CamelCaseClass"), "Camel Case Class")
        self.assertEqual(util.camel_to_space("Gandalf"), "Gandalf")
        self.assertEqual(util.camel_to_space("frodo"), "frodo")

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


# creating items for find testing
class SilverCoin(Item):
    """example of a Miscellaneous Item"""
    def __repr__(self):
        return "SilverCoin()"


class HealthPotion(Item):
    def __init__(self, hp):
        self.hp = hp

    def on_use(self, char, args):
        pass

    @classmethod
    def load(types, data):
        return types(data["hp"])

    def save(self):
        return {"hp": self.hp}

    def __repr__(self):
        return "HealthPotion(%s)" % self.hp


class TestFind(unittest.TestCase):

    def test_error_handling(self):
        """Test that util.find properly checks its arguments"""
        return
        obj = location.Location("test", "")
        msg = ("util.find() names argument should be a str or "
               "iterable of strings, (received type '{}')")

        # this should work
        find(obj, name="foo")
        # this should fail since the provided name is an int
        with self.assertRaises(TypeError, msg=msg.format("<class 'int'>")):
            find(obj, name=3)

        # multiple strings
        find(obj, name=["foo", "bar"])
        find(obj, name={"foo", "bar"})
        with self.assertRaises(TypeError, msg=msg.format("<class 'float'>")):
            find(obj, name=["foo", 3.4])

        msg = ("util.find() types argument should be a type or "
               "iterable of types, (received value '{}')")
        find(obj, name="foo", type=str)
        find(obj, name="foo", type=(str, float))
        find(obj, name="foo", type={str, float})
        with self.assertRaises(TypeError, msg=msg.format("<class 'int'>")):
            find(obj, type=3)
        with self.assertRaises(TypeError, msg=msg.format("<class 'str'>")):
            find(obj, type=(str, "float"))

        find(obj, maxdepth=3)
        msg = ("util.find() maxdepth argument must be int or float, received "
               "type '{}'")
        with self.assertRaises(TypeError, msg=msg.format("<class 'str'>")):
            find(obj, type=(str, "float"))

        # can provide must_have arguments
        find(obj, must_have={"foo": "bar"})
        msg = ("util.find() optional argument must be dict, received "
               "type '{}'")
        with self.assertRaises(TypeError, msg=msg.format("<class 'int'>")):
            find(obj, must_have=3)


    def test_find_location(self):
        """Test that util.find works with locations.
        (Implictly tests that Location.find_child works.)
        """
        shopkeep = char.Character("Bill")
        # the drunkard is named "outside" for some reason
        drunkard = char.Character("Outside")
        guest = char.Character("Matt")

        tavern = location.Location("Tavern", "A cool tavern")
        outside = location.Location("Outside", "It's muddy.")
        basement = location.Location("Tavern Basement",
                                     "This is where he stores the ale.")
        upstairs = location.Location("Tavern Upstairs",
                                     "There is a comfy bed for guests.")
        safe_room = location.Location("Tavern Safe Room",
                                      "Room only shopkeep knows about.")
        exit_list = [
            location.Exit(
                outside, "out", ["outside"]
            ),
            # only shopkeeper allowed downstairs
            location.Exit(
                basement, "basement", ["downstairs"],
                interact=char.Filter("whitelist", include_chars=[shopkeep])
            ),
            # only the guest and the shopkeeper allowed upstairs
            location.Exit(
                upstairs, "upstairs", ["up"],
                interact=char.Filter("blacklist", exclude_chars=[drunkard])
            ),
            # only the shopkeeper can see the safe_room, but others
            # can interact if they know about it
            location.Exit(
                safe_room, "safe room", ["safe"],
                perceive=char.Filter("whitelist", include_chars=[shopkeep])
            )
        ]
        for ex in exit_list:
            tavern.add_exit(ex)
        tavern.add_char(shopkeep)
        tavern.add_char(drunkard)
        tavern.add_char(guest)

        self.maxDiff = 3000
        # just doing a generic find should yield everything in the location
        self.assertCountEqual(find(tavern),
                              exit_list + [shopkeep, drunkard, guest])
        # providing a depth less than 0 should give us no items
        self.assertCountEqual(find(tavern, maxdepth=-1), [])

        # can we filter by type?
        self.assertCountEqual(find(tavern, type=location.Exit),
                              exit_list)
        self.assertCountEqual(find(tavern, type=char.Character),
                              [shopkeep, guest, drunkard])
        self.assertCountEqual(find(tavern, type=(char.Character,
                                                  location.Exit)),
                              exit_list + [shopkeep, drunkard, guest])

        # can we look by name?
        self.assertCountEqual(find(tavern, name="outside"),
                             [exit_list[0], drunkard])
        self.assertCountEqual(find(tavern, name="outside",
                                   type=location.Exit),
                             [exit_list[0]])
        # name and type
        self.assertCountEqual(find(tavern, name="outside",
                                   type=location.Exit),
                             [exit_list[0]])
        self.assertCountEqual(find(tavern, name="up"),
                             [exit_list[2]])
        self.assertCountEqual(find(tavern, name="safe"),
                             [exit_list[3]])
        self.assertCountEqual(find(tavern, name="bill"),
                             [shopkeep])
        # testing that all the permissions checking works as expected
        self.assertCountEqual(find(tavern, name="bill", pov=shopkeep),
                             [shopkeep])
        # shopkeeper can see all the exits
        self.assertCountEqual(find(tavern, type=location.Exit, pov=shopkeep),
                              exit_list)
        self.assertCountEqual(find(tavern, type=location.Exit, pov=drunkard),
                              [exit_list[0], exit_list[3]])
        self.assertCountEqual(find(tavern, type=location.Exit, pov=guest),
                              [exit_list[0], exit_list[2], exit_list[3]])

        # now adding some items
        tavern.add_item(HealthPotion(1))
        tavern.add_item(HealthPotion(1))
        tavern.add_item(HealthPotion(5))
        tavern.add_item(SilverCoin())
        tavern.add_item(SilverCoin())
        tavern.add_item(SilverCoin())
        items = [(HealthPotion(1), 2), (HealthPotion(5), 1), (SilverCoin(), 3)]

        # directly comparing items is hard, so we will serialize them first
        self.assertEqual(10, len(find(tavern)))

        # helper function to make comparing items easier
        def item_list(i_list):
            return [(item.save(), c) for (item, c) in i_list]

        self.assertCountEqual(
            item_list(find(tavern, type=Item)),
            item_list(items)
        )
        self.assertCountEqual(
            item_list(find(tavern, name="Health Potion")),
            item_list([(HealthPotion(1), 2), (HealthPotion(5), 1)])
        )
        self.assertCountEqual(
            item_list(find(tavern, hp=1)),
            item_list([(HealthPotion(1), 2)])
        )
