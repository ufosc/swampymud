import entity
import character
import inventory
import random

# name_modifiers = ["Old", "Oak", "Birch", "Rusty", "Spruce", "Carved", "Pine"]
# Should the open/close state of a chest be global or be player specific?

class Chest(entity.Entity):

    def __init__(self, proper_name=None, items=[]):
        super().__init__(proper_name=proper_name)
        self.inv = inventory.Inventory()
        if items:
            for item in items:
                self.inv += item
        self._description = "A large wooden chest. Its hinges are caked with rust."
        # A list to keep track of the character who have opened the chest; stores their names
        self.opened = []

    def describe(self):
        return self._description 

    @entity.entity_command
    def open(self, character, args):
        ''' Open the chest and look inside at the contents'''
        msg = []
        if(str(character) not in self.opened):
            self.opened.append(str(character))
            msg.append("The chest opens with a creak.")
        # The following prints a formatted list of the chests contents
        msg.append("{:-^30}".format("Contents"))
        for item in self.inv:
            msg.append("{: ^30}".format(str(item)))
        msg.append("------------------------------")
        character.message("\n".join(msg))

    @entity.entity_command
    def take(self, character, args):
        ''' Take an item from the chest 
        Usage: take [item name]'''
        # TODO: implement removing items from the chest
        item_name = " ".join(args[1:])
        if(str(character) in self.opened):
            success = False
            target_item = self.inv.find(item_name)
            if(target_item):
                try:
                    character.inv += target_item
                    self.inv -= target_item
                    success = True
                except:
                    pass
            if(success):
                character.message("You took %s from the chest." % item_name)
            else:
                character.message("You couldn't find that item in the chest's contents.")
        else:
            character.message("The chest is closed.")

    @entity.entity_command
    def close(self, character, args):
        ''' Close the chest '''
        if(str(character) in self.opened):
            self.opened.remove(str(character))
            character.message("You close the chest with a thud.")
        else:
            character.message("The chest is already closed.")

    @entity.entity_command
    def add(self, character, args):
        ''' Add an item to the chest
        Usage: add [item name] '''
        item_name = " ".join(args[1:])
        foundItem = False
        if(str(character) in self.opened):
            success = False
            try:
                target_item = character.inv.find(item_name)
                if(target_item):
                    try:
                        character.inv -= target_item
                        self.inv += target_item
                        success = True
                        foundItem = bool(target_item)
                    except:
                        pass
            except:
                pass
            if(success):
                character.message("You put %s in the chest." % item_name)
            else:
                if not (foundItem):
                    character.message("You couldn't find that item in your inventory.")
                else:
                    character.message("You can't add that to the chest!")
        else:
            character.message("The chest is closed.")

        


