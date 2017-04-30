; Vertical Strip Test Rom for CHIP 8
;
; Displays alternating stripes on the screen (solid first)
; then spins, rom must be terminated manually.
; Pre-Processor directives are only here for testing and
; can be removed.
;
; Licensed under GPLv3, Adam Nunez
; Apart of the tortilla 8 project
;

solid   EQU    #ffffffff     ; Testing replacment

    ld  va, 0                ; Initial X cord
    ld  vb, 0                ; Initial Y cord
    ld  i,  stripe           ; Load strip for drawing

start:
    drw va, vb, 1            ; Draw a 1px tall strip on row vb
    add vb, 2
    se  vb, 32
    jp  start

spin:
    jp spin                  ; Spin forever

stripe:
    dd  solid, solid

ifdef something
                             ; Stuff to be thrown away
else
    dd  #00000000            ; Useless padding
endif
