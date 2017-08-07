#!/usr/bin/env python3

# Register stuff
NUMB_OF_REGS = 16
ARG_SUB   = {0:'x',1:'y',2:'z'}
REGISTERS = ('v0','v1','v2','v3',
            'v4','v5','v6','v7',
            'v8','v9','va','vb',
            'vc','vd','ve','vf')

# ROM Memory Addresses and Related
BYTES_OF_RAM = 4096
MAX_ROM_SIZE = 3232
PROGRAM_BEGIN_ADDRESS = 0x200
#PROGRAM_BEGIN_ADDRESS = 0x600 #I dunno who uses this
OVERFLOW_ADDRESS = PROGRAM_BEGIN_ADDRESS+MAX_ROM_SIZE

# Stack
STACK_SIZE    = 12
STACK_ADDRESS = None
#STACK_ADDRESS = 0xEA0 #Uncomment to emulate stack in ram

# Graphics
GFX_ADDRESS    = 0xF00
GFX_HEIGHT_PX  = 32
GFX_WIDTH_PX   = 64
GFX_WIDTH      = int(GFX_WIDTH_PX/8)
GFX_RESOLUTION = int(GFX_WIDTH*GFX_HEIGHT_PX) #In bytes

SET_VF_ON_GFX_OVERFLOW = False # Undocumented 'feature'. When 'Add I, VX' overflows 'I'
                               # VF is set to one when this is True. The insturction does
                               # not set VF low. Used by Spacefight 2019.
# Fonts (80 bytes)
GFX_FONT_ADDRESS = 0x050
GFX_FONT = (
    0xF0, 0x90, 0x90, 0x90, 0xF0, # 0
    0x20, 0x60, 0x20, 0x20, 0x70, # 1
    0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2
    0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3
    0x90, 0x90, 0xF0, 0x10, 0x10, # 4
    0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
    0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
    0xF0, 0x10, 0x20, 0x40, 0x40, # 7
    0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
    0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
    0xF0, 0x90, 0xF0, 0x90, 0x90, # A
    0xE0, 0x90, 0xE0, 0x90, 0xE0, # B
    0xF0, 0x80, 0x80, 0x80, 0xF0, # C
    0xE0, 0x90, 0x90, 0x90, 0xE0, # D
    0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
    0xF0, 0x80, 0xF0, 0x80, 0x80  # F
    )

# Curses Min size to function
DISPLAY_H = 16 # Terminal blocks are twice as tall as wide
DISPLAY_W = 64

# Action Keys
KEY_ESC   = 27  # Invisable esc
KEY_ARROW = 91  # '['
KEY_STEP  = 115 # S
KEY_EXIT  = 120 # X
KEY_RESET = 114 # R
KEY_REWIN = 119 # W
KEY_RESUM = 117 # U

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

from collections import namedtuple

ENABLE_LEGACY_SHIFT = False

# OP CODES
OP_CODE_SIZE = 2
OpData = namedtuple('OpData', 'regular, args, hex')
OP_CODES = {                                 # X and Y in the right most indicates if it is for the 1st or 2nd arg
    'cls' : OpData('00e0',[],'00E0'),
    'ret' : OpData('00ee',[],'00EE'),
    'sys' : OpData('0(^0)..',['addr'],'0xxx'), # prevent match to cls or ret
    'call': OpData('2...',['addr'],'2xxx'),
    'skp' : OpData('e.9e',['reg'],'Ex9E'),
    'sknp': OpData('e.a1',['reg'],'ExA1'),
    'se'  :(OpData('5..0',['reg','reg'],'5xy0'),
            OpData('3...',['reg','byte'],'3xyy')),
    'sne' :(OpData('9..0',['reg','reg'],'9xy0'),
            OpData('4...',['reg','byte'],'4xyy')),
    'add' :(OpData('7...',['reg','byte'],'7xyy'),
            OpData('8..4',['reg','reg'],'8xy4'),
            OpData('f.1e',['i','reg'],'Fy1E')),
    'or'  : OpData('8..1',['reg','reg'],'8xy1'),
    'and' : OpData('8..2',['reg','reg'],'8xy2'),
    'xor' : OpData('8..3',['reg','reg'],'8xy3'),
    'sub' : OpData('8..5',['reg','reg'],'8xy5'),
    'subn': OpData('8..7',['reg','reg'],'8xy7'),
    'shr' :(OpData('8..6',['reg'],'8x06'),
            OpData('    ',['reg','reg'],'8xy6')), # Blank regex, we never match, use Legacy_shift instead
    'shl' :(OpData('8..e',['reg'],'8x0E'),
            OpData('    ',['reg','reg'],'8xyE')), # as above
    'rnd' : OpData('c...',['reg','byte'],'Cxyy'),
    'jp'  :(OpData('b...',['v0','addr'],'Byyy'),
            OpData('1...',['addr'],'1xxx')),
    'ld'  :(OpData('6...',['reg','byte'],'6xyy'),
            OpData('8..0',['reg','reg'],'8xy0'),
            OpData('f.07',['reg','dt'],'Fx07'),
            OpData('f.0a',['reg','k'],'Fx0A'),
            OpData('f.65',['reg','[i]'],'Fx65'),
            OpData('a...',['i','addr'],'Ayyy'),
            OpData('f.15',['dt','reg'],'Fy15'),
            OpData('f.18',['st','reg'],'Fy18'),
            OpData('f.29',['f','reg'],'Fy29'),
            OpData('f.33',['b','reg'],'Fy33'),
            OpData('f.55',['[i]','reg'],'Fy55')),
    'drw' : OpData('d...',['reg','reg','nibble'],'Dxyz')
    }

UNOFFICIAL_OP_CODES = ('xor','shr','shl','subn') # But still supported
BANNED_OP_CODES = ('7f..','8f.4','8f.6','8f.e','cf..','6f..','8f.0','ff07','ff0a','ff65') # Ins that modify VF: add, shr, shl, rnd, ld
SUPER_CHIP_OP_CODES = ('00c.','00fb','00fc','00fd','00fe','00ff','d..0','f.30','f.75','f.85') # Super chip-8, not supported

# Used to explode opcodes that are not used (below)
def explode_op_codes( op_code_list ):
    exploded_list = []
    for item in op_code_list:
        if item.find('.') == -1:
            exploded_list.append(item)
        else:
            upper,repl,fill = 16,'.',1
            if item[2:] == '..':
                upper,repl,fill = 256,'..',2
            for i in range(0, upper):
                exploded_list.append(item.replace(repl, hex(i)[2:].zfill(fill)))
    return exploded_list

BANNED_OP_CODES_EXPLODED = explode_op_codes(BANNED_OP_CODES)
SUPER_CHIP_OP_CODES_EXPLODED = explode_op_codes(SUPER_CHIP_OP_CODES)



