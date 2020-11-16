"""Module defining the Location and Exit classes, used to construct the
in-game world.

You can conceive of the in-game world as a directed, acyclic graph.
With this model in mind, Locations act as vertices while Exits act as
edges.

At any given point in time, Locations may store characters, entities,
and items.
"""
from typing import Iterable
import swampymud.character as _char
import swampymud.util as _util
import swampymud.inventory
from swampymud import _types

class Exit(_types.Exit):
    """Class representing an in-game Exit.

    Exits link a set of names with a particular Location.
    """
    def __init__(self, destination: 'Location',
                 name: str,
                 other_names: Iterable[str] = (),
                 interact: _char.Filter = None,
                 perceive: _char.Filter = None,
                 hide_des: bool = False):
        """Create a new Exit.

        Required arguments:
        destination -- The location that this exit points to
        name -- primary name that this exit will appear under

        Optional arguments:
        other_names -- other names that users can refer to exit with
        interact -- a character.Filter controlling which characters can
        use this exit. By default, all characters can use this Exit
        perceive -- a character.Filter controlling which characters
        can view this exit. By default, all characters can see this Exit
        hide_des -- If true, then characters will not be shown the
        location that this Exit points to.
        """
        self._name = name
        self._destination = destination
        self.names = frozenset((name, *other_names))
        # if not either filter is not provided, create an empty
        # blacklist in its place
        self.interact = interact
        if interact is None:
            self.interact = _char.Filter(False)
        self.perceive = perceive
        if perceive is None:
            self.perceive = _char.Filter(False)
        self.hide_des = hide_des

    @property
    def destination(self):
        return self._destination

    def __repr__(self):
        """Return an a representation of the exit"""
        other_names = list(self.names - {self._name})
        return ("Exit({!r}, {!r}, other_names={!r}, "
                "interact={!r}, perceive={!r})".format(
                    self._destination, self._name, other_names,
                    self.interact, self.perceive
                ))

    def __str__(self):
        """return the primary name of this exit"""
        return self._name

    def view(self):
        """return a more informative image of this exit"""
        if self.hide_des:
            return str(self)
        else:
            return f"{self} -> {self._destination}"

    @staticmethod
    def from_dict(ex_dict):
        """creates an Exit from a pythonic representation"""
        # convert interact filter data into a character.Filter
        if "interact" in ex_dict:
            ex_dict["interact"] = _char.Filter.from_dict(ex_dict["interact"])
        # convert perceive filter data into a character.Filter
        if "perceive" in ex_dict:
            ex_dict["perceive"] = _char.Filter.from_dict(ex_dict["perceive"])
        return Exit(**ex_dict)

    def to_dict(self):
        """returns a pythonic representation of this Exit"""
        other_names = list(self.names)
        other_names.remove(self._name)
        data = {"name" : self._name, "other_names": other_names}
        data["destination"] = self._destination
        if self.hide_des:
            data["hide_des"] = True
        #TODO: elide Filter fields if they are empty blacklists
        data["interact"] = self.interact.to_dict()
        data["perceive"] = self.interact.to_dict()
        return data


class Location(_types.Location):
    """Class representing an in-game Location
    Maintains a list of players
    Contains a list of exits to other locations
    Has a name and description
    """

    def __init__(self, name: str, description: str):
        self.characters = []
        self.entities = []
        self._exit_list = []
        self.inv = swampymud.inventory.Inventory()
        self.name = name
        self.description = description

    def message(self, msg: str, exclude: Iterable = ()):
        """Send message to all characters and entites in this location.

        Optional arguments:
        exclude -- a SET of characters / entities to be excluded
        """
        for character in self.characters:
            if character not in exclude:
                character.message(msg)
        for entity in self.entities:
            if entity not in exclude:
                entity.on_message(msg)

    @property
    def exits(self):
        yield from self._exit_list

    def add_exit(self, exit_to_add):
        """adds an exit to this Location's list of exits, while checking
         for any ambigious names"""
        for exit_name in exit_to_add.names:
            for already_added in self.exits:
                assert exit_name not in already_added.names, \
                f"Location {self} already has exit with name '{exit_name}'"
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

    # TODO: add indefinite articles, oxford comma, etc.
    def view(self, viewer=None):
        """return an information-rich, user-focused view of this
        location.
        If [viewer] is supplied, then that character will be filtered
        out.
        """
        output = [str(self), self.description]

        # remove any exits that character cannot see
        exit_list = self._exit_list
        if viewer is not None:
            exit_list = [ex for ex in self.exits if ex.perceive.permits(char)]

        if exit_list:
            output.append("Exits:")
            output.extend([ex.view() for ex in exit_list])

        transition = "You see"

        if self.characters:
            output.append(f"""{transition} {', '.join(
                [char.view() for char in self.characters if char is not viewer]
            )}""")
            transition = "You also see"
        if self.entities:
            output.append(f"""{transition} {', '.join(
                [ent.view() for ent in self.entities]
            )}""")
        if self.inv:
            output.append("Items available:")
            output.append(self.inv.readable())
        return "\n".join(output)

    def __repr__(self):
        return f"Location{repr((self.name, self.description))}"

    def __str__(self):
        """return the name of the location"""
        return self.name

    # serialization-related methods
    @property
    def symbol(self):
        """return a guaranteed unique symbol for this location"""
        return f'{self.name.replace(" ", "")}#{_util.to_base(id(self), 62)}'

    @classmethod
    def load(self, data):
        """load in a location with data in the following form:
        { 'name' : [name of location], 'description': [description]"""
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

    # helper method for _util.find
    def find_child(self, params: _util.FindParams, **other_fields):
        # check that maxdepth hasn't been exceeded
        if params.maxdepth < 0:
            return
        # only check exits if Exit type is specified (or no type specified)
        if params.type is None or _util.has_subclass(params.type, _types.Exit):
            # exitsare not first class game objects, so we manually
            # sort through them
            for ex in self._exit_list:
                # check for any must have other_fields
                if not _util.obj_does_have(ex, other_fields):
                    continue
                # TODO: check params.optional
                # if a character is provided, see if it can interact
                # with this exit
                if not (params.pov is None or ex.interact.permits(params.pov)):
                    continue
                # check for any intersecting names
                if params.name is None or params.name & ex.names:
                    yield ex
        if params.type is None or _util.has_instance(params.type, _types.CharacterClass):
            for other_char in self.characters:
                if _util.find_check(other_char, params, **other_fields):
                    yield other_char
                # try to visit the character
                yield from _util.find_child(other_char, params.decrement(),
                                           **other_fields)
        if params.type is None or _util.has_instance(params.type, _types.ItemClass):
            # We don't decrement the maxdepth here, because the inventory
            # is considered to be a part of the location itself.
            # Items in a location's inventory might be on the ground,
            # on a table, etc.
            yield from self.inv.find_child(params, **other_fields)
        if params.type is None or _util.has_instance(params.type, _types.EntityClass):
            for ent in self.entities:
                if _util.find_check(ent, params, **other_fields):
                    yield ent
                yield from _util.find_child(ent, params.decrement(),
                                           **other_fields)
