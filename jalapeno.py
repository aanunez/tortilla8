#!/usr/bin/python3

import sys
import argparse
from cilantro import cilantro
from tortilla8_constants.py import *

#TODO do something with mode options
#TODO clean up
#TODO write main

class jalapeno:

    def __init__(self):
        self.collection = []
        self.symbols = {}

    def reset(self):
        self.__init__(self)

    def process(self, file_handler, definitions = []):
        skipping_lines = False
        awaiting_end = False

        for i,line in enumerate(file_handler):
            t = cilantro(line, i)

            if skipping_lines:
                if (t.pp_directive in ('endif','else')) or\
                  ((t.pp_directive in ELSE_IF) and (t.pp_args[0] in definitions)):
                    skipping_lines = False
                continue

            if not t.pp_directive:
                self.collection.append(t)
                continue

            if awaiting_end and t.pp_directive in END_MARKS:
                awaiting_end = False
                continue

            if t.pp_directive is 'ifdef':
                if t.pp_args[0] in definitions:
                    awaiting_end = True
                else:
                    skipping_lines = True
                continue

            if t.pp_directive is 'ifndef':
                if t.pp_args[0] not in definitions:
                    awaiting_end = True
                else:
                    skipping_lines = True
                continue

            if t.pp_directive in MODE_MARKS:
                continue #Throw away for now

            if t.pp_directive in ('equ','='):
                self.symbols[t.pp_args[0]] = t.pp_args[1]

            self.collection.append(t)

        for sym in self.symbols:
            for tl in self.collection:
                for i,arg in enumerate(tl.arguments):
                    if arg is sym:
                        tl.arguments[i] = self.symbols[sym]
                for i,arg in enumerate(tl.data_declarations):
                    if arg is sym:
                        tl.data_declarations[i] = self.symbols[sym]

    def print_processed_source(self, file_handler):
        for tl in self.collection:
            file_handler.write(tl.original)

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



