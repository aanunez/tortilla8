#!/usr/bin/python3

import os
import argparse
from tortilla8.jalapeno import jalapeno

def parse_args():
    parser = argparse.ArgumentParser(description='Jalapeno will scan your CHIP-8 source code for pre-processor directives, \
                                                  apply them as needed, and produce a flattend source file that can be \
                                                  assembled with blackbean.')
    parser.add_argument('input', help='File to assemble')
    parser.add_argument('-o','--output',help='file to store processed source to, by default INPUT.jala is used.')
    opts = parser.parse_args()

    if not os.path.isfile(opts.input):
        raise OSError("File '" + opts.input + "' does not exist.")
    if not opts.output:
        opts.output  = '.'.join(opts.input.split('.')[0:-1]) if opts.input.find('.') != -1 else opts.input
        opts.output += '.jala'

    return opts

def main(opts):
    pp = jalapeno()
    with open(opts.input) as FH:
        pp.process(FH)
    with open(opts.output, 'w+') as FH:
        pp.print_processed_source(FH)

main(parse_args())
