'''
Module that deserializes developer-made game-data, converting it into real objects
'''
import json
import os
import importlib
import logging
import traceback
from location import Location, Exit
from util.stocstring import StocString
import library


class Importer:
    '''Base class for other importers'''
    def __init__(self, lib=None):
        self.successes = {}
        if lib is not None:
            self.successes = lib
        self.failures = {}

    def import_file(self, filename):
        '''Import one file with filename [filename]'''
        try:
            self._do_import(filename)
        except Exception as ex:
            self.failures[getattr(ex, "name")] = traceback.format_exc()

    def _do_import(self, filename):
        '''This method should be implemented in base classes'''
        pass

    def all_to_str(self):
        '''cheap method to get an output for all values in each list'''
        output = "\nSUCCESS LIST\n"
        for _, obj in self.successes.items():
            output += str(obj) + "\n"
        output += "FAILURE LIST\n"
        for name, reason in self.failures.items():
            output += str(name) + " :\n"
            output += str(reason) + "\n"
        return output


class LocationImporter(Importer):
    '''Imports Locations from jsons
    '''
    # TODO: explain the philosophy here
    def __init__(self, library=None):
        self.skeletons = {}
        self.exit_failures = {}
        self.item_failures = {}
        super().__init__(library)

    def _do_import(self, filename):
        # TODO: with proper exception handling, throw the location name when possible
        name = filename
        try:
            with open(filename) as location_file:
                # read the file, processing any stocstring macros
                json_data = StocString.process(location_file.read())
            json_data = json.loads(json_data)
            name = json_data["name"]
            # check that "items" is a dict
            if "items" in json_data:
                assert(isinstance(json_data["items"], dict))
            # check that "exits" is a list
            if "exits" in json_data:
                assert(isinstance(json_data["exits"], list))
        except Exception as ex:
            # modify exception to show what the name is, rethrow
            setattr(ex, "name", name)
            raise ex
        self.skeletons[json_data["name"]] = json_data
        self.successes[json_data["name"]] = Location(json_data["name"], json_data["description"])

    def build_exits(self):
        '''looks at the skeletons, adds exits for each
        on fail, an exit is simply not added'''
        for location_name, skeleton in self.skeletons.items():
            # creating an empty list of failed exits
            self.exit_failures[location_name] = {}
            if "exits" not in skeleton:
                continue
            for exit in skeleton["exits"]:
                
                # check if the exit specified a destination first
                if "destination" not in exit:
                    # make a fake name
                    exit_name = "[Exit #%i]" % (len(self.exit_failures))
                    self.exit_failures[location_name][exit_name] = "No destination provided"
                    continue
                try:
                    if exit["destination"] in self.successes:
                        # get destination from the successfully loaded locations
                        dest = self.successes[exit["destination"]]
                        

                        # parsing the strings in the blacklist/whitelists,
                        if "blacklist" in exit:
                            exit["blacklist"] = [library.character_classes[clsname]
                                                 for clsname in exit["blacklist"]]
                        if "whitelist" in exit:
                            exit["whitelist"] = [library.character_classes[clsname]
                                                 for clsname in exit["whitelist"]]

                        # TODO: handle references to "proper characters"
                        
                        # Preparing exit dict for conversion to keyword arguments
                        kwargs = dict(exit)
                        del kwargs["destination"]
                        #del kwargs["name"]
                        self.successes[location_name].add_exit(Exit(dest, **kwargs))
                    elif exit["destination"] in self.failures:
                        raise Exception("Destination \'%s\' failed to import." % (exit["destination"]))
                    else:
                        raise Exception("Destination \'%s\' could not be found." % (exit["destination"]))
                except Exception:
                    self.exit_failures[location_name][(exit["destination"])] = traceback.format_exc()
            # check if any failed exits were added to the exit_failures dictionary
            # if not, we delete the entry for this location (no failures to mention!)
            if not self.exit_failures[location_name]:
                del self.exit_failures[location_name]

    def add_items(self):
        '''looks at the skeletons, adds items for each
        on fail, an item is simply not added'''
        for location_name, skeleton in self.skeletons.items():
            failures = {}
            # items might be provided, in which case we just continue
            if "items" not in skeleton:
                continue
            for item_name, quantity in skeleton["items"].items():
                try:
                    item = library.items[item_name]
                    quanity = int(quantity)
                    self.successes[location_name].add_items(item, quanity)
                except Exception as ex:
                    failures[item_name] = traceback.format_exc()
                    # this is an idempotent operation
                    # even if we re-assign the dict multiple times, it has the same effect
                    self.item_failures[location_name] = failures

    def add_entities(self):
        '''looks at skeletons, adds entity for each
        on fail, an entity is simply not added'''
        # entities have not been added yet
        pass

    def all_to_str(self):
        output = super().all_to_str()
        output += "\nEXIT FAILURES\n"
        for location, exits in self.exit_failures.items():
            for dest, exc in exits.items():
                output += str(location) + " -> " + str(dest) + "\n" + exc
        output += "\nITEM FAILURES\n"
        for location, items in self.exit_failures.items():
            output += str(location) + ":\n"
            for item, exc in exits.items():
                output +=  str(dest) + "\n" + exc
        return output


