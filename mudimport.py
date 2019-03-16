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
from character import CharFilter


def process_json(filename):
    '''load a json from [filename], return a pythonic representation'''
    with open(filename) as location_file:
        # read the file, processing any stocstring macros
        json_data = StocString.process(location_file.read())
    json_data = json.loads(json_data)
    # ensure that json has a "name" attribute that can be used
    assert "name" in json_data
    return json_data


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
            # TODO: make these operations idempotent
            self._loc_importer.build_exits(self.locations.keys(), self.char_classes)
            self._loc_importer.add_items(self.locations.keys(), self.items)
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


class ValidateError(Exception):
    '''Error raised if schema is not valid'''
    def __init__(self, component, msg):
        self.component = component
        self.msg = msg
        super().__init__()

    def __str__(self):
        return str(self.component) + "\n" + self.msg

#TODO: warn on unused fields?https://www.youtube.com/watch?v=wuQNxwOhGmAdal
def validate(schema, data):
    '''validate that [data] fits a provided [schema]'''
    if "check" in schema:
        err = None
        try:
            schema["check"](data)
        except Exception as ex:
            err = ValidateError(data, "Failed check: %s " % ex)
        if err:
            raise err
    if "type" in schema:
        if schema["type"] is not type(data):
            raise ValidateError(data, "Invalid type %s, expected %s."
                                % (type(data), schema["type"]))
    if isinstance(data, list) and "items" in data:
        for sub in data:
            if "items" in schema:
                validate(schema["items"], sub)
    if isinstance(data, dict) and "properties" in schema:
        for field, subschema in schema["properties"].items():
            # if "required" is not provided by schema, assume field is required
            if (("required" not in subschema or subschema["required"])
                    and field not in data):
                raise ValidateError(data, "Missing required field '%s'"
                                    % field)
            if field in data:
                validate(subschema, data[field])
        #TODO: actually return the warnings so Importers can store them
        for data_field in data:
            if data_field not in schema["properties"]:
                print("ValidateWarning: unused field %s in %s" % (data_field, data))


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


def dict_to_filter(filter_dict, chars):
    '''Convert the dictionary to CharFilter
    filter_dict = dict following the FILTER_SCHEMA dict
    chars = dict of character classes
    this method raises a KeyError if a class is not found
    '''
    mode = filter_dict["type"]
    filter_set = []
    if "set" in filter_dict:
        for name in filter_dict["set"]:
            filter_set.append(chars[name])
    return CharFilter(mode, filter_set)


class Importer:
    '''Base class for other importers
    objects:        dict mapping object names -> object instances
    object_source:  dict mapping object names -> filenames
    file_data:      dict mapping filenames -> filedata
    file_fails:     dict mapping filenames -> reasons while file failed to load
    failures:       dict mapping object names -> reasons why they could not be constructed
    warnings:       dict mapping object names -> warnings about content
    '''
    SCHEMA = {}

    def __init__(self, lib={}):
        self.objects = lib
        self.object_source = {}
        self.file_data = {}
        self.file_fails = {}
        self.failures = {}
        self.warnings = {}

    def import_file(self, filename, **kwargs):
        '''Import one file with name [filename]'''
        # if filename has already been processed
        if filename in self.file_data:
            # check if there was an issue with the file
            # if so, we will try to reimport
            if filename in self.file_fails:
                del self.file_fails[filename]
            else:
                # if json is fine, but data had errors
                object_name = self.file_data[filename]["name"]
                if object_name in self.failures:
                    del self.failures[object_name]
                # file has already been imported successfully
                # reload_file must be explicitly called to reload the file
                else:
                    return
        try:
            json_data = process_json(filename)
            self.file_data[filename] = json_data
        except Exception as ex:
            self.file_fails[filename] = traceback.format_exc()
            return
        try:
            validate(self.SCHEMA, json_data)
            name, game_object = self._do_import(json_data, **kwargs)
            self.objects[name] = game_object
            self.object_source[name] = filename
        except Exception as ex:
            err_name = filename
            if "name" in json_data:
                err_name = json_data["name"]
            self.failures[err_name] = traceback.format_exc()

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
                if success in self.warnings:
                    for warning in self.warnings[success]:
                        output.append("\t%s" % warning)
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

def _check_item_dict(items):
    ex = None
    for item_name, quantity in items.items():
        if not isinstance(item_name, str):
            raise Exception("Item names must be strings.")
        try:
            int(quantity)
        except ValueError:
            raise Exception("Item quantity could not be converted to"
                                 " int: %s" % quantity)
    

