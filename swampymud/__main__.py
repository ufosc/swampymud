#!/usr/bin/env python3
'''main script for MuddySwamp'''
import sys
import logging
import threading
import queue
import enum
import traceback
import errno
import argparse
# import the MUD server class
from swampymud.mudserver import MudServer, Event, EventType
# import modules from the MuddySwamp engine
from swampymud import mudworld, mudscript

# better names welcome
class MainServer(MudServer):
    '''Bundles a server and a library together'''
    def __init__(self, world, port):
        self.world = world
        self.default_class = None
        self.default_location = None
        self.players = {} # dict mapping socket IDs to characters
        super().__init__(port)

    def get_player_class(self):
        '''get a player class from the server'''
        if self.default_class is not None:
            return self.default_class
        else:
            return self.world.random_cls()


# Setup the logger
logging.basicConfig(format='%(asctime)s [%(threadName)s] [%(levelname)s] %(message)s',
                    level=logging.INFO,
                    handlers=[
                        logging.FileHandler("server.log"),
                        logging.StreamHandler(sys.stdout)
                    ])


SHELL_MODE = False

class ServerCommandEnum(enum.Enum):
    ''' basic enum for the type of server command'''
    BROADCAST_MESSAGE = 0
    GET_PLAYERS = 1

class ServerComand:
    '''Simple wrapper class for a server-side command'''
    def __init__(self, command_type, params):
        self.command_type = command_type
        self.params = params

class MudServerWorker(threading.Thread):
    def __init__(self, q, server, *args, **kwargs):
        self.keep_running = True
        self.q = q
        self.mud = server
        super().__init__(*args, **kwargs)


    # Cannot call mud.shutdown() here because it will try to call
    # the sockets in run on the final go through
    def shutdown(self):
        self.keep_running = False

    def run(self):
        logging.info("Starting server.")
        logging.info("Server started successfully.")
        # main game loop. We loop forever (i.e. until the program is terminated)
        while self.keep_running:
            try:
                server_command = self.q.get(block=False)
                if server_command is not None:
                    if server_command.command_type == ServerCommandEnum.BROADCAST_MESSAGE:
                        self.mud.send_message_to_all(server_command.params)
                    elif server_command.command_type == ServerCommandEnum.GET_PLAYERS:
                        logging.info("Players: ")
                        for player in self.mud.players.values():
                            logging.info(str(player))

            except Exception:
                pass

            # 'update' must be called in the loop to keep the game running and give
            # us up-to-date information
            self.mud.update()

            # handle events on the server_queue
            while self.mud.server_queue:
                event = self.mud.server_queue.popleft()
                logging.info(event)
                etype, pid, content = event
                if etype is EventType.PLAYER_JOIN:
                    logging.info("Player %s joined." % pid)
                    # create a new character and map it to the ID
                    PlayerClass = self.mud.get_player_class()
                    character = PlayerClass()
                    self.mud.players[pid] = character

                    # TODO: make all location changes silent!
                    # set the character location
                    # server default overrides everything
                    if self.mud.default_location is not None:
                        start_loc = self.mud.default_location
                    elif character.starting_location is not None:
                        start_loc = character.starting_location
                    # if no default class
                    else:
                        try:
                            start_loc = next(iter(self.mud.world.locations.values()))
                        except StopIteration:
                            logging.critical(f"Could not spawn {pid}, server has no locations")
                            continue
                        logging.warning(f"{PlayerClass} has no default location, "
                                        f"so {pid} will be spawned in {start_loc}")

                    # put the character in "greet" mode
                    character.spawn(start_loc)

                elif etype is EventType.MESSAGE_RECEIVED:
                    try:
                        self.mud.players[pid].command(content)
                    except Exception:
                        logging.error(traceback.format_exc())

                elif etype is EventType.PLAYER_DISCONNECT:
                    # logging data of the player
                    logging.info("%s left" % pid)
                    try:
                        character = self.mud.players[pid]
                        self.mud.send_message_to_all(f"{character} quit the game")
                        del self.mud.players[pid]
                    except KeyError:
                        pass

            # temporary: move this to a better place later
            for socket, character in self.mud.players.items():
                for msg in character.msgs:
                    self.mud.send_message(socket, msg)
                character.msgs.clear()
        # Shut down the mud instance after the while loop finishes
        self.mud.shutdown()

parser = argparse.ArgumentParser(description="Launch a MuddySwamp server.")
parser.add_argument("-p", "--port", type=int,
                    help="Specify a port. [Default: 1234]", default=1234)
parser.add_argument("-w", "--world", metavar="FILE",
                    help="Load world from [FILE]")
parser.add_argument("--default-class", metavar="CLASS",
                    help="Force all characters to spawn as [CLASS]")
parser.add_argument("--default-location", metavar="LOCATION",
                    help="Force all new characters to spawn at [LOCATION].\
                          Overrides any default class spawn locations.")

