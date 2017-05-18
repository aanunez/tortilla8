#!/usr/bin/python3

import os
import argparse
from tortilla8.platter import platter

def pos_int(value):
    ivalue = int(value)
    if ivalue < 1:
         raise argparse.ArgumentTypeError("%s is an invalid positive int value." % value)
    return ivalue

parser = argparse.ArgumentParser(description=
'''
Start a text (unicdoe) based Chip8 emulator.
''')
parser.add_argument('rom', help='ROM to load and play.')
group = parser.add_mutually_exclusive_group()
group.add_argument('-f','--frequency', type=pos_int, default=10,help='CPU frequency (in Hz) to target, minimum 1 hz.')
group.add_argument('-s','--step',     help='Start the emulator is "step" mode.',action='store_true')
parser.add_argument('-d','--drawfix', help='Enable anti-flicker, stops platter from drawing to screen when sprites are only removed.', action='store_true')
parser.add_argument('-i','--initram', help='Initialize RAM to all zero values. Needed to run some ROMs that assume untouched addresses to be zero.', action='store_true')
parser.add_argument('-a','--audio',   help='Path to audio to play for Sound Timer, or "off" to prevent sound from playing.')
parser.add_argument("-st","--soundtimer", type=pos_int, default=60, help='Frequency (in Hz) to target for the audio timmer.')
parser.add_argument("-dt","--delaytimer", type=pos_int, default=60, help='Frequency (in Hz) to target for the delay timmer.')
opts = parser.parse_args()

if not os.path.isfile(opts.rom):
    raise OSError("File '" + opts.rom + "' does not exist")

if opts.step:
    opts.frequency = 1000000 # 1 Ghz

disp = platter(opts.rom, opts.frequency, opts.soundtimer, opts.delaytimer, opts.initram, opts.drawfix, opts.audio)
disp.start(opts.step)

