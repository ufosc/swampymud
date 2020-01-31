from item import UsableBase
from character import Character
from effect import Damage
import material
import util.english as eng

class Sword(UsableBase):

    # Multiplier for sword damage
    multiplier = 2

    # *args is a list of effects specified when creating a sword
    def __init__(self, material, *args):
        super().__init__()
        self.durability = material.max_durability
        self.damage = material.damage * self.multiplier
        self.effects = material.effects + list(args)
        self.effects.append(Damage(self.damage))
        # If the list of effects is more than just damage (len(self.effects) > 1) then the sword is called enchanted
        if(len(self.effects) > 1):
            self._item_name = ("Enchanted " + str(material) + " sword").title()
            self._description = [eng.indefinite_article(self._item_name) + " " + self._item_name]
            self._description.append("{:-^30}".format("Enchantments"))
            for effect in self.effects:
                self._description.append("{: ^30}".format(str(effect)))
        else:
            self._item_name = (str(material) + " sword").title()
            self._description = (eng.indefinite_article(str(self._item_name))) + " " + self._item_name

    # Applies all of effects on target
    def use(self, target):
        for effect in self.effects:
            effect.apply(target)
        self.durability -= 1

    def __str__(self):
        return self._item_name

    @property
    def name(self):
        return self._item_name
     