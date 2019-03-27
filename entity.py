'''Method defining an entity'''
import character
from location import NULL_ISLAND
from util import camel_to_space

class EntityMeta(type):
    def __init__(self, cls, namespace, bases):
        if "name" not in namespace:
            self.name = camel_to_space(cls)


class Entity(metaclass=EntityMeta):
    pass


class DroppedItem(Entity):
    pass