from item import UsableBase
import scripts.recipes as recipes
import random
import util.english as eng
import character

class RecipeItem(UsableBase):

    _recipe = recipes.iron_sword_recipe

    def __init__(self):
        super().__init__()
        self._item_name = str(self._recipe) + " Recipe"
        self._item_name.title()
        msg = ["A"]
        msg.append(random.choice(["tattered","yellowing"]))
        msg.append(random.choice(["vellum","papyrus","paper"]))
        msg.append("scroll desribing the recipe for")
        msg.append(eng.indefinite_article(str(self._recipe)))
        msg.append(str(self._recipe))
        self._description = (" ").join(msg)

    @classmethod
    def recipe(cls):
        return cls._recipe

    def use(self, target, user):
        try:
            target.learn_recipe(self._recipe, str(self._recipe))
        except:
            try:
                msg = "{} {} cannot be used on {} {}".format(eng.indefinite_article(str(self)),str(self),eng.indefinite_article(str(type(target))),str(type(target)))
                user.message(msg)
            except:
                pass

# use() must be defined explicitly in the following classes becuase the Usable metaclass forces a method
# by the use() name to exist in its namespace.
# TODO: Fix this^ in future update, so use() is inherited

class IronSwordRecipeItem(RecipeItem):
    _recipe = recipes.iron_sword_recipe

    def use(self, target, user):
        try:
            target.learn_recipe(self._recipe, str(self._recipe))
        except:
            try:
                msg = "{} {} cannot be used on {} {}".format(eng.indefinite_article(str(self)),str(self),eng.indefinite_article(str(type(target))),str(type(target)))
                user.message(msg)
            except:
                pass

class SteelSwordRecipeItem(RecipeItem):
    _recipe = recipes.steel_sword_recipe

    def use(self, target, user):
        try:
            target.learn_recipe(self._recipe, str(self._recipe))
        except:
            try:
                msg = "{} {} cannot be used on {} {}".format(eng.indefinite_article(str(self)),str(self),eng.indefinite_article(str(type(target))),str(type(target)))
                user.message(msg)
            except:
                pass

class GatorBoneSwordRecipeItem(RecipeItem):
    _recipe = recipes.gator_bone_sword_recipe

    def use(self, target, user):
        try:
            target.learn_recipe(self._recipe, str(self._recipe))
        except:
            try:
                msg = "{} {} cannot be used on {} {}".format(eng.indefinite_article(str(self)),str(self),eng.indefinite_article(str(type(target))),str(type(target)))
                user.message(msg)
            except:
                pass

