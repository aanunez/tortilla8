#!/usr/bin/env python3

from random import randint
from tortilla8.emulation_error import Emulation_Error
from .constants.reg_rom_stack import STACK_ADDRESS, STACK_SIZE
from .constants.graphics import GFX_FONT_ADDRESS, GFX_RESOLUTION, GFX_ADDRESS, \
                                GFX_WIDTH, GFX_HEIGHT_PX, GFX_WIDTH_PX

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Instructions - All 20 mnemonics, 35 total instructions
# Add-3 SE-2 SNE-2 LD-11 JP-2 (mnemonics w/ extra instructions)

def i_cls(emu):
    emu.ram[GFX_ADDRESS:GFX_ADDRESS + GFX_RESOLUTION] = [0x00] * GFX_RESOLUTION
    emu.draw_flag = True

def i_ret(emu):
    emu.stack_pointer -= 1
    if emu.stack_pointer < 0:
        emu.log("Stack underflow", Emulation_Error._Fatal)
    emu.program_counter = emu.stack.pop()

def i_sys(emu):
    emu.log("RCA 1802 call to " + hex( get_address(emu) ) + " was ignored.", Emulation_Error._Warning)

def i_call(emu):
    if STACK_ADDRESS:
        emu.ram[stack_pointer] = emu.program_counter
    emu.stack_pointer += 1
    emu.stack.append(emu.program_counter)
    if emu.stack_pointer > STACK_SIZE:
        emu.log("Stack overflow. Stack is now size " + emu.stack_pointer, Emulation_Error._Warning)
    emu.program_counter = get_address(emu) - 2

def i_skp(emu):
    if emu.keypad[ get_reg1_val(emu) & 0x0F ]:
        emu.program_counter += 2

def i_sknp(emu):
    if not emu.keypad[ get_reg1_val(emu) & 0x0F ]:
        emu.program_counter += 2

def i_se(emu):
    comp =  get_lower_byte(emu) if "byte" in emu.dis_ins.mnemonic_arg_types else get_reg2_val(emu)
    if  get_reg1_val(emu) == comp:
        emu.program_counter += 2

def i_sne(emu):
    comp =  get_lower_byte(emu) if "byte" in emu.dis_ins.mnemonic_arg_types else get_reg2_val(emu)
    if  get_reg1_val(emu) != comp:
        emu.program_counter += 2

def i_shl(emu):
    if emu.legacy_shift:
        emu.register[0xF] = 0x01 if get_reg2_val(emu) >= 0x80 else 0x0
        emu.register[ get_reg1(emu) ] = ( get_reg2_val(emu) << 1 ) & 0xFF
    else:
        emu.register[0xF] = 0x01 if get_reg1_val(emu) >= 0x80 else 0x0
        emu.register[ get_reg1(emu) ] = ( get_reg1_val(emu) << 1 ) & 0xFF

def i_shr(emu):
    if emu.legacy_shift:
        emu.register[0xF] = 0x01 if ( get_reg2_val(emu) % 2) == 1 else 0x0
        emu.register[ get_reg1(emu) ] = get_reg2_val(emu) >> 1
    else:
        emu.register[0xF] = 0x01 if ( get_reg1_val(emu) % 2) == 1 else 0x0
        emu.register[ get_reg1(emu) ] = get_reg1_val(emu) >> 1

def i_or(emu):
    emu.register[ get_reg1(emu) ] = get_reg1_val(emu) | get_reg2_val(emu)

def i_and(emu):
    emu.register[ get_reg1(emu) ] = get_reg1_val(emu) & get_reg2_val(emu)

def i_xor(emu):
    emu.register[ get_reg1(emu) ] = get_reg1_val(emu) ^ get_reg2_val(emu)

def i_sub(emu):
    emu.register[0xF] = 0x01 if get_reg1_val(emu) > get_reg2_val(emu) else 0x00
    emu.register[ get_reg1(emu) ] = get_reg1_val(emu) - get_reg2_val(emu)
    emu.register[ get_reg1(emu) ] &= 0xFF

def i_subn(emu):
    emu.register[0xF] = 0x01 if get_reg2_val(emu) > get_reg1_val(emu) else 0x00
    emu.register[ get_reg1(emu) ] = get_reg2_val(emu) - get_reg1_val(emu)
    emu.register[ get_reg1(emu) ] &= 0xFF

def i_jp(emu):
    init_pc = emu.program_counter
    if 'v0' in emu.dis_ins.mnemonic_arg_types:
        emu.program_counter = get_address(emu) + emu.register[0] - 2
    else:
        emu.program_counter = get_address(emu) - 2

    if init_pc == emu.program_counter + 2:
        emu.spinning = True

def i_rnd(emu):
    emu.register[ get_reg1(emu) ] = randint(0, 255) & get_lower_byte(emu)

