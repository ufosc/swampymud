from scripts.basic_rpg import Humanoid
from scripts.recipes import iron_sword_recipe
from scripts.materialItems import IronIngot, WoodPlank

class Paladin(Humanoid):
    ''' Master craftsman, paladins use their knowledge of mechanical
    engineering and materials to craft, and use, the finest weapons
    and armor '''

    def __init__(self):
        super().__init__()
        self.recipes_dict = {"iron sword" : iron_sword_recipe}

    def cmd_craft(self, args):
        ''' Craft an item 
        Usage: craft [material] [item] with [ingredient1], [ingredient2], . . . [ingredient-n]
        '''
        if len(args) < 3:
            self.message("Invalid syntax; try using 'help craft' to see how to use this command")
        item_name = " ".join(args[1:3])
        ingredient_args = " ".join(args[4::])
        ingredient_args = ingredient_args.split(",")
        # The following line removes leading and trailing whitespaces from each element
        ingredient_args = list(map(lambda x: x.strip(), ingredient_args))
        if item_name in self.recipes_dict:
            ingredients_list = []
            for argument in ingredient_args:
                if self.inv.find(argument):
                    ingredients_list.append(self.inv.find(argument))
            item = self.recipes_dict[item_name].make(ingredients_list)
            if item:
                self.inv += item
                for ing in ingredients_list:
                    self.inv.remove_item(ing)
            else:
                self.message("You didn't supply the necessary items.")
        else:
            self.message("You don't know a recipe with that name.")

    def cmd_gimme(self, args):
        ''' Gives some items '''
        self.inv += IronIngot()
        self.inv += IronIngot()
        self.inv += WoodPlank()

    

        