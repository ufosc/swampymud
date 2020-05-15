'''Defining some basic RPG classes for testing'''
from swampymud.character import Character
from swampymud.item import Item, Equippable
from swampymud.inventory import EquipTarget
from swampymud.entity import Entity
from time import time
import random

class Humanoid(Character):
    '''Testing class that provides some basic traits'''
    max_health = 100
    heal_rate = 500

    equip_slots = ["Head", "Right Hand", "Left Hand"]

    def __init__(self, name=None):
        super().__init__(name)
        self._health = self.max_health
        self._last_heal = time()

    def update(self):
        if self.health < self.max_health and self._last_heal < time() - 30:
            self._last_heal = time()
            self.health += 1
        super().update()

    @property
    def health(self):
        return self._health

    @health.setter
    def health(self, value):
        self._health = value
        if value <= 0:
            self.die()
        if value > self.max_health:
            self._health = self.max_health


class Wizard(Character):
    def cmd_fireball(self, args):
        '''Shoot a fireball at [target].
        Usage: fireball [target]
        '''
        if len(args) < 2:
            self.message("Error: No target provided.")
        # TODO: upgrade this to include entities and items
        target = self.location.find(args[1])
        if target is None:
            self.message("Error: Target '%s' not found." % args[1])
        else:
            try:
                target.health -= 10
                target.message("%s hit you with a fireball." % self)
            except AttributeError:
                pass

    def cmd_heal(self, args, amt=10):
        '''Restore health on [target].
        Usage: heal [target]
        '''
        if len(args) < 2:
            self.message("Error: No target provided.")
        # TODO: upgrade this to include entities and items
        target = self.location.find(args[1])
        if target is None:
            self.message("Error: Target '%s' not found." % args[1])
        else:
            try:
                target.health += amt
                target.message("%s healed you." % self)
            except AttributeError:
                pass

class DarkWizard(Wizard):
    def cmd_puppet(self, args):
        '''Use another [sender] as a puppet
        Usage: puppet [sender] [receiver] [message]
        '''
        if len(args) < 4:
            self.message("Error: Usage: puppet [sender] [receiver] [message]")
        # get the sender
        sender = self.location.find(args[1])
        if sender is None:
            self.message("Cannot find sender '%s'" % args[1])
            return
        receiver = self.location.find(args[2])
        if receiver is None:
            self.message("Cannot find receiver '%s'" % args[1])
            return
        try:
            receiver.message("%s : %s" % (sender, " ".join(args[3:])))
        except AttributeError:
            pass

    def cmd_heal(self, args):
        '''Attempt to heal [target]. This corrupted spell could hurt the target.
        Usage: heal [target]
        '''
        amt = random.choice((10, -3, -5))
        super().cmd_heal(args, amt)

class Warrior(Character):
    base_damage = 12

    def __init__(self, name=None):
        super().__init__(name)
        self.damage = self.base_damage
        self.attack_msg = "%s punched %s!"

    def cmd_hit(self, args):
        '''Hit a target with your weapon (or bare hands).
        Usage: hit [target]'''
        if len(args) < 2:
            self.message("Error: No target provided.")
        # TODO: upgrade this to include entities and items
        target = self.location.find(args[1])
        if target is None:
            self.message("Error: Target '%s' not found." % args[1])
        else:
            try:
                target.health -= self.damage
                self.location.message_chars(self.attack_msg % (self, target))
            except AttributeError:
                pass


#TODO: add class filters to this item once they are added
class BigClub(Equippable):
    target = EquipTarget("Right Hand")

    def __init__(self):
        self.old_msg = ""

    def on_equip(self, char):
        try:
            char.damage += 2
            # store a copy of the old message
            self.old_msg = char.attack_msg
            char.attack_msg = "%s clubbed %s."
        except AttributeError:
            pass

    def on_unequip(self, char):
        try:
            char.damage -= 2
            char.attack_msg = self.old_msg
        except AttributeError:
            pass


class Thief(Character):
    def cmd_pickpocket(self, args):
        '''Pickpocket another player.
        [not implemented]
        '''
        pass


# a healing potion
class HealthPotion(Item):

    def on_use(self, char):
        char.message("You drink the potion.")
        try:
            char.health += 10
        except AttributeError:
            pass


# a cool entity
class Golem(Entity):
    pass

# a specialized class just for the golem
class GolemRiddle:
    pass