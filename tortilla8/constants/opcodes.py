#!/usr/bin/env python3

from collections import namedtuple

# OP CODES
OP_CODE_SIZE = 2
OpData = namedtuple('OpData', 'regular, args, hex')
OP_CODES = {                                 # X and Y in the right most indicates if it is for the 1st or 2nd arg
    'cls' : OpData('00e0',[],'00E0'),
    'ret' : OpData('00ee',[],'00EE'),
    'sys' : OpData('0(^0)..',['addr'],'0xxx'), # prevent match to cls or ret
    'call': OpData('2...',['addr'],'2xxx'),
    'skp' : OpData('e.9e',['reg'],'Ex9E'),
    'sknp': OpData('e.a1',['reg'],'ExA1'),
    'se'  :(OpData('5..0',['reg','reg'],'5xy0'),
            OpData('3...',['reg','byte'],'3xyy')),
    'sne' :(OpData('9..0',['reg','reg'],'9xy0'),
            OpData('4...',['reg','byte'],'4xyy')),
    'add' :(OpData('7...',['reg','byte'],'7xyy'),
            OpData('8..4',['reg','reg'],'8xy4'),
            OpData('f.1e',['i','reg'],'Fy1E')),
    'or'  : OpData('8..1',['reg','reg'],'8xy1'),
    'and' : OpData('8..2',['reg','reg'],'8xy2'),
    'xor' : OpData('8..3',['reg','reg'],'8xy3'),
    'sub' : OpData('8..5',['reg','reg'],'8xy5'),
    'subn': OpData('8..7',['reg','reg'],'8xy7'),
    'shr' :(OpData('8..6',['reg'],'8x06'),
            OpData('    ',['reg','reg'],'8xy6')), # Blank regex, we never match, use shfit_mod instead
    'shl' :(OpData('8..e',['reg'],'8x0E'),
            OpData('    ',['reg','reg'],'8xyE')), # as above
    'rnd' : OpData('c...',['reg','byte'],'Cxyy'),
    'jp'  :(OpData('b...',['v0','addr'],'Byyy'),
            OpData('1...',['addr'],'1xxx')),
    'ld'  :(OpData('6...',['reg','byte'],'6xyy'),
            OpData('8..0',['reg','reg'],'8xy0'),
            OpData('f.07',['reg','dt'],'Fx07'),
            OpData('f.0a',['reg','k'],'Fx0A'),
            OpData('f.65',['reg','[i]'],'Fx65'),
            OpData('a...',['i','addr'],'Ayyy'),
            OpData('f.15',['dt','reg'],'Fy15'),
            OpData('f.18',['st','reg'],'Fy18'),
            OpData('f.29',['f','reg'],'Fy29'),
            OpData('f.33',['b','reg'],'Fy33'),
            OpData('f.55',['[i]','reg'],'Fy55')),
    'drw' : OpData('d...',['reg','reg','nibble'],'Dxyz')
    }

UNOFFICIAL_OP_CODES = ('xor','shr','shl','subn') # But still supported
BANNED_OP_CODES = ('7f..','8f.4','8f.6','8f.e','cf..','6f..','8f.0','ff07','ff0a','ff65') # Ins that modify VF: add, shr, shl, rnd, ld
SUPER_CHIP_OP_CODES = ('00c.','00fb','00fc','00fd','00fe','00ff','d..0','f.30','f.75','f.85') # Super chip-8, not supported

# Used to explode opcodes that are not used (below)
def explode_op_codes( op_code_list ):
    exploded_list = []
    for item in op_code_list:
        if item.find('.') == -1:
            exploded_list.append(item)
        else:
            upper,repl,fill = 16,'.',1
            if item[2:] == '..':
                upper,repl,fill = 256,'..',2
            for i in range(0, upper):
                exploded_list.append(item.replace(repl, hex(i)[2:].zfill(fill)))
    return exploded_list

BANNED_OP_CODES_EXPLODED = explode_op_codes(BANNED_OP_CODES)
SUPER_CHIP_OP_CODES_EXPLODED = explode_op_codes(SUPER_CHIP_OP_CODES)



