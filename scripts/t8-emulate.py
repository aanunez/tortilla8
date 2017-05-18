#!/usr/bin/python3

import os
import argparse
from tortilla8.platter import platter

def parse_args():
    parser = argparse.ArgumentParser(description='Platter is a text based front end for the Chip-8 emulator guacamole. ')
    parser.add_argument('rom', help='ROM to load and play.')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-f','--frequency', default=10,help='CPU frequency (in Hz) to target, minimum 1 hz.')
    group.add_argument('-s','--step', help='Start the emulator is "step" mode.',action='store_true')
    parser.add_argument('-d','--drawfix', help='Enable anti-flicker, stops platter from drawing to screen when sprites are only removed.', action='store_true')
    parser.add_argument('-i','--initram', help='Initialize RAM to all zero values. Needed to run some ROMs that assume untouched addresses to be zero.', action='store_true')
    parser.add_argument('-a','--audio', help='Path to audio to play for Sound Timer, or "off" to prevent sound from playing.')
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
    disp = platter(opts.rom, opts.frequency, 60, 60, opts.initram, opts.drawfix, opts.audio)
    disp.start(opts.step)

main(parse_args())

