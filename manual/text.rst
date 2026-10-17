.. module:: text
   :synopsis: High-level interface for text typesetting using TeX/LaTeX or direct Unicode font rendering

.. _text:

****
Text
****

Overview and Quick Start
========================

The :mod:`text` module provides PyX's text typesetting facilities. Depending on
your needs and environment, PyX offers two complementary text rendering engines:

* **TeX and LaTeX engines** (:class:`TexEngine` and :class:`LatexEngine`):
  The default typesetting backend. PyX runs Donald E. Knuth's TeX [#]_ or LaTeX
  as a background process, giving you full access to TeX's mathematical
  typesetting, macro expansion, kerning, ligatures, and LaTeX packages.
* **Direct Unicode font engine** (:class:`UnicodeEngine`):
  A lightweight, pure-Python text engine that renders Unicode strings directly
  using Type 1 or OpenType/TrueType (``.otf``/``.ttf``) fonts without invoking an
  external TeX process.

Basic Usage
-----------

In most scripts, you do not create a text engine directly. Instead, you call
:meth:`canvas.canvas.text` (which delegates to the module-level default engine)
and configure the global engine via :func:`text.set` and :func:`text.preamble`:

.. code-block:: python

   from pyx import *

   # Switch the default engine from plain TeX to LaTeX and load packages
   text.set(cls=text.LatexEngine)
   text.preamble(r"\usepackage{amsmath}")

   c = canvas.canvas()
   c.text(0, 0, r"$\int_{-\infty}^{\infty} e^{-x^2}\,dx = \sqrt{\pi}$",
          [text.halign.center, text.vshift.mathaxis, text.size.Large])
   c.writePDFfile("gauss")

Calling :func:`text.text` (or :meth:`canvas.canvas.text`) returns a
:class:`textextbox_pt` (or :class:`textbox`) instance—a canvas-like object that
knows its exact typographic width, height, and depth, and can be aligned,
transformed, or queried for its bounding box before or after insertion into a
canvas.


Architecture of the TeX Interface
=================================

Understanding how PyX communicates with TeX/LaTeX is helpful when customizing
preambles, handling TeX warnings, or optimizing scripts that typeset many text
fragments.

1. **Direct TeX execution**:
   PyX does not parse or restrict TeX syntax itself; instead, it passes your
   text directly to an external ``tex`` or ``latex`` process wrapped in a thin
   TeX macro for box measurement and shipout. Because arbitrary TeX primitives
   can read files on disk, untrusted user input should only be typeset inside a
   restricted environment (see :ref:`chroot`).

2. **Persistent background process**:
   As soon as the first preamble command or :func:`text` call is issued, PyX
   launches the TeX interpreter as a child process bound to a
   :class:`SingleEngine` instance. This single process stays alive across
   subsequent :func:`text` calls so that TeX only initializes once and macro
   definitions persist.

