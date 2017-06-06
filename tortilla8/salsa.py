#!/usr/bin/env python3

import re
from collections import namedtuple
from .constants.opcodes import OP_REG, OP_ARGS, OP_CODES, UNOFFICIAL_OP_CODES

salsa_data = namedtuple('salsa_data', 'hex_instruction is_valid mnemonic\
    mnemonic_arg_types disassembled_line unoffical_op')

def salsa(byte_list):
    '''
    Salsa is a one line (2 byte) dissassembler function for CHIP-8 Rom It
    returns a named tuple with various information on the line.
    '''
    hex_instruction =  hex( byte_list[0] )[2:].zfill(2)
    hex_instruction += hex( byte_list[1] )[2:].zfill(2)
    is_valid = False
    mnemonic = None
    mnemonic_arg_types = None
    disassembled_line = ""
    unoffical_op = False

    # Match the instruction via a regex index
    for mnemonic, reg_patterns in OP_CODES.items():
        for pattern_version in reg_patterns:
            if not re.match(pattern_version[OP_REG], hex_instruction):
                continue
            mnemonic = mnemonic
            mnemonic_arg_types = pattern_version[OP_ARGS]
            is_valid = True
            break
        if is_valid:
            break

    # If not a valid instruction, assume data
    if not is_valid:
        disassembled_line = hex_instruction
        return salsa_data(hex_instruction, is_valid, mnemonic,
            mnemonic_arg_types, disassembled_line, unoffical_op)

    # If unoffical, flag it.
    if mnemonic in UNOFFICIAL_OP_CODES:
        unoffical_op = True

    # No args to parse
    if mnemonic_arg_types is None:
        disassembled_line = mnemonic
        return salsa_data(hex_instruction, is_valid, mnemonic,
            mnemonic_arg_types, disassembled_line, unoffical_op)

    # Parse Args
    tmp = ''
    reg_numb = 1
    for arg_type in mnemonic_arg_types:
        if arg_type is 'register':
            tmp = 'v'+hex_instruction[reg_numb]
        elif arg_type is 'byte':
            tmp = '#'+hex_instruction[2:]
        elif arg_type is 'address':
            tmp = '#'+hex_instruction[1:]
        elif arg_type is 'nibble':
            tmp = '#'+hex_instruction[3]
        else:
            tmp = arg_type
        disassembled_line += tmp.ljust(5) + ','
        reg_numb = 2

    disassembled_line = (mnemonic.ljust(5) + disassembled_line[:-1]).rstrip()
    return salsa_data(hex_instruction, is_valid, mnemonic,
        mnemonic_arg_types, disassembled_line, unoffical_op)

