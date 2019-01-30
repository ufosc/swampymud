'''library holding dictionaries for in-game objects'''
from location import Location
from character import CharacterClass
from util.distr import RandDist

locations = {}
character_classes = {}
items = {}
server = None
random_class = None

#lookup appropriate list by type

def build_char_class_distr():
    '''takes the current set of CharacterClasses
    and builds a random distribution based on their frequency
    can be called again to rebuild the distribution
    '''
    global random_class
    frequencies = [char_class.frequency for char_class in character_classes.values()]
    random_class = RandDist(list(character_classes.values()), frequencies)

def store_server(input_server):
    '''stores [input_server] as library.server'''
    global server
    server = input_server