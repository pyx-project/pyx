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
According to the developers of PyX, it should be pronounced as pyks. Please do
not pronounce it as pyx or pyç.

.. todo::

   Replace y in IPA by the correct sign (U+028F).

.. _where_do_I_get_PyX:

Where do I get the latest version of PyX?
=========================================

The current release of PyX (as well as older ones) is freely available from
`pyx.sourceforge.net <http://pyx.sourceforge.net>`_ where also a
subversion repository with the latest patches can be found. Possibly older
versions of PyX are also available as package for various Linux distributions:
see, for instance,  `http://packages.debian.org/testing/python/python-pyx.html
<http://packages.debian.org/testing/python/python-pyx.html>`_ for information
on the \PyX package in Debian GNU/Linux,
`http://packages.gentoo.org/ebuilds/?pyx-0.7.1
<http://packages.gentoo.org/ebuilds/?pyx-0.7.1>`_ for a Gentoo Linux ebuild,
and `http://www.novell.com/products/linuxpackages/professional/python-pyx.html
<http://www.novell.com/products/linuxpackages/professional/python-pyx.html>`_
for the PyX package in the SUSE LINUX professional distribution.

How can I determine the version of PyX running on my machine?
=============================================================

Start a python session (usually by typing ``python`` at the system prompt) and
then type the following two commands (``>>>`` is the python prompt)

>>> import pyx
>>> pyx.__version__

Note that there are two underscores before and after ``version``.

How can I access older versions of PyX?
=======================================

As at present it is not guaranteed that PyX is backward compatible, it may be
desirable to access an older version of PyX instead of adapting older code to
the current version of PyX. In order to do that, one needs the corresponding
PyX package (see :ref:`where_do_I_get_PyX` if you need to download it), which
should be unpacked below a directory, e.g.  ``/home/xyz/Python``,  where you
want to keep the various PyX versions.  This will result in a subdirectory with
a name like ``PyX-0.11.1`` which contains the contents of the corresponding
package. You can then ask Python to first look in the appropriate directory
before looking for the current version of PyX by inserting the following code
(appropriately modified according to your needs) at the beginning of your
program before importing the PyX module::

   import sys
   sys.path.insert(0, "/home/xyz/Python/PyX-0.11.1")

Including appropriate lines even if the current version of PyX is used, might
turn out to be helpful when the current version has become an old version
(unless you have no difficulties determining the PyX version by looking at your
code).

If your operating system supports path expansion, you might use as an
alternative::

   import sys, os
   sys.path.insert(0, os.path.expanduser("~/Python/PyX-0.11.1"))

which will expand the tilde to your home directory.

Does PyX run under my favorite operating system?
================================================

Yes, if you have installed Python :ref:`what_is_python`) and TeX
(:ref:`what_is_tex`). Both are available for a large variety of operating
systems so chances are pretty good that you will get PyX to work on your
system.

Under which versions of Python will PyX run?
============================================

PyX is supposed to work with Python 2.1 and above. However, most of the
development takes place under the current production version of Python (2.4.1
by the time of this writing) and thus PyX is better tested with this version.
On the other hand, the examples and tests are verified to run with Python 2.1
and above using the latest bugfix releases. PyX will not work with earlier
Python versions due to missing language features. 

The version of your Python interpreter can be determined by calling it with the
option ``-V``. Alternatively, you can simply start the interpreter and take a
look at the startup message. Note that there may be different versions of
Python installed on your system at the same time. The default Python version
need not be the same for all users.

Does PyX provide a GUI to view the produced image?
==================================================

No, PyX itself does not provide a means to view the produced image. The result
of a PyX run is an EPS (= Encapsulated PostScript) file, a PS (= PostScript)
file or a PDF (= Portable Document Format) file, which can be viewed, printed
or imported into other applications.

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

I am a Gnuplot user and want to try PyX. Where can I get some help?
===================================================================

There exists a tutorial by Titus Winters which explains how to perform standard
Gnuplot tasks with \PyX. The tutorial can be found at
`http://www.cs.ucr.edu/~titus/pyxTutorial/
<http://www.cs.ucr.edu/~titus/pyxTutorial/>`_.

Where can I get help if my question is not answered in this FAQ?
================================================================

The PyX sources contain a reference manual which is also available online at
`http://pyx.sourceforge.net/manual/ <http://pyx.sourceforge.net/manual/>`_.
Furthermore, there exists a set of examples demonstrating various features of
PyX, which is available in the sources or can be browsed at
`http://pyx.sourceforge.net/examples.html
<http://pyx.sourceforge.net/examples.html>`_.  If the feature you are looking
for is among them, using the appropriate part of the example code or adapting
it for your purposes may help.

There is also a user discussion list about PyX which you can subscribe to at
`http://lists.sourceforge.net/lists/listinfo/pyx-user
<http://lists.sourceforge.net/lists/listinfo/pyx-user>`_.  The archive of the
discussion list is available at
`http://sourceforge.net/mailarchive/forum.php?forum_name=pyx-user
<http://sourceforge.net/mailarchive/forum.php?forum_name=pyx-user>`_.

Finally, it might be worth checking `http://pyx.sourceforge.net/pyxfaq.pdf
<http://pyx.sourceforge.net/pyxfaq.pdf>`_ for an updated version of this FAQ.

.. [#texbook] D.Knuth, *The TeX book* (Addison-Wesley, 1984) 
