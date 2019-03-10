'''
Module that deserializes developer-made game-data, converting it into real objects
'''
import json
import os
import importlib
import traceback
from location import Location, Exit
from util.stocstring import StocString
from util.distr import RandDist

def get_filenames(directory, ext=""):
    '''returns all filenames in [directory] with extension [ext]'''
    return [directory + name for name in os.listdir(directory) \
            if name.endswith(ext)]

class Library:
    '''Class to represent a library of interacting game elements'''
    def __init__(self):
        self.locations = {}
        self.char_classes = {}
        self.items = {}
        # random distribution based on class frequencies
        self.random_class = None
        self._loc_importer = LocationImporter(self.locations)
        self._char_importer = CharacterClassImporter(self.char_classes)
        self._item_importer = ItemImporter(self.items)

    def build_class_distr(self):
        '''takes the current set of CharacterClasses
        and builds a random distribution based on their frequency
        can be called again to rebuild the distribution
        '''
        # grab character classes with frequency > 0
        to_include = [c_class for c_class in self.char_classes.values()
                      if c_class.frequency > 0]
        if not to_include:
            raise Exception("No valid classes with frequency greater than 0")
        self.random_class = RandDist(to_include, list(map(lambda x: x.frequency, to_include)))

    def import_files(self, locations=[], chars=[], items=[]):
        '''import an arbitrary number of files
        arguments:
            locations = list of location json filenames
            chars = list of char json filenames
            items = list of item json filenames
        this method will automatically build exits after
        files are imported
        '''
        if locations:
            for filename in locations:
                self._loc_importer.import_file(filename)
        if chars:
            for filename in chars:
                self._char_importer.import_file(filename, locations=self.locations)
        if items:
            for filename in items:
                self._item_importer.import_file(filename)
        if locations:
            self._loc_importer.build_exits(*self.locations.keys())
            #self._loc_importer.add_items()
            #self._loc_importer.add_entities()

    def import_results(self):
        return '''
LOCATIONS
%s
ITEMS
%s
CHARACTER CLASSES
%s''' % (self._loc_importer, self._item_importer, self._char_importer)

    def __repr__(self):
        output = []
        if self.locations:
            output += ["Locations:    " + repr(list(self.locations.keys()))]
        if self.char_classes:
            output += ["CharClasses:  " + repr(list(self.char_classes.keys()))]
        if self.items:
            output += ["Items:        " + repr(list(self.items.keys()))]
        return "\n".join(output)


def process_json(filename):
    '''load a json from [filename], return a pythonic representation'''
    with open(filename) as location_file:
        # read the file, processing any stocstring macros
        json_data = StocString.process(location_file.read())
    json_data = json.loads(json_data)
    assert "name" in json_data
    return json_data


class ValidateError(Exception):
    '''Error raised if schema is not valid'''
    def __init__(self, component, msg):
        self.component = component
        self.msg = msg
        super().__init__()

    def __str__(self):
        return str(self.component) + "\n" + self.msg

#TODO: warn on unused fields?
def validate(schema, data):
    '''validate that [data] fits a provided [schema]'''
    if "check" in schema:
        try:
            schema["check"](data)
        except Exception as err:
            raise ValidateError(data, "Failed check: %s " % err)
    if "type" in schema:
        if schema["type"] is not type(data):
            raise ValidateError(data, "Invalid type %s, expected %s."
                                % (type(data), schema["type"]))
    if isinstance(data, list):
        for sub in data:
            validate(schema["items"], sub)
    if isinstance(data, dict):
        for field, subschema in schema["properties"].items():
            # if "required" is not provided by schema, assume field is required
            if (("required" not in subschema or subschema["required"])
                    and field not in data):
                raise ValidateError(data, "Missing required field '%s'"
                                    % field)
            if field in data:
                validate(subschema, data[field])


class Importer:
    '''Base class for other importers
    objects:        dict mapping object names -> object instances
    object_source:  dict mapping object names -> filenames
    file_data:      dict mapping filenames -> filedata
    file_fails:     dict mapping filenames -> reasons while file failed to load
    failures:       dict mapping object names -> reasons why they could not be constructed
    '''
    def __init__(self, lib={}):
        self.objects = lib
        self.object_source = {}
        self.file_data = {}
        self.file_fails = {}
        self.failures = {}

    def import_file(self, filename, **kwargs):
        '''Import one file with filename [filename]'''
        try:
            json_data = process_json(filename)
            self.file_data[filename] = json_data
        except Exception as ex:
            self.file_fails[filename] = traceback.format_exc()
            return
        try:
            name, game_object = self._do_import(json_data, **kwargs)
            self.objects[name] = game_object
            self.object_source[name] = filename
        except Exception as ex:
            self.failures[ex.name] = traceback.format_exc()

    def _do_import(self, json_data):
        '''This method should be implemented in base classes
        _do_import should return a tuple:
            (name, object)
        where name is the name of the object
        a file created by _do_import should be guaranteed to
        have proper syntax, type checking, etc.
        '''
        return "", {}

    def __repr__(self):
        '''cheap method to get an output for all values in each list'''
        output = [repr(self.__class__)]
        output += ["Successes:       " + list(repr(self.objects.keys()))]
        output += ["File Failures:   " + list(repr(self.file_fails.keys()))]
        output += ["Build Failures:  " + list(repr(self.failures.keys()))]
        return "\n".join(output)

    def __str__(self):
        output = []
        if self.objects:
            output.append("\tSuccesses [%s]" % len(self.objects))
            for success in self.objects:
                output.append(success)
        else:
            output.append("\t[No Successes]")
        if self.file_fails:
            output.append("\tFile Failures [%s]" % len(self.file_fails))
            for fail_name, fail in self.file_fails.items():
                output.append(fail_name)
                output.append(fail)
        else:
            output.append("\t[No File Failures]")
        if self.failures:
            output.append("\tBuild Failures [%s]" % len(self.failures))
            for fail_name, fail in self.failures.items():
                output.append(fail_name)
                output.append(fail)
        else:
            output.append("\t[No Build Failures]")
        return "\n".join(output)

