'''module dedicated to the biject class'''

class Biject:
    '''class representing a bijection'''
    def __init__(self, start_dict=None):
        self._left = {}
        self._right = {}
        if start_dict:
            for l, r in start_dict.items():
                self[l] = r

    def __getitem__(self, key):
        if key in self._left:
            return self._left[key]
        else:
            return self._right[key]

    def __setitem__(self, key, value):
        try:
            current_value = self[key]
            if current_value is not value:
                raise TypeError("Key already assigned to different value")
        except KeyError:
            pass
        try:
            current_key = self[value]
            if current_key is not key:
                raise TypeError("Value already assigned to different key")
        except KeyError:
            pass
        self._left[key] = value
        self._right[value] = key

    def __delitem__(self, key):
        if key in self._left:
            value = self._left[key]
            del self._left[key]
            del self._right[value]
        else:
            value = self._right[key]
            del self._right[key]
            del self._left[value]
    
    def __contains__(self, key):
        return key in self._left or self._right

    def __repr__(self):
        if self._left:
            return "Biject(%r)" % self._left
        else:
            return "Biject()"

    def __iter__(self):
        for left, right in self._left.items():
            yield (left, right)
    
    def __dict__(self):
        return self._left.copy()