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
import warnings
from swampymud.util.biject import Biject
# for asynchronous stuff
import asyncio
# required for websockets to work
import websockets


class MudServer:
    '''A high-level game server that coordinates between a TelnetServer
    instance and the in-game world.

    Generally speaking, you should initialize this object, not a telnet
    server.
    '''

    def __init__(self, world, ws_port=None, tcp_port=None):
        logging.debug("Server %r created", self)
        # game-related data
        self.world = world
        self.default_class = None
        self.default_location = None
        # dict mapping pid [int] to in-game Characters
        # use a biject here so we can get Characters back if needed
        self.players = Biject()

        self.tcp_port = tcp_port
        self.tcp_server = None
        self._tcp_clients = {}
        self.ws_port = ws_port
        self.ws_server = None
        self._ws_clients = {}
        # by tracking clients, we can write a 'kick' function and
        # have a cleaner shutdown (in the case of the tcp server)

        self.next_id = 0
        self._running = False
        # at least one port must be provided
        if tcp_port is None and ws_port is None:
            raise ValueError("Cannot create MudServer without at least one "
                             "TCP or WS port.")

    async def run(self):
        """Begin this MudServer.
        This method is asynchronous, so it must be called in the context
        of an event loop, perhaps like this:
            asyncio.get_event_loop().run_until_complete(my_mud.run())
        """
        logging.debug("Starting server...")
        # First, check to make sure the same server instance isn't being
        # run multiple times.
        if self._running:
            raise RuntimeError(f"server {self!r} is already running")

        # Flag the server as running
        self._running = True

        # We create a list of coroutines, since we might be running more
        # than just one if we have a TCP Server AND a WebSocketServer.
        coroutines = []

        if self.tcp_port is not None:
            # start asyncio.Server
            self.tcp_server = await asyncio.start_server(self._register_tcp,
                                                         port=self.tcp_port)
            # add it to the list of coroutines
            coroutines.append(self.tcp_server.serve_forever())

        if self.ws_port is not None:
            # start a WebSocketServer
            self.ws_server = await websockets.serve(self._register_ws,
                                                    port=self.ws_port)
            # use a simple coro so that MudServer doesn't close
            # with WebSocketServer still running
            coroutines.append(self.ws_server.wait_closed())

        # We use asyncio.gather() to execute multiple coroutines.
        await asyncio.gather(*coroutines, return_exceptions=True)

    def shutdown(self):
        """Shut down this server and disconnect all clients. (Both TCP
        and WebSocket clients are disconnected.)
        """
        if self.tcp_server is not None:
            self.tcp_server.close()
            # asyncio.Server doesn't automatically close existing
            # sockets, so we manually close them all now
            for stream_writer in self._tcp_clients.values():
                stream_writer.close()
        if self.ws_server is not None:
            self.ws_server.close()
        self._running = False

    # Callback methods for the TCP Server.
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

        # Now, store the tcp client in a dictionary, so we can track it
        # down later if necessary.
        self._tcp_clients[pid] = writer

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
        await asyncio.wait([self._incoming_tcp(pid, reader),
                            self._outgoing_tcp(pid, writer)],
                           return_when=asyncio.FIRST_COMPLETED)


        # If the interpreter reaches this line, that means an EOF has
        # been detected and this player has disconnected.
        # Close the StreamWriter.
        writer.close()
        del self._tcp_clients[pid]

        # Finally, call server.on_player_quit().
        # By default, this will delete the player's Character and send a
        # message to the other players, letting them know that this
        # player left.
        # This method can be overriden for custom behavior.
        self.on_player_quit(pid)

    async def _incoming_tcp(self, pid, reader):
        """Handle incoming messages from a Tcp Client."""

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

    async def _outgoing_tcp(self, pid, writer):
        """Handles outgoing messages, that is, messages sent to a Character
        that must be forwarded to a Player.
        """
        character = self.players[pid]

        # This coroutine just loops forever, and will eventually be
        # broken once the client disconnects.
        while True:
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

    # Callback methods for new WebSocket connections.
    # This method is executed whenever a new WebSocket connects to the
    # WebSocketServer.
    async def _register_ws(self, websocket, path):
        # we don't currently do anything with the path, so just log it
        logging.debug("WebSocket %s connected at path %s", websocket, path)

        # First, grab a new unique identifier.
        pid = self.next_id
        self.next_id += 1

        # Now, store the websocket in a dictionary, so we can track it
        # down later if necessary.
        self._ws_clients[pid] = websocket

        # Call the server's custom handler. (By default, this will
        # create a new Character and assign it to the player.)
        self.on_player_join(pid)

        # WebSockets have a slightly different API than the tcp streams
        # rather than a reading and writing stream, which just have
        # one socket.
        # As with _register_tcp, we want to quit immediately the player
        # disconnects, so we use return_when=asyncio.FIRST_COMPLETED
        await asyncio.wait([self._incoming_ws(pid, websocket),
                            self._outgoing_ws(pid, websocket)],
                           return_when=asyncio.FIRST_COMPLETED)

        # If this code is reached, then the WebSocket has disconnected.
        # This should already be closed, but just in case.
        await websocket.close()

        # Delete the pid / websocket from the clients.
        del self._ws_clients[pid]
        # (We still keep track of pid in self._players... just in case.)

        # Call the server's event handler. (By default, this will simply
        # notify the other players.)
        self.on_player_quit(pid)

    async def _incoming_ws(self, pid, websocket):
        """Handle incoming messages from a Tcp Client."""
        # websockets have a convenient __aiter__ interface, allowing
        # us to just iterate over the messages forever.
        # Under the hood, if there are no messages available from the
        # WebSocket, this code will yield and until another message is
        # received.

        # If the WebSocket is disconnected unexpectedly, the for loop
        # will produce an exception.
        try:
            async for msg in websocket:
                # Trim whitespace
                msg = msg.strip()
                # Make sure the message isn't an empty string
                if msg:
                    # Pass the message onto the server's handler.
                    self.on_player_msg(pid, msg)
        # If we get this error, then player probably just logged off.
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            logging.debug("_incoming_ws closed for %s", pid)

    async def _outgoing_ws(self, pid, websocket):
        """Handles outgoing messages, that is, messages sent to a Character
        that must be forwarded to a Player.
        """
        character = self.players[pid]

        while not websocket.closed:
            msg = await character.msgs.get()

            # TODO: try to get more messages and buffer writes?
            try:
                await websocket.send(msg + "\n\r")
            except websockets.exceptions.ConnectionClosed:
                break

        logging.debug("_outgoing_ws closed for %s", pid)

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
            self.message_all(f"{character} quit the game.")

    # methods used in mudscript
    def message_all(self, message):
        """Sends the text in the 'message' parameter to every player that
        is connected to the server.
        """
        # We copy the _clients into a list to avoid dictionary changing
        # size during iteration.
        for (_pid, character) in self.players:
            character.message(message)

    def kick(self, character, reason: str=""):
        """Find the client associated with [character] and disconnect
        them from the game.
        Raises KeyError if [character] cannot be found.
        """
        # get the pid from the player biject
        # (raises KeyError if character not found)
        pid = self.players[character]

        try:
            tcp_stream_writer = self._tcp_clients[pid]
            kick_coro = tcp_stream_writer.close()
        # pid is not in tcp_clients, maybe it's a websocket?
        except KeyError:
            try:
                websocket = self._ws_clients[pid]
                kick_coro = websocket.close()
            except KeyError:
                logging.error("Could not kick pid '%s' "
                              "(are they already disconnected?)", pid)
                return

        character.message("You are being kicked from the server.")
        if reason:
            character.message(f"(Reason: {reason})")
        try:
            # turn the coroutine into a task to schedule it
            asyncio.create_task(kick_coro)
        # loop is not running right now
        except RuntimeError:
            if self._running:
                logging.error("Could not kick pid '%s' (Maybe MudServer.run() "
                              "was called but never awaited?)", pid)
            else:
                logging.error("Could not kick pid '%s' "
                              "(server is not running)", pid)
            return
        if reason:
            logging.info("Kicked pid '%s' associated with [%s] "
                         "(Reason: %s)", pid, character, reason)
        else:
            logging.info("Kicked pid '%s' associated with [%s]",
                         pid, character)
