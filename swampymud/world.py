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
from swampymud.inventory import ItemStack
from swampymud.mudscript import LocationExport

# TODO: change these to sets?
_GAME_OBJS = (Character, Item, Entity, Location)
_GAME_CLASSES = (CharacterClass, ItemClass, EntityClass)

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
    """return a dict of classes imported according to prelude_data"""
    # by default, we include Location and ItemStack
    cls_dict = {"Location": Location, "ItemStack": ItemStack}
    for fname, classes in prelude_data.items():
        # convert the pathname to a module name and attempt import
        mod_name = fname.replace('.py', '').replace('/', '.')
        mod = importlib.import_module(mod_name)
        for cls_name in classes:
            cls = getattr(mod, cls_name)
            # check that class is a valid class to import
            if isinstance(cls, _GAME_CLASSES):
                cls_dict[cls_name] = cls
            # if not, raise an exception
            else:
                raise TypeError("{!r} is wrong type, expected one of"
                                "{}".format(cls, _GAME_CLASSES))
    return cls_dict


# functions for loading personae
def check_types(personae, type_names=None):
    """Return a copy of personae with all objs missing a "_type" field
    removed. Produces a warning for each object removed.

    optional arguments
    type_names -- if provided, remove and warn about any objects with an
    unknown type
    """
    skipped = 0
    updated_personae = {}
    for symbol, data in personae.items():
        if "_type" not in data:
            msg = f"Object '{symbol}' missing required field '_type'."
            # catch an easy pitfall
            if "type" in data:
                msg += " (Did you add a 'type' field instead of '_type'?)"
            warnings.warn(msg)
            skipped += 1
            continue
        obj_type = data["_type"][1:] # strip off the '^'
        if type_names is not None and obj_type not in type_names:
            msg = f"Object '{symbol}' has unknown type '{obj_type}'."
            # catch another easy pitfall
            if not data["_type"].startswith("^"):
                msg += " (Did you remember to put '^' in front of your type?)"
            warnings.warn(msg)
            skipped += 1
            continue
        updated_personae[symbol] = data
    if skipped:
        warnings.warn(f"Skipped {skipped} objects. (Unknown type.)")
    return updated_personae


