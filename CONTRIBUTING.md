# Contributing to MuddySwamp

Thank you for helping out with the Open Source Club's MuddySwamp project!

Following these guidelines helps us keep good project workflow. We appreciate your help.

Our community guidelines are described in [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md).
Hop in our [discord](https://discord.gg/SCqmG3x) for any additional questions or just to hangout!

## How do I help?

Please check the **[Issues](https://github.com/ufosc/MuddySwamp/issues)** pages for current tasks.
If you see something that you would like to help with, ask about helping in a comment.
If you're just starting out, checkout our **[beginner friendly](https://github.com/ufosc/MuddySwamp/issues?q=is%3Aopen+is%3Aissue+label%3A%22good+first+issue%22)** issues for ways to help. 

Check out the [DESIGN.md](./DESIGN.md) file for a high level explanation of the project.

## Reporting Bugs

Check to see if someone already reported this [bug](https://github.com/ufosc/MuddySwamp/issues).
If so then comment on that issue.
If not, provide a detailed description of the bug.
Include what happened before the error, all settings, and test results. This helps us more quickly identify and solve any problems.
**[Create an Issue](https://github.com/ufosc/MuddySwamp/issues/new)** with the description and add the `bug` label.

## Requesting a Feature

Check our [design document](DESIGN.md) and other [issues](https://github.com/ufosc/MuddySwamp/issues) to see if the feature has already been requested. If so, then feel free to add your thoughts on that issue. If not, **[create an Issue](https://github.com/ufosc/MuddySwamp/issues/new)** with the description and add the `feature` label. 

## Testing on your own server

Any contributors working on scripts or engine code should test their code before submitting it. 

To test server code on your own machine, run

```
python MuddySwamp.py
```

Then with a telnet client, you will connect to the following IP like so:

```
telnet 127.0.0.1 1234
```

Alternatively, you can use Mudlet or another MUD client. 
Follow the instructions provided in [README.md](README.md) and use "127.0.0.1" and "1234" as the address and port, respectively. 

Test thoroughly, and maybe we can avoid some headaches down the line.

## Submitting Changes 

1. Create a fork or branch to tackle a specific issue 
	- Team members branch off of dev and follow this [guide](https://guides.github.com/introduction/flow/) 
	- Others make a [fork](https://guides.github.com/activities/forking/)
  	- Name it after the issue or feature you are working on
2. Follow the style guidelines below 
	- This helps with debugging and working on the project
3. Make small incremental commits
	- It's easier to find issues when only a small amount of code is changed
4. Thoroughly test your changes (see the section above). 
5. Make a pull request 
	- The request will be reviewed
	- Any needed changes will be noted 
6. The changes will be added to the project 
	- Yay! Thanks for the help. 

## Style Guide 

Use our **[.editorconfig]()** to help automatically format your code.

Python is meant to be a **readable**. We follow [PEP8](https://www.python.org/dev/peps/pep-0008/) and you should too.

You can also find our complete introduction to Python [here](https://github.com/ufosc/club-resources/tree/master/python).

## MuddySwamp - Creating a Location
Creating a location in MuddySwamp is easy. 
They are stored using the .json format, and you can refer to the locations [template](./locations/template) for reference.

A location's description is at the foundation of a text-based world. Here are a few words of advice:

- Use imagery
- Be brief and clear, avoid demonstratives and other clunky phrases
  - "In the corner, there is a bucket."  -> "In the corner, **sits** a bucket."
- Be Descriptive
  - "In the **shadowy** corner, sits a **gross** bucket."
- Show, don't tell
  - "In the shadowy corner, sits a bucket **caked in God knows what**."
- Action verbs are prefered over linking verbs (again, show don't tell)
  - "The boy is cold." -> "The boy **shivers**". 
- Vary your sentence structure
  - Bad:    "The boy and the girl played in the park. They were happy because they saw a dog. The boy was secretly in love."
  - Better: "The boy and the girl played in the park. Because they saw a dog, they were happy. Secretly, the boy was in love."
- Vary sentence length
  - Bad: "The prisoner's vision faded. He felt numbness. He saw past memories. He was going to die."
  - Better: "The prisoner's vision faded. He trembled and lost feeling in his limbs. Memories-his fifth birthday cake, his first kiss, his mother's tears at the trial-all flashed before him. He was going to die. 
- 3-4 sentences max (players will be reading these many times. More locations with short descriptions > less locations with long descriptions.)

## MuddySwamp - Creating a CharacterClass
Distinct characters are a cornerstone of this engine's gameplay. 
CharacterClasses provide a rich and easy way to write classes for in-game characters, with virtually no restrictions.
Any python code can be included in a CharacterClass.

### CharacterClasses: more than just a class

In the [character module](./character.py), there are two important definitions.

1) The CharacterClass metaclass
2) The Character class

A metaclass can best be explained like this:

* Gandalf the Grey, Dumbledore, and Hannibal Traven are instances of Wizard 
* Wizard is a class, which is itself an instance of CharacterClass

Without diving into the implementation too much, the CharacterClass metaclass changes the way ChracterClasses work, adding a few key features.
These 'CharacterClasses' are more than just standard classes.
They have one particularly amazing feature: any method prefixed with `cmd_` will be accessible to the player for direct execution. (More on this later.) 

To the user, writing a CharacterClass is the same as writing a normal class. 

In practice, the user simply inherits from the Character base class.
By inheriting from the Character base class, your class will be a CharacterClass. 

### Example CharacterClass
Here is an example:

```python
# import the Character base class
from character import Character

class Wizard(Character):
    def __str__(self):
        '''overriding the str() function'''
        return self.name + "the Wizard"

    def _level_check(self):
        '''internal method to check level'''
        if len(self.spells > self.level * 5):
            self.level += 1
  
    def add_spell(self, spell):
        '''add a spell, making it available to this wizard'''
        self.spells = spell
  
    def cmd_cast(self, args):
        '''usage: cast [spellname] [arguments]
        Cast [spellname] with arguments. Arguments very by spell.
        '''
        spell = args[1]
        if spell in self.spells:
            # cast the spell
            spell(args)
        else:
            # let the player know they do not have that spell
            self.message("You do not have that spell.")
    
    def cmd_spells(self, args):
        '''usage: spells [spells]
        List your spells.'''
        if len(self.spells)  == 0:
            self.message("You have no spells.")
        for spell in self.spells:
            self.message(str(spell))
```

When a user spawns as a Wizard, they will see this:

```
Welcome to MuddySwamp!
You are a(n): Wizard

What is your name?
>>>Bill

Announcement: Welcome to the server, Bill the Wizard!
>>> help

Type "help [command]" for specific information.
Commands available:
[PLAYER COMMANDS]
help  say  tell  walk  report
[WIZARD COMMANDS]
cast
>>> help cast

usage: cast [spellname] [arguments]
Cast [spellname] with arguments. Arguments very by spell. 

>>> cast fireball

Error: You do not have that spell.
>>> help spells

You have no spells.
```

First of all, notice how our class inherits from `Character`.
This **must** be done for it to be viable. 

Now, let's look at the Wizard's methods:
 - `__str__` is a special method that hooks into a top level function. 
    In this case, str(). You can read about those [here](https://docs.python.org/3/reference/datamodel.html).
 - `_level_check` is an internal method, which signals to other programmers that this method should not be called outside the class.
    (C++/Java programmers, think `private`).
 - `add_spell` is a normal method, intended to be executed anywhere.
 - `cmd_cast` and `cmd_spells` are commands, which can be executed anywhere... or **executed by directly by the user** as shown above.

Remember, `cmd_` commands are what makes CharacterClasses special.
By adding `cmd_cast` and `cmd_spells`, we have given the players two commands, `cast` and `spells`. We can implement them however we want, but there are a few restrictions:

First, you must accept at least one argument, `args`,  a list of strings that the user passed in.

```
>>> cast fireball
```

Will be executed as executing:

```python
wizard1.cmd_cast(["cast", "fireball"])
```
(assuming wizard1 is the Wizard character that Bill the Wizard is playing as)

The first element of "args" will always be the name of the command itself. 

Next, Take note of the use of doc-strings. 
Using doc-strings is good python practice (see above). 
But more importantly, this **MUST** be done for `cmd_` methods.
If we look at the help menus in the example above, you we will see that they are *generated from the the doc-strings*. 
Not only is including doc-strings good practice, but it's also vital for player experience!

Finally, let's look at our error handling for our `cmd_cast` method:
```python
def cmd_cast(self, args):
    '''usage: cast [spellname] [arguments]
    Cast [spellname] with arguments. Arguments very by spell.
    '''
    spell = args[1]
    if spell in self.spells:
        # cast the spell
        spell(args)
    else:
        # let the player know they do not have that spell
        self.message("You do not have that spell.")
```
We first get the spell's name from the list of args.
We need to check if the spell name is actually in the user's dictionary of spells. 
If it is, then good!
We can simply cast the spell.

If not, we should be nice and let the player know that they don't actually have that spell.
The `Character.message(string)` method will send a message to the player.

We haven't actually covered all our bases yet.
This method assumes the player will always enter a spell when they enter cast.
But what if they forget to?

```
>>> cast
```
is equivalent to
```python
wizard1.cmd_cast(["cast"])
```
In this case, we would get an `IndexError`, which could crash our whole server!
Now, we could try to catch that exception, or just avoid it altogether.
Since this is so easy to avoid and exceptions can prove expensive, let's just check the function first.

```python
def cmd_cast(self, args):
    '''usage: cast [spellname] [arguments]
    Cast [spellname] with arguments. Arguments very by spell.
    '''
    if len(args) < 2:
        self.message("You must enter a spell to cast.")
        return
    spell = args[1]
    if spell in self.spells:
        # cast the spell
        spell(args)
    else:
        # let the player know they do not have that spell
        self.message("You do not have that spell.")
```

Now our command is much more robust.

### An improved example
Now, this class won't work for a few reasons:
* `self.spells` has not been initialized
* `self.level` has not been initialized

Realize that, any time you add some new data field, you have to initalize it.
I could go back and add a `spells` data field to Character itself, but not all derived classes would need to use `spells`. 
So, let's add `spells` to just our wizard class.
(We'll do the same with `level`.)

To accomplish this, we have to add an `__init__`.

```python
from character import Character

class Wizard(Character):
    def __init__(self):
        self.spells = {}
        self.level = 1
        super().__init__()

    def __str__(self):
        '''overriding the str() function'''
        return self.name + "the Wizard"

    def _level_check(self):
        '''internal method to check level'''
        if len(self.spells > self.level * 5):
            self.level += 1

    def update(self):
        self._level_check()
        super().update()

    def add_spell(self, spell):
        '''add a spell, making it available to this wizard'''
        self.spells[spell.name] = spell

    def cmd_cast(self, args):
        '''usage: cast [spellname] [arguments]
        Cast [spellname] with arguments. Arguments very by spell.
        '''
        if len(args) < 2:
            self.message("You must enter a spell to cast.")
            return
        spell = args[1]
        if spell in self.spells:
            # cast the spell
            spell(args)
        else:
            # let the player know they do not have that spell
            self.message("You do not have that spell.")
    
    def cmd_spells(self, input_str):
        '''usage: spells [spells]
        List your spells.'''
        if len(self.spells)  == 0:
            self.message("You have no spells.")
        for spell in self.spells:
            self.message(str(spell))
```

Our new `__init__` method is pretty straightforward, but it has one important line.
Whenever we override `__init__`, we **must** call `super().__init__()`. 
This will call the `__init__` for the base class, Character, and make it do the important work that it needs to do. 

Also note: I added in an `update` method. 
This is overriding a method in the Character class, which you can expect to be called periodically.
If you have a functon, in this case, `_level_check`, to be called periodically, then we should put it here.
Again note that we call the base class's method: `super().update()`.
If you don't include that line, your CharacterClass will probably not work.

### The More Classes the Better
There is still a problem: what the heck is a spell? Let's create a class!

```python
class Spell:
    def __init__(self, name, effect):
        self.name = name
        self.effect = effect
    
    def __str__(self):
        return self.name

    def __eq__(self, other):
        # overriding the == operator
        # will also affect 'in' operator
        try:
            return self.name == other.name
        except AttributeError:
            return self.name == other

    def __call__(self, target=None):
        # this makes the spell object callable
        # i.e. typing spell(target) means spell.__call__(target)
        effect(target)
```

Now let's update our `cmd_cast` method:

```python
    def cmd_cast(self, args):
        '''usage: cast [spellname] [arguments]
        Cast [spellname] with arguments. Arguments very by spell.
        '''
        if len(args) < 3:
            self.message("You must enter a spell and target.")
            return
        spell = args[1]
        target_name = args[2]
        # search for a target
        target = None
        for character in self.location.get_character_list():
            if target_name == character.name:
                target = character
                break
        # if no target is found message the player
        if target is None:
            self.message("Could not find target with that name.")
            return
        if spell in self.spells:
            # cast the spell
            spell(target)
        else:
            # let the player know they do not have that spell
            self.message("You do not have that spell.")

```


So, I now we have a simple spell class.
In reality, you should make it far more robust. 
What about different kinds of spells?
Should there always be a target? 
The cast command in particular has a few issues, but this is just a demo. 

Now to make the magic happen:

```python
# lots of lazy exception handling for the sake of brevity
def fire_effect(target):
    try:
        target.message("You are on fire.")
        target.health -= 5
    except Exception:
        pass

def heal_effect(target):
    try:
        target.message("You are being healed")
        target.health += 5
    except Exception:
        pass

def insult_effect(target):
    import random
    sense = random.choice(['smell', 'look', 'sound', 'fight'])
    thing = random.choice(['horse', 'onion', 'muddycrab', 'gamer'])
    try:
        target.message("You %s like a %s." sense, thing)
    except Exception:
        pass

fireball = Spell("fireball", fire_effect)
soothe = Spell("soothe", heal_effect)
curse = Spell("curse", insult_effect)
wizard1.add_spell(fireball)
wizard1.add_spell(curse)
wizard1.add_spell(soothe)
```

Assume we have Bill the Wizard, or wizard1 from before, and we load him up with all the right spells. Now let's return to Bill:

```
>>> spells
fireball
curse
soothe

>>> cast fireball
You must enter a spell and target.

>>> cast fireball Bill

You are on fire!
>>> cast curse Bill

You sound like a onion.
```
Notice we never prevented the player from targeting themselves in cmd_cast. Now suppose someone else enters:

```
Matt the Dark Wizard enters.
Matt the Dark Wizard blasts you with lightning.
>>> cast heal Bill
You are being healed.

>>> cast fireball Matt
>>> cast fireball Matt
>>> cast fireball Matt
>>> cast fireball Matt
>>> cast fireball Matt

Matt the Dark Wizard died.
```

Here, we witness our spells in action.
Though, it seems unfair that we just spammed that command over and over again.
Maybe there should be a cooldown.
Hmmm... sounds like an idea for another day.

The key takeaway here should be that there is not a one class-per-file rule. 
You can have as many CharacterClasses and classes in a file are controlled by the mudimport.py system.
That brings us to our next section.

## Making your CharacterClass a playable option
For a CharacterClass to be playable, you first create a json in `chars/`
Suppose our script containing the class definition was in "wizard.py". We should put wizard.py into `./script/`. 

Next, we create a JSON file. 
You can find a template [here](chars/template):
```js
{
    "name" : "Wizard",
    "frequency" : 1.0,
    "path" : "scripts/wizard.py"
}
```
For good practice, should save this json as `wizard.json` (matching the name of the CharacterClass), but this is not required.
The important thing is, the **"name" field MUST match the name of the CharacterClass**, as defined in the file. 

If our python file reads:

```python
class RottenPotatoDealer(Character):
```
Then our JSON file should read:

```js
"name" : "RottenPotatoDealer"
```

The "path" should be a path from the top MuddySwamp directory, to the script containing the CharacterClass.

The field "frequency" establishes the relative frequency of this class. 
Essentially, the higher this number, then the more likely that a new player will spawn as a Wizard.

To provide a bit more nuance:
The frequency field is actually optional, and you can define the frequency in the python file directly:

```python
from character import Character

class Wizard(Character):
    
    frequency = 1.0

    def __init__(self):
        self.spells = {}
        self.level = 1
        super().__init__()
```

Any value in the JSON file's "frequency" field will just override the value in the python file.
We prefer that you write in the desired frequency directly in the python file.
We usually just change the "frequency" field of the json for debugging purposes.

### Coming soon
A few topics that I did not cover in this guide that I will cover later:
- referencing static objects
- the built-in features of the Character class
- Creating new Items