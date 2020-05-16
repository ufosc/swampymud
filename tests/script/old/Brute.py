import mudscript
import item
from scripts.basic_rpg import Humanoid

class Brute(Humanoid):
    mudscript.get_location("Marston Basement")

    def __init__(self, name=None):
        super().__init__(name)
        self.damage = 1;        

    def cmd_slap(self, args):
        '''Slap another player.
        Usage: slap [player]
        '''
        if len(args) < 1:
            return
        for char in self.location.characters:
            if args[1] == str(char):
                break
        else:
            self.message("Could not find player with name %s." % args[0])
            return
        # if we get to this point, then we slapped someone
        try:
            char.health -= (10*self.damage)
        except:
            self.location.message_chars("%s tried to slap %s, to no avail." % (self, char))
        

    def cmd_rage(self, args):
        '''You channel your anger to unleash more ferocious attacks
        Usage: rage
        '''
        self.message("you get angry at nothing....weirdo")
        self.damage*=10