def skim_for_locations(personae):
    """extract locations from personae
    warns if any locations are missing fields
    """
    skipped = 0
    locs = {}
    for symbol, data in personae.items():
        # assume that _type has already been checked
        if data["_type"] == "^Location":
            try:
                locs[symbol] = Location(data["name"], data["description"])
            except KeyError as err:
                warnings.warn(f"Location '{symbol}' missing required field "
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


def check_symbols(data, obj_names, type_names):
    """Return a deep copy of data with each symbol checked. Warn if a
    symbol is used in data but cannot be found in obj_names or
    type_names.

    If a symbol cannot be found, then the item is omitted (in the case
    of a list) or the key, value pair is omitted (in the case of a
    dict).
    """
    with warnings.catch_warnings(record=True) as warn_list:
        checked = _check_symbols(data, obj_names, type_names)
    # collect the warnings, resend them, and provide number of skipped
    for warn in warn_list:
        warnings.warn(warn.message)
    if warn_list:
        warnings.warn(f"Omitted {len(warn_list)} field(s). (Bad symbol.)")
    return checked


def _check_symbols(data, obj_names, type_names):
    """Helper function for check_symbols"""
    if isinstance(data, str):
        if data.startswith("$") and data[1:] not in obj_names:
            warnings.warn(f"Unknown object symbol '{data}'.")
            return
        if data.startswith("^") and data[1:] not in type_names:
            warnings.warn(f"Unknown type symbol '{data}'.")
            return
    elif isinstance(data, list):
        checked = [_check_symbols(i, obj_names, type_names) for i in data]
        # remove any items that failed the check
        return [
            after for before, after in zip(data, checked)
            if after is not None or before is None
        ]
    elif isinstance(data, dict):
        checked = {
            key: _check_symbols(value, obj_names, type_names)
            for key, value in data.items()
        }
        # remove any values that failed the check
        return {
            k: checked[k] for k in checked
            if checked[k] is not None or data[k] is None
        }
    # data has passed the check, return it
    return data


def update_symbols(data, obj_names, type_names):
    """Return a deep copy of [data] with all symbols replaced with their
    corresponding in-game values.

    Object symbols (prefixed with '$') are updated by [obj_names].
    Type symbols (prefixed with '^') are updated by [type_names].

    Raises KeyError if a symbol cannot be found. (Consider checking data
    with check_symbols before using this function.)
    """
    # base case 1--data is a string
    if isinstance(data, str):
        # if object is a symbol, return the appropriate object / type
        if data.startswith("$"):
            return obj_names[data[1:]]
        if data.startswith("^"):
            return type_names[data[1:]]
        # otherwise, return the original string
        return data
    # recursive case 1--data is a list
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
    """Returns a dict mapping symbols to game objects loaded from
    personae_data.

    [personae_data] : personae-formatted object definions
    [type_names]: dict mapping strings (names) to classes
    [obj_names]: optional argument containing starter symbols and
    objects (like locations skimmed earlier).
    """
    obj_names = obj_names.copy() if obj_names else {}
    skipped = 0
    for obj_id, obj_data in personae_data.items():
        # check if 'name' is already in the symbol table
        # e.g. skimmed locations need not be loaded in again
        if obj_id in obj_names:
            continue
        # load the object and add it to the table
        try:
            obj_names[obj_id] = load_object(obj_data, type_names)
        except Exception as e:
            warnings.warn(f"Object '{obj_id}' failed to load. (Reason: {e!r})")
            skipped += 1
    if skipped:
        warnings.warn(f"{skipped} object(s) failed to load.")
    # check fields with malformed symbols
    personae_data = check_symbols(personae_data, obj_names, type_names)
    # update all the symbols as appropriate
    # TODO: take into account symbols that failed above?
    updated_data = update_symbols(personae_data, obj_names, type_names)
    # now call all the 'post_load' methods
    for obj_id, obj in obj_names.items():
        obj_data = updated_data[obj_id]
        obj.post_load(obj_data)
    return obj_names


def walk_tree(tree, obj_names, cls_names):
    """recursively perform a preorder traversal of [tree], loading in
    Characters, Items, and Entities in the process
    """
    # base case 1--tree is a symbol
    if isinstance(tree, str):
        # return the object with that symbol
        yield obj_names[tree]
    elif isinstance(tree, dict):
        # base case 2--tree is anonymous object data
        # this is why '_type' cannot be used as a symbol
        if "_type" in tree:
            try:
                obj = load_object(tree, cls_names)
                tree = update_symbols(tree, obj_names, cls_names)
                obj.post_load(tree)
                yield obj
            except Exception as ex:
                warnings.warn("Failed to load anon object. "
                              f"(Reason: {ex!r})")
        # recursive case 1--tree is a dict mapping object its children
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
                    elif isinstance(child_obj, ItemStack):
                        owner.add_item(child_obj.copy(), child_obj.amount)
                    else:
                        raise TypeError(f"{child_obj!r} has wrong type")
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
    """Returns a copy of [data], but with all classes and game objects
    replaced with the proper symbols.

    The frequency of each symbol is recorded in [sym_counts].
    """
    # check if object is a game object, replace with obj symbol
    if isinstance(data, _GAME_OBJS):
        sym = f"${data.symbol}"
        sym_counts[sym] += 1
        return sym
    # if the object is a game class, replace with class symbol
    elif isinstance(data, _GAME_CLASSES) or data in _GAME_OBJS:
        return f"^{data.__name__}"
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
    """Returns a tuple (subtree, personae_chunk) containing a subtree of
    the World Tree and a chunk of personae data

    This function recursively processes all objects in
    obj.children() to build up the world tree. Calling build_tree() on a
    location will serialize all characters, items, and entities in that
    location. Calling build_tree() on a World will serialize the entire
    World.

    personae_counts and tree_counts will be updated to reflect the
    number of times this obj and its children are used.
    """
    personae = {}
    subtrees = []
    # recursive step
    for child in obj.children():
        # developers may write a faulty 'children' method that
        # returns / yields None, so we skip
        if child is None:
            continue

        # replace the child's data symbols and add to personae
        child_data = symbol_replace(child.save(), personae_counts)
        personae[child.symbol] = child_data

        chunk, subtree = build_tree(child, personae_counts, tree_counts)
        # update personae with the personae_chunk
        # this is valid since each symbol should be unique
        personae.update(chunk)
        subtrees.append(subtree)
    # run through a series of cases to build the tree
    # refer to the World Specification document for discussion of cases
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
        # remove any fields without a '_type' from the personae
        personae = check_types(personae)

        # skim the personae, creating all locations
        self.locations = skim_for_locations(personae)
        # the prelude won't change, so simply save it
        self.prelude = prelude

        # make the locations available for the modules in the prelude
        # this allows developers to use "mudscript.import_location"
        with LocationExport({str(l) : l for l in self.locations.values()}):
            # load in classes from the prelude
            type_names = load_prelude(prelude)

        # do another type check from the personae
        personae = check_types(personae, type_names)

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
        # developers may change the frequency of a CharacterClass during
        # gameplay, so we simply check the frequencies each time
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
