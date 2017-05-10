#!/usr/bin/python3

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

