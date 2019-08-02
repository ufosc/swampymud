'''module testing the Character class'''
import unittest
import control
import character
import location

class EntryPlug(control.Controller):
    '''simple controller for programmatic use'''
    def __init__(self, character):
        super().__init__()
        self.assume_control(character)
        self.last_cmd = None
        self.msgs = []
    
    def command(self, cmd):
        '''add a command and update the receiver to respond'''
        self.last_cmd = cmd
        self.receiver.update()

    def read_cmd(self):
        '''return the stored command, set to None'''
        cmd, self.last_cmd = self.last_cmd, None
        return cmd

    def has_cmd(self):
        return self.last_cmd is not None

    def write_msg(self, msg):
        self.msgs.append(msg)
    
    def has_msg(self):
        return bool(self.msgs)
        
room = location.Location("Room", "This is just a room for testing.")
billy = character.Character("Billy")
billy.set_location(room)
con = EntryPlug(billy)
