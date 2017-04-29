#!/usr/bin/python3

import os
import curses
import argparse
import collections
from guacamole import guacamole
from display_constants import *
from mem_addr_register_constants import *

#TODO Step mode breaks borders? Why??
#TODO get rid of as many of these magic numbers as possible
#TODO grab max rom size warning
#TODO grab warnings
#TODO move constants
#TODO Support non 64x32 displays
#TODO double the resolution if window is large enough

class platter:

    def __init__(self, rom, hz):
        self.screen = curses.initscr()
        if (self.screen.getmaxyx()[0] < H_MIN) or (self.screen.getmaxyx()[1] < W_MIN):
            self.cleanup()
            raise IOError("Terminal window too small to use.\nResize to atleast " + str(W_MIN) + "x" + str(H_MIN))

        L = curses.LINES      # newwin( Number of Lines, Number of Col, Y origin, X origin )
        self.w_reg     = curses.newwin( WIN_REG_H, WIN_REG_W , 0, int(curses.COLS - WIN_REG_W) )
        self.w_instr   = curses.newwin( L - WIN_REG_H, WIN_INSTR_W, WIN_REG_H, self.w_reg.getbegyx()[1] )
        self.w_stack   = curses.newwin( L - WIN_REG_H, WIN_STACK_W, WIN_REG_H, self.w_instr.getbegyx()[1] + WIN_INSTR_W )
        self.w_logo    = curses.newwin( L - WIN_REG_H, WIN_LOGO_W , WIN_REG_H, self.w_stack.getbegyx()[1] + WIN_STACK_W )
        self.w_game    = None
        self.w_console = None

        if (self.screen.getmaxyx()[0] < DISPLAY_MIN_H) or (self.screen.getmaxyx()[1] < DISPLAY_MIN_W):
            self.w_console = curses.newwin( L,  self.w_reg.getbegyx()[1], 0, 0 )
            # TODO show info in console screen about min size
        else:
            print(int( ( L - WIN_REG_W - DISPLAY_W ) / 2 ))
            self.w_game    = curses.newwin( DISPLAY_H, DISPLAY_W, 0, int( ( curses.COLS - WIN_REG_W - DISPLAY_W ) / 2 ) )
            self.w_console = curses.newwin( L-DISPLAY_H, self.w_reg.getbegyx()[1], DISPLAY_H, 0 )
            self.w_game.border()

        self.instr_history = collections.deque(maxlen = self.w_instr.getmaxyx()[0] - BORDERS)
        self.emu = guacamole(rom, hz, hz) #TODO grab max rom size warning

        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)

        self.screen.clear()
        self.w_reg.border()
        self.w_reg.addstr( 1, REG_OFFSET, "Registers")
        self.w_stack.border()
        self.w_stack.addstr( 1, STAK_OFFSET, "Stack")
        self.w_console.border()
        self.w_instr.border()
        self.w_logo.nodelay(1)

        self.display_logo()
        curses.doupdate()

    def start(self, step_mode=False):      #TODO Step mode is borken :\ can't seem to get that S key
        previous_pc = 0
        try:
            while True:
                self.emu.run()
                if self.emu.program_counter != previous_pc:
                    previous_pc = self.emu.program_counter
                    self.update_history()
                    self.update_screen()
                if step_mode:
                    exit = False
                    while True:
                        try:
                            while self.w_logo.getkey() != 'S':
                                pass
                            exit = True
                        except KeyboardInterrupt:
                            raise
                        except: pass
                        if exit: break

        except KeyboardInterrupt:
            self.cleanup()
            pass
        except:
            self.cleanup()
            raise

    def cleanup(self):
        curses.nocbreak()
        curses.echo()
        curses.endwin()

    def update_screen(self):
        self.display_registers()
        self.display_stack()
        self.display_console()
        self.display_instructions()
        self.display_game()
        curses.doupdate()

    def update_history(self):
        self.instr_history.appendleft(hex3(self.emu.program_counter - 2) + " " + \
                                           self.emu.hex_instruction + " " + \
                                           self.emu.mnemonic)

    def display_logo(self):
        if self.screen.getmaxyx()[0] < LOGO_MIN: return
        logo_offset = int( ( self.w_logo.getmaxyx()[0] - len(LOGO) ) / 2 )
        for i in range(len(LOGO)):
            self.w_logo.addstr( i + logo_offset, 0, LOGO[i] )
        self.w_logo.noutrefresh()

    def display_game(self):
        #if not self.w_game or not self.emu.output_draw_flag(): return
        if not self.w_game: return
        for x in range(1,64+1):
            for y in range(1,16+1):
                self.w_game.addstr( y, x, "█" )
        self.w_game.noutrefresh()
        self.emu.ram[GFX_ADDRESS:GFX_ADDRESS+GFX_RESOLUTION]

    def display_console(self):
        self.w_console.addstr( 1,  1, "HelloWorld!" )
        self.w_console.noutrefresh()

    def display_instructions(self):
        for i,val in enumerate(self.instr_history):
            self.w_instr.addstr( 1 + i, 2, val.ljust(15))
        self.w_instr.noutrefresh()

    def display_registers(self):
        for i in range(NUMB_OF_REGS):
            self.w_reg.addstr( int( i / 4 ) + 2, i % 4 * 9 + 2, hex(i)[2] + ": " + hex2(self.emu.register[i]) )
        self.w_reg.addstr(6, 1, " dt: " + hex2(self.emu.delay_timer_register) + \
                               "  st: " + hex2(self.emu.sound_timer_register) + \
                                "  i: " + hex3(self.emu.index_register))
        self.w_reg.noutrefresh()

    def display_stack(self):
        top = max(3, self.w_stack.getmaxyx()[0] - 1 - self.emu.stack_pointer)
        if top > 3:
            self.w_stack.addstr( top - 2, 1, " " * 10 )
        self.w_stack.addstr( top - 1, 2, str(self.emu.stack_pointer).zfill(2) + ": sp   ")
        for i,val in enumerate(reversed(self.emu.stack)):
            if i == self.w_stack.getmaxyx()[0] - 4: break
            self.w_stack.addstr(top + i, 2, str(self.emu.stack_pointer - i - 1).zfill(2) + ": " + hex2(val))
        self.w_stack.noutrefresh()

def hex2(integer):
    return "0x" + hex(integer)[2:].zfill(2)

def hex3(integer):
    return "0x" + hex(integer)[2:].zfill(3)

def parse_args():
    parser = argparse.ArgumentParser(description='Plate is a text based front end for the Chip-8 emulator guacamole ...')
    parser.add_argument('rom', help='ROM to load and play.')
    parser.add_argument("-f","--frequency", default=60,help='Frequency (in Hz) to target.')
    parser.add_argument('-s','--step', help='Start the emulator is "step" mode.',action='store_true')
    opts = parser.parse_args()

    if not os.path.isfile(opts.rom):
        raise OSError("File '" + opts.rom + "' does not exist.")

    if opts.frequency:
        opts.frequency = int(opts.frequency)

    return opts

def main(opts):
    disp = platter(opts.rom, opts.frequency)
    disp.start(opts.step)

if __name__ == '__main__':
    main(parse_args())












