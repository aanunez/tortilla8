#!/usr/bin/env python3

from . import export
from . import EmulationError
from os.path import getsize
from time import time
from .salsa import Salsa
from collections import namedtuple, deque
from .instructions import *
from .constants.reg_rom_stack import BYTES_OF_RAM, PROGRAM_BEGIN_ADDRESS, \
                                     NUMB_OF_REGS, MAX_ROM_SIZE
from .constants.graphics import GFX_FONT, GFX_FONT_ADDRESS, GFX_RESOLUTION, GFX_ADDRESS
__all__ = []

# TODO Rewind bug when waiting for keypress
# TODO Rewind isn't storing all of RAM, so ld [i], reg will break rewind

@export
class RewindData( namedtuple('RewindData', 'gfx_buffer register index_register ' + \
    'delay_timer_register sound_timer_register program_counter calling_pc ' + \
    'dis_ins stack stack_pointer draw_flag waiting_for_key spinning') ):
    pass

@export
class Guacamole:
    '''
    Guacamole is an emulator class that will happily emulate a Chip-8 ROM
    at a select frequency with various other options available.
    '''
    def __init__(self, rom=None, cpuhz=200, audiohz=60, delayhz=60,
                 init_ram=False, legacy_shift=False, err_unoffical="None",
                 rewind_depth=1000):
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
        self.warn_exotic_ins = EmulationError.from_string(err_unoffical)

        # Rewind Info
        self.rewind_frames = None if rewind_depth == 0 else deque(maxlen=rewind_depth)

        # # # # # # # # # # # # # # # # # # # # # # # #
        # Private (ish)

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
        self.log("Initializing emulator at " + str(cpuhz) + " hz" ,EmulationError._Information)
        self.log("Max Rewind of " + str(rewind_depth) + " instructions" ,EmulationError._Information)

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
                " bytes" , EmulationError._Warning)

        with open(file_path, "rb") as fh:
            self.ram[PROGRAM_BEGIN_ADDRESS:PROGRAM_BEGIN_ADDRESS + file_size] = \
                [int.from_bytes(fh.read(1), 'big') for i in range(file_size)]
            self.log("Rom file loaded" , EmulationError._Information)

    def reset(self, rom=None, cpuhz=None, audiohz=None, delayhz=None,
              init_ram=None, legacy_shift=None, err_unoffical="None",
              rewind_depth=1000):
        '''
        Resets the emulator to run another game. By default all frequencies
        and the init_ram flag are preserved.
        '''
        if cpuhz is None: cpuhz = self.cpu_hz
        if audiohz is None: audiohz = self.audio_hz
        if delayhz is None: delayhz = self.delay_hz
        if init_ram is None: init_ram = True if self.ram[0] == 0 else False
        if legacy_shift is None: legacy_shift = self.legacy_shift
        if err_unoffical is None: err_unoffical = str(self.warn_exotic_ins)
        if rewind_frames is None:
            rewind_frames =  0 if self.rewind_frames == None else self.rewind_frames.maxlen

        self.__init__(rom, cpuhz, audiohz, delayhz,
                      init_ram, legacy_shift, err_unoffical,
                      rewind_frames)

    def run(self):
        '''
        Attempt to run the next instruction. This should be called as a part
        of the main loop, it insures that the CPU and timers execute at the
        target frequency.
        '''
        if self.cpu_wait <= (time() - self.cpu_time):
            self.cpu_time = time()
            self.cpu_tick()

        if self.audio_wait <= (time() - self.audio_time):
            self.audio_time = time()
            self.sound_timer_register -= 1 if self.sound_timer_register != 0 else 0

        if self.delay_wait <= (time() - self.delay_time):
            self.delay_time = time()
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
            self.dis_ins = Salsa(self.ram[self.program_counter:self.program_counter+2])
        except TypeError:
            self.log("No instruction found at " + hex(self.program_counter), EmulationError._Fatal)
            return

        # Execute instruction
        if self.dis_ins.is_valid:
            if self.warn_exotic_ins and self.dis_ins.unoffical_op:
                self.log("Unoffical instruction '" + self.dis_ins.mnemonic + \
                    "' executed at " + hex(self.program_counter), self.warn_exotic_ins)
            self.ins_tbl[self.dis_ins.mnemonic](self)

        # Error out. NOTE: to add new instruction update OP_CODES and self.ins_tbl
        elif self.dis_ins.is_super8:
            self.log("Super8 instruction " + self.dis_ins.hex_instruction + " at " + \
                hex(self.program_counter), EmulationError._Fatal)
        elif self.dis_ins.is_banned:
            self.log("Banned instruction (makes a modification to VF)" + self.dis_ins.hex_instruction + \
                " at " + hex(self.program_counter), EmulationError._Fatal)
        else:
            self.log("Unknown instruction " + self.dis_ins.hex_instruction + " at " + \
                hex(self.program_counter), EmulationError._Fatal)

        # Print what was processed to screen
        if self.debug:
            self.enforce_rules()
            print( hex(self.calling_pc) + " " + self.dis_ins.hex_instruction + " " + self.dis_ins.mnemonic )

        # Increment the PC, Store Rewind Data
        self.program_counter += 2
        self.store_RewindData()

    def store_RewindData(self):
        '''
        Save the current state of the emulator.
        Without rewind guac/platter use 7.6 megs of RAM. Using rewind uses
        2.64 kB of ram per frame.
        '''
        if self.rewind_frames is None:
            return
        gfx_buffer = self.ram[GFX_ADDRESS:GFX_ADDRESS + GFX_RESOLUTION]
        self.rewind_frames.append( RewindData(gfx_buffer, self.register.copy(), self.index_register,
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

    def graphics(self):
        '''
        Generator that returns true/false if the nth pixel is set.
        '''
        for i in self.ram[GFX_ADDRESS:GFX_ADDRESS + GFX_RESOLUTION]:
            for j in bin(i):
                yield j=='1'

    def log(self, message, error_type):
        '''
        Logs an EmulationError that can be latter addressed by the instantiator
        or prints it to screen if called from command line.
        '''
        if self.debug:
            print(str(error_type) + ": " + message)
            if error_type is EmulationError._Fatal:
                print("Fatal error has occured, please reset.")
        else:
            self.error_log.append( (error_type, message) )

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Helpers for Load Key ( Private )

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

