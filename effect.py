'''Module defining the effect class'''
import util
from util.biject import Biject

class Effect(type):
    '''metaclass establishing what an effect does'''

    reverse = Biject()
    def __init__(self, cls, bases, dict, **kwargs):
        if "name" not in dict:
            self.effect_name = util.camel_to_space(cls)
        if cls != "BaseEffect":
            assert("apply" in dict and callable(dict["apply"]))
    
    def __str__(self):
        return self.name
    
    def __add__(self, other):
        '''add two effects together'''
        return CompoundEffect(self, other)
    
    @staticmethod
    def reverse_effect(self, effect):
        #TODO: reverse effect, take all parameters into account
        pass


class BaseEffect(metaclass=Effect):
    def __init_subclass__(self, reverse=None, **kwargs):
        '''overriding this method to allow the 'reverse' keyword to work'''
        #TODO: add support for parameterized effects
        # check __init__ method?
        if reverse:
            assert(isinstance(reverse, Effect))
            Effect.reverse[self] = reverse
        super().__init_subclass__(**kwargs)


def cancel_out(self, effect_list):
    '''returns a copy of effect_list without any 
    opposing reversible effects cancelled out'''
    effect_list = effect_list.copy()
    index = 0
    while index < len(effect_list):
        eff = effect_list[index]
        if eff in Effect.reverse and Effect.reverse[eff] in effect_list:
            effect_list.remove(eff)
            effect_list.remove(Effect.reverse[eff])
            continue
        index += 1
    return effect_list


def remove_duplicates(self, effect_list):
    '''returns a copy of effect_list without any 
    redundant idempotent effects'''
    effect_list = effect_list.copy()
    index = 0
    while index < len(effect_list):
        eff = effect_list[index]
        if eff in effect_list[index+1:]:
            del effect_list[index]
            continue
        index += 1


class CompoundEffect(metaclass=Effect):
    '''class that represents combinations of individual effects'''

    def __init__(self, *subs):
        self._subeffects = []
        for subeff in subs:
            if isinstance(subeff, CompoundEffect):
                self._subeffects.append(*subeff)
            elif isinstance(subeff, Effect):
                self._subeffects.append(subeff)
            else:
                raise TypeError("Invalid subeffect %s" % subeff)
    
    def apply(self, target):
        for subeff in self:
            subeff.apply(target)

    def __iter__(self):
        for subeff in self._subeffects:
            yield subeff


class Melt(BaseEffect):
    def apply(self, target):
        try:
            target.melt()
        except AttributeError:
            pass


class Freeze(BaseEffect, reverse=Melt):
    def apply(self, target):
        try:
            target.freeze()
        except AttributeError:
            pass

class Ignite(BaseEffect):
    def apply(self, target):
        try:
            target.ignite()
        except AttributeError:
            pass

class Extinguish(BaseEffect, reverse=Ignite):
    def apply(self, target):
        try:
            target.extinguish()
        except AttributeError:
            pass
