'''Module defining the CharacterClass metaclass, and Character base class'''
import enum
from time import time
import util
import location
import control
import inventory
import item
import mudscript

class CharException(Exception):
    pass


class AmbiguityError(CharException):
    '''Error representing some sort of ambiguity
    This error should be thrown if a user's input
    could refer to multiple in-game options
    For instance:
        Suppose the user has two swords, both named "Epic Sword"
        One was created statically, and looted from a dungeon.
        The other was created dynamically by the user through
        some enchating process.
        If the user types "Epic Sword" we cannot assume which one
        should be used. Hence, we should use raise an error of
        this class.
    '''
    def __init__(self, indices, query, options):
        '''
        indices = the indices of the offending words
                [May be a slice or int]
        phrase = the offending phrase
        options = list containing the available options
        Example:
        > equip epic sword
        indices = slice(1,2)
        query = "epic sword"
        options = [list of results from inventory.get_item()]
        '''
        super().__init__()
        self.indices = indices
        self.options = options
        self.query = query


class CharacterClass(type):
    '''The metaclass for all Character class
    key features:
        name: how the class appears to the players
        commands: a dictionary of all user commands
        unique_commands: a list of commands not found in base classes
        help_menu: a preformatted help menu, printed when 'help' is called
    '''
    def __init__(self, cls, bases, dict):
        # creating the proper name, if one is not provided
        if "name" not in dict:
            self.name = util.camel_to_space(cls)
        # adding a frequency field, if not already provided
        if "frequency" not in dict:
            self.frequency = 1
        # creating a dictionary of commands
        # all functions starting with cmd_ are commands
        self.commands = {}
        for func in dir(self):
            if func.startswith("cmd_"):
                self.commands[func[4::]] =  getattr(self, func)
        # building the unique_commands
        # a unique command is not found in any of the base classes
        self.unique_commands = []
        character_bases = [base for base in bases if hasattr(base, "commands")]
        for command in self.commands:
            # if the command does not appear in any of the base classes
            if not any(command in base.commands for base in character_bases):
                self.unique_commands.append(command)
        # building the help menu
        self.help_menu = self._build_help_menu(bases)
        # calling the super init
        super().__init__(cls, bases, dict)
    
    def _build_help_menu(self, bases):
        '''building a help menu, with the commands from each base on coming
        before the commands unique to this class'''
        output = ""
        for base in bases:
            if isinstance(base, CharacterClass):
                output += base.help_menu
        output += "[%s Commands]\n" % self
        output += "\t".join(self.unique_commands) + "\n"
        return output

    def __str__(self):
        return self.name

