from item import EquippableBase
from character import Character
from effect import Damage

class Sword(EquippableBase):

    multiplier = 2 

    def __init__(self, material):
        super().__init__()
        self.durability = material.max_durability
        self.damage = material.damage * self.multiplier
        self.effects = material.effects
        self.effects.append(Damage(self.damage))

    # Applies all of effects on target
    def use(self, target):
        if isinstance(target, Character):
            for effect in self.effects:
                try:
                    effect.apply(target)
                except:
                    pass
        else:
            pass
            


      