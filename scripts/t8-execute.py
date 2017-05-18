#!/usr/bin/python3

import os
import argparse
from tortilla8.guacamole import guacamole

def pos_int(value):
    ivalue = int(value)
    if ivalue < 1:
         raise argparse.ArgumentTypeError("%s is an invalid positive int value." % value)
    return ivalue

parser = argparse.ArgumentParser(description=
'''
Execute a rom to quickly check for errors, instructions are printed to screen
immediately after execution of that operation code.
''')
parser.add_argument('rom', help='ROM to load and play.')
parser.add_argument("-f","--frequency",   type=pos_int, default=5,  help='Frequency (in Hz) to target for CPU.')
parser.add_argument("-st","--soundtimer", type=pos_int, default=60, help='Frequency (in Hz) to target for the audio timmer.')
parser.add_argument("-dt","--delaytimer", type=pos_int, default=60, help='Frequency (in Hz) to target for the delay timmer.')
parser.add_argument('-i','--initram', help='Initialize RAM to all zero values.', action='store_true')
opts = parser.parse_args()

if not os.path.isfile(opts.rom):
    raise OSError("File '" + opts.rom + "' does not exist.")

guac = guacamole(opts.rom, opts.frequency, opts.soundtimer, opts.delaytimer, opts.initram)
guac.log_to_screen = True
try:
    while True:
        guac.run()
except KeyboardInterrupt:
    pass

