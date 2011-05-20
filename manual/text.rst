
.. module:: text

***************************************
Module :mod:`text`: TeX/LaTeX interface
***************************************


Basic functionality
===================

The :mod:`text` module seamlessly integrates Donald E. Knuths famous TeX
typesetting engine into PyX. The basic procedure is:

* start a TeX/LaTeX instance as soon as a TeX/LaTeX preamble setting or a text
  creation is requested

* create boxes containing the requested text and shipout those boxes to the dvi
  file

* immediately analyse the TeX/LaTeX output for errors; the box extents are also
  contained in the TeX/LaTeX output and thus become available immediately

* when your TeX installation supports the ``ipc`` mode and PyX is configured to
  use it, the dvi output is also analysed immediately; alternatively PyX quits the
  TeX/LaTeX instance to read the dvi file once the output needs to be generated or
  marker positions are accessed

* Type1 fonts are used for the PostScript generation

Note that for using Type1 fonts an appropriate font mapping file has to be
provided. When your TeX installation is configured to use Type1 fonts by
default, the ``psfonts.map`` will contain entries for the standard TeX fonts
already. Alternatively, you may either look for ``updmap`` used by many TeX
distributions to create an appropriate font mapping file. You may also specify
one or several alternative font mapping files like ``psfonts.cmz`` in the global
``pyxrc`` or your local ``.pyxrc``. Finally you can also use the *fontmap*
keyword argument to a texrunners :meth:`text` method to use different mappings
within a single outout file.


TeX/LaTeX instances: the :class:`texrunner` class
=================================================


Instances of the class :class:`texrunner` are responsible for executing and
controling a TeX/LaTeX instance.


.. class:: texrunner(mode="tex", lfs="10pt", docclass="article", docopt=None, usefiles=[], fontmaps=config.get("text", "fontmaps", "psfonts.map"), waitfortex=config.getint("text", "waitfortex", 60), showwaitfortex=config.getint("text", "showwaitfortex", 5), texipc=config.getboolean("text", "texipc", 0), texdebug=None, dvidebug=0, errordebug=1, pyxgraphics=1, texmessagesstart=[], texmessagesdocclass=[], texmessagesbegindoc=[], texmessagesend=[], texmessagesdefaultpreamble=[], texmessagesdefaultrun=[])

   *mode* should the string ``tex`` or ``latex`` and defines whether TeX or LaTeX
   will be used. *lfs* specifies an ``lfs`` file to simulate LaTeX font size
   selection macros in plain TeX. PyX comes with a set of ``lfs`` files and a LaTeX
   script to generate those files. For *lfs* being ``None`` and *mode* equals
   ``tex`` a list of installed ``lfs`` files is shown.

   *docclass* is the document class to be used in LaTeX mode and *docopt* are the
   options to be passed to the document class.

   *usefiles* is a list of TeX/LaTeX jobname files. PyX will take care of the
   creation and storing of the corresponding temporary files. A typical use-case
   would be *usefiles=["spam.aux"]*, but you can also use it to access TeXs log and
   dvi file.

   *fontmaps* is a string containing whitespace separated names of font mapping
   files. *waitfortex* is a number of seconds PyX should wait for TeX/LaTeX to
   process a request. While waiting for TeX/LaTeX a PyX process might seem to do
   not perform any work anymore. To give some feedback to the user, a messages is
   issued each *waitfortex* seconds. The ``texipc`` flag indicates whether PyX
   should use the ``--ipc`` option of TeX/LaTeX for immediate dvi file access to
   increase the execution speed of certain operations. See the output of ``tex
   --help`` whether the option is available at your TeX installation.

   *texdebug* can be set to a filename to store the commands passed to TeX/LaTeX
   for debugging. The flag *dvidebug* enables debugging output in the dvi parser
   similar to ``dvitype``. *errordebug* controls the amount of information
   returned, when an texmessage parser raises an error. Valid values are ``0``,
   ``1``, and ``2``.

   *pyxgraphics* allows use LaTeXs graphics package without further configuration
   of ``pyx.def``.

   The TeX message parsers verify whether TeX/LaTeX could properly process its
   input. By the parameters *texmessagesstart*, *texmessagesdocclass*,
   *texmessagesbegindoc*, and *texmessagesend* you can set TeX message parsers to
   be used then TeX/LaTeX is started, when the ``documentclass`` command is issued
   (LaTeX only), when the ``\\begin{document}`` is sent, and when the TeX/LaTeX is
   stopped, respectively. The lists of TeX message parsers are merged with the
   following defaults: ``[texmessage.start]`` for *texmessagesstart*,
   ``[texmessage.load]`` for *texmessagesdocclass*, ``[texmessage.load,
   texmessage.noaux]`` for *texmessagesbegindoc*, and ``[texmessage.texend,
   texmessage.fontwarning]`` for *texmessagesend*.

   Similarily *texmessagesdefaultpreamble* and *texmessagesdefaultrun* take TeX
   message parser to be merged to the TeX message parsers given in the
   :meth:`preamble` and :meth:`text` methods. The *texmessagesdefaultpreamble* and
   *texmessagesdefaultrun* are merged with ``[texmessage.load]`` and
   ``[texmessage.loaddef, texmessage.graphicsload, texmessage.fontwarning,
   texmessage.boxwarning]``, respectively.

