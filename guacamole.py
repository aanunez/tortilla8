#!/usr/bin/python3

import os
import argparse
from tortilla8_constants import *

#TODO allow audio in seprate thread

class guacamole:

    def __init__(self):
        self.ram = []
        self.stack = []
        self.gfx = []

        self.key_state = 0x00
        self.opcode = []

        self.program_counter = PROGRAM_BEGIN_ADDRESS
        self.stack_pointer = 0

        self.register = []
        self.index_register = 0
        self.delay_timer_register = 0
        self.sound_timer_register = 0

    def reset(self):
        self.__init__()

    def tick(self, instruction):

    def draw(self):

    def check_key_press(self):

def parse_args():
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('rom', help='ROM to load and play')
    opts = parser.parse_args()

    if not os.path.isfile(opts.rom):
        raise OSError("File '" + opts.input + "' does not exist.")

    return opts

def main(opts):
    guac = guacamole()
    with open(opts.rom) as FH:
        guac.load_ROM(FH)

if __name__ == '__main__':
    main(parse_args())
