"""testcases for interaction between characters, items, and entities"""
import unittest
import swampymud.location as location
import swampymud.character as character
import swampymud.item as item
import swampymud.inventory as inventory

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


class MagicSalesman(MagicUser):
    """While they cannot cast spells, Magic Salesman are still magic users
    in their own right.
    """

    @character.Command
    def brew(self):
        """create a potion"""
        self.message("Created a potion.")
        self.add_item(Potion())

# now for some items

def find_player(char, args):
    if len(args) == 0:
        char.message("Please enter a target.")
        return
    name = " ".join(args).lower()
    for target in char.location.characters:
        if name == str(target).lower():
            return target
    char.message(f"Target '{name}' not found.")


class Potion:
    """a simple potion"""

    def on_use(self, char, args):
        self.char.message("Used a potion.")


class FireStaff(item.Equippable):
    """a staff that enables people to craft weapons"""
    target = inventory.EquipTarget("right hand")

    # interestingly, a staff uses can vary by class
    @character.Command.with_traits(filter=character.Filter(
        character.Filter.WHITELIST,
        [Wizard]
    ))
    def fireball(self, char, args):
        """Cast a fireball at a target."""
        target = find_player(char, args[1:])
        if target is not None:
            target.message(f"{char} hit you with a fireball.")
            char.message(f"You hit {target} with a fireball.")

    @character.Command.with_traits(filter=character.Filter(
        character.Filter.WHITELIST,
        [Brute]
    ))
    def hit(self, char, args):
        """Hit target with this staff."""
        target = find_player(char, args[1:])
        if target is not None:
            target.message(f"{char} hit you with a staff.")
            char.message(f"You hit {target} with a staff.")


class InvisibleLocket:
    """a locket that can only be seen by magic users"""


class TestInteraction(unittest.TestCase):

    def setUp(self):
        self.brute = Brute("Joe")
        self.seller = MagicSalesman("Adam")
        self.wizard = Wizard("Simon")
        self.brute.set_location(tavern)
        self.seller.set_location(tavern)
        self.wizard.set_location(tavern)

    def tearDown(self):
        self.brute.despawn()
        self.seller.despawn()
        self.wizard.despawn()

    def test_fire_staff(self):
        brute, seller, wizard = self.brute, self.seller, self.wizard
        # put down three fire staffs
        tavern.add_item(FireStaff())
        tavern.add_item(FireStaff())
        tavern.add_item(FireStaff())
        # each character picks one up
        brute.command("pickup fire staff")
        seller.command("pickup fire staff")
        wizard.command("pickup fire staff")
        inv_with_staff = inventory.Inventory(
            (FireStaff(), 1)
        )
        self.assertEqual(brute.inv, inv_with_staff)
        self.assertEqual(seller.inv, inv_with_staff)
        self.assertEqual(wizard.inv, inv_with_staff)
        # each player should be able to equip the staff
        brute.command("equip fire staff")
        seller.command("equip fire staff")
        wizard.command("equip fire staff")
        rh = inventory.EquipTarget("Right hand")
        self.assertTrue(isinstance(brute.equip_dict[rh][0], FireStaff))
        self.assertTrue(isinstance(seller.equip_dict[rh][0], FireStaff))
        self.assertTrue(isinstance(wizard.equip_dict[rh][0], FireStaff))
        # now brute and wizard should have updated commands
        self.assertTrue("hit" in brute.cmd_dict and
                        "fireball" not in brute.cmd_dict)
        self.assertTrue("hit" not in seller.cmd_dict and
                        "fireball" not in seller.cmd_dict)
        self.assertTrue("hit" not in wizard.cmd_dict and
                        "fireball" in wizard.cmd_dict)
        # test that the commands can be used
        brute.command("hit adam")
        self.assertEqual(brute.msgs.get_nowait(),
                         f"You hit {seller} with a staff.")
        self.assertEqual(seller.msgs.get_nowait(),
                         f"{brute} hit you with a staff.")
        wizard.command("fireball adam")
        self.assertEqual(wizard.msgs.get_nowait(),
                         f"You hit {seller} with a fireball.")
        self.assertEqual(seller.msgs.get_nowait(),
                         f"{wizard} hit you with a fireball.")
