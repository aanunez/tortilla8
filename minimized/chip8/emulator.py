#!/usr/bin/env python3

from random import randint
from os.path import getsize
from time import time
from collections import namedtuple
from .constants import BYTES_OF_RAM, PROGRAM_BEGIN_ADDRESS, NUMB_OF_REGS, MAX_ROM_SIZE, \
                       GFX_FONT, GFX_FONT_ADDRESS, GFX_RESOLUTION, GFX_ADDRESS, \
                       GFX_WIDTH, GFX_HEIGHT_PX, GFX_WIDTH_PX, ENABLE_LEGACY_SHIFT, \
                       SET_VF_ON_GFX_OVERFLOW, STACK_ADDRESS, STACK_SIZE, \
                       OP_CODES, UNOFFICIAL_OP_CODES, \
                       BANNED_OP_CODES_EXPLODED, SUPER_CHIP_OP_CODES_EXPLODED

class ASMdata( namedtuple('ASMdata', 'hex_instruction valid mnemonic\
    mnemonic_arg_types disassembled_line unoffical_op banned super8') ):
    pass

class EarlyExit(Exception):
    pass

class Emulator:

    def __init__(self, rom=None, cpuhz=200, audiohz=60, delayhz=60):

        # RAM
        self.ram = [0x00] * BYTES_OF_RAM

        # Registers
        self.register = [0x00] * NUMB_OF_REGS
        self.index_register = 0x000
        self.delay_timer_register = 0x00
        self.sound_timer_register = 0x00

        # Current dissassembled instruction / OP Code
        self.dis_ins = None

        # Program Counter
        self.program_counter = PROGRAM_BEGIN_ADDRESS
        self.calling_pc      = PROGRAM_BEGIN_ADDRESS

        # I/O
        self.keypad      = [False] * 16
        self.prev_keypad = 0
        self.draw_flag   = False
        self.waiting_for_key = False
        self.spinning = False

        # Stack
        self.stack = []
        self.stack_pointer = 0

        # Timming variables
        self.cpu_wait   = 1/cpuhz
        self.audio_wait = 1/audiohz
        self.delay_wait = 1/delayhz

        # Load Font, clear screen
        self.ram[GFX_FONT_ADDRESS:GFX_FONT_ADDRESS + len(GFX_FONT)] = GFX_FONT
        self.ram[GFX_ADDRESS:GFX_ADDRESS + GFX_RESOLUTION] = [0x00] * GFX_RESOLUTION

        # Load Rom
        if rom is not None:
            self.load_rom(rom)

        # Instruction lookup table
        self.ins_tbl={
        'cls' :i_cls, 'ret' :i_ret,  'sys' :i_sys, 'call':i_call,
        'skp' :i_skp, 'sknp':i_sknp, 'se'  :i_se,  'sne' :i_sne,
        'add' :i_add, 'or'  :i_or,   'and' :i_and, 'xor' :i_xor,
        'sub' :i_sub, 'subn':i_subn, 'shr' :i_shr, 'shl' :i_shl,
        'rnd' :i_rnd, 'jp'  :i_jp,   'ld'  :i_ld,  'drw' :i_drw}

    def load_rom(self, file_path):
        '''
        Loads a Chip-8 ROM from a file into the RAM.
        '''
        file_size = getsize(file_path)
        if file_size > MAX_ROM_SIZE:
            self.log("Rom file exceeds maximum rom size of " + str(MAX_ROM_SIZE) + \
                " bytes" , EmulationError._Fatal)
            return

        with open(file_path, "rb") as fh:
            self.ram[PROGRAM_BEGIN_ADDRESS:PROGRAM_BEGIN_ADDRESS + file_size] = \
                [int.from_bytes(fh.read(1), 'big') for i in range(file_size)]

    def run(self):
        '''
        Attempt to run the next instruction. This should be called as a part
        of the main loop, it insures that the CPU and timers execute at the
        target frequency.
        '''
        if self.cpu_wait <= (time() - run.cpu_time):
            self.cpu_time = time()
            self.cpu_tick()

        if self.audio_wait <= (time() - run.audio_time):
            self.audio_time = time()
            self.sound_timer_register -= 1 if self.sound_timer_register != 0 else 0

        if self.delay_wait <= (time() - run.delay_time):
            self.delay_time = time()
            self.delay_timer_register -= 1 if self.delay_timer_register != 0 else 0
    run.cpu_time = 0
    run.audio_time = 0
    run.delay_time = 0

    def cpu_tick(self):
        '''
        Ticks the CPU forward a cycle without regard for the target frequency.
        '''
        # Handle the ld reg,k instruction
        if self.waiting_for_key:
            self.handle_load_key()
            return
        else:
            self.prev_keypad = self.decode_keypad()

        self.calling_pc = self.program_counter

        # Dissassemble next instruction
        self.dis_ins = None
        try:
            self.dis_ins = disassemble(self.ram[self.program_counter:self.program_counter+2])
        except:
            raise

        # Execute instruction
        if self.dis_ins.valid:
            self.ins_tbl[self.dis_ins.mnemonic](self)
        else:
            print("Invalid instruction found.\n" + hex(self.program_counter) + "\n" + str(self.dis_ins))
            raise SystemExit

        # Increment the PC
        self.program_counter += 2

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Helpers for Load Key

    def decode_keypad(self):
        '''
        Helper method to decode the current keypad into a binary string
        '''
        return int(''.join(['1' if x else '0' for x in self.keypad]),2)

    def handle_load_key(self):
        '''
        Helper method to check if keys have changed and, if so, load the
        key per the ld reg,k instruction.
        '''
        k = self.decode_keypad()
        nk = bin( (k ^ self.prev_keypad) & k )[2:].zfill(16).find('1')
        if nk != -1:
            self.register[ self.get_reg1() ] = nk
            self.program_counter += 2
            self.waiting_for_key = False

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Dissassembler

    def disassemble(byte_list):
        '''
        A one line (2 byte) dissassembler function for CHIP-8 Rom It
        returns a named tuple with various information on the line.
        '''
        hex_instruction =  hex( byte_list[0] )[2:].zfill(2)
        hex_instruction += hex( byte_list[1] )[2:].zfill(2)
        valid = False
        mnemonic = None
        mnemonic_arg_types = None
        disassembled_line = ""
        unoffical_op = False
        banned = False
        super8 = False

        try:
            # Check if the Op-Code a Super-8 instruction
            if hex_instruction in SUPER_CHIP_OP_CODES_EXPLODED:
                mnemonic = 'SPR'
                super8 = True
                raise EarlyExit

            # Match the instruction via a regex index
            for mnemonic, reg_patterns in OP_CODES.items():

                if type(reg_patterns) is not tuple:
                    reg_patterns = (reg_patterns,)
                for pattern_version in reg_patterns:
                    if not match(pattern_version.regular, hex_instruction):
                        continue
                    mnemonic = mnemonic
                    mnemonic_arg_types = pattern_version.args
                    valid = True
                    break
                if valid:
                    break

            # If not a valid instruction, assume data
            if not valid:
                disassembled_line = hex_instruction
                raise EarlyExit

            # If banned, flag and exit.
            if hex_instruction in BANNED_OP_CODES_EXPLODED:
                banned = True
                raise EarlyExit

            # If unoffical, flag it.
            if mnemonic in UNOFFICIAL_OP_CODES:
                unoffical_op = True

            # No args to parse
            if mnemonic_arg_types is None:
                disassembled_line = mnemonic
                raise EarlyExit

            # Parse Args
            tmp = ''
            reg_numb = 1
            for arg_type in mnemonic_arg_types:
                if arg_type is 'reg':
                    tmp = 'v'+hex_instruction[reg_numb]
                elif arg_type is 'byte':
                    tmp = '#'+hex_instruction[2:]
                elif arg_type is 'addr':
                    tmp = '#'+hex_instruction[1:]
                elif arg_type is 'nibble':
                    tmp = '#'+hex_instruction[3]
                else:
                    tmp = arg_type
                disassembled_line += tmp.ljust(5) + ','
                reg_numb = 2

            disassembled_line = (mnemonic.ljust(5) + disassembled_line[:-1]).rstrip()
        except EarlyExit:
            pass
        finally:
            return ASMdata(hex_instruction, valid, mnemonic,
                mnemonic_arg_types, disassembled_line, unoffical_op,
                banned, super8)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Instructions - All 20 mnemonics, 35 total instructions
