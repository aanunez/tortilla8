# tortilla8

Tortilla8 is a collection of Chip8 tools for per-processing, assembling, emulating, disassembling, and visualizing Chip8 ROMs.

## What is Chip8

[Chip8](https://en.wikipedia.org/wiki/CHIP-8) is a language published in 1978 via the RCA COSMAC VIP Instruction Manual that was bosted as making game programming easier for hobbiests on the system. Chip8 is popular to emulate due to its simplicity and the now extensive amount of documentation. Unfortunately there are some issues with Chip8 emulations, notably that there were differing implementations early on. These differences have been very well documented [here](https://github.com/Chromatophore/HP48-Superchip#behavior-and-quirk-investigations). Some of these isuses are addressed in tortilla8, but some are not as I have yet to encounter them for myself.

## Known Issues

* No docs for modules
* Keypad input could be better
* Controls can't be edited
* Rewinding while waiting for key input (ld reg, k) causes odd behavior
* Pre-Proc does not remove extra whitespace due to removing 'junk' lines
* No 'real' gui.

## Setup

Setup is strait forward, two dependencies are used for the text based gui (platter), Simple Audio and Curses, the later of which is discussed below on specifc OSes. Scripts can, of course, be run directly from package without install. If you are on a system that doesn't support symbolic links (read: windows) you'll need to copy the scripts up a level to the root of the pacakge so they can see the inner tortilla8 folder.

```
# If you haven't installed pip, do that
python -m pip install -U pip setuptools
# Navigate to the root of the package
# Install tortiall8
pip install .
# Install Simple Audio (optional)
pip install simpleaudio
```

## Demo

After insallation you can pre-processes, assemble, and emulate the any of the provided ROMs (or your own) by...
```
tortilla8 pre-process roms/vertical_stripes.asm
tortilla8 assemble roms/vertical_stripes_pp.asm -o roms/demo
tortilla8 emulate roms/demo.ch8 -f 150
```

![tortillas are made into chips, get it?](https://github.com/aanunez/tortilla8/raw/master/docs/platter_demo1.png "Platter running vertical_stripes.ch8")

## Usage

The main entry point after install is `tortilla8`, which has five options: assemble, disassemble, pre-process, execute, and emulate. More information for each can be found via tortilla8's help menus.

```
usage: tortilla8 [-h] {pre-process,assemble,disassemble,execute,emulate} ...

A collection of Chip8 tools for pre-processing, assembling, emulating,
disassembling, and visualizing Chip8 ROMs.

positional arguments:
  {pre-process,assemble,disassemble,execute,emulate}
                        Options for tortilla8...
    pre-process         Scan your CHIP-8 source code for pre-processor
                        directives, apply them as needed, and produce a
                        flattend source file. Respected Directives are:
                        'ifdef', 'ifndef', 'elif', 'elseif',
                        'elifdef','elseifdef', 'endif', 'else', 'equ', '='.
                        Currently, no mode modifers ('option', 'align' etc)
                        are respected.
    assemble            Assemble your CHIP-8 programs to executable machine
                        code. Listing files and comment-striped files can also
                        be generated. Arguments to mnemonics must be either be
                        integers in decimal or hex using '#' as a prefix. Data
                        declares may also be prefixed with '$' to denote
                        binary (i.e. '$11001100' or '$11..11..').
    disassemble         Dissassemble a Chip8 ROM, any byte pair that is not an
                        instruction is assumed to be a data declaration. No
                        checks are performed to insure the program is valid.
    execute             Execute a rom to quickly check for errors. The program
                        counter, hex instruction (the two bytes that make up
                        the opcode), and mnemonic are printed to the screen
                        immediately after the execution of that operation
                        code. All errors (info, warning, and fatal) are
                        printed to screen.
    emulate             Start a text (unicode) based Chip8 emulator which
                        disaplys a game screen, all registers, the stack,
                        recently processed instructions, and a console to log
                        any issues that occur.
```

## Modules

### Cilantro

A lexer/tokenizer used by blackbean and jalapeno for individual lines of Chip8 assembly. The initialiser does the tokenizing, the class is then used as a data container that can be populated later for information only the assembler or pre-proccessor would know.

### Jalapeno

Pre-Processor used to flatten files before running them through blackbean. Currently strips "mode" and "option" directives without respecting them. Repects options such as "if" and "else".

### Blackbean

An assembler that can generate Chip8 roms, comment-stripped Chip8 assembly, or a listing file (asm with memory addresses). The assembler makes no attempt to insure that illegal calls are not made or that the VF register isn't set.

### Salsa

Disassembler function for two bytes worth of data. If the input is not a valid instruction then it is assumed to be a data declaration.

### Guacamole

Emulator for the Chip8 language/system. The emulator has no display, for that you should use platter or nacho. There are currently no known major bugs in guacamole, however there are oddoties in Chip-8 in general (see abve in the 'What is Chip8' section). Guacamole makes use of two other modules: 'emulation_error' which houses a simple enum to determine the severity of an error that occured within the emulation and not one raised by python, and 'instructions' which contains a function for every Chip-8 opcode.

### Platter

Text based GUI for Guacamole that requires curses and simpleaudio, see below for any issues with your OS. Display information, warnings, and fatal errors reported by the emulator along with all registers, the stack, and recently executed instructions. Detects when the emulator enters a "spin" state and gives the option of reseting. Press the underlined (on GNU/Linux) or uppercase (Mac/Windows) to perform the menu actions (i.e. Stepping through the program, exiting) and use the arrow keys to control the rewind size (Left/Right) and emulation target frequency (Up/Down).

### Nachos

Kivy based gui intended to be highly portable. No work has started yet.

## Platter Compatability (Curses)

### Running on GNU/Linux, BSD variants

The Curses module ships with your python install, I have had no issues thus far. Some terminals will not correctly display some unicode characters, you can use either use the '-u' flag to disable unicode if that is the case.

### Running on Windows

Python for Windows does not ship with Curses, which is needed by platter, so you'll need install the wheel package yourself from [here](http://www.lfd.uci.edu/~gohlke/pythonlibs/). The 'cp34' (CPython 3.4) was tested on Windows 7. Once the package is downloaded, just cd to the directory and install via pip.
```
:: If you haven't installed Wheel, do that
pip install wheel
:: Install Curses for win32
python -m pip install curses-2.2-cp34-none-win32.whl
```
Unfortunately the windows version of curses doesn't support unicode, so the game display in Platter is 'unique'.

The below is only included as an infromational.
Additonally, there is [PDCurses](https://pdcurses.sourceforge.io/), with the popular python library being [UniCurses](https://pdcurses.sourceforge.io/). Instructions on installing follow, but **support is not included** as the syntax differs for UniCurses accross platforms.
```
:: Use pip to install UniCurses
pip install https://sourceforge.net/projects/pyunicurses/files/latest/download?source=typ_redirect
```
You will also need the dlls for both PDCurses and SDL; both are included in the win32 directory. Alternativly, [PDCurses](https://pdcurses.sourceforge.io/) distributes both source, pre-built dlls, and cofig files. Similarly, [SDL](https://www.libsdl.org/download-1.2.php) pre-built dlls, source, and configs can be easily found. SDL 1.2 is the recomended version for UniCurses 1.2, the latests avaialbe version as of writing, and was used for testing.

### Running on Mac OS X

The Curses module ships with your python install, however the mac default terminal does not correctly display unicode underline characters. Instead a version is shown where the uppercase letters are the hot-keys to perform the action.

## License

All source code is licensed under GPLv3, including the asm for the Chip8 roms. Win32 DLLs include their licenses.

