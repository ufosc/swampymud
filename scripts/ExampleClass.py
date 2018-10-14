from character import Character

class ExampleClass(Character):
    def cmd_echo(self, args):
        '''Echoes the provided phrase back.
        usage: example [phrase]
        '''
        self.message(args)
        
    def cmd_me(self, args):
        '''Illustrate an action of a character
		usage me [phrase]
        '''
        self.location.message_chars("*%s %s" % (self,args))
        