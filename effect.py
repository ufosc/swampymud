'''Module defining the effect class'''
import math
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
            assert "apply" in namespace or any([hasattr(base, "apply") and callable(base.apply) for base in bases])
    
    def __str__(self):
        return self.name
    
    @staticmethod
    def reverse_effect(eff):
        #TODO: consider removing this
        if type(eff) not in Effect.reverse:
            raise ValueError("Effect %s has no defined reverse" % (type(eff)))
        return Effect.reverse[type(eff)](*eff.params)

        
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
    
    def __add__(self, other):
        '''overriding +, result is a compound effect'''
        if not isinstance(type(other), Effect):
            return NotImplemented
        else:
            return CompoundEffect(self, other)

    def __repr__(self):
        if self.params:
            return "%s%r" %(self.__class__.name, self.params)
        else:
            return "%s()" % self.__class__.name


class StatusEffect(Effect):
    def __init__(self, cls, bases, namespace, **kwargs):
        super().__init__(cls, bases, namespace)
        if "name" not in namespace:
            self.name = util.camel_to_space(cls)
        if "state_name" not in namespace:
            self.state_name = cls + "Status"
        if "method_name" not in namespace:
            self.method_name = cls.lower()
        if "reverse" in namespace:
            rev = namespace["reverse"]
            assert(isinstance(rev, Effect))
            assert(rev.state_name == self.state_name)
            Effect.reverse[rev] = self
            self.is_reverse = True
        else:
            self.is_reverse = False

    @staticmethod
    def create_pair(forward, inverse, state_name):
        # return a pair of reversing effects
        status_eff1 = StatusEffect(forward, (StatusEffectBase,), {"state_name" : state_name})
        status_eff2 = StatusEffect(inverse, (StatusEffectBase,), {"state_name" : state_name, "reverse" : status_eff1})
        return status_eff1, status_eff2


class StatusEffectBase(metaclass=StatusEffect):
    def __init__(self, amount):
        self.amount = amount

    def apply(self, target):
        if not self.is_reverse:
            try:
                # try to add status with name
                target.add_status(self.state_name)
            except AttributeError:
                pass
        else:
            try:
                # try to add status with name
                target.remove_status(self.state_name)
            except AttributeError:
                pass
        try:
            # try calling the trigger
            getattr(target, self.method_name)(self.amount)
        except AttributeError:
            pass

    def __add__(self, other):
        '''overriding +
        this is analgous to vector addition'''
        if type(other) is type(self):
            new_amount = self.amount + other.amount
        elif type(other) is Effect.reverse[type(self)]:
            new_amount = self.amount - other.amount
        else:
            return NotImplemented
        return self.create_new(new_amount)
    
    def __sub__(self, other):
        '''overriding -
        this is analgous to vector addition'''
        if type(other) is type(self):
            new_amount = self.amount - other.amount
        elif type(other) is Effect.reverse[type(self)]:
            new_amount = self.amount + other.amount
        else:
            return NotImplemented
            #raise TypeError("Cannot combine %s with %s" % (type(self), type(other)))
        return self.create_new(new_amount)
       
    def __mul__(self, other):
        '''overriding * 
        this is analogous to scalar multiplication'''
        new_amount = self.amount * other
        return self.create_new(new_amount)
    
    def __rmul__(self, other):
        '''overriding right multiplication
        this is analogous to scalar multiplication'''
        return self * other
    
    def __floordiv__(self, other):
        '''overriding /
        this is analogous to scalar multiplication'''
        new_amount = self.amount / other
        return self.create_new(new_amount)

    def __repr__(self):
        '''overriding repr()'''
        return "%s(%s)" % (type(self).name, self.amount)
    
    @classmethod
    def create_new(cls, amt):
        '''create a new effect in this class's dimension, based on new_amount
        if new_amount is positive, an effect of this type is created
        if new_amount is zero, a null effect is created
        if new_amount is negative, an effect of the inverse type is created
        '''
        if math.isnan(amt):
            amt = 0
        elif not math.isinf(amt):
            amt = int(amt)
        if amt == 0:
            return NULL_EFFECT
        elif amt > 0:
            return cls(amt)
        else:
            return Effect.reverse[cls](amt * -1)