class LocationImporter(Importer):
    '''Imports Locations from json'''

    EXIT_SCHEMA = {
        "type": dict,
        "properties": {
            "destination" : {"type" : str},
            "name" : {"type" : str},
            "other_names": {
                "type" : list,
                "required" : False,
                "items" : {"type": str}
            },
            "visibility" : FILTER_SCHEMA,
            "access" : FILTER_SCHEMA
        }
    }

    SCHEMA = {
        "properties" : {
            "name" : {"type" : str, "required" : True},
            "description" : {"type": str, "required": True},
            "exits" : {
                "type" : list,
                "items" : EXIT_SCHEMA
            },
            "items": {
                "type": dict,
                "required" : False,
                "check": _check_item_dict
            }
        }
    }

    def __init__(self, lib={}):
        '''
        exit_faults: maps location responsible for error -> (location, reason for failure, exit_data)
        note that we only add the "exit_fault" if another location causes the issue
        otherwise, we simply remove the location

        {"reason" : [reason for failure], "affected": [names of locations affected]}

        '''
        self.exit_fail_causes = {}
        self.exit_fail_effects = {}
        super().__init__(lib)

    def _do_import(self, json_data):
        #TODO: if this location was responsible for an exit build error, fix it
        return json_data["name"], Location(json_data["name"], json_data["description"])

    #TODO: delete all existing exits
    def build_exits(self, loc_names, chars):
        '''This method is always executed on locations
        that have already passed through _do_import.
        Thus, we can assume the types of each field are correct.
        '''
        for loc_name in loc_names:
            location = self.objects[loc_name]
            json_data = self.file_data[self.object_source[loc_name]]
            if "exits" in json_data:
                for exit_data in json_data["exits"]:
                    self._build_exit(location, exit_data, chars)
                    
    def _build_exit(self, loc, exit_data, chars):
        '''build and add a single exit to loc, with [exit_data]
        [exit_data] should confrom to EXIT_SCHEMA
        chars must be a dictionary mapping names to CharacterClasses (used for building)
        '''
        dest_name = exit_data["destination"]
        # first, check the destination
        try:
            dest = self.objects[dest_name]
        except KeyError:
            # destination is not loaded correctly
            if loc not in self.exit_fail_effects:
                self.exit_fail_effects[loc] = []
            if dest_name not in self.exit_fail_causes:
                self.exit_fail_causes[dest_name] = []
            if dest_name in self.failures:
                reason = "Destination '%s' failed to load." % dest_name
            else:
                reason = "Destination '%s' not found." % dest_name
            self.exit_fail_effects[loc].append((exit_data, reason))
            self.exit_fail_causes[dest_name].append((loc, exit_data, reason))
            return
        kwargs = {"name": exit_data["name"], "destination": dest}
        try:
            if "access" in exit_data:
                kwargs["access"] = dict_to_filter(exit_data["access"], chars)
            if "visibility" in exit_data:
                kwargs["visibility"] = dict_to_filter(exit_data["visibility"], chars)
        except KeyError as ex:
            reason = "Invalid CharFilter field '%s'" % ex.args
            if loc not in self.exit_fail_effects:
                self.exit_fail_effects[loc] = []
            self.exit_fail_effects[loc].append((exit_data, reason))
        try: 
            loc.add_exit(Exit(**kwargs))
        except Exception as ex:
            if loc not in self.exit_fail_effects:
                self.exit_fail_effects[loc] = []
            self.exit_fail_effects[loc].append((exit_data, traceback.format_exc()))


    def add_items(self, loc_names, items):
        '''for each loc_name in [loc_names], add items specified 
        in the 'items' line of the location JSON
        [items] must be dictionary mapping names to Item classes
        '''
        for loc_name in loc_names:
            location = self.objects[loc_name]
            json_data = self.file_data[self.object_source[loc_name]]
            if "items" in json_data:
                for item_name, quantity in json_data["items"].items():
                    self._add_item(location, item_name, quantity, items)
    
    def _add_item(self, loc, item_name, quantity, items):
        # our schema should guarantee that quantity can be
        # coerced into an int
        quantity = int(quantity)
        try:
            Item = items[item_name]
        except KeyError:
            if loc.name not in self.warnings:
                self.warnings[loc.name] = []
            self.warnings[loc.name].append("Could not find item"
                                           " named '%s'." % item_name)
            return
        # we add a new instance of Item [quantity] times
        # this is done so that two users don't wind up sharing state somehow
        for i in range(quantity):
            loc.add_item(Item())


    def add_entities(self):
        '''looks at , adds entity for each
        on fail, an entity is simply not added'''
        # entities have not been added yet
        pass

    def __str__(self):
        output = []
        if self.objects:
            output.append("\tSuccesses [%s]" % len(self.objects))
            for name, loc in self.objects.items():
                output.append(name)
                if name in self.warnings:
                    for warning in self.warnings[name]:
                        output.append("\t%s" % warning)
                if loc in self.exit_fail_effects:
                    output.append("\tFailed Exits")
                    for exit_data, reason in self.exit_fail_effects[loc]:
                        output.append("\t%s: %s" % (exit_data["name"], reason))
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


class CharacterClassImporter(Importer):
    '''Importer for CharacterClasses'''

    SCHEMA = {
        "properties" : {
            "name": {"type" : str},
            "path": {"type" : str},
            "frequency": {"type": float, "required": False},
            "starting_location": {"type": str, "required": False}
        }
    }

    def _do_import(self, json_data, locations={}):
        name = json_data["name"]
        path = json_data["path"]
        path = path.replace('.py','').replace('/', '.')
        module = importlib.import_module(path)
        character_class = getattr(module, name)
        if "starting_location" in json_data:
            starting_location = locations[json_data["starting_location"]]
            character_class.starting_location = starting_location
        if "frequency" in json_data:
            character_class.frequency = json_data["frequency"]
        return str(character_class), character_class


class ItemImporter(Importer):
    '''Class for importing items'''

    SCHEMA = {
        "properties" : {
            "name": {"type" : str},
            "path": {"type" : str}
        }
    }

    def _do_import(self, json_data):
        name = json_data["name"]
        path = json_data["path"]
        module = importlib.import_module(path.replace('.py', '').replace('/', '.'))
        item = getattr(module, name)
        return str(item), item


class EntityImporter(Importer):
    pass
