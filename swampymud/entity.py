'''Module defining the entity class'''
import inspect
from swampymud.util import camel_to_space
import swampymud.character as character
from swampymud import _types

class EntityClass(type, _types.EntityClass):
    '''Metaclass controlling entity types'''

    def __init__(self, cls, bases, namespace):
        '''initialize an Entity class'''
        if "classname" not in namespace:
            self.classname = camel_to_space(cls)
        if "description" not in namespace:
            if self.__doc__ is not None:
                self.description = inspect.cleandoc(self.__doc__)
            else:
                self.description = "[No description provided.]"

        # note that this is essentially the same as CharacterClass
        # first gather the Commands defined in this class
        self._local_commands = {}
        for value in namespace.values():
            if isinstance(value, character.Command):
                value.label = "Equipped"
                self._local_commands[str(value)] = value

        # now gather all commands, with the most recent commands exposed
        self._commands = {}
        for base in reversed(self.__mro__):
            if not isinstance(base, EntityClass):
                continue
            self._commands.update(base._local_commands)
        self._commands.update(self._local_commands)

    def __str__(cls):
        '''returns a string representation of this class'''
        return cls.classname


class Entity(_types.Entity, metaclass=EntityClass):
    '''Base class for all other entities'''
    def __init__(self):
        self.location = None

    def __str__(self):
        '''Return a simple representation of this item.
        By default, str(item) returns the name of the entity's class.
        '''
        return self.classname

    def set_location(self, new_location):
        '''sets location, updating previous location as appropriate'''
        try:
            self.location.entities.remove(self)
            # remove this entity's commands from all the
            # characters in the current location
            for char in self.location.characters:
                self.remove_cmds(char)
        except AttributeError:
            # location was none
            pass
        self.location = new_location
        self.location.add_entity(self)
        # add this entity's commands to all the
        # characters in the current location
        for char in new_location.characters:
            self.add_cmds(char)

    def add_cmds(self, char):
        '''add a command to a character'''
        for cmd in self._commands.values():
            if cmd.filter.permits(char):
                cmd = cmd.specify(self, char)
                char.cmd_dict[str(cmd)] = cmd

    def remove_cmds(self, char):
        '''remove all commands from this char from this entity'''
        for cmd in self._commands.values():
            cmd = cmd.specify(self, char)
            try:
                char.cmd_dict.remove_value(str(cmd), cmd)
            # command was not in cmd_dict
            except KeyError:
                pass
            except ValueError:
                pass

    def despawn(self):
        """removes entity from location and frees it for gc"""
        if self.location is not None:
            for char in self.location.characters:
                self.remove_cmds(character)
            self.location.entities.remove(self)
        self.location = None

    # these methods can be overriden
    def on_enter(self, char: character.Character):
        pass

    def on_exit(self, char: character.Character):
        pass

    def on_message(self, char: character.Character, msg: str):
        pass

    # serialization-related methods
    @classmethod
    def load(cls, data):
        proper_name = None
        return cls(proper_name)

    def post_load(self, data, obj_symbols, cls_symbols):
        pass

    def save(self):
        return {}
