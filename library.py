'''library holding dictionaries for in-game objects'''
from location import Location
from character import CharacterClass
from util.distr import RandDist

locations = {}
character_classes = {}
items = {}
server = None

# random distribution based on class frequencies
random_class = None


def build_char_class_distr():
    '''takes the current set of CharacterClasses
    and builds a random distribution based on their frequency
    can be called again to rebuild the distribution
    '''
    global random_class
    # grab character classes with frequency > 0
    to_include = [c_class for c_class in character_classes.values() 
                   if c_class.frequency > 0]
    if len(to_include) == 0:
        raise Exception("No valid classes with frequency greater than 0")
    random_class = RandDist(to_include, map(lambda x: x.frequency, to_include))


def store_server(input_server):
    '''stores [input_server] as library.server'''
    global server
    server = input_server