:class:`texrunner` instances provides several methods to be called by the user:


.. method:: texrunner.set(**kwargs)

   This method takes the same keyword arguments as the :class:`texrunner`
   constructor. Its purpose is to reconfigure an already constructed
   :class:`texrunner` instance. The most prominent use-case is to alter the
   configuration of the default :class:`texrunner` instance ``defaulttexrunner``
   which is created at the time of loading of the :mod:`text` module.

   The ``set`` method fails, when a modification cannot be applied anymore (e.g.
   TeX/LaTeX has already been started).


.. method:: texrunner.preamble(expr, texmessages=[])

   The :meth:`preamble` can be called prior to the :meth:`text` method only or
   after reseting a texrunner instance by :meth:`reset`. The *expr* is passed to
   the TeX/LaTeX instance not encapsulated in a group. It should not generate any
   output to the dvi file. In LaTeX preamble expressions are inserted prior to the
   ``\\begin{document}`` and a typical use-case is to load packages by
   ``\\usepackage``. Note, that you may use ``\\AtBeginDocument`` to postpone the
   immediate evaluation.

   *texmessages* are TeX message parsers to handle the output of TeX/LaTeX. They
   are merged with the default TeX message parsers for the :meth:`preamble` method.
   See the constructur description for details on the default TeX message parsers.


