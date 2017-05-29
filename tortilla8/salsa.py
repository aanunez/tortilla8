#!/usr/bin/python3

import re
from collections import namedtuple
from .constants.opcodes import OP_REG, OP_ARGS, OP_CODES, UNOFFICIAL_OP_CODES

def salsa(byte_list):
    '''
    Salsa is a one line (2 byte) dissassembler function for CHIP-8 Roms. It
    returns a named tuple with various information on the line.
    '''
    s = namedtuple('salsa_data', 'hex_instruction is_valid mnemonic\
        mnemonic_arg_types disassembled_line unoffical_op')
    s.hex_instruction =  hex( byte_list[0] )[2:].zfill(2)
    s.hex_instruction += hex( byte_list[1] )[2:].zfill(2)
    s.is_valid = False
    s.mnemonic = None
    s.mnemonic_arg_types = None
    s.disassembled_line = ""
    s.unoffical_op = False

    # Match the instruction via a regex index
    for mnemonic, reg_patterns in OP_CODES.items():
        for pattern_version in reg_patterns:
            if not re.match(pattern_version[OP_REG], s.hex_instruction): continue
            s.mnemonic = mnemonic
            s.mnemonic_arg_types = pattern_version[OP_ARGS]
            s.is_valid = True
            break
        if s.is_valid:
            break

    # If not a valid instruction, assume data
    if not s.is_valid:
        s.disassembled_line = s.hex_instruction
        return s

    # If unoffical, flag it.
    if s.mnemonic in UNOFFICIAL_OP_CODES:
        s.unoffical_op = True

    # No args to parse
    if s.mnemonic_arg_types is None:
        s.disassembled_line = s.mnemonic
        return s

    # Parse Args
    tmp = ''
    reg_numb = 1
    for arg_type in s.mnemonic_arg_types:
        if arg_type is 'register':
            tmp = 'v'+s.hex_instruction[reg_numb]
        elif arg_type is 'byte':
            tmp = '#'+s.hex_instruction[2:]
        elif arg_type is 'address':
            tmp = '#'+s.hex_instruction[1:]
        elif arg_type is 'nibble':
            tmp = '#'+s.hex_instruction[3]
        else:
            tmp = arg_type
        s.disassembled_line += tmp.ljust(5) + ','
        reg_numb = 2

    s.disassembled_line = (s.mnemonic.ljust(5) + s.disassembled_line[:-1]).rstrip()
    return s

