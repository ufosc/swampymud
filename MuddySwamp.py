#!/usr/bin/env python3
'''main script for MuddySwamp'''
import sys
import logging
import threading
import queue
import enum
import traceback
import errno
# import the MUD server class
from mudserver import MudServer, Event, EventType
# import modules from the MuddySwamp engine
import mudimport
from glob import glob
import mudscript
import control

# better names welcome
class MainServer(MudServer):
    '''Bundles a server and a library together'''
    def __init__(self, port=1234):
        self.lib = mudimport.Library()
        super().__init__(port)


# Setup the logger
logging.basicConfig(format='%(asctime)s [%(threadName)s] [%(levelname)s] %(message)s',
                    level=logging.INFO,
                    handlers=[
                        logging.FileHandler("server.log"),
                        logging.StreamHandler(sys.stdout)
                    ])


# defining a set of paths
# by default, we import every json in chars and locations
IMPORT_PATHS = {
    "locations" : glob("locations/*.json"),
    "chars" : glob("chars/*json"),
    "items" : glob("items/*json")
}

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
        mudscript.export_server(self.mud)
        self.mud.lib.import_files(**IMPORT_PATHS)
        logging.info(self.mud.lib.import_results())
        self.mud.lib.build_class_distr()
        super().__init__(*args, **kwargs)
        

    # Cannot call mud.shutdown() here because it will try to call the sockets in run on the final go through
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
            while (len(self.mud.server_queue) > 0):
                event = self.mud.server_queue.popleft()
                logging.info(event)
                id = event.id
                if event.type is EventType.PLAYER_JOIN:
                    logging.info("Player %s joined." % event.id)
                    if SHELL_MODE:
                        print(">>> ")
                    # notifying the player of their class, creating the character
                    self.mud.send_message(id, "Welcome to MuddySwamp!")
                    PlayerClass = self.mud.lib.random_class.get()
                    self.mud.send_message(id, "You are a(n) %s" % PlayerClass)
                    self.mud.send_message(id, "What is your name?")
                    # creating a controler (a 'Player'), then giving that Player control of a new character
                    # of whatever class the player is
                    new_player = control.Player(event.id)
                    new_character = PlayerClass()
                    new_player.assume_control(new_character)

                elif event.type is EventType.MESSAGE_RECEIVED:
                    # log the message
                    logging.debug("Event message: " + event.message)
                    if SHELL_MODE:
                        print(">>> ")
                    try:
                        control.Player.send_command(id, event.message)
                    except Exception:
                        logging.error(traceback.format_exc())

                elif event.type is EventType.PLAYER_DISCONNECT:
                    # logging data of the player
                    player = control.Player.player_ids[id]
                    logging.info("%s left" % player)
                    if SHELL_MODE:
                        print(">>> ")
                    if player.receiver is not None:
                        pass
                        #self.mud.send_message_to_all("%s quit the game" % player.receiver)
                    control.Player.remove_player(id)

            # temporary: move this to a better place later
            for id, msg in control.Player.receive_messages():
                self.mud.send_message(id, msg)

        # Shut down the mud instance after the while loop finishes
        self.mud.shutdown()

if __name__ == "__main__":
    # parse arguments for port number
    # if we get more complex, we will need an argparser
    port = 1234
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Error. Port must be an integer.", file=sys.stderr)
            exit(-1)
    try:
        server = MainServer(port)
    except PermissionError:
        print("Error. Do not have permission to use port '%s'" % port, file=sys.stderr)
        exit(-1)
    except OSError as ex:
        if ex.errno == errno.EADDRINUSE:
            print("Error. Port '%s' is already in use." % port, file=sys.stderr)
        else:
            print(ex, file=sys.stderr)
        exit(-1)


    # Create a threadsafe queue for commands entered on the server side
    command_queue = queue.Queue()
    # Create an instance of the thread and start it
    thread = MudServerWorker(command_queue, server)
    thread.setName("MudServerThread")
    thread.start()

    # Look for input on the server and send it to the thread
    while True:
        if not SHELL_MODE:
            try:
                command, params = (input("").split(" ", 1) + ["", ""])[:2]
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
                        for name, ref in self.mud.lib.locations.items():
                            location_list += "Name: %s\n" \
                            "Object:\n%s\n" % (name, repr(ref))
                        logging.info(location_list)
                    elif params == "items":
                        pass
                    elif params == "chars":
                        pass
                    else:
                        logging.info("Argument not recognized. Type help for a list of commands.")
                elif command == "shell":
                    SHELL_MODE = True
                    print("Entering shell mode (press CTRL-C to exit)")
                else:
                    logging.info("Command not recognized. Type help for a list of commands.")
            except KeyboardInterrupt:
                logging.info("Keyboard interrupt detected. Shutting down.")
                command_queue.put(ServerComand(ServerCommandEnum.BROADCAST_MESSAGE, u"\u001b[32m" + "[Server] " + "Server shutting down..." + u"\u001b[0m"))
                break
            except EOFError:
                logging.info("EOF character detected. Shutting down.")
                command_queue.put(ServerComand(ServerCommandEnum.BROADCAST_MESSAGE, u"\u001b[32m" + "[Server] " + "Server shutting down..." + u"\u001b[0m"))
        else:
            try:
                inp = input(">>> ")
                result = eval(inp)
                if result is not None:
                    print(repr(result))
            except KeyboardInterrupt:
                print("\nLeaving shell mode...")
                SHELL_MODE = False
            except SyntaxError:
                try:
                    exec(inp)
                except:
                    print(traceback.format_exc())
            except Exception:
                print(traceback.format_exc())



    # Shut down the server gracefully
    logging.info("Shutting down server")
    thread.shutdown()
    thread.join()
    logging.info("Server shutdown. Good bye!!")
