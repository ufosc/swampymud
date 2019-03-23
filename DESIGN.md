# MuddySwamp Design

As wonderful as it may be, Python is incredibly slow.
So that we may justify using this language, we attend to use Python's more dynamic features as much as possible. 
Therefore, we create metaclasses and manipulate functions at runtime. 
We use duck typing so we don't have to write out long if-else statements. 
These features are available to us, and we believe we should use them.

Characters in this engine have an extremely strong sense of class. 
A character's class dictates precisely what commands they could use.
**CharacterClasses** also affect items, access to locations, and other abiltiies.
Class pervades everything in the MuddySwamp engine.

Accordingly, we made creating ChararacterClasses as made as easy as possible for developers.
[CONTRIBUTING.md](CONTRIBUTING.md) has a detailed section on creating a new **CharacterClass**.

Beyond CharacterClasses, the MuddySwamp engine is quite simple. 
The world is divided into pieces, called rooms **locations**.
**Locations** contain a description, list of characters in that location, an inventory of **items**, and a set of **entities**. 

**Locations** are connected by **exits**. 
**Exits** are one way be default, and they can be restricted to certain **CharacterClasses** and players if desired.

**Items** are objects that can be stored in an inventory and can be picked up, managed, and used by players.
The MuddySwamp engine is pretty unopinionated about what items are, so you can put whatever functionality you want into an item.
You can add class restrictions to items if desired. 
(In fact, you will be able to separately restrict visibility, posession, and usage.)

**Entities** (not yet implemented) can be placed inside locations and be interacted with.
Like **Items**, **Entities** can be used for many different purposes.
A Sphinx that gives potions if you answer its riddles?
A frog that teleports people five minutes after they enter a room?
Why not? 
s with **Locations** and **Items**, entity visibility and usage can be restricted by class.

Perhaps best of all, the elements of the world--**Locations**, **Exits**, **Items**, and **Entities**--can be created dynamically.
(Thank you Python!)
We encourage users of engine to allow unlimited creation at runtime.
Our game, `MuddySwamp` aims to have spell creation, crafting, location building, and exit building-all for players to explore.

## From the Player's Side

When the player logs in, they will receive a message akin to this:
```
Welcome to MuddySwamp!
You are a(n): Wizard

What is your name?
>>>
```
At this point, the player will now enter a valid name.
```
>>> Bill
Announcement: Welcome to the server, Bill the Wizard!
```
That announcement will be sent to all players.

Now, the player is free to explore. At any time, they can view available abilities like so:
```
>>> help

Type "help [command]" for specific information.
Commands available:
[STANDARD COMMANDS]
help  say  tell  walk  report
[WIZARD COMMANDS]
cast  enchant  brew

>>> help report

usage: report [player name] [optional reason]
Report [player name] for violating server rules. 
Reports will be sent to the server logs for later review.
False reports may result in a response, as per the policy of the server admins.

>>> help cast

usage: cast [spellname] [arguments]
Cast [spellname] with arguments. Arguments very by spell. 
```

Coming soon: what does one do once they are in the game?
 
## Components
### mudserver.py (Core Server)
  - Based on the MUD Pi code
  - Only changed as necessary
  - handles events like new players joining
  - sends / receives messages

### control.py
- defines Controller abstract class
  - the concept of a "Controller" is used to interface with different types of Controllers
  - Player, Nonplayer, etc. work as controllers
  - easily multithreaded
  - Key methods:
    - `assume_control(receiver)` take control of receiver
    - `read_cmd()` read a command from the input stream (used by receivers)
    - `write_msg(msg)` write feedback from the receiver back to the controller
    - `has_msg()` returns true if there is feedback available for the controller to read
    - `has_cmd()` returns true if there are commands available for the receiver to read
- defines the Player class
  - Players are Controllers that can be accessed by id
  - using Player.player_ids[id] allows server to grab any particular player
  - Players are used to interface with players connected
- future: Nonplayer
  - reads from file or script

### mudimport.py
  - defines the Importer class
    - an Importer imports game objects and adds them to a library
  - defines the derived LocationImporter, ItemImporter, CharacterClassImporter
    - responsible for parsing respective files
  - contains `import_files` function, which imports all files provided
  - Locations are defined in JSON files (see `./locations/template`)
  - CharacterClasses are defined by a JSON file, and implemented by some python file in `./script/` see (see `./chars/template`)
  - Items are defined by a JSON file, and implemented by some python file in `./script/` see (see `./items/template`)

### library.py
  - makes in-game objects globally available
  - key fields:
    - `locations`: dictionary of locations, indexed by location name
    - `character_classes`: dictionary of character_classes, indexed by proper name
    - `random_class`: a random distribution, use `random_class.get()` to produce a random CharacterClass with appropriate weighting
    - `server`:  stored instance of a MudServer
  - key functions:
    - `store_server(input_server)`: provide an instance of MUD server, which will be stored as `server`

