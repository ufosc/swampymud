
class Recipe:
    ''' Class defining parameters and methods for all recipe objects
    '''
    def __init__(self, item, material, *args):
        ''' Recipe constructor requiring item which is to be made by this recipe
        and an aribtrarily long string of the required ingredients '''
        self.ingredients = args
        self.item = item
        self.material = material

    def check_ingredients(self, *args):
        ''' Verifies user has the necessary ingredients; the *args put into this method will be
        either the inventory of the user or the crafting ingredients provided (if the user is
        prompted to provide ingredients) '''
        user_ingredients = list(args)
        fulfilled = False
        for ing in self.ingredients:
            if ing in user_ingredients:
                user_ingredients.remove(ing)
                fulfilled = True
            else:
                fulfilled = False
                break    
        if fulfilled:
            self.make(user_ingredients)

    def make(self, effect_items):
        effect_list = []
        for effect_item in effect_items:
            effect_list += effect_item.effects
        self.item(self.material, *effect_list)

        
