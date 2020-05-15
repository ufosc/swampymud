'''Module defining the ShadowDict class.
A ShadowDict functions like a normal dictionary, except each key
actually points to a stack, with the most recent value being used when
__getitem__ is called / deleted when __delitem__ is called.

Thus, a key,value pair will be "shadowed" if you set the same key
to have two different values.

For example:

sd = ShadowDict()
sd["wizard"] = "gandalf"
sd["wizard"] # returns "gandalf"
sd["wizard"] = "dumbledore"
sd["wizard"] # returns "dumbledore"
del sd["wizard"]
sd["wizard"] # returns "gandalf"

This data structure is used to store character Commands, thus allowing
CharacterClass Commands to temporarily be shadowed by Equippable or
Entity Commands.
'''

class ShadowDict:
    '''class representing a ShadowDict, in which multiple values can be
    stored under one key. Only the most recent value will be visible.
    '''

    def __init__(self, start_dict=None):
        '''Create a new ShadowDict. Provide [start_dict] (optional) to
        to fill the ShadowDict with something.'''
        self._dict = {}
        if start_dict:
            for key, value in start_dict.items():
                self._dict[key] = [value]

    def __getitem__(self, key):
        '''Get the object corresponding to [key].
        Raises a KeyError if key is not present.'''
        lst = self._dict[key]
        return lst[-1]

    def __setitem__(self, key, value):
        '''Map 'key' to 'value'.
        If key is already in use, the previous value gets shadowed.'''
        if key in self._dict:
            self._dict[key].append(value)
        else:
            self._dict[key] = [value]

    def __delitem__(self, key):
        '''delete 'key'
        If a value was shadowed, the key is reverted to the previous value
        raises KeyError if key is not in use'''
        lst = self._dict[key]
        lst.pop()
        # if lst is now empty, remove the key altogether
        if not lst:
            del self._dict[key]

    def __contains__(self, key):
        '''returns true if 'key' is in ShadowDict'''
        return key in self._dict

    def __repr__(self):
        '''return a representation of the ShadowDict'''
        if self._dict:
            return "ShadowDict(%r)" % dict(self.items())
        else:
            return "ShadowDict()"

    def __iter__(self):
        '''iterate over the keys of the dict'''
        for k in self._dict.keys():
            yield k

    def copy(self):
        '''return a shallow copy of this ShadowDict'''
        return ShadowDict(start_dict=self)

    def items(self):
        '''iterate over the current key, value pairs'''
        for k in self._dict:
            yield (k, self[k])

    def remove_value(self, key, value):
        '''remove a value stored under key, even if value is shadowed
        raises a KeyError if the key is not in the ShadowDict
        raises a ValueError if the value is not stored under the key'''
        lst = self._dict[key]
        lst.remove(value)
        # remove lst if it is empty
        if not lst:
            del self._dict[key]

    def __len__(self):
        '''returns the number of keys in ShadowDict'''
        return len(self._dict)
