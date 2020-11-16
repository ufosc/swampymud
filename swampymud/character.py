"""Module defining the CharacterClass metaclass and Character class,
which serves as the basis for all in-game characters.

This module also defines the 'Filter', used for CharacterClass-based
permissions systems, and 'Command', a wrapper that converts methods into
commands that can be invoked by characters.
"""
import re
import enum
import functools
import inspect
import weakref
import asyncio
import swampymud.inventory as inv
from swampymud import util, _types
from swampymud.util import parser
from swampymud.util.shadowdict import ShadowDict

class Filter:
    """Filter for screening out certain CharacterClasses and Characters
        _classes  - set of CharacterClasses tracked by the filter
        _include_chars - set characters to be included
        _exclude_chars - set characters to be excluded
        _mode - Filter.WHITELIST or Filter.BLACKLIST
            if WHITELIST is selected, only characters whose class is in
            _classes are allowed through the filter.
            if BLACKLIST is selected, only characters whose class is NOT
            in _classes are allowed through the filter.
        Note that _include_chars / _exclude_chars take precedence over
        the _classes. That is, if a WHITELIST includes the class
        Wizard, but Bill the Wizard is in _exclude_chars, Bill will not
        be permitted through the filter.
    """

    class _FilterMode(enum.Enum):
        """Enum representing whether a filter includes or excludes the
        classes that it tracks"""
        WHITELIST = True
        BLACKLIST = False

    WHITELIST = _FilterMode.WHITELIST
    BLACKLIST = _FilterMode.BLACKLIST

    def __init__(self, mode, classes=(),
                 include_chars=(), exclude_chars=()):
        """initialize a Filter with [mode]
        if [mode] is True, the Filter will act as a whitelist
        if [mode] is False, the Filter will act as a blacklist
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
        # store characters in a WeakSet, so that the Filter will not
        # prevent them from getting garbage collected
        self._include_chars = weakref.WeakSet(include_chars)
        self._exclude_chars = weakref.WeakSet(exclude_chars)
        if isinstance(mode, self._FilterMode):
            self._mode = mode
        elif isinstance(mode, bool):
            if mode:
                self._mode = Filter.WHITELIST
            else:
                self._mode = Filter.BLACKLIST
        else:
            if mode.lower() == "whitelist":
                self._mode = Filter.WHITELIST
            elif mode.lower() == "blacklist":
                self._mode = Filter.BLACKLIST
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
            if self._mode is Filter.WHITELIST:
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
                             f" received {type(other)}")

    def exclude(self, other):
        """Set the filter to return 'False' if [other] is supplied
        to permit()"""
        # check that other is a Character / CharacterClass
        if isinstance(other, CharacterClass):
            if self._mode == Filter.WHITELIST:
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
                             f" received {type(other)}")

    def __repr__(self):
        """overriding repr()"""
        return "Filter({!r}, {!r}, {!r}, {!r})".format(
            self._mode.value,
            set(self._classes),
            set(self._include_chars), set(self._exclude_chars)
        )

    @staticmethod
    def from_dict(filter_dict):
        """returns a Filter pythonic representation [filter_dict]"""
        return Filter(**filter_dict)

    def to_dict(self):
        """returns a pythonic representation of this Filter"""
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
    The default implementation of functools.partial does not normally
    support equality for mathematically sound reasons:
    https://bugs.python.org/issue3564

    With this class's equality operators, we aren't trying to solve an
    undecidable problem, but just confirm that two partially-applied
    functions have the same arguments and underlying functions.

    Optional fields, "name", "label", and "filter" are also provided.
    These fields store player-relevant information that are NOT factored
    into comparisons.

    In addition, this class has a convenience method, '.specify' to
    derive a new Command from an existing one by simply adding
    additional arguments. All other information (base function, names,
    etc.) will be propagated.

    While you can update Command.keywords, avoid doing so.
    All comparisons are based on the INITIAL keywords, so changing
    keywords after initialization is unsupported.
    """

    def __init__(self, *args, **kwargs):
        """initialize a Command like a functools.partial object"""
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
        self.filter = Filter(Filter.BLACKLIST)

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
        """return a help message for this command"""
        if self.label is not None:
            return f"{self} [from {self.label}]:\n{self.__doc__}"
        return f"{self}:\n{self.__doc__}"

    @staticmethod
    def with_traits(name: str = None, label: str = None,
                    filter: Filter = None):
        """decorator to easily wrap a function additional traits
        [name] = to invoke this Command, the Character must use [name]
            instead of the function's name
        [label] = the type of the command. (Affects help menu.)
        [filter] = if provided, determine which Characters / Classes
            are permitted to use this command. """
        def decorator(func):
            cmd = Command(func)
            cmd.name = name
            cmd.label = label
            if filter is not None:
                cmd.filter = filter
            return cmd
        return decorator


