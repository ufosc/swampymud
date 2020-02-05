"""module for easy text coloring via ANSI escape codes
Read more about ANSI escape codes here:
https://en.wikipedia.org/wiki/ANSI_escape_code

Escape codes are supported by most terminals. Most curses libraries by printing
these escape codes. You can accomplish this without a library like so:

>>> print("\\033[31mHello world!\\033[0m")

will print "Hello world!" in red. (Note that some users might have their 'red'
changed to another color.)

Key things to note:
All escape sequences the ASCII character 'ESC'
(ESC is encoded as 27 (decimal) / 0x1b (hex) / 033 (octal) )
In python3, you can write this as "\\x1b" or as "\\033"

For Control Sequence Introducer (CSI) commands, you write ESC [ (or "\\033[")
followed by some sort of code.

Finally, for Select Graphics Resolution (SGR) command, you write ESC[*m,
where *= arguments to the SGR command. The SGR command allows you to
change a variety of graphical settings.

Note that the support for each ANSI escape code varies widely from platform to
platform. We make the following recommendations:

For Windows CMD, this module will not work. Thus, for compatibility with all
clients, do not use this module.

Almost all terminal emulators support the basic 8 colors (both for backgrounds
and foregrounds) and some form of color inversion / video reverse.
For a bit of flair with a great deal of portability, use classes
Black, Red, Green, etc. for foreground colors, classes BlackBg, RedBg, GreenBg, etc.
for background colors, and the Reverse class to do color inverse.

Many terminal emulators support 'bold' / 'bright' colors, and underlining text.
Typically, at worst, these features are simply not rendered on unsupported
terminals. If interested, Use Underline and Bold classes. You can also use the
'Bright' colors (e.g. BrightRed, BrightGreen, BrightRedBG, etc.), however,
these are not part of the ANSI standard.

Many terminals also support 8-bit "256 color". You can use the Color8Bit and
Color256 classes for 256-color rendering.

Finally, some terminal emulators support 24-bit "true color", italics, framing,
and other more obscure SGR commands. However, wrappers for these escape codes
were not developed due to low demand. Make a pull request if you are interested.

If you are interested in what features your target platform supports, try
printing / sending the TEST_SGR string defined in this module.
"""
from abc import ABCMeta, abstractmethod

# the CSI command, ESC + [
CSI="\033["


class SGRFunction(metaclass = ABCMeta):
    '''Base class for other SGRFunctions
    Attempting to instantiate this class raises a TypeError'''

    def __init__(self, child):
        """initalize an SGRFunction call, wrapping around [child]
        note that [child] can either be another SGRFunction or some
        sort of string
        """
        self.child = child

    def iter_params(self):
        """iterate over all the SGR parameters
        in this stack of functions"""
        yield self.sgr_param
        try:
            yield from self.child.iter_params()
        except AttributeError:
            # hit the base content (a string with no 'params()' method)
            pass

    def content(self):
        """get the base content (a string) at the bottom of the stack"""
        try:
            return self.child.content()
        except AttributeError:
            # hits the base case, a string that IS the content
            return self.child

    def __add__(self, other):
        return str(self) + other

    def __radd__(self, other):
        return other + str(self)

    def __repr__(self):
        """overriding repr()"""
        return f"{type(self).__name__}({repr(self.child)})"

    def __str__(self):
        """overriding str()
        produces an ANSI-escaped message based on the content of this function"""
        # get a list of all sgr params
        params = ';'.join(self.iter_params())
        content = self.content()
        # return a string with
        # the SGR command with its params,
        # the content,
        # and the SGR command to reset the terminal
        return f"{CSI}{params}m{content}{CSI}0m"

    @property
    @abstractmethod
    def sgr_param(self):
        """Abstract method that returns the SGR parameter."""
        return NotImplemented

# note on bold / faint modes on windows cmd do not necessarily work properly
# essentially, they make the foreground color "bright"
# (this operation is also supported by CSI codes 90-97, but this is nonstandard)
# i.e.
# CSI 0 = reset
# CSI 1 = bold
# CSI 2 = should be 'faint', no effect
# CSI 21 = (should be 'bold off', has no effect
# CSI 22 = should be 'cancel faint / bold', cancels bold

class Bold(SGRFunction):
    sgr_param = "1"

class Italic(SGRFunction):
    """Makes text appear italic"""
    sgr_param = "3"

class Underline(SGRFunction):
    sgr_param = "4"

class Blink(SGRFunction):
    """makes text blink using the 'slow blink' SGR function"""
    sgr_param = "5"

