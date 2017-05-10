#!/usr/bin/python3

# Import curses
import os
try: import curses
except ImportError:
    os.environ['PATH'] = os.path.abspath('win32') + ';' + os.environ['PATH'] # TODO this 'import' doesn't seem to work
    import unicurses as curses

# Import Sound
import wave
import pyaudio

# Everything else
import time
import textwrap
import collections
from enum import Enum
from constants.curses import *
from guacamole import guacamole, Emulation_Error
from constants.reg_rom_stack import PROGRAM_BEGIN_ADDRESS, NUMB_OF_REGS
from constants.graphics import GFX_RESOLUTION, GFX_ADDRESS, GFX_HEIGHT_PX, GFX_WIDTH

# Only used when called as script
import argparse

#TODO Need a simple audio library

#TODO Allow editing controls
#TODO Improve input. Also, E isn't mapped

#TODO Support non 64x32 displays
#TODO double the resolution if window is large enough
#TODO add Keypad display
#TODO add statistics display / menu (X,S,R change freq? Toggle stepmode?)

class platter:

    def __init__(self, rom, cpuhz, audiohz, delayhz, init_ram, drawfix):

        # Init Curses
        self.screen = curses.initscr()

        # Used for graphics "smoothing" w/ -d flag
        self.draw_fix = drawfix
        self.prev_board=[0x00]*GFX_RESOLUTION

        self.rom = rom
        self.dynamic_window_gen()
        self.init_logs()

        # Define control mapping
        self.controls={
        '0' :0x0,'1' :0x1,'2' :0x2,'3' :0x3,
        '4' :0x4,'5' :0x5,'6' :0x6,'7' :0x7,
        '8' :0x8,'9' :0x9,'//':0xA,'*' :0xB,
        '-' :0xC,'+' :0xD,';' :0xE,'.' :0xF}

        # Print FYI for game window
        if self.w_game is None:
            self.console_print("Window must be atleast "+ str(DISPLAY_MIN_W) + "x" + str(DISPLAY_MIN_H) +" to display the game screen")

        # Init the emulator
        self.emu = guacamole(rom, cpuhz, audiohz, delayhz, init_ram)
        self.check_emu_log()
        self.init_emu_status()

        # Curses settings
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)

    def init_emu_status(self):
        self.previous_pc = PROGRAM_BEGIN_ADDRESS
        self.halt        = False

    def init_logs(self):
        self.instr_history   = collections.deque(maxlen = self.w_instr.getmaxyx()[0] - BORDERS)
        self.console_history = collections.deque(maxlen = self.w_console.getmaxyx()[0] - BORDERS)

    def start(self, step_mode=False):
        key_press_time = 0
        audio_playing = False
        key_msg_displayed = False

        #audio_file = os.path.join('sound',"play.wav")
        if step_mode:
            self.console_print("Emulator started in step mode. Press '" + KEY_STEP.upper() + "' to process one instruction.")

        try:
            while True:
                # Try to get a keypress
                try:
                    key = self.w_console.getkey()
                except:
                    key = ''
                    pass

                # Update Keypad press
                if time.time() - key_press_time > 0.5: #TODO Better input
                    self.emu.keypad = [False] * 16
                    key_press_time = time.time()
                if key in self.controls:
                    self.emu.keypad[self.controls[key]] = True

                # Exit check
                if key == KEY_EXIT:
                    break

                # Reset check
                if key == KEY_RESET:
                    self.emu.reset( self.rom )
                    self.init_emu_status()
                    self.init_logs()
                    self.clear_all_windows()
                    continue

                # Step if requested
                if key == KEY_STEP:
                    self.halt = False

                # Try to tick the cpu
                if not self.halt:
                    self.emu.run()

                # Display what keys are being pressed
                #if [i for i, x in enumerate(self.emu.dump_keypad()) if x]:
                #    self.console_print(self.emu.dump_keypad())

                # Update Display if we executed
                if self.emu.program_counter != self.previous_pc:
                    self.previous_pc = self.emu.program_counter
                    self.update_instr_history()
                    key_msg_displayed = False

                # Watch for spin for key
                elif self.emu.waiting_for_key and not key_msg_displayed:
                    self.instr_history.appendleft(hex3(self.emu.program_counter) + " key  ld")
                    self.console_print("Program is trying to load a key press.")
                    key_msg_displayed = True

                # Detect Spinning
                elif not self.halt and self.emu.spinning:
                    self.instr_history.appendleft(hex3(self.emu.program_counter) + " spin jp")
                    self.console_print("Spin detected. Press '" + KEY_EXIT.upper() + "' to exit")
                    self.halt  = True

                # Toggle for Step Mode
                if step_mode:
                    self.halt = True

                # Start/stop Audio
                audio_playing = False if self.emu.sound_timer_register == 0 else True
                if audio_playing:
                    pass
                    #self.play_beep()

                self.check_emu_log()
                self.update_screen()

            self.update_screen()
        except KeyboardInterrupt:
            return
        except:
            raise
        finally:
            self.cleanup()

    def check_emu_log(self):
        # Print all logged errors in the emu
        for err in reversed(self.emu.error_log):
            self.console_print( str(err[0]) + ": " + err[1] )
            if err[0] is Emulation_Error._Fatal:
                self.halt = True
                self.console_print( "Fatal error has occured. Press '" + KEY_RESET.upper() + "' to reset" )

        # Manually reset
        self.emu.error_log = []

    def cleanup(self):
        curses.nocbreak()
        curses.echo()
        curses.endwin()

    def update_screen(self):
        self.display_registers()
        self.display_stack()
        self.display_instructions()
        self.display_game()
        curses.doupdate()

    def update_instr_history(self):
        self.instr_history.appendleft(hex3(self.emu.calling_pc) + " " + \
                                           self.emu.dis_ins.hex_instruction + " " + \
                                           self.emu.dis_ins.mnemonic)

    def play_beep(self):
        chunk = 1024
        f = wave.open(r"sound/play.wav","rb")
        p = pyaudio.PyAudio()
        stream = p.open(format = p.get_format_from_width(f.getsampwidth()),
                        channels = f.getnchannels(),
                        rate = f.getframerate(),
                        output = True)
        data = f.readframes(chunk)
        while data:
            stream.write(data)
            data = f.readframes(chunk)
        stream.stop_stream()
        stream.close()
        p.terminate()

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Display functions for windows

    def console_print(self, message):
        message_list = textwrap.wrap("-" + message, self.w_console.getmaxyx()[1]- (BORDERS + 1) )
        for msg in reversed(message_list):
            self.console_history.appendleft( msg.ljust(self.w_console.getmaxyx()[1] - (BORDERS + 1) ) )
        for i,val in enumerate(self.console_history):
            self.w_console.addstr( 1 + i, 1, val )
        self.w_console.noutrefresh()

    def clear_all_windows(self):
        self.screen.clear()
        self.w_stack.clear()
        self.w_console.clear()
        self.w_instr.clear()
        if self.w_menu is not None:
            self.w_menu.clear()
            self.w_menu.border()
        if self.w_game is not None:
            self.w_game.clear()
            self.w_game.border()
        self.w_reg.border()
        self.w_reg.addstr( 1, REG_OFFSET, "Registers")
        self.w_stack.border()
        self.w_stack.addstr( 1, STAK_OFFSET, "Stack")
        self.w_console.border()
        self.w_instr.border()
        self.w_console.nodelay(1)
        self.display_logo()
        curses.doupdate()

    def display_logo(self):
        if self.screen.getmaxyx()[0] < LOGO_MIN: return
        logo_offset = int( ( self.w_logo.getmaxyx()[0] - len(LOGO) ) / 2 )
        for i in range(len(LOGO)):
            self.w_logo.addstr( i + logo_offset, 0, LOGO[i] )
        self.w_logo.noutrefresh()

    def display_game(self):
        if not self.w_game or not self.emu.draw_flag: return
        self.emu.draw_flag = False

        if self.draw_fix:
            prev_str = ""
            curr_str = ""
            for val in self.prev_board:
                prev_str += bin(val)[2:].zfill(8)
            for val in self.emu.ram[GFX_ADDRESS:GFX_ADDRESS+GFX_RESOLUTION]:
                curr_str += bin(val)[2:].zfill(8)
            int_prev = int(prev_str,2)
            int_curr = int(curr_str,2)
            self.prev_board = self.emu.ram[GFX_ADDRESS:GFX_ADDRESS+GFX_RESOLUTION]
            if ( ( int_prev ^ int_curr ) & int_prev ) == ( int_prev ^ int_curr ):
                #Only 1s were changed to 0s, skip the draw to prevent SOME flicker
                return

        for y in range( int(GFX_HEIGHT_PX / 2) ):
            for x in range(GFX_WIDTH):
                upper_chunk = int( bin( self.emu.ram[ GFX_ADDRESS + ( (y * 2 + 0) * GFX_WIDTH) + x ] )[2:] )
                lower_chunk = int( bin( self.emu.ram[ GFX_ADDRESS + ( (y * 2 + 1) * GFX_WIDTH) + x ] )[2:].replace('1','2') )
                total_chunk  = str(upper_chunk + lower_chunk).zfill(8).replace('3', "█" ).replace('2', "▄" )\
                                                                      .replace('1', "▀" ).replace('0', " " )
                self.w_game.addstr( 1 + y, 1 + x * 8, total_chunk )
        self.w_game.noutrefresh()

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
        C = self.screen.getmaxyx()[1]
        L = self.screen.getmaxyx()[0]

        if (L < H_MIN) or (C < W_MIN):
            self.cleanup()
            raise IOError("Terminal window too small to use.\nResize to atleast " + str(W_MIN) + "x" + str(H_MIN)) # TODO display resize message?

        self.w_reg     = curses.newwin( WIN_REG_H, WIN_REG_W , 0, int( C - WIN_REG_W ) )
        self.w_instr   = curses.newwin( L - WIN_REG_H, WIN_INSTR_W, WIN_REG_H, self.w_reg.getbegyx()[1] )
        self.w_stack   = curses.newwin( L - WIN_REG_H, WIN_STACK_W, WIN_REG_H, self.w_instr.getbegyx()[1] + WIN_INSTR_W )
        self.w_logo    = curses.newwin( L - WIN_REG_H, WIN_LOGO_W , WIN_REG_H, self.w_stack.getbegyx()[1] + WIN_STACK_W )
        self.w_game    = None
        self.w_console = None
        self.w_menu    = None

        if (L < DISPLAY_MIN_H) or (C < DISPLAY_MIN_W):
            self.w_console = curses.newwin( L,  self.w_reg.getbegyx()[1], 0, 0 )
        else:
            self.w_game    = curses.newwin( DISPLAY_H, DISPLAY_W, 0, int( ( C - WIN_REG_W - DISPLAY_W ) / 2 ) )
            self.w_console = curses.newwin( L - DISPLAY_H - WIN_MENU_H, self.w_reg.getbegyx()[1], DISPLAY_H, 0 )
            self.w_menu    = curses.newwin( WIN_MENU_H, self.w_reg.getbegyx()[1], L - WIN_MENU_H, 0 )
            self.w_game.noutrefresh()

        self.clear_all_windows()

