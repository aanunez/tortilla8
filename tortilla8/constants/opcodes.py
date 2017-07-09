#!/usr/bin/env python3

from collections import namedtuple

# OP CODES
OP_CODE_SIZE = 2
OpData = namedtuple('OpData', 'regular, args, hex')
OP_CODES = {                                 # X and Y in the right most indicates if it is for the 1st or 2nd arg
    'cls' : OpData('00e0',(),'00E0'),
    'ret' : OpData('00ee',(),'00EE'),
    'sys' : OpData('0(^0)..',('address'),'0xxx'), # prevent match to cls or ret
    'call': OpData('2...',('address'),'2xxx'),
    'skp' : OpData('e.9e',('register'),'Ex9E'),
    'sknp': OpData('e.a1',('register'),'ExA1'),
    'se'  :(OpData('5..0',('register','register'),'5xy0'),
            OpData('3...',('register','byte'),'3xyy')),
    'sne' :(OpData('9..0',('register','register'),'9xy0'),
            OpData('4...',('register','byte'),'4xyy')),
    'add' :(OpData('7...',('register','byte'),'7xyy'),
            OpData('8..4',('register','register'),'8xy4'),
            OpData('f.1e',('i','register'),'Fy1E')),
    'or'  : OpData('8..1',('register','register'),'8xy1'),
    'and' : OpData('8..2',('register','register'),'8xy2'),
    'xor' : OpData('8..3',('register','register'),'8xy3'),
    'sub' : OpData('8..5',('register','register'),'8xy5'),
    'subn': OpData('8..7',('register','register'),'8xy7'),
    'shr' :(OpData('8..6',('register'),'8x06'),
            OpData('    ',('register','register'),'8xy6')), # Blank regex, we never match, use shfit_mod instead
    'shl' :(OpData('8..e',('register'),'8x0E'),
            OpData('    ',('register','register'),'8xyE')), # as above
    'rnd' : OpData('c...',('register','byte'),'Cxyy'),
    'jp'  :(OpData('b...',('v0','address'),'Byyy'),
            OpData('1...',('address'),'1xxx')),
    'ld'  :(OpData('6...',('register','byte'),'6xyy'),
            OpData('8..0',('register','register'),'8xy0'),
            OpData('f.07',('register','dt'),'Fx07'),
            OpData('f.0a',('register','k'),'Fx0A'),
            OpData('f.65',('register','(i)'),'Fx65'),
            OpData('a...',('i','address'),'Ayyy'),
            OpData('f.15',('dt','register'),'Fy15'),
            OpData('f.18',('st','register'),'Fy18'),
            OpData('f.29',('f','register'),'Fy29'),
            OpData('f.33',('b','register'),'Fy33'),
            OpData('f.55',('(i)','register'),'Fy55')),
    'drw' : OpData('d...',('register','register','nibble'),'Dxyz')
    }

UNOFFICIAL_OP_CODES = ('xor','shr','shl','subn') # But still supported
BANNED_OP_CODES = ('7f..','8f.4','8f.6','8f.e','cf..','6f..','8f.0','ff07','ff0a','ff65') # Ins that modify VF: add, shr, shl, rnd, ld
#SUPER_CHIP_OP_CODES = ('00C.','00FB','00FC','00FD','00FE','00FF','D..0','F.30','F.75','F.85') # Super chip-8, not supported

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
#SUPER_CHIP_OP_CODES_EXPLODED = explode_op_codes(SUPER_CHIP_OP_CODES)



