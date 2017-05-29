#!/usr/bin/python3

# Import curses
try: import curses
except ImportError:
    raise ImportError('Curses is missing from your system. Consult the README for information on installing for your platform.')

# Import Sound (optional)
try: import simpleaudio as sa
except ImportError:
    sa = None
    pass

# Everything else
from sys import platform
import os
import time
import textwrap
import collections
from enum import Enum
from .constants.curses import *
from tortilla8.guacamole import guacamole, Emulation_Error
from .constants.reg_rom_stack import PROGRAM_BEGIN_ADDRESS, NUMB_OF_REGS
from .constants.graphics import GFX_RESOLUTION, GFX_ADDRESS, GFX_HEIGHT_PX, GFX_WIDTH

#TODO pass through for shift (old/new) functionality

#TODO Allow editing controls
#TODO Improve input. Only most recent button press is used.

#TODO Support non 64x32 displays
#TODO double the resolution if window is large enough
#TODO add Keypad display?

class platter:

    def __init__(self, rom, cpuhz, audiohz, delayhz, init_ram, drawfix, wave_file=None):

        # Check if windows (no unicode in their Curses)
        self.unicode   = True if platform != 'win32' else False
        self.draw_char = UNICODE_DRAW if self.unicode else WIN_DRAW

        # Init Curses
        self.screen = curses.initscr()
        self.screen.clear()
        self.L, self.C = self.screen.getmaxyx()

        # Used for graphics "smoothing" w/ -d flag
        self.draw_fix = drawfix
        self.prev_board=[0x00]*GFX_RESOLUTION

        # General Prep
        self.rom = rom
        self.dynamic_window_gen()
        self.clear_all_windows()
        self.init_logs()

        # Print FYI for game window
        if self.w_game is None:
            self.console_print("Window must be atleast "+ str(DISPLAY_MIN_W) + "x" + str(DISPLAY_MIN_H) +" to display the game screen")

        # Load default sound
        self.wave_obj = None
        if not wave_file:
            wave_file = os.path.join('tortilla8','sound','play.wav')

        # Print FYI for sound if no SA
        if sa is None:
            self.console_print("SimpleAudio is missing from your system. You can install it via 'pip install simpleaudio'. The sound timmer will not be raised.")

        # Init sound if available
        elif wave_file.lower() != 'off':
            try:
                self.wave_obj = sa.WaveObject.from_wave_file(wave_file)
                self.play_obj = None
                self.audio_playing = False
            except FileNotFoundError:
                self.console_print("No sound file provided as parameter. Unable to load default 'play.wav' from sound directory.")

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

    def resize_logs(self):
        if (self.w_instr.getmaxyx()[0] - BORDERS) != self.instr_history.maxlen:
            self.instr_history
        self.console_history

    def start(self, step_mode=False):
        key_press_time = 0
        key_msg_displayed = False

        if step_mode:
            self.console_print("Emulator started in step mode. Press '" + chr(KEY_STEP).upper() + "' to process one instruction.")

        try:

            while True:

                # Grab key, escape any arrow seq
                key = self.w_console.getch()
                if key == KEY_ESC:
                    key = self.w_console.getch()
                    if key == KEY_ARROW:
                        key = KEY_ARROW_MAP[self.w_console.getch()]

                # Freq modifications
                if key == 'up':
                    self.emu.cpu_hz *= 1.05
                if key == 'down':
                    self.emu.cpu_hz = 1 if self.emu.cpu_hz * .95 < 1 else self.emu.cpu_hz * .95

                # Update Keypad press
                if time.time() - key_press_time > 0.5: #TODO Better input?
                    self.emu.keypad = [False] * 16
                    key_press_time = time.time()
                if key in KEY_CONTROLS:
                    self.emu.keypad[KEY_CONTROLS[key]] = True

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

                # Detect jp Spinning
                elif not self.halt and self.emu.spinning:
                    self.instr_history.appendleft(hex3(self.emu.program_counter) + " spin jp")
                    self.console_print("Spin detected. Press '" + chr(KEY_EXIT).upper() + "' to exit")
                    self.halt  = True

                # Toggle for Step Mode
                if step_mode:
                    self.halt = True

                # Start/stop Audio
                if sa is not None and self.wave_obj is not None:
                    self.audio_playing = False if self.emu.sound_timer_register == 0 else True
                    if not self.audio_playing and self.play_obj is None:
                        pass
                    elif self.audio_playing and self.play_obj is None:
                        self.play_obj = self.wave_obj.play()
                    elif not self.audio_playing and self.play_obj is not None:
                        self.play_obj.stop()
                        self.play_obj = None
                    elif self.audio_playing and not self.play_obj.is_playing():
                        self.play_obj = self.wave_obj.play()

                # Check if screen was re-sized
                if curses.is_term_resized(self.L, self.C):
                    self.L, self.C = self.screen.getmaxyx()
                    curses.resizeterm(self.L, self.C)
                    self.screen.clear()
                    self.screen.refresh()
                    self.dynamic_window_gen()
                    self.clear_all_windows()
                    self.init_logs()

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
                self.console_print( "Fatal error has occured. Press '" + chr(KEY_RESET).upper() + "' to reset" )

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
        self.display_menu()
        curses.doupdate()

    def update_instr_history(self):
        self.instr_history.appendleft(hex3(self.emu.calling_pc) + " " + \
                                           self.emu.dis_ins.hex_instruction + " " + \
                                           self.emu.dis_ins.mnemonic)

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
            self.w_menu.refresh()
        if self.w_game is not None:
            self.w_game.clear()
            self.w_game.border()
            self.w_game.refresh()
        self.w_reg.border()
        self.w_reg.addstr( 1, REG_OFFSET, "Registers")
        self.w_stack.border()
        self.w_stack.addstr( 1, STAK_OFFSET, "Stack")
        self.w_console.border()
        self.w_instr.border()
        self.w_console.nodelay(1)
        self.display_logo()

    def display_logo(self):
        if self.screen.getmaxyx()[0] < LOGO_MIN: return
        if not self.unicode: return
        logo_offset = ( self.w_logo.getmaxyx()[0] - len(LOGO) ) // 2
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
                total_chunk  = str(upper_chunk + lower_chunk).zfill(8).replace('3', self.draw_char.both ).replace('2', self.draw_char.lower )\
                                                                      .replace('1', self.draw_char.upper ).replace('0', self.draw_char.empty )
                self.w_game.addstr( 1 + y, 1 + x * 8, total_chunk )
        self.w_game.noutrefresh()

    def display_instructions(self):
        for i,val in enumerate(self.instr_history):
            self.w_instr.addstr( 1 + i, 2, val.ljust(15))
        self.w_instr.noutrefresh()

    def display_registers(self):
        for i in range(NUMB_OF_REGS):
            self.w_reg.addstr( ( i // 4 ) + 2, i % 4 * 9 + 2, hex(i)[2] + ": " + hex2(self.emu.register[i]) )
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

    def display_menu(self):
        if self.w_menu is None: return
        prefix = ""
        cpu_hz = str(self.emu.cpu_hz) if self.emu.cpu_hz > 1e3 else str(self.emu.cpu_hz)[0:5]
        for pre,val in PREFIX:
            if self.emu.cpu_hz % val != self.emu.cpu_hz:
                prefix = pre
                cpu_hz = str(self.emu.cpu_hz / val)[0:5]
                break
        left = "E̲xit  ̲Reset  ̲Step"
        right = "🡹🡻 Freq " + cpu_hz + prefix + "hz"
        middle = " " * ( self.w_menu.getmaxyx()[1] - len(left) - len(right) - 1 )
        self.w_menu.addstr( 1, 2, left + middle + right )
        self.w_menu.noutrefresh()

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Dynamic Window Generator

    def dynamic_window_gen(self):
        while (self.L < H_MIN) or (self.C < W_MIN):
            try:
                self.screen.addstr(self.L//2 -1, (self.C - len(DY_MSG_1)) //2 , DY_MSG_1)
                self.screen.addstr(self.L//2,    (self.C - len(DY_MSG_2)) //2 , DY_MSG_2)
                self.screen.refresh()
                if curses.is_term_resized(self.L, self.C):
                    self.L, self.C = self.screen.getmaxyx()
                    curses.resizeterm(self.L, self.C)
                    self.screen.clear()
            except:
                self.cleanup()
                raise IOError("Terminal window too small to use.\nResize to atleast " + str(W_MIN) + "x" + str(H_MIN))

        self.w_reg     = curses.newwin( WIN_REG_H, WIN_REG_W , 0, self.C - WIN_REG_W )
        self.w_instr   = curses.newwin( self.L - WIN_REG_H, WIN_INSTR_W, WIN_REG_H, self.w_reg.getbegyx()[1] )
        self.w_stack   = curses.newwin( self.L - WIN_REG_H, WIN_STACK_W, WIN_REG_H, self.w_instr.getbegyx()[1] + WIN_INSTR_W )
        self.w_logo    = curses.newwin( self.L - WIN_REG_H, WIN_LOGO_W , WIN_REG_H, self.w_stack.getbegyx()[1] + WIN_STACK_W )
        self.w_menu = curses.newwin( WIN_MENU_H, self.w_reg.getbegyx()[1], self.L - WIN_MENU_H, 0 )
        self.w_game    = None
        self.w_console = None

        if (self.L < DISPLAY_MIN_H) or (self.C < DISPLAY_MIN_W):
            self.w_console = curses.newwin( self.L - WIN_MENU_H,  self.w_reg.getbegyx()[1], 0, 0 )
        else:
            self.w_game    = curses.newwin( DISPLAY_H, DISPLAY_W, 0, ( self.C - WIN_REG_W - DISPLAY_W ) // 2 )
            self.w_console = curses.newwin( self.L - DISPLAY_H - WIN_MENU_H, self.w_reg.getbegyx()[1], DISPLAY_H, 0 )

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Helper functions

def hex2(integer):
    return "0x" + hex(integer)[2:].zfill(2)

def hex3(integer):
    return "0x" + hex(integer)[2:].zfill(3)

