"""a few CharacterClasses for testing the 'find' method
(see save 'tavern.yaml')"""
from swampymud.character import Character

class Humanoid(Character):
    """a base class for all other classes in this group"""

class Merchant(Humanoid):
    """good with coin (especially other people's)"""

class Wizard(Humanoid):
    """masters of the perplexing arts"""

class Thug(Humanoid):
    """hired hands of few scruples"""

class Thief(Humanoid):
    """sneaky folks"""
