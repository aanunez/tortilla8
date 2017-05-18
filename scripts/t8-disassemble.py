#!/usr/bin/python3

import os
import argparse
from tortilla8.salsa import salsa

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
        opts.output  = '.'.join(opts.rom.split('.')[0:-1]) if opts.rom.find('.') != -1 else opts.rom
        opts.output += '.asm'

    return opts

def main(opts):
    file_in  = open(opts.rom, 'rb')
    file_out = open(opts.output, 'w+')
    dissassemble_file(file_in, file_out)
    file_in.close()
    file_out.close()

main(parse_args())
