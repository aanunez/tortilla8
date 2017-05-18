#!/usr/bin/python3

import os
import argparse
from tortilla8.salsa import salsa

def dissassemble_file(in_handler, out_handler):
    byte_list = []
    file_size = os.path.getsize(input_path)
    for _ in range(int(file_size/2)):
        byte_list[0:2] = [int.from_bytes(in_handler.read(1), 'big') for _ in range(2)]
        dis_inis = salsa(byte_list)
        out_handler.write(dis_inis.disassembled_line + '\n')
    if file_size % 2 == 1:
        out_handler.write(hex(int.from_bytes(in_handler.read(1), 'big'))[2:].zfill(2) + '\n')

parser = argparse.ArgumentParser(description=
'''
Dissassemble a Chip8 ROM, any byte pair that is not an instruction is assumed
to be a data declaration, regardless of it being referenced.
''')
parser.add_argument('rom', nargs='?', help='File to disassemble.')
parser.add_argument('-o','--output',help='File to write to.')
opts = parser.parse_args()

if opts.output is None:
    opts.output  = '.'.join(opts.rom.split('.')[0:-1]) if opts.rom.find('.') != -1 else opts.rom
    opts.output += '.asm'

with open(opts.rom, 'rb') as fi:
    with open(opts.output, 'w+') as fo:
        dissassemble_file(fi, fo)
