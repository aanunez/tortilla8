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


def assemble(file_path):
    print("Nope")

def util_strip_comments(file_handle, outpout_handler=None):
    for line in file_handle:
        if line.isspace(): continue
        if line.lstrip().startswith(";"): continue
        line = line.rstrip().split(";")[0].rstrip()
        if outpout_handler==None:
            print(line)
        else:
            outpout_handler.write(line, end='\n')

def util_add_listing(file_handle, outpout_handler=None):
    mem_addr = 0x0200
    for line in file_handle:
        if line.isspace():
            line = (" " * 10) + line
        elif line.lstrip().startswith(";"):
            line = (" " * 10) + line
        elif ":" in line.split(";")[0]:
            line = (" " * 10) + line
        else:
            line = format(mem_addr, '#06x') + "    " + line
            mem_addr += 2
        if outpout_handler==None:
            print(line, end="")
        else:
            outpout_handler.write(line)

if __name__ == "__main__":
    #parser = argparse.ArgumentParser(description='Description of your program')
    #parser.add_argument('-i','--input', help='File to assemble', required=True)
    #parser.add_argument('-i','--input', help='File to assemble', required=True)
    #parser.add_argument('-i','--input', help='File to assemble', required=True)
    #parser.add_argument('-i','--input', help='File to assemble', required=True)

    #if len(sys.argv) != 3:
    #    print("Usage: " + sys.argv[0] + "<input> <output>")
    #    sys.exit(1)

    #if not os.path.isfile(sys.argv[1]):
    #    print("File does not exist.")
    #    sys.exit(1)

    with open(sys.argv[1]) as FH:
        #util_strip_comments(sys.argv[1])
        util_add_listing(FH)
    #assemble(sys.argv[1])
