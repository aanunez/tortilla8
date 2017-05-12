#!/usr/bin/python3

import os
import re
import argparse
from constants.opcodes import OP_REG, OP_ARGS, OP_CODES

# TODO all of this is wrong.

class disassembler:

    def __init__(self, byte_list):
        self.hex_instruction =  hex( byte_list[0] )[2:].zfill(2)
        self.hex_instruction += hex( byte_list[1] )[2:].zfill(2)
        self.is_valid = False
        self.mnemonic = None
        self.mnemonic_arg_types = None

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

def dissassemble_file(file_path):
    byte_list = [0,0]
    file_size = os.path.getsize(file_path)
    with open(file_path, 'rb') as fh:
        with open(file_path + '.asm', 'w+') as oh:
            for i in range(int(file_size/2)):
                byte_list[0] = int.from_bytes(fh.read(1), 'big')
                byte_list[1] = int.from_bytes(fh.read(1), 'big')
                dis_inis = disassembler(byte_list)
                if not dis_inis.is_valid:
                    oh.write(dis_inis.hex_instruction + '\n')
                    continue
                if dis_inis.mnemonic_arg_types is None:
                    oh.write(dis_inis.mnemonic + '\n')
                    continue
                line = ""
                part = ""
                pos = 1
                for j in dis_inis.mnemonic_arg_types:
                    if j is 'register':
                        part = 'v'+dis_inis.hex_instruction[pos]
                    elif j is 'byte':
                        part = '#'+dis_inis.hex_instruction[2:]
                    elif j is 'address':
                        part = '#'+dis_inis.hex_instruction[1:]
                    elif j is 'nibble':
                        part = '#'+dis_inis.hex_instruction[3]
                    else:
                        part = j
                    part = part.ljust(5)
                    line += ',' + part
                    pos = 2
                oh.write(dis_inis.mnemonic.ljust(5) + line[:-1] + '\n')

def parse_args():
    parser = argparse.ArgumentParser(description='Does a thing')
    parser.add_argument('rom', nargs='?', help='file to disassemble.')
    opts = parser.parse_args()

    return opts

def main(opts):
    dissassemble_file(opts.rom)

if __name__ == '__main__':
    main(parse_args())
