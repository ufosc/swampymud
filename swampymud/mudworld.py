"""This module provides methods for serializing / deserializing game data,
and also defines the World class"""
import importlib
import warnings
from collections import defaultdict
from random import choices
import yaml
from swampymud.location import Location
from swampymud.character import CharacterClass, Character
from swampymud.item import ItemClass, Item
from swampymud.entity import EntityClass, Entity
from swampymud.mudscript import LocationExport

# TODO: change these to sets?
_GAME_OBJS = [Character, Item, Entity, Location]
_GAME_CLASSES = [CharacterClass, ItemClass, EntityClass]

def read_worldfile(save_name):
    """return a parsed world file"""
    #TODO: add a 'gzip' layer to this
    with open(save_name) as save_file:
        save_data = save_file.read()
    save_data = yaml.safe_load(save_data)
    # TODO: maybe add a link to the documentation for this one?
    if not isinstance(save_data, dict):
        raise TypeError(f"Received '{type(save_data)}' instead a dict "
                        f"in world file {save_name}'. (World files should "
                        "contain three sections: prelude, personae, tree.")
    # check that we have exactly these three sections
    valid_sections = set(("prelude", "personae", "tree"))
    input_sections = set(save_data)
    unexpected = list(input_sections - valid_sections)
    if unexpected:
        raise ValueError(f"Found unexpected section(s) {unexpected} "
                         f"in world file '{save_name}'")
    missing = list(valid_sections - input_sections)
    if missing:
        raise ValueError(f"Missing section(s) {missing} "
                         f"in world file '{save_name}'")
    # to allow for 'blank' sections, convert any None's to empty dicts
    for sect, value in save_data.items():
        if value is None:
            save_data[sect] = {}
    return save_data


def write_worldfile(save_name, save_data):
    """write [save_data] to file [save_name] in YAML format"""
    #TODO add a gzip layer to this
    save_data = yaml.dump(save_data, default_flow_style=False)
    with open(save_name, 'w') as save_file:
        save_file.write(save_data)


def load_prelude(prelude_data):
    #TODO use context manager for locations
    cls_dict = {}
    for fname, classes in prelude_data.items():
        # convert the pathname to a module name
        mod_name = fname.replace('.py', '').replace('/', '.')
        # attempt to import it
        mod = importlib.import_module(mod_name)
        # try to get each class in the module
        for cls_name in classes:
            cls = getattr(mod, cls_name)
            # check that class is a valid class to import
            if any(map(lambda x: isinstance(cls, x), _GAME_CLASSES)):
                cls_dict[cls_name] = cls
            # if not, raise an exception
            else:
                #TODO: use a more specific exception
                raise TypeError("{!r} is wrong type, expected one of"
                                "{}".format(cls, _GAME_CLASSES))
    return cls_dict

def skim_for_locations(personae):
    """extract locations from personae
    warns if any locations are missing fields
    """
    skipped = 0
    locs = {}
    for key, data in personae.items():
        # assume that _type has already been checked
        if data["_type"] == "^Location":
            try:
                locs[key] = Location(data["name"], data["description"])
            except KeyError as err:
                warnings.warn(f"Location '{key}' missing required field "
                              f"'{err.args[0]}'. All locations must provide "
                              "a name and description.")
                skipped += 1
    if skipped:
        warnings.warn(f"Skipped {skipped} Location(s).", stacklevel=10000)
    return locs


def load_object(obj_data, type_names):
    """load a personae-formatted object with [obj_data]"""
    # get object's type, which should be prefixed with "^"
    ObjType = type_names[obj_data["_type"][1:]]
    return ObjType.load(obj_data)


def update_symbols(data, obj_names, type_names):
    """returns a deep copy of [data] where all symbols (names prefixed with $)
    have been recursively replaced according to the dictionary [obj_names]"""
    # base case 1--data is a string
    if isinstance(data, str):
        if data.startswith("$"):
            # data is an object symbol, return the corresponding object
            return obj_names[data[1:]]
        elif data.startswith("^"):
            # data is a type symbol, return the corresponding type
            return type_names[data[1:]]
        # otherwise, return the original string
        return data
    # recurive case 1--data is a list
    elif isinstance(data, list):
        # run the function on every member of the list
        return [update_symbols(x, obj_names, type_names) for x in data]
    # recurive case 2--data is a dict
    elif isinstance(data, dict):
        # run the function on every value in the dictionary
        return {
            key: update_symbols(value, obj_names, type_names)
            for (key, value) in data.items()
        }
    # base case 2--data is some other type and we won't touch it
    else:
        return data