3. **Immediate box metrics and output parsing**:
   For each text fragment, PyX places the typeset material into a TeX box,
   instructs TeX to print the box's exact ``width``, ``height``, and ``depth`` to
   ``stdout`` followed by a unique end-of-command marker, and ships the box out
   to its own page in the DVI [#]_ file. PyX immediately parses ``stdout`` using
   a chain of :class:`texmessage` parsers:

   * Expected status messages are stripped silently.
   * Overfull/underfull box notices and font warnings are logged via the
     ``"pyx"`` logger at ``WARNING`` level.
   * Any unrecognized output left over after all :class:`texmessage` parsers
     have run raises a :exc:`TexResultError` with a detailed diagnostic report.

   Because TeX reports box dimensions immediately on ``stdout``, PyX knows the
   exact dimensions of every text box (`width`, `height`, `depth`) right away—even
   before reading the DVI file.

4. **DVI reading and font embedding**:
   When final output (EPS, PS, PDF, or SVG) is written—or when a coordinate
   marker inside the text box is queried via :meth:`textextbox_pt.marker`—PyX
   reads the corresponding page from the DVI file, resolves virtual fonts
   (``.vf``), TeX font metrics (``.tfm``), and font map files (``psfonts.map`` /
   ``pdftex.map``), and embeds the required Type 1 font outlines directly into
   the output document.


TeX and LaTeX Engines
=====================

PyX separates the low-level management of a single TeX process
(:class:`SingleEngine`) from the high-level engine interface
(:class:`MultiEngine`) that automatically restarts TeX if needed (for instance,
when the DVI file must be flushed and read mid-script without :ref:`texipc`).

Single-Process Engines
----------------------

.. autoclass:: SingleEngine
   :members: preamble, text, text_pt, texmessages_start_default, texmessages_end_default, texmessages_preamble_default, texmessages_run_default

.. autoclass:: SingleTexEngine

.. autoclass:: SingleLatexEngine
   :members: texmessages_docclass_default, texmessages_begindoc_default

Multi-Run Wrapper Engines
-------------------------

:class:`MultiEngine` and its subclasses (:class:`TexEngine` and
:class:`LatexEngine`) wrap one or more :class:`SingleEngine` instances. They
provide the same public methods (:meth:`~MultiEngine.preamble`,
:meth:`~MultiEngine.text`, and :meth:`~MultiEngine.text_pt`), while
automatically starting a fresh :class:`SingleEngine` (and replaying all
accumulated preamble commands) whenever the previous process had to be closed to
read its DVI file.

.. autoclass:: MultiEngine
   :members: preamble, text, text_pt, reset

.. autoclass:: TexEngine

.. autoclass:: LatexEngine

Text Boxes and Coordinate Markers
---------------------------------

Every call to ``text()`` or ``text_pt()`` on a TeX/LaTeX engine returns a
:class:`textextbox_pt` instance:

.. autoclass:: textextbox_pt
   :members: marker, left, right, width, height, depth

.. tip::

   **Using PyX Markers inside TeX**:
   You can record the exact position of any point inside a TeX expression by
   inserting ``\PyXMarker{id}`` in your TeX string and later calling
   ``tb.marker("id")`` on the returned text box to obtain its ``(x, y)``
   coordinates on the canvas:

   .. code-block:: python

      tb = c.text(0, 0, r"$y = \PyXMarker{rhs}\underbrace{a x^2 + b x + c}$")
      mx, my = tb.marker("rhs")


Module-Level Functions
======================

For convenience, the :mod:`text` module maintains a default module-level text
engine (:data:`defaulttextengine`, which defaults to a :class:`TexEngine`
instance) and exposes its methods as module-level functions. Calling
:func:`text.set` replaces :data:`defaulttextengine` with a newly configured
engine.

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


TeX Output Parsers and Error Handling
=====================================

When TeX or LaTeX runs, it writes status banners, file load notices, box
warnings, and error messages to ``stdout``. After stripping its own internal page
and extent markers, PyX passes the remaining output string through a sequence of
:class:`texmessage` parser callables. Each parser inspects the output string and
performs one of four actions:

1. **Unrelated output**: Return the string unchanged so subsequent parsers can
   inspect it.
2. **Expected/harmless message**: Strip the recognized message and return the
   remaining string.
3. **Warning**: Log a warning via the ``"pyx"`` logger (printed to ``stderr`` by
   default, e.g. for overfull/underfull boxes or font substitutions), strip the
   message, and return the remaining string.
4. **Error**: Raise :exc:`TexResultError` (or leave the error text in the
   returned string—any non-empty text remaining after all parsers have run
   automatically triggers a :exc:`TexResultError`).

The amount of context included in a :exc:`TexResultError` exception is
controlled by :class:`errordetail`:

.. autoclass:: errordetail
   :members:

.. autoexception:: TexResultError

To accept unknown TeX output without raising an error, you can append
:attr:`texmessage.warn` or :attr:`texmessage.ignore` to the ``texmessages_*``
lists. The built-in message parsers are:

.. autoclass:: texmessage
   :members:


Text Attributes (Alignment, Parboxes, Math Mode, Font Size)
===========================================================

Text attributes are passed in a list to :func:`text.text` or
:meth:`canvas.canvas.text` alongside transformations (:class:`trafo.trafo`),
colors (:class:`color.color`), and decorators. They generate appropriate
TeX/LaTeX wrapper fragments or geometric alignments and automatically resolve
ordering dependencies.

Horizontal Alignment (:class:`halign`)
--------------------------------------

.. class:: halign(boxhalign, flushhalign)

   Controls both the horizontal alignment of the text box relative to its
   reference point ``(x, y)`` (*boxhalign*) and the horizontal alignment of text
   lines inside a multi-line :class:`parbox` (*flushhalign*). Standard values are
   ``0`` (left), ``0.5`` (center), and ``1`` (right), though arbitrary floating
   point numbers are permitted.

   The separate helper classes :class:`boxhalign` and :class:`flushhalign` allow
   setting box placement and line flushing independently. Predefined instances
   are provided as class attributes on :class:`halign`:

   .. attribute:: halign.boxleft

      Left-aligns the text box at the reference point (``boxhalign=0``, leaves
      *flushhalign* unchanged).

   .. attribute:: halign.boxcenter

       Horizontally centers the text box at the reference point
       (``boxhalign=0.5``, leaves *flushhalign* unchanged).

   .. attribute:: halign.boxright

      Right-aligns the text box at the reference point (``boxhalign=1``, leaves
      *flushhalign* unchanged).

   .. attribute:: halign.flushleft
   .. attribute:: halign.raggedright

      Left-aligns (ragged-right) lines inside a :class:`parbox`
      (``flushhalign=0``, leaves *boxhalign* unchanged).

   .. attribute:: halign.flushcenter
   .. attribute:: halign.raggedcenter

      Centers lines inside a :class:`parbox` (``flushhalign=0.5``, leaves
      *boxhalign* unchanged).

   .. attribute:: halign.flushright
   .. attribute:: halign.raggedleft

      Right-aligns (ragged-left) lines inside a :class:`parbox`
      (``flushhalign=1``, leaves *boxhalign* unchanged).

   .. attribute:: halign.left

      Combines :attr:`boxleft` and :attr:`flushleft` (``halign(0, 0)``).

   .. attribute:: halign.center

      Combines :attr:`boxcenter` and :attr:`flushcenter` (``halign(0.5, 0.5)``).

   .. attribute:: halign.right

      Combines :attr:`boxright` and :attr:`flushright` (``halign(1, 1)``).

Vertical Alignment (:class:`valign`) and Multi-Line Boxes (:class:`parbox`)
---------------------------------------------------------------------------

.. _fig_textvalign:
.. figure:: textvalign.*
   :align: center

   Vertical alignment of single-line text boxes using :class:`valign` (left) and
   baseline selection in multi-line :class:`parbox` boxes (right).

.. class:: valign(valign)

   Sets the vertical alignment of the text box relative to its overall bounding
   height (from bottom of depth to top of height): ``0`` aligns at the top,
   ``0.5`` at the vertical center, and ``1`` at the bottom. See the left side of
   figure :ref:`fig_textvalign`.

   .. attribute:: valign.top

      Aligns the top of the text box with the reference point (``valign(0)``).

   .. attribute:: valign.middle

      Vertically centers the text box at the reference point (``valign(0.5)``).

   .. attribute:: valign.bottom

      Aligns the bottom of the text box with the reference point (``valign(1)``).

   .. attribute:: valign.baseline

      Clears any box-based vertical alignment (identical to ``valign.clear``) so
      that the text box is aligned along its typographic baseline (the default).

.. class:: parbox(width, baseline=top)

   Typesets text in a vertical paragraph box of fixed *width* (a PyX length or
   number in user units), enabling automatic line wrapping and explicit line
   breaks (``\\``). By default, TeX typesets in LR (left-to-right) mode on a
   single line unless a :class:`parbox` attribute is provided.

   Because a multi-line paragraph has multiple baselines, *baseline* selects
   which baseline serves as the reference baseline of the box:

   * :attr:`parbox.top` (default): the baseline of the first line.
   * :attr:`parbox.middle`: the vertical center of the paragraph box.
   * :attr:`parbox.bottom`: the baseline of the last line.

   See the right side of figure :ref:`fig_textvalign`.

Vertical Shifts (:class:`vshift`)
---------------------------------

.. class:: vshift(lowerratio, heightstr="0")

   Lowers the text box relative to its baseline by *lowerratio* times the height
   of the character(s) in *heightstr* (default ``"0"``). Multiple :class:`vshift`
   attributes accumulate; use ``vshift.clear`` to remove all vertical shifts.

   .. attribute:: vshift.bottomzero

      ``vshift(0)`` — no vertical shift (aligns at the baseline of ``"0"``).

   .. attribute:: vshift.middlezero

      ``vshift(0.5)`` — lowers the text by half the height of ``"0"``.

   .. attribute:: vshift.topzero

      ``vshift(1)`` — lowers the text by the full height of ``"0"``.

   .. attribute:: vshift.mathaxis

      Lowers the text by the height of TeX's mathematical axis (the vertical
      center of math operators such as minus signs and fraction bars). This is
      used by default for graph axis labels and titles.

