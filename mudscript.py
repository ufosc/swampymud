'''module containing useful functions for creating MuddySwamp scripts'''

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
def message_all(msg):
    '''send message to all players'''
    global server
    server.send_message_to_all(msg)