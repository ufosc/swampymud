"""Module defining the CharacterClass metaclass, and Character base class"""
import enum
import functools
import inspect
import inventory as inv
import util
from util.shadowdict import ShadowDict
import util.english as eng

class CharException(Exception):
    pass

class FilterMode(enum.Enum):
    WHITELIST = True
    BLACKLIST = False


class CharFilter:
    """Filter for screening out certain CharacterClasses and Characters
        _classes  - set of CharacterClasses tracked by the filter
        _include_chars - set characters to be included, regardless of _classes
        _exclude_chars - set characters to be included, regardless of _classes
        _mode - FilterMode.WHITELIST or FilterMode.BLACKLIST
                if WHITELIST is selected, only tracked chars are allowed in
                if BLACKLIST is selected, tracked chars are excluded
    """

    def __init__(self, mode, classes=frozenset(),
                 include_chars=frozenset(),
                 exclude_chars=frozenset()):
        """initialize a CharFilter with [mode]
        if [mode] is True, the CharFilter will act as a whitelist
        if [mode] is False, the CharFilter will act as a blacklist
        [classes] are those classes to be whitelisted/blacklisted
        [include_chars] are specific characters to be included
        [exclude_chars] are specific characters to be excluded
        """
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
        """returns True if Character/CharacterClass is allowed in
        the individual Character is evaluated first,
        then the Character's class, then all the Character's
        ancestor classes
        """
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
        """Set the filter to return 'True' if [other] is supplied
        to permit()"""
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
        """Set the filter to return 'False' if [other] is supplied
        to permit()"""
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
        """overriding repr()"""
        return ("CharFilter(%r, %r, %r, %r)"
                % (self._mode.value, self._classes, self._include_chars,
                   self._exclude_chars))

    @staticmethod
    def from_dict(filter_dict):
        """returns a CharFilter pythonic representation [filter_dict]"""
        return CharFilter(**filter_dict)

    def to_dict(self):
        """returns a pythonic representation of this CharFilter"""
        data = {"mode" : self._mode.value}
        if self._classes:
            data["classes"] = list(self._classes)
        if self._include_chars:
            data["include_chars"] = list(self._include_chars)
        if self._exclude_chars:
            data["exclude_chars"] = list(self._exclude_chars)
        return data


class Command(functools.partial):
    """A subclass of functools.partial that supports equality.
    The default implementation of functools.partial does not normally support
    equality for mathematically sound reasons:
    https://bugs.python.org/issue3564

    With this class's equality operators, we aren't trying to solve an
    undecidable problem, but just confirm that two partially-applied functions
    have the same arguments and underlying functions.

    Optional fields, "name" and "label" are also provided. These fields store
    player-relevant information that are NOT factored into comparisons.

    In addition, this class has a convenience method, '.specify' to create
    a new Command derived from one by simply adding additional arguments.
    All other information (base function, names, etc.) will be propagated.

    While you can update Command.keywords, avoid doing so.
    All comparisons are based on the INITIAL keywords, so changing keywords
    after initialization is unsupported.
    """

    def __init__(self, *args, **kwargs):
        """initialize a Command as you would a functools.partial object"""
        super().__init__()
        # creating an immutable set of keywords for comparisons
        self._keys = frozenset(self.keywords.items())
        # propagate the name and doc from the base function
        self.__name__ = self.func.__name__
        self.__doc__ = self.func.__doc__
        # try to clean the docstring, if one was provided
        try:
            self.__doc__ = inspect.cleandoc(self.__doc__)
        except AttributeError:
            pass
        # initialize satellite data
        self.name = None
        self.label = None
        # by default, add a filter that permits all (empty blacklist)
        self.filter = CharFilter(FilterMode.BLACKLIST)

    def __eq__(self, other):
        """Two commands are equal iff the base functions are equal,
        the args are equal, and the (initial) keywords are equal"""
        try:
            return (self.func, self.args, self._keys) == \
                   (other.func, other.args, other._keys)
        except AttributeError:
            # other is not a Command
            return False

    def __hash__(self):
        """overriding hash"""
        return hash((self.func, self.args, self._keys))

    def specify(self, *newargs, **new_keywords) -> 'Command':
        """Derive a new version of this function by applying additional
        arguments.

        If a provided keyword argument conflicts with a prior argument,
        the prior argument will be overriden.
        """
        args = self.args + tuple(newargs)
        keywords = self.keywords.copy()
        keywords.update(new_keywords)
        new_cmd = Command(self.func, *args, **keywords)
        # propagate the name and source
        new_cmd.name = self.name
        new_cmd.label = self.label
        # note that a new filter is not created, so any changes to the
        # old NewCommand will change to the old Command, and visa versa
        new_cmd.filter = self.filter
        return new_cmd

    def __str__(self):
        """returns the name of this command
        if no name is provided, func.__name__ is used
        """
        if self.name is None:
            return self.func.__name__
        return self.name

    def help_entry(self) -> str:
        if self.label is not None:
            return f"{self} [from {self.label}]:\n{self.__doc__}"
        return f"{self}:\n{self.__doc__}"

    @staticmethod
    def with_traits(name=None, label=None, filter=None):
        """decorator to easily wrap a function and add a name / source"""
        def decorator(func):
            cmd = Command(func)
            cmd.name = name
            cmd.label = label
            if filter is not None:
                cmd.filter = filter
            return cmd
        return decorator


