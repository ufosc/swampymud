import unittest
import swampymud.location as loc

class TestExit(unittest.TestCase):

    def setUp(self):
        self.wizard_world = loc.Location("Wizard World", "You see magic people.")
        self.magic_portal = loc.Exit(self.wizard_world, "portal",
                                     other_names=["magic portal", "magic"])
        self.magic_door = loc.Exit(self.wizard_world, "door",
                                   other_names=["magic door"],
                                   hide_des=True)

    def test_repr(self):
        # sorting of the other_names is not guaranteed,
        # so we use a regex that can detect either pattern
        regex=r"Exit\(Location\('Wizard World', 'You see magic people.'\), "\
              r"'portal', other_names=\[(('magic portal', 'magic')|('magic', 'magic portal'))\], "\
              r"interact=Filter\(False, set\(\), set\(\), set\(\)\), "\
              r"perceive=Filter\(False, set\(\), set\(\), set\(\)\)\)"
        self.assertRegex(repr(self.magic_portal), regex)

    def test_exit_str(self):
        self.assertEqual(str(self.magic_portal), "portal")
        self.assertEqual(str(self.magic_door), "door")

    def test_exit_view(self):
        self.assertEqual(self.magic_portal.view(), "portal -> Wizard World")
        self.assertEqual(self.magic_door.view(), "door")


class TestLocationExits(unittest.TestCase):

    def setUp(self):
        self.normal_world = loc.Location("Normal World", "You see less magic people.")
        self.wizard_world = loc.Location("Wizard World", "You see magic people.")
        self.magic_portal = loc.Exit(self.wizard_world, "portal",
                                     other_names=["magic portal", "magic"])
        self.magic_door = loc.Exit(self.wizard_world, "door",
                                   other_names=["magic door"])
        self.redundant_portal = loc.Exit(self.wizard_world, "redundant portal", ["portal"])

    def test_add_exit(self):
        self.normal_world.add_exit(self.magic_portal)
        self.assertEqual(list(self.normal_world.exits), [self.magic_portal])
        self.normal_world.add_exit(self.magic_door)
        self.assertEqual(list(self.normal_world.exits), [self.magic_portal, self.magic_door])

    def test_add_redundant(self):
        self.normal_world.add_exit(self.magic_portal)
        with self.assertRaisesRegex(AssertionError, ".*already has exit with name 'portal'"):
            self.normal_world.add_exit(self.redundant_portal)