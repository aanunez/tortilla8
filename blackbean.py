#!/usr/bin/python3

import os
import sys
import select
import warning
import argparse
import contextlib

from cilantro import cilantro
from mem_addr_register_constants import *
from pre_proc_assembler_constants import *
from opcode_constants import *

#Opcode reminders: SHR, SHL, XOR, and SUBN/SM are NOT offically supported by original spec
#                  SHR and SHL may or may not move Y (Shifted) into X or just shift X.

#TODO don't allow modifying VF
#TODO Use the "enfore" flag
#TODO support for $ notation

class blackbean:
    """
    Blackbean is an assembler class that can take file handlers,
    assemble the contents, and return a stripped (comment free),
    listing, or binary file.
    """

    def __init__(self, token_collection=None):
        """
        Init the token collection and memory map. Pre-Processor may
        have already done the hard bit for us. Memory addresses
        start at 0x200 on the CHIP 8.
        """
        if token_collection is None:
            self.collection = []
        else:
            self.collection = token_collection
        self.mmap       = {}
        self.address    = PROGRAM_BEGIN_ADDRESS

    def reset(self, token_collection=None):
        """
        Reset the blackbean to assemble another file.
        """
        self.__init__(token_collection)

    def assemble(self, file_handler):
        """
        Assemble a file. Tokenizes, calculates memory addreses, and
        translates mnemonic instructions into hex.
        """
        # Pass One, Tokenize and Address
        for i,line in enumerate(file_handler):
            t = cilantro(line, i)
            self.collection.append(t)
            if t.is_empty: continue
            self.calc_mem_address(t)

        # Pass Two, decode mnemonics
        for t in self.collection:
            if t.is_empty: continue
            self.calc_opcode(t)
            self.calc_data_declares(t)

    def print_listing(self, file_handler=None):
        """
        Prints a the orignal file with two additonal column, the first
        being the memory address of the first byte of the line and the
        second being the calculated hex value for the mnemonic on the
        line. Data declarations do not have their calculated hex
        values shown as they may take more than the normal two bytes
        for all other assembler instructions.
        """
        if not self.collection:
            warnings.warn("No file has been assembled. Nothing to print.")
            return

        for line in self.collection:
            if line.instruction_int:
                form_line = format(line.mem_address, '#06x') + (4*' ') +\
                            format(line.instruction_int, '#06x') + (4*' ') +\
                            line.original
            elif line.dd_ints:
                form_line = format(line.mem_address, '#06x') + (14*' ') +\
                            line.original
            else:
                form_line = (20*' ') + line.original

            if file_handler is None:
                print(form_line, end='')
            else:
                file_handler.write(form_line)

    def print_strip(self, file_handler=None):
        """
        Prints a copy of the input file with all comments and white
        space lines removed. Useful for CHIP 8 interpreters.
        """
        if not self.collection:
            warnings.warn("No file has been assembled. Nothing to print.")
            return

        for line in self.collection:
            if line.is_empty:
                continue
            if file_handler is None:
                print(line.original.split(BEGIN_COMMENT)[0].rstrip(), end='')
            else:
                file_handler.write(line.original.split(BEGIN_COMMENT)[0].rstrip() + '\n')

    def export_binary(self, file_path):
        """
        Writes the assembled file to a binary blob.
        """
        if not self.collection:
            warnings.warn("No file has been assembled. Nothing to print.")
            return

        for line in self.collection:
            if line.is_empty:
                continue
            if line.instruction_int:
                file_path.write(line.instruction_int.to_bytes(OP_CODE_SIZE, byteorder='big'))
            elif line.dd_ints:
                for i in range(len(line.dd_ints)):
                    file_path.write(line.dd_ints[i].to_bytes(line.data_size , byteorder='big'))

    def calc_opcode(self, tl):
        """
        Resolve mnemonics into hex string then to ints.These
        can be easily written out. All instructions are 2 bytes.
        """
        # Skip empty lines
        if not tl.instruction:
            return

        for VERSION in OP_CODES[tl.instruction]:
            issue = False

            # Skips versions of the OPCODE that can't work
            if len(VERSION[OP_ARGS]) != len(tl.arguments):
                continue

            # Easy matches
            if len(VERSION[OP_ARGS]) == 0:
                tl.instruction_int = int(VERSION[OP_HEX], 16)
                break

            # Validate every argument provided to the instruction
            working_hex = VERSION[OP_HEX]
            for i, ARG_TYPE in enumerate(VERSION[OP_ARGS]):
                working_hex = self.is_valid_instruction_arg(ARG_TYPE, tl.arguments[i], working_hex, ARG_SUB[i])
                if not working_hex:
                    break
            if working_hex:
                tl.instruction_int = int(working_hex, 16)
                break

        if not tl.instruction_int:
            raise RuntimeError("Unkown mnemonic-argument combination on line " + str(tl.line_numb) + "\n" + tl.original )

    def is_valid_instruction_arg(self, arg_type, arg_value, hex_template, sub_string):
        """
        Validates an instruction's arg_value to insure it meets the parameters
        of arg_type. If so, hex_template is returned with sub_string correctly
        updated.
        """
        if arg_type == arg_value:
            return hex_template

        if arg_type is 'register':
            if arg_value in REGISTERS:
                return hex_template.replace(sub_string, arg_value[1])

        elif arg_type is 'address':
            if arg_value[0] is HEX_ESC:
                arg_value = arg_value[1:]
                if len(arg_value) == 3:
                    try:
                        int(arg_value, 16)
                        return hex_template.replace(sub_string * 3, arg_value)
                    except: pass
            elif arg_value in self.mmap:
                if self.mmap.get(arg_value):
                    return hex_template.replace(sub_string * 3, hex(self.mmap[arg_value])[2:])

        elif arg_type is 'byte':
            if arg_value[0] is HEX_ESC:
                arg_value = arg_value[1:]
            else:
                try:
                    arg_value = hex(int(arg_value))[2:].zfill(2)
                except: pass
            if len(arg_value) == 2:
                try:
                    int(arg_value, 16)
                    return hex_template.replace(sub_string * 2, arg_value)
                except: pass

        elif arg_type is 'nibble':
            if arg_value[0] is HEX_ESC:
                arg_value = arg_value[1:]
            if len(arg_value) == 1:
                try:
                    int(arg_value, 16)
                    return hex_template.replace(sub_string, arg_value)
                except: pass

        return ''

    def calc_data_declares(self, tl):
        """
        Resolve a data declarations into list of ints. These can
        be easily written out. Size (# of bytes) was found when
        tokenizing the line.
        """
        # Skip lines w/o dd
        if not tl.data_declarations:
            return

        for arg in tl.data_declarations:
            val = None

            # Try to parse the values
            if arg[0] is HEX_ESC:
                arg = arg[1:]
                if len(arg) == (2 * tl.data_size):
                    try: val = int(arg, 16)
                    except: pass
            elif arg.isdigit():
                val = int(arg)

            # Raise errors if parse failed or val too large
            if val == None:
                raise RuntimeError("Incorrectly formated data declaration on line " + str(tl.line_numb))
            if val >= pow(256, tl.data_size):
                raise RuntimeError("Data declaration overflow on line " + str(tl.line_numb))

            tl.dd_ints.append(val)

    def calc_mem_address(self, tl):
        """
        Assign memory addresses to mnemonics (now packed in tokenized
        lines). Store any memory tags found in the memory map to be
        used on the second pass.
        """
        # Add any tags to the mem map
        if tl.mem_tag:
            self.mmap[tl.mem_tag] = self.address

        # One or the other per line, if both then errors are raised
        if tl.instruction:
            tl.mem_address = self.address
            self.address += OP_CODE_SIZE
        elif tl.data_size:
            tl.mem_address = self.address
            self.address += (len(tl.data_declarations) * tl.data_size)

        if self.address >= OVERFLOW_ADDRESS:
            warnings.warn("Memory overflow as of line " + str(tl.line_numb))