if __name__ == "__main__":
    args = parser.parse_args()
    if args.world:
        world = mudworld.World.from_file(args.world)
    else:
        # if no world file is provided, run a test world
        world = mudworld.World.test_world()
    try:
        server = MainServer(world, args.port)
    except PermissionError:
        print(f"Error. Do not have permission to use port '{args.port}'",
              file=sys.stderr)
        exit(-1)
    except OSError as ex:
        if ex.errno == errno.EADDRINUSE:
            print(f"Error. Port '{args.port}' is already in use.",
                  file=sys.stderr)
        else:
            print(ex, file=sys.stderr)
        exit(-1)

    # export server to enable mudscript
    mudscript.export_server(server)

    # set the default values if provided
    if args.default_class:
        try:
            server.default_class = \
                server.world.char_classes[args.default_class]
        except KeyError:
            print("Error setting default class.\n"
                  f"Cannot find class '{args.default_class}'",
                  file=sys.stderr)
            exit(-1)

    if args.default_location:
        try:
            server.default_location = \
                server.world.locations[args.default_location]
        except KeyError:
            print("Error setting default location.\n"
                  f"Cannot find location '{args.default_location}'",
                  file=sys.stderr)
            exit(-1)


    # Create a threadsafe queue for commands entered on the server side
    command_queue = queue.Queue()
    # Create an instance of the thread and start it
    thread = MudServerWorker(command_queue, server)
    thread.setName("MudServerThread")
    thread.start()

    # Look for input on the server and send it to the thread
    previous = ""
    while True:
        if not SHELL_MODE:
            try:
                command, params = (input("> ").split(" ", 1) + ["", ""])[:2]
                if command == "broadcast":
                    command_queue.put(ServerComand(ServerCommandEnum.BROADCAST_MESSAGE, u"\u001b[32m" + "[Server] " + params + u"\u001b[0m"))
                elif command == "players":
                    command_queue.put(ServerComand(ServerCommandEnum.GET_PLAYERS, ""))
                elif command == "stop":
                    command_queue.put(ServerComand(ServerCommandEnum.BROADCAST_MESSAGE, u"\u001b[32m" + "[Server] " + "Server shutting down..." + u"\u001b[0m"))
                    break
                elif command == "help":
                    logging.info("Server commands are: \n" \
                    " broadcast [message] - Broadcasts a message to the entire server\n"\
                    " players - Prints a list of all players\n" \
                    " stop - Stops the server\n" \
                    " list [locations|items|chars] - list all available loaded locations/items/chars\n" \
                    " shell - enter a python shell\n")
                elif command == "list":
                    if params == "locations":
                        location_list = "Loaded Locations:\n"
                        for loc in server.world.locations.values():
                            location_list += "\t%r\n" % loc
                        logging.info(location_list)
                    elif params == "items":
                        item_list = "Loaded Items:\n"
                        for name in server.world.item_classes.values():
                            item_list += "\t%r\n" % name
                        logging.info(item_list)
                    elif params == "chars":
                        char_list = "Loaded CharacterClasses:\n"
                        for name in server.world.char_classes.values():
                            char_list += "\t%s\n" % name
                        logging.info(char_list)
                    else:
                        logging.info("Argument not recognized. Type help for a list of commands.")
                elif command == "save":
                    if params:
                        server.world.to_file(params)
                        logging.info("Saved world to %s", params)
                    else:
                        print("Please provide a filename")
                elif command == "shell":
                    SHELL_MODE = True
                    print("Entering shell mode (press CTRL-C to exit)")
                elif command.strip() == "":
                    continue
                else:
                    logging.info("Command not recognized. Type help for a list of commands.")
                    continue
                logging.log(0, "> " + command + " " + params)
            except KeyboardInterrupt:
                logging.info("Keyboard interrupt detected. Shutting down.")
                command_queue.put(ServerComand(ServerCommandEnum.BROADCAST_MESSAGE, u"\u001b[32m" + "[Server] " + "Server shutting down..." + u"\u001b[0m"))
                break
            except EOFError:
                logging.info("EOF character detected. Shutting down.")
                command_queue.put(ServerComand(ServerCommandEnum.BROADCAST_MESSAGE, u"\u001b[32m" + "[Server] " + "Server shutting down..." + u"\u001b[0m"))
                break
        else:
            try_exec = False
            # try to eval the output first
            try:
                inp =  input(">>> ")
                result = eval(inp)
                # show a representation of the input on the screen
                if result is not None:
                    print(repr(result))
            # leave the shell if ^C is pressed during input
            except KeyboardInterrupt:
                print("\nLeaving shell mode...")
                SHELL_MODE = False
            # if ^D is pressed, we exit the entire server
            except EOFError:
                logging.info("EOF character detected. Shutting down.")
                command_queue.put(ServerComand(ServerCommandEnum.BROADCAST_MESSAGE, u"\u001b[32m" + "[Server] " + "Server shutting down..." + u"\u001b[0m"))
                break
            except SyntaxError:
                # if there was a syntax error, give exec a shot
                try_exec = True
            except Exception:
                # print any exceptions
                print(traceback.format_exc())
            if try_exec:
                try:
                    exec(inp)
                except Exception:
                    # print any exceptions
                    print(traceback.format_exc())

    # Shut down the server gracefully
    logging.info("Shutting down server")
    thread.shutdown()
    thread.join()
    logging.info("Server shutdown. Good bye!!")
