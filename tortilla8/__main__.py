#!/usr/bin/env python3

import os
import select
import contextlib
from time import sleep
from sys import platform, argv
from argparse import ArgumentParser, ArgumentTypeError
from .jalapeno import Jalapeno
from .blackbean import Blackbean
from .salsa import Salsa
from .guacamole import Guacamole
from .platter import Platter

def pos_int(value):
    ivalue = int(value)
    if ivalue < 1:
         raise ArgumentTypeError("%s is an invalid positive int value." % value)
    return ivalue

def dissassemble_file(in_handler, out_handler):
    byte_list = []
    file_size = os.path.getsize(input_path)
    for _ in range(int(file_size/2)):
        byte_list[0:2] = [int.from_bytes(in_handler.read(1), 'big') for _ in range(2)]
        dis_inis = Salsa(byte_list)
        out_handler.write(dis_inis.disassembled_line + '\n')
    if file_size % 2 == 1:
        out_handler.write(hex(int.from_bytes(in_handler.read(1), 'big'))[2:].zfill(2) + '\n')

def parse_args():
    parser = ArgumentParser(description=
        '''
        A collection of Chip8 tools for pre-processing, assembling,
        emulating, disassembling, and visualizing Chip8 ROMs.
        ''')
    subparsers = parser.add_subparsers(dest='option', help=
        'Options for tortilla8...')

    pp_parser = subparsers.add_parser('pre-process',help=
        '''
        Scan your CHIP-8 source code for pre-processor directives, apply them as
        needed, and produce a flattend source file. Respected Directives are:
        'ifdef', 'ifndef', 'elif', 'elseif', 'elifdef','elseifdef', 'endif',
        'else', 'equ', '='. Currently, no mode modifers ('option', 'align' etc)
        are respected.
        ''')
    pp_parser.add_argument('input', help=
        'File to assemble.')
    pp_parser.add_argument('-d','--define',nargs='+',help=
        'Strings to define as true for evaluation of pre-processor directives.')
    pp_parser.add_argument('-o','--output',help=
        'File to store processed source to, by default INPUT_pp.asm is used.')

    asm_parser = subparsers.add_parser('assemble', help=
        '''
        Assemble your CHIP-8 programs to executable machine code. Listing files and
        comment-striped files can also be generated. Arguments to mnemonics must be
        either be integers in decimal or hex using '#' as a prefix. Data declares may
        also be prefixed with '$' to denote binary (i.e. '$11001100' or '$11..11..').
        ''')
    asm_parser.add_argument('input', nargs='?', help=
        'File to assemble.')
    asm_parser.add_argument('-o','--output',help=
        'Name of every generated file, will have either "strip", "lst", or "ch8" appended.')
    asm_parser.add_argument('-l','--list',  help=
        'Generate listing file and store to OUTPUT.lst file.',action='store_true')
    asm_parser.add_argument('-s','--strip', help=
        'Strip comments and store to OUTPUT.strip file.',action='store_true')
    asm_parser.add_argument('-e','--enforce',action='store_true',help=
        'Force original Chip-8 specification and do not allow SHR, SHL, XOR, or SUBN instructions.')

    dis_parser = subparsers.add_parser('disassemble', help=
        '''
        Dissassemble a Chip8 ROM, any byte pair that is not an instruction is assumed
        to be a data declaration. No checks are performed to insure the program is
        valid.
        ''')
    dis_parser.add_argument('rom', nargs='?', help=
        'File to disassemble.')
    dis_parser.add_argument('-o','--output',help=
        'File to write to.')

    ex_parser = subparsers.add_parser('execute', help=
        '''
        Execute a rom to quickly check for errors. The program counter, hex instruction (the two
        bytes that make up the opcode), and mnemonic are printed to the screen immediately after
        the execution of that operation code. All errors (info, warning, and fatal) are printed
        to screen.
        ''')
    ex_parser.add_argument('rom', help='ROM to load and play.')
    ex_parser.add_argument("-f","--frequency",   type=pos_int, default=5,  help=
        'Frequency (in Hz) to target for CPU.')
    ex_parser.add_argument("-st","--soundtimer", type=pos_int, default=60, help=
        'Frequency (in Hz) to target for the audio timmer.')
    ex_parser.add_argument("-dt","--delaytimer", type=pos_int, default=60, help=
        'Frequency (in Hz) to target for the delay timmer.')
    ex_parser.add_argument('-i','--initram', help=
        'Initialize RAM to all zero values.', action='store_true')
    ex_parser.add_argument('-ls','--legacy_shift', help=
        'Use the legacy shift method of bit shift Y and storing to X.', action='store_true')
    ex_parser.add_argument("-e","--enforce_instructions", default='None', help=
        'Warning to log if an unoffical instruction is executed. Options: None Info Warning Fatal')

    emu_parser = subparsers.add_parser('emulate', help=
        '''
        Start a text (unicode) based Chip8 emulator which disaplys a game screen, all
        registers, the stack, recently processed instructions, and a console to log
        any issues that occur.
        ''')
    emu_parser.add_argument('rom', help=
        'ROM to load and play.')
    group = emu_parser.add_mutually_exclusive_group()
    group.add_argument('-f','--frequency', type=pos_int, default=10,help=
        'CPU frequency to target, minimum 1Hz. 10Hz by default.CPU frequency can be adjusted in platter.')
    group.add_argument('-s','--step', action='store_true', help=
        'Start the emulator in "step" mode. Allows for execution of a single instruction at a time.')
    emu_parser.add_argument('-d','--drawfix', action='store_true', help=
        'Enable anti-flicker, stops platter from drawing to the screen when sprites are only removed.', )
    emu_parser.add_argument('-i','--initram', action='store_true', help=
        'Initialize RAM to all zero values. Needed to run some ROMs that assume untouched addresses to be zero. By default RAM address without values are not initalized, accessing them will cause an Emulation Error.')
    emu_parser.add_argument('-a','--audio', help=
        'Path to audio to play for Sound Timer, or "off" to prevent sound from playing.' + \
        'By default a 440Hz square wave is used.')
    emu_parser.add_argument("-st","--soundtimer", type=pos_int, default=60, help=
        'Frequency to target for the audio timmer. 60Hz by default.')
    emu_parser.add_argument("-dt","--delaytimer", type=pos_int, default=60, help=
        'Frequency to target for the delay timmer. 60Hz by default.')
    emu_parser.add_argument('-ls','--legacy_shift', action='store_true', help=
        'Use the legacy shift method of bit shift Y and storing to X. ' +\
        'By default the newer method is used where Y is ignored and X is bitshifted then stored to itself.')
    emu_parser.add_argument("-e","--enforce_instructions", default='None', help=
        'Warning to log if an unoffical instruction is executed. ' +\
        'By default, no errors are logged. Options: None Info Warning Fatal')
    emu_parser.add_argument("-r","--rewind_depth", type=pos_int, default=1000, help=
        'Number of instructions back to be recorded to enable rewinding. ' +\
        'To disable set to zero or "off". By default 1000 instructions are recorded.')
    emu_parser.add_argument("-u","--unicode", nargs='*', help=
        'Forces unicode on or off for the menu and game screen. ' +\
        'Valid values are: On, Off, Menu-On, Menu-Off, Game-On, Game-Off. ' +\
        'By default, unicode support is determined by the OS. ' +\
        'Mac displays a unicode game screen, Windows displays no unicode, ' +\
        'and GNU/Linux displays both the game and menu in unicode.')

    return parser.parse_args()

