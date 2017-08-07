#!/usr/bin/env python3

from os.path import isfile
from sys import platform, argv
from argparse import ArgumentParser, ArgumentTypeError
from .emulator import Emulator
from .display import Display

def pos_int(value):
    ivalue = int(value)
    if ivalue < 1:
         raise ArgumentTypeError("%s is an invalid positive int value." % value)
    return ivalue

def parse_args():
    parser = ArgumentParser(description=
        '''
        Start a text (unicode) based Chip8 emulator which disaplys a game screen, all
        registers, the stack, recently processed instructions, and a console to log
        any issues that occur.
        ''')

    parser.add_argument('rom', help=
        'ROM to load and play.')
    parser.add_argument('-f','--frequency', type=pos_int, default=10,help=
        'CPU frequency to target, minimum 1Hz. 10Hz by default.')
    parser.add_argument('-d','--drawfix', action='store_true', help=
        'Enable anti-flicker, stops the display from drawing to the screen when sprites are only removed.', )
    parser.add_argument('-a','--audio', help=
        'Path to audio to play for Sound Timer, or "off" to prevent sound from playing.' + \
        'By default a 440Hz square wave is used.')
    parser.add_argument('-ls','--legacy_shift', action='store_true', help=
        'Use the legacy shift method of bit shift Y and storing to X. ' +\
        'By default the newer method is used where Y is ignored and X is bitshifted then stored to itself.')
    parser.add_argument("-u","--unicode", action='store_true', help=
        'Forces unicode to be used for the game screen.')

    return parser.parse_args()

def main():
    if len(argv) == 1:
        argv.append('-h')

    opts = parse_args()
    if not isfile(opts.rom):
        raise OSError("File '" + opts.rom + "' does not exist")

    screen_unicode = True if platform != 'win32' or opts.unicode else False
    disp = Display( opts.rom, opts.frequency, 60, 60,
                    opts.drawfix, screen_unicode, opts.audio )
    disp.start()

if __name__ == "__main__":
    main()
