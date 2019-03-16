'''Defining some basic RPG classes for testing'''
from character import Character
from time import time
from mudscript import server

def timed(delay):
    def delayed_cooldown(func):
        setattr(func, "last_used", 0)
        def cooled_down_func(*args, **kwargs):
            print(func.last_used + delay)
            print(time())
            diff = func.last_used + delay - time()
            if diff < 0:
                func.last_used = time()
                return func(*args, **kwargs)
        return cooled_down_func
    return delayed_cooldown

class Humanoid(Character):
    '''Testing class that provides some basic traits'''
    starting_location = server.lib.locations["Hoggetown Pub and Inn"]
    max_health = 100
    
    def __init__(self):
        self.health = self.max_health
        super().__init__()

    def update(self):
        super().update()
        if self.health < self.max_health:
            self._regen_health()
    
    def check_death(self):
        if self.health < 0:
            self.die()

    @timed(10)
    def _regen_health(self):
        self.health += 1
    
    def cmd_slap(self, args):
        '''Slap another player.
        Usage: slap [player]
        '''
        if len(args) < 2:
            return
        for char in self.location.character_list:
            if args[1] == char.name:
                break
        else:
            self.message("Could not find player with name %s." % args[1])
            return
        # if we get to this point, then we slapped someone
        try:
            char.health -= 10
            char.check_death()
        except:
            self.location.message_chars("%s tried to slap %s, to no avail." % (self, char))
        