def main():
    if len(argv) == 1:
        argv.append('-h')
    opts = parse_args()

    if opts.option == 'pre-process':
        if not os.path.isfile(opts.input):
            raise OSError("File '" + opts.input + "' does not exist.")

        if not opts.output:
            opts.output  = '.'.join(opts.input.split('.')[0:-1]) if opts.input.find('.') != -1 else opts.input
            opts.output += '_pp.asm'

        with open(opts.input) as fh:
            pp = Jalapeno(fh, opts.define)

        with open(opts.output, 'w+') as fh:
            pp.print_processed_source(fh)

    if opts.option == 'assemble':
        if not os.path.isfile(opts.input):
            raise OSError("File '" + opts.input + "' does not exist.")

        if not opts.output:
            opts.output  = '.'.join(opts.input.split('.')[0:-1]) if opts.input.find('.') != -1 else opts.input

        bb = Blackbean()
        with open(opts.input) as fh:
            bb.assemble(fh)

        if opts.list:
            with open(opts.output + '.lst', 'w') as fh:
                bb.print_listing(fh)

        if opts.strip:
            with open(opts.output + '.strip', 'w') as fh:
                bb.print_strip(fh)

        with open(opts.output + '.ch8', 'wb') as fh:
            bb.export_binary(fh)

    if opts.option == 'disassemble':
        if opts.output is None:
            opts.output  = '.'.join(opts.rom.split('.')[0:-1]) if opts.rom.find('.') != -1 else opts.rom
            opts.output += '.asm'

        with open(opts.rom, 'rb') as fi:
            with open(opts.output, 'w+') as fo:
                dissassemble_file(fi, fo)

    if opts.option == 'execute':
        if not os.path.isfile(opts.rom):
            raise OSError("File '" + opts.rom + "' does not exist.")

        guac = Guacamole(opts.rom, opts.frequency, opts.soundtimer, opts.delaytimer,
                         opts.initram, opts.legacy_shift, opts.enforce_instructions)
        guac.log_to_screen = True
        sleep_time = (1/opts.frequency)*.98
        try:
            while True:
                guac.run()
                sleep(sleep_time)

        except KeyboardInterrupt:
            pass

    if opts.option == 'emulate':
        if not os.path.isfile(opts.rom):
            raise OSError("File '" + opts.rom + "' does not exist")

        if opts.step:
            opts.frequency = 1000000 # 1 Ghz

        screen_unicode = False if platform == 'win32' else True
        menu_unicode   = True  if platform == 'linux' else False
        if opts.unicode:
            if len(opts.unicode) > 2:
                raise IOError("Too many values following the '--unicode' flag.")
            for val in opts.unicode:
                val = val.lower().split('-')
                if   val[0] == 'menu' and val[1]== 'on':
                    menu_unicode = True
                elif val[0] == 'menu' and val[1]== 'off':
                    menu_unicode = False
                elif val[0] == 'game' and val[1]== 'on':
                    game_unicode = True
                elif val[0] == 'game' and val[1]== 'off':
                    game_unicode = False
                else:
                    raise IOError("Unknown value following the '--unicode' flag.")

        disp = Platter( opts.rom, opts.frequency, opts.soundtimer, opts.delaytimer,
                        opts.initram, opts.legacy_shift, opts.enforce_instructions,
                        opts.rewind_depth, opts.drawfix, screen_unicode, menu_unicode,
                        opts.audio )
        disp.start(opts.step)

if __name__ == "__main__":
    main()
