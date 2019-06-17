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