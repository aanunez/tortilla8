#!/usr/bin/python3

import os
import time
import curses
import argparse
import collections
from guacamole import guacamole
from display_constants import *
from mem_addr_register_constants import *

#TODO get rid of as many of these magic numbers as possible
#TODO grab max rom size warning
#TODO grab warnings
#TODO Support non 64x32 displays
#TODO double the resolution if window is large enough

class platter:

    def __init__(self, rom, hz):
        self.screen = curses.initscr()
        self.w_reg     = None
        self.w_instr   = None
        self.w_stack   = None
        self.w_logo    = None
        self.w_game    = None
        self.w_console = None
        self.w_dummy   = None

        self.dynamic_window_gen()
        self.instr_history   = collections.deque(maxlen = self.w_instr.getmaxyx()[0] - BORDERS)
        self.console_history = collections.deque(maxlen = self.w_console.getmaxyx()[0] - BORDERS)
        self.emu = guacamole(rom, hz, hz) #TODO grab max rom size warning

        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)

    def console_print(self, message):
        self.console_history.appendleft(message)
        for i,val in enumerate(self.console_history):
            self.w_console.addstr( 1 + i, 2, val )
        #self.w_console.noutrefresh()
        self.w_console.refresh()

    def start(self, step_mode=False):      #TODO Step mode is borken :\ can't seem to get that S key
        previous_pc = 0
        last_exec = time.time()
        watch_dog = self.emu.cpu_wait + .01 #TODO probs shouldn't do this
        try:
            while True:
                #TODO Check for key presses         self.w_console.nodelay(1)
                self.emu.run()

                # Update Display if we executed
                if self.emu.program_counter != previous_pc:
                    previous_pc = self.emu.program_counter
                    self.update_history()
                    self.update_screen()
                    last_exec = time.time()
                # Detect Spinning
                elif step_mode or (not step_mode and (time.time() - last_exec > watch_dog)):
                    self.instr_history.appendleft(hex3(self.emu.program_counter) + " spin jp")
                    self.update_screen()
                    self.console_print("Spin detected. Press 'X' to exit.")
                    self.w_console.nodelay(0)
                    while self.w_console.getch() != ASCII_X: continue
                    break

                # Pause for Step Mode
                if step_mode:
                    exit = False
                    self.w_console.nodelay(0)
                    while self.w_console.getch() != ASCII_S: continue   #TODO the way this works needs to change yo.

        except KeyboardInterrupt:
            return
        except:
            raise
        finally:
            self.cleanup()

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

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Display functions for windows

    def display_logo(self):
        if self.screen.getmaxyx()[0] < LOGO_MIN: return
        logo_offset = int( ( self.w_logo.getmaxyx()[0] - len(LOGO) ) / 2 )
        for i in range(len(LOGO)):
            self.w_logo.addstr( i + logo_offset, 0, LOGO[i] )
        self.w_logo.noutrefresh()

    def display_game(self):
        if not self.w_game or not self.emu.draw_flag: return
        self.emu.draw_flag = False
        for y in range( int(GFX_HEIGHT_PX / 2) ):
            for x in range(GFX_WIDTH):
                upper_chunk = int( bin( self.emu.ram[ GFX_ADDRESS + ( (y * 2 + 0) * GFX_WIDTH) + x ] )[2:] )
                lower_chunk = int( bin( self.emu.ram[ GFX_ADDRESS + ( (y * 2 + 1) * GFX_WIDTH) + x ] )[2:].replace('1','2') )
                total_chunk  = str(upper_chunk + lower_chunk).zfill(8).replace('3', "█" ).replace('2', "▄" )\
                                                                      .replace('1', "▀" ).replace('0', "." )
                self.w_game.addstr( 1 + y, 1 + x * 8, total_chunk )
        self.w_game.noutrefresh()

    def display_console(self):
        #self.w_console.addstr( 1,  1, "HelloWorld!" )
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

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Dynamic Window Generator

    def dynamic_window_gen(self):
        if (self.screen.getmaxyx()[0] < H_MIN) or (self.screen.getmaxyx()[1] < W_MIN):
            self.cleanup()
            raise IOError("Terminal window too small to use.\nResize to atleast " + str(W_MIN) + "x" + str(H_MIN)) # TODO display resize message?

        C = curses.COLS
        L = curses.LINES      # newwin( Number of Lines, Number of Col, Y origin, X origin )
        self.w_reg     = curses.newwin( WIN_REG_H, WIN_REG_W , 0, int( C - WIN_REG_W ) )
        self.w_instr   = curses.newwin( L - WIN_REG_H, WIN_INSTR_W, WIN_REG_H, self.w_reg.getbegyx()[1] )
        self.w_stack   = curses.newwin( L - WIN_REG_H, WIN_STACK_W, WIN_REG_H, self.w_instr.getbegyx()[1] + WIN_INSTR_W )
        self.w_logo    = curses.newwin( L - WIN_REG_H, WIN_LOGO_W , WIN_REG_H, self.w_stack.getbegyx()[1] + WIN_STACK_W )
        self.w_game    = None
        self.w_console = None

        if (self.screen.getmaxyx()[0] < DISPLAY_MIN_H) or (self.screen.getmaxyx()[1] < DISPLAY_MIN_W):
            self.w_console = curses.newwin( L,  self.w_reg.getbegyx()[1], 0, 0 )
            # TODO show info in console screen about min size
        else:
            self.w_game    = curses.newwin( DISPLAY_H, DISPLAY_W, 0, int( ( C - WIN_REG_W - DISPLAY_W ) / 2 ) )
            self.w_console = curses.newwin( L-DISPLAY_H, self.w_reg.getbegyx()[1], DISPLAY_H, 0 )
            self.w_game.border()
            self.w_game.noutrefresh()

        self.screen.clear()
        self.w_reg.border()
        self.w_reg.addstr( 1, REG_OFFSET, "Registers")
        self.w_stack.border()
        self.w_stack.addstr( 1, STAK_OFFSET, "Stack")
        self.w_console.border()
        self.w_instr.border()

        self.display_logo()
        curses.doupdate()

def hex2(integer):
    return "0x" + hex(integer)[2:].zfill(2)

def hex3(integer):
    return "0x" + hex(integer)[2:].zfill(3)

def parse_args():
    parser = argparse.ArgumentParser(description='Plate is a text based front end for the Chip-8 emulator guacamole ...')
    parser.add_argument('rom', help='ROM to load and play.')
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-f","--frequency", default=60,help='Frequency (in Hz) to target, minimum 1 hz.')
    group.add_argument('-s','--step', help='Start the emulator is "step" mode.',action='store_true')
    opts = parser.parse_args()

    if not os.path.isfile(opts.rom):
        raise OSError("File '" + opts.rom + "' does not exist.")

    if opts.frequency:
        try: opts.frequency = int(opts.frequency)
        except: raise ValueError("Non-numeric frequency provided.")
        if opts.frequency < 1:
            raise ValueError("Please use step mode for sub 1 hz operation.")

    if opts.step:
        opts.frequency = 2 ** 63 - 1

    return opts

def main(opts):
    disp = platter(opts.rom, opts.frequency)
    disp.start(opts.step)

if __name__ == '__main__':
    main(parse_args())












