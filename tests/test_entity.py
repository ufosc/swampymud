"""testcases for the entity module"""
import unittest
from swampymud import entity
import swampymud.character as char
from swampymud.location import Location


class TestEntityMeta(unittest.TestCase):
    """testcases for the basic guarantees of the entity class"""

    class DefaultCharacter(char.Character):
        """Slightly more convenient CharacterClass that stores messages
        in a list instead of a Queue for more straightforward testing.
        """
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.msgs = []

        def message(self, msg):
            self.msgs.append(msg)

    class CoolRobot(entity.Entity):
        pass

    class TalkingRobot(entity.Entity):
        """this robot can talk"""

        def on_message(self, msg):
            """give hostile replies to every message"""
            first_word = msg[:msg.find(" ")].upper()
            if not hasattr(self, "first_msg"):
                self.location.message(f"WHO ARE YOU, '{first_word}'?",
                                      exclude=[self])
                self.first_msg = False
            else:
                self.location.message(f"STOP TALKING TO ME, '{first_word}'.",
                                      exclude=[self])

        def on_exit(self, char):
            """make a snide remark to characters when they leave"""
            char.message(f"Don't bother coming back, '{char}'.".upper())

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

        def on_enter(self, char):
            """pleasantly greet characters when they walk in"""
            char.message(f"Nice to see you, {char}!")

        # we must override this method, to cancel out the effect of
        # TalkingRobot.on_exit
        def on_exit(self, char):
            pass

    class BrokenRobot(NiceRobot):
        @char.Command.with_traits(name="greet")
        def broken_greet(self, char, args):
            pass

        @char.Command
        def fix(self, char, args):
            pass

    def setUp(self):
        self.ship = Location("Discovery", "A quiet, humming spaceship.")
        self.room = Location("Private Quarters", "Your personal quarters.")
        self.bmo_room = Location("BMO's Room", "Where BMO lives.")
        self.dave = self.DefaultCharacter("Dave")
        self.hal = self.TalkingRobot()
        self.bmo = self.NiceRobot()
        self.dave.set_location(self.room)
        self.hal.set_location(self.ship)
        self.bmo.set_location(self.bmo_room)

    def tearDown(self):
        self.dave.despawn()
        self.hal.despawn()
        self.bmo.despawn()

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

    def test_on_enter(self):
        """test the Entity.on_enter trigger"""
        self.dave.set_location(self.bmo_room)
        self.assertEqual(self.dave.msgs, [
            "Nice to see you, Dave!"
        ])

        # go in and out again
        self.dave.set_location(self.room)
        self.dave.set_location(self.bmo_room)
        self.assertEqual(self.dave.msgs, [
            "Nice to see you, Dave!",
            "Nice to see you, Dave!"
        ])

        # what happens if we just set the location to itself?
        self.dave.set_location(self.bmo_room)
        self.assertEqual(self.dave.msgs, [
            "Nice to see you, Dave!",
            "Nice to see you, Dave!",
            "Nice to see you, Dave!"
        ])

    def test_on_exit(self):
        """test the Entity.on_exit trigger"""
        self.dave.set_location(self.ship)
        self.dave.set_location(self.room)
        self.assertEqual(self.dave.msgs, [
            "DON'T BOTHER COMING BACK, 'DAVE'."
        ])
        # now go in and out again
        self.dave.set_location(self.ship)
        self.dave.set_location(self.room)
        self.assertEqual(self.dave.msgs, [
            "DON'T BOTHER COMING BACK, 'DAVE'.",
            "DON'T BOTHER COMING BACK, 'DAVE'."
        ])

    def test_on_message(self):
        """test the Entity.on_message trigger"""
        dave = self.dave
        dave.set_location(self.ship)
        dave.command("say hello there")
        self.assertEqual(dave.msgs, [
            "Dave the Default Character: hello there",
            "WHO ARE YOU, 'DAVE'?"
        ])
        dave.msgs.clear()

        dave.command("say umm... I'm David Bowman? ")
        self.assertEqual(dave.msgs, [
            "Dave the Default Character: umm... I'm David Bowman?",
            "STOP TALKING TO ME, 'DAVE'."
        ])
        dave.msgs.clear()

        dave.command("say uh... ok then.")
        self.assertEqual(dave.msgs, [
            "Dave the Default Character: uh... ok then.",
            "STOP TALKING TO ME, 'DAVE'."
        ])
        dave.msgs.clear()
