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
W_MIN = 80
H_MIN = 24

# Messages to display when window is too small
DY_MSG_1 = "Window too small"
DY_MSG_2 = "Resize to " + str(W_MIN) + "x" + str(H_MIN)

# Display size, and mins
DISPLAY_MIN_W = 104
DISPLAY_MIN_H = 34
DISPLAY_H = 16 + BORDERS # Terminal blocks are twice as tall as wide
DISPLAY_W = 64 + BORDERS

LEN_STR_REG = len("Regiters")
LEN_STR_STA = len("Stack")

# Action Keys
KEY_ESC   = 27  # Invisable esc
KEY_ARROW = 91  # '['
KEY_STEP  = 115 # S
KEY_EXIT  = 120 # X
KEY_RESET = 114 # R
KEY_REWIN = 119 # W

KEY_CONTROLS={
48:0x0, 49:0x1, 50:0x2, 51:0x3, # 0 1 2 3
52:0x4, 53:0x5, 54:0x6, 55:0x7, # 4 5 6 7
56:0x8, 57:0x9, 47:0xA, 42:0xB, # 8 9 / *
45:0xC, 43:0xD, 10:0xE, 46:0xF} # - + E .

KEY_ARROW_MAP={65:'up',66:'down',67:'right',68:'left'}

# Graphics Draw
from collections import namedtuple
CHAR_SET = namedtuple('CHAR_SET', 'upper lower both empty')
UNICODE_DRAW = CHAR_SET('▀','▄','█',' ')
WIN_DRAW = CHAR_SET('*','o','8',' ')

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



