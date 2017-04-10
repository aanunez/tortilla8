#!/usr/bin/python3

import sys
import os
import argparse

# Features:
# Generate code only
# Generate memory addresses (list)
# assemble
#
# Input flags:
#
# -i, --input           [expects param after]
# -o, --output          [expects param after]
# -l, --list, --listing [expects param after]
# -s, --strip           *Need param? Better name?
#

# Issues:
#   No support for "$" notation
#
# Assumes:
#   Tags are at the start of the line
#   Pre proc commands don't share a line with asm

# Statment:
#
#
#
#
#
#

PRE_PROC=("ifdef","else","endif","option","align","equ","=")
DATA_DECLARE={"db":1,"dw":2,"dd":4}
REGISTERS={ "v0":0x0,"v1":0x1,"v2":0x2,"v3":0x3,
            "v4":0x4,"v5":0x5,"v6":0x6,"v7":0x7,
            "v8":0x8,"v9":0x9,"va":0xA,"vb":0xB,
            "vc":0xC,"vd":0xD,"ve":0xE,"vf":0xF}
OP_CODES={}

class blackbean:

    def __init__(self):
        self.collection=[]
        self.mmap={}
        self.address=0x0200

    def reset(self):
        __init__()

    def assemble(self, file_path):
        with open(file_path) as fhandler:
            for line in fhandler:
                current_tokens = self.tokenize(line)
                self.update_memory(current_tokens)
                #Xlate to machine
                self.collection.append(current_tokens)

    def print_listing(self):
        # TODO print opcodes aswell
        for line in self.collection:
            if line.get('asm'):
                print(format(line['address'], '#06x') + '    ' + line['original'], end="")
            else:
                print((' ' * 10) + line['original'], end="")

    def export_binary(self, file_path):
        print("TODO")

    def update_memory(self, tokens):
        #TODO support db, dd.
        if tokens.get('asm'):
            tokens['address'] = self.address
            self.mmap[tokens.get('tag')] = self.address
            self.address += 2

    def tokenize(self,line):
        tokens = dict()
        tokens['original'] = line
        tokens['isEmpty'] = True
        line = line.lstrip()

        # Remove Blanks
        if line is '':
            return tokens

        # Remove Comment only lines
        if line.startswith(';'):
            tokens['comment'] = line.rstrip()
            return tokens

        tokens['isEmpty'] = False

        # Check for any comments
        tokens['comment'] = line.split(';')[1:]
        line = line.split(';')[0].rstrip()

        # Breakout into array
        line_array = list(filter(None, line.split(' ')))

        # Check if tag exists, must be left most
        if line_array[0].endswith(':'):
            tokens['tag'] = line_array[0][:-1]
            line_array.pop(0)
            if not line_array:
                return tokens

        # If there are additional tags raise error
        if ':' in ''.join(line_array):
            #TODO raise error
            print("ERROR: Multiple Memory Tags found on same line.")

        # Check for any pre-processor commands
        #TODO Pre proc directives are not respected right now
        for i,lex in enumerate(line_array):
            if lex.lower() in PRE_PROC:
                tokens['preProcess'] = ' '.join(line_array)
                line_array.pop(i)
                #TODO continue to tokenize
                return tokens

        # Check for data declarations
        if line_array[0].lower() in DATA_DECLARE:
            tokens['dataType'] = DATA_DECLARE[line_array[0].lower()]
            line_array.pop(0)
            if not line_array:
                #TODO raise error
                print("ERROR: Expected data declaration.")
            ddargs = ''.join(line_array).split(',')
            dec = []
            for arg in ddargs:
                if arg[0] is '#':
                    #TODO wrap int parse in try
                    val = int(arg[1:],16)
                else:
                    val = int(arg)
                if val > pow(256,tokens['dataType']):
                    #TODO raise error
                    print("ERROR: Data declaration overflow.")
                dec.append(val)
            tokens['declarations']=dec
            return tokens

        # Check for assembly instruction
        if line_array[0].lower in OP_CODES:
            #TODO continue to tokenize
            tokens['asm'] = " ".join(line_array)
            return tokens

        # Trash
        print("ERROR: Unkown command")
        return tokens

def util_strip_comments(file_path, outpout_handler=None):
    with open(file_path) as fhandler:
        for line in fhandler:
            if line.isspace(): continue
            if line.lstrip().startswith(';'): continue
            line = line.split(';')[0].rstrip()
            if outpout_handler==None:
                print(line)
            else:
                outpout_handler.write(line, end='\n')

def util_add_listing(file_path, outpout_handler=None):
    mem_addr = 0x0200
    with open(file_path) as fhandler:
        for line in fhandler:
            mem_inc = 2
            nocomment = line.split(';')[0].rstrip().lower()
            if not nocomment or nocomment.endswith(':') or any(s in nocomment for s in PRE_PROC):
                line = (' ' * 10) + line
            else:
                for k in DATA_DEFINE.keys():
                    if k in nocomment:
                        mem_inc = DATA_DEFINE[k]
                        break
                line = format(mem_addr, '#06x') + '    ' + line
                mem_addr += mem_inc
            if outpout_handler==None:
                print(line, end='')
            else:
                outpout_handler.write(line)

def parse_args():
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('-i','--input', help='File to assemble', required=True)

def main(args):
    print("Nope")

if __name__ == '__main__':
    #util_add_listing(sys.argv[1])
    bb = blackbean()
    bb.assemble(sys.argv[1])
    bb.print_listing()
    sys.exit(0)
    with open(sys.argv[1]) as FH:
        for line in FH:
            token = tokenize(line)
            if not token["isEmpty"]:
                if "asm" in token: print(token["asm"])
                if "tag" in token: print(token["tag"])
        #util_add_listing(FH)
    #main(parse_args())




