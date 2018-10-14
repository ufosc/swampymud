from character import Character


def meow_hash(word):
    output = ""
    for bit in str(bin(hash(word))):
        if bit == "1":
            output += "meow"
        else:
            output += "raow"
    return output

    

class Cat(Character):
    def cmd_say(self, args):
        args = " ".join([meow_hash(word) for word in args.split(" ")])
        super().cmd_say(args)