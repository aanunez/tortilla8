# CHIP-8 Documentation
The included docs, plus maybe bugging people on /r/emudev should be more than enough to make a working CHIP8 emulator.

Things I got stuck on:
* Setting VF high means setting it to exectly one.
* The 'add i, reg' instruction has undocumented behavior where an overflow of I causes the VF flag to be set, but the instruction never sets VF low. This is accounted for via a constant 'SET_VF_ON_GFX_OVERFLOW' in tortilla8 and is off by default.

Included
--------
* Original manual - Original RCA manual with chip 8. Excludes some instructions (XOR, shifts, subn)
* Viper Vol 1, Issue 2 - Goes over the above missing instructions on page 3.
* Cowgod's Chip-8 Technical Reference - Probably the most complete spec for the Chip-8

Additional Online Sources
-------------------------
[Mastering Chip-8 by Matthew Mikolay](http://mattmik.com/files/chip8/mastering/chip8.html)

[How to write an emulator by Laurence Muller](http://www.multigesture.net/articles/how-to-write-an-emulator-chip-8-interpreter/)

[Reddit user Dannyg86 asking about bugs in their emulator](https://www.reddit.com/r/EmuDev/comments/5so1bo/chip8_emu_questions/)

[Chip8.com Archive](https://web.archive.org/web/20161002171937/http://chip8.com/)

[Chip8.com's rom collection](https://web.archive.org/web/20161020052454/http://chip8.com/downloads/Chip-8%20Pack.zip)

[Wiki Article](https://en.wikipedia.org/wiki/CHIP-8)
