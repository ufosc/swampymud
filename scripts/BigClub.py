import item

class BigClub(item.EquippableBase):
    target = item.EquipTarget("Hand")
    item.item_type = "item type"
    item.name = "BigClub"
    
    def equip(self, character):
        character.message("This club is heavy!")
    
    def unequip(self, character):
        pass