# Add-3 SE-2 SNE-2 LD-11 JP-2 (mnemonics w/ extra instructions)

def i_cls(emu):
    emu.ram[GFX_ADDRESS:GFX_ADDRESS + GFX_RESOLUTION] = [0x00] * GFX_RESOLUTION
    emu.draw_flag = True

def i_ret(emu):
    emu.stack_pointer -= 1
    if emu.stack_pointer < 0:
        emu.log("Stack underflow", EmulationError._Fatal)
    emu.program_counter = emu.stack.pop()

def i_sys(emu):
    emu.log("RCA 1802 call to " + hex( get_address(emu) ) + " was ignored.", EmulationError._Warning)

def i_call(emu):
    if STACK_ADDRESS:
        emu.ram[stack_pointer] = emu.program_counter
    emu.stack_pointer += 1
    emu.stack.append(emu.program_counter)
    if emu.stack_pointer > STACK_SIZE:
        emu.log("Stack overflow. Stack is now size " + emu.stack_pointer, EmulationError._Warning)
    emu.program_counter = get_address(emu) - 2

def i_skp(emu):
    if emu.keypad[ get_reg1_val(emu) & 0x0F ]:
        emu.program_counter += 2

def i_sknp(emu):
    if not emu.keypad[ get_reg1_val(emu) & 0x0F ]:
        emu.program_counter += 2

