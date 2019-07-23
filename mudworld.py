'''Module that developer-made game-data,
converting it into real objects'''
import importlib
import yaml
from location import Location, Exit
from character import CharacterClass, Character
from item import ItemClass, Item
from entity import EntityClass, Entity
from collections import namedtuple


def read_savefile(save_name):
    '''return a parsed save file'''
    #TODO: add a 'gzip' layer to this
    with open(save_name) as save_file:
        save_data = save_file.read()
    save_data = yaml.load(save_data)
    # check that only the following sections appear in the world tree
    valid_sections = set(("prelude", "personae", "tree"))
    for section in save_data:
        if section not in valid_sections:
            #TODO: use a more specific exception
            raise Exception("Found unexpected section '%s' in save file '%s'"
                            % (section, save_name))
    return save_data

VALID_CLASSES = [CharacterClass, ItemClass, EntityClass]

def load_prelude(prelude_data):
    # TODO use context manager for locations
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
            if any(map(lambda x: isinstance(cls, x), VALID_CLASSES)):
                cls_dict[cls_name] = cls
            # if not, raise an exception
            else:
                #TODO: use a more specific exception
                raise Exception("Class is wrong type")
    return cls_dict
    

def skim_for_locations(personae):
    '''return a dict mapping names to locations based on the provided tree'''
    return {
        name : Location(name, data["description"])
            for name, data in personae.items() if data["type"] == "Location"
    }


def load_personae(personae_data, type_names, to_add=None):
    '''return a SymbolTable containing locations, chars, items, and entities
    loaded from [personae_data]
    by default, a fresh SymbolTable is created, but to load data into an existing
    SymbolTable, use the [to_add] argument'''
    table = {}
    if to_add:
        table.update(to_add)
    for obj_name, obj_data in personae_data.items():
        # check if 'name' is already in the symbol table
        # e.g. skimmed locations need not be loaded in again
        if obj_name in table:
            continue
        obj_data["name"] = obj_name
        # find the type of the object
        # and load the obj in using the special .load method
        ObjType = type_names(obj_data["type"])
        table["name"] = ObjType.load(obj_name, data)
    # now call all the 'post_load' methods
    for obj_name, obj in table.items():
        # look up the object's data
        obj_data = personae[obj_name]
        # call the post load method
        obj.post_load(data)
    return table

def _load_child_node(node, symbol_table):
    '''recurse function for evaluating branches
    of the tree'''
    # branch is either a string (leaf node) or a dictionary (branch node)
    # base case--child is a solitary leaf
    if isinstance(node, str):
        yield symbol_table[node]
    # recursive case--child has more children
    elif isinstance(node, dict):
        # check dictionary
        for child_name, grandchildren in node.items():
            # load in the object
            child_obj = symbol_table[child_name]
            # recursively load in its children and add it
            for grandchild in _load_child_node(grandchildren, symbol_table):
                # child could be None if the dictionary was empty
                if grandchild is None:
                    continue
                if isinstance(grandchild, Character):
                    child_obj.add_char(grandchild)
                elif isinstance(grandchild, Entity):
                    child_obj.add_entity(grandchild)
                elif isinstance(grandchild, Item):
                    child_obj.add_item(grandchild)
                else:
                    raise TypeError("%r has wrong type" % grandchild)
            yield child_obj
    # edge case--dictionary may point to nothing
    elif node is None:
        return
    else:
        raise TypeError("node %r has wrong type" % node)

def load_tree(tree, symbol_table):
    '''load in each of the locations of the tree,
    using [symbol_table] as reference
    this function calls "load_object" for each element of the tree'''
    for loc_name, loc_data in tree.items():
        location = symbol_table[loc_name]
        # TODO: make this fit into the case above
        for child in _load_child_node(loc_data, symbol_table):
            if isinstance(child, Character):
                location.add_char(child)
            elif isinstance(child, Entity):
                location.add_entity(Entity)
            elif isinstance(child, Item):
                location.add_item(child)


class World:
    '''class representing an in-game world'''
    def __init__(self, prelude={}, personae={}, tree={}):
        '''initialize an empty world'''
        # skim the personae, creating all locations
        self.locations = skim_for_locations(personae)
        # the prelude won't change, so simply save it
        self.prelude = prelude
        # load in classes from the prelude
        type_names = load_prelude(prelude)
        # prepare a dictionary of type names
        type_names["Exit"] = Exit
        # prepare the symbol table
        # TODO turn this into a custom class
        symbols = self.locations.copy()
        # load the dramatis personae
        symbols = load_personae(personae, type_names, to_add=symbols)
        # load the tree

    @staticmethod
    def from_savefile(self, save_name):
        '''returns a World loaded from a save_file'''
        save_data = read_savefile(save_name)
        return World(**save_data)
