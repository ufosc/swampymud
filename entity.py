'''Method defining an entity'''
import character
from location import NULL_ISLAND
from util import camel_to_space

class EntityMeta(type):
    def __init__(self, cls, namespace, bases):
        if "name" not in namespace:
            self.name = camel_to_space(cls)
        # self._instances = []
        # self._nextid = 0

class EntityCommand:
    def __init__(self, command, perms=None):
        self.perms = perms
        if perms is None:
            self.perms = character.CharFilter("blacklist")
        self.command = command
    
    def __call__(self, *args, **kwargs):
        return self.command(*args, **kwargs)
    
    def __repr__(self):
        return "EntityCommand(%r, %r)" % (self.command, self.perms)

def filtered_command(perms):
    '''decorator for methods with CharFilters'''
    def inner(func):
        return EntityCommand(func, perms)
    return inner

def entity_command(func):
    '''decorator for methods without CharFilters'''
    return EntityCommand(func)

class Entity(metaclass=EntityMeta):
    def __init__(self, proper_name=None):
        self.proper_name = proper_name


class DroppedItem(Entity):
    @entity_command
    def pickup(self, player):
        pass