def _filter_type(typ):
    if typ not in ["blacklist", "whitelist"]:
        raise Exception("Must be 'whitelist' or 'blacklist'")


FILTER_SCHEMA = {
    "type" : dict,
    "required" : False,
    "properties" : {
        "type" : {"type" : str, "check" : _filter_type},
        "set" : {
            "type" : list,
            "required" : False,
            "items" : {
                "type" : str
            }
        }
    }
}


class LocationImporter(Importer):
    '''Imports Locations from json'''

    exit_schema = {
        "type": dict,
        "properties": {
            "destination" : {"type" : str, "required" : False},
            "name" : {"type" : str, "required" : True},
            "other_names": {
                "type" : list,
                "required" : False,
                "items" : {"type": str}
            },
            "visibility" : FILTER_SCHEMA,
            "access" : FILTER_SCHEMA
        }
    }

    location_schema = {
        "properties" : {
            "name" : {"type" : str, "required" : True},
            "description" : {"type": str, "required": True},
            "exits" : {
                "type" : list,
                "items" : exit_schema
            }
        }
    }

    def __init__(self, lib={}):
        '''
        exit_failure: dict mapping destination names to a dict:
        {"reason" : [reason for failure], "affected": [names of locations affected]}
        '''
        super().__init__(lib)

    def _do_import(self, json_data):
        try:
            name = json_data["name"]
            validate(self.location_schema, json_data)
        except ValidateError as ex:
            # modify exception to show what the name is, rethrow
            setattr(ex, "name", name)
            raise ex
        return name, Location(json_data["name"], json_data["description"])

    #TODO: delete all existing exits
    def build_exits(self, *names, chars={}):
        '''This method is always executed on locations
        that have already passed through _do_import.
        Thus, we can assume the types of each field are correct.
        '''
        for loc_name in names:
            location = self.objects[loc_name]
            json_data = self.file_data[self.object_source[loc_name]]
            if "exits" in json_data:
                for exit_data in json_data["exits"]:
                    dest_name = exit_data["destination"]
                    try:
                        dest = self.objects[exit_data["destination"]]
                    except KeyError:
                        if dest_name in self.exit_failures:
                            self.exit_failures[dest_name]["affected"].append(loc_name)
                        else:
                            new_failure = {"affected" : [loc_name]}
                            if dest_name in self.failures:
                                new_failure["reason"] = "Destination failed to load."
                            else:
                                new_failure["reason"] = "Destination not found."
                            self.exit_failures[dest_name] = new_failure
                        continue
                    # this only handles CharacterClasses
                    # TODO: handle "proper" characters

                    kwargs = dict(exit_data)
                    kwargs["destination"] = dest
                    location.add_exit(Exit(**kwargs))

#    def add_items(self):
#        '''looks at the skeletons, adds items for each
#        on fail, an item is simply not added'''
#        for location_name, skeleton in self.skeletons.items():
#            failures = {}
#            # items might be provided, in which case we just continue
#            if "items" not in skeleton:
#                continue
#            for item_name, quantity in skeleton["items"].items():
#                try:
#                    item = library.items[item_name]
#                    quanity = int(quantity)
#                    self.successes[location_name].add_items(item, quanity)
#                except Exception as ex:
#                    failures[item_name] = traceback.format_exc()
#                    # this is an idempotent operation
#                    # even if we re-assign the dict multiple times, it has the same effect
#                    self.item_failures[location_name] = failures
#
#    def add_entities(self):
#        '''looks at skeletons, adds entity for each
#        on fail, an entity is simply not added'''
#        # entities have not been added yet
#        pass


class CharacterClassImporter(Importer):
    def _do_import(self, json_data, locations={}):
        try:
            name = json_data["name"]
            path = json_data["path"]


            module = importlib.import_module(path.replace('.py', '').replace('/', '.'))
            character_class = getattr(module, name)
            if "starting_location" in json_data:
                starting_location = locations[json_data["starting_location"]]
                character_class.starting_location = starting_location
            if "frequency" in json_data:
                assert isinstance(json_data["frequency"], float)
                character_class.frequency = json_data["frequency"]
            # add other json arguments here
        except Exception as ex:
            setattr(ex, "name", name)
            raise ex
        return str(character_class), character_class

class ItemImporter(Importer):
    def _do_import(self, json_data):
        try:
            name = json_data["name"]
            path = json_data["path"]
            module = importlib.import_module(path.replace('.py', '').replace('/', '.'))
            item = getattr(module, name)
        except Exception as ex:
            setattr(ex, "name", name)
            raise ex
        return str(item), item

class EntityImporter(Importer):
    pass