def i_se(emu):
    comp = get_lower_byte(emu) if 'byte' is emu.dis_ins.mnemonic_arg_types[1] else get_reg2_val(emu)
    if get_reg1_val(emu) == comp:
        emu.program_counter += 2

def i_sne(emu):
    comp = get_lower_byte(emu) if 'byte' is emu.dis_ins.mnemonic_arg_types[1] else get_reg2_val(emu)
    if get_reg1_val(emu) != comp:
        emu.program_counter += 2

def i_shl(emu):
    if ENABLE_LEGACY_SHIFT:
        emu.register[0xF] = 0x01 if get_reg2_val(emu) >= 0x80 else 0x0
        emu.register[ get_reg1(emu) ] = ( get_reg2_val(emu) << 1 ) & 0xFF
    else:
        emu.register[0xF] = 0x01 if get_reg1_val(emu) >= 0x80 else 0x0
        emu.register[ get_reg1(emu) ] = ( get_reg1_val(emu) << 1 ) & 0xFF

def i_shr(emu):
    if ENABLE_LEGACY_SHIFT:
        emu.register[0xF] = 0x01 if ( get_reg2_val(emu) % 2) == 1 else 0x0
        emu.register[ get_reg1(emu) ] = get_reg2_val(emu) >> 1
    else:
        emu.register[0xF] = 0x01 if ( get_reg1_val(emu) % 2) == 1 else 0x0
        emu.register[ get_reg1(emu) ] = get_reg1_val(emu) >> 1

def i_or(emu):
    emu.register[ get_reg1(emu) ] = get_reg1_val(emu) | get_reg2_val(emu)

def i_and(emu):
    emu.register[ get_reg1(emu) ] = get_reg1_val(emu) & get_reg2_val(emu)

def i_xor(emu):
    emu.register[ get_reg1(emu) ] = get_reg1_val(emu) ^ get_reg2_val(emu)

def i_sub(emu):
    emu.register[0xF] = 0x01 if get_reg1_val(emu) >= get_reg2_val(emu) else 0x00
    emu.register[ get_reg1(emu) ] = get_reg1_val(emu) - get_reg2_val(emu)
    emu.register[ get_reg1(emu) ] &= 0xFF

def i_subn(emu):
    emu.register[0xF] = 0x01 if get_reg2_val(emu) >= get_reg1_val(emu) else 0x00
    emu.register[ get_reg1(emu) ] = get_reg2_val(emu) - get_reg1_val(emu)
    emu.register[ get_reg1(emu) ] &= 0xFF

def i_jp(emu):
    init_pc = emu.program_counter
    numb_args = len(emu.dis_ins.mnemonic_arg_types)

    if 'v0' is emu.dis_ins.mnemonic_arg_types[0] and numb_args == 2:
        emu.program_counter = get_address(emu) + emu.register[0] - 2
    elif numb_args == 1:
        emu.program_counter = get_address(emu) - 2
    else:
        emu.log("Unknown argument at address " + hex(emu.program_counter), EmulationError._Fatal)

    if init_pc == emu.program_counter + 2:
        emu.spinning = True

def i_rnd(emu):
    emu.register[ get_reg1(emu) ] = randint(0, 255) & get_lower_byte(emu)

def i_add(emu):
    arg1 = emu.dis_ins.mnemonic_arg_types[0]
    arg2 = emu.dis_ins.mnemonic_arg_types[1]

    if 'reg' is arg1:

        if 'byte' is arg2:
            emu.register[ get_reg1(emu) ] = get_reg1_val(emu) + get_lower_byte(emu)
            emu.register[ get_reg1(emu) ] &= 0xFF
        elif 'reg' is arg2:
            emu.register[ get_reg1(emu) ] = get_reg1_val(emu) + get_reg2_val(emu)
            emu.register[0xF] = 0x01 if emu.register[ get_reg1(emu) ] > 0xFF else 0x00
            emu.register[ get_reg1(emu) ] &= 0xFF
        else:
            emu.log("Unknown argument at address " + hex(emu.program_counter), EmulationError._Fatal)

    elif 'i' in arg1 and 'reg' is arg2:
        emu.index_register += get_reg1_val(emu)
        if (emu.index_register > 0xFF) and SET_VF_ON_GFX_OVERFLOW:
            emu.register[0xF] = 0x01
        emu.index_register &= 0xFFF

    else:
        emu.log("Unknown argument at address " + hex(emu.program_counter), EmulationError._Fatal)

