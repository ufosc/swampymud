import library
import item
from scripts.basic_rpg import Humanoid

class Brute(Humanoid):
    starting_location = library.locations["Marston Basement"]

    def __init__(self):
        super().__init__()
        self.damage = 1;        

    def cmd_slap(self, args):
        '''Slap another player.
        Usage: slap [player]
        '''
        if len(args) < 1:
            return
        for char in self.location.get_character_list():
            if args[0] == char.name:
                break
        else:
            self.message("Could not find player with name %s." % args[0])
            return
        # if we get to this point, then we slapped someone
        try:
            char.health -= 10*self.damage
            char.check_death()
        except:
            self.location.message_chars("%s tried to slap %s, to no avail." % (self, char))
        

    def cmd_rage(self, args):
        self.message("you get angry at nothing....weirdo")
        self.damage*=10
        