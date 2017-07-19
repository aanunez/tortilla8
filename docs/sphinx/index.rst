tortilla8's docs
================

Summary goes here

Using tortilla8
===============

Stuff goes here

Code
====

.. automodule:: tortilla8.salsa
   :members:

.. automodule:: tortilla8.guacamole
   :members:

.. automodule:: tortilla8.blackbean
   :members:

.. automodule:: tortilla8.cilantro
   :members:

.. automodule:: tortilla8.jalapeno
   :members:

.. toctree::
   :hidden:
   :maxdepth: 2


Desgin - Curses
===============

[UniCurses](https://pdcurses.sourceforge.io/) was not used for Platter as the syntax differs on Posix and Windows implimentations. Unicruses on Windows uses [PDCurses](https://pdcurses.sourceforge.io/). Instructions on installing follow, but, to be clear,**support is not included**.
```
:: Use pip to install UniCurses
pip install https://sourceforge.net/projects/pyunicurses/files/latest/download?source=typ_redirect
```
You will also need the dlls for both PDCurses and SDL; [PDCurses](https://pdcurses.sourceforge.io/) distributes both source, pre-built dlls, and cofig files for this. Similarly, [SDL](https://www.libsdl.org/download-1.2.php) pre-built dlls, source, and configs can be easily found online. SDL 1.2 is the recomended version for UniCurses 1.2, the latests avaialbe version as of writing, and was used for testing while UniCurses was being used.

Design - Why Tkinter
====================

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

