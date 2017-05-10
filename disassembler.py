#!/usr/bin/python3

import re
from constants.opcodes import OP_REG, OP_ARGS, OP_CODES

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