class Reverse(SGRFunction):
    sgr_param = "7"

class CrossOut(SGRFunction):
    """the 'crossed out' SGR function"""
    sgr_param = "9"

# foreground colors
class Black(SGRFunction):
    sgr_param = "30"

class Red(SGRFunction):
    sgr_param = "31"

class Green(SGRFunction):
    sgr_param = "32"

class Yellow(SGRFunction):
    sgr_param = "33"

class Blue(SGRFunction):
    sgr_param = "34"

class Magenta(SGRFunction):
    sgr_param = "35"

class Cyan(SGRFunction):
    sgr_param = "36"

class White(SGRFunction):
    sgr_param = "37"

class Default(SGRFunction):
    """Displays text using the terminal's default foreground color"""
    sgr_param = "39"

# background colors
class BlackBG(SGRFunction):
    sgr_param = "40"

class RedBG(SGRFunction):
    sgr_param = "41"

class GreenBG(SGRFunction):
    sgr_param = "42"

class YellowBG(SGRFunction):
    sgr_param = "43"

class BlueBG(SGRFunction):
    sgr_param = "44"

class MagentaBG(SGRFunction):
    sgr_param = "45"

class CyanBG(SGRFunction):
    sgr_param = "46"

class WhiteBG(SGRFunction):
    sgr_param = "47"

class DefaultBG(SGRFunction):
    """Displays text using the terminal's default background color"""
    sgr_param = "49"

# display color from a 256-color palette
class Color256(SGRFunction):
    """Select a color from the palette of 256 colors"""

    def __init__(self, child, code):
        """Wrap [child] with a custom 256-color command.
        [code] must be a value in range [0,255]
        """
        if code not in range(256):
            raise ValueError("Expected code in range [0,255], "
                             f"received '{code}''")
        self.code = code
        super().__init__(child)

    @property
    def sgr_param(self):
        """returns the SGR command, including the 256-color code"""
        return f"38;5;{self.code}"


class ColorRGB(Color256):
    """Displays text with based on provided r, g, b values.
    Note that this uses the same SGR command as the Color256 class.
    """

    def __init__(self, child, r, g, b):
        """Color [child] according to the rgb palette,
        where r, g, b are in range [0,6]"""
        try:
            code = 16 + r * 36 + g * 6 + b
        except TypeError as exc:
            print(exc.args)
            for letter, value in zip(['r', 'g', 'b'], [r, g, b]):
                if not isinstance(value, int):
                    raise TypeError(f"Expected type int for '{letter}', "
                                    f"received '{type(value)}'") from exc
        super().__init__(child, code)

# constructing a series of SGR tests

# test for 8-bit background support
_list = [f"{CSI}37m"] # making text white to begin with

for _i in range(16):
    _list.append(f" {CSI}37;48;5;{_i}m{_i:^3}{CSI}0m ")

_list.append("\n")
for _j in range(6):
    _temp = []
    for _i in range(16,51):
        _i += _j * 36
        _temp.append(f" {CSI}37;48;5;{_i}m{_i:^3}{CSI}0m ")
    _list.append("".join(_temp))
    _list.append("\n")

for _i in range(232,256):
    _list.append(f" {CSI}37;48;5;{_i}m{_i:^3}{CSI}0m ")

TEST_8BIT_BG = "".join(_list)

# test for 8-bit foreground support
_list = [] # making text white to begin with
for _i in range(16):
    _list.append(f" {CSI}40;38;5;{_i}m{_i:^3}{CSI}0m ")

_list.append("\n")
for _j in range(6):
    _temp = []
    for _i in range(16, 51):
        _i += _j * 36
        _temp.append(f" {CSI}40;38;5;{_i}m{_i:^3}{CSI}0m ")
    _list.append("".join(_temp))
    _list.append("\n")

for _i in range(232, 256):
    _list.append(f" {CSI}40;38;5;{_i}m{_i:^3}{CSI}0m ")

TEST_8BIT_FG = "".join(_list)

# test for 24 bit 'true color' support
_list = [f"{CSI}37m"]
for _r in range(8):
    for _b in range(8):
        for _g in range(8):
            _list.append(f"{CSI}37;48;2;{_r};{_g};{_b}m{_r}{_g}{_b}{CSI}0m")
        _list.append("\n")
    _list.append("\n")

TEST_24BIT = "".join(_list)


