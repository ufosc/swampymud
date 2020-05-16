"""testcases for the entity module"""
import unittest
from swampymud import entity
import swampymud.character as char


class TestEntityMeta(unittest.TestCase):
    """testcases for the basic guarantees of the entity class"""

    class CoolRobot(entity.Entity):
        pass

    class TalkingRobot(entity.Entity):
        """this robot can talk"""

    class AngryRobot(entity.Entity):
        """manually setting description"""
        description = """this robot is angry"""
        classname = "Angrytron2000"

    class NiceRobot(TalkingRobot):
        classname = "HAL"
        @char.Command
        def greet(self, char, args):
            pass

        @char.Command
        def smile(self, char, args):
            pass

    class BrokenRobot(NiceRobot):
        @char.Command.with_traits(name="greet")
        def broken_greet(self, char, args):
            pass

        @char.Command
        def fix(self, char, args):
            pass


    classes = [CoolRobot, TalkingRobot, AngryRobot, NiceRobot, BrokenRobot]
    def test_str(self):
        """test that str and classname work as expected"""
        self.assertEqual(list(map(str, self.classes)),
                         ["Cool Robot", "Talking Robot", "Angrytron2000",
                          "HAL", "Broken Robot"])

    def test_description(self):
        """test that description field is generated as expected"""
        descripts = map(lambda x: getattr(x, "description"), self.classes)
        self.assertEqual(list(descripts), [
            "[No description provided.]",
            "this robot can talk",
            "this robot is angry",
            "[No description provided.]",
            "[No description provided.]"
        ])

    def test_commands(self):
        """test that entity commands are inherited and initialized properly"""
        local_cmds = map(lambda x: getattr(x, "_local_commands"), self.classes)
        self.assertEqual(list(local_cmds), [
            {},
            {},
            {},
            {"greet" : self.NiceRobot.greet, "smile" : self.NiceRobot.smile},
            {"fix" : self.BrokenRobot.fix,
             "greet" : self.BrokenRobot.broken_greet},
        ])
        total_cmds = map(lambda x: getattr(x, "_commands"), self.classes)
        self.assertEqual(list(total_cmds), [
            {},
            {},
            {},
            {"greet" : self.NiceRobot.greet, "smile" : self.NiceRobot.smile},
            {"smile" : self.NiceRobot.smile, "fix" : self.BrokenRobot.fix,
             "greet" : self.BrokenRobot.broken_greet},
        ])
