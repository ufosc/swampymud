'''Miscellaneous (but useful) functions that don't fit in other modules'''
#TODO: replace with regex
def camel_to_space(name):
    '''adds spaces before capital letters
    ex: "CamelCaseClass" => "Camel Case Class"'''
    output = []
    for letter in name:
        if letter.upper() == letter:
            output.append(" ")
        output.append(letter)
    return "".join(output).strip()

def to_base(num, base, alphabet="0123456789abcdefghijklmnopqrstuvwxyz"):
    '''convert an unsigned integer [num] to base 36'''
    # check that the base is in an appropriate range
    try:
        max_base = len(alphabet)
        if base > len(alphabet) or base < 2:
            raise ValueError("Expected base in range [2, %i], received %r"
                             % (max_base, base))
    except TypeError:
        raise TypeError("Expected base with <class 'int'>, received %r" % num)
    # check that the num is an unsigned integer
    try:
        if num < 1:
            if num == 0:
                return "0"
            else:
                raise ValueError("Expected unsigned integer, received %i"
                                 % num)
    except TypeError:
        raise TypeError("Expected num with <class 'int'>, received %r" % num)
    digits = []
    while num > 0:
        num, digit = divmod(num, base)
        digits.append(alphabet[digit])
    return "".join(digits[::-1])

def group_and_count(items, format="%s\t[%i]", single_format="%s", sep="\n"):
    '''takes a list of items and a formatter,
    and produces a list with counts
    if items = ["apple", "apple", "banana", "cap", "cap", "cap"]
    then output = 
        apple    [2]
        banana
        cap      [3]
    '''
    counts = {}
    for item in items:
        if item not in counts:
            counts[item] = items.count(item)
    unique_items = list(counts.keys())
    unique_items.sort()
    output = []
    for item in unique_items:
            if single_format and counts[item] == 1:
                output.append(single_format % (item,))
            else:
                output.append(format % (item, counts[item]))
    return sep.join(output)