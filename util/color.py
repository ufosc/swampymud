"""module for easy text coloring via ANSI escape codes
Read more about ANSI escape codes here:
https://en.wikipedia.org/wiki/ANSI_escape_code

Key things to note:
All escape sequences the ASCII character 'ESC'
(ESC is encoded as 27 (decimal) / 0x1b (hex) / 033 (octal) )
In python3, you can write this as "x1b" or as "\033"

For "Control Sequence Introducer" commands, you write ESC [ (or "\033[")
followed by some sort of code.

Here, we focus on the normal 16-colors supported by most servers.
"""
