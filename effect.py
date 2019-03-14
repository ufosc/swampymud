from abc import ABC, abstractclassmethod, ABCMeta

class Effect(metaclass=ABCMeta):

    def __init__(self):
        self.name = self.__class__.__name__

    @abstractmethod
    def apply(self):
        ''' Applies the effect to the target '''
        pass
    
    def str(self):
        return self.name

class Damage(Effect):

    def __init__(self, num):
        super().__init__()
        self.damage = num
    
    def apply(self, target):
        try:
            target.health -= num
        except:
            pass

    def repr(self):
        pass
        
    