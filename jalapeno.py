#!/usr/bin/python3

import sys
import argparse

# Eventually, this will be the pre-processor

BEGIN_COMMENT=';'
PRE_PROC=('ifdef','ifndef','else','elif','elseif','endif','option','align','equ','=')

class jalapeno:

    def __init__(self):
        print("None")

    def reset(self):
        __init__(self)

    def process(self, in_handler, out_handler, definitions = []):
        skipping_lines = False
        awaiting_end = False

        for line in in_handler:
            piece = line.lower().split(BEGIN_COMMENT)[0].split()[0]

            if skipping_lines:
                if piece[0] in ('endif', 'else'):
                    skipping_lines = False
                    continue
                if piece[0] in ('elif', 'elseif') and piece[1] in definitions:
                    skipping_lines = False
                    continue

            if piece[0] is BEGIN_COMMENT:
                out_handler.write(line)
                continue

            if awaiting_end and piece[0] in ('endif', 'else'):
                #bork

            if piece[0] is 'ifdef' and piece[1] in definitions:
                continue
            else:
                skipping_lines = True
                continue

            if piece[0] is 'ifndef' and piece[1] not in definitions:
                continue.
            else:
                skipping_lines = True
                continue

            if piece[0] is 'option':
                continue #Throw away for now
            if piece[0] is 'align':
                continue #Throw away for now

            if piece[1] in ('equ','='):


            out_handler.write(line)

def parse_args():
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('input', help='File to assemble')
    parser.add_argument('-o','--output',help='file to store processed source to, by default INPUT.jala is used.')
    opts = parser.parse_args()

    if not os.path.isfile(opts.input):
        raise OSError("File '" + opts.input + "' does not exist.")
    if not opts.output:
        if opts.input.endswith('.src'):
            opts.output = opts.input[:-4]
        else:
            opts.output = opts.input

    return opts

def main(args):
    jala = jalapeno()
    with open(opts.input) as FH:
        jala.process(FH)

if __name__ == '__main__':
    main(parse_args())



