import item

class Sword(item.EquippableBase):
    _item_name = "Sword"
    target = item.EquipTarget("Hands")
    def __init__(self):
        self.eqc = 0
        self.uqc = 0

    def equip(self, character):
        print("%s equipped %s! %s" % (character, self.name, self.eqc))
        self.eqc +=1

    def unequip(self, character):
        print("%s unequipped %s! %s" % (character, self.name, self.uqc))
        self.uqc += 1
