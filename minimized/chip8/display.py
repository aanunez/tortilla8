#!/usr/bin/env python3

# Import curses
try: import curses
except ImportError:
    raise ImportError("Curses is missing from your system! ")

# Import Sound (optional)
try: import simpleaudio as sa
except ImportError:
    sa = None

# Import System to clear keybuffer
try:
    termios = True
    from termios import tcflush, TCIOFLUSH
    from sys import stdin
except ImportError:
    termios = None
    from msvcrt import getch, kbhit

# Everything else
from os import path
from sys import platform
from time import time, sleep
from .emulator import Emulator
from collections import namedtuple

CHAR_SET = namedtuple('CHAR_SET', 'upper lower both empty')

class Display:

    UNICODE_DRAW = CHAR_SET('▀','▄','█',' ')
    WIN_DRAW = CHAR_SET('*','o','8',' ')

    KEY_EXIT  = 120 # X
    KEY_CONTROLS={
        48:0x0, 49:0x1, 50:0x2, 51:0x3, # 0 1 2 3
        52:0x4, 53:0x5, 54:0x6, 55:0x7, # 4 5 6 7
        56:0x8, 57:0x9, 47:0xA, 42:0xB, # 8 9 / *
        45:0xC, 43:0xD, 10:0xE, 46:0xF} # - + E .

    def __init__(self, rom, cpuhz, audiohz, delayhz,
                 drawfix, enable_unicode,
                 wave_file=None):

        # Check if windows (no unicode in their Curses)
        self.screen_unicode = enable_unicode
        self.draw_char = Display.UNICODE_DRAW if enable_unicode else Display.WIN_DRAW

        # Init Curses
        self.screen = curses.initscr()
        self.screen.clear()

        # Used for graphics "smoothing" w/ -d flag
        self.draw_fix = drawfix
        self.prev_board=[0x00]*Emulator.GFX_RESOLUTION

        # General Prep
        self.window = curses.newwin( int(Emulator.GFX_HEIGHT_PX/2)+2, Emulator.GFX_WIDTH_PX+2, 0, 0)
        self.window.nodelay(1)
        self.window.clear()
        self.window.refresh()
        self.window.border()

        # Load default sound
        self.wave_obj = None
        if not wave_file:
            wave_file = path.join('play.wav')

        # Init sound if available
        elif wave_file.lower() != 'off':
            try:
                self.wave_obj = sa.WaveObject.from_wave_file(wave_file)
                self.play_obj = None
                self.audio_playing = False
            except FileNotFoundError:
                pass

        # Init the emulator
        self.emu = Emulator(rom, cpuhz, audiohz, delayhz)

        # Curses settings
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)

    def start(self):
        halt = False
        key_press_time = 0
        previous_pc = 0

        try:

            while True:

                # Grab key
                key = self.window.getch()

                # Update Keypad press
                if time() - key_press_time > 0.5: #TODO Better input?
                    self.emu.prev_keypad = 0
                    self.emu.keypad = [False] * 16
                    key_press_time = time()
                if key in Display.KEY_CONTROLS:
                    self.emu.keypad[Display.KEY_CONTROLS[key]] = True

                # Exit check
                if key == Display.KEY_EXIT:
                    break

                # Try to tick the cpu
                if not halt:
                    self.emu.run()

                # Update Display if we executed
                if self.emu.program_counter != previous_pc:
                    previous_pc = self.emu.program_counter
                    self.display_game()
                    curses.doupdate()

                # Detect jp Spinning
                elif not halt and self.emu.spinning:
                    halt  = True

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

                # Don't waste too many cycles
                sleep(self.emu.cpu_wait * 0.25)

        except KeyboardInterrupt:
            return
        except:
            print("Unhandled Error!")
            raise
        finally:
            curses.nocbreak()
            curses.echo()
            curses.endwin()

    def display_game(self):
        if not self.emu.draw_flag: return
        self.emu.draw_flag = False

        if self.draw_fix:
            prev_str = ""
            curr_str = ""
            for val in self.prev_board:
                prev_str += bin(val)[2:].zfill(8)
            for val in self.emu.ram[Emulator.GFX_ADDRESS:Emulator.GFX_ADDRESS+Emulator.GFX_RESOLUTION]:
                curr_str += bin(val)[2:].zfill(8)
            int_prev = int(prev_str,2)
            int_curr = int(curr_str,2)
            self.prev_board = self.emu.ram[Emulator.GFX_ADDRESS:Emulator.GFX_ADDRESS+Emulator.GFX_RESOLUTION]
            if ( ( int_prev ^ int_curr ) & int_prev ) == ( int_prev ^ int_curr ):
                #Only 1s were changed to 0s, skip the draw to prevent SOME flicker
                return

        for y in range( int(Emulator.GFX_HEIGHT_PX / 2) ):
            for x in range(Emulator.GFX_WIDTH):
                upper_chunk = int( bin( self.emu.ram[ Emulator.GFX_ADDRESS + ( (y * 2 + 0) * Emulator.GFX_WIDTH) + x ] )[2:] )
                lower_chunk = int( bin( self.emu.ram[ Emulator.GFX_ADDRESS + ( (y * 2 + 1) * Emulator.GFX_WIDTH) + x ] )[2:].replace('1','2') )
                total_chunk  = str(upper_chunk + lower_chunk).zfill(8) \
                    .replace('3', self.draw_char.both ).replace('2', self.draw_char.lower ) \
                    .replace('1', self.draw_char.upper ).replace('0', self.draw_char.empty )
                self.window.addstr( 1+y, 1+x*8, total_chunk )
        self.window.noutrefresh()

    def flush_key_buffer():
        if termios:
            tcflush(stdin, TCIOFLUSH)
        else:
            while kbhit():
                getch()

