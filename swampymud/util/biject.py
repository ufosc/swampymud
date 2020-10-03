'''module dedicated to the biject class
If you are confused about what a bijection is, refer to:
https://simple.wikipedia.org/wiki/Bijective_function
'''

class Biject:
    '''Class representing a bijection.
    A biject is simply a special dict representing a one-to-one
    relationship, (a normal dict is many-to-one). Because a bijection
    has exactly one value for every key, we can pass a value into
    the biject to its original key back.
    In a normal dict:
        d = dict()
        d["a"] = "apple"
        d["apple"] # this produces a KeyError
        d["b"] = "apple" # this works, many keys can point to one value
    With a biject:
        b = biject()
        b["a"] = "apple"
        d["apple"] # this works, giving a key to a biject its value back
        d["b"] = "apple" # produces a ValueError, since only one key
        # can point to a value at a time
    '''
    def __init__(self, start_dict=None):
        '''start_dict can be provided to
        fill the bijection with something
        otherwise, an empty bijection is created'''
        self._left = {}
        self._right = {}
        if start_dict:
            for l, r in start_dict.items():
                self[l] = r

    def __getitem__(self, key):
        '''get the object corresponding to 'key'''
        if key in self._left:
            return self._left[key]
        else:
            return self._right[key]

    def __setitem__(self, key, value):
        '''create a pair with 'key' and 'value'
        if key or value is already in use,
        a KeyError is raised'''
        try:
            current_value = self[key]
            if current_value is not value:
                raise ValueError("Key already assigned to different value")
        except KeyError:
            pass
        try:
            current_key = self[value]
            if current_key is not key:
                raise ValueError("Value already assigned to different key")
        except KeyError:
            pass
        self._left[key] = value
        self._right[value] = key

    def __delitem__(self, key):
        '''delete 'key'
        raises KeyError if 'key' is not
        in bijection'''
        if key in self._left:
            value = self._left[key]
            del self._left[key]
            del self._right[value]
        else:
            value = self._right[key]
            del self._right[key]
            del self._left[value]

    def __contains__(self, key):
        '''returns true if 'key' is in bijection'''
        return key in self._left or self._right

    def __repr__(self):
        '''return a representation of the bijection'''
        if self._left:
            return f"Biject({self._left!r})"
        else:
            return "Biject()"

    def __iter__(self):
        '''iterate over (key, value) in bijection'''
        for left, right in self._left.items():
            yield (left, right)

    def __len__(self):
        '''overriding len() to return number of pairs'''
        return len(self._left)
