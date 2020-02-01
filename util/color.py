"""module for easy text coloring via ANSI escape codes
Read more about ANSI escape codes here:
https://en.wikipedia.org/wiki/ANSI_escape_code

Escape codes are supported by most terminals. Most curses libraries by printing
these escape codes. You can accomplish this without a library like so:

>>> print("\033[31mHello world!\033[0m")
will print "Hello world!" in red. (Note that some users might have their 'red'
changed to another color.)

Key things to note:
All escape sequences the ASCII character 'ESC'
(ESC is encoded as 27 (decimal) / 0x1b (hex) / 033 (octal) )
In python3, you can write this as "\x1b" or as "\033"

For Control Sequence Introducer (CSI) commands, you write ESC [ (or "\033[")
followed by some sort of code.

Finally, for Select Graphics Resolution (SGR) command, you write ESC[*m,
where *=arguments to the SGR command. The SGR command allows you to 

Here, we focus on the normal 16-colors supported by most servers.
"""

# the CSI command, ESC + [
CSI="\033["


# note on bold / faint modes on windows cmd do not necessarily work properly
# essentially, they make the foreground color "bright"
# (this operation is also supported by CSI codes 90-97, but this is nonstandard)
# i.e.
# CSI 0 = reset
# CSI 1 = bold
# CSI 2 = should be 'faint', no effect
# CSI 21 = (should be 'bold off', has no effect
# CSI 22 = should be 'cancel faint / bold', cancels bold


_temp_list = [f"{CSI}37m"] # making text white to begin with

for _i in range(16):
    _temp_list.append(f" {CSI}37;48;5;{_i}m{_i:^3}{CSI}0m ")

_temp_list.append("\n")
for _j in range(6):
    _temp = []
    for _i in range(16,51):
        _i += _j * 36
        _temp.append(f" {CSI}37;48;5;{_i}m{_i:^3}{CSI}0m ")
    _temp_list.append("".join(_temp))
    _temp_list.append("\n")

for _i in range(232,256):
    _temp_list.append(f" {CSI}37;48;5;{_i}m{_i:^3}{CSI}0m ")

TEST_8BIT_BG = "".join(_temp_list)


_temp_list = [] # making text white to begin with
for _i in range(16):
    _temp_list.append(f" {CSI}40;38;5;{_i}m{_i:^3}{CSI}0m ")

_temp_list.append("\n")
for _j in range(6):
    _temp = []
    for _i in range(16,51):
        _i += _j * 36
        _temp.append(f" {CSI}40;38;5;{_i}m{_i:^3}{CSI}0m ")
    _temp_list.append("".join(_temp))
    _temp_list.append("\n")

for _i in range(232,256):
    _temp_list.append(f" {CSI}40;38;5;{_i}m{_i:^3}{CSI}0m ")

TEST_8BIT_FG = "".join(_temp_list)


TEST_24BIT_BG = ""

for r in range(8):
    for b in range(8):
        for g in range(8):
            TEST_24BIT_BG += f"{CSI}37;48;2;{r};{g};{b}m{r}{g}{b}{CSI}0m "
        TEST_24BIT_BG += "\n"
    TEST_24BIT_BG += "\n"


SGR_TEST = f"""Testing basic 8 foreground colors.
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
{TEST_24BIT_BG}
"""



print(SGR_TEST)
