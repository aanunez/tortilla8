#!/usr/bin/python3

import os
import argparse
from tortilla8.guacamole import guacamole

def parse_args():
    parser = argparse.ArgumentParser(description='Guacamole is a Chip-8 emulator ...')
    parser.add_argument('rom', help='ROM to load and play.')
    parser.add_argument("-f","--frequency", default=5,help='Frequency (in Hz) to target for CPU.')
    parser.add_argument("-st","--soundtimer", default=60,help='Frequency (in Hz) to target for the audio timmer.')
    parser.add_argument("-dt","--delaytimer", default=60,help='Frequency (in Hz) to target for the delay timmer.')
    parser.add_argument('-i','--initram', help='Initialize RAM to all zero values.', action='store_true')
    opts = parser.parse_args()

    if not os.path.isfile(opts.rom):
        raise OSError("File '" + opts.rom + "' does not exist.")

    if opts.frequency:
        opts.frequency = int(opts.frequency)

    return opts

def main(opts):
    guac = guacamole(opts.rom, opts.frequency, opts.soundtimer, opts.delaytimer, opts.initram)
    guac.log_to_screen = True
    try:
        while True:
            guac.run()
    except KeyboardInterrupt:
        pass

main(parse_args())
