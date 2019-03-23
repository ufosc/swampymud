'''Module defining the effect class'''

class Effect(type):
    '''metaclass establishing what an effect does'''
    _prev = None
    def __init__(self, cls, bases, dict, reverse=None):
        if "effect_name" not in dict:
            self.effect_name = camel_to_space(cls)
        assert("apply" in dict and callable(dict["apply"]))
        if reverse:
            assert(isinstance(reverse, effect))
            self.reverse = reverse
            if hasattr("reverse", reverse):
                assert(reverse.reverse is self)