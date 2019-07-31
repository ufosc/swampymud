'''Module defining the CharacterClass metaclass, and Character base class'''
import enum
import util
import control
import inventory
import item
from command import Command, CommandDict
import util
import util.english as eng

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
        _unique_cmds: a list of commands not found in base classes
        command_class: a list of commands not found in base classes
    '''
    def __init__(self, cls, bases, namespace):
        # creating the proper name, if one is not provided
        if "classname" not in namespace:
            self.classname = util.camel_to_space(cls)
        # adding a frequency field, if not already provided
        if "frequency" not in namespace:
            self.frequency = 1
        # creating a dictionary of commands
        # all functions starting with cmd_ are command

        # get a list of all character base classes
        char_bases = list(filter(lambda x: isinstance(x, CharacterClass),
                                 self.__mro__))
        self._unique_cmds = []
        # build list of unique commands
        for cmd_name in namespace:
            # check that the commands start wtih cmd_ and that it is callable
            # TODO: use a decorator instead
            # also check that the command is not defined in an ancestor class
            if (cmd_name.startswith("cmd_") and callable(namespace[cmd_name])
                and not (any(cmd_name in base._unique_cmds for base in char_bases))):
                self._unique_cmds.append(cmd_name)

        self.cmd_classes = {}
        for base in char_bases + [self]:
            if base._unique_cmds:
                if base.classname == "Default Character":
                    self.cmd_classes["Default"] = base._unique_cmds
                else:
                    self.cmd_classes[base.classname] = base._unique_cmds

        # calling the super init
        super().__init__(cls, bases, namespace)

    def __str__(cls):
        '''overriding str to return classname'''
        return cls.classname

class Character(control.Monoreceiver, metaclass=CharacterClass):
    '''Base class for all other CharacterClasses'''

    # Name for this class
    classname = "Default Character"

    # Starting location for this player
    starting_location = None
    # Valid equip slots for characters of this class
    equip_slots = []

    #TODO: remove the name argument?
    def __init__(self, name=None):
        super().__init__()
        self._name = name
        self.location = None
        self.inv = inventory.Inventory()
        self.cmd_dict = CommandDict()

        # add all the commands from this class
        for cmd_class, cmd_names in self.cmd_classes.items():
            for cmd_name in cmd_names:
                # create the command
                cmd = Command(cmd_name[4:], getattr(self, cmd_name), cmd_class)
                # add the command to the command dict
                self.cmd_dict.add_cmd(cmd)

        self.equip_dict = item.EquipTarget.make_dict(*self.equip_slots)
        self._parser = lambda line: self.parse_command(line)
        #TODO: make this a property
        self.is_alive = True

    @property
    def symbol(self):
        '''return a unique symbol for this Character'''
        # failsafe to ensure that Character always has a symbol
        # even if someone forgets to set self._symbol in the __init__
        if not hasattr(self, "_symbol"):
            symbol = "%s#%s" % (type(self).__name__,
                                util.to_base(id(self), 62))
            setattr(self, "_symbol", symbol)
        return self._symbol

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
        # TODO: match the beginning of the line with one of the cmds
        # to allow for multi-word commands
        cmd_name = args[0]
        if not self.cmd_dict.has_name(cmd_name):
            self.message("Command \'%s\' not recognized." % cmd_name)
            return
        cmd = self.cmd_dict.get_cmd(cmd_name)
        try:
            cmd(args)
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

    def __repr__(self):
        '''return a representation of the player'''
        if self._name is None:
            return "%s()" % type(self).__name__
        return "%s(name=%s)" % (type(self).__name__, self._name)

    def __str__(self):
        '''return the player's name'''
        if self._name is None:
            return self.info()
        else:
            return self._name
    
    def describe(self):
        ''' Describes the character '''
        return self.info()

    def info(self):
        '''return the player's name'''
        if self._name is None:
            return "A nameless %s" % type(self)
        return "%s the %s" % (self._name, type(self))

    # these methods need heavy refinement 
    def die(self, msg="%s died."):
        '''method executed when a player dies'''
        if msg is not None:
            if "%s" in msg:
                msg = msg % self
            self.location.message_chars(msg)
        self.location.remove_char(self)
        self.location = None
        self.detach()
        self.is_alive = False


    #location manipulation methods        
    def set_location(self, new_location):
        '''sets location, updating the previous and new locations as appropriate
        if reported_exit is supplied, then other players in the location 
        will be notified of which location he is going to
        '''
        try:
            self.location.remove_char(self)
            # remove commands from all the entities
            # in the current location
            for entity in self.location.entities:
                entity.remove_cmds(self)
        except AttributeError:
            # location was none
            pass
        self.location = new_location
        self.location.add_char(self)
        # add commands from all the entities
        # in the current locations
        for entity in new_location.entities:
            entity.add_cmds(self)

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
            item.add_cmds(self)
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
            item.remove_cmds(self)
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
            self.message(self.cmd_dict.help())
            return
        name = args[1]
        if self.cmd_dict.has_name(name):
            self.message(str(self.cmd_dict.get_cmd(name).help()))
        else:
            self.message("Command \'%s\' not recognized." % name)

    def cmd_look(self, args, verbose=True):
        '''Gives description of current location, or looks at a certain object/character
        in your location and/or inventory when called with arguments 
        usage: look
        OR
        usage: look [item/character/entity name]
        '''
        #TODO: move much of this functionality into the Location.info method
        # (replace the ugly formatting in that function)
        # add an optional char_class parameter so we can filter it
        if len(args) == 1:
            msg =  []
            msg.append(self.location.describe())
            exit_msg = []
            for exit_name in self.location.exits:
                exit_msg.append(str(exit_name))
            msg.append("\n".join(exit_msg))
            if verbose:
                char_list = self.location.characters
                try:
                        char_list.remove(self)
                except ValueError:
                    pass
                # Convert all chars in list to their strings
                char_list = list(map(str,char_list))
                entity_list = self.location.entities
                # The following moves all NPC entities from the entity list to the character list
                for entity in entity_list:
                    if entity.isNPC:
                        char_list.append(str(entity))
                        entity_list.remove(entity)
                if char_list:
                    char_msg = ["You see"]
                    # The function call from eng (util/english.py) formats the list to a gramatically correct english list
                    char_msg.append(eng.english_list_no_article(char_list))  
                    msg.append(" ".join(char_msg))
                # Convert all entities in list to their strings
                entity_list = list(map(str,entity_list))
                if entity_list:
                    entity_msg = ["You also see"]
                    # The function call from eng formats the list to a gramatically correct english list
                    entity_msg.append(eng.english_list_indefinite_article(entity_list))
                    msg.append(" ".join(entity_msg))
                # Creates list of items in location as strings
                item_list = list(map(str,self.location.all_items()))
                if item_list:
                    item_msg = ["Items available:"]
                    item_msg.append(util.group_and_count(item_list))
                    msg.append("\n".join(item_msg))
            self.message("\n".join(msg))
        else:
            query =  " ".join(args[1:])
            location_result = self.location.find(query)
            if(location_result):
                try:
                    self.message(location_result.describe())
                    return
                except:
                    # Change this message later
                    self.message("You weren't able to look at that!")
                    return
            inv_result = self.inv.find(query)
            if(inv_result):
                try:
                    self.message(inv_result.describe())
                    return
                except:
                    # Change this message later
                    self.message("You weren't able to look at that!") 
                    return
            self.message("You couldn't find anything by that name.")

    def cmd_say(self, args):
        '''Say a message aloud, sent to all players in your current locaton.
        usage: say [msg]
        '''
        self.location.message_chars("%s : %s" % (self, " ".join(args[1:])))

    def cmd_go(self, args):
        '''Walk to an accessible location.
        usage: walk [exit name]
        '''
        exit_name = " ".join(args[1:])
        #TODO: check for visibility
        found_exit = self.location.find_exit(exit_name)            
        if found_exit:
            #TODO: check for accessbility
            if found_exit.access.permits(self):
                self.take_exit(found_exit, True, 
                                "exit '%s'" % str(found_exit), True)
            elif not found_exit.visibility.permits(self):
                self.message("No exit with name %s" % exit_name)            
            else:
                self.message("The path to %s" % exit_name + " is unaccessible to you")
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

    def cmd_drop(self, args):
        '''Drop an item into the environment'''
        if len(args) < 2:
            self.message("Provide an item to drop.")
            return

        item_name = " ".join(args[1::])
        found_item = self.inv.find(item_name)
        if found_item:
            self.inv.remove_item(found_item)
            self.location.add_item(found_item)
        else:
            self.message("Could not find item with name '%s'" % item_name)

    def cmd_inv(self, args):
        '''Show your inventory.'''
        output = ""
        for target, equipped in self.equip_dict.items():
            output += str(target).upper() + "\n\t" + str(equipped) + "\n"
        self.message(output + self.inv.readable())

    #TODO: streamline this method
    def cmd_use(self,args):
        ''' Use an item
        Using an item on someone else:
        use [item_name] on [target's name]
        Using an item on yourself:
        use [item_name]
        '''
        if len(args) < 2:
            self.message("Provide an item to be used.")
        elif args[-1] == "on":
            if len(args) == 2:
                self.message("Provide an item to be used and a target to use it on.")
            else:
                self.message("Provide a target to use this item on.")
        elif "on" in args:
            i = args.index("on")
            item_name = " ".join(args[1:i])
            target_name = " ".join(args[i+1:])
            used_item = self.inv.find(item_name)
            target = self.location.find(target_name)
            if target and used_item:
                # This needs to be done more elegantly; perhaps there is a way to extract
                # information from the attribute error itself?
                if not isinstance(used_item, item.Usable):
                    self.message("This item is not of type usable.")
                try:
                    used_item.use(target,self)
                    self.inv.remove_item(used_item)
                except AttributeError:
                    # if item caused attribute error:
                    #      tell user that item is not of type usable
                    # if target caused attribute error:
                    self.message("You are unable to use that item on that target.")
                except:
                    self.message("You are unable to use that item on that target.")
            else:
                if not target:
                    self.message("An entity or character with that name could not be found.")
                if not used_item:
                    self.message("You do not have an item with that name.")
        else:
            item_name = " ".join(args[1:])
            used_item = self.inv.find(item_name)
            if used_item:
                if not isinstance(used_item, item.Usable):
                    self.message("This item is not of type usable.")
                try:
                    used_item.use(self,self)
                    self.inv.remove_item(used_item)
                except AttributeError as e:
                    # This needs to be changed later
                    print(e)
                except:
                    self.message("You are unable to use that item on yourself.")
            else:
                self.message("You do not have an item with that name.")

    def add_item(self, item):
        '''add [item] to player's inventory'''
        self.inv.add_item(item)

    @classmethod
    def load(cls, data):
        name = data["name"] if "name" in data else None
        return cls(name)

    def post_load(self, data):
        pass
    
    def save(self):
        '''return a pythonic representation of this Character'''
        return {"_type": type(self), "name": self._name}
    
    def children(self):
        '''pass'''
        return []
        #TODO: handle items here


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
        _classes  - set of CharacterClasses tracked by the filter
        _include_chars - set characters to be included, regardless of _classes
        _exclude_chars - set characters to be included, regardless of _classes
        _mode - FilterMode.WHITELIST or FilterMode.BLACKLIST
                if WHITELIST is selected, only tracked chars are allowed in
                if BLACKLIST is selected, tracked chars are excluded
    '''

    def __init__(self, mode, classes=[], include_chars=[], exclude_chars=[]):
        '''initialize a CharFilter with [mode]
        if [mode] is True, the CharFilter will act as a whitelist
        if [mode] is False, the CharFilter will act as a blacklist
        [classes] are those classes to be whitelisted/blacklisted
        [include_chars] are specific characters to be included
        [exclude_chars] are specific characters to be excluded
        '''
        self._classes = set(classes)
        for char in include_chars:
            if char in exclude_chars:
                raise ValueError("Cannot have character in both include" 
                                 " and exclude")
        for char in exclude_chars:
            if char in include_chars:
                raise ValueError("Cannot have character in both include"
                                 " and exclude")
        self._include_chars = set(include_chars)
        self._exclude_chars = set(exclude_chars)
        if isinstance(mode, FilterMode):
            self._mode = mode
        elif isinstance(mode, bool):
            if mode:
                self._mode = FilterMode.WHITELIST
            else:
                self._mode = FilterMode.BLACKLIST
        else:
            if mode.lower() == "whitelist":
                self._mode = FilterMode.WHITELIST
            elif mode.lower() == "blacklist":
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
            if other in self._include_chars:
                return True
            elif other in self._exclude_chars:
                return False
            # now try the Character's class
            other = type(other)
        if isinstance(other, CharacterClass):
            # cycle through each ancestor
            ancestors = filter(lambda x: isinstance(x, CharacterClass),
                              other.__mro__)
            for char_class in ancestors:
                if char_class in self._classes:
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
        if isinstance(other, CharacterClass):
            if self._mode is FilterMode.WHITELIST:
                self._classes.add(other)
            else:
                if other in self._classes:
                    self._classes.remove(other)
        elif isinstance(other, Character):
            if other in self._exclude_chars:
                self._exclude_chars.remove(other)
            self._include_chars.add(other)
        else:
            raise ValueError("Expected Character/CharacterClass,"
                             " received %s" % type(other))

    def exclude(self, other):
        '''Set the filter to return 'False' if [other] is supplied
        to permit()'''
        # check that other is a Character / CharacterClass
        if isinstance(other, CharacterClass):
            if self._mode is FilterMode.WHITELIST:
                if other in self._classes:
                    self._classes.remove(other)
            else:
                self._classes.add(other)
        elif isinstance(other, Character):
            if other in self._include_chars:
                self._include_chars.remove(other)
            self._exclude_chars.add(other)
        else:
            raise ValueError("Expected Character/CharacterClass,"
                             " received %s" % type(other))

    def __repr__(self):
        '''overriding repr()'''
        return ("CharFilter(%r, %r, %r, %r)" 
                % (self._mode.value, self._classes, self._include_chars,
                   self._exclude_chars))

    @staticmethod
    def from_dict(filter_dict):
        '''returns a CharFilter pythonic representation [filter_dict]'''
        return CharFilter(**filter_dict)

    def to_dict(self):
        '''returns a pythonic representation of this CharFilter'''
        data = {"mode" : self._mode.value }
        if self._classes:
            data["classes"] = list(self._classes)
        if self._include_chars:
            data["include_chars"] = list(self._include_chars)
        if self._exclude_chars:
            data["exclude_chars"] = list(self._exclude_chars)
        return data
