#!/usr/bin/python3

import os
import curses
import argparse
from guacamole import guacamole
from tortilla8_constants import *

#TODO get rid of as many of these magic numbers as possible
#TODO grab max rom size warning
#TODO grab warnings
#TODO move constants

BORDERS     = 2
WIN_REG_H   = 8
WIN_REG_W   = 9*4 + BORDERS
WIN_STACK_W = 11  + BORDERS
W_MIN       = 60
H_MIN       = 15
LEN_STR_REG = len("Regiters")
LEN_STR_STA = len("Stack")

class plate:

    def __init__(self, rom, hz):
        self.screen = curses.initscr()
        if (self.screen.getmaxyx()[0] < H_MIN) or (self.screen.getmaxyx()[1] < W_MIN):
            self.cleanup()
            raise IOError("Terminal window too small to use as display.\nResize to atleast " + str(W_MIN) + "x" + str(H_MIN))

                             # newwin( Number of Lines, Number of Col, Y origin, X origin )
        self.w_reg     = curses.newwin(WIN_REG_H, WIN_REG_W , 0, int(curses.COLS - WIN_REG_W))
        self.w_stack   = curses.newwin(curses.LINES - self.w_reg.getmaxyx()[0], WIN_STACK_W, self.w_reg.getmaxyx()[0], int(curses.COLS - WIN_STACK_W))
        self.w_console = curses.newwin(curses.LINES, self.w_reg.getbegyx()[1], 0, 0)
        self.w_instr   = curses.newwin(curses.LINES - self.w_reg.getmaxyx()[0], WIN_REG_W - WIN_STACK_W, WIN_REG_H, self.w_reg.getbegyx()[1])

        self.emu = guacamole(rom, hz, hz) #TODO grab max rom size warning

        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)

        self.screen.clear()
        self.w_reg.border()
        self.w_stack.border()
        self.w_console.border()
        self.w_instr.border()

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
        self.w_instr.noutrefresh()
        curses.doupdate()

    def display_registers(self):
        self.w_reg.addstr( 1, int((self.w_reg.getmaxyx()[1]-LEN_STR_REG)/2), "Registers")
        for i in range(NUMB_OF_REGS):
            self.w_reg.addstr(int(i/4) + 2, ((i % 4) * 9) + 1, " " + hex(i)[2] + ": " + hex2(self.emu.register[i]) + " ")
        self.w_reg.addstr(6, 1, " dt: " + hex2(self.emu.delay_timer_register) + \
                               "  st: " + hex2(self.emu.sound_timer_register) + \
                                "  i: " + hex3(self.emu.index_register))
        self.w_reg.noutrefresh()

    def display_stack(self):
        y_top_stack = max(3, self.w_stack.getmaxyx()[0] - 1 - self.emu.stack_pointer)
        self.w_stack.addstr( 1, int((self.w_stack.getmaxyx()[1]-LEN_STR_STA)/2), "Stack")
        if y_top_stack > 3:
            self.w_stack.addstr( y_top_stack - 2, 1, " " * 10 )
        self.w_stack.addstr( y_top_stack-1, 1, " " + str(self.emu.stack_pointer).zfill(2) + ": sp   ")
        for i,val in enumerate(reversed(self.emu.stack)):
            if i > self.w_stack.getmaxyx()[0]-5: break
            self.w_stack.addstr(y_top_stack + i, 1, " " + str(self.emu.stack_pointer - i - 1).zfill(2) + ": " + hex2(val))
        self.w_stack.noutrefresh()

def hex2(integer):
    return "0x" + hex(integer)[2:].zfill(2)

def hex3(integer):
    return "0x" + hex(integer)[2:].zfill(3)

def parse_args():
    parser = argparse.ArgumentParser(description='Plate is a text based front end for the Chip-8 emulator guacamole ...')
    parser.add_argument('rom', help='ROM to load and play.')
    parser.add_argument("-f","--frequency", default=60,help='Frequency (in Hz) to target.')
    opts = parser.parse_args()

    if not os.path.isfile(opts.rom):
        raise OSError("File '" + opts.rom + "' does not exist.")

    if opts.frequency:
        opts.frequency = int(opts.frequency)

    return opts

def main(opts):
    disp = plate(opts.rom, opts.frequency)
    disp.start()

if __name__ == '__main__':
    main(parse_args())
