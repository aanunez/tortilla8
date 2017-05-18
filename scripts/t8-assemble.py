#!/usr/bin/python3

import os
import sys
import select
import argparse
import contextlib

from tortilla8.blackbean import blackbean

def parse_args():
    """
    Parse arguments to blackbean when called as a script.
    """
    parser = argparse.ArgumentParser(description='Blackbean will assemble your CHIP-8 programs to executable machine code. BB can also generate listing files and comment-striped files. The "enforce" option is not currently supported.')
    parser.add_argument('input', nargs='?', help='file to assemble.')
    parser.add_argument('-o','--output',help='file to store binary executable to, by default INPUT.ch8 is used.')
    parser.add_argument('-l','--list',  help='generate listing file and store to OUTPUT.lst file.',action='store_true')
    parser.add_argument('-s','--strip', help='strip comments and store to OUTPUT.strip file.',action='store_true')
    parser.add_argument('-e','--enforce',help='force original Chip-8 specification and do not allow SHR, SHL, XOR, or SUBN instructions.',action='store_true')
    opts = parser.parse_args()

    force_out = True

    if not opts.input:
        if select.select([sys.stdin,],[],[],0.0)[0]:
            opts.input = sys.stdin
            if not opts.output:
                opts.output = sys.stdout
        else:
            raise OSError("No input provided.")
    elif not os.path.isfile(opts.input):
        raise OSError("File '" + opts.input + "' does not exist.")

    if not opts.output:
        opts.output  = '.'.join(opts.input.split('.')[0:-1]) if opts.input.find('.') != -1 else opts.input
        force_out = False

    return opts, force_out

@contextlib.contextmanager
def smart_open(filename = None, mode = 'r'):
    """
    Open file OR use stdin. This is used to support piping.
    """
    if filename and filename != '-':
        fh = open(filename, mode)
    else:
        fh = sys.stdin
    try:
        yield fh
    finally:
        if fh is not sys.stdin:
            fh.close()

def main(opts, force_out):
    """
    Handles blackbean being called as a script.
    """
    bb = blackbean()
    with smart_open(opts.input) as FH:
        bb.assemble(FH)
    if opts.list:
        with open(opts.output + '.lst', 'w') as FH:
            bb.print_listing(FH)
    if opts.strip:
        with open(opts.output + '.strip', 'w') as FH:
            bb.print_strip(FH)
    if not force_out:
        opts.output += '.ch8'
    with open(opts.output, 'wb') as FH:
        bb.export_binary(FH)

main(*parse_args())