class CompoundEffect(metaclass=Effect):
    '''class that represents combinations of individual effects'''

    def __init__(self, *subs):
        self._subeffects = []
        for subeff in subs:
            if isinstance(subeff, CompoundEffect):
                self._subeffects.extend(subeff)
            elif isinstance(subeff, BaseEffect):
                self._subeffects.append(subeff)
            elif isinstance(subeff, StatusEffectBase):
                sum_effect = None
                for appended_eff in list(self._subeffects):
                    sum_effect = subeff.__add__(appended_eff)
                    if sum_effect is NotImplemented:
                        sum_effect = None
                        continue
                    self._subeffects.remove(appended_eff)
                    break
                if sum_effect:
                    self._subeffects.append(sum_effect)
                else:
                    self._subeffects.append(subeff)
            else:
                raise TypeError("%r is not an Effect" % subeff)
        self._subeffects = tuple(self._subeffects)
  
    def __add__(self, other):
        '''overriding +
        this returns a union between this and other'''
        if isinstance(type(other), Effect):
            return CompoundEffect(self, other)
        else:
            return NotImplemented

    def __radd__(self, other):
        return self + other
    
    def __sub__(self, other):
        if isinstance(type(other), StatusEffect):
            new_effs = []
            sum_effect = None
            for subeff in self._subeffects:
                if not sum_effect:
                    try:
                        sum_effect = subeff - other
                    except TypeError:
                        new_effs.append(subeff)
                else:
                    new_effs.append(subeff)
            if sum_effect:
                new_effs.append(sum_effect)
            else:
                new_effs.append(-1 * other)
            return CompoundEffect(*new_effs)
        
        elif isinstance(type(other), Effect):
            # should we try to remove other effects?
            return NotImplemented
        else:
            return NotImplemented

    def __addi__(self, subeff):
        '''overriding +=
        adds "subeff" to list subeffects'''
        if isinstance(type(subeff), Effect):
            return CompoundEffect(self, subeff)
        else:
            return NotImplemented
    
    def __mul__(self, amount):
        '''overriding *
        returns a new compound effect with all
        FILL THIS IN
        '''
        if not isinstance(amount, int) and not isinstance(amount, float):
            return NotImplemented
        new_eff = []
        for subeff in self:
            try:
                new_eff.append(subeff * amount)
            except TypeError:
                new_eff.append(subeff)
        return CompoundEffect(*new_eff)

    def __rmul__(self, amount):
        '''overriding right *
        returns a new compound effect with all
        FILL THIS IN
        '''
        return self * amount

    def __floordiv__(self, amount):
        '''overriding //
        FILL THIS IN
        '''
        new_eff = []
        for subeff in self:
            try:
                new_eff.append(subeff // amount)
            except TypeError:
                new_eff.append(subeff)
        return CompoundEffect(*new_eff)
    
    def apply(self, target):
        for subeff in self:
            subeff.apply(target)

    def __iter__(self):
        for subeff in self._subeffects:
            yield subeff
    
    def __repr__(self):
        '''overriding repr()'''
        return "CompoundEffect%r" % (self._subeffects,)


NULL_EFFECT = CompoundEffect()

class Teleport(BaseEffect):
    param_schema = [str]
    def apply(self, target):
        try:
            target.ignite()
        except AttributeError:
            pass

class Recall(BaseEffect, reverse=Teleport):
    param_schema = [str]
    def apply(self, target):
        try:
            target.extinguish()
        except AttributeError:
            pass

Ignite, Extinguish  = StatusEffect.create_pair("Ignite", "Extinguish", "Fire")
Freeze, Melt  = StatusEffect.create_pair("Freeze", "Melt", "Frozen")
curse = CompoundEffect(Ignite(10), Melt(5), Teleport('Hell'))
curse2 = curse - Ignite(4)