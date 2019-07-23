from item import Equippable, EquipTarget, MiscItem
from .basic_rpg import HealthPotion

class IronSword(Equippable):
    target = EquipTarget("Right Hand")
    def equip(self):
        pass
    
    def unequip(self):
        pass

class WoodenStaff(Equippable):
    target = EquipTarget("Right Hand")
    def equip(self):
        pass
    
    def unequip(self):
        pass

# a ring that lowers the max health of someone wearing it
class CursedRing(Equippable):
    target = EquipTarget("Left Hand")

    def equip(self, char):
        try:
            char.max_health -= 10
            if char.health > char.max_health:
                char.health = char.max_health
            char.message("You feel yourself becoming weaker...")
        except AttributeError:
            pass
    
    def unequip(self, char):
        try:
            char.max_health += 10
            if char.health > char.max_health:
                char.health = char.max_health
            char.message("You breathe a sigh of relief.")
        except AttributeError:
            pass

class GoldNugget(MiscItem):
    pass