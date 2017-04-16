#!/usr/bin/python3

import os
import sys
import argparse
from cilantro import cilantro
from tortilla8_constants import *

#TODO not correctly replacing EQU and = stuff
#TODO do something with mode options
#TODO clean up
#TODO write main
#TODO correct file naming issues
#TODO remove excess white space

class jalapeno:
    """
    Jalapeno is a pre-processor class that can take file handlers,
    process all common chip 8 pre processor directives and return
    a flatten source file.
    """

    def __init__(self):
        """
        Init the token collection and symbols list.
        """
        self.collection = []
        self.symbols = {}

    def reset(self):
        """
        Reset the pre-processor to process another file.
        """
        self.__init__(self)

    def process(self, file_handler, definitions = []):
        """
        TODO write some good stuff here
        """
        skipping_lines = False
        awaiting_end = False

        for i,line in enumerate(file_handler):
            t = cilantro(line, i)

            if skipping_lines:
                if (t.pp_directive in ('endif','else')) or\
                   (t.pp_directive in ELSE_IF and t.pp_args[0] in definitions):
                    skipping_lines = False
                    awaiting_end = True
                continue

            if not t.pp_directive:
                self.collection.append(t)
                continue

            if awaiting_end and t.pp_directive in END_MARKS:
                awaiting_end = False
                continue

            if t.pp_directive == 'ifdef':
                if t.pp_args[0] in definitions:
                    awaiting_end = True
                else:
                    skipping_lines = True
                continue

            if t.pp_directive == 'ifndef':
                if t.pp_args[0] not in definitions:
                    awaiting_end = True
                else:
                    skipping_lines = True
                continue

            if t.pp_directive in MODE_MARKS:
                continue #TODO Throw away for now

            if t.pp_directive in ('equ','='):
                self.symbols[t.pp_args[0]] = t.pp_args[1]
                continue

            self.collection.append(t)

        for sym in self.symbols:                 #TODO Can this loop be better?
            for tl in self.collection:
                for i,arg in enumerate(tl.arguments):
                    if arg == sym:
                        tl.arguments[i] = self.symbols[sym]
                for i,arg in enumerate(tl.data_declarations):
                    if arg == sym:
                        tl.data_declarations[i] = self.symbols[sym]
                tl.pp_line = tl.original.replace(sym, self.symbols[sym])

    def print_processed_source(self, file_handler = None):
        """
        Print flattened source code to stdout or file handler.
        """
        print(self.symbols)
        for tl in self.collection:
            if file_handler:
                file_handler.write(tl.pp_line) #TODO Not writing out translations
            else:
                print(tl.pp_line, end='')

def parse_args():
    """
    Parse arguments to guacamole when called as a script.
    """
    parser = argparse.ArgumentParser(description='Jalapeno will scan your CHIP-8 source code for pre-processing directives, apply them as needed, and produce a flatten source file that can be assembled with blackbean.')
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

def main(opts):
    """
    Handles guacamole being called as a script.
    """
    jala = jalapeno()
    with open(opts.input) as FH:
        jala.process(FH)
    with open(opts.output + '.jala', 'w') as FH:
        jala.print_processed_source(FH)

if __name__ == '__main__':
    """
    """
    main(parse_args())



