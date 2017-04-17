#!/usr/bin/python3

# General
BEGIN_COMMENT=';'
END_MEM_TAG=':'
HEX_ESC='#'
BIN_ESC='$' #TODO not used yet

# Pre Processor
ELSE_IF=('elif','elseif','elifdef','elseifdef')
END_MARKS=('endif','else')+ELSE_IF
EQU_MARKS=('equ','=')
MODE_MARKS=('option','align')
PRE_PROC=('ifdef','ifndef')+END_MARKS+EQU_MARKS+MODE_MARKS

# Register stuff
NUMB_OF_REGS=16
ARG_SUB={0:'x',1:'y',2:'z'}
REGISTERS=( 'v0','v1','v2','v3',
            'v4','v5','v6','v7',
            'v8','v9','va','vb',
            'vc','vd','ve','vf')

# Memory Addresses and Related
OVERFLOW_ADDRESS=0xEA0
PROGRAM_BEGIN_ADDRESS=0x200
BYTES_OF_RAM=4096
STACK_DEPTH=12
GFX_RESOLUTION=64*32
FONT_ADDRESS=0x050
GFX_ADDRESS=0xF00
#0x000-0x1FF - Chip 8 interpreter
#0x050-0x0A0 - Used for the built in 4x5 pixel font set (0-F)
#0x200-0xE9F - Program ROM
#0xEA0-0xEFF - Call stack
#0xF00-0xFFF - Display

# OP CODE related
DATA_DECLARE={'db':1,'dw':2,'dd':4}
OP_ARGS=0
OP_HEX=1
OP_CODE_SIZE=2
OP_CODES={  'cls' :[[[],'00E0']],
            'ret' :[[[],'00EE']],
            'sys' :[[['address'],'1xxx']],
            'call':[[['address'],'2xxx']],
            'skp' :[[['register'],'Ex9E']],
            'sknp':[[['register'],'ExA1']],
            'se'  :[[['register','register'],'5xy0'],
		            [['register','byte'],'3xyy']],
            'sne' :[[['register','register'],'9xy0'],
		            [['register','byte'],'4xyy']],
            'add' :[[['register','byte'],'7xyy'],
		            [['register','register'],'8xy4'],
		            [['i','register'],'Fx1E']],
            'or'  :[[['register','register'],'8xy1']],
            'and' :[[['register','register'],'8xy2']],
            'xor' :[[['register','register'],'8xy3']],    #TODO not in orig spec.
            'sub' :[[['register','register'],'8xy5']],
            'subn':[[['register','register'],'8xy7']],    #TODO not in orig spec.
            'shr' :[[['register'],'8x06'],                #TODO not in orig spec.
                    [['register','register'],'8xy6']],    #TODO not in orig spec.
            'shl' :[[['register'],'8x0E'],                #TODO not in orig spec.
                    [['register','register'],'8xyE']],    #TODO not in orig spec.
            'rnd' :[[['register','byte'],'cxyy']],
            'jp'  :[[['address'],'1xxx'],
		            [['v0','address'],'Byyy']],           #This works! V0 is checked before generic regs
            'ld'  :[[['register','byte'],'6xyy'],
		            [['register','register'],'8xy0'],
		            [['register','dt'],'Fx07'],
		            [['register','k'],'Fx0A'],
		            [['register','[i]'],'Fx65'],
		            [['i','address'],'Ayyy'],
		            [['dt','register'],'Fy15'],
		            [['st','register'],'Fy18'],
		            [['f','register'],'Fy29'],
		            [['b','register'],'Fy33'],
		            [['[i]','register'],'Fy55']],
            'drw' :[[['register','register','nibble'],'Dxyz']]}

# Fonts (80 bytes)
FONT=[
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
]




