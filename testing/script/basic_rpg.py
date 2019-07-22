'''Defining some basic RPG classes for testing'''
from character import Character
from item import Usable
from entity import Entity

class Wizard(Character):
    pass

class DarkWizard(Character):
    pass

class Warrior(Character):
    pass

class Thief(Character):
    pass

# a healing potion
class HealthPotion(Usable):

    def use(self, char):
        char.message("You are feeling healed")

# a cool entity
class Golem(Entity):
    pass

# a specialized class just for the golem
class GolemRiddle:
    pass