"""this script attempts to load a location that doesn't exist"""
from swampymud import mudscript
from tests.script.basic_rpg import Humanoid

epic_castle = mudscript.import_location("Epic Castle")

class DarkLord(Humanoid):
    pass
