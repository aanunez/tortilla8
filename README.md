# tortilla8
**What is Chip8**

[Chip8](https://en.wikipedia.org/wiki/CHIP-8) is a language published in 1978 via the RCA COSMAC VIP Instruction Manual that was bosted as making programming easier for hobbiests on the system. Chip8 is popular to emulate due to its simplicity and the now extensive amount of documentation.

**Major Issues**

* Key presses are not always correctly respected in Platter.
* Vertical wrapping on the screen doesn't work yet (no pong).

**Modules**

* Cilantro
A lexer/tokenizer used by blackbean and jalapeno for individual lines of Chip8 assembly. The initialiser does the tokenizing, the class is then used as a data container. Cilanto canot be invoked from the terminal.

* Jalapeno
Pre-Processor used to flatten files before running them through blackbean. Currently strips "mode" and "option" directives without respecting them.
```shell
\# Invoke Jalapeno, generates a ".jala" file
./jalapeno.py roms/vertical_stripes.asm
```

* Blackbean
An assembler that can generate Chip8 roms, stripped Chip8 assembly, or a listing file (asm with memory addresses).
```shell
\# Invoke blackbean, generate a listing and strip file along with the ".ch8" binary.
./blackbean.py roms/vertical_stripes.jala -l -s
```

* Guacamole
Emulator for the Chip8 language/system. The emulator has no display, for that you should use platter or nacho. All successfully executed instructions are printed to the screen with the current value of the program counter and their mnemonic representation. All informational, warning, and fatal errors are also directed to stdout.
```shell
\# Invoke guacamole, running at 10hz
./guacamole.py roms/vertical_stripes.ch8 -f 10
```

* Platter
Text based GUI for Guacamole. Display information, warnings, and fatal errors reported by Guacamole along with all registers, the stack, and recently executed instructions. Detects when the emulator enters a "spin" state and gives the option of reseting.
```shell
\# Start platter at 10hz, X to exit, R to reset, S to step in step mode (-s flag)
./platter.py roms/vertical_stripes.ch8 -f 10
```

* Nachos
A GTK+ gui. No work has been started on this as of yet.

**Running on Windows**

I have yet to test this in a VM under mingw or cyngwin, but I have read that curses (used by platter) works fine under both.

**License**

All source code is licensed under GPLv3, including the asm for the Chip8 roms.

