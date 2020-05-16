'''defines the Cat class'''
from character import Character

MEOW_DICT = {
    '0' : "meow",
    '1' : "raow",
    '2' : "roaow",
    '3' : "meoow",
    '4' : "maow",
    '5' : "meow? ",
    '6' : "meow... ",
    '7' : "miao",
    '8' : "mraow",
    '9' : "bao",
    'a' : "meeow",
    'b' : "reeow",
    'c' : "ow",
    'd' : "meow-meow",
    'e' : "meow! ",
    'f' : "oww"
}

def meow_hash(player, message):
    meow_hashed = ""
    converted  = "".join([str(hex(ord(x)))[2::] for x in message])
    for num in converted:
        meow_hashed += MEOW_DICT[num]
    return meow_hashed


class Cat(Character):
    def cmd_say(self, *args):
        if args:
            hashed = meow_hash(self, args[0])
            super().cmd_say(hashed)