def load_personae(personae_data, type_names, obj_names=None):
    """[personae_data] : personae-formatted object definions
    [type_names]: dict mapping strings (names) to classes
    [obj_names]: optional argument containing starter symbols and objects
    returns a dict mapping symbols to game objects loaded form [personae_data]
    """
    # copy any starter symbols if provided
    obj_names = obj_names.copy() if obj_names else {}
    for obj_id, obj_data in personae_data.items():
        # check if 'name' is already in the symbol table
        # e.g. skimmed locations need not be loaded in again
        if obj_id in obj_names:
            continue
        # load the object and add it to the table
        obj_names[obj_id] = load_object(obj_data, type_names)
    # update all the symbols as appropriate
    updated_data = update_symbols(personae_data, obj_names, type_names)
    # now call all the 'post_load' methods
    for obj_id, obj in obj_names.items():
        # look up the object's data
        obj_data = updated_data[obj_id]
        # call the post load method
        obj.post_load(obj_data)
    return obj_names


def walk_tree(tree, obj_names, cls_names):
    """recursive function for evaluating the World Tree"""
    # base case 1--tree is a symbol
    if isinstance(tree, str):
        # return the object with that symbol
        yield obj_names[tree]
    # base case 2--tree is anonymous object data
    elif isinstance(tree, dict):
        # this is why '_type' cannot be used as a symbol
        if "_type" in tree:
            # load in the object
            obj = load_object(tree, cls_names)
            # call object's postload method
            obj.postload(tree, obj_names, cls_names)
            yield obj
        # recursive case 1--tree is a dict mapping object to other, owned objects
        else:
            for symbol, subtree in tree.items():
                # get the owner from the sybmol
                owner = obj_names[symbol]
                # load in each child in this subtree
                for child_obj in load_tree(subtree, obj_names, cls_names):
                    if isinstance(child_obj, Character):
                        owner.add_char(child_obj)
                    elif isinstance(child_obj, Item):
                        owner.add_item(child_obj)
                    elif isinstance(child_obj, Entity):
                        owner.add_entity(child_obj)
                    else:
                        raise TypeError("%r has wrong type" % child_obj)
                yield owner
    # recursive case 2--tree is a list of subtrees
    elif isinstance(tree, list):
        for subtree in tree:
            for child in load_tree(subtree, obj_names, cls_names):
                yield child
    elif tree is None:
        pass
    else:
        raise TypeError("Expected symbol, list, or mapping, "
                        f"received '{tree!r}' of type '{type(tree)}'")


def load_tree(tree, obj_names, cls_names):
    """wrapper function for walk_tree
    returns a list of objects at the top of the hierarchy
    """
    # TODO: check that symbols are used only once in each tree
    return [obj for obj in walk_tree(tree, obj_names, cls_names)]


def symbol_replace(data, sym_counts):
    """returns a copy of [data], but with all classes
    and game objects replaced with the proper symbols
    the frequency of each symbol is recorded in [sym_counts]"""
    # check if object is a game object, replace with obj symbol
    if any(map(lambda x: isinstance(data, x), _GAME_OBJS)):
        sym = "$%s" % data.symbol
        sym_counts[sym] += 1
        return sym
    # if the object is a game class, replace with class symbol
    elif any(map(lambda x: isinstance(data, x), _GAME_CLASSES)) or data in _GAME_OBJS:
        return "^%s" % data.__name__
    # recurive case 1--data is a list
    elif isinstance(data, list):
        # run the function on every member of the list
        return [symbol_replace(x, sym_counts) for x in data]
    # recurive case 2--data is a dict
    elif isinstance(data, dict):
        # run the function on every key and value in the dictioanry
        return {
            symbol_replace(key, sym_counts): symbol_replace(value, sym_counts)
            for (key, value) in data.items()
        }
    # base case 2--data is some other type and we won't touch it
    else:
        return data