.. method:: texrunner.text(x, y, expr, textattrs=[], texmessages=[])

   *x* and *y* are the position where a text should be typeset and *expr* is the
   TeX/LaTeX expression to be passed to TeX/LaTeX.

   *textattrs* is a list of TeX/LaTeX settings as described below, PyX
   transformations, and PyX fill styles (like colors).

   *texmessages* are TeX message parsers to handle the output of TeX/LaTeX. They
   are merged with the default TeX message parsers for the :meth:`text` method. See
   the constructur description for details on the default TeX message parsers.

   The :meth:`text` method returns a :class:`textbox` instance, which is a special
   :class:`canvas` instance. It has the methods :meth:`width`, :meth:`height`, and
   :meth:`depth` to access the size of the text. Additionally the :meth:`marker`
   method, which takes a string *s*, returns a position in the text, where the
   expression ``\\PyXMarker{s}`` is contained in *expr*. You should not use ``@``
   within your strings *s* to prevent name clashes with PyX internal macros
   (although we don't the marker feature internally right now).

Note that for the outout generation and the marker access the TeX/LaTeX instance
must be terminated except when ``texipc`` is turned on. However, after such a
termination a new TeX/LaTeX instance is started when the :meth:`text` method is
called again.


.. method:: texrunner.reset(reinit=0)

   This method can be used to manually force a restart of TeX/LaTeX. The flag
   *reinit* will initialize the TeX/LaTeX by repeating the :meth:`preamble` calls.
   New :meth:`set` and :meth:`preamble` calls are allowed when *reinit* was not set
   only.


TeX/LaTeX attributes
====================


TeX/LaTeX attributes are instances to be passed to a :class:`texrunner`\ s
:meth:`text` method. They stand for TeX/LaTeX expression fragments and handle
dependencies by proper ordering.


.. class:: halign(boxhalign, flushhalign)

   Instances of this class set the horizontal alignment of a text box and the
   contents of a text box to be left, center and right for *boxhalign* and
   *flushhalign* being ``0``, ``0.5``, and ``1``. Other values are allowed as well,
   although such an alignment seems quite unusual.

Note that there are two separate classes :class:`boxhalign` and
:class:`flushhalign` to set the alignment of the box and its contents
independently, but those helper classes can't be cleared independently from each
other. Some handy instances available as class members:


.. attribute:: halign.boxleft

   Left alignment of the text box, *i.e.* sets *boxhalign* to ``0`` and doesn't set
   *flushhalign*.


.. attribute:: halign.boxcenter

   Center alignment of the text box, *i.e.* sets *boxhalign* to ``0.5`` and doesn't
   set *flushhalign*.


.. attribute:: halign.boxright

   Right alignment of the text box, *i.e.* sets *boxhalign* to ``1`` and doesn't
   set *flushhalign*.


.. attribute:: halign.flushleft

   Left alignment of the content of the text box in a multiline box, *i.e.* sets
   *flushhalign* to ``0`` and doesn't set *boxhalign*.


.. attribute:: halign.raggedright

   Identical to :attr:`flushleft`.


.. attribute:: halign.flushcenter

   Center alignment of the content of the text box in a multiline box, *i.e.* sets
   *flushhalign* to ``0.5`` and doesn't set *boxhalign*.


.. attribute:: halign.raggedcenter

   Identical to :attr:`flushcenter`.


.. attribute:: halign.flushright

   Right alignment of the content of the text box in a multiline box, *i.e.* sets
   *flushhalign* to ``1`` and doesn't set *boxhalign*.


.. attribute:: halign.raggedleft

   Identical to :attr:`flushright`.


.. attribute:: halign.left

   Combines :attr:`boxleft` and :attr:`flushleft`, *i.e.* ``halign(0, 0)``.


.. attribute:: halign.center

   Combines :attr:`boxcenter` and :attr:`flushcenter`, *i.e.* ``halign(0.5, 0.5)``.


.. attribute:: halign.right

   Combines :attr:`boxright` and :attr:`flushright`, *i.e.* ``halign(1, 1)``.

.. _fig_textvalign:
.. figure:: textvalign.*
   :align:  center

   valign example


.. class:: valign(valign)

   Instances of this class set the vertical alignment of a text box to be top,
   center and bottom for *valign* being ``0``, ``0.5``, and ``1``. Other values are
   allowed as well, although such an alignment seems quite unusual. See the left
   side of figure :ref:`fig_textvalign` for an example.

Some handy instances available as class members:


.. attribute:: valign.top

   ``valign(0)``


.. attribute:: valign.middle

   ``valign(0.5)``


.. attribute:: valign.bottom

   ``valign(1)``


.. attribute:: valign.baseline

   Identical to clearing the vertical alignment by :attr:`clear` to emphasise that
   a baseline alignment is not a box-related alignment. Baseline alignment is the
   default, *i.e.* no valign is set by default.


.. class:: parbox(width, baseline=top)

   Instances of this class create a box with a finite width, where the typesetter
   creates multiple lines in. Note, that you can't create multiple lines in
   TeX/LaTeX without specifying a box width. Since PyX doesn't know a box width, it
   uses TeXs LR-mode by default, which will always put everything into a single
   line. Since in a vertical box there are several baselines, you can specify the
   baseline to be used by the optional *baseline* argument. You can set it to the
   symbolic names :attr:`top`, :attr:`parbox.middle`, and :attr:`parbox.bottom`
   only, which are members of :class:`valign`. See the right side of figure
   :ref:`fig_textvalign` for an example.

Since you need to specify a box width no predefined instances are available as
class members.


.. class:: vshift(lowerratio, heightstr="0")

   Instances of this class lower the output by *lowerratio* of the height of the
   string *heigthstring*. Note, that you can apply several shifts to sum up the
   shift result. However, there is still a :attr:`clear` class member to remove all
   vertical shifts.

Some handy instances available as class members:


.. attribute:: vshift.bottomzero

   ``vshift(0)`` (this doesn't shift at all)


.. attribute:: vshift.middlezero

   ``vshift(0.5)``


.. attribute:: vshift.topzero

   ``vshift(1)``


.. attribute:: vshift.mathaxis

   This is a special vertical shift to lower the output by the height of the
   mathematical axis. The mathematical axis is used by TeX for the vertical
   alignment in mathematical expressions and is often usefull for vertical
   alignment. The corresponding vertical shift is less than :attr:`middlezero` and
   usually fits the height of the minus sign. (It is the height of the minus sign
   in mathematical mode, since that's that the mathematical axis is all about.)

There is a TeX/LaTeX attribute to switch to TeXs math mode. The appropriate
instances ``mathmode`` and ``clearmathmode`` (to clear the math mode attribute)
are available at module level.


.. data:: mathmode

   Enables TeXs mathematical mode in display style.

The :class:`size` class creates TeX/LaTeX attributes for changing the font size.


.. class:: size(sizeindex=None, sizename=None, sizelist=defaultsizelist)

   LaTeX knows several commands to change the font size. The command names are
   stored in the *sizelist*, which defaults to ``["normalsize", "large", "Large",
   "LARGE", "huge", "Huge", None, "tiny", "scriptsize", "footnotesize", "small"]``.

   You can either provide an index *sizeindex* to access an item in *sizelist* or
   set the command name by *sizename*.

Instances for the LaTeXs default size change commands are available as class
members:


.. attribute:: size.tiny

   ``size(-4)``


.. attribute:: size.scriptsize

   ``size(-3)``


.. attribute:: size.footnotesize

   ``size(-2)``


.. attribute:: size.small

   ``size(-1)``


.. attribute:: size.normalsize

   ``size(0)``


.. attribute:: size.large

   ``size(1)``


.. attribute:: size.Large

   ``size(2)``


.. attribute:: size.LARGE

   ``size(3)``


.. attribute:: size.huge

   ``size(4)``


.. attribute:: size.Huge

   ``size(5)``

There is a TeX/LaTeX attribute to create empty text boxes with the size of the
material passed in. The appropriate instances ``phantom`` and ``clearphantom``
(to clear the phantom attribute) are available at module level.


.. data:: phantom

   Skip the text in the box, but keep its size.


Using the graphics-bundle with LaTeX
====================================

The packages in the LaTeX graphics bundle (``color.sty``, ``graphics.sty``,
``graphicx.sty``, ...) make extensive use of ``\\special`` commands. PyX defines
a clean set of such commands to fit the needs of the LaTeX graphics bundle. This
is done via the ``pyx.def`` driver file, which tells the graphics bundle about
the syntax of the ``\\special`` commands as expected by PyX. You can install the
driver file ``pyx.def`` into your LaTeX search path and add the content of both
files ``color.cfg`` and ``graphics.cfg`` to your personal configuration files.
[#]_ After you have installed the ``cfg`` files, please use the :mod:`text`
module with unset ``pyxgraphics`` keyword argument which will switch off a
convenience hack for less experienced LaTeX users. You can then import the LaTeX
graphics bundle packages and related packages (e.g. ``rotating``, ...) with the
option ``pyx``, e.g. ``\\usepackage[pyx]{color,graphicx}``. Note that the option
``pyx`` is only available with unset *pyxgraphics* keyword argument and a
properly installed driver file. Otherwise, omit the specification of a driver
when loading the packages.

When you define colors in LaTeX via one of the color models ``gray``, ``cmyk``,
``rgb``, ``RGB``, ``hsb``, then PyX will use the corresponding values (one to
four real numbers). In case you use any of the ``named`` colors in LaTeX, PyX
will use the corresponding predefined color (see module ``color`` and the color
table at the end of the manual). The additional LaTeX color model ``pyx`` allows
to use a PyX color expression, such as ``color.cmyk(0,0,0,0)`` directly in
LaTeX. It is passed to PyX.

When importing Encapsulated PostScript files (``eps`` files) PyX will rotate,
scale and clip your file like you expect it. Other graphic formats can not be
imported via the graphics package at the moment.

For reference purpose, the following specials can be handled by PyX at the
moment:

``PyX:color_begin (model) (spec)``
   starts a color. ``(model)`` is one of ``gray``, ``cmyk``, ``rgb``, ``hsb``,
   ``texnamed``, or ``pyxcolor``. ``(spec)`` depends on the model: a name or some
   numbers

``PyX:color_end``
   ends a color.

``PyX:epsinclude file= llx= lly= urx= ury= width= height= clip=0/1``
   includes an Encapsulated PostScript file (``eps`` files). The values of ``llx``
   to ``ury`` are in the files' coordinate system and specify the part of the
   graphics that should become the specified ``width`` and ``height`` in the
   outcome. The graphics may be clipped. The last three parameters are optional.

``PyX:scale_begin (x) (y)``
   begins scaling from the current point.

``PyX:scale_end``
   ends scaling.

``PyX:rotate_begin (angle)``
   begins rotation around the current point.

``PyX:rotate_end``
   ends rotation.


TeX message parsers
===================


Message parsers are used to scan the output of TeX/LaTeX. The output is analysed
by a sequence of TeX message parsers. Each message parser analyses the output
and removes those parts of the output, it feels responsible for. If there is
nothing left in the end, the message got validated, otherwise an exception is
raised reporting the problem. A message parser might issue a warning when
removing some output to give some feedback to the user.


.. class:: texmessage()

   This class acts as a container for TeX message parsers instances, which are all
   instances of classes derived from :class:`texmessage`.

The following TeX message parser instances are available:


.. attribute:: texmessage.start

   Check for TeX/LaTeX startup message including scrollmode test.


.. attribute:: texmessage.noaux

   Ignore LaTeXs no-aux-file warning.


.. attribute:: texmessage.end

   Check for proper TeX/LaTeX tear down message.


.. attribute:: texmessage.load

   Accepts arbitrary loading of files without checking for details, *i.e.* accept
   ``(file ...)`` where ``file`` is an readable file.


.. attribute:: texmessage.loaddef

   Accepts arbitrary loading of ``fd`` files, *i.e.* accept ``(file.def)`` and
   ``(file.fd)`` where ``file.def`` or ``file.fd`` is an readable file,
   respectively.


.. attribute:: texmessage.graphicsload

   Accepts arbitrary loading of ``eps`` files, *i.e.* accept ``(file.eps)`` where
   ``file.eps`` is an readable file.


.. attribute:: texmessage.ignore

   Ignores everything (this is probably a bad idea, but sometimes you might just
   want to ignore everything).


.. attribute:: texmessage.allwarning

   Ignores everything but issues a warning.


.. attribute:: texmessage.fontwarning

   Issues a warning about font substitutions of the LaTeXs NFSS.


.. attribute:: texmessage.boxwarning

   Issues a warning on under- and overfull horizontal and vertical boxes.


.. class:: texmessagepattern(pattern, warning=None)

   This is a derived class of :class:`texmessage`. It can be used to construct
   simple TeX message parsers, which validate a TeX message matching a certain
   regular expression pattern *pattern*. When *warning* is set, a warning message
   is issued. Several of the TeX message parsers described above are implemented
   using this class.


The :attr:`defaulttexrunner` instance
=====================================


.. data:: defaulttexrunner

   The ``defaulttexrunner`` is an instance of :class:`texrunner`. It is created
   when the :mod:`text` module is loaded and it is used as the default texrunner
   instance by all :class:`canvas` instances to implement its :meth:`text` method.


.. function:: preamble(...)

   ``defaulttexrunner.preamble``


.. function:: text(...)

   ``defaulttexrunner.text``


.. function:: set(...)

   ``defaulttexrunner.set``


.. function:: reset(...)

   ``defaulttexrunner.reset``


Some internals on temporary files etc.
======================================

It is not totally obvious how TeX processes are supervised by PyX and why it's
done that way. However there are good reasons for it and the following
description is intended for people wanting and/or needing to understand how
temporary files are used by PyX. All others don't need to care.

Each time PyX needs to start a new TeX process, it creates a base file name for
temporary files associated with this process. This file name is used as
``\jobname`` by TeX. Since TeX does not handle directory names as part of
``\jobname``, the temporary files will be created in the current directory. The
PyX developers decided to not change the current directory at all, avoiding all
kind of issues with accessing files in the local directory, like for loading
graph data, LaTeX style files etc.

PyX creates a TeX file containing ``\relax`` only. It's only use is to set TeXs
``\jobname``. Immediately after processing ``\relax`` TeX falls back to stdin to
read more commands. PyX than uses ``stdin`` and ``stdout`` to avoid various
buffering issues which would occur when using files (or named pipes). By that
PyX can fetch TeX errors as soon as they occur while keeping the TeX process
running (i.e. in a waiting state) for further input. The size of the TeX output
is also availble immediately without fetching the ``dvi`` file created by TeX,
since PyX uses some TeX macros to output the extents of the boxes created for
the requested texts to ``stdout`` immediately. There is a TeX hack ``--ipc``
which PyX knows to take advantage of to fetch informations from the ``dvi`` file
immediately as well, but it's not available on all TeXinstallations. Thus this
feature is disabled by default and fetching informations from the ``dvi`` is
tried to be limited to those cases, where no other option exists. By that TeX
usually doesn't need to be started several times.

By default PyX will clean up all temporary files after TeX was stopped. However
the ``usefiles`` list allows for a renaming of the files from (and to, if
existing) the temporary ``\jobname`` (+ suffix) handled by PyX. Additionally,
since PyX does not write a useful TeX input file in a file and thus a
``usefiles=["example.tex"]`` would not contain the code actually passed to TeX,
the ``texdebug`` feature of the texrunner can be used instead to get a the full
input passed to TeX.

In case you need to control the position where the temporary files are created
(say, you're working on a read-only directory), the suggested solution is to
switch the current directory before starting with text processing in PyX (i.e.
an ``os.chdir`` at the beginning of your script will do fine). You than just
need to take care of specifying full paths when accessing data from your
original working directory, but that's intended and necessary for that case.

.. rubric:: Footnotes

.. [#] If you do not know what this is all about, you can just ignore this paragraph.
   But be sure that the *pyxgraphics* keyword argument is always set!

