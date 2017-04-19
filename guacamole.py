#!/usr/bin/python3

import os
import argparse
from tortilla8_constants import *

#TODO allow audio in seprate thread

class guacamole:

    def __init__(self):
        self.ram = [None]*BYTES_OF_RAM
        self.stack = []
        self.program_counter = PROGRAM_BEGIN_ADDRESS
        self.stack_pointer = 0

        self.key_state = 0x00
        self.opcode = []

        self.register = []
        self.index_register = 0
        self.delay_timer_register = 0
        self.sound_timer_register = 0

        # Load Font data
        for i,val in enumerate(FONT):
            self.ram[FONT_ADDRESS + i] = val

        # Clear gfx buffer
        for i in range(GFX_RESOLUTION):
            self.ram[GFX_ADDRESS + i] = 0x00

    def load_rom(self, file_path):    # TODO should this take a handler or path?
        file_size = os.path.getsize(file_path)
        if file_size > MAX_ROM_SIZE:
            # TODO raise error
            print("ERROR: Rom file too large")
            return False

        with open(file_path, "rb") as fh:
            for i in range(file_size):
                self.ram[PROGRAM_BEGIN_ADDRESS + i] = int.from_bytes(fh.read(1), 'big')
        return True

    def reset(self):
        self.__init__()

    def cpu_tick(self, instruction):

    def stack_push(self, val)
        if STACK_ADDRESS:
            self.ram[stack_pointer] = val
            stack_pointer += 1
        else:
            self.stack.append(val)

    def stack_pop(self, val)
        if STACK_ADDRESS:
            stack_pointer += 1
            return self.ram[self.stack_pointer]
        else:
            return self.stack.pop()

    def sound_tick(self)
        # Decrement sound registers
        if self.delay_timer_register != 0:
            self.delay_timer_register -= 1
        if self.sound_timer_register != 0
            self.delay_timer_register -= 1

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
