#!/usr/bin/python3

import sys
import os
import argparse
from collections import defaultdict

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
#   Tags and preproc commands can't be on the same line.
#

PRE_PROC=("ifdef","else","endif","option","align","equ","=")
DATA_DEFINE=("db","dw","dd")

def util_strip_comments(file_handle, outpout_handler=None):
    for line in file_handle:
        if line.isspace(): continue
        if line_is_comment(line): continue
        line = line.rstrip().split(';')[0].rstrip()
        if outpout_handler==None:
            print(line)
        else:
            outpout_handler.write(line, end='\n')

def util_add_listing(file_handle, outpout_handler=None):
    # TODO check if db, dd, dw and calc mem correctly.
    mem_addr = 0x0200
    for line in file_handle:
        mem_inc = 2
        if line.isspace() or line_is_comment(line) or line_is_tag(line) or line_is_preproc(line):
            line = (' ' * 10) + line
        else:
            #Check here
            line = format(mem_addr, '#06x') + '    ' + line
            mem_addr += mem_inc
        if outpout_handler==None:
            print(line, end='')
        else:
            outpout_handler.write(line)

def tokenize(line):
    token = dict()
    line = line.lstrip()

    if line is '':
        token["isEmpty"] = True
        return token

    # Remove Blanks and Comment only lines
    if line.startswith(';'):
        token["comment"] = line.rstrip()
        token["isEmpty"] = True
        return token

    token["isEmpty"] = False

    # Check for any comments
    token["comment"] = line.split(';')[1:]
    line = line.split(';')[0].rstrip()

    # Breakout into array
    line_array = list(filter(None, line.split(' ')))

    # Check if tag exists, must be left most
    if line_array[0].endswith(':'):
        token["tag"] = line_array[0]
        line_array.pop(0)

    # Check for any pre-processor commands
    for i in line_array:
        if i.lower() in PRE_PROC:
            token["pre"] = " ".join(line_array)
            return token

    # Either asm or data declare
    token["asm"] = " ".join(line_array)

    return token



def parse_args():
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('-i','--input', help='File to assemble', required=True)

def main(args):
    print("Nope")

if __name__ == '__main__':
    with open(sys.argv[1]) as FH:
        for line in FH:
            token = tokenize(line)
            if not token["isEmpty"]:
                if "pre" in token: print(token["pre"])
                if "asm" in token: print(token["asm"])
                if "tag" in token: print(token["tag"])
        #util_add_listing(FH)
    #main(parse_args())



############################################################################################




def is_line_addressable(line):
    return line.isspace() or line_is_comment(line) or line_is_tag(line) or line_is_preproc(line)

def util_strip_preproc(file_handle, outpout_handler=None):
    print("Nope")

def line_is_comment(line):
    '''Returns true if the line contains ONLY a comment'''
    return line.lstrip().startswith(';')

def line_is_tag(line):
    '''Returns true if the line contains ONLY a memory tag (trailing comments are fine).'''
    return line.split(';')[0].rstrip().endswith(':')

def line_contains_tag(line):
    '''_'''
    return line.split(' ')[0].endswith(':')

def line_is_preproc(line):
    '''Returns true if the line contains ONLY a pre-processor command'''
    if line_contains_tag(line): return False
    if '=' in line.split(';')[0] or 'equ' in line.split(';')[0].lower(): return True
    return line.lstrip().split(' ')[0].lower() in PRE_PROC

def line_contains_preproc(line):
    return '=' in line.split(';')[0] or 'equ' in line.split(';')[0].lower()



