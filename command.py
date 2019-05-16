'''module containing the CommandDict class'''
from util.shadowdict import ShadowDict

class Command:
    '''class representing a Command
    a Command has 3 important values:
        - a name that will represent the command
        - a function that the command will call
        - a type_name that is used for sorting the help menu
    Optionally, a Command may also have a source
    (this source is used if the function is an unbound method)
    '''

    def __init__(self, name, func, type_name, source=None):
        self.name = name
        self._func = func
        self.type_name = type_name
        self.source = source

    def __call__(self, *args, **kwargs):
        if self.source is not None:
            return self._func(self.source, *args, **kwargs)
        else:
            return self._func(*args, **kwargs)
    
    def help(self):
        return self._func.__doc__

    def __repr__(self):
        return "Command%r" % ((self.name, self._func, self.type_name, self.source),)
    
    def __hash__(self):
        # TODO: make these properties immutable somehow?
        return hash((self.name, self._func, self.type_name, self.source))

    def __eq__(self, other):
        '''overriding  =='''
        return all((self.name == other.name, self._func is other._func,
                    self.type_name == other.type_name, self.source is other.source))

    def __str__(self):
        return self.name

# TODO: improve the help menu to make it more efficient
# options include adding indicies for CommandTypes
# or simply caching the help menu
class CommandDict:
    '''dictionary that maps names (strings) to commands (functions)'''
    def __init__(self):
        '''initialize a CommandDict with commands [cmds]'''
        self._commands = ShadowDict()
        self._command_names = {}

    def add_cmd(self, cmd, name=None):
        '''add cmd to the dict with name
        if 'name' is not provided, the builtin name
        of the command is used'''
        if name is None:
            name = str(cmd)
        self._commands[name] = cmd
        self._command_names[cmd] = name

    #TODO: document shadowing behavior
    def remove_cmd(self, cmd):
        '''provide a command to remove from the dict'''
        name = self._command_names[cmd]
        self._commands.remove_value(name, cmd)
        del self._command_names[cmd]

    #TODO: document shadowing behavior
    def remove_name(self, name):
        '''provide a name to remove from the dict'''
        cmd = self._commands[name]
        del self._commands[name]
        del self._command_names[cmd]

    def change_name(self, current, new_name):
        '''change the name associated with a command'''
        cmd = self._commands[current]
        del self._commands[current]
        self._commands[new_name] = cmd
        self._command_names[cmd] = new_name

    def get_cmd(self, name):
        '''get a cmd by providing its name'''
        return self._commands[name]

    def get_name(self, cmd):
        '''get a name by providing the cmd'''
        return self._command_names[cmd]

    def has_name(self, name):
        '''returns true if 'name' is in use'''
        return name in self._commands

    def has_cmd(self, cmd):
        '''returns true if 'cmd' exists in the dict'''
        return cmd in self._command_names

    def iter_cmds(self):
        for cmd in self._command_names:
            yield cmd

    def help(self, width=30):
        '''produce a formatted help menu with width [width]'''
        output = []

        # TODO: improve this sorting process
        types = {}
        # create a type dictionary
        for name, cmd in self._commands.items():
            if cmd.type_name not in types:
                types[cmd.type_name] = []
            types[cmd.type_name].append(name)
        typelist = list(types.keys())

        # sorting through the typelist to ensure a reliable ordering
        # TODO: find a better way of doing this
        typelist.sort()
        if "Default" in typelist:
            typelist.remove("Default")
            typelist.insert(0, "Default")
        if "Equipped" in typelist:
            typelist.remove("Equipped")
            typelist.append("Equipped")
        if "Environmental" in typelist:
            typelist.remove("Environmental")
            typelist.append("Environmental")
        for typ in typelist:
            names = types[typ]
            output.append("{0:-^{width}}".format(typ + " Commands", width=width))
            length = 0
            name_row = []
            for name in names:
                length += len(name) + 2
                if length >= width - 2:
                    length = len(name)
                    output.append("{0: ^{width}}".format("  ".join(name_row), width=width))
                    name_row = []
                name_row.append(name)
            output.append("{0: ^{width}}".format("  ".join(name_row), width=width))
        return "\n".join(output)


# def dummy_command(name, type_name):
#     return Command(name, lambda x: x, type_name)
# y = dummy_command("say", "Player")
# m = dummy_command("make", "Paladin")
# c = dummy_command("compile", "Paladin")
# d = dummy_command("decant", "Alchemist")
# b = dummy_command("brew", "Alchemist")
# p = dummy_command("pull", "Environmental")
# s = dummy_command("swing", "Equipped")
# x = dummy_command("brew", "Environmental")
# cd = CommandDict()
# cd.add_cmd(m)
# cd.add_cmd(c)
# cd.add_cmd(d)
# cd.add_cmd(b)
# print(cd.help())
# cd.add_cmd(y)
# print(cd.help())