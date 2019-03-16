from abc import ABC, abstractmethod, ABCMeta

class Effect(metaclass=ABCMeta):
    ''' Effect metaclass, establishing all necessary effect behavior '''

    def __init__(self):
        self.name = self.__class__.__name__

    @abstractmethod
    def apply(self):
        ''' Applies the effect to the target '''
        pass
    
    def str(self):
        return self.name

    def repr(self):
        pass

class Damage(Effect):
    ''' Effect which decrements the targets health by a number specified during instantiation '''

    def __init__(self, dmg_points):
        super().__init__()
        self.damage = dmg_points
    
    def apply(self, target):
        try:
            target.health -= self.damage
        except:
            pass


class Ignite(Effect):

    def __init__(self):
        super().__init__()

    def apply(self, target):
        try:
            target.status.add(str(target) + "is on fire")
            # OR target.ignite() and handle the ignite descriptionn target-side
        except:
            pass

class Burn(Damage, Ignite):
    ''' Combination of Damage and Ignite effects; constructor requires dmg_points keyword '''

    def __init__(self, **kwds):
        super().__init__(**kwds)

    def apply(self, target):
        try:
            Damage(self.damage).apply(target)
            Ignite().apply(target)
        except:
            pass