def parse_args():
    """
    Parse arguments to blackbean when called as a script.
    """
    parser = argparse.ArgumentParser(description='Blackbean will assemble your CHIP-8 programs to executable machine code. BB can also generate listing files and comment-striped files. The "enforce" option is not currently supported.')
    parser.add_argument('input', nargs='?', help='file to assemble.')
    parser.add_argument('-o','--output',help='file to store binary executable to, by default INPUT.bin is used.')
    parser.add_argument('-l','--list',  help='generate listing file and store to OUTPUT.lst file.',action='store_true')
    parser.add_argument('-s','--strip', help='strip comments and store to OUTPUT.strip file.',action='store_true')
    parser.add_argument('-e','--enforce',help='force original Chip-8 specification and do not allow SHR, SHL, XOR, or SUBN instructions.',action='store_true')
    opts = parser.parse_args()

    force_out = True

    if not opts.input:
        if select.select([sys.stdin,],[],[],0.0)[0]:
            opts.input = sys.stdin
            if not opts.output:
                opts.output = sys.stdout
        else:
            raise OSError("No input provided.")
    elif not os.path.isfile(opts.input):
        raise OSError("File '" + opts.input + "' does not exist.")

    if not opts.output:
        opts.output  = '.'.join(opts.input.split('.')[0:-1]) if opts.input.find('.') else opts.input
        force_out = False

    return opts, force_out

@contextlib.contextmanager
def smart_open(filename = None, mode = 'r'):
    """
    Open file OR use stdin. This is used to support piping.
    """
    if filename and filename != '-':
        fh = open(filename, mode)
    else:
        fh = sys.stdin
    try:
        yield fh
    finally:
        if fh is not sys.stdin:
            fh.close()

def main(opts, force_out):
    """
    Handles blackbean being called as a script.
    """
    bb = blackbean()
    with smart_open(opts.input) as FH:
        bb.assemble(FH)
    if opts.list:
        with open(opts.output + '.lst', 'w') as FH:
            bb.print_listing(FH)
    if opts.strip:
        with open(opts.output + '.strip', 'w') as FH:
            bb.print_strip(FH)
    if not force_out:
        opts.output += '.ch8'
    with open(opts.output, 'wb') as FH:
        bb.export_binary(FH)

if __name__ == '__main__':
    main(*parse_args())


############################################################
# Below are utility functions usefull if creating a class
# is over shooting your needs.

def util_strip_comments(file_path, outpout_handler = None):
    with open(file_path) as fhandler:
        for line in fhandler:
            if line.isspace(): continue
            if line.lstrip().startswith(BEGIN_COMMENT): continue
            line = line.split(BEGIN_COMMENT)[0].rstrip()
            if outpout_handler == None:
                print(line)
            else:
                outpout_handler.write(line)

def util_add_listing(file_path, outpout_handler = None):
    mem_addr = 0x0200
    with open(file_path) as fhandler:
        for line in fhandler:
            mem_inc = 2
            nocomment = line.split(BEGIN_COMMENT)[0].rstrip().lower()
            if not nocomment or nocomment.endswith(':') or any(s in nocomment for s in PRE_PROC):
                line = (10*' ') + line
            else:
                for k in DATA_DEFINE:
                    if k in nocomment:
                        mem_inc = DATA_DEFINE[k]
                        break
                line = format(mem_addr, '#06x') + (4*' ') + line
                mem_addr += mem_inc
            if outpout_handler == None:
                print(line, end='')
            else:
                outpout_handler.write(line, end='')




