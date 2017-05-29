#!/usr/bin/python3

from collections import namedtuple
from .constants.preprocessor import END_MEM_TAG, PRE_PROC, DATA_DECLARE
from .constants.symbols import BEGIN_COMMENT
from .constants.opcodes import OP_CODES

cilantro_data = namedtuple('cilantro_data', 'is_empty original \
    comment mem_tag mem_address line_numb pp_directive pp_args \
    pp_line data_declarations data_size dd_ints instruction \
    arguments instruction_int')

def cilantro(line, line_number):
    '''
    Cilantro is a lexer/tokenizer for Chip 8 instructions. Used by Blackbean
    (assembler) and Jalapeno (pre-processor).
    '''
    is_empty = True,         #Default, is blank or comment only
    original = line,         #whole, unedited, line
    comment  = "",           #comment on the line
    mem_tag  = "",           #tag/label for the line, no ":"
    mem_address  = 0,        #address
    line_numb = line_number, #1 index line number

    pp_directive = "",       #pre-procs directive on the line
    pp_args      = [],       #arguments after or surounding a pp directive
    pp_line      = "",       #line with pp applied

    data_declarations = [],  #list of strings in original form
    data_size         = 0,   #size (in bytes) of data defined on line
    dd_ints           = [],  #ints for machine code of size dataType

    instruction     = "",    #"cls", "ret" etc
    arguments       = [],    #list of args in original form
    instruction_int = None   #single int for machine code

    line = line.lstrip()

    # Remove Blanks
    if line.isspace() or not line:
        return cilantro_data(is_empty, original, comment, mem_tag, mem_address,
            line_numb, pp_directive, pp_args, pp_line, data_declarations,
            data_size, dd_ints, instruction, arguments, instruction_int)

    # Remove Comment only lines
    if line.lstrip().startswith(BEGIN_COMMENT):
        c.comment = line.rstrip()
        return cilantro_data(is_empty, original, comment, mem_tag, mem_address,
            line_numb, pp_directive, pp_args, pp_line, data_declarations,
            data_size, dd_ints, instruction, arguments, instruction_int)

    c.is_empty = False

    # Check for any comments
    c.comment = ''.join(line.split(BEGIN_COMMENT)[1:])
    line = line.split(BEGIN_COMMENT)[0].rstrip()

    # Breakout into array
    line_array = line.lower().split()

    # Check if tag exists, must be left most
    if line_array[0].endswith(END_MEM_TAG):
        c.mem_tag = line_array[0][:-1]
        line_array.pop(0)
        if not line_array:
            return cilantro_data(is_empty, original, comment, mem_tag, mem_address,
                line_numb, pp_directive, pp_args, pp_line, data_declarations,
                data_size, dd_ints, instruction, arguments, instruction_int)

    # If there are additional tags raise error
    if END_MEM_TAG in ''.join(line_array):
        raise RuntimeError("Multiple Memory Tags found on line " + str(c.line_numb))

    # Check for any pre-processor commands
    for i,word in enumerate(line_array):
        if word in PRE_PROC:
            c.pp_directive = word
            line_array.pop(i)
            c.pp_args = line_array
            return cilantro_data(is_empty, original, comment, mem_tag, mem_address,
                line_numb, pp_directive, pp_args, pp_line, data_declarations,
                data_size, dd_ints, instruction, arguments, instruction_int)

    # Check for data declarations
    if line_array[0] in DATA_DECLARE:
        c.data_size = DATA_DECLARE[line_array[0]]
        line_array.pop(0)
        if not line_array:
            raise RuntimeError("Expected data declaration on line " + str(c.line_numb))
        c.data_declarations = ''.join(line_array).split(',')
        return cilantro_data(is_empty, original, comment, mem_tag, mem_address,
            line_numb, pp_directive, pp_args, pp_line, data_declarations,
            data_size, dd_ints, instruction, arguments, instruction_int)

    # Check for assembly instruction
    if line_array[0] in OP_CODES:
        c.instruction = line_array[0]
        line_array.pop(0)
        c.arguments = []
        if line_array:
            c.arguments = ''.join(line_array).split(',')
        return cilantro_data(is_empty, original, comment, mem_tag, mem_address,
            line_numb, pp_directive, pp_args, pp_line, data_declarations,
            data_size, dd_ints, instruction, arguments, instruction_int)

    # Trash
    raise RuntimeError("Cannot parse line " + str(c.line_numb))