Math Mode, Font Sizes, and Phantom Text
---------------------------------------

.. data:: mathmode

   Typesets the text in TeX display math mode (``$\displaystyle ...$``). Use
   ``clearmathmode`` to clear this attribute.

.. class:: size(sizeindex=None, sizename=None, sizelist=defaultsizelist)

   Applies a TeX/LaTeX font size command from *sizelist*
   (default ``["normalsize", "large", "Large", "LARGE", "huge", "Huge", None,
   "tiny", "scriptsize", "footnotesize", "small"]``). You can specify either an
   integer *sizeindex* into *sizelist* or a command name *sizename*.

   Predefined instances corresponding to standard LaTeX font sizes are available
   as class attributes:

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

.. data:: phantom

   Typesets an invisible box that occupies the exact width, height, and depth of
   the given text without drawing any glyphs (equivalent to TeX's ``\phantom``).
   Use ``clearphantom`` to clear this attribute.


.. _UnicodeEngine:

UnicodeEngine: Direct Font Rendering without TeX
================================================

.. module:: text
   :noindex:

When you only need simple labels or want to use system OpenType/TrueType
(``.otf``/``.ttf``) or Type 1 fonts without invoking an external TeX process,
you can use :class:`UnicodeEngine`.

.. code-block:: python

   from pyx import *

   text.set(text.UnicodeEngine, size=12)

   c = canvas.canvas()
   c.text(0, 0, "Direct Unicode text rendering", [color.rgb.blue])

.. class:: UnicodeEngine(font=_marker, size=10)

   A pure-Python text engine that renders Unicode strings directly using Type 1
   (:class:`font.T1font`) or OpenType/TrueType (:class:`font.OTFfont`) fonts.

   * *font*: Font instance (defaults to ``T1font.from_fontname("cmr10")``).
   * *size*: Base font size in PostScript points (default ``10``).

   .. method:: text_pt(x_pt, y_pt, text, textattrs=[], texmessages=[], fontmap=None, singlecharmode=False)
   .. method:: text(x, y, text, textattrs=[], **kwargs)

      Typesets *text* (which may be a string, :class:`Text`, :class:`StackedText`,
      :class:`MultiEngineText`, or a list thereof) at ``(x, y)`` and returns a
      :class:`unicodetextbox_pt` instance. Supports :data:`mathmode`,
      :class:`trafo.trafo_pt`, and :class:`style.fillstyle` (such as
      :class:`color.color`) attributes in *textattrs*.

.. class:: Text(text, scale=1, shift=0)

   Wraps a string *text* for :class:`UnicodeEngine` with a relative font *scale*
   factor and a vertical baseline *shift* (in units of the unscaled text size).
   This is useful for superscripts and subscripts when using
   :class:`UnicodeEngine`, for example
   ``["10", text.Text("-3", scale=0.7, shift=0.4)]``.

.. class:: StackedText(texts, frac=False, align=0)

   Stacks a sequence of *texts* vertically for :class:`UnicodeEngine` with
   horizontal alignment *align* (``0`` for left, ``0.5`` for center, ``1`` for
   right) and optional fraction bar *frac* (when ``len(texts) == 2``).

.. class:: MultiEngineText(tex, unicode)

   Holds two representations of a text fragment: *tex* (passed when a TeX/LaTeX
   engine is active) and *unicode* (passed when :class:`UnicodeEngine` is
   active). PyX's axis texters use :class:`MultiEngineText` so that exponential
   tick labels work seamlessly with both TeX engines and :class:`UnicodeEngine`.


.. _pyxgraphics:

Using the LaTeX ``graphics`` Bundle with PyX
============================================

The packages in the standard LaTeX graphics bundle (``color``, ``graphicx``,
``rotating``, etc.) rely on driver-specific ``\special`` commands emitted into
the DVI file. PyX ships with its own driver file ``pyx.def`` (located in
``pyx/data/def/pyx.def``) that translates LaTeX color, scaling, rotation, and EPS
inclusion commands into native PyX canvas operations.

By default, :class:`SingleLatexEngine` enables ``pyxgraphics=True``, which
automatically injects ``pyx.def`` so you can write
``\usepackage{color,graphicx}`` in your LaTeX preamble without specifying a
driver option. If you install ``pyx.def`` into your local TeX tree and configure
``color.cfg`` / ``graphics.cfg`` [#]_, you can set ``pyxgraphics=False`` and load
packages explicitly with ``\usepackage[pyx]{color,graphicx}``.

Supported LaTeX Color Models and Specials
-----------------------------------------

When you define or use colors in LaTeX via the ``gray``, ``cmyk``, ``rgb``,
``RGB``, or ``hsb`` models, or via ``named`` colors, PyX maps them directly to
the corresponding :mod:`color` classes and predefined named colors (see appendix
:ref:`colorname`). In addition, the ``pyx`` color model lets you pass any PyX
color expression directly from LaTeX, such as
``\textcolor[pyx]{color.cmyk.PineGreen}{colored text}``.

For developer reference, PyX's DVI reader interprets the following ``\special``
commands generated by ``pyx.def``:

``PyX:color_begin (model) (spec)``
   Pushes a color onto the graphics state. ``(model)`` is one of ``gray``,
   ``cmyk``, ``rgb``, ``hsb``, ``texnamed``, or ``pyxcolor``, and ``(spec)``
   contains the model parameters or name.

``PyX:color_end``
   Restores the previous color state.

``PyX:epsinclude file= llx= lly= urx= ury= width= height= clip=0/1``
   Includes an Encapsulated PostScript (``.eps``) file scaled, positioned, and
   optionally clipped according to the specified bounding box coordinates.

``PyX:scale_begin (x) (y)`` / ``PyX:scale_end``
   Starts and ends coordinate scaling relative to the current DVI reference
   point.

``PyX:rotate_begin (angle)`` / ``PyX:rotate_end``
   Starts and ends coordinate rotation (in degrees) around the current DVI
   reference point.


.. _config:
.. _pyxrc:

Configuration and Debugging
===========================

As described in :ref:`intro`, PyX reads its system-wide defaults from
``pyx/data/pyxrc``, followed by user-level settings in ``~/.pyxrc`` (or
``%APPDATA%\pyxrc`` on Windows) and any file referenced by the ``PYXRC``
environment variable. Most options in ``[general]`` and ``[text]`` configure how
PyX locates TeX files and runs the TeX/LaTeX interpreter.

.. _texipc:

TeX IPC Mode
------------

To read the actual glyph positions or ``\PyXMarker`` coordinates of a text box,
PyX must read the DVI page written by TeX. However, standard TeX buffers its DVI
output until the TeX process terminates. When ``texipc`` is disabled (the
default), accessing a marker or writing a canvas forces :class:`MultiEngine` to
close the running TeX process so the DVI file is flushed, and then spawn a new
TeX process if further text is typeset afterward.

Most modern TeX distributions support the ``--ipc`` command-line option, which
flushes the DVI file after every ``\shipout``. Enabling ``texipc = 1`` in the
``[text]`` section of your ``pyxrc`` allows PyX to read DVI pages on the fly
without terminating TeX, dramatically speeding up scripts that alternate between
typesetting text and querying marker positions.

.. _debug:

Debugging TeX Typesetting Issues
--------------------------------

PyX provides several tools for diagnosing TeX errors and environment problems:

1. **Error verbosity** (:class:`errordetail`):
   Pass ``errordetail=text.errordetail.full`` to :func:`text.set` to include the
   full TeX session transcript and input commands whenever a
   :exc:`TexResultError` is raised.
2. **Saving the TeX input stream** (``copyinput``):
   Pass a filename or writable file object as ``copyinput="debug.tex"`` to
   :func:`text.set` to record the exact TeX code PyX sends to the interpreter so
   you can run ``tex`` or ``latex`` on it manually.
3. **Preserving ``.log`` and ``.aux`` files** (``usefiles``):
   Each TeX process runs in a temporary working directory that is deleted on
   exit. Passing ``usefiles=["myjob.log", "myjob.aux"]`` to :func:`text.set`
   copies those files into and out of the temporary directory (matching PyX's
   internal ``\jobname`` while preserving the file extension), allowing you to
   inspect the full TeX ``.log`` file or share ``.aux`` files across runs.
4. **Enabling ``INFO`` logging** (:func:`pyx.pyxinfo`):

   .. module:: pyx
      :synopsis: The PyX package
      :noindex:

   PyX logs all external command executions and file lookups to the standard
   Python logger ``"pyx"`` at ``INFO`` level. Calling :func:`pyx.pyxinfo` at the
   top of your script attaches a stream handler that prints these messages to
   ``stderr``:

   .. autofunction:: pyxinfo

.. _chroot:

Typesetting Untrusted Text
--------------------------

Because TeX has primitives that can read arbitrary files accessible to the user
running the script (and, in misconfigured environments, execute shell commands),
never pass untrusted user input directly to TeX without isolation [#]_. If you
use PyX in a web service or multi-user environment, you can run TeX inside a
``chroot`` jail by configuring the ``chroot`` option, the TeX executable command,
and the ``filelocator`` paths in ``pyxrc``.


.. rubric:: Footnotes

.. [#] https://en.wikipedia.org/wiki/TeX

.. [#] https://en.wikipedia.org/wiki/Device_independent_file_format

.. [#] Unless you specifically need custom driver configuration in your local
       TeX tree, leave ``pyxgraphics=True`` (the default) and omit the ``[pyx]``
       package option in ``\usepackage{color,graphicx}``.

.. [#] Although PyX wraps user text inside an internal TeX macro argument,
       catcode changes and macro expansion still allow arbitrary TeX primitives
       to be executed.
