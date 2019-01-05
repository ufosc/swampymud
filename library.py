from location import Location
from character import CharacterClass
from util.distr import RandDist
'''library holding dictionaries for in-game objects'''

locations = {}
character_classes = {}
items = {}
server = None
random_class = None

#lookup appropriate list by type

'''
typedict = {
    Location : locations,
    CharacterClass : character_classes
}

def store_lib(input_library):
'''
'''unpacks a library produced by fileparser.py
stores it in the module as library.[class_name]
'''
'''
    # referring to the the global names in the module
    global locations, character_classes, random_class
    if Location in input_library:
        locations = input_library[Location]
    if CharacterClass in input_library:
        character_classes = input_library[CharacterClass]
        # gathering the frequencies for each CharacterClass
        frequencies = [c_class.frequency for c_class in character_classes.values()]
        # creating a dictionary with each frequency
        freq_dict = dict(zip(character_classes.values(), frequencies))
        # creading a Random Distribution for each class
        random_class = RandDist(freq_dict)
'''
def build_char_class_distr():
    '''takes the current set of CharacterClasses
    and builds a random distribution based on their frequency
    can be called again to rebuild the distribution
    '''
    global random_class
    frequencies = [char_class.frequency for char_class in character_classes.values()]
    freq_dict = dict(zip(character_classes.values(), frequencies))
    random_class = RandDist(freq_dict)

def store_server(input_server):
    '''stores [input_server] as library.server'''
    global server
    server = input_server
