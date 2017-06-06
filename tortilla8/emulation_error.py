#!/usr/bin/env python3

from enum import Enum

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