class CharacterClassImporter(Importer):
    '''Importer for CharacterClasses'''
    def _do_import(self, filename):
        name = filename
        try:
            with open(filename) as charclass_file:
                # read the file, processing any stocstring macros
                json_data = StocString.process(charclass_file.read())
            json_data = json.loads(json_data)
            name = json_data["name"]
            assert isinstance(json_data["name"], str)
            if "frequency" in json_data:
                assert isinstance(json_data["frequency"], float)
            path = json_data["path"]
            module = importlib.import_module(path.replace('.py', '').replace('/', '.'))
            character_class = module.__dict__[name]
            if "starting_location" in json_data:
                starting_location = library.locations[json_data["starting_location"]]
                character_class.starting_location = starting_location
            if "frequency" in json_data:
                character_class.frequency = json_data["frequency"]
            # add other json arguments here
        except Exception as ex:
            setattr(ex, "name", name)
            raise ex
        self.successes[str(character_class)] = character_class

class ItemImporter(Importer):
    def _do_import(self, filename):
        name = filename
        try:
            with open(filename) as item_file:
                # read the file, processing any stocstring macros
                json_data = StocString.process(item_file.read())
            json_data = json.loads(json_data)
            name = json_data["name"]
            path = json_data["path"] 
            module = importlib.import_module(path.replace('.py', '').replace('/', '.'))
            item = module.__dict__[name]
        except Exception as ex:
            setattr(ex, "name", name)
            raise ex
        self.successes[str(item)] = item

class EntityImporter(Importer):
    pass

def import_files(**paths):
    location_importer = LocationImporter(library.locations)
    character_importer = CharacterClassImporter(library.character_classes)
    item_importer = ItemImporter(library.items)
    if "locations" in paths:
        for filename in paths["locations"]:
            location_importer.import_file(filename)
    if "chars" in paths:
        for filename in paths["chars"]:
            character_importer.import_file(filename)
    if "items" in paths:
        for filename in paths["items"]:
            item_importer.import_file(filename)
    if "entities" in paths:
        pass
        # TODO implement this
        # for filename in paths["entities"]:
            # entity_importer.import_file(filename)
    if "locations" in paths:
        location_importer.build_exits()
        location_importer.add_items()
        location_importer.add_entities()
    logging.info(location_importer.all_to_str())
    logging.info(character_importer.all_to_str())


def get_filenames(directory, ext=""):
    '''returns all filenames in [directory] with extension [ext]'''
    return [directory + name for name in os.listdir(directory) \
            if name.endswith(ext)]
