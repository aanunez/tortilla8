#!/usr/bin/env python3

from . import export
from .cilantro import Cilantro
from .constants.symbols import BEGIN_COMMENT
from .constants.preprocessor import MODE_MARKS, EQU_MARKS, ELSE_IF, END_MARKS
__all__ = []

#TODO Respect MODE_MARKS and add common directives to it.
#TODO Remove excess whitespace when its around pre-proc directives

@export
class Jalapeno:
    """
    Jalapeno is a pre-processor class that can take file handlers,
    process all common chip8 pre processor directives and return
    a flattend source file.
    """

    def __init__(self, file_handler=None, definitions=None):
        """
        Init the token collection and symbols list.
        """
        self.collection = []
        self.symbols = {}

        if file_handler:
            self.process(file_handler, definitions)

    def reset(self):
        """
        Reset the pre-processor to process another file.
        """
        self.__init__(self)

    def process(self, file_handler, definitions=None):
        """
        Flattens all if/else/elif etc and replaces EQU directives for a file.
        Stores to the lexer class under cilantro.pp_line
        Does not currently support any option or mode directives.
        """
        skipping_lines = False
        awaiting_end = False
        if definitions is None:
            definitions = []

        # Flatten all IF/ELSE/ETC directives  - Pass One
        for i,line in enumerate(file_handler):
            t = Cilantro(line, i)

            if skipping_lines:
                if (t.pp_directive in ('endif','else')) or\
                   (t.pp_directive in ELSE_IF and t.pp_args[0] in definitions):
                    skipping_lines = False
                    awaiting_end = True
                continue

            if not t.pp_directive:
                self.collection.append(t)
                continue

            if awaiting_end and t.pp_directive in END_MARKS:
                awaiting_end = False
                continue

            if t.pp_directive == 'ifdef':
                if t.pp_args[0] in definitions:
                    awaiting_end = True
                else:
                    skipping_lines = True
                continue

            if t.pp_directive == 'ifndef':
                if t.pp_args[0] not in definitions:
                    awaiting_end = True
                else:
                    skipping_lines = True
                continue

            if t.pp_directive in MODE_MARKS:
                continue #TODO Throw away for now

            if t.pp_directive in EQU_MARKS:
                self.symbols[t.pp_args[0]] = t.pp_args[1]
                continue

            self.collection.append(t)

        # Replace Symbols ( EQU and '=' ) and set pp_line  - Pass Two
        for sym in self.symbols:
            for tl in self.collection:

                if not tl.pp_line:
                    tl.pp_line = tl.original

                iterator = tl.arguments if tl.arguments != [] else tl.data_declarations
                for i,arg in enumerate(iterator):
                    if arg == sym:
                        if tl.arguments != []:
                            tl.arguments[i] = self.symbols[sym]
                        else:
                            tl.data_declarations[i] = self.symbols[sym]
                        tl.pp_line = tl.pp_line.replace(sym, self.symbols[sym])
                        if tl.pp_line.find(BEGIN_COMMENT) != -1:
                            tl.pp_line = tl.pp_line.split(BEGIN_COMMENT)[0] + BEGIN_COMMENT + tl.comment

    def print_processed_source(self, file_handler=None):
        """
        Print flattened source code to stdout or file handler.
        """
        for tl in self.collection:
            if file_handler is None:
                print(tl.pp_line, end='')
            else:
                file_handler.write(tl.pp_line)




