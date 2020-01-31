"""module with a location-based circular dependency"""
import mudscript
from testing.script.basic_rpg import Humanoid

# location imports
DARK_TOWER = mudscript.import_location("Dark Tower")
DARK_DUNGEON = mudscript.import_location("Dark Dungeon")

class DarkLord(Humanoid):
    """the most evil, corrupt wizard"""

    starting_location = DARK_TOWER

    def cmd_retreat(self, args):
        """retreat to your home base"""
        self.location.message_chars(f"{self._name} disappeared "
                                    "in a plume of smoke!")
        self.set_location(DARK_TOWER)

    def cmd_capture(self, args):
        """send a character to the Dark Dungeon"""
        if len(args) < 2:
            self.message("You must select a target.")
            return
        target = self.location.find(args[1])
        if target is None:
            self.message(f"Error: Target '{args[1]}' not found.")
        else:
            target.message("You have been captured!")
            target.set_location(DARK_DUNGEON)

    def cmd_laugh(self, args):
        """laugh maniacally"""
        mudscript.message_all(f"{self} laughs maniacally.")

# note we have no mechanism of exporting locations
# all 'static' locations (locations created before the server launches) should be declared using mudscript.import_location
# all 'dynamic' locations (locations created programatically) should be connected to an existing Location via an exit
# this allows the world tree to correctly traverse the plane of exits when serializing the world

# what if a character is in an exit that is created programmatically, with no other exits?
# what if an important item, test, etc. is in an unreachable location? too bad
