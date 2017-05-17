# tortilla8

Tortilla8 is a collection of Chip8 tools for per-processing, assembling, emulating, disassembling, and visualizing Chip8 ROMs.

What is Chip8
-------------

[Chip8](https://en.wikipedia.org/wiki/CHIP-8) is a language published in 1978 via the RCA COSMAC VIP Instruction Manual that was bosted as making game programming easier for hobbiests on the system. Chip8 is popular to emulate due to its simplicity and the now extensive amount of documentation.

Major Issues
------------

* Platter is untested on Mac. May work after installing a curses varient.
* Keypad input could be better

Modules
-------

* Cilantro

A lexer/tokenizer used by blackbean and jalapeno for individual lines of Chip8 assembly. The initialiser does the tokenizing, the class is then used as a data container. Cilanto canot be invoked from the terminal.

* Jalapeno

Pre-Processor used to flatten files before running them through blackbean. Currently strips "mode" and "option" directives without respecting them.
```
# Invoke Jalapeno, generates a ".jala" file
./jalapeno.py roms/vertical_stripes.asm
```

* Blackbean

An assembler that can generate Chip8 roms, stripped Chip8 assembly, or a listing file (asm with memory addresses).
```
# Invoke blackbean, generate a listing and strip file along with the ".ch8" binary.
./blackbean.py roms/vertical_stripes.jala -l -s
```

* Guacamole

Emulator for the Chip8 language/system. The emulator has no display, for that you should use platter or nacho. All successfully executed instructions are printed to the screen with the current value of the program counter and their mnemonic representation. All informational, warning, and fatal errors are also directed to stdout.
```
# Invoke guacamole, running at 10hz
./guacamole.py roms/vertical_stripes.ch8 -f 10
```

* Salsa

Disassembler for a two bytes worth of data, contains a utilty function to loop over a file handler and fully dissassemble.
```
# Invoke salsa
./guacamole.py roms/vertical_stripes.ch8 -o roms/vertical_stripes.asm
```

* Platter

Text based GUI for Guacamole that requires curses and simpleaudio, see below for any issues with your OS. Display information, warnings, and fatal errors reported by Guacamole along with all registers, the stack, and recently executed instructions. Detects when the emulator enters a "spin" state and gives the option of reseting.
```
# Start platter at 10hz, X to exit, R to reset, S to step in step mode (-s flag)
./platter.py roms/vertical_stripes.ch8 -f 10
```

* Nachos

Kivy based gui intended to be highly portable. No work has started yet.

Running on GNU/Linux, BSD variants
-----------------------------------

Install SimpleAudio via pip for sound in platter, Curses should ship with your python install.

Running on Windows
------------------

Install SimpleAudio via pip for sound in platter.
Windows does not ship with Curses, which is needed by platter, so you'll need install the wheel package yourself from [here](http://www.lfd.uci.edu/~gohlke/pythonlibs/). The 'cp34' (CPython 3.4) was tested on Windows 7. Once the package is downloaded, just cd to the directory and install via pip.
```
:: If you haven't installed pip, do that
python -m pip install -U pip setuptools
:: If you haven't installed Wheel, do that
pip install wheel
:: Install Curses for win32
python -m pip install curses-2.2-cp34-none-win32.whl
```
Unfortunately the windows version of curses doesn't support unicode, so only partial platter functionallity exists currently.

The below is only included as an infromational.
Additonally, there is [PDCurses](https://pdcurses.sourceforge.io/), with the popular python library being [UniCurses](https://pdcurses.sourceforge.io/). Instructions on installing follow, but **support is not included** as the syntax differs for UniCurses accross platforms.
```
:: Use pip to install UniCurses
pip install https://sourceforge.net/projects/pyunicurses/files/latest/download?source=typ_redirect
```
You will also need the dlls for both PDCurses and SDL; both are included in the win32 directory. Alternativly, [PDCurses](https://pdcurses.sourceforge.io/) distributes both source, pre-built dlls, and cofig files. Similarly, [SDL](https://www.libsdl.org/download-1.2.php) pre-built dlls, source, and configs can be easily found. SDL 1.2 is the recomended version for UniCurses 1.2, the latests avaialbe version as of writing, and was used for testing.

Running on Mac OS X
-------------------

Platter has not been tested on Mac OS X yet.

License
-------

All source code is licensed under GPLv3, including the asm for the Chip8 roms. Win32 DLLs include their licenses.