def i_add(emu):
    if 'byte' in emu.dis_ins.mnemonic_arg_types:
        emu.register[ get_reg1(emu) ] += get_lower_byte(emu)
        emu.register[ get_reg1(emu) ] &= 0xFF

    elif 'i' in emu.dis_ins.mnemonic_arg_types:
        emu.index_register += get_reg1_val(emu)
        emu.index_register &= 0xFFF

    else: # Reg + Reg
        emu.register[ get_reg1(emu) ] += get_reg2_val(emu)
        emu.register[ get_reg1(emu) ] &= 0xFF
        emu.register[0xF] = 0x00
        if  get_reg1_val(emu) + get_reg2_val(emu) > 0xFF:
            emu.register[ get_reg1(emu) ] &= 0xFF
            emu.register[0xF] = 0x01

def i_ld(emu):
    arg1 = emu.dis_ins.mnemonic_arg_types[0]
    arg2 = emu.dis_ins.mnemonic_arg_types[1]

    if 'register' is arg1:
        if   'byte'     is arg2: emu.register[ get_reg1(emu) ] = get_lower_byte(emu)
        elif 'register' is arg2: emu.register[ get_reg1(emu) ] = get_reg2_val(emu)
        elif 'dt'       is arg2: emu.register[ get_reg1(emu) ] = emu.delay_timer_register
        elif 'k'        is arg2:
            emu.waiting_for_key = True
            emu.program_counter -= 2
        elif '[i]' == arg2:
            for i in range( get_reg1(emu) ):
                emu.register[i] = emu.ram[emu.index_register + i]

        else:
            emu.log("Loads with argument type '" + arg2 + "' are not supported.", Emulation_Error._Fatal)

    elif 'register' is arg2:
        if   'dt' is arg1: emu.delay_timer_register =  get_reg1_val(emu)
        elif 'st' is arg1: emu.sound_timer_register =  get_reg1_val(emu)
        elif 'f'  is arg1: emu.index_register = GFX_FONT_ADDRESS + ( 5 * get_reg1_val(emu) )
        elif 'b'  is arg1:
            bcd = str( get_reg1_val(emu) ).zfill(3)
            for i in range(3):
                emu.ram[emu.index_register + i] = int(bcd[i])

        elif '[i]' == arg1:
            for i in range( get_reg1(emu)):
                emu.ram[emu.index_register + i] = emu.register[i]

        else:
            emu.log("Loads with argument type '" + arg1 + "' are not supported.", Emulation_Error._Fatal)

    elif 'i' is arg1 and 'address' is arg2:
        emu.index_register =  get_address(emu)

    else:
        emu.log("Loads with argument types '" + arg1 + "' and '" + arg2 +  \
            "' are not supported.", Emulation_Error._Fatal)

def i_drw(emu):
    emu.draw_flag = True
    height = int(emu.dis_ins.hex_instruction[3],16)
    x_origin_byte = int( get_reg1_val(emu) / 8 ) % GFX_WIDTH
    y_origin_byte = (get_reg2_val(emu) % GFX_HEIGHT_PX) * GFX_WIDTH
    shift_amount = get_reg1_val(emu) % GFX_WIDTH_PX % 8

    emu.register[0xF] = 0x00
    for y in range(height):
        sprite =  bin(emu.ram[ emu.index_register + y ])[2:].zfill(8)
        for x in range(2):
            if shift_amount == 0 and x == 1:
                continue

            x_offset = x if x_origin_byte + x != GFX_WIDTH else 1-GFX_WIDTH
            working_byte = GFX_ADDRESS + (( x_origin_byte + y_origin_byte + \
                (y * GFX_WIDTH) + x_offset ) % GFX_RESOLUTION)

            original = emu.ram[ working_byte ]
            b_list = bin(original)[2:].zfill(8)
            if x == 0:
                untouched_chunk = b_list[:shift_amount]
                original_chunk  = b_list[shift_amount:]
                sprite_chunk    = sprite[:8-shift_amount]
            if x == 1:
                untouched_chunk = b_list[shift_amount:]
                original_chunk  = b_list[:shift_amount]
                sprite_chunk    = sprite[8-shift_amount:]

            xor_chunk = bin(int(original_chunk,2) ^ int(sprite_chunk,2))[2:].zfill(len(original_chunk))
            emu.ram[ working_byte ] = \
                int(untouched_chunk + xor_chunk,2) if x == 0 else int(xor_chunk + untouched_chunk,2)

            if bin( ( emu.ram[ working_byte ] ^ original ) & original ).find('1') != -1:
                emu.register[0xF] = 0x01

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Hex Extraction

def get_address(emu):
    return int(emu.dis_ins.hex_instruction[1:4], 16)

def get_reg1(emu):
    return int(emu.dis_ins.hex_instruction[1],16)

def get_reg2(emu):
    return int(emu.dis_ins.hex_instruction[2],16)

def get_reg1_val(emu):
    return emu.register[int(emu.dis_ins.hex_instruction[1],16) ]

def get_reg2_val(emu):
    return emu.register[int(emu.dis_ins.hex_instruction[2],16) ]

def get_lower_byte(emu):
    return int(emu.dis_ins.hex_instruction[2:4], 16)


