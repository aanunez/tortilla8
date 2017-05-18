#!/usr/bin/python3

import os
import sys
import select
import argparse
import contextlib

from tortilla8.blackbean import blackbean

parser = argparse.ArgumentParser(description=\
'''
Assemble your CHIP-8 programs to executable machine code. Listing files and
comment-striped files can also be generated. The "enforce" option is not
currently supported.
''')
parser.add_argument('input', nargs='?', help='File to assemble.')
parser.add_argument('-o','--output',help='Name of every generated file, will have either "strip", "lst", or "ch8" appended.')
parser.add_argument('-l','--list',  help='Generate listing file and store to OUTPUT.lst file.',action='store_true')
parser.add_argument('-s','--strip', help='Strip comments and store to OUTPUT.strip file.',action='store_true')
parser.add_argument('-e','--enforce',help='Force original Chip-8 specification and do not allow SHR, SHL, XOR, or SUBN instructions.',action='store_true')
opts = parser.parse_args()

if not os.path.isfile(opts.input):
    raise OSError("File '" + opts.input + "' does not exist.")

if not opts.output:
    opts.output  = '.'.join(opts.input.split('.')[0:-1]) if opts.input.find('.') != -1 else opts.input

bb = blackbean()
with open(opts.input) as fh:
    bb.assemble(fh)

if opts.list:
    with open(opts.output + '.lst', 'w') as fh:
        bb.print_listing(fh)

if opts.strip:
    with open(opts.output + '.strip', 'w') as fh:
        bb.print_strip(fh)

with open(opts.output + '.ch8', 'wb') as fh:
    bb.export_binary(fh)


