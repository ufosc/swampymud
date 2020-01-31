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
from mudserver import MudServer, Event, EventType
# import modules from the MuddySwamp engine
import mudworld
import mudscript
import control

# better names welcome
class MainServer(MudServer):
    '''Bundles a server and a library together'''
    def __init__(self, world, port):
        self.world = world
        self.default_class = None
        self.default_location = None
        super().__init__(port)

    def set_default_class(self, cls_name):
        '''set default class to class with name [default_name]
        throws an error if default_name is not found in server's lib'''
        self.default_class = server.world.char_classes[cls_name]

    def set_default_location(self, loc_name):
        '''set default class to class with name [default_name]
        throws an error if default_name is not found in server's lib'''
        self.default_location = server.world.locations[loc_name]

    def clear_default_class(self):
        '''clear the provided default class'''
        self.default_class = None

    def clear_default_location(self):
        '''clear the provided default location'''
        self.default_location = None

    def get_player_class(self):
        '''get a player class from the server'''
        if self.default_class is not None:
            return self.default_class
        else:
            return self.world.random_cls()


class Greeter(control.Monoreceiver):
    '''Class responsible for greeting the player
    and handing them a Character to control'''

    GREETING = '''Welcome to MuddySwamp!'''

    def __init__(self, server):
        self.server = server
        self.player_cls = server.get_player_class()
        super().__init__()

    def attach(self, controller):
        '''attach to [controller], greeting it as appropriate'''
        super().attach(controller)
        self.controller.write_msg(self.GREETING)
        self.controller.write_msg("You are a(n) %s" % self.player_cls)
        self.controller.write_msg("What is your name?")


    def update(self):
        while self.controller.has_cmd():
            new_name = self.controller.read_cmd().strip()
            if new_name == "":
                continue
            if not new_name.isalnum():
                self.controller.write_msg("Names must be alphanumeric.")
                continue
            # TODO: perform check to prevent users from having the same name
            else:
                # first, find the location we are putting them in
                if self.server.default_location is not None:
                    loc = self.server.default_location
                elif self.player_cls.starting_location is not None:
                    loc = self.player_cls.starting_location
                else:
                    try:
                        loc = next(iter(self.server.world.locations.values()))
                    except StopIteration:
                        logging.critical("Could not spawn %s, server has no locations", new_name)
                        continue
                    logging.warning("%s has no default location, "
                                    "so %s will be spawned in %s",
                                    self.player_cls, new_name, loc)

                # create the character and give it to the player
                new_char = self.player_cls(new_name)
                self.controller.assume_control(new_char)
                # put new character in location
                new_char.set_location(loc)
                self.server.send_message_to_all(f"Welcome, {new_char}, to the server!")
                break


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
                        for player in control.Player.player_ids.values():
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
                id = event.id
                if event.type is EventType.PLAYER_JOIN:
                    logging.info("Player %s joined." % event.id)
                    # create a controller (a 'Player')
                    new_player = control.Player(event.id)

                    # give player a greeter
                    new_player.assume_control(Greeter(self.mud))

                elif event.type is EventType.MESSAGE_RECEIVED:
                    # log the message
                    logging.debug("Event message: " + event.message)
                    try:
                        control.Player.send_command(id, event.message)
                    except Exception:
                        logging.error(traceback.format_exc())

                elif event.type is EventType.PLAYER_DISCONNECT:
                    # logging data of the player
                    player = control.Player.player_ids[id]
                    logging.info("%s left" % player)
                    if player.receiver is not None:
                        pass
                        #self.mud.send_message_to_all("%s quit the game" % player.receiver)
                    control.Player.remove_player(id)

            # temporary: move this to a better place later
            for id, msg in control.Player.receive_messages():
                self.mud.send_message(id, msg)
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

    # set the default class if one was provided
    if args.default_class:
        try:
            server.set_default_class(args.default_class)
        except KeyError:
            print("Error setting default class.\n"
                  f"Cannot find class '{args.default_class}'",
                  file=sys.stderr)
            exit(-1)

    if args.default_location:
        try:
            server.set_default_location(args.default_location)
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