class CharacterClass(type):
    """metaclass establishing basic Character behaviors
    CharacterClasses include the following important attributes:
    - classname: how the class appears to the players
    - frequency: how often will new players spawn as this class
    - command_label: how  commands from this class appear in help menu
    """
    def __init__(self, cls, bases, namespace):
        # add the proper name, if not already provided
        if "classname" not in namespace:
            self.classname = util.camel_to_space(cls)
        # add a frequency field, if not already provided
        if "frequency" not in namespace:
            self.frequency = 1
        # add a "command_label", if not already provided
        # this field is used in creating help menus
        if "command_label" not in namespace:
            self.command_label = f"{self} Commands"

        # commands that were implemented for this class
        self._local_commands = {}
        for value in namespace.values():
            if isinstance(value, Command):
                value.label = self.command_label
                self._local_commands[str(value)] = value

        # all commands, with the most recent commands exposed
        self._commands = {}
        for base in reversed(self.__mro__):
            if not isinstance(base, CharacterClass):
                continue
            self._commands.update(base._local_commands)
        self._commands.update(self._local_commands)

        # calling the super init
        super().__init__(cls, bases, namespace)

    def __str__(cls):
        """overriding str to return classname"""
        return cls.classname


class Character(metaclass=CharacterClass):
    """Base class for all other CharacterClasses"""

    # How this class appears to players
    classname = "Default Character"

    # Starting location for this class
    starting_location = None

    # Commands from this class will be labeled "Default Commands"
    command_label = "Default Commands"

    # Valid equip slots for characters of this class
    equip_slots = []

    def __init__(self, name=None):
        super().__init__()
        self._name = name
        self.location = None
        self.msgs = []

        # build dict from Commands collected by CharacterClass
        self.cmd_dict = ShadowDict()
        for (name, cmd) in self._commands.items():
            cmd = cmd.specify(self)
            # add command only if filter permits it
            if cmd.filter.permits(self):
                self.cmd_dict[name] = cmd
            # because NewCommands are not bound properly like a normal method
            # we must manually bind the methods
            # TODO: override getattribute__ to solve the super() issue?
            if isinstance(getattr(self, cmd.func.__name__), Command):
                setattr(self, cmd.func.__name__, cmd)

        # set up inventory and equipping items
        self.inv = inv.Inventory()
        self.equip_dict = inv.EquipTarget.make_dict(*self.equip_slots)

        # put character in default command parsing mode
        self._parser = self.parse_command

    def message(self, msg):
        """send a message to the controller of this character"""
        self.msgs.append(msg)
        # store this last message for convenience
        # TODO: remove this
        self.last_msg = msg

    def command(self, msg):
        """issue 'msg' to character.
        character will parse 'msg' using its current parser."""
        if msg:
            self._parser(msg)

    def update(self):
        """periodically called method that updates character state"""
        print(f"[{self}] received update")
        pass

    def spawn(self, spawn_location):
        """Send a greeting to the character, put them in name-entering mode
        [spawn_location]: where the character should spawn
        """
        self.message(f"Welcome to MuddySwamp! You are a {type(self)}")
        self.message(f"What should we call you?")

        # set player location to spawn_location, but do not MOVE them
        # thus, player will not be available to attack
        self.location = spawn_location

        self._parser = self._greeter

    def despawn(self):
        """method executed when a player dies"""
        if self.location is not None:
            self.location.message_chars(f"{self} died.")
            try:
                self.location.characters.remove(self)
            except ValueError:
                pass
        self.location = None
        # TODO: make a custom parser for dead people

    # default user-input parsers
    def _greeter(self, new_name: str):
        """parser for a player who has just joined, used for selecting a name"""
        if len(new_name) < 2:
            self.message("Names must have at least 2 characters.")
            return
        if not new_name.isalnum():
            self.message("Names must be alphanumeric.")
            return
        # TODO: perform some kind of check to prevent players having same name?
        self._name = new_name

        # move the player to the actual location they should be in
        loc = self.location
        self.location = None
        self.set_location(loc)

        self._parser = self.parse_command

    def parse_command(self, line: str = None, args=None):
        """The default parser for parses a command, raises AttributeError if command cannot be found"""
        if args is None and line is None:
            return
        if args is None:
            args = line.split()
        # TODO: match the beginning of the line with one of the cmds
        # to allow for multi-word commands
        # TODO: match the longest command
        cmd_name = args[0]
        if not cmd_name in self.cmd_dict:
            self.message("Command \'%s\' not recognized." % cmd_name)
            return
        cmd = self.cmd_dict[cmd_name]
        cmd(args)

    # string-formatting methods
    def __repr__(self):
        """return a representation of the player"""
        if self._name is None:
            return f"{type(self).__name__}()"
        return f"{type(self).__name__}(name={self})"

    def __str__(self):
        """return the Character's name"""
        if self._name:
            return self._name
        return "[nameless character]"

    def view(self):
        """return a more lengthy, user-focused description of the Character"""
        if self._name is None:
            return f"A nameless {type(self)}"
        return f"{self._name} the {type(self)}"

    #location manipulation methods
    def set_location(self, new_location):
        """sets location, updating the previous and new locations as appropriate
        if reported_exit is supplied, then other players in the location
        will be notified of which location he is going to
        """
        try:
            self.location.characters.remove(self)
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

    def take_exit(self, exit,
                  show_leave=True, leave_via=None,
                  show_enter=True, enter_via=None):
        """
        high-level function for characters to change rooms
        [exit]: exit taken by the player
        [show_leave]: if True, characters in the current location are notified
        of this character leaving
        [leave_via]: if a string is provided, then players are informed which
        exit the character left through
        [show_enter]: if True, characters in the destination are notified of
        this character arriving
        [enter_via]: if True, characters in the destination are notified of
        this character arriving
        """
        # send entry message first, so that this character doesn't see it
        if show_enter:
            try:
                if enter_via:
                    exit.destination.message_chars(f"{self} entered through {enter_via}.")
                else:
                    exit.destination.message_chars(f"{self} entered.")
            except AttributeError:
                # self.location was None
                pass
        # change the location
        old_loc = self.location
        self.set_location(exit.destination)
        # TODO have the player look around
        # self.cmd_look(["look"], verbose=False)
        # now send the exit message
        if show_leave:
            try:
                if leave_via:
                    old_loc.message_chars(f"{self} left through {leave_via}.")
                else:
                    old_loc.location.message_chars(f"{self} left.")
            except AttributeError:
                # self.location was None
                pass

    #inventory/item related methods
    def add_item(self, item, amt=1):
        """add [item] to player's inventory"""
        # if the item is an ItemStack, unpack it first
        if isinstance(item, inv.ItemStack):
            self.inv.add_item(item.copy(), item.amount)
        self.inv.add_item(item, amt)

    def equip(self, item, from_inv=True):
        """place [item] in this player's equip dict
        [item]: item to Equip
        [from_inv]: if True, [item] should be removed from inventory first
        if False, [item] is not removed from inventory and returned on unequip

        sends character an error message if [item] if not Equippable or if [self]
        lacks the proper slots to equip this item
        sends character an error message if [from_inv] is True
        but this character does not have a copy of [item] in its inventory
        """
        # duck test that the item is even equippable
        try:
            target = item.target
        except AttributeError:
            self.message(f"{item} cannot be equipped.")
            return
        if target in self.equip_dict:
            # check remove_inv, if true, remove item from inventory
            # this avoids duplication
            if from_inv:
                try:
                    self.inv.remove_item(item)
                # item not found
                except KeyError:
                    self.message(f"Cannot equip {item}-"
                                 "not found in inventory.")
                    return
            # check for an already equipped weapon, unequip it
            if self.equip_dict[target] is not None:
                self.unequip(target)
            item.on_equip(self)
            item.add_cmds(self)
            self.equip_dict[item.target] = item, from_inv
        # class doesn't have an equip target for this item, cannot equip
        else:
            self.message(f"Cannot equip item {item} to {target}.")
            return

    def unequip(self, target):
        """updates this character's equip_dict such that the [target]
        is set to None and any item at that position is unequipped
        [target]: an EquipTarget"""
        # test if anything is even equipped
        # also duck test to see if this character even has [target]
        # in its equip slots
        try:
            if self.equip_dict[target] is None:
                self.message(f"No item equipped on target {target}.")
                return
        except KeyError:
            self.message(f"{type(self)} does not possess"
                         f" equip slot '{target}'.")
            return
        equipped, from_inv = self.equip_dict[target]
        equipped.on_unequip(self)
        equipped.remove_cmds(self)
        self.equip_dict[target] = None
        # if item was from character's inventory, return it
        if from_inv:
            self.inv.add_item(equipped)

    # default commands
    @Command
    def help(self, args):
        """Show relevant help information for a particular command.
        usage: help [command]
        If no command is supplied, a list of all commands is shown.
        """
        if len(args) < 2:
            # TODO: cache this or something
            menu = self.help_menu()
            self.message(menu)
        else:
            name = args[1]
            try:
                self.message(self.cmd_dict[name].help_entry())
            except KeyError:
                self.message(f"Command '{name}' not recognized.")

    @Command
    def look(self, args):
        """Gives a description of your current location.
        usage: look
        """
        # TODO: update to allow players to 'inspect' certain objects in detail
        self.message(self.location.view())

    @Command
    def say(self, args):
        """Say a message aloud, sent to all players in your current locaton.
        usage: say [msg]
        """
        msg = ' '.join(args[1:])
        if msg and self.location is not None:
            self.location.message_chars(f"{self.view()}: {msg}")

    @Command
    def go(self, args):
        """Go to an accessible location.
        usage: go [exit name]
        """
        ex_name = " ".join(args[1:])
        # TODO handle ambiguity?
        # structural solution might be avoided here
        found_exit = self.location.find_exit(ex_name)
        if found_exit:
            if found_exit.access.permits(self):
                # TODO: replace this with a more generic name
                self.take_exit(found_exit, show_leave=True, show_enter=True,
                               leave_via=f"exit '{ex_name}'")
            elif not found_exit.visibility.permits(self):
                self.message(f"No exit with name '{ex_name}'.")
            else:
                self.message(f"Exit '{ex_name}' is unaccessible to you.")
        else:
            self.message(f"No exit with name '{ex_name}'.")

    @Command.with_traits(name="equip")
    def cmd_equip(self, args):
        """Equip an equippable item from your inventory."""
        if len(args) < 2:
            self.message("Provide an item to equip.")
            return
        item_name = " ".join(args[1::]).lower()
        found_items = list(self.inv.find(name=item_name))
        if len(found_items) == 1:
            self.equip(found_items[0][0])
        elif len(found_items) > 1:
            #TODO handle ambiguity
            self.message(f"Ambigious item name. Results={found_items}")
        else:
            self.message(f"Could not find item '{item_name}'.")

    @Command.with_traits(name="unequip")
    def cmd_unequip(self, args):
        """Unequip an equipped item.
        Usage: unequip [item]"""
        if len(args) < 2:
            self.message("Provide an item to equip.")
            return
        item_name = " ".join(args[1::]).lower()
        # search through the items in the equip_dict
        found_items = []
        for target, equip_data in self.equip_dict.items():
            if equip_data is None:
                continue
            item, _ = equip_data
            if str(item).lower() == item_name:
                found_items.append(item)
        if len(found_items) == 1:
            self.unequip(found_items[0].target)
        elif len(found_items) > 1:
            #TODO handle ambiguity
            self.message(f"Ambigious item name. Results={found_items}")
        else:
            self.message(f"Could not find equipped item '{item_name}'.")

    @Command
    def pickup(self, args):
        """Pick up item from the environment."""
        if len(args) < 2:
            self.message("Provide an item to pick up.")
            return
        item_name = " ".join(args[1::]).lower()
        found_items = list(self.location.inv.find(name=item_name))
        if len(found_items) == 1:
            item = found_items[0][0]
            self.location.inv.remove_item(item)
            self.inv.add_item(item)
        elif len(found_items) > 1:
            #TODO handle ambiguity
            self.message(f"Ambigious item name. Results={found_items}")
        else:
            self.message(f"Could not find item '{item_name}' to pick up.")

    @Command
    def drop(self, args):
        """Drop an item into the environment"""
        if len(args) < 2:
            self.message("Provide an item to drop.")
            return
        item_name = " ".join(args[1:]).lower()
        found_items = list(self.inv.find(name=item_name))
        if len(found_items) == 1:
            item = found_items[0][0]
            self.inv.remove_item(item)
            self.location.inv.add_item(item)
        elif len(found_items) > 1:
            #TODO handle ambiguity
            self.message(f"Ambigious item name. Results={found_items}")
        else:
            self.message(f"Could not find item '{item_name}' to drop.")

    @Command.with_traits(name="inv")
    def cmd_inv(self, args):
        """Show your inventory.
        usage: inv"""
        # create a string representation of the equipped items
        equipped = []
        for target, item in self.equip_dict.items():
            if item is None:
                equipped.append(f"{target}: none")
            else:
                equipped.append(f"{target}: {item[0]}")
        equipped.sort()
        self.message("\n".join(equipped))
        inv_msg = self.inv.readable()
        # only send a message if inv has items
        if inv_msg:
            self.message(inv_msg)

    @Command.with_traits(name="use")
    def cmd_use(self, args):
        """ Use an item.
        usage: use [item] [options for item]
        Options may vary per item.
        """
        # TODO: allow players to use accessible items in location?
        if len(args) < 2:
            self.message("Please specify an item.")
            return
        item_name = args[1]
        found_items = list(self.inv.find(name=item_name))
        if len(found_items) == 1:
            item = found_items[0][0]
            self.inv.remove_item(item)
            item.on_use(self, args[2:])
            # replace the item
            self.inv.add_item(item)
        elif len(found_items) > 1:
            #TODO handle ambiguity
            self.message(f"Ambigious item name. Results={found_items}")
        else:
            self.message(f"Could not find item '{item_name}' to use.")

    # miscellaneous methods
    def help_menu(self) -> str:
        sources = {}
        # walk the mro, to get the list of CharacterClasses in order
        for cls in reversed(type(self).__mro__):
            if isinstance(cls, CharacterClass):
                sources[cls.command_label] = []
        for name, cmd in self.cmd_dict.items():
            try:
                sources[cmd.label].append(name)
            except KeyError:
                sources[cmd.label] = [name]
        # unpack the dictionary in reverse order
        output = []
        while sources:
            source, names = sources.popitem()
            output.append(f"---{source}---")
            output.append(" ".join(names))
        return "\n".join(output)


    # serialization-related methods
    @property
    def symbol(self):
        """return a unique symbol for this Character"""
        # failsafe to ensure that Character always has a symbol
        # even if someone forgets to set self._symbol in the __init__
        if not hasattr(self, "_symbol"):
            symbol = "{}#{}".format(type(self).__name__,
                                    util.to_base(id(self), 62))
            setattr(self, "_symbol", symbol)
        return self._symbol

    @classmethod
    def load(cls, data):
        name = data["name"] if "name" in data else None
        return cls(name)

    def post_load(self, data):
        pass

    def save(self):
        """return a pythonic representation of this Character"""
        return {"_type": type(self), "name": self._name}

    def children(self):
        """pass"""
        return []
        #TODO: handle items here

