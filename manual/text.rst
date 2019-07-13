
.. module:: text
   :synopsis: High-level interface for text output including a TeX/LaTeX
              interface

****
Text
****

Rationale
=========

The :mod:`text` module is used to create text output. It seamlessly integrates
Donald E. Knuths famous TeX typesetting engine\ [#]_. The module is a
high-level interface to an extensive stack of TeX and font related
functionality in PyX, whose details are way beyond this manual and completely
irrelevant for the typical PyX user. However, the basic concept should be
described briefly, as it provides important insights into essential properties
of the whole machinery.

PyX does not apply any limitations on the text submitted by the user. Instead
the text is directly passed to TeX. This has the implication, that the text to
be typeset should come from a trusted source or some special security measures
should be applied (see :ref:`chroot`). PyX just adds a light and transparent
wrapper using basic TeX functionality for later identification and output
extraction. This procedure enables full access to all TeX features and makes
PyX on the other hand dependent on the error handling provided by TeX. However,
a detailed and immediate control of the TeX output allows PyX to report
problems back to the user as they occur.

While we only talked about TeX so far (and will continue to do so in the rest
of this section), it is important to note that the coupling is not limited to
plain TeX. Currently, PyX can also use LaTeX for typesetting, and other TeX
variants could be added in the future. What PyX really depends on is the
ability of the typesetting program to generate DVI\ [#]_.

As soon as some text creation is requested or, even before that, a preamble
setting or macro definition is submitted, the TeX program is started as a
separate process. The input and output is bound to a :class:`SingleEngine`
instance. Typically, the process will be kept alive and will be reused for all
future typesetting requests until the end of the PyX process. However, there
are certain situations when the TeX program needs to be shutdown early, which
are be described in detail in the :ref:`texipc` section.

Whenever PyX sends some commands to the TeX interpreter, it adds an output
marker at the end, and waits for this output marker to be echoed in the TeX
output. All intermediate output is attributed to the commands just sent and
will be analysed for problems. This is done by :class:`texmessage` parsers.
Here, a problem could be logged to the PyX logger at warning level, thus
be reported to ``stderr`` by default. This happens for over- or underful boxes
or font warnings emitted by TeX. For other unknown problems (*i.e.* output not
handled by any of the given :class:`texmessage` parsers), a
:exc:`TexResultError` is raised, which creates a detailed error report
including the traceback, the commands submitted to TeX and the output returned
by TeX.

PyX wraps each text to be typeset in a TeX box and adds a shipout of this box
to the TeX code before forwarding it to TeX. Thus a page in the DVI file is
created containing just this output. Furthermore TeX is asked to output the box
extent. By that PyX will immediately know the size of the text without
referring to the DVI. This also allows faking the box size by TeX means, as you
would expect it.

Once the actual output is requested, PyX reads the content of the DVI file,
accessing the page related to the output in question. It then does all the
necessary steps to transform the DVI content to the requested output format,
like searching for virtual font files, font metrices, font mapping files, and
PostScript Type1 fonts to be used in the final output. Here a present
limitation has been mentioned: PyX presently can use PostScript Type1 fonts
only to generate text output. While this is a serious limitation, all the
default fonts in TeX are available in Type1 nowadays and current TeX
installations are alreadily configured to use them by default.


TeX interface
=============

.. autoclass:: SingleEngine
   :members: preamble, text, text_pt, texmessages_start_default, texmessages_end_default, texmessages_preamble_default, texmessages_run_default

.. autoclass:: SingleTexEngine

.. autoclass:: SingleLatexEngine
   :members: texmessages_docclass_default, texmessages_begindoc_default

The :class:`SingleEngine` classes described above do not handle restarts of the
interpreter when the actuall DVI result is required and is not available via
the :ref:`texipc` feature.

The :class:`MultiEngine` classes below are not derived from
:class:`SingleEngine` even though the provide the same functional interface
(:meth:`MultiEngine.preamble`, :meth:`MultiEngine.text`, and
:meth:`MultiEngine.text_pt`), but instead wrap a :class:`SingleEngine`
instance, and provide an automatic (or manual by the :meth:`MultiEngine.reset`
function) restart of the interpreter as required.

.. autoclass:: MultiEngine
   :members: preamble, text, text_pt, reset

.. autoclass:: TexEngine

.. autoclass:: LatexEngine

.. autoclass:: textextbox_pt
   :members: marker

.. unfortunately we cannot list left, right, etc. as members, as they will show up with the value None
.. see https://bitbucket.org/birkenfeld/sphinx/issue/904/autodocs-does-not-work-well-with-instance
.. we're using the undocumented autoinstanceattribute as a workaround

.. autoinstanceattribute:: textbox_pt.left
   :annotation:

.. autoinstanceattribute:: textbox_pt.right
   :annotation:

.. autoinstanceattribute:: textbox_pt.width
   :annotation:

.. autoinstanceattribute:: textbox_pt.height
   :annotation:

.. autoinstanceattribute:: textbox_pt.depth
   :annotation:


Module level functionality
==========================

The text module provides the public interface of the :class:`SingleEngine`
class by module level functions. For that, a module level :class:`MultiEngine`
is created and configured by the :func:`set` function. Each time the
:func:`set` function is called, the existing module level :class:`MultiEngine`
is replaced by a new one.

.. autodata:: defaulttextengine
   :annotation:

.. autodata:: preamble
   :annotation:

.. autodata:: text_pt
   :annotation:

.. autodata:: text
   :annotation:

.. autodata:: reset
   :annotation:

.. autofunction:: set

.. autofunction:: escapestring

.. only:: doctest

   .. autofunction:: remove_string
   .. autofunction:: remove_pattern
   .. autofunction:: index_all
   .. autofunction:: remove_nested_brackets


TeX output parsers
==================

While running TeX (and variants thereof) a variety of information is written to
``stdout`` like status messages, details about file access, and also warnings
and errors. PyX reads all the output and analyses it. Some of the output is
triggered as a direct response to the TeX input and is thus easy to understand
for PyX. This includes page output information, but also workflow control
information injected by PyX into the input stream. PyX uses it to check the
communication and typeset progress. All the other output is handled by a list
of :class:`texmessage` parsers, an individual set of functions applied to the
TeX output one after the other. Each of the function receives the TeX output as
a string and return it back (maybe altered). Such a function must perform one
of the following actions in response to the TeX output is receives:

 1. If it does not find any text in the TeX output it feals responsible for, it
    should just return the unchanged string.

 2. If it finds a text it is responsible for, and the message is just fine
    (doesn't need to be communicated to the user), it should just remove this
    text and return the rest of the TeX output.

 3. If the text should be communicated to the user, a message should be written
    the the pyx logger at warning level, thus being reported to the user on
    ``stderr`` by default. Examples are underfull and overfull box warnings or
    font warnings. In addition, the text should be removed as in 2 above.

 4. In case of an error, :exc:`TexResultError` should be raised.

This is rather uncommon, that the fourth option is taken directly. Instead,
errors can just be kept in the output as PyX considers unhandled TeX output
left after applying all given :class:`texmessage` parsers as an error. In
addition to the error message, information about the TeX in- and output will be
added to the exception description text by the :class:`SingleEngine` according
to the :class:`errordetail` setting. The following verbosity levels are
available:

.. autoclass:: errordetail
   :members:

.. autoexception:: TexResultError

To prevent any unhandled TeX output to be reported as an error,
:attr:`texmessage.warn` or :attr:`texmessage.ignore` can be used. To complete
the description, here is a list of all available :class:`texmessage` parsers:

.. autoclass:: texmessage
   :members:


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


.. _pyxgraphics:

Using the graphics-bundle with LaTeX
====================================

The packages in the LaTeX graphics bundle (``color.sty``, ``graphics.sty``,
``graphicx.sty``, ...) make extensive use of ``\\special`` commands. PyX
defines a clean set of such commands to fit the needs of the LaTeX graphics
bundle. This is done via the ``pyx.def`` driver file, which tells the graphics
bundle about the syntax of the ``\\special`` commands as expected by PyX. You
can install the driver file ``pyx.def`` into your LaTeX search path and add the
content of both files ``color.cfg`` and ``graphics.cfg`` to your personal
configuration files\ [#]_. After you have installed the ``cfg`` files, please
use the :mod:`text` module with unset ``pyxgraphics`` keyword argument which
will switch off a convenience hack for less experienced LaTeX users. You can
then import the LaTeX graphics bundle packages and related packages (e.g.
``rotating``, ...) with the option ``pyx``, e.g.
``\\usepackage[pyx]{color,graphicx}``. Note that the option ``pyx`` is only
available with unset *pyxgraphics* keyword argument and a properly installed
driver file. Otherwise, omit the specification of a driver when loading the
packages.

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


.. _config:

.. _pyxrc:

Configuration
=============

While the PyX configuration technically has nothing to do with the text module,
we mention it here as part of the text module since its main purpose is the
configuration of various aspects related to the typesetting of text.

PyX comes with reasonable defaults which should work out of the box on most TeX
installations. The default values are defined in the PyX source code itself and
are repeated in the system-wide config file in INI file format located at
``pyx/data/pyxrc``. This file also contains a description of each of the listed
config values and is read at PyX startup. Thus the system-wide configuration
can be adjusted by editing this file.

In addition, a user-specific configuration can be setup by a ``~/.pyxrc`` on
unix-like Systems (including OS X) or ``pyxrc`` in the directory defined by the
environment variable ``APPDATA`` on MS Windows. This user-specific
configuration will overwrite the system-wide settings.

Yet another configuration can be set by the environment variable ``PYXRC``. The
given file will is loaded on top of the configuration defined in the previous
steps.


.. _texipc:

TeX ipc mode
------------

For output generation of typeset text and to calculate the positions of markers
(see :meth:`textbox_pt.marker`) the DVI output of the TeX interpreter must be
read. In contrast, the text extent (:attr:`textbox_pt.left`,
:attr:`textbox_pt.right`, :attr:`textbox_pt.width`, :attr:`textbox_pt.height`,
:attr:`textbox_pt.depth`) is available without accessing the DVI output, as the
TeX interpreter is instructed by PyX to output it to stdout, which is read and
analysed at the typesetting step immediately.

Since TeX interpreters usually buffer the DVI output, the interpreter itself
needs to be terminated to get the DVI output. As :class:`MultiEngine` instances
can start a new interpreter when needed, this does not harm the functionality
and happens more or less unnoticable. Still it generates some penalty in terms
of execution speed, which can become huge for certain situations (alternation
between typesetting and marker access).

One of the effects of the ``texipc`` option available in almost all present TeX
interpreters is to flush the DVI output after each page. As PyX reads the DVI
output linearily, it can successfully read all output whithout stopping the TeX
interpreter. It is suggested to enable the ``texipc`` feature in the
system-wide configuration if available in the TeX interpreter being used.


.. _debug:

Debugging
---------

PyX provides various functionality to collect details about the typesetting
process. First off all, PyX reads the output generated by the TeX interpreter
while it processes the text provided by the user. If the given
:class:`texmessage` parsers do not validate this output, an
:exc:`TexResultError` is raised immediately. The verbosity of this output can
be adjusted by the :class:`errordetail` setting of the :class:`SingleEngine`.
This might help in some cases to identify an error in the text passed for
typesetting, but for more complicated problems, other help is required.

One possibility is to output the actual code passed to the TeX interpreter. For
that you can pass a file name or a file handle to the ``copyinput`` argument of
the :class:`SingleEngine`. You can then process the text by the TeX interpreter
yourself to reproduce the issue outside of PyX.

Similarily you can also save the log output from the TeX interpreter. For that
you need to pass a log file name (with the suffix ``.log``) in the ``usefiles``
argument (which is a list of files) of the :class:`SingleEngine`. This list of
files are saved and restored in the temporary directory used by the TeX
interpreter. While originally it is meant to share, for example, a ``.aux``
file between several runs (for which the temporary directory is different and
removed after each run), it can do the same for the ``.log`` file (where the
restore feature is needless, but does not harm). PyX takes care of the proper
``\jobname``, hence you can choose the filename arbitrarily with the exception
of the suffix, as the suffix is kept during the save and restore.

.. module:: pyx
   :synopsis: The PyX package

Still, all this might not help to fully understand the problem you're facing.
For example there might be situations, where it is not clear which TeX
interpreter is actually used (when several executables are available and the
path setup within the Python interpreter differs from the one used on the
shell). In those situations it might help to enable some additional logging
output created by PyX. PyX uses the logging module from the standard library
and logs to a logger named ``"pyx"``. By default, various information about
executing external programms and locating files will not be echoed, as it is
written at info level, but PyX provides a simple convenience function to enable
the output of this logging level. Just call the :func:`pyxinfo` function
defined on the PyX package before actually start using the package in your
Python program:

.. autofunction:: pyxinfo

.. _chroot:

Typesetting insecure text
-------------------------

When typesetting text it is passed to a TeX interpreter unchanged\ [#]_. This
is a security problem if the text does not come from a trusted source. While
full access to all typesetting features is not considered a problem, you should
bear in mind that TeX code can be used to read data from any other file
accessible to the TeX process. To surely prevent this process from accessing
any other data unrelated to the TeX installation, you can setup a chroot
environment for the TeX interpreter and configure PyX to use it. This can be
achieved by setting the ``chroot`` option and adjusting the TeX interpreter
call and the ``filelocator`` configuration in the ``pyxrc``.

UnicodeEngine
=============
.. module:: text
   :noindex:

.. autoclass:: UnicodeEngine

.. autoclass:: Text

.. autoclass:: StackedText

.. rubric:: Footnotes

.. [#] https://en.wikipedia.org/wiki/TeX

.. [#] https://en.wikipedia.org/wiki/Device_independent_file_format

.. [#] If you do not know what this is all about, you can just ignore this
       paragraph. But be sure that the ``pyxgraphics`` keyword argument is
       always set!

.. [#] The text is actually passed as an argument of a TeX command defined by
       PyX, but this is a minor detail and has no effect regarding possible
       attacks.

