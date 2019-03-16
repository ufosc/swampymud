import inventory as inv
import item

class Exit:
    '''Class representing an Exit
    Exits link a set of names with a particular location
    Contains: 
        a list of strings [exit names]
        destination [the location this points to]
    The list can be accessed by treating the this as an iterable
    For instance:
        "exit_name" in myExit [returns true if "exit_name" is in exit]
        for exit_name in myExit:
            [iterates over all the possible exit names]
    There are also several variables involved with filtering:
        access     = CharFilter that permits accessing the exit 
        visibility = CharFilter that permits viewing the exit
    '''
    def __init__(self, destination, name, other_names=[], access=None, visibility=None):
        '''Constructor for Exit
        Takes as input:
            location [location it points to]
            at least one name is required [primary name]
            additional names are optional
        optional keyword arguments:
            other_names = list of other names
            access  = set the access CharFilter(default: all permitted)
            visible = set the visibility CharFilter(default: all permitted)
        '''
        self._destination = destination
        self._names = [name] + list(other_names)
        self.access = access
        if access is None:
            self.access = character.CharFilter(False)
        self.visibility = visibility
        if visibility is None:
            self.visibility = character.CharFilter(False)

    @property
    def destination(self):
        return self._destination

    def __eq__(self, other):
        '''overriding ==
        if a name is provided, returns true this exit contains the name
        if a Location is provided, returns true if it is the destination
        else, returns true if the exit equals this exit
        '''
        if isinstance(other, str):
            return other in self
        elif isinstance(other, Location):
            return self._destination == other
        else:
            return self is other

    def __contains__(self, other):
        '''Overriding in operator
        Returns True if other is in list of names
        '''
        return other in self._names

    def __iter__(self):
        for name in self._names:
            yield name

    def __str__(self):
        '''overriding str() function'''
        return "%s -> %s" % (self._names[0], self._destination.name)


class Location:
    '''Class representing an in-game Location
    Maintains a list of players
    Contains a list of exits to other locations
    Has a name and description
    '''

    def __init__(self, name, description):
        self._character_list = []
        self._exit_list = []
        self._items = inv.Inventory()
        self.name = name
        self.description = description
        # this will come into play later
        self.owner = None

    def add_char(self, char):
        self._character_list.append(char)

    def remove_char(self, char, silent=False, exit=None):
        self._character_list.remove(char)
        if not silent:
            if exit is not None:
                self.message_chars("%s left via %s" % (char, exit))
            else:
                self.message_chars("%s left." % char)

    @property
    def character_list(self):
        return list(self._character_list)

    def message_chars(self, msg):
        '''send message to all characters currently in location'''
        for char in self._character_list:
            char.message(msg)

    def add_exit(self, exit_to_add):
        '''adds an exit, while performing a check for any ambigious names'''
        for exit_name in exit_to_add:
            assert exit_name not in self._exit_list, \
            "\nLocation:\t%s\nExit:\t\t%s" % (self.name, exit_to_add)
        self._exit_list.append(exit_to_add)

    def exit_list(self):
        '''returns a copy of private exit list'''
        return list(self._exit_list)

    def get_exit(self, exit_name):
        '''returns an exit corresponding to exit name
        if exit name is not in list, error is raised'''
        for exit in self._exit_list:
            if exit_name == exit:
                return exit
        raise KeyError("Exit with name \'%s\' not in Location %s"
                       % (exit_name, self.name))

    def add_item(self, item, quantity=1):     
        self._items.add_item(item, quantity)

    def remove_item(self, item, quantity=1):
        self._items.remove_item(item, quantity)

    def __contains__(self, other):
        '''Overriding in operator
        Returns True where
            other is an exit or string:
                and there exists an exit in _exit_list that matches
            other is a Character:
                and there exists a character in _character_list that matches
            other is an item:
                the item is present in the location's inventory
        '''
        if isinstance(other, Exit):
            return other in self._exit_list
        elif isinstance(other, character.Character):
            return other in self._character_list
        elif isinstance(other, item.Item):
            return other in self._items
        else:
            raise ValueError("Received %s, expected Exit, Character, or Item"
                             % type(other))

    def find(self, query):
        str_char_list = list(map(str, self._character_list))
        for char in str_char_list:
            if query == char:
                return self._character_list[str_char_list.index(char)]
        for exit_name in self._exit_list:
            if exit_name == query:
                return exit_name
        print("Preparing to search items. . .")
        if self._items.get_item(query):
            return self._items.get_item(query)
        return False

    def __repr__(self):
        #TODO: make the output more pythonic
        output = "Name:\t%s\n" % self.name
        output += "Desc:\t%s\n" % self.description
        output += "Chars:\t%s\n" % self._character_list
        output += "Exits:\t%s\n" % self._exit_list
        output += "Owner:\t%s\n" % self.owner
        return output


    def __str__(self, verbose=False):
        '''supplies a string
        if verbose is selected, description also supplied
        '''
        if verbose:
            return "%s:\n%s" % (self.name, self.description)
        else:
            return self.name

# explanation for this import statement being at the bottom
# location uses the Character class
# Character references Location class in body of Character class
import character
