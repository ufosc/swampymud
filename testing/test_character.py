'''module testing the Character class'''
import unittest
import control as con
import character as char
import location as loc

class EntryPlug(con.Controller):
    '''simple controller for programmatic use'''
    def __init__(self, character):
        super().__init__()
        self.assume_control(character)
        self.last_cmd = None
        self.msgs = []

    def __repr__(self):
        return f"EntryPlug{self.receiver}"

    def command(self, cmd):
        '''add a command and update the receiver to respond'''
        self.last_cmd = cmd
        self.receiver.update()

    def read_cmd(self):
        '''return the stored command, set to None'''
        cmd, self.last_cmd = self.last_cmd, None
        return cmd

    def has_cmd(self):
        '''returns true if command is available'''
        return self.last_cmd is not None

    def write_msg(self, msg):
        '''write [msg] back to the controller'''
        self.msgs.append(msg)
    
    def has_msg(self):
        '''returns true if messages are available'''
        return bool(self.msgs)
        
TEST_ROOM = loc.Location("Room", "This is just a room for testing.")

class TestDefaultCommands(unittest.TestCase):
    
    def setUp(self):
        self.room = loc.Location("Room", "This is just a room for testing.")
        self.bill = char.Character("Bill")
        self.bill.set_location(TEST_ROOM)
        self.billcon = EntryPlug(self.bill)
    
    def tearDown(self):
        self.bill.die()
    
    def test_help(self):
        '''test that help command works properly'''
        self.billcon.command("help")
        # check message