def build_tree(obj, personae_counts, tree_counts):
    """returns a tuple containing subtree, personae_chunk
    subtree: a subtree of the World Tree
    personae_data: a chunk of personae_data
    """
    personae = {}
    subtrees = []
    # recursive step
    for child in obj.children():
        # replace the child's data symbols and add to personae
        child_data = symbol_replace(child.save(), personae_counts)
        personae[child.symbol] = child_data

        personae_chunk, subtree = build_tree(child, personae_counts, tree_counts)
        # update personae with the personae_chunk
        # this is valid since each symbol should be unique
        personae.update(personae_chunk)
        subtrees.append(subtree)
    # run through a series of cases to build the tree
    # refer to the World Specification document for discussion of each case
    if len(subtrees) == 0:
        # if there are no subtrees, then we can use obj's symbol as tree
        tree = obj.symbol
    elif len(subtrees) == 1:
        tree = { obj.symbol : subtrees[0] }
    elif all(map(lambda x: isinstance(x, dict), subtrees)):
        # list is unecessary, we can join the dicts together
        # this is valid because symbols can be used only once
        combined_dict = {}
        for subdict in subtrees:
            combined_dict.update(subdict)
        tree = {obj.symbol: combined_dict}
    else:
        # worst case, simply map the list
        tree = {obj.symbol: subtrees}
    return personae, tree


class World:
    """class representing an in-game world"""
    def __init__(self, prelude, personae, tree):
        """initialize an empty world"""
        # skim the personae, creating all locations
        self.locations = skim_for_locations(personae)
        # the prelude won't change, so simply save it
        self.prelude = prelude

        # make the locations available for the modules in the prelude
        # this allows developers to access locations via "import_location"
        with LocationExport({str(l) : l for l in self.locations.values()}):
            # load in classes from the prelude
            type_names = load_prelude(prelude)

        # add "Location" to the possible type names
        type_names["Location"] = Location

        # load the dramatis personae
        symbols = load_personae(personae, type_names,
                                obj_names=self.locations)
        # load the tree
        load_tree(tree, symbols, type_names)

        # sort out the remaining classes
        self.char_classes = {}
        self.item_classes = {}
        self.entity_classes = {}
        self.symbol = "world"
        for cls in type_names.values():
            if isinstance(cls, CharacterClass):
                self.char_classes[cls.__name__] = cls
            elif isinstance(cls, ItemClass):
                self.item_classes[cls.__name__] = cls
            elif isinstance(cls, EntityClass):
                self.entity_classes[cls.__name__] = cls


    def children(self):
        """iterate over the locations in this world"""
        for location in self.locations.values():
            yield location

    def save(self):
        """returns a pythonic representation of this world"""
        personae_counts = defaultdict(int)
        tree_counts = defaultdict(int)
        personae, tree = build_tree(self, personae_counts, tree_counts)
        return {
            "prelude": self.prelude,
            "personae": personae,
            "tree": tree["world"]
        }

    def to_file(self, filename):
        """write this world's save data to [filename]"""
        write_worldfile(filename, self.save())

    @staticmethod
    def from_file(filename):
        """returns a World loaded from a file"""
        world_data = read_worldfile(filename)
        return World(**world_data)

    def random_cls(self):
        """return a random CharacterClass, based on each CharClass's
        'frequency' value"""
        cls_list = list(self.char_classes.values())
        freqs = [cls.frequency for cls in cls_list]
        return choices(cls_list, weights=freqs)[0]

    @staticmethod
    def test_world():
        """create a barebones world for testing purposes"""
        prelude = {"swampymud.character": ["Character"]}
        personae = {"tavern":{
            "_type": "^Location",
            "name": "Swampy Tavern",
            "description": "Welcome to the best (and only) tavern in the world"
                           + "! [This is a test location.]"
        }}
        tree = "tavern"
        return World(prelude, personae, tree)
