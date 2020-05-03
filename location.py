import inventory as inv
import item
from character import Character, CharFilter
import util

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
    def __init__(self, destination, name, other_names=[],
                 access=None, visibility=None, hide_des=False):
        '''Constructor for Exit
        Takes as input:
            location [location it points to]
            at least one name is required [primary name]
            additional names are optional
        optional keyword arguments:
            other_names = list of other names
            access  = set the access CharFilter(default: all permitted)
            visible = set the visibility CharFilter(default: all permitted)
            hide_des = make the destination invisible to players
        '''
        self._name = name
        self._destination = destination
        self._nameset = set((name, *other_names))
        self.access = access
        if access is None:
            self.access = CharFilter(False)
        self.visibility = visibility
        if visibility is None:
            self.visibility = CharFilter(False)
        self.hide_des = hide_des

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

    def __repr__(self):
        '''Return an a representation of the exit'''
        other_names = list(set(self._nameset - set((self._name,))))
        return ("Exit(%r, %r, other_names=%r, access=%r, visibility=%r)"
               % (self._destination, self._name,
                  other_names,
                  self.access, self.visibility))

    def __contains__(self, other):
        '''Overriding in operator
        Returns True if other is in list of names
        '''
        return other in self._nameset

    def __iter__(self):
        for name in self._nameset:
            yield name

    def __str__(self):
        '''return the primary name of this exit'''
        return self._name

    def view(self):
        '''return a more informative image of this exit'''
        if self.hide_des:
            return str(self)
        else:
            return f"{self} -> {self._destination}"

    @staticmethod
    def from_dict(ex_dict):
        '''creates an Exit from a pythonic representation'''
        # convert access filter data into a CharFilter
        if "access" in ex_dict:
            ex_dict["access"] = CharFilter.from_dict(ex_dict["access"])
        # convert visibility filter data into a CharFilter
        if "visibility" in ex_dict:
            ex_dict["visibility"] = CharFilter.from_dict(ex_dict["visibility"])
        return Exit(**ex_dict)

    def to_dict(self):
        '''returns a pythonic representation of this Exit'''
        other_names = list(self._nameset)
        other_names.remove(self._name)
        data = {"name" : self._name, "other_names": other_names}
        data["destination"] = self._destination
        if self.hide_des:
            data["hide_des"] = True
        #TODO: elide CharFilter fields if they are empty blacklists
        data["access"] = self.access.to_dict()
        data["visibility"] = self.access.to_dict()
        return data


class Location:
    '''Class representing an in-game Location
    Maintains a list of players
    Contains a list of exits to other locations
    Has a name and description
    '''

    def __init__(self, name, description):
        self.characters = []
        self.entities = []
        self._exit_list = []
        self.inv = inv.Inventory()
        self.name = name
        self.description = description

    def message_chars(self, msg):
        '''send message to all characters currently in location'''
        for char in self.characters:
            char.message(msg)

    @property
    def exits(self):
        yield from self._exit_list

    def add_exit(self, exit_to_add):
        '''adds an exit, while performing a check for any ambigious names'''
        for exit_name in exit_to_add:
            for already_added in self.exits:
                assert exit_name not in already_added, \
                "Location '%s' already has exit with name '%s'" % (self.name, exit_name)
        self._exit_list.append(exit_to_add)

    def find(self, query):
        for char in self.characters:
            if str(char) == query:
                return char
        for loc_exit in self.exits:
            if str(loc_exit) == query:
                return loc_exit
        item_result = self.inv.find(name=query)
        if item_result:
            return item_result
        for entity in self.entities:
            if str(entity) == query:
                return entity

    def find_exit(self, exit_name):
        '''returns an exit corresponding to exit name
        returns 'None' if no exit is found'''
        for exit in self._exit_list:
            if exit_name == exit:
                return exit

    # TODO: add indefinite articles, oxford comma, etc.
    def view(self, viewer=None):
        '''return an information-rich, user-focused view of this location
        If [perspective] is supplied, then that character will be filtered out.'''
        output = [str(self), self.description]

        transition = "You see "

        # remove any exist that character cannot see
        exit_list = self._exit_list
        if viewer is not None:
            exit_list = [ex for ex in self._exit_list if ex.visibility.permits(char)]

        if exit_list:
            output.append("Exits:")
            output.extend([ex.view() for ex in exit_list])

        if self.characters:
            output.append(f"""{transition} {', '.join(
                [char.view() for char in self.characters if char is not viewer]
            )}""")
            transition = "You also see"
        if self.entities:
            output.append(f"""{transition} {', '.join(
                [ent.view() in self.entities]
            )}""")
        if self.inventory:
            output.append("Items available:")
            output.append(util.group_and_count(list(self.inventory)))

    def __repr__(self):
        return f"Location{repr((self.name, self.description))}"

    def __str__(self):
        '''return the name of the location'''
        return self.name

    # serialization-related methods
    @property
    def symbol(self):
        '''return a guaranteed unique symbol for this location'''
        return f'{self.name.replace(" ", "")}#{util.to_base(id(self), 62)}'

    @classmethod
    def load(self, data):
        '''load in a location with data in the following form:
        { 'name' : [name of location], 'description': [description]'''
        return Location(data["name"], data["description"])

    def post_load(self, data):
        if "exits" in data:
            for exit_data in data["exits"]:
                self.add_exit(Exit.from_dict(exit_data))

    def save(self):
        return {
            "_type": Location,
            "name": self.name,
            "description": self.description,
            "exits":
                [ex.to_dict() for ex in self.exits]
        }

    def children(self):
        for char in self.characters:
            yield char
        for entity in self.entities:
            yield entity
        #TODO: add items

    # these methods are redundant, but necessary for when World Tree
    # is traversed during serialization
    def add_char(self, char):
        self.characters.append(char)

    def add_entity(self, entity):
        self.entities.append(entity)

    def add_item(self, item, quantity=1):     
        self.inv.add_item(item, quantity)
