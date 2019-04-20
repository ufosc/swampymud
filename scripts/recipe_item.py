from item import UsableBase
import scripts.recipes as recipes
import random
import util.english as eng

class RecipeItem(UsableBase):

    _recipe = recipes.iron_sword_recipe

    def __init__(self):
        super().__init__()
        self._item_name = str(self._recipe) + "recipe"
        msg = ["A"]
        msg.append(random.choice(["tattered","yellowing"]))
        msg.append(random.choice(["vellum","papyrus","paper"]))
        msg.append("desribing the recipe for")
        msg.append(eng.indefinite_article(str(self._recipe)))
        msg.append(str(self._recipe))
        self._description = (" ").join(msg)

    @classmethod
    def recipe(cls):
        return cls._recipe

    def describe(self):
        return self._description
        


    def use(self, user):
        if hasattr(user, "learn_recipe"):
            user.learn_recipe(self._recipe, str(self._recipe))
        else:
            if hasattr(user, "message"):
                msg = "Your class, %s, cannot use this item!" % str(type(self))
                user.message(msg)
            else:
                pass

class IronSwordRecipeItem(RecipeItem):
    _recipe = recipes.iron_sword_recipe

    def use(self, user):
        super.use(user)

class SteelSwordRecipeItem(RecipeItem):
    _recipe = recipes.steel_sword_recipe

    def use(self, user):
        super.use(user)


    
class GatorBoneSwordRecipeItem(RecipeItem):
    _recipe = recipes.gator_bone_sword_recipe

    def use(self, user):
        super.use(user)

