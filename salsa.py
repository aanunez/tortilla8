#!/usr/bin/python3

import os
import re
import argparse
from constants.opcodes import OP_REG, OP_ARGS, OP_CODES

# TODO Strings, comments

class salsa:

    def __init__(self, byte_list):
        self.hex_instruction =  hex( byte_list[0] )[2:].zfill(2)
        self.hex_instruction += hex( byte_list[1] )[2:].zfill(2)
        self.is_valid = False
        self.mnemonic = None
        self.mnemonic_arg_types = None
        self.disassembled_line = ""

        # Match the instruction via a regex index
        for mnemonic, reg_patterns in OP_CODES.items():
            for pattern_version in reg_patterns:
                if not re.match(pattern_version[OP_REG], self.hex_instruction): continue
                self.mnemonic = mnemonic
                self.mnemonic_arg_types = pattern_version[OP_ARGS]
                self.is_valid = True
                break
            if self.is_valid:
                break

        # If not a valid instruction, assume data
        if not self.is_valid:
            self.disassembled_line = 'dw' + self.hex_instruction
            return

        # No args to parse
        if self.mnemonic_arg_types is None:
            self.disassembled_line = self.mnemonic
            return

        # Parse Args
        reg_numb = 1
        for arg_type in self.mnemonic_arg_types:
            if arg_type is 'register':
                tmp = 'v'+self.hex_instruction[reg_numb]
            elif arg_type is 'byte':
                tmp = '#'+self.hex_instruction[2:]
            elif arg_type is 'address':
                tmp = '#'+self.hex_instruction[1:]
            elif arg_type is 'nibble':
                tmp = '#'+self.hex_instruction[3]
            else:
                tmp = arg_type
            self.disassembled_line += tmp.ljust(5) + ','
            reg_numb = 2

        self.disassembled_line = (self.mnemonic.ljust(5) + self.disassembled_line[:-1]).rstrip()

def dissassemble_file(in_handler, out_handler):
    byte_list = []
    file_size = os.path.getsize(input_path)
    for i in range(int(file_size/2)):
        byte_list[0:2] = [int.from_bytes(in_handler.read(1), 'big') for j in range(2)]
        dis_inis = salsa(byte_list)
        out_handler.write(dis_inis.disassembled_line + '\n')
    if file_size % 2 == 1:
        out_handler.write(hex(int.from_bytes(in_handler.read(1), 'big'))[2:].zfill(2) + '\n')

def parse_args():
    parser = argparse.ArgumentParser(description='Does a thing')
    parser.add_argument('rom', nargs='?', help='file to disassemble.')
    parser.add_argument('-o','--output',help='file to write to.')
    opts = parser.parse_args()

    if opts.output is None:
        opts.output  = '.'.join(opts.rom.split('.')[0:-1]) if opts.rom.find('.') else opts.rom
        opts.output += '.asm'

    return opts

def main(opts):
    file_in  = open(opts.rom, 'rb')
    file_out = open(opts.output, 'w+')
    dissassemble_file(file_in, file_out)
    file_in.close()
    file_out.close()

if __name__ == '__main__':
    main(parse_args())
