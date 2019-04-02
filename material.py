from effect import Effect

class Material:

    def __init__(self, name, max_durability, damage, *effects):
        self._name = name
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

    def __str__(self):
        return self._name

default_material = Material(name="default_material", max_durability=1, damage=0)

iron = Material(name="iron",max_durability=100, damage=20) 

steel = Material(name="steel",max_durability=120, damage=30)

gatorbone = Material(name="gator bone",max_durability=1000, damage=500)

wood = Material(name="wood", max_durability=15, damage=5)

    

