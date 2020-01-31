'''Defining some basic RPG classes for testing'''
from character import Character
from time import time
from mudscript import server
import effect

def timed(delay):
    def delayed_cooldown(func):
        setattr(func, "last_used", 0)
        def cooled_down_func(*args, **kwargs):
            diff = func.last_used + delay - time()
            if diff < 0:
                func.last_used = time()
                return func(*args, **kwargs)
        return cooled_down_func
    return delayed_cooldown

class Humanoid(Character):
    '''Testing class that provides some basic traits'''
    #starting_location = server.lib.locations["Hoggetown Pub and Inn"]
    max_health = 100
    
    def __init__(self, name=None):
        super().__init__(name)
        self._health = self.max_health

    def update(self):
        if self.health < self.max_health:
            self._regen_health()
        super().update()
    
    @timed(5)
    def _regen_health(self):
        self.health += 5
    
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
    
    def cmd_slap(self, args):
        '''Slap another player.
        Usage: slap [player]
        '''
        if len(args) < 2:
            return
        for char in self.location.characters:
            if args[1] == str(char):
                break
        else:
            self.message("Could not find player with name %s." % args[1])
            return
        # if we get to this point, then we slapped someone
        try:
            char.health -= 10
        except:
            self.location.message_chars("%s tried to slap %s, to no avail." % (self, char))
        
class Heal(effect.BaseEffect):
    param_schema = [int]

    def apply(self, target):
        '''attempt to harm character'''
        try:
            target.health -= self.params[0]
        except AttributeError:
            pass

class Harm(effect.BaseEffect, reverse=Heal):
    param_schema = [int]

    def apply(self, target):
        '''attempt to harm character'''
        try:
            target.health -= self.params[0]
        except AttributeError:
            pass

Ignite, Extinguish = effect.StatusEffect.create_pair("Ignite", "Extinguish", "Fire")