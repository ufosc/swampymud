import material
from item import MiscItemBase
import util.english as english
import util.misc as misc

class MaterialItem(MiscItemBase):
    ''' Misceallenous items which have a material member. All subclasses of material item
    should have a material corresponding to their in-game significance '''
    _material = material.default_material
    _description = "A material item"

    def __init__(self):
        super().__init__()
        self._item_name = str(type(self))

    @classmethod
    def material(cls):
        return cls._material

class IronIngot(MaterialItem):
    _material = material.iron
    _description = "An iron ingot"

class WoodPlank(MaterialItem):
    _material = material.wood

class SteelIngot(MaterialItem):
    _material = material.steel
    _description = "A steel ingot"

class GatorBoneShard(MaterialItem):
    _material = material.gatorbone
    _description = "A shard of alligator bone"
