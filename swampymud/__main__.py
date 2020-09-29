#!/usr/bin/env python3
'''main script for creating swampy MUDs'''
import sys
import logging
import errno
import argparse
import warnings
# import the MUD server class
from swampymud.mudserver import MudServer
# import modules from the SwampyMud engine
from swampymud.world import World
from swampymud import mudscript
# import asyncio to use its event loop
import asyncio

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


parser = argparse.ArgumentParser(description="Launch a swampy Multi-User Dungeon.")
parser.add_argument("--ws", type=int, metavar="PORT", default=1234,
                    help="Specify a port for a WebSocket Server. [Default: 1234]")
parser.add_argument("--tcp", type=int, metavar="PORT",
                    help="Specify a port for a TCP Server. "
                    "(If no port is provided, no TCP Server will be created.)")
parser.add_argument("--tcp-only", action="store_true",
                    help="Only launch a TCP Server, not a WebSocketServer. "
                    "(Ignores any values provided with -p or --ws.)")
parser.add_argument("-w", "--world", metavar="FILE",
                    help="Load world from [FILE]")
# TODO: add log level to the parser
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
        ws_port = args.ws
        tcp_port = args.tcp
        if args.tcp_only:
            ws_port = None
            # edge case: --tcp-only was provided without a tcp_port
            if tcp_port is None:
                print("Error: --tcp-only flag was provided without providing "
                      "a TCP port.\nI can't launch a TCP server if you don't"
                      "give me a port!\n(Hint: try providing a port with --tcp.)",
                      file=sys.stderr)
                exit(-1)

            logging.info("Launching a TCP Server on port '%d'", tcp_port)
        elif tcp_port is None:
            logging.info("Launching a WebSocket Server on port '%d'", ws_port)
        # both TCP and WS ports were provided
        else:
            # edge case: ports provided are the same
            if ws_port == tcp_port:
                print("Error: TCP Server and WebSocket server cannot use the "
                      f"same port '{ws_port}'. Provide different ports.",
                      file=sys.stderr)
                # user may have just forgotten to provide tcp port
                if ws_port == 1234:
                    print("(Hint: If you're trying to ONLY run a TCP server, "
                          "provide the --tcp-only flag.)", file=sys.stderr)
                exit(-1)
            logging.info("Launching a WebSocket Server on port '%d' and a "
                         "TCP Server on port '%d'", ws_port, tcp_port)
    try:
        server = MudServer(world, ws_port, tcp_port)
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

    try:
        asyncio.get_event_loop().run_until_complete(server.run())
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt detected")
        server.shutdown()
    # Shut down the server gracefully
    logging.info("Shutting down server")
    logging.info("Server shutdown. Good bye!!")
