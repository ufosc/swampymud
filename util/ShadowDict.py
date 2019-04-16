'''module containing the ShadowDict class'''

class ShadowDict:
    '''class representing a ShadowDict,
    in which multiple values can be stored under one key
    with only the most recent value being visible'''

    def __init__(self, start_dict=None):
        '''start_dict can be provided to 
        fill the ShadowDict with something
        otherwise, an empty ShadowDict is created'''
        self._dict = {}
        if start_dict:
            self._dict = start_dict.copy()

    def __getitem__(self, key):
        '''get the object corresponding to 'key'
        raises a KeyError if key is not present'''
        lst = self._dict[key]
        return lst[-1]

    def __setitem__(self, key, value):
        '''map 'key' to 'value'
        if key or value is already in use, the previous value is shadowed'''
        if key in self._dict:
            self._dict[key].append(value)
        else:
            self._dict[key] = [value]

    def __delitem__(self, key):
        '''delete 'key'
        if a value was shadowed, the key is reverted to that previous value
        raises KeyError if key is not in use'''
        lst = self._dict[key]
        lst.pop()
        # if lst is now empty, remove the key altogether
        if not lst:
            del self._dict[key]
        
    def __contains__(self, key):
        '''returns true if 'key' is in bijection'''
        return key in self._dict

    def __repr__(self):
        '''return a representation of the bijection'''
        if self._dict:
            return "ShadowDict(%r)" % self._dict
        else:
            return "ShadowDict()"

    def __iter__(self):
        '''iterate over the keys of the dict'''
        for k in self._dict.keys():
            yield k
    
    def __dict__(self):
        '''return a dictionary representation
        of the ShadowDict'''
        return self._dict.copy()