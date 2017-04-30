#!/usr/bin/python3

from pre_proc_assembler_constants import *
from opcode_constants import *

#TODO raise real warnings

class cilantro:
    '''
    Lexer/tokenizer for Chip 8 instructions. Used by Blackbean (assembler)
    and Jalapeno (pre-processor).
    '''

    def __init__(self, line, line_number):
        """
        Intializes by parsing the line and storing the line_number.
        The object is then used as a data container for Blackbean.
        """
        self.is_empty = True         #Default, is blank or comment only
        self.original = line         #whole, unedited, line
        self.comment  = ""           #comment on the line
        self.mem_tag  = ""           #tag/label for the line, no ":"
        self.mem_address  = 0        #address
        self.line_numb = line_number #1 index line number

        self.pp_directive = ""       #pre-procs directive on the line
        self.pp_args      = []       #arguments after or surounding a pp directive
        self.pp_line      = ""       #line with pp applied

        self.data_declarations = []  #list of strings in original form
        self.data_size         = 0   #size (in bytes) of data defined on line
        self.dd_ints           = []  #ints for machine code of size dataType

        self.instruction     = ""    #"cls", "ret" etc
        self.arguments       = []    #list of args in original form
        self.instruction_int = None  #single int for machine code

        line = line.lstrip()

        # Remove Blanks
        if line.isspace() or not line:
            return

        # Remove Comment only lines
        if line.lstrip().startswith(BEGIN_COMMENT):
            self.comment = line.rstrip()
            return

        self.is_empty = False

        # Check for any comments
        self.comment = ''.join(line.split(BEGIN_COMMENT)[1:])
        line = line.split(BEGIN_COMMENT)[0].rstrip()

        # Breakout into array
        line_array = line.lower().split()

        # Check if tag exists, must be left most
        if line_array[0].endswith(END_MEM_TAG):
            self.mem_tag = line_array[0][:-1]
            line_array.pop(0)
            if not line_array:
                return

        # If there are additional tags raise error
        if END_MEM_TAG in ''.join(line_array):
            print("Fatal: Multiple Memory Tags found.")
            return

        # Check for any pre-processor commands
        for i,word in enumerate(line_array):
            if word in PRE_PROC:
                self.pp_directive = word
                line_array.pop(i)
                self.pp_args = line_array
                return

        # Check for data declarations
        if line_array[0] in DATA_DECLARE:
            self.data_size = DATA_DECLARE[line_array[0]]
            line_array.pop(0)
            if not line_array:
                print("Fatal: Expected data declaration.")
                return
            self.data_declarations = ''.join(line_array).split(',')
            return

        # Check for assembly instruction
        if line_array[0] in OP_CODES:
            self.instruction = line_array[0]
            line_array.pop(0)
            self.arguments = []
            if line_array:
                self.arguments = ''.join(line_array).split(',')
            return

        # Trash
        print("Fatal: Cannot parse.")
        return
