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

class TestDefaultCommands(unittest.TestCase):
    """test that all the default Character commands work properly"""
    def setUp(self):
        self.room = loc.Location("Room", "This is just a room for testing.")
        self.bill = char.Character("Bill")
        self.bill.set_location(TEST_ROOM)
        self.billcon = EntryPlug(self.bill)

    def tearDown(self):
        self.bill.die()

    def test_help(self):
        """test for the help command"""
        # using help by itself
        self.billcon.command("help")
        self.assertEqual(self.billcon.msgs.pop(), self.bill.cmd_dict.help())

        # using help with other commands should produce their docstring
        self.billcon.command("help help")
        help_msg = self.billcon.msgs.pop()
        # check that help message agrees with the CommandDict
        self.assertEqual(help_msg, self.bill.cmd_dict.get_cmd("help").help())
        #print(help_msg)
        self.assertEqual(help_msg,
                         "Show relevant help information for a particular command.\n"
                         "usage: help [command]\n"
                         "If no command is supplied, a list of all commands is shown.")