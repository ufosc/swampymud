#!/usr/bin/env python3
'''main script for creating swampy MUDs'''
import sys
import logging
import threading
import queue
import traceback
import errno
import argparse
import warnings
# import the MUD server class
from swampymud.mudserver import MudServer
# import modules from the SwampyMud engine
from swampymud.world import World
from swampymud import mudscript


# Setup the logger
logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',
                    level=logging.INFO,
                    handlers=[
                        logging.FileHandler("server.log"),
                        logging.StreamHandler(sys.stdout)
                    ])

# Redirect warnings to the logger
logging.captureWarnings(True)
warnings.simplefilter('always')

SHELL_MODE = False

class MudServerWorker(threading.Thread):
    def __init__(self, q, server, *args, **kwargs):
        self.keep_running = True
        self.q = q
        self.server = server
        super().__init__(*args, **kwargs)

    # Cannot call mud.shutdown() here because it will try to call
    # the sockets in run on the final go through
    def shutdown(self):
        self.keep_running = False

    def run(self):
        logging.info("Server started successfully.")
        # main game loop. We loop forever (i.e. until the program is terminated)
        while self.keep_running:
            self.server.update()
        self.server.shutdown()

parser = argparse.ArgumentParser(description="Launch a swampy Multi-User Dungeon.")
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
        # load the world file, catch any warnings and manually log them
        # to make the output less ugly
        with warnings.catch_warnings(record=True) as warn_list:
            world = World.from_file(args.world)
        for warn in warn_list:
            logging.warning(str(warn.message))
    else:
        # if no world file is provided, run a test world
        world = World.test_world()
    try:
        server = MudServer(world, args.port)
        logging.info(f"Starting server on port [{args.port}]")
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
