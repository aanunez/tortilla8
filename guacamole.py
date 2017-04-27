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

        self.keypad = [False]*16
        self.draw_flag = False
        
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

    def input_keys(self, pressed_keys):
        self.keypad = pressed_keys
        
    def output_screen(self):
        return self.ram[GFX_ADDRESS:GFX_ADDRESS+GFX_RESOLUTION]

    def output_audio(self):
        return [self.delay_timer_register == 0, self.sound_timer_register == 0]

    def run(self):
        exit = False
        audio_time = 0
        cpu_time = 0
        while not exit:
            if CPU_WAIT_TIME <= (time.time() - cpu_time):
                cpu_time = time.time()
                self.cpu_tick()
                if self.draw_flag:
                    self.draw_flag = False
                    # TODO Draw to screen
            if AUDIO_WAIT_TIME <= (time.time() - audio_time):
                audio_time = time.time()
                self.audio_tick()

        # TODO Update keys

    def cpu_tick(self):
        # Fetch instruction from ram
        flag = False
        instruction =  hex(self.ram[self.program_counter + 0])[2:].zfill(2)
        instruction += hex(self.ram[self.program_counter + 1])[2:].zfill(2)

        for reg_pattern in OP_REG:
            if re.match(reg_pattern.lower(), instruction):   # TODO probably should remove the need for .lower()
                print(hex(self.program_counter) + " " + instruction + " " + OP_REG[reg_pattern][0])
                self.execute_op_code(OP_REG[reg_pattern][0],OP_REG[reg_pattern][1],instruction)
                flag = True
                break

        if not flag:
            print("ERROR: Unknown instruction! " + instruction + " at " + hex(self.program_counter))

        self.program_counter += 2

    def execute_op_code(self, mnemonic, version, hex_code):
        #alias common stuff
        reg1       = int(hex_code[1],16)
        reg1_val   = self.register[reg1]
        reg2       = int(hex_code[2],16)
        reg2_val   = self.register[reg2]
        lower_byte = int(hex_code[2:4], 16)
        addr       = int(hex_code[1:4], 16)

        if mnemonic is 'cls':
            self.clear_gfx()

        elif mnemonic is 'ret':
            self.program_counter = self.stack_pop()

        elif mnemonic is 'sys':
            print("Warning: RCA 1802 call to " + hex(addr) + " was ",end="")
            if self.ram[addr] is not None:
                self.stack_push(self.program_counter)
                self.program_counter = addr - 2
                print("allowed as the call was within the rom.")
            else:
                print("disallowed as the call was to a null valued location.")

        elif mnemonic is 'call':
            self.stack_push(self.program_counter)
            self.program_counter = addr + self.register[0] - 2
            
        elif mnemonic is 'skp':
            if self.keypad[reg1_val & 0x0F]:
                self.program_counter += 2

        elif mnemonic is 'sknp':
            if not self.keypad[reg1_val & 0x0F]:
                self.program_counter += 2

        elif mnemonic is 'se':
            comp = lower_byte if "byte" in OP_CODES[mnemonic][version][OP_ARGS] else reg2_val
            if reg1_val == comp:
                self.program_counter += 2

        elif mnemonic is 'sne':
            comp = lower_byte if "byte" in OP_CODES[mnemonic][version][OP_ARGS] else reg2_val
            if reg1_val != comp:
                self.program_counter += 2

        elif mnemonic is 'shl':                                         #TODO add option to respect "old" shift
            self.register[reg1] = (reg1_val << 1) & 0xFF
            self.register[0xF] = 0xFF if reg1_val >= 0x80 else 0x0

        elif mnemonic is 'shr':                                         #TODO add option to respect "old" shift
            self.register[reg1] = reg1_val >> 1
            self.register[0xF] = 0xFF if (reg1_val % 2) == 1 else 0x0

        elif mnemonic is 'or':
            self.register[reg1] = reg1_val | reg2_val

        elif mnemonic is 'and':
            self.register[reg1] = reg1_val & reg2_val

        elif mnemonic is 'xor':
            self.register[reg1] = reg1_val ^ reg2_val

        elif mnemonic is 'sub':
            self.ins_sub(self, reg1_val, reg2_val, reg1)

        elif mnemonic is 'subn':
            self.ins_sub(self, reg2_val, reg1_val, reg1)

        elif mnemonic is 'jp':
            if 'v0' in OP_CODES[mnemonic][version][OP_ARGS]:
                self.program_counter = addr + self.register[0] - 2
            else:
                self.program_counter = addr - 2

        elif mnemonic is 'rnd':
            self.register[reg1] = random.randint(0, 255) & lower_byte

        elif mnemonic is 'add':
            if 'byte' in OP_CODES[mnemonic][version][OP_ARGS]:
                self.register[reg1] += lower_byte
            elif 'i' in OP_CODES[mnemonic][version][OP_ARGS]:
                self.index_register += reg1_val
            else:
                self.register[reg1] += reg2_val
                if reg1_val + reg2_val > 0xFF:
                    self.register[reg1] &= 0xFF

        elif mnemonic is 'ld':                                     # TODO this sucks
            if 'register' is OP_CODES[mnemonic][version][OP_ARGS][0]:
                if   'byte' is OP_CODES[mnemonic][version][OP_ARGS][1]:
                    self.register[reg1] = lower_byte
                elif 'register'  is OP_CODES[mnemonic][version][OP_ARGS][1]:
                    self.register[reg1] = reg2_val
                elif 'dt'   is OP_CODES[mnemonic][version][OP_ARGS][1]:
                    self.register[reg1] = self.delay_timer_register
                elif 'k'    is OP_CODES[mnemonic][version][OP_ARGS][1]:
                    original = ~int(''.join(['1' if x else '0' for x in self.keypad]),2)
                    new = 0x0000
                    while not (original & new):
                        new = int(''.join(['1' if x else '0' for x in self.keypad]),2)
                        continue
                    self.register[reg1] = new.find('1')
                elif '[i]'  is OP_CODES[mnemonic][version][OP_ARGS][1]:
                    for i in range(reg1):
                        self.register[i] = self.ram[self.index_register + i]
                else:
                    print("ERROR: Bad Load")
            elif 'register' is OP_CODES[mnemonic][version][OP_ARGS][1]:
                if   'dt'  is OP_CODES[mnemonic][version][OP_ARGS][0]:
                    self.delay_timer_register = reg1_val
                elif 'st'  is OP_CODES[mnemonic][version][OP_ARGS][0]:
                    self.sound_timer_register = reg1_val
                elif 'f'   is OP_CODES[mnemonic][version][OP_ARGS][0]:
                    self.index_register = FONT_ADDRESS + (5 * reg1_val)
                elif 'b'   is OP_CODES[mnemonic][version][OP_ARGS][0]:
                    reg1_val = str(reg1_val).zfill(3)
                    for i in range(3):
                        self.ram[self.index_register + i] = int(reg1_val[i])
                elif '[i]' is OP_CODES[mnemonic][version][OP_ARGS][0]:
                    for i in range(reg1):
                        self.ram[self.index_register + i] = self.register[i]
                else:
                    print("ERROR: Bad Load")
            else:
                self.index_register = addr

        elif mnemonic is 'drw':           # TODO Wrap around doesn't work
            if reg1_val >= GFX_WIDTH_PX:
                print("ERROR: Draw instruction called with X origin >= GFX_WIDTH_PX\nWrap-around not yet supported.")
            if reg2_val >= GFX_HEIGHT_PX:
                print("ERROR: Draw instruction called with Y origin >= GFX_HEIGHT_PX\nWrap-around not yet supported.")

            self.draw_flag = True
            height = int(hex_code[3],16)
            origin = GFX_ADDRESS + int(reg1_val/8) + (reg2_val * GFX_WIDTH) #To lowest byte
            mask = [0xFF >> (reg1_val%8)]
            mask.insert(0, ~mask[0])
            self.register[0xF] = 0x00

            for y in range(height):
                for x in range(2):
                    original = self.ram[origin + x + (y * GFX_WIDTH)]
                    self.ram[origin + x + (y * GFX_WIDTH)] ^= self.ram[self.index_register + y]   # This should be I + y only? Was: self.ram[self.index_register + x + (y * GFX_WIDTH)] 
                    self.ram[origin + x + (y * GFX_WIDTH)] |= mask[x]
                    self.ram[origin + x + (y * GFX_WIDTH)] &= original
                    if ((self.ram[origin + x + (y * GFX_WIDTH)] ^ original) & original):
                        self.register[0xF] = 0xFF

        else:
            print("ERROR: Bad Instruction!")

    def ins_sub(self, reg1_val, reg2_val, store_reg):
        self.register[store_reg] = reg1_val - reg2_val
        self.register[store_reg] += 0x00 if reg1_val > reg2_val else 0xFF
        self.register[0xF] = 0xFF if reg1_val > reg2_val else 0x00

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
    for i in range(200):
        time.sleep(0.2)
        guac.cpu_tick()
    #guac.dump_ram()

if __name__ == '__main__':
    main(parse_args())