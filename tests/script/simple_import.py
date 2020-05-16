"""module with a location-based circular dependency
this module expects 'simple.yaml' to be loaded first
"""
from swampymud import mudscript
from tests.script.basic_rpg import Humanoid

HOUSE = mudscript.import_location("Boring House")
INTERIOR = mudscript.import_location("Boring House Interior")

class Housekeeper(Humanoid):
    pass