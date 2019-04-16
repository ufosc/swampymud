'''module containing the CommandDict class'''

class Command:
    def __init__(self, name, func, type_name, source=None):
        self.name = name
        self._func = func
        self.type_name = type_name
        self.source = source
    
    def __call__(self, *args, **kwargs):
        if self.source:
            return func(source, *args, **kwargs)
        else:
            return func(*args, **kwargs)
    
    def __str__(self):
        return self.name


class CommandDict:

    def __init__(self, cmds=[]):
        self._commands = {}
        self._command_names = {}
        self._types = {}
        for cmd in cmds:
            self.add_cmd(cmd)

    def add_cmd(self, cmd, name=None):
        if name is None:
            name = str(cmd)
        self._commands[name] = cmd
        self._command_names[cmd] = name
        if cmd.type_name not in self._types:
            self._types[cmd.type_name] = []
        self._types[cmd.type_name].append(cmd)
    
    def remove_cmd(self, cmd):
        '''provide a command to remove from the dict'''
        name = self._command_names[cmd]
        type_name = cmd.type_name
        self._types[type_name].remove(cmd)
        if not self._types[type_name]:
            del self._types[type_name]
        del self._commands[name]
        del self._command_names[cmd]
    
    def remove_name(self, name):
        '''provide a name to remove from the dict'''
        cmd = self._commands[name]
        type_name = cmd.type_name
        self._types[type_name].remove(cmd)
        if not self._types[type_name]:
            del self._types[type_name]
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
        '''returns true if cmd with name 'name' exists'''
        return name in self._commands
    
    def has_cmd(self, cmd):
        '''returns true if cmd with name 'name' exists'''
        return cmd in self._command_names

    def help(self, width=30):
        output = ""
        for type, cmds in self._types.items():
            output += "{0:-^{width}}\n".format(type, width=width)
            length = 0
            maxlength = 0
            names = []
            for cmd in cmds:
                name = self._command_names[cmd]
                length += len(name) + 1
                if length >= width - 2:
                    length = len(name)
                    output += " " +  " ".join(names) + " \n"
                    names = []
                    maxlength = 0
                names.append(name)
            output += " " +  " ".join(names) + " \n"
        return output

def dummy_command(name, type_name):
    return Command(name, lambda x: x, type_name)
m = dummy_command("make", "BUILDING")
c = dummy_command("compile", "BUILDING")
d = dummy_command("decant", "ALCHEMY")
b = dummy_command("brew", "ALCHEMY")
cd = CommandDict()
cd.add_cmd(m)
cd.add_cmd(c)
cd.add_cmd(d)
cd.add_cmd(b)
print(cd.help())