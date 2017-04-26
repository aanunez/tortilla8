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
MAX_ROM_SIZE=3232
PROGRAM_BEGIN_ADDRESS=0x200
OVERFLOW_ADDRESS=PROGRAM_BEGIN_ADDRESS+MAX_ROM_SIZE
#PROGRAM_BEGIN_ADDRESS=0x600 #I dunno who uses this
BYTES_OF_RAM=4096
STACK_SIZE=12
STACK_ADDRESS=None
#STACK_ADDRESS=0xEA0 #Not really used, original calls for
SPRITE_WIDTH=8
GFX_HEIGHT=32
GFX_WIDTH=64
GFX_RESOLUTION=int((GFX_WIDTH*GFX_HEIGHT)/8)
#GFX_RESOLUTION=int((64*48)/8) #Used by ETI 660
#GFX_RESOLUTION=int((64*64)/8) #Used by ETI 660
FONT_ADDRESS=0x050
GFX_ADDRESS=0xF00

# Data Type Enum - Probably not a good idea
#from enum import Enum
#class argument(Enum):
#    address  = auto()
#    register = auto()
#    byte     = auto()
#    nibble   = auto()
#    i        = auto()
#    [i]      = auto()
#    v0       = auto()
#    dt       = auto()
#    st       = auto()
#    b        = auto()
#    f        = auto()
#
#    def __str__(self):
#        return self.name

# Frequency
CPU_HZ=60
AUDIO_HZ=60
CPU_WAIT_TIME=1/(CPU_HZ)
AUDIO_WAIT_TIME=1/(AUDIO_HZ)

# OP CODE related
DATA_DECLARE={'db':1,'dw':2,'dd':4}
OP_ARGS=0
OP_HEX=1
OP_CODE_SIZE=2
OP_CODES={'cls' :[[[],'00E0']],
          'ret' :[[[],'00EE']],
          'sys' :[[['address'],'1xxx']],                #Jump with no offset
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
          'jp'  :[[['v0','address'],'Byyy'],
                  [['address'],'1xxx']],                # jp == sys
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

OP_REG={'00E0':['cls',0],
        '00EE':['ret',0],
        '1...':['sys',0],
        '2...':['call',0],
		'3...':['se',1],
		'4...':['sne',1],
        '5..0':['se',0],
        '6...':['ld',0],
        '7...':['add',0],
		'8..0':['ld',1],
        '8..1':['or',0],
        '8..2':['and',0],
        '8..3':['xor',0],
		'8..4':['add',1],
        '8..5':['sub',0],
        '8..6':['shr',0], #TODO no support for emulating the "more correct" form of shift
        '8..7':['subn',0],
        '8..E':['shl',0], #TODO above
        '9..0':['sne',0],
		'A...':['ld',5],
		'B...':['jp',0],
        'C...':['rnd',0],
        'D...':['drw',0],
        'E.9E':['skp',0],
        'E.A1':['sknp',0],
		'F.07':['ld',2],
		'F.0A':['ld',3],
		'F.15':['ld',6],
		'F.18':['ld',7],
		'F.1E':['add',2],
		'F.29':['ld',8],
		'F.33':['ld',9],
		'F.55':['ld',10],
		'F.65':['ld',4]}

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




