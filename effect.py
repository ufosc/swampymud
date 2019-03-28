'''Module defining the effect class'''
from itertools import zip_longest
import util
from util.biject import Biject

class Effect(type):
    '''metaclass establishing what an effect does'''

    reverse = Biject()
    def __init__(self, cls, bases, namespace, **kwargs):
        if "name" not in namespace:
            self.name = util.camel_to_space(cls)
        if not (cls == "BaseEffect" or cls == "StatusEffect"):
            assert("apply" in namespace and callable(namespace["apply"]))
    
    def __str__(self):
        return self.name
    
    def __add__(self, other):
        '''add two effects together'''
        return CompoundEffect(self, other)
    
    @staticmethod
    def reverse_effect(eff):
        #TODO: consider removing this
        if type(eff) not in Effect.reverse:
            raise ValueError("Effect %s has no defined reverse" % (type(eff)))
        return Effect.reverse[type(eff)](*eff.params)
        

#TODO consider scrapping this
class BaseEffect(metaclass=Effect):
    param_schema = []

    def __init__(self, *params):
        for index, (typ, param) in enumerate(zip_longest(self.param_schema, params)):
            if typ is None:
                raise ValueError("%s received %i, expect arguments expected %i" % (self.__class__, len(self.param_schema), len(params)))
            if not isinstance(param, typ):
                raise ValueError("%s received argument %i of type %s, expected %s" % (self.__class__, index, type(param), typ))
        self.params = params

    def __init_subclass__(self, reverse=None, **kwargs):
        '''overriding this method to allow the 'reverse' keyword to work'''
        #TODO: add support for parameterized effects
        # check __init__ method?
        if reverse:
            assert(isinstance(reverse, Effect))
            assert(self.param_schema == reverse.param_schema)
            Effect.reverse[self] = reverse
        super().__init_subclass__(**kwargs)
    
    def __repr__(self):
        if self.params:
            return "%s%r" %(self.__class__.name, self.params)
        else:
            return "%s()" % self.__class__.name

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

class StatusEffect(Effect):
    def __init__(self, cls, bases, namespace, **kwargs):
        super().__init__(cls, bases, namespace)
        if "name" not in namespace:
            self.name = util.camel_to_space(cls)
        if "status_name" not in namespace:
            self.state_name = cls + "Status"

    @staticmethod
    def create_pair(forward, inverse, status_name):
        # return a pair of reversing effects
        pass
        



class _StatusEffectBase(metaclass=StatusEffect):
    def __init__(self, amount):
        self.amount = amount

    # add this on in the metaclass?
    # make this either add or remove the effects
    def apply(self, target):
        #best way to add to both??
        try:
            # try to set the status with 
            target.set_status(self.status_name, )
        except AttributeError:
            pass
        try:
            # try calling the trigger
            getattr(target, self.method_name)(self.amount)
        except AttributeError:
            pass
    
    def __init_subclass__(self, reverse=None, **kwargs):
        '''overriding this method to allow the 'reverse' keyword to work'''
        if reverse:
            assert(isinstance(reverse, Effect))
            assert(self.param_schema == reverse.param_schema)
            Effect.reverse[self] = reverse
        super().__init_subclass__(**kwargs)

    def __add__(self, other):
        if type(other) is type(self):
            new_amount = self.amount + other.amount
        elif type(other) is Effect.reverse[self]:
            new_amount = self.amount - other.amount
        else:
            return NotImplemented
        return self.create_new(new_amount)
    
    def __sub__(self, other):
        if type(other) is type(self):
            new_amount = self.amount - other.amount
        elif type(other) is Effect.reverse[self]:
            new_amount = self.amount + other.amount
        else:
            return NotImplemented
            #raise TypeError("Cannot combine %s with %s" % (type(self), type(other)))
        return self.create_new(new_amount)
       
    def __mul__(self, other):
        new_amount = self.amount * other
        return self.create_new(new_amount)
    
    def __floordiv__(self, other):
        new_amount = self.amount // other
        return self.create_new(new_amount)

    def __repr__(self):
        if self.params:
            return "%s(%s)" % (self.__class__name, self.amount)
    
    @classmethod
    def create_new(cls, amt):
        '''create a new effect in this class's dimension, based on new_amount
        if new_amount is positive, an effect of this type is created
        if new_amount is zero, a null effect is created
        if new_amount is negative, an effect of the inverse type is created
        '''
        if amt > 0:
            return cls(amt)
        elif amt == 0:
            return NullEffect
        else:
            return Effect.reverse[cls](amt * -1)
        

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
    param_schema = [str]
    def apply(self, target):
        try:
            target.ignite()
        except AttributeError:
            pass

class Extinguish(BaseEffect, reverse=Ignite):
    param_schema = [str]
    def apply(self, target):
        try:
            target.extinguish()
        except AttributeError:
            pass
