# Muddy World Files: An Informal Specification
*Name subject to change.*

## Purpose
We created this save format so that all meaningful in-game data can be saved and loaded at a later time.
Our main objectives are as follows:

1) Make the save files easy for humans to read, parse, and interpret.

2) Minimize the complexity of the text parsers and evaluaters that we write.

3) Minimize redundant information.

4) Capture cyclic and recursive relationships between game objects.

This format is **not** optimized for performance.
While we avoid needlessly expensive features, our main goal is not to create a format that is novel and innovative, but rather, one that is straightforward and intuitive.
Our project is, after all, a Python project.

## Muddy World Files are based on YAML

With our aims in mind, this format is based on [YAML](https://yaml.org/).
YAML is a reasonable choice given Objective #1.
Furthermore, by using existing libraries (namely [PyYAML](https://pyyaml.org/) we can write less code to evalauate the save files (Objective #2).
Therefore, in our project, all files are first processed using PyYAML.

Given save file `myworld.yaml`, you would complete this first processing like so:
```python
import yaml
with open("myworld.yaml") as save_file:
    data = save_file.read()

parsed_data = yaml.load(data)
```

For the remainder of this specification, we can discuss the format using terms like "list" and "mapping".
Refer to the YAML specification for formal definitions of these terms.

## File Structure
MuddySaves contain exactly 3 segments:

```yaml
prelude:
    # Prelude data
personae:
    # Dramatis Personae data
tree:
    # World Tree data
```

- The `prelude` defines classes and points to their location. For example:
    - The class "Wizard" is defined in `scripts/magic.py`
    - The class "GoldenRing" is defined in `scripts/jewelry.py`
- The dramatis `personae` defines specific in-game objects
    - "The Red House" is a Location
    - "Matt" is a Wizard with skill level 5
    - "Vulcan's Band" is a GoldenRing with a fire shield
- The world `tree` defines the hierarchy of the world (e.g. "Matt" the Wizard is in a Location named "The Lair")
    - Matt is in the Red House.
    - Matt is holding "Vulcan's Band".

A save file is valid if and only if it contains exactly these 3 segments.
Missing a segment or adding a new one invalidates the file.

Now we will discuss each segment in detail.

### The Prelude
The `prelude` segment is a mapping that maps filenames to desired exports.
For instance:

```yaml
prelude:
    scripts/magic.py: [Wizard, DarkWizard, Alchemist, WoodenStaff]
    scripts/jewerly.py: [GoldenRing, SilverRing, EnchantedNecklace]
    # add more scripts and classes as appropriate
```

The example above equates to the following Python code:

```python
from scripts.magic import Wizard, DarkWizard, Alchemist, WoodenStaff
from scripts.jewerly import GoldenRing, SilverRing, EnchantedNecklace
```

More formally, the mapping in the `prelude` segment should fit the following format:
```
filename -> class_list
```
Where `filename` is a string containing the script's location, and `class_list` is a list of strings containing classes to be imported from the script.
Each class name in `class_list` must refer to a valid class in the script.

Game objects in the `personae` and world `tree` can then refer to classes with the names provided in this segment. So, in this example, a personae object can be of type "Wizard", "SilverRing", etc.

In addition to the classes imported from the `prelude`, we can also expect some built-in classes.
Refer to the [Built-in Classes](#built-in-classes) section of the appendix.

#### Pseudoclasses
*Defining new types in the save file itself*
```
#TODO
```


### The Dramatis Personae
The `personae` segment is a dictionary that maps object symbols (strings) to their data (mappings).
For instance:

```yaml
personae:
    Red_House:
        _type: Location
        description: This is a beautiful brick house.
    WIZARD_MATT:
        _type: Wizard
        lvl: 5
    vulcans_band:
        _type: GoldenRing
        value: 1500
        shield_type: fire
```

This segment roughly approximates the following Python code:
```python
Red_House = Location(description="This is beautiful brick house.")
WIZARD_MATT = Wizard(lvl=5)
vulcans_band = GoldenRing(value=1500, shield_type="fire")
```
Although this Python representation adequately describes this example, this code will be expanded [below](#implementation-detail-cyclic-references).

#### Symbol Recommendations
To make the World Tree unambigious, all but two symbols are forbidden. 
Two strings are reserved words and cannot be used as symbols: `_type` and `_id`.
This restriction is used to make the World Tree unambigious.

Although any string except for `_type` and `_id` can be used as an identifier, we recommend that they match the regex `[A-Za-z0-9_]+`. 
In other words, one or more letters, digits or underscores. Symbols should be short, but expressive (e.g. "WIZ_MATT" or "chest53").

Most importantly, symbols **must** be unique to each game object.
Using a symbol to refer to multiple game objects is considered invalid, and will result elicit undefined behavior from our project.

#### Implementation Detail: Cyclic References
*Author's Note: We will later move this section into our developer's manual. When we do, we will leave a link to the relevant section here...*

To satisfy Objective #4, allow other symbols to be referenced within the data blocks.

Consider a "Person" class, a class that allows everyone to have one best friend forever (bff).
```yaml
    bill:
        _type: Person
        age: 21
        bff: george
    george:
        _type: Person
        age: 20
        bff: bill
    fred:
        age: 30
        _type: Person
        bff: fred
```

If we translate this to Python code like the code above, we will get an error:
```python
bill = Person(bff=george)   # NameError: 'george' is not defined
george = Person(bff=bill)
fred = Person(bff=fred)     # NameError: 'fred' is not defined
```

To address this, we need to refine our model of the personae.
In actuality, the `personae` is **read twice**.
First, basic objects are loaded and bound to the appropriate symbol.
Then, when all symbols have been established, objects are read in a second time.

This is a more accurate representation of what happens with the code above.
```python
bill = Person()
george = Person()
fred = Person()

# we call a 'postload' method
# which can use symbols 
bill.set_bff(george)
george.set_bff(bill)
fred.set_bff(fred)
```

Because the `personae` is processed in two passes, MUD developers can capture cyclic and recursive relationships as they see fit.

### The World Tree
The `tree` captures the hierarchy of the world.
That is, the `tree` depicts what game objects own other objects.

Consider the following tree:
```yaml
tree:
    Secret_Lair:
        lord_moldybort
    Red_House:
        WIZARD_MATT:
            vulcans_band
```
This `tree` states that the Secret Lair contains Lord Moldybort and The Red House contains Matt the Wizard, who is holding Vulcan's Band. 

Let us define the World Tree recursively.

First, a symbol (string) is a valid World Tree.
```yaml
# a valid, yet simple World Tree
vulcans_band
```

An anonymous object [(discussed below)](#anonymous-objects) is a valid World Tree.
```yaml
_type: IronSword
name: Ole Rusty
damage: 10
```

An list of World Trees is a valid World Tree.
```yaml
- _type: IronSword
  name: Ole Rusty
  damage: 10
- vulcans_band
- WIZARD_MATT
```
Most importantly, a dictionary that maps symbols to World Trees is a valid World Tree.
When we a symbol is mapped to a World Tree, we say that the symbol *owns* the World Tree.
```yaml
Secret_Lair:
    lord_moldybort
Red_House:
    WIZARD_MATT
```
Thus, this World Tree shows that the Secret Lair *owns* Lord Moldybort as the Red House *owns* Matt the Wizard.
In other words, Lord Moldybort is in the Secret Lair and Matt the Wizard is in the Red House.

#### Symbols can only be used once
The World Tree is an *ownership* hierarchy.
Thus, symbols can appear only in one place in the hierarchy.
Consider the following example:
```yaml
Red_House:
    WIZARD_MATT
Blue_House:
    WIZARD_MATT
```
Well, which house is Matt the Wizard in?
The answer is ambigious and thus this World Tree is invalid.

Some violations are more innocuous:
```yaml
Red_House:
    WIZARD_MATT
Red_House:
    benedict_the_thief
```
In this case, it is clear that the World Tree is trying to say that both Matt and Benedict are in the the Red House.
However, this YAML will not even import correctly, since Red_House" can only map to one field, not multiple.
The fix here is simple:

```yaml
Red_House:
    - WIZARD_MATT
    - benedict_the_thief
```
Lastly, some objects may be especially tempting to use more than once.
```yaml
Red_House:
    WIZARD_MATT:
        health_potion
    benedict_the_thief:
        health_potion
```
This code feels correct, but we must remember that the symbol `health_potion` refers to one specific object, not a general Health Potion type.
In scenarios like these, anonymous objects work well, which brings us to our next section.

#### Anonymous Objects
To understand the need for anonymous objects, consider this highly likely case.
We have a thief (Benedict) with a lot of golden nuggets.
```yaml
prelude:
    scripts/thief.py: [Thief, GoldenNugget]
personae:
    thief_den:
        _type: Location
        name: Thief's Den
        description: This is where the infamous thief Benedict lives.
    benedict_the_thief:
        _type: Thief
        name: Benedict
    gold_nug1:
        _type: GoldenNugget
    gold_nug2:
        _type: GoldenNugget
    gold_nug3:
        _type: GoldenNugget
    gold_nug4:
        _type: GoldenNugget
    gold_nug5:
        _type: GoldenNugget
    gold_nug6:
        _type: GoldenNugget
tree:
    thief_den:
        benedict_the_thief:
            - gold_nug1
            - gold_nug2
            - gold_nug3
            - gold_nug4
            - gold_nug5
            - gold_nug6
```
This is a clear violation of Objective #3.
The symbols gold_nug[1-6] only appear in the `tree`, and are not actually referenced anywhere in the `personae`.
So here we introduce an *anonymous object*, an object that appears directly the tree and lacks any symbol in the `personae` segment.
```yaml
prelude:
    scripts/thief.py: [Thief, GoldenNugget]
personae:
    thief_den:
        _type: Location
        name: Thief's Den
        description: This is where the infamous thief Benedict lives.
    benedict_the_thief:
        _type: Thief
        name: Benedict
tree:
    thief_den:
        benedict_the_thief:
            - _type: GoldenNugget
            - _type: GoldenNugget
            - _type: GoldenNugget
            - _type: GoldenNugget
            - _type: GoldenNugget
            - _type: GoldenNugget
```
Because we used anonymous objects, we have cut out unnecessary `personae` symbols that will never be used during the file.
If we use an [ItemStack](#built-in-classes), the save will be even more condensed.

```yaml
prelude:
    scripts/thief.py: [Thief, GoldenNugget]
personae:
    thief_den:
        _type: Location
        name: Thief's Den
        description: This is where the infamous thief Benedict lives.
    benedict_the_thief:
        _type: Thief
        name: Benedict
tree:
    thief_den:
        benedict_the_thief:
            - _type: ItemStack
              item: GoldenNugget
              amount: 6  
```

Be warned, however, anonymous objects have one major restriction.
As stated in our definition above, we cannot map anonymous objects to World Trees.
In other words, anonymous objects cannot own other objects and must always be at the bottom of the World Tree.

## Summary

To conclude, let us review the three segments of a World File.
As stated above, World Files are formatted with YAML.
For more rigorous definitions of the terms 'string', 'list', 'mapping', etc., refer to the YAML specification.

A `prelude` defines the types used in a World File.
A valid `prelude` is a mapping that maps filenames (strings) to lists of class names (strings).

A `personae` defines symbols to be referenced in the `personae` and `tree` sections.
These symbols can appear anywhere, including in their own definition.
A valid `personae` is a mapping that maps symbols to object data. (Object data are mappings that map fields with their associated values.)

A `tree` establishes the ownership hierachy of the world.
A valid `tree` should contain a valid World Tree.
We define a valid World Tree inductively:

- symbols are valid World Trees
- anonymous objects are valid World Trees
- lists of World Trees are valid World Trees
- mappings that map symbols to World Trees are valid World Trees

## Appendix
### Built-in Classes
Two classes are always implicitly added to the `prelude`: `Location` and `ItemStack`.

The `Location` class is defined in the `location.py` and used to create in-game locations.
Since this data should obviously be included in a World File, the `Location` class is available automatically.
For more information on the `Location` class, refer to the relevent section of the Developer's Manual.

```
TODO: add a link to the section when complete
```

The `ItemStack` class is defined in `inventory.py` and used to stack redundant item instances together.
Besides being used internally in the `Inventory` class, the `ItemStack` can be used for serialization purposes as well.
We demonstated a use case for this class in the [anonymous object section](#anonymous-objects).

An ItemStack takes the following arguments:
- `item`: the class of the item being stored
- `amount`: the amount of items in this stack
- `data`: any data associated with the items in this stack

The `data` field can be set to `None`.
For items to stack, their data *must* be the same.

As an example, this `ItemStack` represents 13 health potions with that restore 5 HP.
In YAML:
```yaml
_type: ItemStack
item: HealthPotion
amount: 13
data:
    hp: 5
```
In Python:
```python
ItemStack(item=HealthPotion, amount=13, data={"hp": 5})
```

### Suggested Naming Conventions
Because these files are YAML files, we advise using a `.yaml` extension.
If the files are compressed (as is the case with our project), you can append the appropriate file extension to the filename.
For example: `save.yaml.gz`.