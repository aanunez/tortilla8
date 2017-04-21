#!/usr/bin/python3

import re
import os
import time
import random
import argparse
from tortilla8_constants import *

#TODO allow audio in seprate thread

class guacamole:

    def __init__(self, rom=None):
        self.ram = [None]*BYTES_OF_RAM
        self.program_counter = PROGRAM_BEGIN_ADDRESS

        # Stack emulation, only used if STACK_ADDRESS is not defined
        self.stack = []
        self.stack_pointer = 0

        self.key_state = 0x00
        self.opcode = []

        self.register = [0]*16
        self.index_register = 0
        self.delay_timer_register = 0
        self.sound_timer_register = 0

        random.seed()

        # Load Font data
        for i,val in enumerate(FONT):
            self.ram[FONT_ADDRESS + i] = val

        self.clear_gfx()

        # Load Rom
        if rom is not None:
            self.load_rom(self, rom)

    def clear_gfx(self):
        for i in range(GFX_RESOLUTION):
            self.ram[GFX_ADDRESS + i] = 0x00

    def load_rom(self, file_path):
        file_size = os.path.getsize(file_path)
        if file_size > MAX_ROM_SIZE:
            # TODO raise error
            print("ERROR: Rom file too large")

        with open(file_path, "rb") as fh:
            for i in range(file_size):
                self.ram[PROGRAM_BEGIN_ADDRESS + i] = int.from_bytes(fh.read(1), 'big')

    def reset(self):
        self.__init__()

    def run(self):
        exit = False
        audio_time = 0
        cpu_time = 0
        while not exit:
            if CPU_WAIT_TIME <= (time.time() - cpu_time):
                cpu_time = time.time()
                self.cpu_tick()
            if AUDIO_WAIT_TIME <= (time.time() - audio_time):
                audio_time = time.time()
                self.audio_tick()

    def cpu_tick(self):
        # Fetch instruction from ram
        instruction = hex(self.ram[self.program_counter])[2:] + hex(self.ram[self.program_counter + 1])[2:]
        
        for reg_pattern in OP_REG:
            if re.match(reg_pattern, instruction):
                execute_op_code(OP_REG[reg_pattern][0],OP_REG[reg_pattern][1],instruction)

        self.program_counter += 2

        # Draw to screen
        # Update keys

    def execute_op_code(self, mnemonic, version, hex_code):
        #alias common stuff
        reg1       = hex_code[1]
        reg1_val   = self.register[int(hex_code[1])]
        reg2       = hex_code[2]
        reg2_val   = self.register[int(hex_code[1])]
        lower_byte = hex_code[2:4]
        addr       = int(hex_code[0:3], 16)

        if mnemonic is 'cls':
            self.clear_gfx()
        
        elif mnemoinc is 'ret':
            self.program_counter = self.stack_pop()

        elif mnemoinc is 'sys':
            self.stack_push(self.program_counter)
            self.program_counter = addr
            
        elif mnemoinc is 'call':
            print("ERROR: RCA 1802 calls are not permitted")

        elif mnemoinc is 'se':
            ins_skip(1, reg1_val, version, 1 if "byte" in OP_CODES[mnemoinc][version] else 0 )

        elif mnemoinc is 'sne':
            ins_skip(0, reg1_val, version, 1 if "byte" in OP_CODES[mnemoinc][version] else 0 )

        elif mnemoinc is 'shl':
            if reg1_val >= 0x80:
                self.register[reg1] = (reg1_val << 1) & 0xFF
                self.register[0xF]  = 0xF
            else:
                self.register[reg1] = reg1_val << 1
                self.register[0xF]  = 0x0

        elif mnemoinc is 'shr':
            self.register[reg1] = reg1_val >> 1
            if (reg1_val % 2) == 1:
                self.register[0xF]  = 0xF
            else:
                self.register[0xF]  = 0x0
        
        elif mnemoinc is 'or':
            self.register[reg1] = reg1_val | reg2_val

        elif mnemoinc is 'and':
            self.register[reg1] = reg1_val & reg2_val

        elif mnemoinc is 'xor':
            self.register[reg1] = reg1_val ^ reg2_val

        elif mnemoinc is 'sub':
            ins_sub(self, reg1_val, reg2_val, reg1)

        elif mnemoinc is 'subn':
            ins_sub(self, reg2_val, reg1_val, reg1)

        elif mnemoinc is 'jp':
            self.stack_push(self.program_counter)
            self.program_counter = addr + self.register[0]

        elif mnemoinc is 'rnd':
            self.resgister[reg1] = random.randint(0, 255) & lower_byte
            
        elif mnemoinc is 'add':
            if 'byte' in OP_CODES[mnemoinc][version]:
                self.resgister[reg1] += lower_byte
            elif 'i' in OP_CODES[mnemoinc][version]:
                self.index_register += reg1_val
            else:
                self.resgister[reg1] += reg2_val
                if reg1_val + reg2_val > 0xFF:
                    self.resgister[reg1] &= 0xFF          

        elif mnemoinc is 'ld':

        elif mnemoinc is 'drw'
            height = int(hex_code[4],16)
            origin = GFX_ADDRESS + reg1 + reg2
            flag = False
            for x in range(SPRITE_WIDTH):
                for y in range(height):
                    original = self.ram[origin + x + (y * GFX_WIDTH)]
                    self.ram[origin + x + (y * GFX_WIDTH)] ^= self.ram[self.index_register + x + (y * GFX_WIDTH)]
                    if not flag and ((self.ram[origin + x + (y * GFX_WIDTH)] ^ original) & original):
                        flag = True
            self.registers[0xF] = 0xFF

    def ins_sub(self, reg1_val, reg2_val, store_reg):
        if reg1_val > reg2_val:
            self.register[store_reg] = reg1_val - reg2_val
            self.register[0xF]  = 0xF
        else:
            self.register[store_reg] = 0xFF + reg1_val - reg2_val
            self.register[0xF]  = 0x0

    def ins_skip(self, equal, reg, is_byte, arg):
        if ( reg == int(arg[:is_byte + 1],16) ) == equal:
            self.program_counter += 2

    def stack_push(self, val):
        if STACK_ADDRESS:
            self.ram[stack_pointer] = val
            stack_pointer += 1
            if stack_pointer > STACK_SIZE:
                print("ERROR: Stack overflow") 
        else:
            self.stack.append(val)
            if len(self.stack) > STACK_SIZE:
                print("ERROR: Stack overflow") 

    def stack_pop(self):
        if STACK_ADDRESS:
            stack_pointer -= 1
            if stack_pointer < 0:
                print("ERROR: Stack underflow")
            return self.ram[self.stack_pointer]
        else:
            return self.stack.pop()

    def audio_tick(self):
        # Decrement sound registers
        if self.delay_timer_register != 0:
            self.delay_timer_register -= 1
        if self.sound_timer_register != 0:
            self.sound_timer_register -= 1

    def draw(self):
        print("draw")

    def check_key_press(self):
        print("key")

    def dump_ram(self):
        for i,val in enumerate(self.ram):
            if val is None:
                print('0x' + hex(i)[2:].zfill(3))
            else:
                print('0x' + hex(i)[2:].zfill(3) + "  " + '0x' + hex(val)[2:].zfill(2))

def parse_args():
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('rom', help='ROM to load and play')
    opts = parser.parse_args()

    if not os.path.isfile(opts.rom):
        raise OSError("File '" + opts.input + "' does not exist.")

    return opts

def main(opts):
    guac = guacamole()
    guac.load_rom(opts.rom)
    guac.dump_ram()

if __name__ == '__main__':
    main(parse_args())
