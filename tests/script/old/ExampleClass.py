from character import Character, CharFilter
import item
import mudscript
from scripts.RareClass import RareClass

class ExampleClass(Character):
    starting_location = mudscript.get_location("Marston Basement")
    equip_slots = ["Head", "Torso", "Feet"]

    def cmd_echo(self, args):
        '''Echoes the provided phrase back.
        usage: example [phrase]
        '''
        self.message(" ".join(args))
        
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

    @item.equip_command
    def secret(self, character, args): 
        '''this method is a secret'''
        character.message("Hey this is secret Ow0")

    @item.filtered_command(CharFilter("whitelist", [RareClass]))
    def rare(self, character, args): 
        '''this method is a secret'''
        character.message("Hey this is rare Ow0")
        

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
