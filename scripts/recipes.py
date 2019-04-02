from scripts.sword import Sword
import material
import scripts.materialItems as mi 
from character import CharException
import item

class Recipe:
    ''' Class defining parameters and methods for all recipe objects
    '''
    def __init__(self, item_class, key_item_class=mi.MaterialItem, key_item_quantity=1, other_items_classes={}):
        ''' Recipe constructor requiring item_class which is to be made by this recipe
        and an aribtrarily long string of the required ingredients '''
        self.item_class = item_class
        self.key_item_class = key_item_class
        self.ingredients = []
        for i in range(key_item_quantity):
            self.ingredients.append(key_item_class)
        if other_items_classes:
            for item_class in other_items_classes:
                for i in range(other_items_classes[item_class]):
                    self.ingredients.append(item_class)
        # Makes ingredients list immutable
        self.ingredients = tuple(self.ingredients)



    def __contains__(self, other):
        return other in self.ingredients

    def _check_ingredients(self, args):
        ''' Verifies user has the necessary ingredients; the *args put into this method will be
        either the inventory of the user or the crafting ingredients provided (if the user is
        prompted to provide ingredients) '''
        user_ingredients = args.copy()
        fulfilled = False
        # This loop checks to make sure all necessary ingredients are present
        for ing in self.ingredients:
            for user_ing in user_ingredients:
                if type(user_ing) is ing:
                    fulfilled = True
                    user_ingredients.remove(user_ing)
                    break
            else:
                fulfilled = False
        # When we pass in the user_ingredients list, all that should be left are effect items 
        return fulfilled
            
    def make(self, args):
        ''' Make calls check_ingredients to ensure that all ingredients used are present in the argument list
            and, if true, returns the desired item. If false, returns None.
        '''
        user_ingredients = args.copy()
        if(self._check_ingredients(user_ingredients)):
            for ing in self.ingredients:
                for user_ing in user_ingredients:
                    if type(user_ingredients) is ing:
                        user_ingredients.remove(user_ing)
            # Now there should only be effect items in user_ingredients
            effect_list = []
            # for effect_item in user_ingredients:
            #    effect_list += effect_item.effects
            return self.item_class(self.key_item_class.material(), *effect_list)
        else:
            return None

    def __str__(self):
        return str(self.key_item_class.material()) + (self.item_class)

''' 
    Below are the recipe objects to be used throughout the game. When creating a recipe, use
    the following format:
    item_class = the class of the item to be made. This MUST be the first argument
    Ex: the Sword class (see sword.py)
    key_item_class = the class of the ingredient item which will decide the material of the item.
                     Key items MUST be material items.
    
    key_item_quantity = the number of the key_item_class required when crafting
    Then provide any other items needed to craft following this contained in a dictionary, if applicable.
    The keys are the classes of the items and the values are the quantities
'''

iron_sword_recipe = Recipe(Sword, key_item_class=mi.IronIngot, key_item_quantity=2 , other_items_classes={mi.WoodPlank:1})

steel_sword_recipe = Recipe(Sword, key_item_class=mi.SteelIngot, key_item_quantity=3 , other_items_classes={mi.WoodPlank:2})

gator_bone_sword_recipe = Recipe(Sword, key_item_class=mi.GatorBoneShard, key_item_quantity=4 , other_items_classes={mi.WoodPlank:2})

