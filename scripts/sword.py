from item import UsableBase
from character import Character
from effect import Damage
import material

class Sword(UsableBase):

    multiplier = 2 

    def __init__(self, material, *args):
        super().__init__()
        self._item_name = str(material) + "sword"
        self.durability = material.max_durability
        self.damage = material.damage * self.multiplier
        self.effects = material.effects + list(args)
        self.effects.append(Damage(self.damage))

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
     