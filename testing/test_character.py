"""module testing the Character class"""
import unittest
import control as con
import character as char
import location as loc

class EntryPlug(con.Controller):
    """simple controller for programmatic use"""
    def __init__(self, character):
        super().__init__()
        self.assume_control(character)
        self.last_cmd = None
        self.msgs = []

    def __repr__(self):
        return f"EntryPlug{self.receiver}"

    def command(self, cmd):
        """add a command and update the receiver to respond"""
        self.last_cmd = cmd
        self.receiver.update()

    def read_cmd(self):
        """return the stored command, set to None"""
        cmd, self.last_cmd = self.last_cmd, None
        return cmd

    def has_cmd(self):
        """returns true if command is available"""
        return self.last_cmd is not None

    def write_msg(self, msg):
        """write [msg] back to the controller"""
        self.msgs.append(msg)

    def has_msg(self):
        """returns true if messages are available"""
        return bool(self.msgs)
        
TEST_ROOM = loc.Location("Room", "This is just a room for testing.")
TEST_OUT = loc.Location("Outside", "This room is outside.")
TEST_EXIT = loc.Exit(TEST_OUT, "out", ["outside", "test out"])
TEST_ROOM.add_exit(TEST_EXIT)

class TestDefaultCommands(unittest.TestCase):
    """test that all the default Character commands work properly"""
    def setUp(self):
        self.room = loc.Location("Room", "This is just a room for testing.")
        self.bill = char.Character("Bill")
        self.bill.set_location(TEST_ROOM)
        self.billcon = EntryPlug(self.bill)
        self.phil = char.Character("Phil")
        self.phil.set_location(TEST_ROOM)
        self.philcon = EntryPlug(self.phil)
        self.dana = char.Character("Dana")
        self.dana.set_location(TEST_OUT)
        self.danacon = EntryPlug(self.dana)

    def tearDown(self):
        self.bill.die()
        self.phil.die()

    def test_help(self):
        """test for the help command"""
        # using help by itself should produce a list of commands
        self.billcon.command("help")
        self.assertEqual(self.billcon.msgs.pop(), self.bill.cmd_dict.help())

        # using help with other commands should produce their docstring
        self.billcon.command("help help")
        help_msg = self.billcon.msgs.pop()
        # check that help message agrees with the CommandDict
        self.assertEqual(help_msg, self.bill.cmd_dict.get_cmd("help").help())
        self.assertEqual(help_msg,
                         "Show relevant help information for a particular command.\n"
                         "usage: help [command]\n"
                         "If no command is supplied, a list of all commands is shown.")
        self.billcon.command("help say")
        help_msg = self.billcon.msgs.pop()
        self.assertEqual(help_msg,
                         "Say a message aloud, sent to all players in your "
                         "current locaton.\nusage: say [msg]")
        # invalid command should cause an error
        self.billcon.command("help invalid_cmd")
        help_msg = self.billcon.msgs.pop()
        self.assertEqual(help_msg, "Command 'invalid_cmd' not recognized.")

    def test_say(self):
        """test that the say command works properly"""
        # test with a simple message
        self.billcon.command("say hey, what's up?")
        self.assertEqual(self.billcon.msgs,
                         ["Bill the Default Character: hey, what's up?"])
        self.assertEqual(self.philcon.msgs,
                         ["Bill the Default Character: hey, what's up?"])
        self.billcon.msgs.clear()
        self.philcon.msgs.clear()
        self.billcon.command("say spam")
        self.billcon.command("say spam")
        self.billcon.command("say spam")
        self.assertEqual(self.billcon.msgs,
                         ["Bill the Default Character: spam"] * 3)
        self.assertEqual(self.philcon.msgs,
                         ["Bill the Default Character: spam"] * 3)
        self.billcon.msgs.clear()
        self.philcon.msgs.clear()
        # empty messages should not be sent
        self.billcon.command("say")
        self.assertEqual(self.billcon.msgs, [])
        self.assertEqual(self.philcon.msgs, [])
        self.billcon.command("say      ")
        self.assertEqual(self.billcon.msgs, [])
        self.assertEqual(self.philcon.msgs, [])
        # consecutive spaces will be treated as one separator
        self.billcon.command("say  whoops   extra  spaces")
        self.assertEqual(self.billcon.msgs,
                         ["Bill the Default Character: whoops extra spaces"])
        self.assertEqual(self.philcon.msgs,
                         ["Bill the Default Character: whoops extra spaces"])

    def test_go_err(self):
        """test that the 'go' sends an error with a bad exit name"""
        self.billcon.command("go")
        self.assertEqual(self.billcon.msgs, ["No exit with name ''."])
        self.billcon.msgs.clear()
        self.assertTrue(self.bill.location is TEST_ROOM)
        self.billcon.command("go foobar")
        self.assertEqual(self.billcon.msgs, ["No exit with name 'foobar'."])
        self.assertTrue(self.bill.location is TEST_ROOM)
    
    def test_go_basic(self):
        """test that basic use of the go command works properly"""
        self.billcon.command("go outside")
        self.assertEqual(self.billcon.msgs, [])
        self.assertEqual(self.philcon.msgs,
                         ["Bill left through exit 'outside'."])
        self.assertEqual(self.danacon.msgs, ["Bill entered."])
        self.assertTrue(self.bill.location is TEST_OUT)
        self.tearDown()
        self.setUp()
        self.billcon.command("go out")
        self.assertEqual(self.billcon.msgs, [])
        self.assertEqual(self.philcon.msgs,
                         ["Bill left through exit 'out'."])
        self.assertEqual(self.danacon.msgs, ["Bill entered."])
        self.assertTrue(self.bill.location is TEST_OUT)
        self.tearDown()
        self.setUp()
        self.billcon.command("go test  out")
        self.assertEqual(self.billcon.msgs, [])
        self.assertEqual(self.philcon.msgs,
                         ["Bill left through exit 'test out'."])
        self.assertEqual(self.danacon.msgs, ["Bill entered."])
        self.assertTrue(self.bill.location is TEST_OUT)

    def test_go_filtered(self):
        """test that 'go' command respects CharFilters"""
        # set access for exit to an empty whitelist
        # i.e. nobody is allowed through
        TEST_EXIT.access = char.CharFilter(mode=True)
        self.billcon.command("go outside")
        self.assertEqual(self.billcon.msgs, ["Exit 'outside' is unaccessible to you."])
        self.assertEqual(self.philcon.msgs, [])
        self.assertEqual(self.danacon.msgs, [])
        self.assertTrue(self.bill.location is TEST_ROOM)
        self.billcon.msgs.clear()
        # set visibility for exit to an empty whitelist
        # i.e. nobody can see this exit or go through now
        # so Bill should not be informed that this exit even exists
        TEST_EXIT.visibility = char.CharFilter(mode=True)
        self.billcon.command("go outside")
        self.assertEqual(self.billcon.msgs, ["No exit with name 'outside'."])
        self.assertEqual(self.philcon.msgs, [])
        self.assertEqual(self.danacon.msgs, [])
        self.assertTrue(self.bill.location is TEST_ROOM)
        self.billcon.msgs.clear()
        # BUT, if we set access to empty blacklist (allowing anyone in)
        # Bill should be allowed through, even though he can't see the exit
        TEST_EXIT.access = char.CharFilter(mode=False)
        self.billcon.command("go outside")
        self.assertEqual(self.billcon.msgs, [])
        self.assertEqual(self.philcon.msgs,
                         ["Bill left through exit 'outside'."])
        self.assertEqual(self.danacon.msgs, ["Bill entered."])
        self.assertTrue(self.bill.location is TEST_OUT)
