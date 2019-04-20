from scripts.basic_rpg import Humanoid
from scripts.recipes import iron_sword_recipe, steel_sword_recipe, gator_bone_sword_recipe
from scripts.materialItems import IronIngot, WoodPlank, SteelIngot, GatorBoneShard

class Paladin(Humanoid):
    ''' Master craftsman, paladins use their knowledge of mechanical
    engineering and materials to craft, and use, the finest weapons
    and armor '''

    def __init__(self):
        super().__init__()
        # This default dict needs to be changed later, but is fine now for testing
        self.recipes_dict = {
            "iron sword" : iron_sword_recipe,
            "steel sword" : steel_sword_recipe,
            "gator sword" : gator_bone_sword_recipe
        }

    def cmd_craft(self, args):
        ''' Craft an item 
        Usage: craft [material] [item] with [ingredient1] ([quantity]), [ingredient2] ([quantity]), . . . [ingredient-n] ([quantity])
        '''
        if len(args) < 3:
            self.message("Invalid syntax; try using 'help craft' to see how to use this command")
        # The item_name corresponds to the name in the recipes_dict
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
        if item_name in self.recipes_dict:
            ingredients_list = []
            # This loop adds all necessary items from the inventory to ingredients_list; if irrelevant, no item is added
            for key in ingredients_dict:
                if self.inv.find(key):
                    i = ingredients_dict[key]
                    while(i > 0):
                        ingredients_list.append(self.inv.find(key))
                        i -= 1
            # If the necessary ingredients aren't provided item = None
            item = self.recipes_dict[item_name].make(ingredients_list)
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
        if recipe in self.recipes_dict.values():
            self.message("You already know that recipe!")
        else:
            self.recipes_dict[item_name] = recipe