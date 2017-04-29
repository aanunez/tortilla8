#!/usr/bin/python3

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
#PROGRAM_BEGIN_ADDRESS=0x600 #I dunno who uses this
OVERFLOW_ADDRESS=PROGRAM_BEGIN_ADDRESS+MAX_ROM_SIZE
BYTES_OF_RAM=4096
STACK_SIZE=12
STACK_ADDRESS=None
#STACK_ADDRESS=0xEA0 #Uncomment to emulate stack in ram
GFX_HEIGHT_PX=32
GFX_WIDTH_PX=64
GFX_WIDTH=int(GFX_WIDTH_PX/8)
GFX_RESOLUTION=int(GFX_WIDTH*GFX_HEIGHT_PX) #In bytes
#GFX_RESOLUTION=int((64/8)*48) #Used by ETI 660
#GFX_RESOLUTION=int((64/8)*64) #Used by ETI 660
FONT_ADDRESS=0x050
GFX_ADDRESS=0xF00
