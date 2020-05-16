from scripts.basic_rpg import Humanoid
from scripts.recipes import iron_sword_recipe, steel_sword_recipe, gator_bone_sword_recipe
from scripts.materialItems import IronIngot, WoodPlank, SteelIngot, GatorBoneShard
from item import UsableBase
import util.english as english

class Paladin(Humanoid):
    ''' Master craftsman, paladins use their knowledge of mechanical
    engineering and materials to craft, and use, the finest weapons
    and armor '''

    def __init__(self, name=None):
        super().__init__(name)
        self._recipes_dict = {}

    def cmd_craft(self, args):
        ''' Craft an item 
        Usage: craft [material] [item] with [ingredient1] ([quantity]), [ingredient2] ([quantity]), . . . [ingredient-n] ([quantity])
        '''
        if len(args) < 3:
            self.message("Invalid syntax; try using 'help craft' to see how to use this command")
        # The item_name corresponds to the name in the _recipes_dict
        item_name = " ".join(args[1:3])
        # The following two lines parse the comma delimited ingredients into a list of form ["ingredient1", "ingredient2". . .]
        ingredient_args = " ".join(args[4::])
        ingredient_args = ingredient_args.split(",")
        # Remove leading and trailing whitespaces from each element
        ingredient_args = list(map(lambda x: x.strip(), ingredient_args))
        # This dict will contain ingredient names (e.g. "Iron Ingot") mapped to the quantity number
        ingredients_dict = {}
        for element in ingredient_args:
            element = element.split("(")
            element[0] = element[0].strip()
            element[1] = element[1][0]
            try:
                ingredients_dict[element[0]] = int(element[1])
            except:
                pass
        if item_name in self._recipes_dict:
            ingredients_list = []
            # This loop adds all necessary items from the inventory to ingredients_list; if irrelevant, no item is added
            for key in ingredients_dict:
                if self.inv.find(key):
                    i = ingredients_dict[key]
                    while(i > 0):
                        ingredients_list.append(self.inv.find(key))
                        i -= 1
            # If the necessary ingredients aren't provided item = None
            item = self._recipes_dict[item_name].make(ingredients_list)
            if item:
                self.inv += item
                for ing in ingredients_list:
                    self.inv.remove_item(ing)
                self.message(str(item).capitalize() + " added.")
            else:
                self.message("You didn't supply the necessary items.")
        else:
            self.message("You don't know a recipe with that name.")
    
    def learn_recipe(self, recipe, item_name):
        if recipe in self._recipes_dict.values():
            self.message("You already know that recipe!")
            return False
        else:
            self._recipes_dict[item_name] = recipe
            self.message("You have learned the recipe for " + 
                        english.indefinite_article(str(item_name)) + 
                        " " + str(item_name))
            return True 

    def cmd_recipes(self, args):
        if(self._recipes_dict):
            msg = ["Known Recipes:"]
            for key in self._recipes_dict:
                msg.append(key)
            self.message("\n".join(msg))
        else:
            self.message("You don't know any recipes yet")