'''Method defining an entity'''
import character
from location import NULL_ISLAND
from util import camel_to_space

class EntityMeta(type):
    def __init__(self, cls, namespace, bases):
        if "name" not in namespace:
            self.name = camel_to_space(cls)
        self._instances = {}
        self._nextid = 0
    
    def __getitem__(self, key):
        return self._instances[key]
    
    def __setitem__(self, key, item):
        self._instances[key] = item
    
    def __delitem__(self, key):
        del self._instances[key]

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
        self.location = None
        self.proper_name = proper_name
        self._id = self._nextid
        self._nextid += 1
        self._instances[self._id] = self
    
    def __repr__(self):
        return "%s[%i]" % (type(self).__name__, self._id)
    
    def __str__(self):
        if self.proper_name is not None:
            return self.proper_name
        else:
            return repr(self)


class DroppedItem(Entity):
    def __init__(self, item):
        super().__init__("Dropped " + str(item))
        self._item = item

    @entity_command
    def pickup(self, char):
        char.inv
        self.location