def hex2(integer):
    return "0x" + hex(integer)[2:].zfill(2)

def hex3(integer):
    return "0x" + hex(integer)[2:].zfill(3)

def parse_args():
    parser = argparse.ArgumentParser(description='Platter is a text based front end for the Chip-8 emulator guacamole. ')
    parser.add_argument('rom', help='ROM to load and play.')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-f','--frequency', default=10,help='CPU frequency (in Hz) to target, minimum 1 hz.')
    group.add_argument('-s','--step', help='Start the emulator is "step" mode.',action='store_true')
    parser.add_argument('-d','--drawfix', help='Enable anti-flicker, stops platter from drawing to screen when sprites are only removed.', action='store_true')
    parser.add_argument('-i','--initram', help='Initialize RAM to all zero values.', action='store_true')
    opts = parser.parse_args()

    if not os.path.isfile(opts.rom):
        raise OSError("File '" + opts.rom + "' does not exist")

    if opts.frequency:
        try: opts.frequency = int(opts.frequency)
        except: raise ValueError("Non-numeric frequency provided")
        if opts.frequency < 1:
            raise ValueError("Please use step mode for sub 1 hz operation")

    if opts.step:
        opts.frequency = 1000000 # 1 Ghz

    return opts

def main(opts):
    disp = platter(opts.rom, opts.frequency, 60, 60, opts.initram, opts.drawfix)
    disp.start(opts.step)

if __name__ == '__main__':
    main(parse_args())