class CharacterClass(type, _types.CharacterClass):
    """metaclass establishing basic Character behaviors
    CharacterClasses include the following important attributes:
    - classname: how the class appears to the players
    - frequency: how often will new players spawn as this class
    - command_label: how  commands from this class appear in help menu
    """
    def __init__(cls, name, bases, namespace):
        # add the proper name, if not already provided
        if "classname" not in namespace:
            cls.classname = util.camel_to_space(name)
        # add a frequency field, if not already provided
        if "frequency" not in namespace:
            cls.frequency = 1
        # add a "command_label", if not already provided
        # this field is used in creating help menus
        if "command_label" not in namespace:
            cls.command_label = f"{cls} Commands"

        # commands that were implemented for this class
        cls._local_commands = {}
        for value in namespace.values():
            if isinstance(value, Command):
                value.label = cls.command_label
                cls._local_commands[str(value)] = value

        # all commands, with the most recent commands exposed
        cls._commands = {}
        for base in reversed(cls.__mro__):
            if not isinstance(base, CharacterClass):
                continue
            cls._commands.update(base._local_commands)
        cls._commands.update(cls._local_commands)

        # calling the super init
        super().__init__(name, bases, namespace)

    def __str__(cls):
        """overriding str to return classname"""
        return cls.classname


