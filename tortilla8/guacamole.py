#!/usr/bin/python3

import os       # Rom Loading
import time     # CPU Frequency
import random   # RND instruction
from enum import Enum
from tortilla8.salsa import salsa
from collections import namedtuple, deque
from .constants.reg_rom_stack import BYTES_OF_RAM, PROGRAM_BEGIN_ADDRESS, NUMB_OF_REGS,
                                     MAX_ROM_SIZE, STACK_ADDRESS, STACK_SIZE
from .constants.graphics import GFX_FONT, GFX_FONT_ADDRESS, GFX_RESOLUTION, GFX_ADDRESS,
                                GFX_WIDTH, GFX_HEIGHT_PX, GFX_WIDTH_PX

# TODO 'Load' logs fatal errors right now, should all instructions check the structure of input args?

class Emulation_Error(Enum):
    _Information = 1
    _Warning     = 2
    _Fatal       = 3

    def __str__(self):
        return self.name[1:]

    @classmethod
    def from_string(self, value):
        value = value.lower()
        if (value == "info") or (value == "information"):
            return self._Information
        if (value == "warning"):
            return self._Warning
        if (value == "fatal"):
            return self._Fatal
        return None

rewind_data = namedtuple('rewind_data', 'gfx_buffer register index_register \
 delay_timer_register sound_timer_register program_counter calling_pc \
 dis_ins stack stack_pointer draw_flag waiting_for_key spinning')