class Character(control.Monoreceiver, metaclass=CharacterClass):
    '''Base class for all other CharacterClasses'''

    # Name for this class
    name = "Default Character"
    # Dictionary of names for ALL PLAYERS
    # DO NOT TOUCH
    _names = {}
    # Starting location for this player
    starting_location = location.Location("NullLocation", "Default Location")
    # Valid equip slots for characters of this class
    equip_slots = []

    def __init__(self):
        super().__init__()
        self.name = None
        self.location = None
        self.set_location(self.starting_location)
        self.inv = inventory.Inventory()
        self.equip_dict = item.EquipTarget.make_dict(*self.equip_slots)
        self._parser = lambda line: Character.player_set_name(self, line)
        #TODO: make this a property
        self.is_alive = True

    def message(self, msg):
        '''send a message to the controller of this character'''
        if self.controller:
            self.controller.write_msg(msg)
    
    def update(self):
        while self.is_alive and self.controller.has_cmd():
            line = self.controller.read_cmd().strip()
            if line == "":
                continue
            try:
                self._parser(line)
            except CharException as cex:
                self.message(str(cex))

    def parse_command(self, line=None, args=None):
        '''parses a command, raises AttributeError if command cannot be found'''
        if args is None and line is None:
            return
        if args is None:
            args = line.split(" ")
        command = args[0]
        if command not in self.commands:
            self.message("Command \'%s\' not recognized." % command)
            return
        method = self.commands[command]
        try:
            method(self, args)
        except AmbiguityError as amb:
            self._parser = AmbiguityResolver(self, args, amb)
        except CharException as ex:
            self.message(str(ex))
    
    def _check_ambiguity(self, indices, phrase, options):
        '''wraps function outputs to handle ambiguity
        if no option is returned, then raise an error
        if multiple options are found, raise an ambiguity error
        '''
        if len(options) == 1:
            return options[0]
        elif len(options) == 0:
            raise CharException("Error: '%s' not found." % (phrase))
        else:
            raise AmbiguityError(indices, phrase, options)

    def set_name(self, new_name):
        '''changes a characters's name, with all appropriate error checking'''
        if new_name in Character._names:
            raise CharException("Name already taken.")
        # TODO: check that new_name is not a globally-registered 
        # location, CharClass, etc.
        if self.name is not None:
            del(self._names[self.name])
        self.name = new_name
        self._names[self.name] = self

    def player_set_name(self, new_name):
        '''intended for first time players set their name'''
        if not new_name.isalnum():
            self.message("Names must be alphanumeric.")
            return
        self.set_name(new_name)
        self._parser = lambda line: Character.parse_command(self, line)
        try:
            mudscript.message_all("Welcome, %s, to the server!" % self)
        except mudscript.MuddyException:
            pass
        self.cmd_look(["look"])

    def __repr__(self):
        '''return the player's name and class'''
        if self.name is None:
            return "A nameless %s" % self.__class__.name
        return "%s the %s" % (self.name, self.__class__.name)

    def __str__(self):
        '''return the player's name'''
        if self.name is None:
            return repr(self)
        else:
            return self.name

    # these methods need heavy refinement 
    def die(self, msg="%s died."):
        '''method executed when a player dies'''
        if msg is not None:
            if "%s" in msg:
                msg = msg % self
            self.location.message_chars(msg)
        self._remove_references()
        self.detach()
        self.is_alive = False


    def _remove_references(self):
        '''method executed when a character is being removed
        this takes care of any undesired references, and allows
        the player to die'''
        try:
            self.location.remove_char(self)
            self.location = None
        except AttributeError:
            # location is none
            pass

        # delete character from the name dictionary
        try:
            del self._names[self.name]
        except KeyError:
            pass

    #location manipulation methods        
    def set_location(self, new_location):
        '''sets location, updating the previous and new locations as appropriate
        if reported_exit is supplied, then other players in the location 
        will be notified of which location he is going to
        '''
        try:
            self.location.remove_char(self)
        except AttributeError:
            # location was none
            pass
        self.location = new_location
        self.location.add_char(self)
    
    def take_exit(self, exit, show_leave=True, leave_via=None, 
                  show_enter=True, enter_via=None):
        if show_enter:
            try:
                if enter_via:
                    exit.destination.message_chars("%s entered through %s."
                                                 % (self, leave_via))
                else:
                    exit.destination.message_chars("%s entered." % (self,))
            except AttributeError:
                # self.location was none
                pass
        old_loc = self.location
        self.set_location(exit.destination)
        self.cmd_look(["look"], verbose=False)
        if show_leave:
            try:
                if leave_via:
                    old_loc.message_chars("%s left through %s."
                                                 % (self, leave_via))
                else:
                    old_loc.location.message_chars("%s left" % (self,))
            except AttributeError:
                # self.location was none
                pass

    #inventory/item related methods
    def equip(self, item, remove_inv=True):
        if item.target in self.equip_dict:
            already_equip = self.equip_dict[item.target]
            if already_equip is not None:
                self.unequip(already_equip)
            item.equip(self)
            self.equip_dict[item.target] = item
            # check remove_inv, if true, remove item
            # this avoids duplication
            if remove_inv:
                self.inv -= item
            self.message("Equipped %s." % item)
        else:
            raise CharException("You cannot equip item \'%s\' as %s."
                                % (item, self.__class__))
 
    def unequip(self, item):
        if self.equip_dict[item.target] == item:
            item.unequip(self)
            self.inv += item
            self.equip_dict[item.target] = None
            self.message("Unequipped %s." % item)
        else:
            raise CharException("Cannot unequip \'%s\'. Item not equipped."
                % item)

    # default commands        
    def cmd_help(self, args):
        '''Show relevant help information for a particular command.
        usage: help [command]
        If no command is supplied, a list of all commands is shown.
        '''
        if len(args) < 2:
            self.message(self.__class__.help_menu)
            return
        command = args[1]
        if command in self.commands:
            self.message(str(self.commands[command].__doc__))
        else:
            self.message("Command \'%s\' not recognized." % command)

    def cmd_look(self, args, verbose=True):
        '''Gives description of current location
        usage: look
        '''
        #TODO: move much of this functionality into the Location.info method
        # (replace the ugly formatting in that function)
        # add an optional char_class parameter so we can filter it
        if verbose:
            self.message(self.location.__str__(True))
        char_list = self.location.characters
        try:
            char_list.remove(self)
        except ValueError:
            pass
        char_msg = "\nYou see "
        if len(char_list) == 0:
            pass
        elif len(char_list) == 1:
            char_msg += str(char_list[0]) + "."
            self.message(char_msg)
        elif len(char_list) == 2:
            char_msg += " and ".join(map(str, char_list)) + "."
            self.message(char_msg)
        else:
            char_msg += ", ".join(map(str, char_list[:-1])) + ", and " + str(char_list[-1]) + "."
            self.message(char_msg)
        exit_list = self.location.exits
        exit_msg = "\nExits Available:\n"
        if exit_list:
            exit_msg += "\n".join(map(str, exit_list))
        else:
            exit_msg += "None"
        self.message(exit_msg)
        items = map(str, self.location.all_items())
        items = util.group_and_count(list(items), format="%s(%i)", sep=", ")
        if items:
            item_msg = "\nItems Available:\n" + items
            self.message(item_msg)

    def cmd_say(self, args):
        '''Say a message aloud, sent to all players in your current locaton.
        usage: say [msg]
        '''
        self.location.message_chars("%s : %s" % (self, " ".join(args[1:])))
    
    def cmd_walk(self, args):
        '''Walk to an accessible location.
        usage: walk [exit name]
        '''
        exit_name = " ".join(args[1:])
        #TODO: check for visibility
        found_exit = self.location.find_exit(exit_name)
        if found_exit:
            #TODO: check for accessbility
            self.take_exit(found_exit, True, 
                           "exit '%s'" % str(found_exit), True)
        else:
            self.message("No exit with name %s" % exit_name)
    
    def cmd_equip(self, args):
        '''Equip an equippable item from your inventory.'''
        if len(args) < 2:
            self.message("Provide an item to equip.")
            return
        item_name = " ".join(args[1::])
        #item = self._check_ambiguity(slice(1, len(args)), item_name, self.inv.find_all(item_name))
        found_item = self.inv.find(item_name)
            # args must be item that we already have
            #item = args[1]
        if found_item:
            self.equip(found_item)
        else:
            self.message("Could not find item '%s'" % item_name)

    def cmd_unequip(self, args):
        '''Unequip an equipped item.'''
        if len(args) < 2:
            self.message("Provide an item to equip.")
            return
        item_name = " ".join(args[1::])
        options = []
        for target, item in self.equip_dict.items():
            if item and item.name.lower() == item_name:
                options.append(item)
        item = self._check_ambiguity(1, item_name, options)
        self.unequip(item) 
    
    def cmd_pickup(self, args):
        ''' Pick up item from the environment'''        
        if len(args) < 2:
            self.message("Provide an item to pick up.")
            return
        
        item_name = " ".join(args[1::])
        item = self.location.find(item_name)
        if item:
            self.inv.add_item(item)
            self.location.remove_item(item)
        else:
            self.message("Could not find item with name '%s'" % item_name)

    def cmd_inv(self, args):
        '''Show your inventory.'''
        output = ""
        for target, equipped in self.equip_dict.items():
            output += str(target).upper() + "\n\t" + str(equipped) + "\n"
        self.message(output + self.inv.readable())


