from character import Character
import item
from library import library
from location import Location

class ExampleClass(Character):
    starting_location = library[Location]["Marston Basement Bathroom"]
    equip_slots = ["Head", "Torso", "Feet"]

    def cmd_echo(self, *args):
        '''Echoes the provided phrase back.
        usage: example [phrase]
        '''
        self.message(" ".join(args))
        
    def cmd_me(self, *args):
        '''Illustrate an action of a character
		usage me [phrase]
        '''
        self.location.message_chars("*%s %s" % (self, " ".join(args)))
        self.inv += RedPants()
        self.inv += Tentacle()
        self.inv += Cuirass()
        self.inv += BetterCuirass()

    def cmd_gimmie(self, *args):
        self.inv += Necklace()
        self.inv += BlueNecklace()
        self.inv += RedNecklace()
        self.inv += Pants()
        self.inv += RedPants()
        self.inv += Tentacle()
        self.inv += Cuirass()
        self.inv += BetterCuirass()


class Necklace(item.EquippableBase):
    target = item.EquipTarget("Head")
    def __init__(self):
        self.eqc = 0
        self.uqc = 0

    def equip(self, character):
        print("%s equipped %s! %s" % (character, self.name, self.eqc))
        self.eqc += 1

    def unequip(self, character):
        print("%s unequipped %s! %s" % (character, self.name, self.uqc))
        self.uqc += 1

class BlueNecklace(Necklace):
    meme = ""

class RedNecklace(Necklace):
    meme = ""

class Pants(Necklace):
    target = item.EquipTarget("Feet")

class RedPants(Necklace):
    target = item.EquipTarget("Feet")

class Tentacle(Necklace):
    target = item.EquipTarget("Tentacle")

class Cuirass(Necklace):
    target = item.EquipTarget("Torso")

class BetterCuirass(Necklace):
    name = "Cuirass"
