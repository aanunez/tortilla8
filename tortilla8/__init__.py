#!/usr/bin/env python3

from os.path import dirname, basename, isfile
from glob import glob
modules = glob(dirname(__file__)+"/*.py")
__all__ = [ basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py') ]

from . import blackbean
from . import cilantro
from . import guacamole
from . import jalapeno
from . import platter
from . import salsa