class guacamole:
    """
    Guacamole is an emulator class that will happily emulate a Chip-8 ROM
    at a select frequency with various other options available.
    """

    def __init__(self, rom=None, cpuhz=200, audiohz=60, delayhz=60,
                 init_ram=False, legacy_shift=False, err_unoffical="None",
                 rewind_depth=5000):
        '''
        Init the RAM, registers, instruction information, IO, load the ROM etc. ROM
        is a path to a chip-8 rom, *hz is the frequency to target for for the cpu,
        audio register, or delay register. Init_Ram signals that the RAM should be
        initialized to zero. Not initializing the RAM is a great way to find
        incorrect RAM accesses. Legacy Shift can be set to true to use the older
        'Store shift Y to X' rather than 'Shift X' method of bitshifting. Lastly,
        err_unoffical can be used to log an error when an offical instruction is
        found in the program.
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

        # Instruction modification settings
        self.legacy_shift = legacy_shift
        self.warn_exotic_ins = Emulation_Error.from_string(err_unoffical)

        # Rewind Info
        self.rewind_frames = deque(maxlen=rewind_depth)

        # # # # # # # # # # # # # # # # # # # # # # # #
        # Private

        # Warning control
        self.debug = False
        self.error_log = []

        # Timming variables
        self.cpu_hz     = cpuhz
        self.cpu_wait   = 1/cpuhz
        self.cpu_time   = 0
        self.audio_hz   = audiohz
        self.audio_wait = 1/audiohz
        self.audio_time = 0
        self.delay_hz   = delayhz
        self.delay_wait = 1/delayhz
        self.delay_time = 0

        # Load Font, clear screen
        self.ram[GFX_FONT_ADDRESS:GFX_FONT_ADDRESS + len(GFX_FONT)] = GFX_FONT
        self.ram[GFX_ADDRESS:GFX_ADDRESS + GFX_RESOLUTION] = [0x00] * GFX_RESOLUTION

        # Notification
        self.log("Initializing emulator at " + str(cpuhz) + " hz" ,Emulation_Error._Information)

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
        Loads a Chip-8 ROM from a file into the RAM.
        '''
        file_size = os.path.getsize(file_path)
        if file_size > MAX_ROM_SIZE:
            self.log("Rom file exceeds maximum rom size of " + str(MAX_ROM_SIZE) + \
                " bytes" , Emulation_Error._Warning)

        with open(file_path, "rb") as fh:
            self.ram[PROGRAM_BEGIN_ADDRESS:PROGRAM_BEGIN_ADDRESS + file_size] = \
                [int.from_bytes(fh.read(1), 'big') for i in range(file_size)]
            self.log("Rom file loaded" , Emulation_Error._Information)

    def reset(self, rom=None, cpuhz=None, audiohz=None, delayhz=None, init_ram=None):
        '''
        Resets the emulator to run another game. By default all frequencies
        and the init_ram flag are preserved.
        '''
        if cpuhz is None: cpuhz = self.cpu_hz
        if audiohz is None: audiohz = self.audio_hz
        if delayhz is None: delayhz = self.delay_hz
        if init_ram is None: init_ram = True if self.ram[0] == 0 else False
        self.__init__(rom, cpuhz, audiohz, delayhz, init_ram)

    def run(self):
        '''
        Attempt to run the next instruction. This should be called as a part
        of the main loop, it insures that the CPU and timers execute at the
        target frequency.
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
        Ticks the CPU forward a cycle without regard for the target frequency.
        '''
        # Handle the ld reg,k instruction
        if self.waiting_for_key:
            self.handle_load_key()
            return
        else:
            self.prev_keypad = self.decode_keypad()

        # Record current PC, Reset error log
        self.calling_pc = self.program_counter
        self.error = []

        # Dissassemble next instruction
        self.dis_ins = None
        try:
            self.dis_ins = salsa(self.ram[self.program_counter:self.program_counter+2])
        except TypeError:
            self.log("No instruction found at " + hex(self.program_counter), Emulation_Error._Fatal)
            return

        # Execute instruction
        if self.dis_ins.is_valid:
            self.ins_tbl[self.dis_ins.mnemonic]()
            if self.warn_exotic_ins and self.dis_ins.unoffical_op:
                self.log("Unoffical instruction '" + self.dis_ins.mnemonic + \
                    "' executed at " + hex(self.program_counter), self.warn_exotic_ins)

        # Error out. NOTE: to add new instruction update OP_CODES and self.ins_tbl
        else:
            self.log("Unknown instruction " + self.dis_ins.hex_instruction + " at " + \
                hex(self.program_counter), Emulation_Error._Fatal)

        # Print what was processed to screen
        if self.debug:
            self.enforce_rules()
            print( hex(self.calling_pc) + " " + self.dis_ins.hex_instruction + " " + self.dis_ins.mnemonic )

        # Increment the PC, Store Rewind Data
        self.program_counter += 2
        self.store_rewind_data()

    def store_rewind_data(self):
        '''
        Save the current state of the emulator.
        Without rewind guac/platter use 7.6 megs of RAM. Using rewind uses
        2.64 kB of ram per frame.
        '''
        if self.rewind_frames.maxlen == 0:
            return
        gfx_buffer = self.ram[GFX_ADDRESS:GFX_ADDRESS + GFX_RESOLUTION]
        self.rewind_frames.append( rewind_data(gfx_buffer, self.register.copy(), self.index_register,
            self.delay_timer_register, self.sound_timer_register, self.program_counter, self.calling_pc,
            self.dis_ins + (), self.stack.copy(), self.stack_pointer, self.draw_flag, self.waiting_for_key,
            self.spinning ) )

    def rewind(self, depth):
        '''
        "Un-ticks" the CPU depth many times.
        '''
        frame = None
        try:
            for _ in range(depth):
                frame = self.rewind_frames.pop()
        except IndexError:
            if frame is None:
                return
        self.ram[GFX_ADDRESS:GFX_ADDRESS + GFX_RESOLUTION] = \
            frame.gfx_buffer
        self.register, self.index_register = \
            frame.register, frame.index_register
        self.delay_timer_register, self.sound_timer_register = \
            frame.delay_timer_register, frame.sound_timer_register
        self.program_counter, self.calling_pc = \
            frame.program_counter, frame.calling_pc
        self.dis_ins, self.stack, self.stack_pointer = \
            self.dis_ins, frame.stack, frame.stack_pointer
        self.draw_flag, self.waiting_for_key, self.spinning = \
            frame.draw_flag, frame.waiting_for_key, frame.spinning

    def log(self, message, error_type):
        '''
        Logs an Emulation_Error that can be latter addressed by the instantiator
        or prints it to screen if called from command line.
        '''
        if self.debug:
            print(str(error_type) + ": " + message)
            if error_type is Emulation_Error._Fatal:
                print("Fatal error has occured, please reset.")
        else:
            self.error_log.append( (error_type, message) )

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Instructions ( Private ) - All 20 mnemonics, 35 total instructions
    # Add-3 SE-2 SNE-2 LD-11 JP-2 (mnemonics w/ extra instructions)

    def i_cls(self):
        self.ram[GFX_ADDRESS:GFX_ADDRESS + GFX_RESOLUTION] = [0x00] * GFX_RESOLUTION
        self.draw_flag = True

    def i_ret(self):
        self.stack_pointer -= 1
        if self.stack_pointer < 0:
            self.log("Stack underflow", Emulation_Error._Fatal)
        self.program_counter = self.stack.pop()

    def i_sys(self):
        self.log("RCA 1802 call to " + hex( self.get_address()) + " was ignored.", Emulation_Error._Warning)

    def i_call(self):
        if STACK_ADDRESS:
            self.ram[stack_pointer] = self.program_counter
        self.stack_pointer += 1
        self.stack.append(self.program_counter)
        if self.stack_pointer > STACK_SIZE:
            self.log("Stack overflow. Stack is now size " + self.stack_pointer, Emulation_Error._Warning)
        self.program_counter = self.get_address() - 2

    def i_skp(self):
        if self.keypad[ self.get_reg1_val() & 0x0F ]:
            self.program_counter += 2

    def i_sknp(self):
        if not self.keypad[ self.get_reg1_val() & 0x0F ]:
            self.program_counter += 2

    def i_se(self):
        comp =  self.get_lower_byte() if "byte" in self.dis_ins.mnemonic_arg_types else self.get_reg2_val()
        if  self.get_reg1_val() == comp:
            self.program_counter += 2

    def i_sne(self):
        comp =  self.get_lower_byte() if "byte" in self.dis_ins.mnemonic_arg_types else self.get_reg2_val()
        if  self.get_reg1_val() != comp:
            self.program_counter += 2

    def i_shl(self):
        if self.legacy_shift:
            self.register[0xF] = 0x01 if self.get_reg2_val() >= 0x80 else 0x0
            self.register[ self.get_reg1() ] = ( self.get_reg2_val() << 1 ) & 0xFF
        else:
            self.register[0xF] = 0x01 if self.get_reg1_val() >= 0x80 else 0x0
            self.register[ self.get_reg1() ] = ( self.get_reg1_val() << 1 ) & 0xFF

    def i_shr(self):
        if self.legacy_shift:
            self.register[0xF] = 0x01 if ( self.get_reg2_val() % 2) == 1 else 0x0
            self.register[ self.get_reg1() ] = self.get_reg2_val() >> 1
        else:
            self.register[0xF] = 0x01 if ( self.get_reg1_val() % 2) == 1 else 0x0
            self.register[ self.get_reg1() ] = self.get_reg1_val() >> 1

    def i_or(self):
        self.register[ self.get_reg1() ] = self.get_reg1_val() | self.get_reg2_val()

    def i_and(self):
        self.register[ self.get_reg1() ] = self.get_reg1_val() & self.get_reg2_val()

    def i_xor(self):
        self.register[ self.get_reg1() ] = self.get_reg1_val() ^ self.get_reg2_val()

    def i_sub(self):
        self.register[0xF] = 0x01 if self.get_reg1_val() > self.get_reg2_val() else 0x00
        self.register[ self.get_reg1() ] = self.get_reg1_val() - self.get_reg2_val()
        self.register[ self.get_reg1() ] &= 0xFF

    def i_subn(self):
        self.register[0xF] = 0x01 if self.get_reg2_val() > self.get_reg1_val() else 0x00
        self.register[ self.get_reg1() ] = self.get_reg2_val() - self.get_reg1_val()
        self.register[ self.get_reg1() ] &= 0xFF

    def i_jp(self):
        init_pc = self.program_counter
        if 'v0' in self.dis_ins.mnemonic_arg_types:
            self.program_counter = self.get_address() + self.register[0] - 2
        else:
            self.program_counter = self.get_address() - 2

        if init_pc == self.program_counter + 2:
            self.spinning = True

    def i_rnd(self):
        self.register[ self.get_reg1() ] = random.randint(0, 255) & self.get_lower_byte()

    def i_add(self):
        if 'byte' in self.dis_ins.mnemonic_arg_types:
            self.register[ self.get_reg1() ] += self.get_lower_byte()
            self.register[ self.get_reg1() ] &= 0xFF

        elif 'i' in self.dis_ins.mnemonic_arg_types:
            self.index_register += self.get_reg1_val()
            self.index_register &= 0xFFF

        else: # Reg + Reg
            self.register[ self.get_reg1() ] += self.get_reg2_val()
            self.register[ self.get_reg1() ] &= 0xFF
            self.register[0xF] = 0x00
            if  self.get_reg1_val() + self.get_reg2_val() > 0xFF:
                self.register[ self.get_reg1() ] &= 0xFF
                self.register[0xF] = 0x01

    def i_ld(self):
        arg1 = self.dis_ins.mnemonic_arg_types[0]
        arg2 = self.dis_ins.mnemonic_arg_types[1]

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
                self.log("Loads with argument type '" + arg2 + "' are not supported.", Emulation_Error._Fatal)

        elif 'register' is arg2:
            if   'dt' is arg1: self.delay_timer_register =  self.get_reg1_val()
            elif 'st' is arg1: self.sound_timer_register =  self.get_reg1_val()
            elif 'f'  is arg1: self.index_register = GFX_FONT_ADDRESS + ( 5 * self.get_reg1_val() )
            elif 'b'  is arg1:
                bcd = str( self.get_reg1_val() ).zfill(3)
                for i in range(3):
                    self.ram[self.index_register + i] = int(bcd[i])

            elif '[i]' == arg1:
                for i in range( self.get_reg1()):
                    self.ram[self.index_register + i] = self.register[i]

            else:
                self.log("Loads with argument type '" + arg1 + "' are not supported.", Emulation_Error._Fatal)

        elif 'i' is arg1 and 'address' is arg2:
            self.index_register =  self.get_address()

        else:
            self.log("Loads with argument types '" + arg1 + "' and '" + arg2 +  \
                "' are not supported.", Emulation_Error._Fatal)

    def i_drw(self):
        self.draw_flag = True
        height = int(self.dis_ins.hex_instruction[3],16)
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
                working_byte = GFX_ADDRESS + (( x_origin_byte + y_origin_byte + \
                    (y * GFX_WIDTH) + x_offset ) % GFX_RESOLUTION)

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
                self.ram[ working_byte ] = \
                    int(untouched_chunk + xor_chunk,2) if x == 0 else int(xor_chunk + untouched_chunk,2)

                if bin( ( self.ram[ working_byte ] ^ original ) & original ).find('1') != -1:
                    self.register[0xF] = 0x01

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Hex Extraction ( Private )

    def get_address(self):
        return int(self.dis_ins.hex_instruction[1:4], 16)

    def get_reg1(self):
        return int(self.dis_ins.hex_instruction[1],16)

    def get_reg2(self):
        return int(self.dis_ins.hex_instruction[2],16)

    def get_reg1_val(self):
        return self.register[int(self.dis_ins.hex_instruction[1],16) ]

    def get_reg2_val(self):
        return self.register[int(self.dis_ins.hex_instruction[2],16) ]

    def get_lower_byte(self):
        return int(self.dis_ins.hex_instruction[2:4], 16)

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Helpers for Load Key ( Private )

    def decode_keypad(self):
        return int(''.join(['1' if x else '0' for x in self.keypad]),2)

    def handle_load_key(self):
        k = self.decode_keypad()
        nk = bin( (k ^ self.prev_keypad) & k )[2:].zfill(16).find('1')
        if nk != -1:
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
                print()
            print( bin(b)[2:].zfill(8).replace('1','X').replace('0','.'), end='')
        print()

    def dump_reg(self):
        for i,val in enumerate(self.register):
            if (i % 4) == 0:
                print()
            print(hex(i) + " 0x" + hex(val)[2:].zfill(2) + "    ", end='')
        print()

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
        return "\nPC: " + hex(self.program_counter) + " INS: " + self.dis_ins.hex_instruction

