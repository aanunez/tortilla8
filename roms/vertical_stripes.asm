
    ld  va, 0
    ld  vb, 0
start:
    ld  i,  solid
    drw va, vb, 1
    add vb, 2
    se  vb, 32
    jp  start

spin:
    jp spin

solid:
    dd  #ffffffff, #ffffffff


               drw is crashing emu when Y is off screen. Is Vertical wrapping a thing?
