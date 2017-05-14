#!/usr/bin/python3

# Window Sizes
BORDERS     = 2
WIN_REG_H   = 8
WIN_REG_W   = 9*4 + BORDERS
WIN_STACK_W = 11  + BORDERS
WIN_INSTR_W = 16  + BORDERS
WIN_LOGO_W  = 7

WIN_MENU_H = 1 + BORDERS

# TITLE OFFSETS
REG_OFFSET  = 15
STAK_OFFSET = 4

# Min size to function
W_MIN       = 80
H_MIN       = 24

# Display size, and mins
DISPLAY_MIN_W = 104
DISPLAY_MIN_H = 34
DISPLAY_H = 16 + BORDERS # Terminal blocks are twice as tall as wide
DISPLAY_W = 64 + BORDERS

LEN_STR_REG = len("Regiters")
LEN_STR_STA = len("Stack")

# Action Keys
KEY_STEP  = 's'
KEY_EXIT  = 'x'
KEY_RESET = 'r'

KEYPAD_DRAW=[
'┌────────────────┐',
'│     Keypad     │',
'│┌──┐┌──┐┌──┐┌──┐│',
'││00││01││02││03││',
'│└──┘└──┘└──┘└──┘│',
'│┌──┐┌──┐┌──┐┌──┐│',
'││04││05││06││07││',
'│└──┘└──┘└──┘└──┘│',
'│┌──┐┌──┐┌──┐┌──┐│',
'││08││09││10││11││',
'│└──┘└──┘└──┘└──┘│',
'│┌──┐┌──┐┌──┐┌──┐│',
'││12││13││14││15││',
'│└──┘└──┘└──┘└──┘│',
'└────────────────┘'
]

# Prefixes to use for hz
PREFIX = [
    ['Y', 1e24], # yotta
    ['Z', 1e21], # zetta
    ['E', 1e18], # exa
    ['P', 1e15], # peta
    ['T', 1e12], # tera
    ['G', 1e9 ], # giga
    ['M', 1e6 ], # mega
    ['k', 1e3 ]  # kilo
]

# Logo
LOGO_MIN = 34
LOGO=[
'   ██  ',
'███████',
'█  ██  ',
'       ',
'██████ ',
'█   ██ ',
'██████ ',
'       ',
'██████ ',
'    ██ ',
'       ',
'   ██  ',
'███████',
'█  ██  ',
'       ',
'████ ██',
'       ',
'███████',
'       ',
'███████',
'       ',
'████ █ ',
'█  █ █ ',
'██████ ',
'███    ']



