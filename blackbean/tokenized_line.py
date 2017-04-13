#!/usr/bin/python3

from assembler_constants import *

class tokenized_line:

    def __init__(self, line, line_number):
        self.is_empty = True         #Default
        self.original = line         #whole, unedited, line
        self.comment  = ""           #comment on the line
        self.mem_tag  = ""           #tag/label for the line, no ":"
        self.pp_directive = ""       #any pre-procs on the line
        self.mem_address  = 0        #address
        self.line_numb = line_number #1 index line number

        self.data_declarations = []  #list of ints of size dataType
        self.data_size         = 0   #size (in bytes) of data defined on line
        self.dd_ints           = []  #ints for machine code

        self.instruction     = ""    #"cls", "ret" etc
        self.arguments       = []    #list of args in original form
        self.instruction_int = None  #single int for machine code

        line = line.lstrip()

        # Remove Blanks
        if line == '':
            return

        # Remove Comment only lines
        if line.startswith(BEGIN_COMMENT):
            self.comment = line.rstrip()
            return

        self.is_empty = False

        # Check for any comments
        self.comment = line.split(BEGIN_COMMENT)[1:]
        line = line.split(BEGIN_COMMENT)[0].rstrip()

        # Breakout into array
        line_array = list(filter(None, line.lower().split(' ')))

        # Check if tag exists, must be left most
        if line_array[0].endswith(':'):
            self.mem_tag = line_array[0][:-1]
            line_array.pop(0)
            if not line_array:
                return

        # If there are additional tags raise error
        if ':' in ''.join(line_array):
            #TODO raise error
            print("ERROR: Multiple Memory Tags found on same line.")

        # Check for any pre-processor commands
        for i in line_array:
            if i in PRE_PROC:
                self.pp_directive = ' '.join(line_array)
                #TODO raise error
                #raise ValueError("Pre-processor directive found.")
                return

        # Check for data declarations
        if line_array[0] in DATA_DECLARE:
            self.data_size = DATA_DECLARE[line_array[0]]
            line_array.pop(0)
            if not line_array:
                #TODO raise error
                print("ERROR: Expected data declaration.")
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
        print("ERROR: Unkown command.")
        return
