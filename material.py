from effect import Effect

class Material:

    def __init__(self, max_durability, damage, *effects):
        self._max_durability = max_durability
        self._damage = damage
        self.effects = []
        for effect in effects:
            if isinstance(effect, Effect):
                self.effects.append(effect)

    @property
    def max_durability(self):
        return self._max_durability

    @property
    def damage(self):
        return self._damage

iron = Material(max_durability=100, damage=20) 

steel = Material(max_durability=120, damage=30)

gatorbone = Material(max_durability=1000, damage=500)

default_material = Material(max_durability=1, damage=0)

wood = Material(max_durability=15, damage=5)

    

