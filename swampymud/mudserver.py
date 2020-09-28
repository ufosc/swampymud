"""
Basic MUD server module for creating text-based Multi-User Dungeon
(MUD) games.

This module provides one class, MudServer, which represents
the game instance, tracks players, and handles interactions with
TcpClients and websockets.

This module and the MudServer claass was originally written by Mark
Frimston (mfrimston@gmail.com). We based MuddySwamp on Mark's code for
over 2 years, before ultimately replacing it with an asynchronous server
that would work better with the websockets package. Without Mark's
original module, this project would have never gotten off the ground.
Thank you, Mark.
"""
import logging
import traceback
from collections import namedtuple
# for asynchronous stuff
import asyncio
# required for WebsocketServer


TcpCient = namedtuple("TcpClient", ["pid", "reader", "writer"])


class MudServer:
    '''A high-level game server that coordinates between a TelnetServer
    instance and the in-game world.

    Generally speaking, you should initialize this object, not a telnet
    server.
    '''

    # TODO: handle websocket / telnet server ports
    def __init__(self, world, port):
        logging.info("Setting up server on port [%d]", port)
        self.world = world
        self.default_class = None
        self.default_location = None
        self.port = port

        self.players = {} # dict mapping server-socket IDs to characters
        self._tcp_clients = {} # dict mapping pids to TcpClients
        self.next_id = 0
        self._running = False

    async def run(self):
        """Begin this MudServer.
        This method is asynchronous, so it must be called in the context
        of an event loop, perhaps like this:
            asyncio.get_event_loop().run_until_complete(my_mud.run())
        """
        logging.info("Starting server...")
        # First, check to make sure the same server instance isn't being
        # run multiple times.
        if self._running:
            raise RuntimeError(f"server {self!r} is already running")

        # Flag the server as running
        self._running = True
        self.tcp_server = await asyncio.start_server(self._register_tcp,
                                                     port=self.port)
        await self.tcp_server.serve_forever()

        # TODO: add websockets!

    def shutdown(self):
        """Shut down the """
        try:
            self.tcp_server.shutdown()
        except AttributeError:
            pass
        #TODO: kill the websocket server
        self._running = False

    # Callback method for the TCP Server.
    # This method is executed whenever a new client connects to the
    # TCP server.
    async def _register_tcp(self, reader, writer):
        """Register a new TCP client with this server.
        This internal method is sent to asyncio.start_server().
        See https://docs.python.org/3/library/asyncio-stream.html to
        get a better idea of what's going on here.
        """
        # First, grab a new unique identifier.
        pid = self.next_id
        self.next_id += 1

        # Now, create a tcp client and add it to the collection
        self._tcp_clients[pid] = TcpCient(pid, reader, writer)

        # This method will create a new Character and assign it to the
        # player.
        # This method can be overriden for custom behavior.
        self.on_player_join(pid)

        # Now we create two coroutines, one for handling incoming messages,
        # and one for handling outgoing messages.

        # If a player disconnects, the _incoming_tcp coroutine will wake up,
        # and run to completion. However, the _outgoing_tcp coroutine
        # will be stuck waiting until the player's Character receives a
        # message.
        # We want to move on immediately when the player disconnects, so
        # we return_when=asyncio.FIRST_COMPLETED here.
        await asyncio.wait([self._incoming_tcp(pid), self._outgoing_tcp(pid)],
                           return_when=asyncio.FIRST_COMPLETED)


        # If the interpreter reaches this line, that means an EOF has
        # been detected and this player has disconnected.
        # Close the StreamWriter.
        writer.close()
        # Remove the client from the list of TCP clients.
        del self._tcp_clients[pid]

        # Finally, call server.on_player_quit().
        # By default, this will delete the player's Character and send a
        # message to the other players, letting them know that this
        # player left.
        # This method can be overriden for custom behavior.
        self.on_player_quit(pid)

    async def _incoming_tcp(self, pid):
        """Handle incoming messages from a Tcp Client."""
        (_, reader, _) = self._tcp_clients[pid]
        # When the user disconnects, asyncio will call it "EOF" (end of
        # file). Until then, we simply try to read a line from the
        # user.
        while not reader.at_eof():
            # reader.readline() is an asynchronous method
            # This means that it won't actually execute on its own
            # unless we 'await' it.
            # Under the hood, using this 'await' actually switches to
            # execute some other code until this player sends us
            # a message.
            msg = await reader.readline()

            # The player just sent us a message!
            # Remove any whitespace and convert from bytes to str
            msg = msg.strip().decode(encoding="latin1")

            if msg:
                # Pass the message to server.on_player_msg().
                # The method there will send the message to the
                # Character that the player controls.
                # This function can be overriden for custom behavior.
                self.on_player_msg(pid, msg)

        logging.debug("_incoming_tcp closed for %s", pid)

    async def _outgoing_tcp(self, pid):
        """Handles outgoing messages, that is, messages sent to a Character
        that must be forwarded to a Player.
        """
        (_, reader, writer) = self._tcp_clients[pid]
        character = self.players[pid]

        # As with MudServer._incoming_tcp, we use reader.at_eof() to
        # determine when the player has disconnected.
        while not reader.at_eof():
            # Try to get a message from the Character's queue.
            # This will block until the character receives a message.
            msg = await character.msgs.get()

            # TODO: try to get more messages to buffer writes?

            # Add a newline character and convert the message into bytes
            msg = (msg + "\n\r").encode('latin-1')
            writer.write(msg)

            # Once we've written to a StreamWriter, we have to call
            # writer.drain(), which blocks.
            try:
                await writer.drain()
            # If the player disconnected, we will get an error.
            # We will break and finish the coroutine.
            except ConnectionResetError:
                break

        logging.debug("_outgoing_tcp closed for %s", pid)

    # handlers for each event
    # override these for custom behavior
    def on_player_join(self, pid):
        """This method is executed whenever a new player [pid] joins the
        server. By default, the player is assigned a new Character,
        which is then spawned in the game world.

        You can override this method to trigger custom behavior every
        time a player joins.
        """
        logging.info("%s joined.", pid)

        # first, look if this server has a default class established
        # if not, pick a random class stored in the World personae
        if self.default_class is not None:
            PlayerCls = self.default_class
        else:
            PlayerCls = self.world.random_cls()

        # initialize the Character and add it to the server
        character = PlayerCls()
        self.players[pid] = character

        # now prepare a location for the player
        # as with default_class, a server-wide default_location takes
        # precedence
        if self.default_location is not None:
            start_loc = self.default_location
        elif PlayerCls.starting_location is not None:
            start_loc = PlayerCls.starting_location
        # if no default location has been defined for CharacterClass or
        # server, resort to picking the first location in locations
        else:
            try:
                start_loc = next(iter(self.world.locations.values()))
            except StopIteration:
                logging.critical("Could not spawn %d, "
                                 "world has no locations", pid)
                return
            logging.warning("%s has no default location, "
                            "so %d will be spawned in %s",
                            PlayerCls, pid, start_loc)

        # put the character in "greet" mode
        character.spawn(start_loc)

    def on_player_msg(self, pid: int, msg: str):
        """This method is executed whenever a string of data [msg]
        is received from the TcpClient / WebSocket associated with
        [pid]. This method simply passes the msg onto the Character
        controlled by the player.

        You can override this method to trigger custom behavior every
        time a player sends a message to the server.
        """
        logging.info("%s says: [%s]", pid, msg)
        try:
            # Simply look up the character that belongs to this player,
            # and send the msg as a command.
            self.players[pid].command(msg)

        # Now that we're triggering game code, a lot of errors could
        # occur. We're going to just log those and keep moving, so
        # that the server doesn't completely die.
        except Exception:
            logging.error(traceback.format_exc())

    def on_player_quit(self, pid):
        """This method is executed whenever a player [pid] disconnects
        from the server server. By default, the player's Character is
        destroyed and the other players are notified.

        You can override this method to trigger custom behavior every
        time a player quits.
        """
        logging.info("%s quit.", pid)

        try:
            character = self.players[pid]
        except KeyError:
            # player did not exist
            return

        # only send a message if character had provided a name
        if str(character) != "[nameless character]":
            self.send_message_to_all(f"{character} quit the game.")

    # methods used in mudscript
    def send_message_to_all(self, message):
        """Sends the text in the 'message' parameter to every player that
        is connected to the server.
        """
        # We copy the _clients into a list to avoid dictionary changing
        # size during iteration.
        for character in self.players.values():
            character.message(message)
