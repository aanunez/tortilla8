; Vertical Strip Test Rom for CHIP 8
;
; Displays alternating stripes on the screen in a variety
; of ways then spins, rom must be terminated manually.
; Pre-Processor directives are only here for testing and
; can be removed.
;
; Licensed under GPLv3, Adam Nunez
; Apart of the tortilla 8 project
;

solid   EQU    #ff           ; Testing replacment
blank   EQU    #00           ; Testing replacment


; Vertical stripes, one at a time
    call    reset
    ld  i,  stripe           ; Load stripe for drawing
test1:
    drw va, vb, 1            ; Draw a 1px tall, 8px wide block
    add va, 8                ; Inc x by 1 byte
    se  va, 64               ; If x == 64, skip jp
    jp  test1                ; Jump back to draw rest of line
    ld  va, 0                ; reset va
    add vb, 2                ; Inc y by 2
    se  vb, 32               ; If y == 32, skip jp
    jp  test1                ; Jump back to draw another line


; Vertical stripes, several at a time (8x8)
    call    reset
    ld  i,  block            ; Load block for drawing
test2:
    drw va, vb, 8            ; Draw a 8px tall, 8px wide block
    add va, 8                ; Inc x by 1 byte
    se  va, 64               ; If x == 64, skip jp
    jp  test2                ; Jump back to draw rest of line
    ld  va, 0                ; reset va
    add vb, 8                ; Inc y by 8, the height of the block
    se  vb, 32               ; If y == 32, skip jp
    jp  test2                ; Jump back to draw another line


; Checker board, 4x4 at a time
    call    reset
    ld  i,  checker          ; Load block for drawing
test3:
    drw va, vb, 4            ; Draw a 4px tall, 8px wide block
    add va, 8                ; Inc x by a byte
    se  va, 64               ; If x == 64, skip jp
    jp  test3                ; Jump back to draw rest of line
    ld  va, 0                ; reset va
    add vb, 4                ; Inc y by 4, the height of the block
    se  vb, 32               ; If y == 32, skip jp
    jp  test3                ; Jump back to draw another line


; Paint solid white, 8x8 at a time
    call    reset
    ld  i,  largestripe      ; Load thick stripe
test4:
    drw va, vb, 8            ; Draw a 8px tall, 8px wide block
    add va, 8                ; Inc x by a byte
    se  va, 64               ; If x == 64, skip jp
    jp  test4                ; Jump back to draw rest of line
    ld  va, 0                ; reset va
    add vb, 8                ; Inc y by 8, the height of the block
    se  vb, 32               ; If y == 32, skip jp
    jp  test4                ; Jump back to draw another line


; Re paint Checker board, 4x4 at a time, skipping reset to test XOR
    ld  va, 0                ; Initial X cord
    ld  vb, 0                ; Initial Y cord
    ld  i,  checker          ; Load block for drawing
test5:
    drw va, vb, 4            ; Draw a 4px tall, 8px wide block
    add va, 8                ; Inc x by a byte
    se  va, 64               ; If x == 64, skip jp
    jp  test5                ; Jump back to draw rest of line
    ld  va, 0                ; reset va
    add vb, 4                ; Inc y by 4, the height of the block
    se  vb, 32               ; If y == 32, skip jp
    jp  test5                ; Jump back to draw another line

spin:
    jp  spin                 ; Spin forever

reset:
    cls
    ld  va, 0                ; Initial X cord
    ld  vb, 0                ; Initial Y cord
    ret

stripe:
    db  solid

largestripe:
    db  solid,solid,solid,solid,solid,solid,solid,solid

block:
    db  blank,solid,blank,solid,blank,solid,blank,solid

checker:
    db  #AA,#55,#AA,#55

ifdef something
                             ; Stuff to be thrown away
else
    dd  #00000000            ; Useless padding
endif
