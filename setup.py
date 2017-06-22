#!/usr/bin/python3

from setuptools import setup

setup(
	name = 'tortilla8',
	version = '0.2',
	description = 'A collection of Chip8 tools for pre-processing, assembling, emulating, disassembling, and visualizing Chip8 ROMs.',
	author = 'Adam Nunez',
	author_email = 'adam.a.nunez@gmail.com',
	license = 'GPLv3',
	url = 'https://github.com/aanunez/tortilla8',
	packages = ['tortilla8'],
	#install_requires = [], #Curses and SimpleAudio are optional
    extras_require = {
        'Emulation Sound':  ["simpleaudio"],
    },
	scripts = [
		    'scripts/t8-assemble',
		    'scripts/t8-disassemble',
		    'scripts/t8-execute',
		    'scripts/t8-preproc',
		    'scripts/t8-emulate'
		   ],
	include_package_data = True
)
