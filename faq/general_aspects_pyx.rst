======================
General aspects of PyX
======================

The name of the game
====================

Originally, the name PyX was constructed as a combination of **P**\ ostscript,
i.e. the first output format supported by PyX, P\ **y**\ thon, i.e. the language
in which PyX is written, and Te\ **X**, i.e. the program which PyX uses for
typesetting purposes.  Actually, the title of this question is a tribute to TeX
because it is taken from the first chapter of the TeX book [#texbook]_ where
the origin of the name TeX and its pronunciation are explained.

Despite the ties between TeX and PyX, their pronunciation is quite different.
According to the developers of PyX, it should be pronounced as [pʏks]. Please do
not pronounce it as [pʏx] or [pʏç].

.. _where_do_I_get_PyX:

Where do I get the latest version of PyX?
=========================================

The current release of PyX (as well as older ones) is freely available from
`https://pyx-project.org <https://pyx-project.org>`_ where also a
subversion repository with the latest patches can be found. In addition, PyX is
registered on the Python Package Index at
`https://pypi.python.org/pypi/PyX <https://pypi.python.org/pypi/PyX>`_ and can
be installed by ``easy_install`` and ``pip``. As PyX is hosted on PyPI, it can
be directly downloaded and installed by ``pip``. Please see the
`pip documentation <http://www.pip-installer.org/>`_ for details.

Possibly older versions of PyX are also available as package for various Linux
distributions: see, for instance,
`http://packages.debian.org/testing/python-pyx <http://packages.debian.org/testing/python-pyx>`_
for information on the PyX package in Debian GNU/Linux or
`http://packages.ubuntu.com/raring/python-pyx <http://packages.ubuntu.com/raring/python-pyx>`_
for Ubuntu.

PyX has no dependencies on other Python packages.

How can I determine the version of PyX running on my machine?
=============================================================

Start a python session (usually by typing ``python`` at the system prompt) and
then type the following two commands (``>>>`` is the python prompt)

>>> import pyx
>>> pyx.__version__

Note that there are two underscores before and after ``version``.

How can I access older versions of PyX?
=======================================

There are reasons which might make it necessary to use older versions of PyX.
If you are using Python 2 you will need PyX version 0.12.1 or earlier (see
:ref:`python_requirements`). Furthermore, as at present it is not guaranteed
that PyX is backward compatible, it may be desirable to access an older version
of PyX instead of adapting older code to a more recent version of PyX. In order
to do that, one needs the corresponding PyX package (see
:ref:`where_do_I_get_PyX` if you need to download it), which should be unpacked
below a directory, e.g.  ``/home/xyz/Python``,  where you want to keep the
various PyX versions.  This will result in a subdirectory with a name like
``PyX-0.14`` which contains the contents of the corresponding package. You
can then ask Python to first look in the appropriate directory before looking
for the current version of PyX by inserting the following code (appropriately
modified according to your needs) at the beginning of your program before
importing the PyX module::

   import sys
   sys.path.insert(0, "/home/xyz/Python/PyX-0.14")

Including appropriate lines even if the current version of PyX is used, might
turn out to be helpful when the current version has become an old version
(unless you have no difficulties determining the PyX version by looking at your
code).

If your operating system supports path expansion, you might use as an
alternative::

   import sys, os
   sys.path.insert(0, os.path.expanduser("~/Python/PyX-0.14"))

which will expand the tilde to your home directory.

Does PyX run under my favorite operating system?
================================================

Yes, if you have installed Python (:ref:`what_is_python`) and TeX
(:ref:`what_is_tex`). Both are available for a large variety of operating
systems so chances are pretty good that you will get PyX to work on your
system.

.. _python_requirements:

Under which versions of Python will PyX run?
============================================

Starting with version 0.13, PyX requires Python 3.2 or higher. If you still
need to run PyX with Python 2, you should use version 0.12.1 which is designed
to run with Python 2.3 up to 2.7.

The version of your Python interpreter can be determined by calling it with the
option ``-V``. Alternatively, you can simply start the interpreter and take a
look at the startup message. Note that there may be different versions of
Python installed on your system at the same time. The default Python version
need not be the same for all users.

Does PyX provide a GUI to view the produced image?
==================================================

No, PyX itself does not provide a means to view the produced image. The result
of a PyX run is an EPS (= Encapsulated PostScript) file, a PS (= PostScript)
file, a PDF (= Portable Document Format) file or a SVG (= Scalable Vector
Graphics) file, which can be viewed, printed or imported into other
applications.

There are several means of viewing PS and EPS files. A common way would be to
use ``ghostview`` which provides a user interface to the PostScript interpreter
``ghostscript``. More information about this software, which is available for a
variety of platforms, can be found at `http://www.cs.wisc.edu/~ghost/
<http://www.cs.wisc.edu/~ghost/>`_.  If you do not own a printer which is
capable of printing PostScript files directly, ``ghostscript`` may also be
useful to translate PS and EPS files produced by PyX into something your
printer will understand.

PDF files can be viewed by means of the ``Adobe Reader ®`` available from
`http://www.adobe.com/products/acrobat/readstep2.html
<http://www.adobe.com/products/acrobat/readstep2.html>`_. On systems running
X11, ``xpdf`` might be an alternative. It is available from
`http://www.foolabs.com/xpdf/ <http://www.foolabs.com/xpdf/>`_.

SVG files can be viewed by webbrowsers like Firefox available at
`https://www.mozilla.org/en-US/firefox
<https://www.mozilla.org/en-US/firefox>`_ or Chrome available at
`https://www.google.com/chrome/ <https://www.google.com/chrome/>`_.

If you want to do interactive development of a PyX graphics, you might consider
to use an IPython notebook (see :ref:`pyx_ipython_notebook`).

.. _pyx_ipython_notebook:

Will I be able to embed PyX graphics output into an IPython notebook?
=====================================================================

Yes, PyX canvas object and objects inheriting from the canvas class, in particular
graphs and text, can be embedded into an IPython notebook. Suppose you have a 
canvas object called ``c`` on which you have done some drawing. Then entering ``c``
in an IPython notebook cell and executing that cell will automatically produce
a SVG representation and embed it into the notebook. (Alternatively, also PNG
is available by means of ghostscript, but the default display_order of IPython
prefers SVG over PNG.) For more information on IPython and working with its
notebooks see `http://www.ipython.org/ <http://www.ipython.org/>`_.

I am a Gnuplot user and want to try PyX. Where can I get some help?
===================================================================

There exists a tutorial by Titus Winters which explains how to perform standard
Gnuplot tasks with \PyX. The tutorial can be found at
`http://www.cs.ucr.edu/~titus/pyxTutorial/
<http://www.cs.ucr.edu/~titus/pyxTutorial/>`_.

Where can I get help if my question is not answered in this FAQ?
================================================================

The PyX sources contain a reference manual which is also available online at
`https://pyx-project.org/manual/ <https://pyx-project.org/manual/>`_.
Furthermore, there exists a set of examples demonstrating various features of
PyX, which is available in the sources or can be browsed at
`https://pyx-project.org/examples.html
<https://pyx-project.org/examples.html>`_.  If the feature you are looking
for is among them, using the appropriate part of the example code or adapting
it for your purposes may help.

There is also a user discussion list about PyX which you can subscribe to at
`http://lists.sourceforge.net/lists/listinfo/pyx-user
<http://lists.sourceforge.net/lists/listinfo/pyx-user>`_.  The archive of the
discussion list is available at
`http://sourceforge.net/mailarchive/forum.php?forum_name=pyx-user
<http://sourceforge.net/mailarchive/forum.php?forum_name=pyx-user>`_.

Finally, it might be worth checking `https://pyx-project.org/pyxfaq.pdf
<https://pyx-project.org/pyxfaq.pdf>`_ for an updated version of this FAQ.

.. [#texbook] D.Knuth, *The TeX book* (Addison-Wesley, 1984) 
