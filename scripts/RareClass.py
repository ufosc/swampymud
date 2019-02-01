import library
from character import Character

class RareClass(Character):
    starting_location = library.locations["Marston Basement"]
    def cmd_meme(self, args):
        print("meme")
