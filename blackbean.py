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
#
# Assumes:
#   Tags are at the start of the line
#   Pre proc commands don't share a line with asm

# Line Properties:
#   isEmpty    - bool
#   original   - whole, unedited line
#   comment    - comment for the line
#   tag        - mem tag for the line
#   preProcess - Whole line, not used right now
#   dataType   - 1,2,4
#       declarations - [list of data decl]
#   asm

#Opcode reminders: SHR, SHL, XOR, and SUBN/SM are NOT offically supported by original spec
#                  SHR and SHL may or may not move Y (Shifted) into X or just shift X.

HEX_ESC = '#'
PRE_PROC=('ifdef','else','endif','option','align','equ','=')
DATA_DECLARE={'db':1,'dw':2,'dd':4}
REGISTERS={ 'v0':0x0,'v1':0x1,'v2':0x2,'v3':0x3,   #Pretty sure we don't need this...
            'v4':0x4,'v5':0x5,'v6':0x6,'v7':0x7,
            'v8':0x8,'v9':0x9,'va':0xA,'vb':0xB,
            'vc':0xC,'vd':0xD,'ve':0xE,'vf':0xF}
OP_CODES={  'cls' :[{'args':0,'machine':'00E0'}],
            'ret' :[{'args':0,'machine':'00EE'}],
            'sys' :[{'args':1,'machine':'1xxx',1:'address'}],
            'call':[{'args':1,'machine':'1xxx',1:'address'}],
            'skp' :[{'args':1,'machine':'Ex9E',1:'register'}],
            'sknp':[{'args':1,'machine':'ExA1',1:'register'}],
            'se'  :[{'args':2,'machine':'5xy0',1:'register',2:'register'},
		            {'args':2,'machine':'3xyy',1:'register',2:'byte'}],
            'sne' :[{'args':2,'machine':'9xy0',1:'register',2:'register'},
		            {'args':2,'machine':'4xyy',1:'register',2:'byte'}],
            'add' :[{'args':2,'machine':'7xyy',1:'register',2:'byte'},
		            {'args':2,'machine':'8xy4',1:'register',2:'register'},
		            {'args':2,'machine':'Fx1E',1:'i',2:'register'}],
            'or'  :[{'args':2,'machine':'8xy1',1:'register',2:'register'}],
            'and' :[{'args':2,'machine':'8xy2',1:'register',2:'register'}],
            'xor' :[{'args':2,'machine':'8xy3',1:'register',2:'register'}],
            'sub' :[{'args':2,'machine':'8xy5',1:'register',2:'register'}],
            'subn':[{'args':2,'machine':'8xy7',1:'register',2:'register'}],
            'shr' :[{'args':2,'machine':'8xy6',1:'register',2:'register'}],
            'shl' :[{'args':2,'machine':'8xyE',1:'register',2:'register'}],
            'rnd' :[{'args':2,'machine':'cxyy',1:'register',2:'byte'}],
            'jp'  :[{'args':1,'machine':'1xxx',1:'address'}},
		            {'args':2,'machine':'Byyy',1:'v0',2:'address'}}],
            'ld'  :[{'args':2,'machine':'6xyy',1:'register',2:'byte'},
		            {'args':2,'machine':'8xy0',1:'register',2:'register'},
		            {'args':2,'machine':'Fx07',1:'register',2:'dt'},
		            {'args':2,'machine':'Fx0A',1:'register',2:'k'},
		            {'args':2,'machine':'Fx65',1:'register',2:'[i]'},
		            {'args':2,'machine':'Ayyy',1:'i',2:'address'},
		            {'args':2,'machine':'Fy15',1:'dt',2:'register'},
		            {'args':2,'machine':'Fy18',1:'st',2:'register'},
		            {'args':2,'machine':'Fy29',1:'f',2:'register'},
		            {'args':2,'machine':'Fy33',1:'b',2:'register'},
		            {'args':2,'machine':'Fy55',1:'[i]',2:'register'}],
            'drw' :[{'args':3,'machine':'Dxyz',1:'register',2:'register',3:'nibble'}]}

class blackbean:

    def __init__(self):
        self.collection=[]
        self.mmap={}
        self.address=0x0200

    def reset(self):
        __init__()

    def assemble(self, file_path):
        with open(file_path) as fhandler:
            for line in fhandler:
                current_tokens = self.tokenize(line)
                self.update_memory(current_tokens)
                #Xlate to machine
                self.collection.append(current_tokens)

    def print_listing(self):
        # TODO print opcodes aswell
        for line in self.collection:
            if line.get('address'):
                print(format(line['address'], '#06x') + '    ' + line['original'], end="")
            else:
                print((' ' * 10) + line['original'], end="")

    def export_binary(self, file_path):
        print("TODO")

    def update_memory(self, tokens):
        if tokens.get('isEmpty'):
            return
        if tokens.get('tag'):
            self.mmap[tokens.get('tag')] = self.address
        if tokens.get('asm'):
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
        if line is '':
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
        line_array = list(filter(None, line.split(' ')))

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
            if lex.lower() in PRE_PROC:
                tokens['preProcess'] = ' '.join(line_array)
                line_array.pop(i)
                #TODO continue to tokenize
                return tokens

        # Check for data declarations
        if line_array[0].lower() in DATA_DECLARE:
            tokens['dataType'] = DATA_DECLARE[line_array[0].lower()]
            line_array.pop(0)
            if not line_array:
                #TODO raise error
                print("ERROR: Expected data declaration.")
            ddargs = ''.join(line_array).split(',')
            dec = []
            for arg in ddargs:
                if arg[0] is HEX_ESC:
                    if len(arg) != (2 * tokens['dataType'])
                        #TODO raise error
                        print("ERROR: Data size of declare is incorrect.")
                    #TODO wrap int parse in try
                    val = int(arg[1:],16)
                else:
                    #TODO wrap int parse in try
                    val = int(arg)
                if val >= pow(256,tokens['dataType']):
                    #TODO raise error
                    print("ERROR: Data declaration overflow.")
                dec.append(val)
            tokens['declarations']=dec
            return tokens

        # Check for assembly instruction
        if line_array[0].lower() in OP_CODES:
            #TODO continue to tokenize
            tokens['asm'] = " ".join(line_array)
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
                outpout_handler.write(line, end='\n')

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
                outpout_handler.write(line)

def parse_args():
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('-i','--input', help='File to assemble', required=True)

def main(args):
    print("Nope")

if __name__ == '__main__':
    #util_add_listing(sys.argv[1])
    bb = blackbean()
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