### MuddySwamp.py 
  - Creates/uses an instance of MudServer
  - uses the import system to import all the files
  - begin core loop
    - while the queue is not empty, handle events (new players, incoming messages, etc.) on the queue
    - if queue is empty, sleep

### character.py
  - defines CharacterClass, the metaclass that in-game character classes
    - "Wizard" would be a CharacterClass
    - "Bill the Wizard" is a Wizard
  - defines Character, the base class for player-controlled characters
    - possesses many useful functions for working with characters
    - establishes default commands
    - developers should derive from Character to create new CharacterClasses

### location.py 
  - defines Location class
  - Each location includes
    - a name
    - a list of current players
    - list of items (coming soon)
    - list of Interactable objects (coming soon)
  - defines Exit class
    - a simple class representing an exit to some location
    - an Exit contains a destination (target location), a name, and a list of nicknames
    - Exits can also contain whitelists / blacklists that exclude / allow certain CharacterClasses
  - Essentially, on a graph of the wrold, locations are the vertices, exits are the edges

### inventory.py
  - defines the Inventory class, which holds items
  - current implementation feels clunky, any optimizations / suggestions welcome

## item.py [REWRITE IN PROGRESS]
  - base classes for items
  - `Equippable` is used for items intended to be equipped
    - To create an Equippable, derive from `EquippableBase`
    - Include a "target" `EquipTarget`, "apply" function, and "unapply" function
    - (typically) remove from inventory on equip, add to inventory on unequip
  - `EquipTarget` specifies unique targets
    - to get an equip target, use `EquipTarget(name)` (where name is a string)
    - if you try to create an `EquipTarget`, and it already exists, that `EquipTarget` will be returned... this means `EquipTargets` with the same name are equal
  - `Throwables` (better name needed) are intended to be used on other characters / in-game objects
    - include an `apply` 
    - (typically) remove from inventory after use
  - `Consumable` items include an apply method and should be discarded after yes
    - `Consumble` items should be used by the player

## Utilities

Utilties found in `./util/`

### distr.py
  - defines the RandDist class
  - RandDist creates a weighted random distribution

### stocstring.py [in progress]
  - defines the StocString class, which is a superclass of strings
    - StocStrings behave like strings, but can have different contents at different times
    - For instance, "Tim ate !{randrange(1, 10)} berrie(s)" might be evaluated to "Tim ate 2 berries" one time, or "Tim ate 7 berries" another.
    - StocStrings can be used to increase variation

### mudtest.py [coming soon]
  - provides utilities for testing game elements

## Other Directories

- `items/` - contains all Item JSON files
- `chars/` - contains all CharacterClass JSON files
- `locations/` - contains all Location JSON files
- `scripts/` - contains all game scripts


## Timeline

### Phase 1 (Really Really Minimal Viable Product) ***[Completed]***
  - "GatorChat"
  - ~~profanity filter~~ turns out this is a bad idea
    - if interested, read up on the "clbuttic mistake"
    - we have opted for a reporting system instead
  - player names
  - only one chat room

### Phase 2 (Really Minimal Viable Product) ***[Completed]***
  - introduce Locations, Location parsing
  - introudce Location-based parsing
  - introduce interactables?

### Phase 3 (True Minimal Viable Product) ***[Completed]***
  - introduce classes, command palettes vary by class
  - introduce goals
  - classes at this point should form core "Rock-Paper-Scissors" like nucleus for other classes to hook into

### Phase 4 (An Enjoyable RPG) ***[In Progress]***
- Engine goals
  - add entities
  - add an effect system
  - improve items / inventories (both in terms of game design and performance)
  - add class filters
- MuddySwamp goals
  - implement the first generation of character classes
  - produce a skeletal world with some light worldbuilding
  - populate the world with some items, locations, and entities

### Phase N (Iterative Refinements)
- add some submenus / subparsers for characters
- Develop an engine that isn't too unforgivably slow
  - Perform stress tests as necessary
- Add elements to MuddySwamp as necessary
- Improve server administration
  - clean up MuddySwamp.py
  - add more admin commands
  - add more command line arguments / server configuration options

### Phase Omega (We'll get here eventually)
- Develop a WebSocket-based browser client / server combo that can connect to MuddySwamp server

### Phase Aleph (We love these, but don't know if it will happen)
- Multithreading / ansynchronous programming
- Add NPCs that seem somewhat realistic
- Develop a scripting language for writing in-game dialogue and programming NPCs
- Use a database to store in-game objects.
- Allow servers to be paused, stopped, and resumed.
- Allow objects to be imported and updated at runtime.
- Create a robust system for converting characters from one character to another