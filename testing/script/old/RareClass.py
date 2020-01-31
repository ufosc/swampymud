import mudscript
from character import Character

class RareClass(Character):
    starting_location = mudscript.get_location("Marston Basement")
    def cmd_meme(self, args):
        print("meme")
