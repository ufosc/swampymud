import unittest
from swampymud.util import parser

class TestParser(unittest.TestCase):

    def test_split_args(self):
        # convenience function for testing
        def compare(inp, output):
            self.assertListEqual(parser.split_args(inp), output)

        compare('equip epic sword', ['equip', 'epic', 'sword'])
        # quoting words should make them one token
        compare('equip "epic sword"', ['equip', 'epic sword'])
        compare('give "cool sword" to "bill the wizard"',
                ['give', 'cool sword', "to", "bill the wizard"])
        # you can use single or double quotes, or mix and match them
        compare("equip 'epic sword'", ['equip', 'epic sword'])
        compare('give "cool sword" to \'bill the wizard\'',
                ['give', 'cool sword', "to", "bill the wizard"])
        # using ' in the middle of a "-quoted token will not close it...
        compare('equip "bill\'s sword', ['equip', "bill's sword"])
        #... and visa versa
        compare('say \'The wizard told me, "Go find the gemstone."\'',
                ['say', 'The wizard told me, "Go find the gemstone."'])

        # repeated whitespace is just skipped
        compare("hey     there  \n how are\r\r\ryou",
                ["hey", "there", "how", "are", "you"])
        compare("equip\t'epic sword'", ['equip', 'epic sword'])
        # but whitespace within quotes is preserved
        compare("equip\t'epic\tsword'", ['equip', 'epic\tsword'])
        compare("equip  'epic  sword'", ['equip', 'epic  sword'])

        # quotes within a token are simply passed along
        compare("say what's up?",
                ["say", "what's", "up?"])

        # empty tokens are permissible
        compare("", [])
        compare("say ''", ["say", ''])

        # finally, unterminated quotes create a token that lasts until
        # the end of the line
        compare("say 'who is that?",
                ["say", "who is that?"])
        compare('hey whoops I "forgot to close this quote',
                ["hey", "whoops", "I", "forgot to close this quote"])
