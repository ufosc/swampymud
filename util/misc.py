def camel_to_space(name):
    '''adds spaces before capital letters
    ex: "CamelCaseClass" => "Camel Case Class"'''
    output = ""
    for letter in name:
        if letter.upper() == letter:
            output += " "
        output += letter
    return output.strip()