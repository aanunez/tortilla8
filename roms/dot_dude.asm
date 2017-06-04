; Dot Dude Rom for CHIP 8
;
; This rom is for testing the Load key instruction in a
; chip-8 emulator. It moves a dot in the direction of
; the key press (2 4 6 8) then waits for another input.
;
; Licensed under GPLv3, Adam Nunez
; Apart of the tortilla 8 project
;


	ld  va, 32               ; init x cord 64/2
	ld  vb, 16               ; init y cord 32/2
    ld  i,  dot              ; dot for drawing
    ld  vd, 1                ; Sub can only to reg to reg
loop:
    drw va, vb, 1            ; Draw current dot
    ld  vc, k                ; Wait for input
    drw va, vb, 1            ; Remove current dot
    sne vc, 2                ; ----------------------------
    jp  down                 ; Check val of key press on a
    sne vc, 4                ; modern PC numb pad and jump
    jp  left                 ; to current address. If any
    sne vc, 6                ; other key is pressed just
    jp  right                ; jump back to the top of the
    sne vc, 8                ; loop.
    jp  up                   ;
    jp  loop                 ; ----------------------------
down:                        ; ----------------------------
    add vb, vd               ; Add or subtract to the x/y
    jp  loop                 ; cord depending on what was
left:                        ; pressed then jump back to
    sub va, vd               ; top of loop.
    jp  loop                 ;
right:                       ;
    add va, vd               ;
    jp  loop                 ;
up:                          ;
    sub vb, vd               ;
    jp  loop                 ; ----------------------------
dot:                         ;
    db  #80                  ; Dot for drawing
