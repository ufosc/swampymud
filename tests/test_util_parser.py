import unittest
from swampymud.util import parser
from swampymud.util.parser import Keyword, Variable, Group, Star, Plus, Optional

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


    def gammar_parser(self):
        # convenience function
        def compare(inp, output):
            self.assertEqual(parser.with_grammar(inp), output)
        compare("foo", Group(Keyword("foo")))
        compare("foo bar", Group(Keyword("foo bar")))
        compare("foo (bar (baz) bok)",
                Group(Keyword("foo"),
                      Group(Keyword("bar"),
                            Group(Keyword("baz")),
                            Keyword("Bok"))))
        compare("foo | bar",
                Group(alts=[[Keyword("foo")], [Keyword("bar")]]))
        compare("foo | ITEM",
                Group(alts=[[Keyword("foo")], [Variable("ITEM")]]))
        compare("foo?",
                Group(Optional("foo")))
        compare("foo*",
                Group(Star("foo")))
        compare("foo+",
                Group(Plus("foo")))
        compare("give ITEM to? ( ENTITY | CHARACTER )",
                Group(Keyword("give"),
                      Variable("ITEM"),
                      Optional(Keyword("to")),
                      Group(alts=[[Variable("ENTITY")],
                                  [Variable("CHARACTER")]])))

        compare("put (ENTITY | ITEM down?)",
                Group(Keyword("put"),
                      Group(alts=[
                          [Variable("ENTITY")],
                          [Variable("Item"), Optional(Keyword("down"))]
                      ])))

        # TODO: test all the errors and make a better exception
