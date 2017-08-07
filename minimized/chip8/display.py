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
from .constants import *
from resource import getrusage, RUSAGE_SELF

class Display:

    def __init__(self, rom, cpuhz, audiohz, delayhz,
                 drawfix, enable_unicode,
                 wave_file=None):

        # Check if windows (no unicode in their Curses)
        self.screen_unicode = enable_unicode
        self.draw_char = UNICODE_DRAW if enable_unicode else WIN_DRAW

        # Init Curses
        self.screen = curses.initscr()
        self.screen.clear()

        # Used for graphics "smoothing" w/ -d flag
        self.draw_fix = drawfix
        self.prev_board=[0x00]*GFX_RESOLUTION

        # General Prep
        self.w_game = curses.newwin( DISPLAY_H, DISPLAY_W, 0, ( self.screen.getmaxyx()[1] - WIN_REG_W - DISPLAY_W ) // 2 )
        self.screen.clear()
        self.w_game.clear()
        self.w_game.refresh()

        # Load default sound
        self.wave_obj = None
        if not wave_file:
            wave_file = path.join('play.wav')

        # Print FYI for sound if no SA
        if sa is None:
            self.console_print("SimpleAudio is missing from your system." + \
                "You can install it via 'pip install simpleaudio'. " + \
                "The sound timmer will not be raised.")

        # Init sound if available
        elif wave_file.lower() != 'off':
            try:
                self.wave_obj = sa.WaveObject.from_wave_file(wave_file)
                self.play_obj = None
                self.audio_playing = False
            except FileNotFoundError:
                self.console_print("No sound file provided as parameter. " + \
                    "Unable to load default 'play.wav' from sound directory.")

        # Init the emulator
        self.emu = Emulator(rom, cpuhz, audiohz, delayhz)

        # Curses settings
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)

    def start(self):
        key_press_time = 0

        try:

            while True:

                # Grab key, escape any arrow seq
                key = self.w_console.getch()
                if key == KEY_ESC:
                    key = self.w_console.getch()
                    if key == KEY_ARROW:
                        key = KEY_ARROW_MAP[self.w_console.getch()]
                    self.flush_key_buffer()

                # Update Keypad press
                if time() - key_press_time > 0.5: #TODO Better input?
                    self.emu.prev_keypad = 0
                    self.emu.keypad = [False] * 16
                    key_press_time = time()
                if key in KEY_CONTROLS:
                    self.emu.keypad[KEY_CONTROLS[key]] = True

                # Exit check
                if key == KEY_EXIT:
                    break

                # Try to tick the cpu
                if not self.halt:
                    self.emu.run()

                # Update Display if we executed
                if self.emu.program_counter != self.previous_pc:
                    self.previous_pc = self.emu.program_counter

                # Detect jp Spinning
                elif not self.halt and self.emu.spinning:
                    self.halt  = True

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

                # Update the screen
                self.display_game()
                curses.doupdate()

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
                total_chunk  = str(upper_chunk + lower_chunk).zfill(8) \
                    .replace('3', self.draw_char.both ).replace('2', self.draw_char.lower ) \
                    .replace('1', self.draw_char.upper ).replace('0', self.draw_char.empty )
                self.w_game.addstr( 1 + y, 1 + x * 8, total_chunk )
        self.w_game.noutrefresh()

    def flush_key_buffer():
        if termios:
            tcflush(stdin, TCIOFLUSH)
        else:
            while kbhit():
                getch()

