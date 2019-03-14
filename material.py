from effect import Effect

class Material:

    def __init__(self, max_durability, damage, *effects):
        self.max_durability = max_durability
        self.damage = damage
        self.effects = []
        for effect in effects:
            if isinstance(effect, Effect):
                self.effects.append(effect)

    @property
    def max_durability(self):
        return self.max_durability

    @property
    def damage(self):
        return self.damage

Iron = Material(max_durability=100, damage=20) 

Steel = Material(max_durability=120, damage=30)

Dragonbone = Material(max_durability=1000, damage=500)

    

