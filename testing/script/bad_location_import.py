"""this script attempts to load a location that doesn't exist"""
import mudscript
from testing.script.basic_rpg import Humanoid

epic_castle = mudscript.import_location("Epic Castle")

class DarkLord(Humanoid):
    pass
