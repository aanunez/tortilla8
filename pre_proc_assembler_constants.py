#!/usr/bin/python3

# General
BEGIN_COMMENT=';'
END_MEM_TAG=':'
HEX_ESC='#'
BIN_ESC='$' #TODO not used yet

# Data Declaration (Sizes in bytes)
DATA_DECLARE={'db':1,'dw':2,'dd':4}

# Pre Processor
ELSE_IF=('elif','elseif','elifdef','elseifdef')
END_MARKS=('endif','else')+ELSE_IF
EQU_MARKS=('equ','=')
MODE_MARKS=('option','align','list','nolist')
PRE_PROC=('ifdef','ifndef')+END_MARKS+EQU_MARKS+MODE_MARKS
