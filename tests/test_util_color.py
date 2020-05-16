"""unit tests for the color module"""
import unittest
import swampymud.util.color as col

class TestSGRCommand(unittest.TestCase):
    """test case for basic features of SGRCommand functionality"""

    def setUp(self):
        self.red_hello = col.Red("Hello world")
        self.red_3 = col.Red(3)
        self.green_hello = col.Green("Hello world")
        self.nested_red = col.Underline(col.Red("pizza pie"))
        self.bold_default = col.Bold(col.Default("hi there"))
        self.bold_under_yellowbg = col.Bold(
            col.Underline(
                col.YellowBG("heavy formatting")
                )
            )


    def test_repr(self):
        """calling repr on a SGRCommand should simply return a representation
        similar to the call stack used to create it"""
        self.assertEqual(repr(self.red_hello), "Red('Hello world')")
        self.assertEqual(repr(self.red_3), "Red(3)")
        self.assertEqual(repr(self.green_hello), "Green('Hello world')")
        self.assertEqual(repr(self.nested_red), "Underline(Red('pizza pie'))")
        self.assertEqual(repr(self.bold_default), "Bold(Default('hi there'))")
        self.assertEqual(repr(self.bold_under_yellowbg),
                         "Bold(Underline(YellowBG('heavy formatting')))")

    def test_content(self):
        """test that nested SGRFunctions implement 'content' correctly"""
        self.assertEqual(self.red_hello.content(), "Hello world")
        self.assertEqual(self.red_3.content(), 3)
        self.assertEqual(self.green_hello.content(), "Hello world")
        self.assertEqual(self.nested_red.content(), "pizza pie")
        self.assertEqual(self.bold_default.content(), "hi there")
        self.assertEqual(self.bold_under_yellowbg.content(),
                         "heavy formatting")

    def test_escapes(self):
        """test that ANSI escapes can be properly accessed via iter_params"""
        self.assertEqual(list(self.red_hello.iter_params()), ["31"])
        self.assertEqual(list(self.red_3.iter_params()), ["31"])
        self.assertEqual(list(self.green_hello.iter_params()), ["32"])
        self.assertEqual(list(self.nested_red.iter_params()), ["4", "31"])
        self.assertEqual(list(self.bold_default.iter_params()), ["1", "39"])
        self.assertEqual(list(self.bold_under_yellowbg.iter_params()),
                         ["1", "4", "43"])

    def test_str(self):
        """test that SGRCommands appear correctly"""
        self.assertEqual(str(self.red_hello), "\033[31mHello world\033[0m")
        self.assertEqual(str(self.red_3), "\033[31m3\033[0m")
        self.assertEqual(str(self.green_hello), "\033[32mHello world\033[0m")
        self.assertEqual(str(self.nested_red),
                         "\033[4;31mpizza pie\033[0m")
        self.assertEqual(str(self.bold_default),
                         "\033[1;39mhi there\033[0m")
        self.assertEqual(str(self.bold_under_yellowbg),
                         "\033[1;4;43mheavy formatting\033[0m")

    def test_add(self):
        """test that two different strings or SGRCommands can be
        concatenated using '+'"""
        # trying to concatenate a SGRCommand with a non-string character
        # should raise a TypeError
        with self.assertRaises(TypeError):
            _ = self.red_3 + 3
        # should fail both ways
        with self.assertRaises(TypeError):
            _ = 3 + self.red_3
        # test that two SGRCommands can be concatenated
        self.assertEqual(self.red_hello + self.red_3,
                         "\033[31mHello world\033[0m\033[31m3\033[0m")
        # test that an SGRCommand can be concatenated with a string
        self.assertEqual(self.nested_red + " unformatted",
                         "\033[4;31mpizza pie\033[0m unformatted")
        # test the reverse
        self.assertEqual("unformatted " + self.nested_red,
                         "unformatted \033[4;31mpizza pie\033[0m")



class TestColor256(unittest.TestCase):
    """test that the escape codes work properly for the Color256
    and ColorRGB commands"""

    def setUp(self):
        self.pink = col.Color256("pink", code=170)
        self.pink8 = col.ColorRGB("pink2", r=4, g=2, b=0)

    def test_sgr_param(self):
        """test that 256-color commands produce the correct
        modified SGR parameters"""
        self.assertEqual(self.pink.sgr_param, "38;5;170")
        self.assertEqual(self.pink8.sgr_param, "38;5;172")

    def test_value_error(self):
        """test that 256 color commands produce errors when given values
        outside of 256"""
        with self.assertRaises(ValueError,
                               msg="Expected value in range [0,255]; received"
                               "'-13'"):
            _ = col.Color256("foo", -13)
        with self.assertRaises(ValueError,
                               msg="Expected value in range [0,255]; received"
                               "'-13'"):
            _ = col.Color256("foo", 256)
        # test that all other values are fine
        # this should not raise an exception
        for i in range(256):
            _ = col.Color256("foo", i)

        with self.assertRaises(ValueError,
                               msg="Expected value in range [0,5]; for letter"
                               " 'g'; received '-1'"):
            _ = col.ColorRGB("foo", r=0, g=-1, b=0)
        with self.assertRaises(ValueError,
                               msg="Expected value in range [0,5]; for letter"
                               " 'b'; received '10'"):
            _ = col.ColorRGB("foo", r=0, g=0, b=10)
        # test that all other values are fine
        for r in range(6):
            for g in range(6):
                for b in range(6):
                    _ = col.ColorRGB("f", r=r, g=g, b=b)

    def test_type_error(self):
        """test that type errors are properly detected"""
        with self.assertRaises(TypeError, msg="Expected type int for 'b'; "
                                              "received <class 'str'>"):
            _ = col.ColorRGB("foo", 3, 4, "apple")
