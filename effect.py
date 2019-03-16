from abc import ABC, abstractmethod, ABCMeta

class Effect(metaclass=ABCMeta):
    ''' Effect metaclass, establishing all necessary effect behavior '''

    def __init__(self, **kwargs):
        self.name = self.__class__.__name__

    @abstractmethod
    def apply(self, target):
        ''' Applies the effect to the target '''
        pass
    
    def str(self):
        return self.name

    def repr(self):
        pass

class Damage(Effect):
    ''' Effect which decrements the targets health by a number specified during instantiation '''

    def __init__(self, dmg_points, **kwargs):
        super().__init__(**kwargs)
        self.damage = dmg_points
    
    def apply(self, target):
        try:
            target.health -= self.damage
        except:
            pass
        super().apply(target)


class Ignite(Effect):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def apply(self, target):
        try:
            pass
            # target.status.add(str(target) + "is on fire")
            # OR target.ignite() and handle the ignite descriptionn target-side
        except:
            pass
        super().apply(target)

class Burn(Damage, Ignite):
    ''' Combination of Damage and Ignite effects; constructor requires dmg_points keyword '''

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def apply(self, target):
        super().apply(target)

