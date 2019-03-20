from scripts.basic_rpg import Humanoid

class Healer(Humanoid):
    '''Students of the medical arts, healers seek to master
    knowledge of the biological and medical sciences to help others'''

    def __init__(self):
        super().__init__()
        # The following creates a dictionary which maps spell names to the function
        self.spells = {}
        for func in dir(self):
            if func.startswith("spell_"):
                self.spells[func[6::]] = getattr(self, func)
    
    def cmd_cast(self, args):
        '''Cast a spell
        Usage: cast [spell] [player/entity]
        '''
        if len(args) < 1:
            return
        if args[1] in self.spells:
            self.spells[args[1]](args[2])
        else:
            self.message("Could not find a spell with name %s." % args[0])

    # TODO: Message the user after a heal is successful
    def spell_heal(self, *args):
        ''' Heals the target for 10 points
        Usage: cast heal [player/entity]
        '''
        if len(args) < 1:
            return
        for char in self.location.characters:
            if args[0] == char.name:
                break
        else:
            self.message("Could not find player with name %s." % args[0])
            return
        # if we get to this point, then we healed someone
        try:
            char.health += 10
        except:
            self.location.message_chars("%s tried to heal %s, to no avail." % (self, char))