class Character(_types.Character, metaclass=CharacterClass):
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
        self.msgs = asyncio.Queue()

        # build dict from Commands collected by CharacterClass
        self.cmd_dict = ShadowDict()
        for (name, cmd) in self._commands.items():
            cmd = cmd.specify(self)
            # add command only if filter permits it
            if cmd.filter.permits(self):
                self.cmd_dict[name] = cmd
            # because sCommands are not bound properly like a normal
            # method, we must manually bind the methods
            # TODO: override getattribute__ to solve the super() issue?
            if isinstance(getattr(self, cmd.func.__name__), Command):
                setattr(self, cmd.func.__name__, cmd)

        # set up inventory and equipping items
        self.inv = inv.Inventory()
        self.equip_dict = inv.EquipTarget.make_dict(*self.equip_slots)

        # put character in default command parsing mode
        self._parser = self._command_parser

    def message(self, msg):
        """send a message to the controller of this character"""
        # place a
        self.msgs.put_nowait(msg)

    def command(self, msg):
        """issue 'msg' to character.
        character will parse 'msg' using its current parser."""
        if msg:
            self._parser(msg)

    def update(self):
        """periodically called method that updates character state"""
        print(f"[{self}] received update")

    def spawn(self, spawn_location):
        """Send a greeting to the character and put them into a
        name-selection mode.
        [spawn_location]: where the character should spawn after a name
            is submitted.
        """
        self.message(f"Welcome to our SwampyMud! You are a {type(self)}")
        self.message(f"What should we call you?")

        # set player location to spawn_location, but do not MOVE them
        # thus, player will not be available to attack
        self.location = spawn_location

        self._parser = self._join_parser

    def despawn(self):
        """method executed when a player dies"""
        self.message("You died.")
        if self.location is not None:
            self.location.message(f"{self} died.", exclude={self})
            try:
                self.location.characters.remove(self)
            except ValueError:
                pass
        self.location = None
        self._parser = self._dead_parser

    # default user-input parsers
    def _join_parser(self, new_name: str):
        """Parser for a newly joined player, used for selecting a valid
        name"""
        if len(new_name) < 2:
            self.message("Names must have at least 2 characters.")
            return
        if not new_name.isalnum():
            self.message("Names must be alphanumeric.")
            return
        # TODO: perform some kind of check to prevent players
        # from having the same name?
        self._name = new_name

        # move the player to the actual location they should be in
        loc = self.location
        self.location = None
        self.set_location(loc)

        self._parser = self._command_parser

    # simple regex for detecting quoted messages
    _quote_regex = re.compile(r"(['\"])(.*)\1")

    def _command_parser(self, line: str):
        """The default parser for a player."""
        args = util.parser.split_args(line)
        # starting a message with ' or " is a shortcut for the say cmd
        # so, we check for that first
        is_quoted = self._quote_regex.fullmatch(line)

        # if we only have one token, and it's quoted, send as message
        # e.g. _command_parser('"hello there!"')
        if is_quoted and len(args) == 1:
            message = is_quoted.group(2)
            self.say(["say", message])
            return

        # command is always the first word
        cmd_name = args[0]
        if not cmd_name in self.cmd_dict:
            self.message(f"Command '{cmd_name}' not recognized.")
            if line.startswith("'"):
                self.message("(Did you forget a ' at the end of your message?)")
            elif line.startswith('"'):
                self.message('(Did you forget a " at the end of your message?)')
            return
        cmd = self.cmd_dict[cmd_name]
        cmd(args)

    def _dead_parser(self, line: str):
        """Parser used when a character has died"""
        self.message("You have died. Reconnect to this server to start"
                     " as a new character.")

    # string-formatting methods
    def __repr__(self):
        """return a representation of Character"""
        if self._name is None:
            return f"{type(self).__name__}()"
        return f"{type(self).__name__}(name={self})"

    def __str__(self):
        """return the Character's name"""
        if self._name:
            return self._name
        return "[nameless character]"

    def view(self):
        """return a longer, user-focused depiction of Character"""
        if self._name is None:
            return f"A nameless {type(self)}"
        return f"{self._name} the {type(self)}"

    #location manipulation methods
    def set_location(self, new_location):
        """sets location, updating the previous and new locations as
        necessary and gathering commands from any entities in the
        location
        """
        try:
            self.location.characters.remove(self)
            # remove commands from all the entities
            # in the current location
            for entity in self.location.entities:
                entity.on_exit(self)
                entity.remove_cmds(self)
        except AttributeError:
            # location was none
            pass
        self.location = new_location
        self.location.add_char(self)
        # add commands from all the entities
        # in the current locations
        for entity in new_location.entities:
            entity.on_enter(self)
            entity.add_cmds(self)

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
        [from_inv]: if True, [item] should be removed from inventory
            first. If item is not found in inventory, the command fails.
            if False, [item] is not removed from inventory and will not
            be returned to inventory upon unequip.
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
        # TODO: update to allow players to 'inspect' certain objects
        self.message(self.location.view())

    @Command
    def say(self, args):
        """Send a message to all players in your current location.
        usage: say [msg]
        Note that you can drop the 'say' and just type your message
        in quotes:
        "Hello, how are you?"
        """
        msg = ' '.join(args[1:])
        if msg and self.location is not None:
            self.location.message(f"{self.view()}: {msg}")

    @Command
    def go(self, args):
        """Go to an accessible location.
        usage: go [exit name]
        """
        ex_name = " ".join(args[1:])
        exits = util.find(self.location, ex_name, type=_types.Exit)

        if not exits:
            self.message(f"No exit with name '{ex_name}'.")
            return
        found_exit = exits[0]

        if found_exit.interact.permits(self):
            old_location = self.location
            new_location = found_exit.destination
            new_location.message(f"{self} entered.")
            self.set_location(new_location)
            # TODO: only show the exit if a character can see it?
            old_location.message(f"{self} left through exit "
                                        f"'{ex_name}'.")
        else:
            if found_exit.perceive.permits(self):
                self.message(f"Exit '{ex_name}' is inaccessible to you.")
            # if the char can't see or interact with the exit,
            # we lie to them and pretend like it doesn't exist
            else:
                self.message(f"No exit with name '{ex_name}'.")

    @Command.with_traits(name="equip")
    def cmd_equip(self, args):
        """Equip an equippable item from your inventory."""
        if len(args) < 2:
            self.message("Provide an item to equip.")
            return
        item_name = " ".join(args[1::]).lower()
        found_items = util.find(self.inv, name=item_name)
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
        for _, equip_data in self.equip_dict.items():
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

        # TODO: find a way to provide type=Item
        found_items = util.find(self.location, name=item_name)
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
        found_items = util.find(self.inv, name=item_name)
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
        found_items = util.find(self.inv, name=item_name)
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
