#!/usr/bin/python3

import re
from opcode_constants import *

class disassembler:

    def __init__(self, byte_list):
        self.hex_instruction =  hex( byte_list[0] )[2:].zfill(2)
        self.hex_instruction += hex( byte_list[1] )[2:].zfill(2)
        self.mnemonic = None
        self.mnemonic_arg_types = None

        # Match the instruction via a regex index
        for reg_pattern in OP_REG:
            if re.match(reg_pattern.lower(), self.hex_instruction):
                self.mnemonic = OP_REG[reg_pattern][0]
                self.mnemonic_arg_types = OP_CODES[self.mnemonic][OP_REG[reg_pattern][1]][OP_ARGS]
                break
