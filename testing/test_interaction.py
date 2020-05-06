"""testcases for interaction between characters, items, and entities"""
import location
import character
import item
import character

# first, some locations
tavern = location.Location("Tavern", "A scuzzy tavern.")
plaza = location.Location("Plaza", "A few shops can be seen.")
# now connect the two
plaza.add_exit(location.Exit(tavern, "tavern"))
tavern.add_exit(location.Exit(plaza, "outside", ["back", "plaza"]))

# now create some CharacterClasses
class Humanoid(character.Character):
    """A class representing most humanoids"""
    equip_slots = ["Right hand", "head", "cHEST"]

    starting_location = tavern


class Brute(Humanoid):
    """A simple character, known to resolve problems with his fists"""

    @character.Command
    def smash(self, args):
        self.message("RARG BIG SMASH")


class Thief(Humanoid):
    """A unscrupulous grifter of the worst kind, will resort to anything
    for a bit of coin.
    """


class MagicUser(Humanoid):
    """base class for other magic users"""
    equip_slots = ["Right hand", "head", "chest", "necklace"]


class Wizard(MagicUser):
    """A master of the high arts."""


class PotionSeller(MagicUser):
    """While he cannot cast spells, Potion Sellers are still magic users
    in their own right.
    """

# now for some items