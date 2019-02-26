if __name__ == "__main__":
    '''__name__ holds the name of the module
    the top level script is called __main__
    otherwise, if imported, it is not __main__
    '''
    print("This script is not intended to be executable.")
    exit()

server = None
def export_server(inp_server):
    '''store a server in the mudscript module
    this must be done before mudscript can 
    be called in scripts
    '''
    global server
    server = inp_server


class MuddyException(Exception):
    '''Exception class made purely to highlight
    mudscript-specific errors'''
    pass


def server_warning(func, *args, **kwargs):
    '''decorator to break if an import is attempted'''
    def decorated(*args, **kwargs):
        global server
        if not server:
            raise MuddyException("Must export a server before using mudscript.")
        return func(*args, **kwargs)
    return decorated


@server_warning
def get_location(key):
    global server
    try:
        value = server.lib.locations[key]
    except KeyError:
        raise MuddyException("Location '%s' not found." % key)
    return server.lib.locations[key]

@server_warning
def get_item(key):
    global server
    try:
        value = server.lib.items[key]
    except KeyError:
        raise MuddyException("Item '%s' not found." % key)
    return value

@server_warning
def get_char_class(key):
    global server
    try:
        value = server.lib.char_classes[key]
    except KeyError:
        raise MuddyException("CharacterClass '%s' not found." % key)
    return value

@server_warning
def message_all(msg):
    '''send message to all players'''
    global server
    server.send_message_to_all(msg)