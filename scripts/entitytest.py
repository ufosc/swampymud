import entity
import character
import util.misc as misc
from scripts.RareClass import RareClass
import random

class FortuneTeller(entity.Entity):

    FORTUNES = [
        "You look nice today.",
        "You smell of roses and honeysuckle.",
        "May you perform well in all your pursuits."
    ]

    def __init__(self, proper_name=None):
        super().__init__(proper_name)
        self._isNPC = True

    @entity.entity_command
    def tellme(self, character, args):
        '''tell me a fortune'''
        character.message(random.choice(self.FORTUNES))
    
    @entity.filtered_command(character.CharFilter("whitelist", [RareClass]))
    def secret(self, character, args):
        character.message("This is our little secret.")

    def describe(self):
        return self.proper_name + " the " + misc.camel_to_space(str(type(self)))
