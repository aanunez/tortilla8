#!/usr/bin/env python3

# This snipit adds EVERYTHING to __all__
#from os.path import dirname, basename, isfile
#from glob import glob
#modules = glob(dirname(__file__)+"/*.py")
#__all__ = [ basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py') ]

__all__ = []

def export(defn):
    globals()[defn.__name__] = defn
    __all__.append(defn.__name__)
    return defn

from enum import Enum
@export
class Emulation_Error(Enum):
    _Information = 1
    _Warning     = 2
    _Fatal       = 3

    def __str__(self):
        return self.name[1:]

    @classmethod
    def from_string(self, value):
        value = value.lower()
        if (value == "info") or (value == "information"):
            return self._Information
        if (value == "warning"):
            return self._Warning
        if (value == "fatal"):
            return self._Fatal
        return None

# Skipping platter and instructions, they are not useful to programmers
from .blackbean import *
from .cilantro import *
from .guacamole import *
from .jalapeno import *
from .salsa import *


