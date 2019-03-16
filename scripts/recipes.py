from scripts.sword import Sword
import material
import scripts.material_items as mi 
from character import CharException
import item

class Recipe:
    ''' Class defining parameters and methods for all recipe objects
    '''
    def __init__(self, item_class, key_item=mi.MaterialItem(), key_item_quantity=1, other_items=[]):
        ''' Recipe constructor requiring item_class which is to be made by this recipe
        and an aribtrarily long string of the required ingredients '''
        self.item_class = item_class
        self.key_item = key_item
        self.material = key_item.material
        self.ingredients = [key_item] * key_item_quantity
        self.ingredients += other_items
        # Makes ingredients list immutable
        self.ingredients = tuple(self.ingredients)



    def __contains__(self, other):
        return other in self.ingredients

    def check_ingredients(self, *args):
        ''' Verifies user has the necessary ingredients; the *args put into this method will be
        either the inventory of the user or the crafting ingredients provided (if the user is
        prompted to provide ingredients) '''
        user_ingredients = list(args)
        fulfilled = False
        # This loop checks to make sure all necessary ingredients are present
        for ing in self.ingredients:
            if ing in user_ingredients:
                user_ingredients.remove(ing)
                fulfilled = True
            else:
                fulfilled = False
                break 
        # When we pass in the user_ingredients list, all that should be left are effect items 
        if fulfilled:
            self.make(user_ingredients)
        else:
            raise CharException
            

    def make(self, effect_items):
        effect_list = []
        for effect_item in effect_items:
            effect_list += effect_item.effects
        return self.item_class(self.material, *effect_list)

    def __str__(self):
        return str(self.material) + (self.item_class)

''' 
    Below are the recipe objects to be used throughout the game. When creating a recipe, use
    the following format:
    item_class = the class of the item to be made. This MUST be the first argument
    Ex: the Sword class (see sword.py)
    key_item = the item which will decide the material of the item, if applicable.
                If not applicable, use the MaterialItem class which has the 
                default_material as its material. Key items MUST be material items.
    key_item_quantity = the number of the key_item required when crafting
    Then provide any other items needed to craft following this contained in a list, if applicable.
'''

iron_sword_recipe = Recipe(Sword, key_item=mi.IronIngot(), key_item_quantity=2 , other_items=[mi.WoodPlank()])
