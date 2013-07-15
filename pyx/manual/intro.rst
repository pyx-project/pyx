
.. _intro:

************
Introduction
************

PyX is a Python package for the creation of vector graphics. As such it readily
allows one to generate encapsulated PostScript files by providing an abstraction
of the PostScript graphics model.  Based on this layer and in combination with
the full power of the Python language itself, the user can just code any
complexity of the figure wanted. PyX distinguishes itself from other similar
solutions by its TeX/LaTeX interface that enables one to make direct use of the
famous high quality typesetting of these programs.

A major part of PyX on top of the already described basis is the provision of
high level functionality for complex tasks like 2d plots in publication-ready
quality.


Organisation of the PyX package
===============================

The PyX package is split into several modules, which can be categorised in the
following groups

+----------------------------------+------------------------------------------+
| Functionality                    | Modules                                  |
+==================================+==========================================+
| basic graphics functionality     | :mod:`canvas`, :mod:`path`, :mod:`deco`, |
|                                  | :mod:`style`, :mod:`color`, and          |
|                                  | :mod:`connector`                         |
+----------------------------------+------------------------------------------+
| text output via TeX/LaTeX        | :mod:`text` and :mod:`box`               |
+----------------------------------+------------------------------------------+
| linear transformations and units | :mod:`trafo` and :mod:`unit`             |
+----------------------------------+------------------------------------------+
| graph plotting functionality     | :mod:`graph` (including submodules) and  |
|                                  | :mod:`graph.axis` (including submodules) |
+----------------------------------+------------------------------------------+
| EPS file inclusion               | :mod:`epsfile`                           |
+----------------------------------+------------------------------------------+

These modules (and some other less import ones) are imported into the module
namespace by using   ::

   from pyx import *

at the beginning of the Python program.  However, in order to prevent namespace
pollution, you may also simply use ``import pyx``. Throughout this manual, we
shall always assume the presence of the above given import line.

