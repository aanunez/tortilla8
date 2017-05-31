; Dot Dude Rom for CHIP 8
;
; 
;
; Licensed under GPLv3, Adam Nunez
; Apart of the tortilla 8 project
;


	ld  va, 32               ; init x cord 64/2
	ld  vb, 16               ; init y cord 32/2
    ld  i,  dot
    ld  vd, 1
loop:
    drw va, vb, 1
    ld  vc, k
    drw va, vb, 1
    sne vc, 2
    jp  down
    sne vc, 4
    jp  left
    sne vc, 6
    jp  right
    sne vc, 8
    jp  up
    jp  loop
down:
    add vb, vd
    jp  loop
left:
    sub va, vd
    jp  loop
right:
    add va, vd
    jp  loop
up:
    sub vb, vd
    jp  loop
dot:
    db  #80
