#!/usr/bin/env python3

# OP CODES
OP_REG  = 0
OP_ARGS = 1
OP_HEX  = 2
OP_CODE_SIZE = 2
OP_CODES = {
    'cls' :[['00e0',[],'00E0']],
    'ret' :[['00ee',[],'00EE']],
    'sys' :[['0[^0]..',['address'],'0xxx']], # prevent match to cls or ret
    'call':[['2...',['address'],'2xxx']],
    'skp' :[['e.9e',['register'],'Ex9E']],
    'sknp':[['e.a1',['register'],'ExA1']],
    'se'  :[['5..0',['register','register'],'5xy0'],
            ['3...',['register','byte'],'3xyy']],
    'sne' :[['9..0',['register','register'],'9xy0'],
            ['4...',['register','byte'],'4xyy']],
    'add' :[['7...',['register','byte'],'7xyy'],
            ['8..4',['register','register'],'8xy4'],
            ['f.1e',['i','register'],'Fy1E']],
    'or'  :[['8..1',['register','register'],'8xy1']],
    'and' :[['8..2',['register','register'],'8xy2']],
    'xor' :[['8..3',['register','register'],'8xy3']],
    'sub' :[['8..5',['register','register'],'8xy5']],
    'subn':[['8..7',['register','register'],'8xy7']],
    'shr' :[['8..6',['register'],'8x06'],
            ['    ',['register','register'],'8xy6']], # Blank regex, we never match, use shfit_mod instead
    'shl' :[['8..e',['register'],'8x0E'],
            ['    ',['register','register'],'8xyE']], # as above
    'rnd' :[['c...',['register','byte'],'Cxyy']],
    'jp'  :[['b...',['v0','address'],'Byyy'],
            ['1...',['address'],'1xxx']],
    'ld'  :[['6...',['register','byte'],'6xyy'],
            ['8..0',['register','register'],'8xy0'],
            ['f.07',['register','dt'],'Fx07'],
            ['f.0a',['register','k'],'Fx0A'],
            ['f.65',['register','[i]'],'Fx65'],
            ['a...',['i','address'],'Ayyy'],
            ['f.15',['dt','register'],'Fy15'],
            ['f.18',['st','register'],'Fy18'],
            ['f.29',['f','register'],'Fy29'],
            ['f.33',['b','register'],'Fy33'],
            ['f.55',['[i]','register'],'Fy55']],
    'drw' :[['d...',['register','register','nibble'],'Dxyz']]
    }
UNOFFICIAL_OP_CODES = ('xor','shr','shl','subn')
BANNED_OP_CODES = ('7f..','8f.4','8f.6','8f.e','cf..','6f..','8f.0','ff07','ff0a','ff65') # Ins that modify VF: add, shr, shl, rnd, ld
BANNED_OP_CODES_EXPLODED = []
for item in BANNED_OP_CODES:
    if item.find('.') == -1:
        BANNED_OP_CODES_EXPLODED.append(item)
    else:
        upper,repl,fill = 16,'.',1
        if item[2:] == '..':
            upper,repl,fill = 256,'..',2
        for i in range(0, upper):
            BANNED_OP_CODES_EXPLODED.append(item.replace(repl, hex(i)[2:].zfill(fill)))



