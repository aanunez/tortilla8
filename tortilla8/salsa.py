#!/usr/bin/env python3

from . import export
from re import match
from collections import namedtuple
from .constants.opcodes import OP_CODES, UNOFFICIAL_OP_CODES, \
                               BANNED_OP_CODES_EXPLODED, SUPER_CHIP_OP_CODES_EXPLODED
__all__ = []

@export
class ASMdata( namedtuple('ASMdata', 'hex_instruction is_valid mnemonic\
    mnemonic_arg_types disassembled_line unoffical_op is_banned is_super8') ):
    pass

class EarlyExit(Exception):
    pass

@export
def Salsa(byte_list):
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
    is_banned = False
    is_super8 = False

    try:
        # Check if the Op-Code a Super-8 instruction
        if hex_instruction in SUPER_CHIP_OP_CODES_EXPLODED:
            mnemonic = 'SPR'
            is_super8 = True
            raise EarlyExit

        # Match the instruction via a regex index
        for mnemonic, reg_patterns in OP_CODES.items():

            if type(reg_patterns) is not tuple:
                reg_patterns = (reg_patterns,)
            for pattern_version in reg_patterns:
                if not match(pattern_version.regular, hex_instruction):
                    continue
                mnemonic = mnemonic
                mnemonic_arg_types = pattern_version.args
                is_valid = True
                break
            if is_valid:
                break

        # If not a valid instruction, assume data
        if not is_valid:
            disassembled_line = hex_instruction
            raise EarlyExit

        # If banned, flag and exit.
        if hex_instruction in BANNED_OP_CODES_EXPLODED:
            is_banned = True
            raise EarlyExit

        # If unoffical, flag it.
        if mnemonic in UNOFFICIAL_OP_CODES:
            unoffical_op = True

        # No args to parse
        if mnemonic_arg_types is None:
            disassembled_line = mnemonic
            raise EarlyExit

        # Parse Args
        tmp = ''
        reg_numb = 1
        for arg_type in mnemonic_arg_types:
            if arg_type is 'reg':
                tmp = 'v'+hex_instruction[reg_numb]
            elif arg_type is 'byte':
                tmp = '#'+hex_instruction[2:]
            elif arg_type is 'addr':
                tmp = '#'+hex_instruction[1:]
            elif arg_type is 'nibble':
                tmp = '#'+hex_instruction[3]
            else:
                tmp = arg_type
            disassembled_line += tmp.ljust(5) + ','
            reg_numb = 2

        disassembled_line = (mnemonic.ljust(5) + disassembled_line[:-1]).rstrip()
    except EarlyExit:
        pass
    finally:
        return ASMdata(hex_instruction, is_valid, mnemonic,
            mnemonic_arg_types, disassembled_line, unoffical_op,
            is_banned, is_super8)

