# The Design of swampymud

## Introduction

As wonderful as it may be, Python is incredibly slow.
Thus, to make Python worthwhile, we must squeeze as much productivity out of its two main advantages: readability and dynamic typing.
In `swampymud`, we frequently make use of metaclasses to dynamically add attributes to classes created by developers.
(For example, when creating an equippable Sword class, we may automatically collect certain methods to be used as player commands.)
Every implementation decision is dictated by one priority: make an intuitive, easy-to-use package for people relatively new to Python.

In this engine, characters have an extremely strong sense of class.
A character's class dictates precisely what commands they can use, what items they can pickup, and what locations they can enter.
With this in mind, we made creating a **CharacterClass** as simple as possible, just derive from `character.Character` and start writing commands.

Beyond CharacterClasses, the MuddySwamp engine is quite simple. **Items** can be picked up and added to a character's inventory. Some **Items** can be equipped. These **Equippables** give the player access to additional commands whenever they are added.

The world is divided into individual rooms called **Locations**.
**Locations** contain a description, list of characters in that location, an inventory of **items**, and a set of **entities**. 

**Locations** are connected by **Exits**.
You can think of live swampymud world as a [directed graph](https://en.wikipedia.org/wiki/Directed_graph), where **Exits** are the edges and **Locations** are the vertices. In a nutshell, this means that **Exits** are one-way by default.

**Entities** can be placed inside locations and allow for more player interaction.
Like **Items**, **Entities** add additional commands to the player's dictionary.

Perhaps best of all, the elements of the world--**Locations**, **Exits**, **Items**, and **Entities**--can be created and extended dynamically.
(Thank you Python!)
We encourage users of engine to allow unlimited creation at runtime.
You can easily extend these primatives to support things like crafting, location building, spell creation, and more.

## Package Overview
```
swampymud
├── __main__.py
├── mudserver.py
├── location.py
├── character.py
├── entity.py
├── item.py
├── inventory.py
├── mudworld.py
├── mudscript.py
└── util
    ├── color.py
    ├── shadowdict.py
    ├── english.py
    ├── misc.py
    ├── biject.py
    └── validate.py
```

### `__main__.py`
- Script executed when `python3 -m swampymud`
- Handles command-line arguments, loads worldfiles, and starts swampymud server

### `mudserver.py`
  - Forked from `mudserver.py` from Mark Frimston, minimal changes
  - defines a server class that
    - handles events like new players joining
    - sends / receives messages
  - COMING SOON: a websocket-based server

### `location.py`
  - defines the `Location` class
    - Locations have a proper name and description
    - Locations contain characters, entities, and items
  - defines the `Exit` class
    - Exits contain a list of names and a pointer to another location (its destination)
    - Exits can also include filters that only permit certain characters to interact with them

### `character.py`
  - defines `CharacterClass`, the metaclass that in-game character classes
    - "Wizard" would be a `CharacterClass`
    - "Bill the Wizard" is a Wizard
  - defines `Character`, the base class for player-controlled characters
    - possesses many useful functions for working with characters
    - establishes default commands
    - developers should derive from Character to create new CharacterClasses
  - defines the `Filter` class
    - filters grant permissions to some characters while denying others
    - filters can apply to both individual characters and classes as a whole
  - defines the `Command` class
    - you can use Command as a decorator to convert a method into a player-accessible command
    - you can also apply filters to a Command

### `entity.py`
  - defines `Entity`, the base class for all in-game entity-classes
    - can be placed in Locations much like Characters
    - you can use `character.Filter` to affect which characters can perceive or interact with a certain entities
    - Entity methods can be decorator with `character.Command` just as with CharacterClasses
    - includes methods `on_enter`, `on_exit`, and `on_message`, triggers that can be overriden for unique code execution in response to events

### `item.py`
  - defines `Item`, the base class for all Items
    - you can use `character.Filter` to affect which characters can perceive or interact with a certain entities
    - all item classes include the triggers `on_pickup` and `on_drop`, triggers than can be overriden
    - if an `on_use` method is provided, then the `Item` is considered `Usable`
  - defines `Usable`, an abstract class used for convenience
    - `isinstance(item, Usable)` returns true if item has an `on_use` method
  - defines `Equippable`, derived from `Item` and used as a base class for all equippable items
    - include the `on_equip` and `on_unequip` triggers
    - support methods decorated with `character.Command` (any commands will be made available to the player if equipped)
    - `Equippable` classes require a target (see `EquipTarget` below)

### `inventory.py`
  - defines the `Inventory` class
    - used by locations and characters to store items
    - essentially serializes and deserializes items when storing them in a dictionary
    - future optimizations welcome
  - defines the `EquipTarget` class
    - characters use a dictionary of `EquipTarget` keys to track which items are currently equipped

### `mudworld.py`
  - defines a series of functions for parsing world files
    - `read_worldfile` parses a YAML file into a pythonic format, and checks that it has correct sections
    - `load_prelude` loads all the appropriate CharacterClasses, ItemClasses, and EntityClasses
    - `load_personae` initializes all of the serialized objects
    - `load_tree` traverses the world tree, adding characters to location, items to inventories, etc.
  - defines the `World` class to represent an in-game world
    - stores all Locations in a `dict`
    - tracks the source files for CharacterClasses, ItemClasses, EntityClasses
    - provides `to_file` and `from_file` for saving and loading a `World`
  - provides a method, `World.test_world` which loads a test world

### `mudscript.py`
  - provides a high-level API for `swampymud` developers a server instance
    - `message_all` sends a message to *all* players connected to a running server
    - `import_location` allows scripts to import a static location when a location is being loaded
  - within the `swampymud`, we use a handful of methods to make the above functions work
    - `export_server` makes a server available to the `mudscript` module
    - `LocationExport` can be used to make locations available to the `mudscript` module

### `util`
Module containing miscellaneous utilities.

#### `util/color.py`
- has a *LOT* of documentation and research about ANSI escape codes and terminal color support
- defines the `SGRFunction` abstract base class, which serves as a simple wrapper for coloring text
  - Implemented SGRFunctions include things like `Italic`, `Underline`, `Red`, `Green`, etc. 
  - Wrapped strings can easily work with other strings (formatting, concatenating, and more)
  ```python
  name = Red("Sword")
  # prints 'Sword' in red
  print(name)
  # prints 'Epic Sword' with 'Sword' in red
  print("Epic " + name) 
  # prints 'Cool Sword' with 'Sword' in red
  print("Cool {}".format(name))
  ```
- includes several functions for testing
  - run `python3 -m swampymud.util.color` to test which formatting options your terminal supports
- includes convenient function `disable_all()` that globally disables any color formatting

#### `util/shadowdict.py`
- defines the `ShadowDict` class
  - a `ShadowDict` functions just like normal `dict`, excepted that old entries are shadowed, not overrwritten:
    ```python
    sd = ShadowDict()
    sd["color"] = "blue"
    print(sd["color"]) # blue

    # updating the key with a new item
    sd["color"] = "red"
    print(sd["color"]) # red

    # deleting an item reveals the old one
    del sd["color"]
    print(sd["color"]) # blue
    ```
  - Character commands are stored in a `ShadowDict`