TEST_SGR = f"""Testing basic 8 foreground colors.
Normal Bold   Faint  
{CSI}30mHello! {CSI}1;30mHello!{CSI}22m {CSI}2;30mHello!{CSI}0m 'black'
{CSI}31mHello! {CSI}1;31mHello!{CSI}22m {CSI}2;31mHello!{CSI}0m 'red'
{CSI}32mHello! {CSI}1;32mHello!{CSI}22m {CSI}2;32mHello!{CSI}0m 'green'
{CSI}33mHello! {CSI}1;33mHello!{CSI}22m {CSI}2;33mHello!{CSI}0m 'yellow'
{CSI}34mHello! {CSI}1;34mHello!{CSI}22m {CSI}2;34mHello!{CSI}0m 'blue'
{CSI}35mHello! {CSI}1;35mHello!{CSI}22m {CSI}2;35mHello!{CSI}0m 'magenta'
{CSI}36mHello! {CSI}1;36mHello!{CSI}22m {CSI}2;36mHello!{CSI}0m 'cyan'
{CSI}37mHello! {CSI}1;37mHello!{CSI}22m {CSI}2;37mHello!{CSI}0m 'white'
{CSI}39mHello! {CSI}1;39mHello!{CSI}22m {CSI}2;39mHello!{CSI}0m 'default'

Testing the basic 8 background colors.
Normal Bold   Faint  
{CSI}40mHello! {CSI}1;40mHello!{CSI}0m {CSI}2;40mHello!{CSI}0m 'black'
{CSI}41mHello! {CSI}1;41mHello!{CSI}0m {CSI}2;41mHello!{CSI}0m 'red'
{CSI}42mHello! {CSI}1;42mHello!{CSI}0m {CSI}2;42mHello!{CSI}0m 'green'{CSI}30m
{CSI}43mHello! {CSI}1;43mHello!{CSI}0m {CSI}2;43mHello!{CSI}0m 'yellow'
{CSI}44mHello! {CSI}1;44mHello!{CSI}0m {CSI}2;44mHello!{CSI}0m 'blue'
{CSI}45mHello! {CSI}1;45mHello!{CSI}0m {CSI}2;45mHello!{CSI}0m 'magenta'
{CSI}46mHello! {CSI}1;46mHello!{CSI}0m {CSI}2;46mHello!{CSI}0m 'cyan'{CSI}30m
{CSI}47mHello! {CSI}1;47mHello!{CSI}0m {CSI}2;47mHello!{CSI}0m 'white'
{CSI}49mHello! {CSI}1;49mHello!{CSI}0m {CSI}2;49mHello!{CSI}0m 'default'

Testing 'bright' colors. These are not part of the ANSI standard,
so don't feel bad if they don't work.
FG     BG
{CSI}90mHello! {CSI}30;100mHello!{CSI}0m 'bright black'
{CSI}91mHello! {CSI}30;101mHello!{CSI}0m 'bright red'
{CSI}92mHello! {CSI}30;102mHello!{CSI}0m 'bright green'
{CSI}93mHello! {CSI}30;103mHello!{CSI}0m 'bright yellow'
{CSI}94mHello! {CSI}30;104mHello!{CSI}0m 'bright blue'
{CSI}95mHello! {CSI}30;105mHello!{CSI}0m 'bright magenta'
{CSI}96mHello! {CSI}30;106mHello!{CSI}0m 'bright cyan'
{CSI}97mHello! {CSI}30;107mHello!{CSI}0m 'bright white'

Testing italics. (Note: This is often inverted or not supported.)
{CSI}3mThis should be italicized.{CSI}0m

Testing underline.
{CSI}4mThis should be underlined.{CSI}0m

Testing slow blink.
{CSI}5mThis should be blinking slowly.{CSI}0m

Testing rapid blink.
{CSI}6mThis should be blinking rapidly.{CSI}0m

Testing reverse video.
{CSI}7mThe colors of this should be inverted.{CSI}0m

Testing conceal.
{CSI}8mThese letters should be concealed.{CSI}0m

Testing crossed out.
{CSI}9mThese letters should be crossed out.{CSI}0m

Test framed.
{CSI}51mThis text should be framed.{CSI}0m

Test encircled.
{CSI}52mThis text should be encircled.{CSI}0m

Test overlined.
{CSI}52mThis text should be overlined.{CSI}0m

Now testing 8-bit color.
Foregrounds (all BG colors should be black).
{TEST_8BIT_FG}

Backgrounds (all FG colors should be white).
{TEST_8BIT_BG}

Now testing 256-bit color.
{TEST_24BIT}
"""
if __name__ == "__main__":
    print(TEST_SGR)
