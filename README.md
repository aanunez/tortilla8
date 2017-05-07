# tortilla8
What is Chip8
-------------

[Chip8](https://en.wikipedia.org/wiki/CHIP-8) is a language published in 1978 via the RCA COSMAC VIP Instruction Manual that was bosted as making programming easier for hobbiests on the system. Chip8 is popular to emulate due to its simplicity and the now extensive amount of documentation.

Major Issues
------------

* Key presses are not always correctly respected in Platter.
* Vertical wrapping on the screen doesn't work yet (no pong).

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

* Platter
Text based GUI for Guacamole. Display information, warnings, and fatal errors reported by Guacamole along with all registers, the stack, and recently executed instructions. Detects when the emulator enters a "spin" state and gives the option of reseting.
```
# Start platter at 10hz, X to exit, R to reset, S to step in step mode (-s flag)
./platter.py roms/vertical_stripes.ch8 -f 10
```

* Nachos
A GTK+ gui. No work has been started on this as of yet.

Running on Windows
-------------

Platter relies on python's curses, which is built on top of ncurses. The Windows exuivalent is [PDCurses](https://pdcurses.sourceforge.io/), with the popular python library being [UniCurses](https://pdcurses.sourceforge.io/). Instructions on installing follow, but support is not yet included as the syntax differs slightly for UniCurses.
```
:: Install pip
python -m pip install -U pip setuptools
:: Use pip to install UniCurses
pip install https://sourceforge.net/projects/pyunicurses/files/latest/download?source=typ_redirect
```
You will also need the dlls for both PDCurses and SDL; both are included in the win32 directory. Alternativly, [PDCurses](https://pdcurses.sourceforge.io/) distributes both source, pre-built dlls, and cofig files. Similarly, [SDL](https://www.libsdl.org/download-1.2.php) pre-built dlls, source, and configs can be easily found. SDL 1.2 is the recomended version for UniCurses 1.2, the latests avaialbe version as of writing, and was used for testing.

License
-------

All source code is licensed under GPLv3, including the asm for the Chip8 roms. Win32 DLLs include their licenses.

