#!/usr/bin/python3

import sys
import argparse

# Features:
# Generate code only
# Generate memory addresses (list)
# assemble
#
# Input flags:
#
# -i, --input           [expects param after]
# -o, --output          [expects param after]
# -l, --list, --listing [expects param after]
# -s, --strip           *Need param? Better name?
#

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
#       declarations - [list of data decl]
#   instruction
#       arguments - [list of args]

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
            'call':[{'args':['address'],'machine':'1xxx'}],
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
            'xor' :[{'args':['register','register'],'machine':'8xy3'}],
            'sub' :[{'args':['register','register'],'machine':'8xy5'}],
            'subn':[{'args':['register','register'],'machine':'8xy7'}],
            'shr' :[{'args':['register','register'],'machine':'8xy6'}],
            'shl' :[{'args':['register','register'],'machine':'8xyE'}],
            'rnd' :[{'args':['register','byte'],'machine':'cxyy'}],
            'jp'  :[{'args':['address'],'machine':'1xxx'},
		            {'args':['v0','address'],'machine':'Byyy'}],           #TODO pretty sure this won't work
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
        for line in file_handler:
            t = self.tokenize(line)
            self.calc_mem_address(t)
            self.collection.append(t)
        for t in self.collection:
            self.calc_opcode(t)

    def print_listing(self):
        for line in self.collection:
            if line.get('hex'):
                print(format(line['address'], '#06x') + (4*' ') + format(line['hex'], '#06x') + (4*' ') + line['original'], end='')
            elif line.get('dataType'):
                #TODO print out data declares as word grouping
                print(format(line['address'], '#06x') + (14*' ') + line['original'], end='')
            else:
                print((' ' * 20) + line['original'], end="")

    def export_binary(self, file_path):
        print("TODO")

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

    def calc_mem_address(self, tokens):
        if tokens.get('isEmpty'):
            return
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
        #TODO Pre proc directives are not respected right now
        for i,lex in enumerate(line_array):
            if lex in PRE_PROC:
                tokens['preProcess'] = ' '.join(line_array)
                line_array.pop(i)
                #TODO continue to tokenize
                return tokens

        # Check for data declarations
        if line_array[0] in DATA_DECLARE:
            tokens['dataType'] = DATA_DECLARE[line_array[0]]
            line_array.pop(0)
            if not line_array:
                #TODO raise error
                print("ERROR: Expected data declaration.")
            ddargs = ''.join(line_array).split(',')
            dec = []
            for arg in ddargs:
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
                dec.append(val)
            tokens['declarations'] = dec
            return tokens

        # Check for assembly instruction
        if line_array[0] in OP_CODES:
            tokens['instruction'] = line_array[0]
            line_array.pop(0)
            tokens['arguments'] = list(filter(None,''.join(line_array).split(',')))
            return tokens

        # Trash
        print("ERROR: Unkown command ")
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
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('-i','--input', help='File to assemble', required=True)

def main(args):
    print("Nope")

if __name__ == '__main__':
    #util_add_listing(sys.argv[1])
    bb = blackbean()
    with open(sys.argv[1]) as FH:
        bb.assemble(sys.argv[1])
    bb.print_listing()
    sys.exit(0)
    with open(sys.argv[1]) as FH:
        for line in FH:
            token = tokenize(line)
            if not token["isEmpty"]:
                if "asm" in token: print(token["asm"])
                if "tag" in token: print(token["tag"])
        #util_add_listing(FH)
    #main(parse_args())



