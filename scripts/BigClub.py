import item

class BigClub(item.EquippableBase):
    target = item.EquipTarget("Hand")
    
    def equip(self, character):
        character.message("This club is heavy!")
    
    def unequip(self, character):
        pass
