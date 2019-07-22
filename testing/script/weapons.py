from item import Equippable
from .basic_rpg import HealthPotion
class Bar:
    '''this class should not be imported'''
    pass

class DerivedBar(Bar):
    '''this class should not be imported'''
    pass

class IronSword(Equippable):
    target = "foo"
    def equip(self):
        pass
    
    def unequip(self):
        pass

class WoodenBow(Equippable):
    target = "foo"
    def equip(self):
        pass
    
    def unequip(self):
        pass

class CursedRing(Equippable):
    target = "foo"
    def equip(self):
        pass
    
    def unequip(self):
        pass

class Foo(str):
    pass
