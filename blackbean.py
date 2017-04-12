#!/usr/bin/python3

import os
import sys
import argparse

# Issues:
#   No support for "$" notation

# Line Properties:
#   isEmpty    - bool
#   original   - whole, unedited line
#   comment    - comment for the line
#   tag        - mem tag for the line
#   preProcess - Whole line, not used right now
#   address    - If asm or dd then address is populated
#   dataType   - 1,2,4
#       declarations - [list of data decl in orignal form]
#       ddhex  - [list of ints of size dataType]
#   instruction - "cls", "ret" etc
#       arguments - [list of args in original form]
#       hex - single int for machine code

#Opcode reminders: SHR, SHL, XOR, and SUBN/SM are NOT offically supported by original spec
#                  SHR and SHL may or may not move Y (Shifted) into X or just shift X.

HEX_ESC='#'
ARG_SUB={0:'x',1:'y',2:'z'}
PRE_PROC=('ifdef','else','endif','option','align','equ','=')
DATA_DECLARE={'db':1,'dw':2,'dd':4}
REGISTERS=( 'v0','v1','v2','v3',
            'v4','v5','v6','v7',
            'v8','v9','va','vb',
            'vc','vd','ve','vf')
OP_CODES={  'cls' :[{'args':[],'machine':'00E0'}],
            'ret' :[{'args':[],'machine':'00EE'}],
            'sys' :[{'args':['address'],'machine':'1xxx'}],
            'call':[{'args':['address'],'machine':'2xxx'}],
            'skp' :[{'args':['register'],'machine':'Ex9E'}],
            'sknp':[{'args':['register'],'machine':'ExA1'}],
            'se'  :[{'args':['register','register'],'machine':'5xy0'},
		            {'args':['register','byte'],'machine':'3xyy'}],
            'sne' :[{'args':['register','register'],'machine':'9xy0'},
		            {'args':['register','byte'],'machine':'4xyy'}],
            'add' :[{'args':['register','byte'],'machine':'7xyy'},
		            {'args':['register','register'],'machine':'8xy4'},
		            {'args':['i','register'],'machine':'Fx1E'}],
            'or'  :[{'args':['register','register'],'machine':'8xy1'}],
            'and' :[{'args':['register','register'],'machine':'8xy2'}],
            'xor' :[{'args':['register','register'],'machine':'8xy3'}],    #TODO not in orig spec.
            'sub' :[{'args':['register','register'],'machine':'8xy5'}],
            'subn':[{'args':['register','register'],'machine':'8xy7'}],    #TODO not in orig spec.
            'shr' :[{'args':['register','register'],'machine':'8xy6'}],    #TODO not in orig spec. 2nd reg is opt
            'shl' :[{'args':['register','register'],'machine':'8xyE'}],    #TODO not in orig spec. 2nd reg is opt
            'rnd' :[{'args':['register','byte'],'machine':'cxyy'}],
            'jp'  :[{'args':['address'],'machine':'1xxx'},
		            {'args':['v0','address'],'machine':'Byyy'}],           #TODO pretty sure this won't work cause v0
            'ld'  :[{'args':['register','byte'],'machine':'6xyy'},
		            {'args':['register','register'],'machine':'8xy0'},
		            {'args':['register','dt'],'machine':'Fx07'},
		            {'args':['register','k'],'machine':'Fx0A'},
		            {'args':['register','[i]'],'machine':'Fx65'},
		            {'args':['i','address'],'machine':'Ayyy'},
		            {'args':['dt','register'],'machine':'Fy15'},
		            {'args':['st','register'],'machine':'Fy18'},
		            {'args':['f','register'],'machine':'Fy29'},
		            {'args':['b','register'],'machine':'Fy33'},
		            {'args':['[i]','register'],'machine':'Fy55'}],
            'drw' :[{'args':['register','register','nibble'],'machine':'Dxyz'}]}

