#!/usr/bin/python3

import sys
import re       # Matching Op Code
import os       # Rom Loading
import time     # CPU Frequency
import random   # RND instruction
import argparse # Command line
from mem_addr_register_constants import *
from opcode_constants import *

# TODO raise real warnings
# TODO Wrap around doesn't work for drw instruction (Needs testing)
# TODO Shift L/R behavior needs a toggle for "old" and "new" behavior
# TODO Log a warning when running a unoffical instruction?
# TODO add comments

class guacamole:

    def __init__(self, rom=None, cpuhz=60, audiohz=60):
        '''
        Init
        '''
        random.seed()

        # # # # # # # # # # # # # # # # # # # # # # # #
        # Public

        # RAM
        self.ram = [None] * BYTES_OF_RAM

        # Registers
        self.register = [0x00] * NUMB_OF_REGS
        self.index_register = 0x000
        self.delay_timer_register = 0x00
        self.sound_timer_register = 0x00

        # Current Op Code
        self.hex_instruction = None
        self.mnemonic        = None
        self.mnemonic_arg_types = None

        self.program_counter = PROGRAM_BEGIN_ADDRESS
        self.calling_pc      = 0

        # I/O
        self.keypad      = [False] * 16
        self.prev_keypad = 0
        self.draw_flag   =  False
        self.waiting_for_key = False

        # Stack
        self.stack = []
        self.stack_pointer = 0

        # # # # # # # # # # # # # # # # # # # # # # # #
        # Private

        # Timming variables
        self.cpu_wait   = 1/cpuhz
        self.audio_wait = 1/audiohz
        self.audio_time = 0
        self.cpu_time   = 0

        # Load Font, clear screen
        self.ram[FONT_ADDRESS:FONT_ADDRESS+len(FONT) ] = [i for i in FONT]
        self.ram[GFX_ADDRESS:GFX_ADDRESS + GFX_RESOLUTION] = [0x00] * GFX_RESOLUTION

        # Load Rom
        if rom is not None:
            self.load_rom(rom)

        # Instruction lookup table
        self.ins_tbl={
        'cls' :self.i_cls, 'ret' :self.i_ret,  'sys' :self.i_sys, 'call':self.i_call,
        'skp' :self.i_skp, 'sknp':self.i_sknp, 'se'  :self.i_se,  'sne' :self.i_sne,
        'add' :self.i_add, 'or'  :self.i_or,   'and' :self.i_and, 'xor' :self.i_xor,
        'sub' :self.i_sub, 'subn':self.i_subn, 'shr' :self.i_shr, 'shl' :self.i_shl,
        'rnd' :self.i_rnd, 'jp'  :self.i_jp,   'ld'  :self.i_ld,  'drw' :self.i_drw}

    def load_rom(self, file_path):
        '''
        load_rom
        '''
        file_size = os.path.getsize(file_path)
        if file_size > MAX_ROM_SIZE:
            print("Warning: Rom file exceeds MAX_ROM_SIZE.")

        with open(file_path, "rb") as fh:
            self.ram[PROGRAM_BEGIN_ADDRESS:PROGRAM_BEGIN_ADDRESS + file_size] = [int.from_bytes(fh.read(1), 'big') for i in range(file_size)]

    def reset(self, rom=None, cpuhz=60, audiohz=60):
        '''
        reset
        '''
        self.__init__(rom, cpuhz, audiohz)

    def run(self):
        '''
        run
        '''
        if self.cpu_wait <= (time.time() - self.cpu_time):
            self.cpu_time = time.time()
            self.cpu_tick()

        if self.audio_wait <= (time.time() - self.audio_time):
            self.audio_time = time.time()
            self.audio_tick()

    def cpu_tick(self):
        '''
        cpu_tick
        '''
        # Handle the ld k,reg instruction
        self.handle_load_key()

        # Fetch instruction from ram
        found = False
        self.hex_instruction =  hex(self.ram[self.program_counter + 0])[2:].zfill(2)
        self.hex_instruction += hex(self.ram[self.program_counter + 1])[2:].zfill(2)

        # Match the instruction via a regex index
        for reg_pattern in OP_REG:
            if re.match(reg_pattern.lower(), self.hex_instruction):
                self.calling_pc = self.program_counter
                self.mnemonic = OP_REG[reg_pattern][0]
                self.mnemonic_arg_types = OP_CODES[self.mnemonic][OP_REG[reg_pattern][1]][OP_ARGS]
                self.ins_tbl[self.mnemonic]()
                found = True
                break

        # Error out, to add new instruction update OP_REG and OP_CODES and self.i_
        if not found:
            print("Fatal: Unknown instruction " + instruction + " at " + hex(self.program_counter))

        self.program_counter += 2

    def audio_tick(self):
        '''
        audio_tick
        '''
        # Decrement sound registers
        self.delay_timer_register -= 1 if self.delay_timer_register != 0 else 0
        self.sound_timer_register -= 1 if self.sound_timer_register != 0 else 0

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Instructions ( Private )

    def i_cls(self):
        self.ram[GFX_ADDRESS:] = [0x00 for i in range(GFX_RESOLUTION) ]
        self.draw_flag = True

    def i_ret(self):
        self.stack_pointer -= 1
        if self.stack_pointer < 0:
            print("Fatal: Stack underflow")
        self.program_counter = self.stack.pop()

    def i_sys(self):
        print("Warning: RCA 1802 call to " + hex( self.get_address()) + " was ignored.")

    def i_call(self):
        if STACK_ADDRESS:
            self.ram[stack_pointer] = self.program_counter
        self.stack_pointer += 1
        self.stack.append(self.program_counter)
        if self.stack_pointer > STACK_SIZE:
            print("Warning: Stack overflow. Stack is now size " + self.stack_pointer)
        self.program_counter =  self.get_address() - 2

    def i_skp(self):
        if self.keypad[ self.get_reg1_val() & 0x0F]:
            self.program_counter += 2

    def i_sknp(self):
        if not self.keypad[ self.get_reg1_val() & 0x0F]:
            self.program_counter += 2

    def i_se(self):
        comp =  self.get_lower_byte() if "byte" in self.mnemonic_arg_types else self.get_reg2_val()
        if  self.get_reg1_val() == comp:
            self.program_counter += 2

    def i_sne(self):
        comp =  self.get_lower_byte() if "byte" in self.mnemonic_arg_types else self.get_reg2_val()
        if  self.get_reg1_val() != comp:
            self.program_counter += 2

    def i_shl(self):                                         #TODO add option to respect "old" shift
        self.register[ self.get_reg1() ] = ( self.get_reg1_val() << 1) & 0xFF
        self.register[0xF] = 0xFF if  self.get_reg1_val() >= 0x80 else 0x0

    def i_shr(self):                                         #TODO add option to respect "old" shift
        self.register[ self.get_reg1() ] = self.get_reg1_val() >> 1
        self.register[0xF] = 0xFF if ( self.get_reg1_val() % 2) == 1 else 0x0

    def i_or(self):
        self.register[ self.get_reg1() ] = self.get_reg1_val() | self.get_reg2_val()

    def i_and(self):
        self.register[ self.get_reg1() ] = self.get_reg1_val() & self.get_reg2_val()

    def i_xor(self):
        self.register[ self.get_reg1() ] = self.get_reg1_val() ^ self.get_reg2_val()

    def i_sub(self):
        self.register[ self.get_reg1() ] = self.get_reg1_val() - self.get_reg2_val()
        self.register[ self.get_reg1() ] += 0x00 if  self.get_reg1_val() > self.get_reg2_val() else 0xFF
        self.register[0xF] = 0xFF if  self.get_reg1_val() >  self.get_reg2_val() else 0x00

    def i_subn(self):
        self.register[ self.get_reg1() ] = self.get_reg2_val() - self.get_reg1_val()
        self.register[ self.get_reg1() ] += 0x00 if  self.get_reg2_val() > self.get_reg1_val() else 0xFF
        self.register[0xF] = 0xFF if self.get_reg2_val() >  self.get_reg1_val() else 0x00

    def i_jp(self):
        if 'v0' in self.mnemonic_arg_types:
            self.program_counter = self.get_address() + self.register[0] - 2
        else:
            self.program_counter = self.get_address() - 2

    def i_rnd(self):
        self.register[ self.get_reg1() ] = random.randint(0, 255) & self.get_lower_byte()

    def i_add(self):
        if 'byte' in self.mnemonic_arg_types:
            self.register[ self.get_reg1() ] += self.get_lower_byte()

        elif 'i' in self.mnemonic_arg_types:
            self.index_register += self.get_reg1_val()

        else:
            self.register[ self.get_reg1() ] += self.get_reg2_val()
            if  self.get_reg1_val() + self.get_reg2_val() > 0xFF:
                self.register[ self.get_reg1() ] &= 0xFF

    def i_ld(self):
        arg1 = self.mnemonic_arg_types[0]
        arg2 = self.mnemonic_arg_types[1]

        if 'register' is arg1:
            if   'byte'     is arg2: self.register[ self.get_reg1() ] = self.get_lower_byte()
            elif 'register' is arg2: self.register[ self.get_reg1() ] = self.get_reg2_val()
            elif 'dt'       is arg2: self.register[ self.get_reg1() ] = self.delay_timer_register
            elif 'k'        is arg2:
                self.waiting_for_key = True
                self.program_counter -= 2
            elif '[i]' == arg2:
                for i in range( self.get_reg1()):
                    self.register[i] = self.ram[self.index_register + i]

            else:
                print("Fatal: Loads with argument type '" + arg2 + "' are not supported.")

        elif 'register' is arg2:
            if   'dt' is arg1: self.delay_timer_register =  self.get_reg1_val()
            elif 'st' is arg1: self.sound_timer_register =  self.get_reg1_val()
            elif 'f'  is arg1: self.index_register = FONT_ADDRESS + ( 5 * self.get_reg1_val() )
            elif 'b'  is arg1:
                bcd = str( self.get_reg1_val() ).zfill(3)
                for i in range(3):
                    self.ram[self.index_register + i] = int(bcd[i])

            elif '[i]' == arg1:
                for i in range( self.get_reg1()):
                    self.ram[self.index_register + i] = self.register[i]

            else:
                print("Fatal: Loads with argument type '" + arg1 + "' are not supported.")

        elif 'i' is arg1 and 'address' is arg2:
            self.index_register =  self.get_address()

        else:
            print("Fatal: Loads with argument types '" + arg1 + "' and '" + arg2 +  "' are not supported.")

    def i_drw(self):           # TODO Haven't tested wrapping
        #if  self.get_reg1_val() >= GFX_WIDTH_PX:
        #    print("Warning: Draw instruction called with X origin >= GFX_WIDTH_PX\nWrap-around not yet supported.")
        #if  self.get_reg2_val() >= GFX_HEIGHT_PX:
        #    print("Warning: Draw instruction called with Y origin >= GFX_HEIGHT_PX\nWrap-around not yet supported.")

        self.draw_flag = True
        height = int(self.hex_instruction[3],16)
        x_origin_byte = int( self.get_reg1_val() / 8 ) % GFX_WIDTH
        y_origin_byte = (self.get_reg2_val() % GFX_HEIGHT_PX) * GFX_WIDTH
        origin = GFX_ADDRESS + x_origin_byte + y_origin_byte #To lowest byte
        shift_amount = self.get_reg1_val() % GFX_WIDTH_PX % 8

        self.register[0xF] = 0x00
        for y in range(height):
            sprite =  list(bin(self.ram[ self.index_register + y ])[2:].zfill(8))
            for x in range(2):
                x_offset = x if x_origin_byte+x != GFX_WIDTH else 1-GFX_WIDTH
                working_byte = origin + ( (y * GFX_WIDTH) % GFX_RESOLUTION) + x_offset

                original = self.ram[ working_byte ]
                b = list(bin(original)[2:].zfill(8))
                if x == 0:
                    b[shift_amount:] = sprite[shift_amount:]
                else:
                    b[:shift_amount] = sprite[:shift_amount]

                self.ram[ working_byte ] = int(''.join(b),2)

                if (( self.ram[ working_byte ] ^ original) & original):
                    self.register[0xF] = 0xFF



    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Hex Extraction ( Private )

    def get_address(self):
        return int(self.hex_instruction[1:4], 16)

    def get_reg1(self):
        return int(self.hex_instruction[1],16)

    def get_reg2(self):
        return int(self.hex_instruction[2],16)

    def get_reg1_val(self):
        return self.register[int(self.hex_instruction[1],16) ]

    def get_reg2_val(self):
        return self.register[int(self.hex_instruction[2],16) ]

    def get_lower_byte(self):
        return int(self.hex_instruction[2:4], 16)

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Helpers for special Op Codes

    def handle_load_key(self):
        if self.waiting_for_key:
            k = int(''.join(['1' if x else '0' for x in self.keypad]))
            nk = ( (k ^ self.prev_keypad) & k ).find('1')
            if nk != -1: # Was a new key pressed?
                self.register[ self.get_reg1() ] = nk
                self.program_counter += 2
            else:
                return
        else:
            self.prev_keypad = int(''.join(['1' if x else '0' for x in self.keypad]))

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Debug

    def dump_ram(self):
        for i,val in enumerate(self.ram):
            if val is None:
                print('0x' + hex(i)[2:].zfill(3))
            else:
                print('0x' + hex(i)[2:].zfill(3) + "  " + '0x' + hex(val)[2:].zfill(2))

    def dump_gfx(self):
        for i,b in enumerate(self.ram[ GFX_ADDRESS : GFX_ADDRESS + GFX_RESOLUTION ]):
            if i%8 == 0:
                print("")
            print( bin(b)[2:].zfill(8).replace('1','X').replace('0','.'), end="")
        print("")

def parse_args():
    parser = argparse.ArgumentParser(description='Guacamole is a Chip-8 emulator ...')
    parser.add_argument('rom', help='ROM to load and play.')
    parser.add_argument("-f","--frequency", default=60,help='Frequency (in Hz) to target.')
    opts = parser.parse_args()

    if not os.path.isfile(opts.rom):
        raise OSError("File '" + opts.rom + "' does not exist.")

    if opts.frequency:
        opts.frequency = int(opts.frequency)

    return opts

def main(opts):
    guac = guacamole(opts.rom, opts.frequency, opts.frequency)
    for i in range(1000):
        guac.cpu_tick()
    guac.dump_gfx()
    return
    try:
        while True:
            guac.run()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main(parse_args())
