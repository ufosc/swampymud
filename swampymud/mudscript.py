'''module containing useful functions for creating SwampyMud scripts'''
from swampymud.mudserver import MudServer

server = None


def export_server(inp_server):
    '''store a server in the mudscript module
    this must be done before calling the 'message_all' function
    '''
    global server
    if not isinstance(inp_server, MudServer) and inp_server is not None:
        raise TypeError(f"expected MudServer, received {type(inp_server)}")
    server = inp_server


class SwampyException(Exception):
    '''Exception class made purely to highlight
    mudscript-specific errors'''
    pass


def server_warning(func, *args, **kwargs):
    '''decorator to break if an import is attempted'''
    def decorated(*args, **kwargs):
        global server
        if not server:
            raise SwampyException("Must export a server before using mudscript.")
        return func(*args, **kwargs)
    return decorated


@server_warning
def message_all(msg):
    '''send message to all players'''
    global server
    server.message_all(msg)


@server_warning
def kick(character, **kwargs):
    """Find the client associated with [character] and disconnect
    them from the game.
    Raises KeyError if [character] cannot be found.
    """
    global server
    server.kick(character, **kwargs)


_EXPORTED_LOCATIONS = None


class LocationExport:
    """a context-manager style location exporter
    example, where my_locations is a dictionary mapping names to Locations
    with LocationExport(my_locations):
        # do stuff
    # cleans up automatically
    """
    def __init__(self, loc_dict):
        self._loc_dict = loc_dict

    def __enter__(self):
        #TODO: possible swap global with nonlocal?
        global _EXPORTED_LOCATIONS
        if _EXPORTED_LOCATIONS is not None:
            # TODO make this the correct exception
            raise Exception("Tried to export locations to mudscript  "
                            "but other locations have already been exported.")
        _EXPORTED_LOCATIONS = self._loc_dict

    def __exit__(self, exc_type, exc_value, traceback):
        # clean up the global safely
        global _EXPORTED_LOCATIONS
        _EXPORTED_LOCATIONS = None
        # if an exception occurred, raise it
        if exc_value is not None:
            raise


def import_location(name):
    """import a location with [name]
    raises KeyError if name is not found in exported locations
    raises SwampyException if no locations have been exported"""
    global _EXPORTED_LOCATIONS
    if _EXPORTED_LOCATIONS is None:
        raise SwampyException(f"Cannot access location '{name}' "
                              "(no locations are exported)")
    try:
        return _EXPORTED_LOCATIONS[name]
    except KeyError as exc:
        raise KeyError(f"Cannot access location '{name}' "
                       "(no locations with that name)") from exc
