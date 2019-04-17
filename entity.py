'''Method defining an entity'''
import character
from location import NULL_ISLAND
from util import camel_to_space
from command import Command
import location

class EntityMeta(type):
    def __init__(self, cls, bases, namespace):
        super().__init__(cls, bases, namespace)
        if "name" not in namespace:
            self.name = camel_to_space(cls)
        self._instances = {}
        self._nextid = 0
        self._commands = {}
        for item in namespace.values():
            if isinstance(item, EntityCommand):
                self._commands[item.name] = item
        
        entity_bases = list(filter(lambda x: isinstance(x, EntityMeta),
                            self.__mro__))
        # build the set of command names / commands by looking through
        # the mro
        # there is probably a better way to do this
        for base in entity_bases:
            for cmd in base._commands.values():
                if cmd.name not in self._commands:
                    self._commands[cmd.name] = cmd

    
    def __getitem__(self, key):
        return self._instances[key]
    
    def __setitem__(self, key, item):
        self._instances[key] = item
    
    def __delitem__(self, key):
        del self._instances[key]
    
    def cmd_name_set(cls, char=None):
        if char is None:
            return set(cls._commands)
        else:
            nameset = set()
            for cmd in cls._commands.values():
                if cmd.filter.permits(char):
                    nameset.add(cmd.name)
            return nameset
    
    def intersect(cls, other_entity, char=None):
        '''returns the set of names that have corresponding commands 
        in both classes
        if a char is provided, only those commands that the 
        character can use are included'''
        if other_entity is cls:
            return cls.cmd_name_set(char)
        names = cls.cmd_name_set(char)
        other_names = other_entity.cmd_name_set(char)
        return names & other_names
        

class EntityCommand(Command):
    def __init__(self, name, func, type_name="Environmental", source=None, char=None, filter=None):
        super().__init__(name, func, type_name, source)
        self.filter = filter
        if filter is None:
            self.filter = character.CharFilter("blacklist")
        self.char = char
    
    def specify(self, new_source=None, new_char=None):
        '''return a copy of this command with a new source/char'''
        new_cmd = EntityCommand(self.name, self._func, self.type_name, 
                                new_source, new_char, self.filter)
        return new_cmd

    def __call__(self, *args, **kwargs):
        '''call entity command'''
        # should we always assume that a char is specified?
        return self._func(self.source, self.char, *args, **kwargs)
    
    def __repr__(self):
        return "EntityCommand%r" % ((self.name, self._func, self.type_name, 
                                    self.source, self.char, self.filter),)
    
    # TODO: implement __hash__ / __eq__ method, look at Command class

def filtered_command(filt):
    '''decorator for methods with CharFilters'''
    def inner(func):
        return EntityCommand(func.__name__, func, filter=filt)
    return inner

def entity_command(func):
    '''decorator for methods without CharFilters'''
    return EntityCommand(func.__name__, func)

class Entity(metaclass=EntityMeta):
    def __init__(self, proper_name=None, location=None):
        if location is None:
            location = NULL_ISLAND
        self.proper_name = proper_name
        self._id = self._nextid
        self._nextid += 1
        self._instances[self._id] = self
        self.set_location(location)
    
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
        cmd_dict = char.cmd_dict
        
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
            

class Wizard(character.Character):
    pass

class Brute(character.Character):
    pass

brute = Brute()
wiz = Wizard()

class Button(Entity):
    @entity_command
    def push(self, char):
        '''Push the button'''
        char.message("You pushed the button.")

class MagicButton(Entity):
    @filtered_command(character.CharFilter(True, [Wizard]))
    def push(self, char):
        '''Push the button'''
        char.message("You pushed the magic button.")


class DroppedItem(Entity):
    def __init__(self, item):
        super().__init__("Dropped " + str(item))
        self._item = item

    @entity_command
    def pickup(self, char):
        char.inv
        self.location


test_location = location.Location("Test Location", "my loc")
wiz.set_location(test_location)

normal = Button("Normal", test_location)
magic = MagicButton("Magic", test_location)

brute.set_location(test_location)

def test_add(char):
    normal.add_cmds(char)
    magic.add_cmds(char)
    print(char.cmd_dict.help())

def test_remove(char):
    normal.remove_cmds(char)
    magic.remove_cmds(char)
    print(char.cmd_dict.help())