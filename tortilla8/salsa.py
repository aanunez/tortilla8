#!/usr/bin/python3

import re
from .constants.opcodes import OP_REG, OP_ARGS, OP_CODES, UNOFFICIAL_OP_CODES

#TODO Remove class, should just be a function that returns a tuple/dict

class salsa:
    '''
    '''

    def __init__(self, byte_list):
        '''
        '''

        self.hex_instruction =  hex( byte_list[0] )[2:].zfill(2)
        self.hex_instruction += hex( byte_list[1] )[2:].zfill(2)
        self.is_valid = False
        self.mnemonic = None
        self.mnemonic_arg_types = None
        self.disassembled_line = ""
        self.unoffical_op = False

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
            self.disassembled_line = self.hex_instruction
            return

        # If unoffical, flag it.
        if self.mnemonic in UNOFFICIAL_OP_CODES:
            self.unoffical_op = True

        # No args to parse
        if self.mnemonic_arg_types is None:
            self.disassembled_line = self.mnemonic
            return

        # Parse Args
        tmp = ''
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

