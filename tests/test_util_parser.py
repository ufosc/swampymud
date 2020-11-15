import unittest
import itertools
from swampymud.util import parser
from swampymud import item, character
from swampymud._types import (GameObject, Location, Exit, Item,
                              Character, Entity)
from swampymud.util.parser import (Grammar, Keyword, Variable, Group, Star,
                                   Plus, Optional, GrammarError)


class NamedItem(item.Item):
    """Simple item for testing commands"""

    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"NamedItem({self.name!r})<{hash(self)}>"

class DreadZombie(character.Character):

    def __init__(self, id):
        self.id = id
        super().__init__("Dread Zombie")

    def __repr__(self):
        return f"DreadZombie({self.id})"


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


    def test_gammar_parser(self):
        # convenience function
        def compare(inp, output):
            self.assertEqual(Grammar.from_string(inp), output)
        compare("foo", Group(Keyword("foo")))
        compare("foo bar", Group(Keyword("foo"), Keyword("bar")))
        compare("foo (bar (baz) bok)",
                Group(Keyword("foo"),
                      Group(Keyword("bar"),
                            Group(Keyword("baz")),
                            Keyword("bok"))))
        compare("foo | bar",
                Group(alts=[[Keyword("foo")], [Keyword("bar")]]))
        compare("foo | ITEM",
                Group(alts=[[Keyword("foo")], [Variable(Item)]]))
        compare("foo?",
                Group(Optional(Keyword("foo"))))
        compare("foo*",
                Group(Star(Keyword("foo"))))
        compare("foo+",
                Group(Plus(Keyword("foo"))))
        compare("give ITEM to? ( ENTITY | CHARACTER )",
                Group(Keyword("give"),
                      Variable(Item),
                      Optional(Keyword("to")),
                      Group(alts=[[Variable(Entity)],
                                  [Variable(Character)]])))
        compare("put (ENTITY | ITEM down?)",
                Group(Keyword("put"),
                      Group(alts=[
                          [Variable(Entity)],
                          [Variable(Item), Optional(Keyword("down"))]
                      ])))

    def test_grammar_error(self):
        # convenience functions for comparing errors
        def test_error(inp, description):
            self.assertRaisesRegex(GrammarError, description,
                                   Grammar.from_string, inp)

        def test_hint(inp, hint):
            with self.assertRaises(GrammarError):
                try:
                    Grammar.from_string(inp)
                except GrammarError as ge:
                    self.assertEqual(ge.hint(), hint)
                    raise ge

        def test_highlight(inp, highlight):
            with self.assertRaises(GrammarError):
                try:
                    Grammar.from_string(inp)
                except GrammarError as ge:
                    self.assertEqual(ge.highlight(), highlight)
                    raise ge

        test_error("", "Empty group at index 0")
        test_error("()", "Empty group at index 1")
        test_error("foo - bar", "Unrecognized token '-'")
        test_error("(foo]", "Unrecognized token ']'")
        test_error("foo Bar", "Unrecognized token 'Bar'")
        test_error("foo (bar", r"Unmatched '\('")
        test_error("foo bar)", r"Unmatched '\)' at index 7")
        test_error("bim (foo (bar)))", r"Unmatched '\)' at index 15")
        test_error("bim+?*", r"Unexpected quantifier '\?' at 4")
        test_error("bim+*", r"Unexpected quantifier '\*' at 4")
        test_error("foo (+)", r"Quantifier '\+' has no preceding predicate")
        test_error("*", r"Quantifier '\*' has no preceding predicate")
        test_error("foo (bar|*)", r"Quantifier '\*' has no preceding predicate")
        test_error("foo (bar| )", "Expected an alternative before index 10")
        test_error("   |", "Expected an alternative before index 3")
        test_error("foo ( bar ( baz())))", "Empty group at index 16")
        test_error("foo BAR", "Unknown type 'BAR' at index 4")

        test_hint("", "grammars must contain at least one keyword or variable")
        test_hint("()", "groups cannot be empty. '()' matches nothing")
        test_hint("foo - bar", "the only supported operations are |, *, +, and ?")
        test_hint("(foo]", "did you mean to use a ')' instead?")
        test_hint("foo Bar", "use lowercase for keywords and uppercase for variables")
        test_hint("foo ((bar", "add 2 ')' ")
        paren_hint = "did you forget a '(' earlier in your grammar?"
        test_hint("foo bar)", paren_hint)
        test_hint("bim (foo (bar)))", paren_hint)
        quant_hint = r"you can only apply one quantifier (*, +, ?) to keyword/variable/group"
        test_hint("bim+?*", quant_hint)
        test_hint("bim+*", quant_hint)
        pred_hint = "there should be a keyword/variable/group before this quantifier"
        test_hint("foo (+)", pred_hint)
        test_hint("*", pred_hint)
        test_hint("foo (bar|*)", pred_hint)
        alt_hint = ("alternatives cannot be empty. Grammars like (foo | ) "
                    "are invalid,\n       "
                    "there should be something before and after that '|'")
        test_hint("foo (bar| )", alt_hint)
        test_hint("   |", alt_hint)
        test_hint("foo ( bar ( baz())))",
                  r"groups cannot be empty. '()' matches nothing")
        test_hint("foo BAR",
                   f"type must be one of {','.join(Grammar.DEFAULT_TYPES)}")

        from swampymud.util.color import Red, Underline
        # convenience function for making red underlines
        def ru(string):
            return str(Red(Underline(string)))

        test_highlight("()", f"{ru('()')}")
        test_highlight("foo - bar",  f"foo {ru('-')} bar")
        test_highlight("(foo]", f"(foo{ru(']')}")
        test_highlight("foo Bar", f"foo {ru('Bar')}")
        lp, rp = (ru("(")), ru(")")
        test_highlight("foo (bar", f"foo {lp}bar")
        test_highlight("((foo (bar)", f"{lp}{lp}foo {lp}bar{rp}")
        test_highlight("foo bar)", f"foo bar{rp}")
        test_highlight("bim (foo (bar)))", f"bim (foo (bar)){rp}")
        test_highlight("bim+?*", f"bim+{ru('?')}*")
        test_highlight("bim+*", f"bim+{ru('*')}")
        test_highlight("foo ( +)", f"foo {ru('( +')})")
        test_highlight("*", ru('*'))
        test_highlight("foo (bar|*)", f"foo (bar{ru('|*')})")
        test_highlight("foo (bar| )", f"foo (bar{ru('| )')}")
        test_highlight("   |", ru("   |"))
        test_highlight("foo ( bar ( baz())))", f"foo ( bar ( baz{ru('()')})))")
        test_highlight("foo BAR", f"foo {ru('BAR')}")


    def test_match(self):
        def assert_match(grammar, inp):
            self.assertTrue(grammar.matches(parser.split_args(inp)))

        def assert_no_match(grammar, inp):
            self.assertFalse(grammar.matches(parser.split_args(inp)))

        grammar = Keyword("foo")
        assert_match(grammar, "foo")
        assert_no_match(grammar, "foo foo")
        assert_no_match(grammar, "foofoo")
        assert_no_match(grammar, "baz")
        assert_no_match(grammar, "")

        grammar = Optional(Keyword("foo"))
        assert_match(grammar, "")
        assert_match(grammar, "foo")
        assert_no_match(grammar, "foo foo")
        assert_no_match(grammar, "baz")

        grammar = Star(Keyword("baz"))
        assert_match(grammar, "")
        assert_match(grammar, "baz")
        assert_match(grammar, "baz baz baz baz baz")
        assert_match(grammar, "baz baz baz baz baz baz")
        assert_no_match(grammar, "baz foo baz")
        assert_no_match(grammar, "foo baz baz")
        assert_no_match(grammar, "baz baz foo")

        grammar = Plus(Keyword("bing"))
        assert_match(grammar, "bing")
        assert_match(grammar, "bing bing")
        assert_match(grammar, "bing bing bing bing bing")
        assert_match(grammar, "bing bing bing bing bing bing")
        assert_no_match(grammar, "")
        assert_no_match(grammar, "bing baz")
        assert_no_match(grammar, "bi ng")
        assert_no_match(grammar, "bing bing bing baz")
        assert_no_match(grammar, "bing baz bing bing")
        assert_no_match(grammar, "foo foo foo")

        # variables match any multiple words
        grammar = Variable("ITEM")
        assert_match(grammar, "foo")
        assert_match(grammar, "foo bar baz")
        assert_match(grammar, "foo baz fsdfdasf f sdaf s")
        assert_no_match(grammar, "")

        # star of a variable can match any number of variables multiple times
        grammar = Star(Variable("ITEM"))
        assert_match(grammar, "")
        assert_match(grammar, "foo")
        assert_match(grammar, "foo bar baz")
        assert_match(grammar, "foo baz fsdfdasf f sdaf s")

        grammar = Group(Keyword("foo"), Keyword("bar"))
        assert_match(grammar, "foo bar")
        assert_no_match(grammar, "foo")
        assert_no_match(grammar, "bar")
        assert_no_match(grammar, "foo bar baz")
        assert_no_match(grammar, "bar foo")
        assert_no_match(grammar, "")

        # unions can match one or the other
        # "look (up | down)"
        grammar = Group(Keyword("look"),
                        Group(alts=[[Keyword("up")], [Keyword("down")]]))
        assert_match(grammar, "look up")
        assert_match(grammar, "look down")
        assert_no_match(grammar, "look")
        assert_no_match(grammar, "up")
        assert_no_match(grammar, "down")
        assert_no_match(grammar, "give up")
        assert_no_match(grammar, "give down")
        assert_no_match(grammar, "give")
        assert_no_match(grammar, "look around")

        # finally, a complex example
        # "give ITEM to? (ENTITY | CHARACTER)"
        grammar = Group(Keyword("give"),
                        Variable("ITEM"),
                        Optional(Keyword("to")),
                        Group(alts=[[Variable("ENTITY")], [Variable("CHARACTER")]]))
        assert_match(grammar, "give red sword to bob")
        # this matches, assuming 'to' is an Entity / Character
        assert_match(grammar, "give red sword to")
        assert_match(grammar, "give red sword to james the epic wizard")
        assert_match(grammar, "give foo to bar")
        # give an item named 'give' to a character / entity named 'give'
        assert_match(grammar, "give give give")
        assert_match(grammar, "give give to give")
        assert_no_match(grammar, "give")
        assert_no_match(grammar, "give to")
        assert_no_match(grammar, "give give")
        assert_no_match(grammar, "")

    def test_interpret(self):

        def test_interp(grammar, inp, ctx, expected):
            self.assertCountEqual(
                grammar.interpret(parser.split_args(inp), ctx),
                expected
            )

        def test_error(grammar, inp, ctx, err):
            self.assertRaisesRegex(
                parser.ParseError, err,
                grammar.interpret, parser.split_args(inp), ctx
            )

        def product(*iterables):
            """return the cartesian product of iterables, but with a
            list of lists instead of a list of tuples
            """
            return [ list(p) for p in itertools.product(*iterables) ]

        # some objects for a context
        sword = NamedItem("sword")
        shield = NamedItem("shield")
        coin1 = NamedItem("coin")
        coin2 = NamedItem("coin")
        bill = character.Character("Bill")
        loquax = character.Character("Loquax")
        loquax2 = character.Character("Loquax")
        grog = character.Character("GROG")
        game_obj = [sword, shield, coin1, coin2,
                    bill, loquax, loquax2, grog]

        g = Grammar.from_string("throw ITEM (at CHARACTER)?")
        # if no objects are in the context, we will get no results
        test_interp(g, "throw sword", ctx=game_obj,
                    expected=[[sword]])

        test_interp(g, "throw sword at bill", ctx=game_obj,
                    expected=[[sword, bill]])
        test_interp(g, "throw shield at bill", ctx=game_obj,
                    expected=[[shield, bill]])
        test_interp(g, "throw ShIEld at bill", ctx=game_obj,
                    expected=[[shield, bill]])
        test_interp(g, "throw ShIEld at BILL", ctx=game_obj,
                    expected=[[shield, bill]])
        test_interp(g, "throw coin at BILL", ctx=game_obj,
                    expected=[[coin1, bill], [coin2, bill]])
        test_interp(g, "throw coin at grOg", ctx=game_obj,
                    expected=[[coin1, grog], [coin2, grog]])
        test_interp(g, "throw shield at loquax", ctx=game_obj,
                    expected=[[shield, loquax], [shield, loquax2]])
        test_interp(g, "throw coin at loquax", ctx=game_obj,
                    expected=[[coin1, loquax], [coin2, loquax],
                              [coin1, loquax2], [coin2, loquax2]])
        # new scenario: a lot of zombies
        zombies = [DreadZombie(i) for i in range(10)]

        g = Grammar.from_string("attack CHARACTER*")
        test_interp(g, "attack", ctx=zombies,
                    expected=[[]])
        test_interp(g, "attack dread zombie", ctx=zombies,
                    expected=[[z] for z in zombies])
        test_interp(g, "attack dread zombie dread zombie", ctx=zombies,
                    expected=product(zombies, zombies))

        # new scenario: a lot of confusing names
        dread = character.Character("dread")
        zombie = character.Character("zombie")
        dread_zombie = DreadZombie(0)
        confusing = [dread, zombie, dread_zombie]
        test_interp(g, "attack", ctx=confusing,
                    expected=[[]])
        test_interp(g, "attack dread zombie", ctx=confusing,
                    expected=[[dread_zombie], [dread, zombie]])
        test_interp(g, "attack dread zombie dread zombie", ctx=confusing,
                    expected=[[dread_zombie, dread_zombie],
                              [dread_zombie, dread, zombie],
                              [dread, zombie, dread_zombie],
                              [dread, zombie, dread, zombie]])
        # using quotes should help make things clear
        test_interp(g, "attack 'dread zombie'", ctx=confusing,
                    expected=[[dread_zombie]])
        test_interp(g, "attack dread zombie 'dread zombie'", ctx=confusing,
                    expected=[[dread_zombie, dread_zombie],
                              [dread, zombie, dread_zombie]])