#TODO: clean this up, provide documentation
class AmbiguityResolver:
    def __init__(self, char, args, amb):
        self._char = char
        self._old_args = args
        self._amb = amb
        # send the char the ambiguity message
        self._char.message(str(self))
    
    def __call__(self, inp):
        try:
            inp = int(inp)
        except ValueError:
            self._char.message("Please enter an integer.")
            return
        if inp not in range(len(self._amb.options)):
            self._char.message("Provided integer out of range.")
            return
        choice = self._amb.options[inp]
        # delete the invalid options
        del self._old_args[self._amb.indices]
        if type(self._amb.indices) is slice:
            self._old_args.insert(self._amb.indices.start + 1, choice)
        else:
            self._old_args.insert(self._amb.indices + 1, choice)
        self._char._parser = lambda line: Character.parse_command(self._char, line)
        self._char.parse_command(args=self._old_args)

    def __str__(self):
        string = "Multiple options for %s:\n" % self._amb.query
        string += "\n".join(["\t%s) %s" % (index, repr(option)) for index, option in enumerate(self._amb.options)])
        string += "\nEnter a number to resolve it:" 
        return string

class FilterMode(enum.Enum):
    WHITELIST = True
    BLACKLIST = False


class CharFilter:
    '''Filter for screening out certain CharacterClasses and Characters
        _set  - set of Characters and CharacterClasses tracked by the filter
        _mode - FilterMode.WHITELIST or FilterMode.BLACKLIST
                if WHITELIST is selected, only tracked chars are allowed in
                if BLACKLIST is selected, tracked chars are excluded
    '''

    def __init__(self, mode, items=[]):
        '''initialize a CharFilter with [mode]
        if [mode] is True, the CharFilter will act as a whitelist
        if [mode] is False, the CharFilter will act as a blacklist
        [iter] can be optionally set to pre-load the whitelist/blacklist
        '''
        self._set = set(items)
        if isinstance(mode, FilterMode):
            self._mode = mode
        elif isinstance(mode, bool):
            if mode:
                self._mode = FilterMode.WHITELIST
            else:
                self._mode = FilterMode.BLACKLIST
        else:
            if mode == "whitelist":
                self._mode = FilterMode.WHITELIST
            elif mode == "blacklist":
                self._mode = FilterMode.BLACKLIST
            else:
                raise ValueError("Unrecognized mode %s" % repr(mode))
        
    
    def permits(self, other):
        '''returns True if Character/CharacterClass is allowed in
        the individual Character is evaluated first,
        then the Character's class, then all the Character's
        ancestor classes
        '''
        if isinstance(other, Character):
            if other in self._set:
                return self._mode.value
            # now try the Character's class
            other = type(other)
        if isinstance(other, CharacterClass):
            # cycle through each ancestor
            ancestors = filter(lambda x: isinstance(x, CharacterClass),
                              other.__mro__)
            for char_class in ancestors:
                if char_class in self._set:
                    return self._mode.value
        # "other" is neither a CharClass nor Character
        else:
            return False
        # the character / ancestors cannot be found in the list
        return not self._mode.value
    
    def include(self, other):
        '''Set the filter to return 'True' if [other] is supplied
        to permit()'''
        # check that other is a Character / CharacterClass
        assert(isinstance(other, Character) or
               isinstance(other, CharacterClass))
        if self._mode is FilterMode.WHITELIST:
            self._set.add(other)
        else:
            if other in self._set:
                self._set.remove(other)
    
    def exclude(self, other):
        '''Set the filter to return 'False' if [other] is supplied
        to permit()'''
        # check that other is a Character / CharacterClass
        assert(isinstance(other, Character) or
               isinstance(other, CharacterClass))
        if self._mode is FilterMode.WHITELIST:
            if other in self._set:
                self._set.remove(other)
        else:
            self._set.add(other)
    
    def __repr__(self):
        return "CharFilter(%r, %r)" % (self._mode.value, self._set)