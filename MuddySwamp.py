#!/usr/bin/env python3
'''main script for MuddySwamp'''
import sys
import logging
import threading
import queue
import enum
import mudimport
import library
# import the MUD server class
from mudserver import MudServer, Event, EventType
from location import Location, Exit
import control
import traceback


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
    "locations" : mudimport.get_filenames("./locations/", ".json"),
    "chars" : mudimport.get_filenames("./chars/", ".json"),
    "items" : mudimport.get_filenames("./items/", ".json")
}

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
    def __init__(self, q, *args, **kwargs):
        self.keep_running = True
        self.q = q
        mudimport.import_files(**IMPORT_PATHS)
        library.build_char_class_distr()
        super().__init__(*args, **kwargs)

    # Cannot call mud.shutdown() here because it will try to call the sockets in run on the final go through
    def shutdown(self):
        self.keep_running = False

    def run(self):
        logging.info("Starting server.")
        self.mud = MudServer()
        library.store_server(self.mud)
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
                    # notifying the player of their class, creating the character
                    self.mud.send_message(id, "Welcome to MuddySwamp!")
                    PlayerClass = library.random_class.get()
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

# Create a threadsafe queue for commands entered on the server side
command_queue = queue.Queue()
# Create an instance of the thread and start it
thread = MudServerWorker(command_queue)
thread.setName("MudServerThread")
thread.start()

# Look for input on the server and send it to the thread
while True:
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
            " list [locations|items|chars|] - list all available loaded locations/items/chars\n")
        elif command == "list":
            if params == "locations":
                location_list = "Loaded Locations:\n"
                for name, ref in library.locations.items():
                    location_list += "Name: %s\n" \
                    "Object:\n%s\n" % (name, repr(ref))
                logging.info(location_list)
            elif params == "items":
                pass
            elif params == "chars":
                pass
            else:
                logging.info("Argument not recognized. Type help for a list of commands.")
        else:
            logging.info("Command not recognized. Type help for a list of commands.")
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt detected. Shutting down.")
        command_queue.put(ServerComand(ServerCommandEnum.BROADCAST_MESSAGE, u"\u001b[32m" + "[Server] " + "Server shutting down..." + u"\u001b[0m"))
        break


# Shut down the server gracefully
logging.info("Shutting down server")
thread.shutdown()
thread.join()
logging.info("Server shutdown. Good bye!!")
