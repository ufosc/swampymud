'''Method defining an entity'''
import character
from util import camel_to_space
from command import SpecificCommand

class EntityClass(type):
    '''metaclass controlling entity types'''

    # TODO: move dict of individual entities into the server
    def __init__(self, cls, bases, namespace):
        '''initialize an Entity class'''
        super().__init__(cls, bases, namespace)
        if "classname" not in namespace:
            self.classname = camel_to_space(cls)
        self._instances = {}
        self._nextid = 0
        self._commands = {}
        for item in namespace.values():
            if isinstance(item, EntityCommand):
                self._commands[item.name] = item

        entity_bases = list(filter(lambda x: isinstance(x, EntityClass),
                                   self.__mro__))
        # build the set of command names / commands by looking through
        # the mro
        # there is probably a better way to do this
        for base in entity_bases:
            for cmd in base._commands.values():
                if cmd.name not in self._commands:
                    self._commands[cmd.name] = cmd


    def __getitem__(self, key):
        '''overriding cls[k]'''
        return self._instances[key]

    def __setitem__(self, key, item):
        ''' overriding cls[k] = item'''
        self._instances[key] = item

    def __delitem__(self, key):
        '''overriding del cls[k]'''
        del self._instances[key]

    def __str__(self):
        '''overriding str()'''
        return self.classname

    def describe(self):
        ''' Describes the entity '''
        return str(self)

    def cmd_name_set(cls, char=None):
        '''returns a set of the names for each command'''
        if char is None:
            return set(cls._commands)
        else:
            nameset = set()
            for cmd in cls._commands.values():
                if cmd.filter.permits(char):
                    nameset.add(cmd.name)
            return nameset

    def intersect(cls, other_entity, char=None):
        '''returns the set of names that have corresponding
        commands in both classes
        if a char is provided, only those commands that the
        character can use are included'''
        if other_entity is cls:
            return cls.cmd_name_set(char)
        names = cls.cmd_name_set(char)
        other_names = other_entity.cmd_name_set(char)
        return names & other_names


class EntityCommand(SpecificCommand):
    def __init__(self, name, func, type_name="Environmental", filter=None, 
                 source=None, char=None):
        if filter is None:
            # if no filter is provided, use an empty blacklist 
            # to let everyone use it
            filter = character.CharFilter("blacklist")
        super().__init__(name, func, type_name, filter, source, char)


def filtered_command(filt):
    '''decorator for methods with CharFilters'''
    def inner(func):
        return EntityCommand(func.__name__, func, filter=filt)
    return inner


def entity_command(func):
    '''decorator for methods without CharFilters'''
    return EntityCommand(func.__name__, func)


class Entity(metaclass=EntityClass):
    def __init__(self, proper_name=None):
        self.location = None
        self.proper_name = proper_name
        self._id = self._nextid
        self.__class__._nextid += 1
        self._instances[self._id] = self
        self._isNPC = False

    def __repr__(self):
        return "%s[%i]" % (type(self).__name__, self._id)

    def __str__(self):
        if self.proper_name is not None:
            return self.proper_name
        else:
            return repr(self)

    def set_location(self, new_location):
        '''sets location, updating previous location as appropriate'''
        try:
            self.location.remove_entity(self)
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
        # first, determine the commands that collide with other
        # entities commands
        collided_cmds = set()
        for entity in self.location.entities:
            if entity is not self:
                collided_cmds.update(type(self).intersect(type(entity), char))
        for cmd in self._commands.values():
            cmd = cmd.specify(self, char)
            # only add the command if the filter permits the char
            if cmd.filter.permits(char):
                # if the command could be ambigious, 
                # supply the entity name to the command
                if cmd.name in collided_cmds:
                    char.cmd_dict.add_cmd(cmd, name=cmd.name + "-%s" % str(self))
                else:
                    char.cmd_dict.add_cmd(cmd)

    def remove_cmds(self, char):
        '''remove all commands from this char that
        belong to this entity'''
        for cmd in self._commands.values():
            cmd = cmd.specify(self, char)
            if char.cmd_dict.has_cmd(cmd):
                char.cmd_dict.remove_cmd(cmd)

    @property
    def isNPC(self):
        return self._isNPC