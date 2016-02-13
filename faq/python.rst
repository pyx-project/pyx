======
Python
======

.. _what_is_python:

What is Python?
===============

From `www.python.org <http://www.python.org>`_:

   Python is an *interpreted, interactive, object-oriented* programming
   language. It is often compared to Tcl, Perl, Scheme or Java.

   Python combines remarkable power with very clear syntax. It has modules,
   classes, exceptions, very high level dynamic data types, and dynamic typing.
   There are interfaces to many system calls and libraries, as well as to various
   windowing systems (X11, Motif, Tk, Mac, MFC). New built-in modules are easily
   written in C or C++. Python is also usable as an extension language for
   applications that need a programmable interface.

   The Python implementation is portable: it runs on many brands of UNIX, on 
   Windows, OS/2, Mac, Amiga, and many other platforms. If your favorite system 
   isn't listed here, it may still be supported, if there's a C compiler for it. 
   Ask around on `comp.lang.python <news:comp.lang.python>`_ – or just 
   try compiling Python yourself.
  
   The Python implementation is `copyrighted <http://www.python.org/doc/Copyright.html>`_
   but **freely usable and distributable, even for commercial use**.

Where can I learn more about Python?
====================================

The place to start is `www.python.org <http://www.python.org>`_ where you will
find plenty of information on Python including tutorials.

What do I need to import in order to use PyX?
=============================================

It is recommended to begin your Python code with::

   from pyx import *

when using PyX. This allows you for example to write simply ``graph.graphxy``
instead of ``pyx.graph.graphxy``. The following modules will be loaded:
``attr``, ``box``, ``bitmap``, ``canvas``, ``color``, ``connector``, ``deco``,
``deformer``, ``document``, ``epsfile``, ``graph``, ``path``, ``pattern``,
``style``, ``trafo``,  ``text``, and ``unit``.

For convenience, you might import specific objects of a module like in::

   from graph import graphxy

which allows you to write ``graphxy()`` instead of ``graph.graphxy()``.

All code segments in this document assume that the import line mentioned in the
first code snippet is present.

What is a raw string and why should I know about it when using PyX?
===================================================================

The backslash serves in standard Python strings to start an escape sequence.
For example ``\n`` corresponds to a newline character. On the other hand, TeX
and LaTeX, which do the typesetting in PyX, use the backslash to indicate the
start of a command. In order to avoid the standard interpretation, the string
should be marked as a raw string by prepending it by an ``r`` like in::

   c.text(0, 0, r"$\alpha\beta\gamma$")
