from scripts.basic_rpg import Humanoid

class Paladin(Humanoid):
    ''' Master craftsman, paladins use their knowledge of mechanical
    engineering and materials to craft, and use, the finest weapons
    and armor '''

    def __init__(self):
        super().__init__()

    def cmd_craft(self, args):
        ''' Craft an item 
        Usage: craft [material] [item]
        '''
        if len(args) < 2:
            return
        for 