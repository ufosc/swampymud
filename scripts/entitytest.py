import entity
import character
from scripts.RareClass import RareClass
import random

class FortuneTeller(entity.Entity):

    FORTUNES = [
        "You look nice today.",
        "You smell of roses and honeysuckle.",
        "May you perform well in all your pursuits."
    ]

    @entity.entity_command
    def tellme(self, character, args):
        '''tell me a fortune'''
        character.message(random.choice(self.FORTUNES))
    
    @entity.filtered_command(character.CharFilter("whitelist", [RareClass]))
    def secret(self, character, args):
        character.message("This is our little secret.")