class blackbean:

    def __init__(self):
        self.collection=[]
        self.mmap={}
        self.address=0x0200

    def reset(self):
        __init__()

    def assemble(self, file_handler):
        # Pass One, Tokenize and Address
        for line in file_handler:
            t = self.tokenize(line)
            if t['isEmpty']: continue
            self.calc_mem_address(t)
            self.collection.append(t)

        # Pass Two, decode
        for t in self.collection:
            if t['isEmpty']: continue
            self.calc_opcode(t)
            self.calc_data_declares(t)

    def print_listing(self, file_handler):
        for line in self.collection:
            if line.get('hex'):
                form_line = format(line['address'], '#06x') + (4*' ') +\
                            format(line['hex'], '#06x') + (4*' ') +\
                            line['original']
            elif line.get('ddhex'):
                form_line = format(line['address'], '#06x') + (14*' ') +\
                            line['original']
            else:
                form_line = (' ' * 20) + line['original']
            if file_handler:
                file_handler.write(form_line)
            else:
                print(form_line, end='')

    def print_strip(self, file_handler):
        for line in self.collection:
            if line['isEmpty']: continue
            if file_handler:
                file_handler.write(line['original'].split(';')[0].rstrip() + '\n')
            else:
                print(line['original'].split(';')[0].rstrip(), end='')

    def export_binary(self, file_path):
        for line in self.collection:
            if line['isEmpty']: continue
            if line.get('hex'):
                file_path.write(line['hex'].to_bytes(2, byteorder='big'))
            elif line.get('ddhex'):
                for i in range(len(line['ddhex'])):
                    file_path.write(line['ddhex'][i].to_bytes(line['dataType'] , byteorder='big'))

    def calc_opcode(self, tokens):
        if not tokens.get('instruction'):
            return
        for VERSION in OP_CODES[tokens['instruction']]:
            issue = False
            if len(VERSION['args']) != len(tokens['arguments']):
                continue
            if len(VERSION['args']) == 0:
                tokens['hex'] = int(VERSION['machine'],16)
                break
            tmp = VERSION['machine']
            for i, ARG_TYPE in enumerate(VERSION['args']):
                cur_arg = tokens['arguments'][i]
                if ARG_TYPE == cur_arg:
                    continue
                elif ARG_TYPE is 'register':
                    if cur_arg in REGISTERS:
                        tmp = tmp.replace(ARG_SUB[i], cur_arg[1])
                    else: issue = True
                elif ARG_TYPE is 'address':
                    if cur_arg[0] is HEX_ESC:
                        cur_arg = cur_arg[1:]
                        if len(cur_arg) == 3:
                            tmp = tmp.replace(ARG_SUB[i] * 3, cur_arg)
                        else:
                            issue = True
                    elif cur_arg in self.mmap:
                        tmp = tmp.replace(ARG_SUB[i] * 3, hex(self.mmap[cur_arg])[2:])
                    else: issue = True
                elif ARG_TYPE is 'byte':
                    if cur_arg[0] is HEX_ESC:
                        cur_arg = cur_arg[1:]
                    else:
                        try:
                            cur_arg = hex(int(cur_arg)).zfill(2)[2:].zfill(2)
                        except: pass
                    if len(cur_arg) != 2:
                        issue = True
                    else:
                        try:
                            int(cur_arg, 16)
                            tmp = tmp.replace(ARG_SUB[i] * 2, cur_arg)
                        except:
                            issue = True
                elif ARG_TYPE is 'nibble':
                    if cur_arg[0] is HEX_ESC:
                        cur_arg = cur_arg[1:]
                    if len(cur_arg) != 1:
                        issue = True
                    else:
                        try:
                            int(cur_arg, 16)
                            tmp = tmp.replace(ARG_SUB[i], cur_arg)
                        except:
                            issue = True
                else:
                    issue = True
            if not issue:
                tokens['hex'] = int(tmp,16)
                break
        if not tokens.get('hex'):
            #TODO raise error
            print("ERROR: Unkown mnemonic-argument combination.")

    def calc_data_declares(self, tokens):
        if not tokens.get('declarations'):
            return
        ddhex = []
        for arg in tokens['declarations']:
            if arg[0] is HEX_ESC:
                arg = arg[1:]
                if len(arg) != (2 * tokens['dataType']):
                    #TODO raise error
                    print("ERROR: Data size of declare is incorrect.")
                #TODO wrap int parse in try
                val = int(arg,16)
            else:
                #TODO wrap int parse in try
                val = int(arg)
            if val >= pow(256,tokens['dataType']):
                #TODO raise error
                print("ERROR: Data declaration overflow.")
            ddhex.append(val)
        tokens['ddhex'] = ddhex

    def calc_mem_address(self, tokens):
        if tokens.get('tag'):
            self.mmap[tokens.get('tag')] = self.address
        if tokens.get('instruction'):
            tokens['address'] = self.address
            self.address += 2
        elif tokens.get('dataType'):
            tokens['address'] = self.address
            self.address += (len(tokens['declarations']) * tokens['dataType'])

    def tokenize(self,line):
        tokens = dict()
        tokens['original'] = line
        tokens['isEmpty'] = True
        line = line.lstrip()

        # Remove Blanks
        if line == '':
            return tokens

        # Remove Comment only lines
        if line.startswith(';'):
            tokens['comment'] = line.rstrip()
            return tokens

        tokens['isEmpty'] = False

        # Check for any comments
        tokens['comment'] = line.split(';')[1:]
        line = line.split(';')[0].rstrip()

        # Breakout into array
        line_array = list(filter(None, line.lower().split(' ')))

        # Check if tag exists, must be left most
        if line_array[0].endswith(':'):
            tokens['tag'] = line_array[0][:-1]
            line_array.pop(0)
            if not line_array:
                return tokens

        # If there are additional tags raise error
        if ':' in ''.join(line_array):
            #TODO raise error
            print("ERROR: Multiple Memory Tags found on same line.")

        # Check for any pre-processor commands
        for i in line_array:
            if i in PRE_PROC:
                tokens['preProcess'] = ' '.join(line_array)
                #TODO raise error
                print("ERROR: PreProcessor command found.")
                return tokens

        # Check for data declarations
        if line_array[0] in DATA_DECLARE:
            tokens['dataType'] = DATA_DECLARE[line_array[0]]
            line_array.pop(0)
            if not line_array:
                #TODO raise error
                print("ERROR: Expected data declaration.")
            tokens['declarations'] = ''.join(line_array).split(',')
            return tokens

        # Check for assembly instruction
        if line_array[0] in OP_CODES:
            tokens['instruction'] = line_array[0]
            line_array.pop(0)
            tokens['arguments'] = []
            if line_array:
                tokens['arguments'] = ''.join(line_array).split(',')
            return tokens

        # Trash
        print("ERROR: Unkown command.")
        return tokens

