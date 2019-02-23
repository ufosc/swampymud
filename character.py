'''Module defining the CharacterClass metaclass, and Character base class'''
import location
import control
import inventory
import item
from time import time


def camel_to_space(name):
    '''adds spaces before capital letters
    ex: CamelCaseClass => Camel Case Class'''
    output = ""
    for letter in name:
        if letter.upper() == letter:
            output += " "
        output += letter
    return output.strip()

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
        super().__init__(self, indices, options, phrase)
        self.indices = indices
        self.options = options
        self.phrase = phrase


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
            self.name = camel_to_space(cls)
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


def cooldown(delay):
    def delayed_cooldown(func):
        setattr(func, "last_used", 0)
        def cooled_down_func(*args, **kwargs):
            print(func.last_used + delay)
            print(time())
            diff = func.last_used + delay - time()
            if diff < 0:
                func.last_used = time()
                return func(*args, **kwargs)
            else:
                raise Exception("Cooldown expires in : %i" % diff)
        return cooled_down_func
    return delayed_cooldown


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
        self.set_location(self.starting_location, True)
        self.inv = inventory.Inventory()
        self.equip_dict = item.EquipTarget.make_dict(*self.equip_slots)
        self._parser = lambda line: Character.player_set_name(self, line)
        #TODO: make this a property
        self.is_alive = True

    def message(self, msg):
        '''send a message to the controller of this character'''
        if self.controller is not None:
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
            method(self, args[1::])
        except AmbiguityError as amb:
            self._parser = AmbiguityResolver(self, args, amb.indices, amb.phrase, amb.options)
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
            self.message("Error: '%s' not found." % (phrase) )
        else:
            raise AmbiguityError(indices, phrase, options)        

    def set_name(self, new_name):
        '''changes a characters's name, with all appropriate error checking'''
        if new_name in Character._names:
            raise CharException("Name already taken.")
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
        #TODO: move this functionality into the main module
        # For instance, take the new player and print the welcome message there
        from library import server
        server.send_message_to_all("Welcome, %s, to the server!" % self)
        self.cmd_look("")
    
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
    def set_location(self, new_location, silent=False, reported_exit=None):
        '''sets location, updating the previous and new locations as appropriate
        if reported_exit is supplied, then other players in the location 
        will be notified of which location he is going to
        '''
        try:
            self.location.remove_char(self, silent, reported_exit)
        except AttributeError:
            # location was none
            pass
        self.location = new_location
        self.location.add_char(self)

    #inventory/item related methods
    def equip(self, item, add_inv=True):
        print(item)
        if item.target in self.equip_dict:
            already_equip = self.equip_dict[item.target]
            if already_equip is not None:
                self.unequip(already_equip)
            item.equip(self)
            self.equip_dict[item.target] = item
            # check that add_inv is not present and true
            # if so, we dont remove the item on equip
            # duplicating it.
            if not add_inv:
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
        if len(args) == 0:
            self.message(self.__class__.help_menu)
            return
        command = args[0]
        if command in self.commands:
            self.message(str(self.commands[command].__doc__))
        else:
            self.message("Command \'%s\' not recognized." % command)

    def cmd_look(self, *args):
        '''Provide information about the current location.
        usage: look
        '''
        self.message(self.location.__str__(True))
        exit_list = self.location.exit_list()
        exit_msg = "\nExits Available:\n"
        if len(exit_list) == 0:
            exit_msg += "None"
        else:
            exit_msg += ", ".join(map(str, exit_list))
        self.message(exit_msg)
        char_list = self.location.get_character_list()
        char_msg = "You see"
        if len(char_list) == 0:
            pass
        elif len(char_list) == 1:
            char_msg += str(char_list[0]) + "."
            self.message(char_msg)
        elif len(char_list) == 2:
            char_msg += " and ".join(map(str, char_list)) + "."
            self.message(char_msg)
        else:
            char_msg += ", ".join(map(str, char_list[:-1])) + ", and " + char_list[-1] + "."
            self.message(char_msg)

    def cmd_say(self, *args):
        '''Say a message aloud, sent to all players in your current locaton.
        usage: say [msg]
        '''
        self.location.message_chars("%s : %s" % (self, " ".join(args)))
    
    def cmd_walk(self, *args):
        '''Walk to an accessible location.
        usage: walk [exit name]
        '''
        exit_name = " ".join(args)
        exit = self.location.get_exit(exit_name)
        self.set_location(exit.get_destination(), False, exit)
    
    # TODO: Move these into a "human" class
    # Why should we assume the player can do these things?
    def cmd_equip(self, args):
        '''Equip an equippable item from your inventory.'''
        item_name = " ".join(args)
        item = self._check_ambiguity(indices, item_name, self.inv.get_item(item_name))
        self.equip(item)

    def cmd_unequip(self, *args):
        '''Unequip an equipped item.'''
        options = []
        for target,item in self.equip_dict.items():
            if item == args[0]:
                options.append(item)
        item = self._handle_ambiguity(args[0], options)
        self.unequip(item) 
            
    def cmd_inv(self, *args):
        '''Show your inventory.'''
        output = ""
        for target, equipped in self.equip_dict.items():
            output += str(target).upper() + "\n\t" + str(equipped) + "\n"
        self.message(output + self.inv.readable())

    #TODO: provide a static method that transforms characters from one class to another

class AmbiguityResolver:
    def __init__(self, character, old_args, indices, phrase, options):
        self._character = character
        self._old_args = old_args
        self._index = index
        self._target = target
        self._indices = indices
        self._phrase = phrase
        self._options = options
        self._character.message(str(self))
    
    def __call__(self, inp):
        try:
            inp = int(inp)
        except ValueError:
            self._character.message("Please enter an integer.")
            return
        if inp not in range(len(options)):
            self._character.message("Provided integer out of range.")
            return
        choice = self._options(inp)
        old_args[indices] = choice
        self._character._parser = lambda line : Character.parse_command(character, line)
        self._character.parse_command()

    def __str__(self):
        string = "Multiple options for %s:\n" % self.phrase
        string += "\n".join(["\t%s) %s" % (index, repr(option)) for index, option in enumerate(self.options)])
        string += "\nEnter a number to resolve it:"   