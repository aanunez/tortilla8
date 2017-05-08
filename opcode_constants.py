#!/usr/bin/python3

# OP CODES
OP_ARGS=0
OP_HEX=1
OP_CODE_SIZE=2
OP_CODES={
'cls' :[[[],'00E0']],
'ret' :[[[],'00EE']],
'sys' :[[['address'],'0xxx']],
'call':[[['address'],'2xxx']],
'skp' :[[['register'],'Ex9E']],
'sknp':[[['register'],'ExA1']],
'se'  :[[['register','register'],'5xy0'],
        [['register','byte'],'3xyy']],
'sne' :[[['register','register'],'9xy0'],
        [['register','byte'],'4xyy']],
'add' :[[['register','byte'],'7xyy'],
        [['register','register'],'8xy4'],
        [['i','register'],'Fx1E']],
'or'  :[[['register','register'],'8xy1']],
'and' :[[['register','register'],'8xy2']],
'xor' :[[['register','register'],'8xy3']],#TODO not in orig spec.
'sub' :[[['register','register'],'8xy5']],
'subn':[[['register','register'],'8xy7']],#TODO not in orig spec.
'shr' :[[['register'],'8x06'],            #TODO not in orig spec.
        [['register','register'],'8xy6']],#TODO not in orig spec.
'shl' :[[['register'],'8x0E'],            #TODO not in orig spec.
        [['register','register'],'8xyE']],#TODO not in orig spec.
'rnd' :[[['register','byte'],'Cxyy']],
'jp'  :[[['v0','address'],'Byyy'],
        [['address'],'1xxx']],
'ld'  :[[['register','byte'],'6xyy'],
        [['register','register'],'8xy0'],
        [['register','dt'],'Fx07'],
        [['register','k'],'Fx0A'],
        [['register','[i]'],'Fx65'],
        [['i','address'],'Ayyy'],
        [['dt','register'],'Fy15'],
        [['st','register'],'Fy18'],
        [['f','register'],'Fy29'],
        [['b','register'],'Fy33'],
        [['[i]','register'],'Fy55']],
'drw' :[[['register','register','nibble'],'Dxyz']]}

# Index from Regex Hex Codes to mnemonic
OP_REG={
'00E0':['cls',0],
'00EE':['ret',0],
'0.[^E].':['sys',0],   # we don't traverse the dict in order, so make sure this doesn't match to cls or ret
'1...':['jp',1],
'2...':['call',0],
'3...':['se',1],
'4...':['sne',1],
'5..0':['se',0],
'6...':['ld',0],
'7...':['add',0],
'8..0':['ld',1],
'8..1':['or',0],
'8..2':['and',0],
'8..3':['xor',0],
'8..4':['add',1],
'8..5':['sub',0],
'8..6':['shr',0], #TODO no support for emulating the "more correct" form of shift
'8..7':['subn',0],
'8..E':['shl',0], #TODO above
'9..0':['sne',0],
'A...':['ld',5],
'B...':['jp',0],
'C...':['rnd',0],
'D...':['drw',0],
'E.9E':['skp',0],
'E.A1':['sknp',0],
'F.07':['ld',2],
'F.0A':['ld',3],
'F.15':['ld',6],
'F.18':['ld',7],
'F.1E':['add',2],
'F.29':['ld',8],
'F.33':['ld',9],
'F.55':['ld',10],
'F.65':['ld',4]}



