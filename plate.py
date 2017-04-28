#!/usr/bin/python3

import os
import curses
import argparse
from guacamole import guacamole
from tortilla8_constants import *

#TODO get rid of as many of these magic numbers as possible

class plate:

    def __init__(self, rom, hz):
        self.screen = curses.initscr()
                             # newwin( Number of Lines, Number of Col, Y origin, X origin )
        self.w_reg     = curses.newwin(8, (9*4)+2, 0, int(curses.COLS - ((9*4)+2)))
        self.w_stack   = curses.newwin(curses.LINES - self.w_reg.getmaxyx()[0], 10+2, self.w_reg.getmaxyx()[0], int(curses.COLS - (9+2) - 1))
        self.w_console = curses.newwin(curses.LINES , self.w_reg.getbegyx()[1], 0, 0)

        self.emu = guacamole(rom, hz, hz) #TODO grab max rom size warning

        curses.noecho()
        curses.cbreak()

        self.screen.clear()
        self.w_reg.border()
        self.w_stack.border()
        self.w_console.border()

        curses.doupdate()

    def start(self):
        try:
            while True:
                self.emu.run()
                self.update_screen()
        except KeyboardInterrupt:
            self.cleanup()
            pass

    def cleanup(self):
        curses.nocbreak()
        curses.echo()
        curses.endwin()

    def update_screen(self):
        self.display_registers()
        self.display_stack()
        self.w_console.noutrefresh()
        curses.doupdate()

    def display_registers(self):
        self.w_reg.addstr( 1, int((self.w_reg.getmaxyx()[1]-len("Regiters"))/2), "Registers")
        for i in range(NUMB_OF_REGS):
            self.w_reg.addstr(int(i/4) + 2, ((i % 4) * 9) + 1, " " + hex(i)[2] + ": 0x" + hex(self.emu.register[i])[2:].zfill(2) + " ")
        self.w_reg.addstr(6, 1, " dt: 0x" + hex(self.emu.delay_timer_register)[2:].zfill(2) + \
                           "  st: 0x" + hex(self.emu.sound_timer_register)[2:].zfill(2) + \
                           "  i: 0x"  + hex(self.emu.index_register)[2:].zfill(3))
        self.w_reg.noutrefresh()

    def display_stack(self):
        y_top_stack = max(3, self.w_stack.getmaxyx()[0] - 1 - self.emu.stack_pointer)
        self.w_stack.addstr( 1, int((self.w_stack.getmaxyx()[1]-len("Stack"))/2), "Stack")
        self.w_stack.addstr( y_top_stack-1, 1, " " + str(self.emu.stack_pointer).zfill(2) + ": sp")
        for i,val in enumerate(reversed(self.emu.stack)):
            if i > self.w_stack.getmaxyx()[0]-5: break
            self.w_stack.addstr(y_top_stack + i, 1, " " + str(self.emu.stack_pointer - i - 1).zfill(2) + ": 0x" + hex(val)[2:].zfill(2))
        self.w_stack.noutrefresh()

def parse_args():
    parser = argparse.ArgumentParser(description='Plate is a text based front end for the Chip-8 emulator guacamole ...')
    parser.add_argument('rom', help='ROM to load and play.')
    parser.add_argument("-f","--frequency", default=60,help='Frequency (in Hz) to target.')
    opts = parser.parse_args()

    if not os.path.isfile(opts.rom):
        raise OSError("File '" + opts.input + "' does not exist.")

    if opts.frequency:
        opts.frequency = int(opts.frequency)

    return opts

def main(opts):
    disp = plate(opts.rom, opts.frequency)
    disp.start()

if __name__ == '__main__':
    main(parse_args())
