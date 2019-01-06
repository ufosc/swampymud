import random
import bisect as _bisect
import itertools as _itertools

# Random.choices function is only included in Python >3.6
# Python 3.5 is the highest version available in the Ubuntu repos
# So, here, we copy straight from the source code with only a few modifications

def choices(population, weights=None, *, cum_weights=None, k=1):
    """Return a k sized list of population elements chosen with replacement.

    If the relative weights or cumulative weights are not specified,
    the selections are made with equal probability.

    """
    if cum_weights is None:
        if weights is None:
            _int = int
            total = len(population)
            return [population[_int(random.random() * total)] for i in range(k)]
        cum_weights = list(_itertools.accumulate(weights))
    elif weights is not None:
        raise TypeError('Cannot specify both weights and cumulative weights')
    if len(cum_weights) != len(population):
        raise ValueError('The number of weights does not match the population')
    bisect = _bisect.bisect
    total = cum_weights[-1]
    hi = len(cum_weights) - 1
    return [population[bisect(cum_weights, random.random() * total, 0, hi)]
            for i in range(k)]


def weightedchoice(weighted_objects):
    '''
    returns a random object based upon a dictionary
    where objects are keys, and their relative weights
    are the corresponding values

    this function makes it easier to use random.choices()
    '''
    # unzipping the weighted items
    objects, weights = zip(*weighted_objects.items())
    return choices(objects, weights)[0]


class RandDist:
    '''A random weighted distribution
    construct by providing a dictionary with keys being objects,
    and values corresponding to the weight of the object
    the value of a getting an object = w/total
    where w is the weight of object, and total is the sum of all weights
    '''
    def __init__(self, weighted_items):
        # convert weighted_items into a list of tuples
        weighted_items = weighted_items.items()
        # unzip the list into corresponding weights
        self.items, self.weights = zip(*weighted_items)
        
    def get(self):
        '''randomly return an item, based on weight'''
        return random.choices(self.items, self.weights)[0]

class ChoiceDist:
    '''A random distribution where all items are equally weighted'''
    def __init__(self, items):
        self.items = items
    
    def get(self):
        return random.choice(self.items)