def util_strip_comments(file_path, outpout_handler=None):
    with open(file_path) as fhandler:
        for line in fhandler:
            if line.isspace(): continue
            if line.lstrip().startswith(';'): continue
            line = line.split(';')[0].rstrip()
            if outpout_handler==None:
                print(line)
            else:
                outpout_handler.write(line)

def util_add_listing(file_path, outpout_handler=None):
    mem_addr = 0x0200
    with open(file_path) as fhandler:
        for line in fhandler:
            mem_inc = 2
            nocomment = line.split(';')[0].rstrip().lower()
            if not nocomment or nocomment.endswith(':') or any(s in nocomment for s in PRE_PROC):
                line = (' ' * 10) + line
            else:
                for k in DATA_DEFINE.keys():
                    if k in nocomment:
                        mem_inc = DATA_DEFINE[k]
                        break
                line = format(mem_addr, '#06x') + '    ' + line
                mem_addr += mem_inc
            if outpout_handler==None:
                print(line, end='')
            else:
                outpout_handler.write(line, end='')

def parse_args():
    parser = argparse.ArgumentParser(description='Blackbean will assemble your CHIP-8 programs to executable machine code. BB can also generate listing files and comment-striped files. Options do not yet exist to toggle support off for the undocumented functions (Shifts, XOR, SUBN) or to disable/enable the undocumented L/R shift behavior.')
    parser.add_argument('input', help='file to assemble. Only used when invoked with "-i" flag.')
    parser.add_argument('-i','--input', help='file to assemble.')
    parser.add_argument('-o','--output',help='file to store binary executable to.')
    parser.add_argument('-l','--list',  help='generate listing file and store to OUTPUT.lst file.',action='store_true')
    parser.add_argument('-s','--strip', help='strip comments and store to OUTPUT.strip file.',action='store_true')
    parser.add_argument('-e','--enforce',help='Enforce original Chip-8 specification and do not allow SHR, SHL, XOR, or SUBN instructions.')
    opts = parser.parse_args()

    if not opts.input:
        raise "No file to assemble."
        sys.exit(1)
    if not os.path.isfile(opts.input):
        raise "No such file."
        sys.exit(1)
    if not opts.output:
        if opts.input.endswith('.src'):
            opts.output = opts.input[:-4]
        else:
            opts.output = opts.input

    return opts

def main(opts):
    bb = blackbean()
    with open(opts.input) as FH:
        bb.assemble(FH)
    if opts.list:
        with open(opts.output + '.lst', 'w') as FH:
            bb.print_listing(FH)
    if opts.strip:
        with open(opts.output + '.strip', 'w') as FH:
            bb.print_strip(FH)
    if opts.input == opts.output:
        with open(opts.output + '.bin', 'w') as FH:
            bb.export_binary(FH)
    else:
        with open(opts.output, 'wb') as FH:
            bb.export_binary(FH)

if __name__ == '__main__':
    main(parse_args())







