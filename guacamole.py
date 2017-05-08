#!/usr/bin/python3

import re       # Matching Op Code
import os       # Rom Loading
import time     # CPU Frequency
import random   # RND instruction
import argparse # Command line
from enum import Enum
from mem_addr_register_constants import *
from opcode_constants import *

# TODO 'Load' logs fatal warnings right now, should all instructions check the structure of input args?
# TODO Shift L/R behavior needs a toggle for "old" and "new" behavior
# TODO Log a warning when running a unoffical instruction? (enforce flag?)
# TODO add comments

class Emulation_Error(Enum):
    _Information = 1
    _Warning     = 2
    _Fatal       = 3

    def __str__(self):
        return self.name[1:]

class guacamole:

    def __init__(self, rom=None, cpuhz=200, audiohz=60, delayhz=60, init_ram=False):
        '''
        Init
        '''
        random.seed()

        # # # # # # # # # # # # # # # # # # # # # # # #
        # Public

        # RAM
        self.ram = [0x00] * BYTES_OF_RAM if init_ram else [None] * BYTES_OF_RAM

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
        self.draw_flag   = False
        self.waiting_for_key = False
        self.spinning = False

        # Stack
        self.stack = []
        self.stack_pointer = 0

        # # # # # # # # # # # # # # # # # # # # # # # #
        # Private

        # Warning control
        self.log_to_screen = False
        self.error_log = []

        # Timming variables
        self.cpu_wait   = 1/cpuhz
        self.cpu_time   = 0
        self.audio_wait = 1/audiohz
        self.audio_time = 0
        self.delay_wait = 1/delayhz
        self.delay_time = 0

        # Load Font, clear screen
        self.ram[FONT_ADDRESS:FONT_ADDRESS + len(FONT)] = [i for i in FONT]
        self.ram[GFX_ADDRESS:GFX_ADDRESS + GFX_RESOLUTION] = [0x00] * GFX_RESOLUTION

        # Notification
        self.emu_log("Initializing emulator at " + str(cpuhz) + " hz" ,Emulation_Error._Information)

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
            self.emu_log("Rom file exceeds maximum rom size of " + str(MAX_ROM_SIZE) + " bytes" , Emulation_Error._Warning)

        with open(file_path, "rb") as fh:
            self.ram[PROGRAM_BEGIN_ADDRESS:PROGRAM_BEGIN_ADDRESS + file_size] = [int.from_bytes(fh.read(1), 'big') for i in range(file_size)]
            self.emu_log("Rom file loaded" , Emulation_Error._Information)

    def reset(self, rom=None, cpuhz=None, audiohz=None, delayhz=None, init_ram=None):
        '''
        reset
        '''
        if cpuhz is None: cpuhz = int(1/self.cpu_wait)
        if audiohz is None: audiohz = int(1/self.audio_wait)
        if delayhz is None: delayhz = int(1/self.delay_wait)
        if init_ram is None: init_ram = True if self.ram[0] == 0 else False
        self.__init__(rom, cpuhz, audiohz, delayhz, init_ram)

    def run(self):
        '''
        run
        '''
        if self.cpu_wait <= (time.time() - self.cpu_time):
            self.cpu_time = time.time()
            self.cpu_tick()

        if self.audio_wait <= (time.time() - self.audio_time):
            self.audio_time = time.time()
            self.sound_timer_register -= 1 if self.sound_timer_register != 0 else 0

        if self.delay_wait <= (time.time() - self.delay_time):
            self.delay_time = time.time()
            self.delay_timer_register -= 1 if self.delay_timer_register != 0 else 0

    def cpu_tick(self):
        '''
        cpu_tick
        '''
        # Handle the ld k,reg instruction
        if self.waiting_for_key:
            self.handle_load_key()
            return
        else:
            self.prev_keypad = self.decode_keypad()

        # Reset error log
        self.error = []

        # Fetch instruction from ram
        found = False
        try:
            self.hex_instruction =  hex( self.ram[self.program_counter + 0] )[2:].zfill(2)
            self.hex_instruction += hex( self.ram[self.program_counter + 1] )[2:].zfill(2)
        except TypeError:
            self.emu_log("No instruction found at " + hex(self.program_counter), Emulation_Error._Fatal)
            return

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
            self.emu_log("Unknown instruction " + self.hex_instruction + " at " + hex(self.program_counter), Emulation_Error._Fatal)

        # Print what was processed to screen
        if self.log_to_screen:
            print( hex(self.program_counter) + " " + self.hex_instruction + " " + self.mnemonic )

        # Increment the PC
        self.program_counter += 2

    def emu_log(self, message, error_type):
        '''
        emu_log
        '''
        if self.log_to_screen:
            print(str(error_type) + ": " + message)
            if error_type is Emulation_Error._Fatal:
                print("Fatal error has occured, please reset.")
        else:
            self.error_log.append( (error_type, message) )

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Instructions ( Private )

    def i_cls(self):
        self.ram[GFX_ADDRESS:GFX_ADDRESS + GFX_RESOLUTION] = [0x00] * GFX_RESOLUTION
        self.draw_flag = True

    def i_ret(self):
        self.stack_pointer -= 1
        if self.stack_pointer < 0:
            self.emu_log("Stack underflow", )
        self.program_counter = self.stack.pop()

    def i_sys(self):
        self.emu_log("RCA 1802 call to " + hex( self.get_address()) + " was ignored.", Emulation_Error._Warning)

    def i_call(self):
        if STACK_ADDRESS:
            self.ram[stack_pointer] = self.program_counter
        self.stack_pointer += 1
        self.stack.append(self.program_counter)
        if self.stack_pointer > STACK_SIZE:
            self.emu_log("Warning: Stack overflow. Stack is now size " + self.stack_pointer, Emulation_Error._Warning)
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
        self.register[0xF] = 0xFF if self.get_reg1_val() >= 0x80 else 0x0
        self.register[ self.get_reg1() ] = ( self.get_reg1_val() << 1) & 0xFF

    def i_shr(self):                                         #TODO add option to respect "old" shift
        self.register[0xF] = 0xFF if ( self.get_reg1_val() % 2) == 1 else 0x0
        self.register[ self.get_reg1() ] = self.get_reg1_val() >> 1


    def i_or(self):
        self.register[ self.get_reg1() ] = self.get_reg1_val() | self.get_reg2_val()

    def i_and(self):
        self.register[ self.get_reg1() ] = self.get_reg1_val() & self.get_reg2_val()

    def i_xor(self):
        self.register[ self.get_reg1() ] = self.get_reg1_val() ^ self.get_reg2_val()

    def i_sub(self):
        self.register[0xF] = 0xFF if  self.get_reg1_val() >  self.get_reg2_val() else 0x00
        self.register[ self.get_reg1() ] = self.get_reg1_val() - self.get_reg2_val()
        self.register[ self.get_reg1() ] &= 0xFF

    def i_subn(self):
        self.register[0xF] = 0xFF if self.get_reg2_val() >  self.get_reg1_val() else 0x00
        self.register[ self.get_reg1() ] = self.get_reg2_val() - self.get_reg1_val()
        self.register[ self.get_reg1() ] &= 0xFF

    def i_jp(self):
        init_pc = self.program_counter
        if 'v0' in self.mnemonic_arg_types:
            self.program_counter = self.get_address() + self.register[0] - 2
        else:
            self.program_counter = self.get_address() - 2

        if init_pc == self.program_counter + 2:
            self.spinning = True

    def i_rnd(self):
        self.register[ self.get_reg1() ] = random.randint(0, 255) & self.get_lower_byte()

    def i_add(self):
        if 'byte' in self.mnemonic_arg_types:
            self.register[ self.get_reg1() ] += self.get_lower_byte()
            self.register[ self.get_reg1() ] &= 0xFF

        elif 'i' in self.mnemonic_arg_types:
            self.index_register += self.get_reg1_val()
            self.index_register &= 0xFFF

        else: # Reg + Reg
            self.register[ self.get_reg1() ] += self.get_reg2_val()
            self.register[ self.get_reg1() ] &= 0xFF
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
                for i in range( self.get_reg1() ):
                    self.register[i] = self.ram[self.index_register + i]

            else:
                self.emu_log("Loads with argument type '" + arg2 + "' are not supported.", Emulation_Error._Fatal)

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
                self.emu_log("Loads with argument type '" + arg1 + "' are not supported.", Emulation_Error._Fatal)

        elif 'i' is arg1 and 'address' is arg2:
            self.index_register =  self.get_address()

        else:
            self.emu_log("Loads with argument types '" + arg1 + "' and '" + arg2 +  "' are not supported.", Emulation_Error._Fatal)

    def i_drw(self):
        self.draw_flag = True
        height = int(self.hex_instruction[3],16)
        x_origin_byte = int( self.get_reg1_val() / 8 ) % GFX_WIDTH
        y_origin_byte = (self.get_reg2_val() % GFX_HEIGHT_PX) * GFX_WIDTH
        shift_amount = self.get_reg1_val() % GFX_WIDTH_PX % 8

        self.register[0xF] = 0x00
        for y in range(height):
            sprite =  bin(self.ram[ self.index_register + y ])[2:].zfill(8)
            for x in range(2):
                if shift_amount == 0 and x == 1:
                    continue

                x_offset = x if x_origin_byte + x != GFX_WIDTH else 1-GFX_WIDTH
                working_byte = GFX_ADDRESS + (( x_origin_byte + y_origin_byte + (y * GFX_WIDTH) + x_offset ) % GFX_RESOLUTION)

                original = self.ram[ working_byte ]
                b_list = bin(original)[2:].zfill(8)
                if x == 0:
                    untouched_chunk = b_list[:shift_amount]
                    original_chunk  = b_list[shift_amount:]
                    sprite_chunk    = sprite[:8-shift_amount]
                if x == 1:
                    untouched_chunk = b_list[shift_amount:]
                    original_chunk  = b_list[:shift_amount]
                    sprite_chunk    = sprite[8-shift_amount:]

                xor_chunk = bin(int(original_chunk,2) ^ int(sprite_chunk,2))[2:].zfill(len(original_chunk))
                self.ram[ working_byte ] = int(untouched_chunk + xor_chunk,2) if x == 0 else int(xor_chunk + untouched_chunk,2)

                if bin( ( self.ram[ working_byte ] ^ original ) & original ).find('1') != -1:
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

    def decode_keypad(self):
        return int(''.join(['1' if x else '0' for x in self.keypad]))

    def handle_load_key(self):
        k = self.decode_keypad()
        nk = bin( (k ^ self.prev_keypad) & k )[2:].zfill(16).find('1')
        if nk != -1: # Was a new key pressed?
            self.register[ self.get_reg1() ] = nk
            self.program_counter += 2
            self.waiting_for_key = False

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Debug

    def dump_ram(self):
        for i,val in enumerate(self.ram):
            if val is None:
                print('0x' + hex(i)[2:].zfill(3))
            else:
                print('0x' + hex(i)[2:].zfill(3) + '  ' + '0x' + hex(val)[2:].zfill(2))

    def dump_gfx(self):
        for i,b in enumerate(self.ram[ GFX_ADDRESS : GFX_ADDRESS + GFX_RESOLUTION ]):
            if i%8 == 0:
                print('')
            print( bin(b)[2:].zfill(8).replace('1','X').replace('0','.'), end='')
        print('')

    def dump_reg(self):
        for i,val in enumerate(self.register):
            if (i % 4) == 0:
                print('')
            print(hex(i) + " 0x" + hex(val)[2:].zfill(2) + "    ", end='')
        print('')

    def dump_keypad(self):
        r_val = ''
        for i,val in enumerate(self.keypad):
            if val:
                r_val += hex(i) + " "
        return r_val

    def enforce_rules(self):
        assert(self.index_register is not None)
        assert(self.index_register <= 0xFFF)
        assert(self.index_register >= 0x000)
        assert(self.delay_timer_register <= 0xFF)
        assert(self.delay_timer_register >= 0x00)
        assert(self.sound_timer_register <= 0xFF)
        assert(self.sound_timer_register >= 0x00)
        for i,val in enumerate(self.register):
            assert val is not None, "Register " + hex(i) + " has value 'None'" + self.dump_pc()
            assert val >= 0x00, "Register " + hex(i) + "is less than 0x00" + self.dump_pc()
            assert val <= 0xFF, "Register " + hex(i) + "is greater than 0xFF" + self.dump_pc()
        for i,val in enumerate(self.ram):
            if val is None: continue
            assert val >= 0x00, "Ram Address " + hex(i) + "is less than 0x00" + self.dump_pc()
            assert val <= 0xFF, "Ram Address " + hex(i) + "is greater than 0xFF" + self.dump_pc()

    def dump_pc(self):
        return "\nPC: " + hex(self.program_counter) + " INS: " + self.hex_instruction

def parse_args():
    parser = argparse.ArgumentParser(description='Guacamole is a Chip-8 emulator ...')
    parser.add_argument('rom', help='ROM to load and play.')
    parser.add_argument("-f","--frequency", default=5,help='Frequency (in Hz) to target for CPU.')
    parser.add_argument("-st","--soundtimer", default=60,help='Frequency (in Hz) to target for the audio timmer.')
    parser.add_argument("-dt","--delaytimer", default=60,help='Frequency (in Hz) to target for the delay timmer.')
    parser.add_argument('-i','--initram', help='Initialize RAM to all zero values.', action='store_true')
    opts = parser.parse_args()

    if not os.path.isfile(opts.rom):
        raise OSError("File '" + opts.rom + "' does not exist.")

    if opts.frequency:
        opts.frequency = int(opts.frequency)

    return opts

def main(opts):
    guac = guacamole(opts.rom, opts.frequency, opts.soundtimer, opts.delaytimer, opts.initram)
    guac.log_to_screen = True
    try:
        while True:
            guac.run()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main(parse_args())
