import location
import control
import inventory
import item

'''Module defining the CharacterClass metaclass, and Character base class'''

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
    def __init__(self, query, options):
        super().__init__()
        self.options = options
        self.query = query
        self.command = "[command]"
        self.old_args = []

    def __str__(self):
        string = "Multiple options for %s:\n" % self.query
        string += "\n".join(["\t%s) %s" % (index, repr(option)) for index, option in enumerate(self.options)])
        string += "\nEnter a number to resolve it:"
        return string

    def handle(self, num):
        num = int(num.strip())
        choice = self.options[num]
        for index, arg in enumerate(self.old_args):
            if arg == self.query:
                self.old_args[index] = choice
        return self.old_args


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


class Character(control.Monoreceiver, metaclass=CharacterClass):
    '''Base class for all other characters'''

    starting_location = location.Location("NullLocation", "Default Location")
    name = "Default Character"
    names = {}
    equip_slots = []
    

    def __init__(self):
        super().__init__()
        self.name = None
        self.location = None
        self.set_location(self.starting_location, True)
        self.inv = inventory.Inventory()
        self.equip_dict = item.EquipTarget.make_dict(*self.equip_slots)
        # consider moving prempt into Monoreceiver class
        self.prempt = None

    def message(self, msg):
        '''send a message to the controller of this character'''
        if self.controller is not None:
            self.controller.write_msg(msg)
    
    def detach(self, hard_detach=False):
        '''removes a character from its controller
        if hard_detach is True, the player enter its
        death process, defined by die
        '''
        # calling method from control.Receiver
        super().detach()
        if hard_detach:
            self.die()

    def update(self):
        while self.controller.has_cmd():
            line = self.controller.read_cmd()
            if line.strip() == "":
                continue
            # TODO: turn this into a premption
            if self.name is None:
                try:
                    self.player_set_name(line.strip())
                except Exception as ex:
                    self.message(str(ex))
                finally:
                    return
            if self.prempt is not None:
                try:
                    # handling the prempt
                    new_args = self.prempt.handle(line)
                    print(new_args)
                    # getting new args
                    self.parse_command(*new_args)
                    self.prempt = None
                except CharException as ex:
                    self.message(str(ex))
            else:
                try:
                    self.parse_command(*line.split(" "))
                except AmbiguityError as amb:
                    amb.old_args = line.split(" ")
                    self.message(str(amb))
                    self.prempt = amb
                except CharException as ex:
                    self.message(str(ex))

    def parse_command(self, *args):
        '''parses a command, raises AttributeError if command cannot be found'''
        command = args[0]
        if command not in self.commands:
            raise CharException("Command \'%s\' not recognized." % command)
  
        method = self.commands[command]
        method(self, *args[1::])
    
    def _handle_ambiguity(self, query, options):
        '''wraps function outputs to handle ambiguity
        if no option is returned, then raise an error
        if multiple options are found, raise an ambiguity error
        '''
        if len(options) == 1:
            return options[0]
        elif len(options) == 0:
            raise CharException("Error: '%s' not found." % (query) )
        else:
            raise AmbiguityError(query, options)        

    def set_name(self, new_name):
        '''changes a characters's name, with all appropriate error checking'''
        if new_name in Character.names:
            raise CharException("Name already taken.")
        if self.name is not None:
            del(self.names[self.name])
        self.name = new_name
        self.names[self.name] = self
    
    def player_set_name(self, new_name):
        '''intended for first time players set their name'''
        if not new_name.isalnum():
            raise CharException("Names must be alphanumeric.")
        self.set_name(new_name)
        #TODO: replace this when appropriate
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

    # these methods could use refinement 
    def __del__(self):
        self.die()

    def die(self):
        '''method executed when a player dies'''
        self._remove_references()

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
            del self.names[self.name]
        except KeyError:
            pass

    #location manipulation methods        
    def set_location(self, new_location, silent=False, reported_exit=None):
        '''sets location, updating the previous and new locations as appropriate
        if reported_exit is supplied, then other players in the location 
        will be notified of which location he is going to
        '''
        # break recursive loop
        if self.location == new_location:
            return
        try:
            self.location.remove_char(self, silent, reported_exit)
        except AttributeError:
            # location was none
            pass
        self.location = new_location
        self.location.add_char(self)

    #inventory/item related methods
    def equip(self, item, **kwargs):
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
            if "add_inv" not in kwargs or not kwargs["add_inv"]:
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
    def cmd_help(self, *args):
        '''Show relevant help information for a particular command.
        usage: help [command]
        If no command is supplied, a list of all commands is shown.
        '''
        if len(args) == 0:
            self.message(self.__class__.help_menu)
            return
        command = args[0]
        if command in self.commands:
            self.message(self.commands[command].__doc__)
        else:
            raise CharacterException("Command \'%s\' not recognized." % command)

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
            exit_msg += " ,".join(map(str, exit_list))
        self.message(exit_msg)

    def cmd_say(self, *args):
        '''Say a message aloud, sent to all players in your current locaton.
        usage: say [msg]
        '''
        self.location.message_chars("%s : %s" % (self, " ".join(args)))
    
    def cmd_walk(self, *args):
        '''Walk to an accessible location.
        usage: walk [exit name]
        '''
        exit_name = args[0]
        exit = self.location.get_exit(exit_name)
        self.set_location(exit.get_destination(), False, exit)
    
    def cmd_equip(self, *args):
        '''Equip an equippable item from your inventory.'''
        item_name = args[0]
        item = self._handle_ambiguity(item_name, self.inv.get_item(item_name))
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