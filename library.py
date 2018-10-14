'''library holding dictionaries for in-game objects'''
from location import Location
from character import CharacterClass
from util.distr import RandDist

# the library holding in-game objects
library = {}

# reference to the current server
server = None

# random distribution based on class frequencies
random_class = None


def build_class_distribution():
    '''builds a random distribution based on the current
    CharacterClasses'''
    global library, random_class
    character_classes = library[CharacterClass]
    # gathering the frequencies for each CharacterClass
    frequencies = [c_class.frequency for c_class in character_classes.values()]
    # creating a dictionary with each frequency
    freq_dict = dict(zip(character_classes.values(), frequencies))
    # creading a Random Distribution for each class
    random_class = RandDist(freq_dict)
    

def store_server(input_server):
    '''stores [input_server] as library.server'''
    global server
    server = input_server
