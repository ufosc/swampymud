"""This module defines a 'Person' class, which may have a spouse,
several friends, or serve as a legal guardian that 'owns' other
Characters.

The relationships in this module are circular by nature, serving as a
good test of the import system.
"""
from swampymud.character import Character

class Person(Character):

    def __init__(self, name):
        super().__init__(name)
        self.friends = []
        self.spouse = None
        self.dependents = []


    # serialization-related methods
    def post_load(self, data):
        if "friends" in data:
            for friend in data["friends"]:
                self.friends = friend
        if "spouse" in data:
            self.spouse = data["spouse"]

    def add_char(self, char):
        self.dependents.append(char)

    def children(self):
        yield from super().children()
        yield from self.dependents
