#!/usr/bin/env python3

# This is a simple test to make sure there are no obvious errors.
# It is not intended to be exhaustive.

import os

os.system('sudo pip3 uninstall tortilla8')
os.system('sudo pip3 install .')
print("Running tests...")
os.system('t8-assemble roms/vertical_stripes_pp.asm')
print("Done!")