def i_ld(emu):
    arg1 = emu.dis_ins.mnemonic_arg_types[0]
    arg2 = emu.dis_ins.mnemonic_arg_types[1]

    if 'reg' is arg1:
        if   'byte'     is arg2:
            emu.register[ get_reg1(emu) ] = get_lower_byte(emu)
        elif 'reg' is arg2:
            emu.register[ get_reg1(emu) ] = get_reg2_val(emu)
        elif 'dt'       is arg2:
            emu.register[ get_reg1(emu) ] = emu.delay_timer_register
        elif 'k'        is arg2:
            emu.waiting_for_key = True
            emu.program_counter -= 2
        elif '[i]' == arg2:
            emu.register[0: get_reg1(emu) + 1] = emu.ram[ emu.index_register : emu.index_register + get_reg1(emu) + 1]
        else:
            emu.log("Loads with second argument type '" + arg2 + \
                "' are not supported.", EmulationError._Fatal)

    elif 'reg' is arg2:
        if   'dt' is arg1:
            emu.delay_timer_register =  get_reg1_val(emu)
        elif 'st' is arg1:
            emu.sound_timer_register =  get_reg1_val(emu)
        elif 'f'  is arg1:
            emu.index_register = GFX_FONT_ADDRESS + ( 5 * get_reg1_val(emu) )
        elif 'b'  is arg1:
            bcd = [int(f) for f in list(str( get_reg1_val(emu) ).zfill(3))]
            emu.ram[ emu.index_register : emu.index_register + len(bcd)] = bcd
        elif '[i]' == arg1:
            emu.ram[ emu.index_register : emu.index_register + get_reg1(emu) + 1] = emu.register[0: get_reg1(emu) + 1]
        else:
            emu.log("Unknown argument at address " + hex(emu.program_counter), EmulationError._Fatal)

    elif 'i' is arg1 and 'addr' is arg2:
        emu.index_register =  get_address(emu)

    else:
        emu.log("Unknown argument at address " + hex(emu.program_counter), EmulationError._Fatal)

def i_drw(emu):
    emu.draw_flag = True
    height = int(emu.dis_ins.hex_instruction[3],16)
    x_origin_byte = int( get_reg1_val(emu) / 8 ) % GFX_WIDTH
    y_origin_byte = (get_reg2_val(emu) % GFX_HEIGHT_PX) * GFX_WIDTH
    shift_amount = get_reg1_val(emu) % GFX_WIDTH_PX % 8
    next_byte_offset = 1 if x_origin_byte + 1 != GFX_WIDTH else 1-GFX_WIDTH

    emu.register[0xF] = 0x00
    for y in range(height):
        sprite =  emu.ram[ emu.index_register + y ] << (8-shift_amount)

        working_bytes = (
            GFX_ADDRESS + (( x_origin_byte + y_origin_byte + (y * GFX_WIDTH) ) % GFX_RESOLUTION) ,
            GFX_ADDRESS + (( x_origin_byte + y_origin_byte + (y * GFX_WIDTH) + next_byte_offset ) % GFX_RESOLUTION)
        )

        original = ( emu.ram[ working_bytes[0] ], emu.ram[ working_bytes[1] ] )
        xor = (original[0]*256 + original[1]) ^ sprite
        emu.ram[ working_bytes[0] ], emu.ram[ working_bytes[1] ] = xor >> 8, xor & 0x00FF

        if (bin( ( emu.ram[ working_bytes[0] ] ^ original[0] ) & original[0] ) + \
            bin( ( emu.ram[ working_bytes[1] ] ^ original[1] ) & original[1] )).find('1') != -1:
            emu.register[0xF] = 0x01

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Hex Extraction

def get_address(emu):
    return int(emu.dis_ins.hex_instruction[1:4], 16)

def get_reg1(emu):
    return int(emu.dis_ins.hex_instruction[1],16)

def get_reg2(emu):
    return int(emu.dis_ins.hex_instruction[2],16)

def get_reg1_val(emu):
    return emu.register[int(emu.dis_ins.hex_instruction[1],16)]

def get_reg2_val(emu):
    return emu.register[int(emu.dis_ins.hex_instruction[2],16)]

def get_lower_byte(emu):
    return int(emu.dis_ins.hex_instruction[2:4], 16)

