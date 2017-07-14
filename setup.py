#!/usr/bin/env python3

# doc page:
# https://docs.python.org/3.5/distutils/setupscript.html
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
        'Sound':  ['simpleaudio'],
        'GUI': ['pygame'],
    },
	#scripts = [
	#	    'scripts/t8-assemble',
	#	    'scripts/t8-disassemble',
    #	    'scripts/t8-execute',
	#	    'scripts/t8-preproc',
	#	    'scripts/t8-emulate'
	#	   ],
	include_package_data = True,
    entry_points={
        'console_scripts': [
            'tortilla8 = tortilla8.__main__:main'
        ]
    },
    classifiers=[
        # List here: https://pypi.python.org/pypi?%3Aaction=browse
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.5',
    ],
    keywords='emulation chip-8 chip8 rom emulator assembler disassembler'
)
