.. _intro:

************
Introduction
************


What is PyX?
============

PyX is a Python package for creating publication-quality graphics in PostScript,
PDF, and SVG formats. It combines a clean Pythonic abstraction of the PostScript
drawing model with seamless TeX/LaTeX integration and native Type 1 and OpenType
font handling.

The design of PyX is guided by several core principles:

- **Programmatic precision**: Figures are described in Python code rather than
  assembled interactively in a GUI. This makes complex or data-driven figures
  reproducible, parameterizable, and easy to maintain alongside scientific or
  engineering code.
- **Unified drawing primitives**: Geometric shapes are represented as math-aware
  PostScript-like paths (:mod:`path` and :mod:`normpath`) or MetaPost-like
  spline paths (:mod:`metapost.path`) that support intersections, arc-length
  parameterization, tangents, curvatures, and geometric deformations
  (:mod:`deformer`).
- **Composable canvases and attributes**: Graphics primitives are collected on
  hierarchically nestable canvases (:mod:`canvas`) and styled through a typed,
  composable attribute system (:mod:`attr`, :mod:`style`, :mod:`deco`,
  :mod:`color`, :mod:`pattern`, :mod:`trafo`).
- **First-class typography**: Text can be typeset through an interactive TeX or
  LaTeX subprocess (:class:`text.TexEngine`, :class:`text.LatexEngine`) so that
  mathematical formulas and document fonts match your manuscript, or rendered
  directly via :class:`text.UnicodeEngine` using Type 1 or OpenType fonts without
  invoking TeX.
- **Modular plotting architecture**: High-level components such as 2D and 3D
  graphs (:mod:`graph`) and axes (:mod:`graph.axis`) are built directly on top
  of PyX's path, canvas, and text primitives, with clear interfaces for custom
  data sources, plot styles, axis partitioners, texters, and painters.


A first example
===============

To see how these concepts fit together, consider a minimal script that draws a
stroked red rectangle and typesets a centered mathematical expression inside it::

   from pyx import *

   c = canvas.canvas()
   c.stroke(path.rect(0, 0, 4, 2), [style.linewidth.Thick, color.rgb.red])
   c.text(2, 1, r"$\int_{-\infty}^\infty e^{-x^2}\,\mathrm{d}x = \sqrt{\pi}$",
          [text.halign.center, text.valign.middle])

   c.writeEPSfile("hello")
   c.writePDFfile("hello")
   c.writeSVGfile("hello")

Here ``canvas.canvas()`` creates an drawing surface, ``path.rect(0, 0, 4, 2)``
constructs a rectangular path of width 4 cm and height 2 cm (using PyX's default
user unit of centimeters), and the attribute list ``[style.linewidth.Thick,
color.rgb.red]`` specifies how the path is stroked. Finally, ``writeEPSfile``,
``writePDFfile``, and ``writeSVGfile`` write the canvas to ``hello.eps``,
``hello.pdf``, and ``hello.svg``.


Organization of this manual
===========================

This manual is organized both as a progressive guide for new users and as a
complete technical reference for experienced PyX users and developers:

- **Basic graphics** (:ref:`graphics`, :ref:`path`, :ref:`metapost`,
  :ref:`deformer`, :ref:`canvas`, :ref:`document`): Introduces the drawing model,
  the attribute system (:mod:`attr`), stroke and fill styles (:mod:`style`), path
  decorators (:mod:`deco`), path construction and normalized path geometry
  (:mod:`path`, :mod:`normpath`, :mod:`metapost`), path deformers
  (:mod:`deformer`), canvases (:mod:`canvas`), and multi-page documents
  (:mod:`document`).
- **Text** (:ref:`text`): Covers text typesetting with TeX, LaTeX, and
  :class:`text.UnicodeEngine`, text alignment and sizing attributes, color and
  transformation handling, markers, and diagnostics.
- **Plotting** (:ref:`graph`, :ref:`axis`): Describes 2D and 3D data plotting,
  data sources (:mod:`graph.data`), plotting styles (:mod:`graph.style`), graph
  keys (:mod:`graph.key`), and the axis system (:mod:`graph.axis`,
  :mod:`graph.axis.parter`, :mod:`graph.axis.texter`, :mod:`graph.axis.painter`,
  :mod:`graph.axis.rater`, :mod:`graph.axis.tick`).
- **Boxes and Connectors** (:ref:`box`, :ref:`connector`): Explains aligned
  polygonal and rectangular boxes and the connectors linking them.
- **External graphics and bitmaps** (:ref:`epsfile`, :ref:`pdffile`,
  :ref:`svgfile`, :ref:`bitmap`): Covers embedding EPS, PDF, SVG, and raster
  bitmap images.
- **Basic classes and modules** (:ref:`bbox`, :ref:`color`, :ref:`pattern`,
  :ref:`unit`, :ref:`trafo`): Documents bounding boxes, color spaces and
  gradients, fill patterns, the multi-scale unit system, and affine
  transformations.
- **Appendix**: Provides visual catalogs of predefined colors, gradients, path
  styles, arrows, and internal utility helpers.

.. note::

   Throughout this manual, classes and functions that accept geometric coordinates
   or lengths in PyX units (which support unit scaling and explicit units such as
   ``2*unit.t_cm``) often have a companion class or method ending in ``_pt``
   (such as :class:`path.line_pt` or :meth:`canvas.canvas.text_pt`). These
   ``_pt`` variants take numerical values directly in PostScript points
   (1 pt = 1/72 inch) and bypass unit conversion for performance-critical
   internal and developer code.


Installation
============

Prerequisites
-------------

PyX requires Python 3. When using the default TeX/LaTeX text engines
(:class:`text.TexEngine` and :class:`text.LatexEngine`), a working TeX
installation (such as TeX Live or MiKTeX) with Type 1 fonts is required. If you
use :class:`text.UnicodeEngine` exclusively with shipped or local Type 1 /
OpenType fonts, PyX can generate PostScript, PDF, and SVG output without invoking
an external TeX interpreter.

To include or manipulate raster images beyond uncompressed PNM or JPEG files,
the Python Imaging Library (`Pillow <https://python-pillow.org/>`_) is optional
but recommended.


Installing PyX
--------------

The easiest way to install the latest release of PyX is via ``pip``::

   pip install pyx

To install PyX from a source distribution or a Git checkout, run::

   pip install .

from the top-level directory of the source tree.

By default, PyX installs as a pure Python package and locates TeX files and
fonts by invoking the ``kpsewhich`` command-line tool. For faster file lookup in
environments with frequent font searches, PyX also includes an optional C
extension module, ``pykpathsea``, which links directly against ``libkpathsea``.
You can enable building ``pykpathsea`` by editing ``setup.cfg`` prior to
installation and specifying the appropriate include and library paths for your
TeX distribution.


.. _config:

Configuration and file location
===============================

Runtime configuration (``pyxrc``)
---------------------------------

PyX reads its runtime configuration from a sequence of INI-style configuration
files:

1. The built-in default configuration ``pyx/data/pyxrc`` shipped with PyX.
2. A user-specific configuration file: ``~/.pyxrc`` on Unix/macOS systems, or
   ``%APPDATA%\pyxrc`` on Windows.
3. Any configuration file specified by the environment variable ``PYXRC``.

Settings in later files override earlier ones. The configuration is divided into
three sections:

``[general]``
   - ``space`` (default ``SPACE``): Whitespace-separated list options in
     ``pyxrc`` use this token to represent literal space characters inside list
     items.

``[text]``
   - ``defaulttextengine`` (default ``TexEngine``): Default text engine class
     initialized in :mod:`text` (``TexEngine``, ``LatexEngine``, or
     ``UnicodeEngine``).
   - ``tex`` (default ``tex``): Command (and optional whitespace-separated
     arguments) used to start the plain TeX interpreter.
   - ``latex`` (default ``latex``): Command (and optional whitespace-separated
     arguments) used to start the LaTeX interpreter.
   - ``psfontmaps`` (default ``psfonts.map``): Whitespace-separated list of font
     mapping files used for PostScript and SVG output.
   - ``pdffontmaps`` (default ``pdftex.map``): Whitespace-separated list of font
     mapping files used for PDF output.
   - ``wait`` (default ``60``): Maximum time in seconds to wait for a response
     from the TeX/LaTeX subprocess before raising a timeout error.
   - ``showwait`` (default ``5``): Interval in seconds between progress warnings
     logged while waiting for TeX/LaTeX (set to ``0`` to disable).
   - ``texipc`` (default ``0``): Boolean flag enabling TeX's ``--ipc`` option for
     reading DVI pages before TeX terminates.
   - ``chroot`` and ``tmpdir``: Optional path overrides for running TeX inside a
     chroot environment or a custom temporary directory.

``[filelocator]``
   - ``methods`` (default ``local internal pykpathsea kpsewhich``):
     Whitespace-separated list of file lookup methods tried in order when PyX
     searches for fonts, metrics, headers, or figures:

     - ``local``: Searches the current working directory.
     - ``internal``: Searches the ``pyx/data`` package resources shipped with PyX
       (such as built-in ``.lfs`` files, ``pyxrc``, and standard AFM/Type 1 files).
     - ``recursivedir``: Recursively searches the directories listed in the
       ``recursivedir`` option of ``[filelocator]``.
     - ``ls-R``: Searches TeX ``ls-R`` filename databases listed in the ``ls-R``
       option of ``[filelocator]``.
     - ``pykpathsea``: Uses the compiled ``pykpathsea`` C extension if available.
     - ``kpsewhich``: Calls the ``kpsewhich`` executable (customizable via the
       ``kpsewhich`` option in ``[filelocator]``).
     - ``locate``: Calls the system ``locate`` command (customizable via the
       ``locate`` option in ``[filelocator]``).


Developer interface: :mod:`config` and logging
----------------------------------------------

.. module:: config
   :synopsis: Configuration and file location

For PyX developers, the :mod:`config` module provides programmatic access to configuration settings, resource discovery, and subprocess execution:

.. function:: get(section, option, default=...)
              getint(section, option, default=...)
              getfloat(section, option, default=...)
              getboolean(section, option, default=...)
              getlist(section, option, default=...)

   Retrieve an option from *section* as a string, integer, float, boolean, or
   whitespace-split list of strings. If *default* is provided, it is returned
   whenever the section or option is not present in the configuration.

.. function:: open(filename, formats, ascii=False)

   Locate and open *filename* by trying the configured ``[filelocator]`` methods
   for the given list of :class:`format` specifications. Returns a binary stream
   by default, or a text stream with ``ascii`` encoding and ``surrogateescape``
   error handling when *ascii* is ``True``. Raises :exc:`IOError` if the file
   cannot be found.

   Standard file formats defined on :class:`format` are:

   - ``format.tfm`` (``.tfm``)
   - ``format.afm`` (``.afm``)
   - ``format.pfm`` (``.pfm``)
   - ``format.fontmap`` (``.map``)
   - ``format.pict`` (``.eps``, ``.epsi``)
   - ``format.tex_ps_header`` (PostScript headers and ``.enc`` encoding files)
   - ``format.type1`` (``.pfa``, ``.pfb``)
   - ``format.vf`` (``.vf``)
   - ``format.dvips_config``
   - ``format.ttf`` (``.ttf``, ``.ttc``, ``.TTF``, ``.TTC``, ``.dfont``)
   - ``format.t42`` (``.t42``, ``.T42``)
   - ``format.otf`` (``.otf``)
   - ``format.pyx`` (internal PyX data files)

PyX uses Python's standard :mod:`logging` module to report warnings and
diagnostic information:

- ``logging.getLogger("pyx")``: Main logger used for warnings across all PyX
  modules.
- ``logging.getLogger("pyx.execute")``: Logs external subprocess invocations
  (such as ``tex``, ``latex``, ``kpsewhich``, or ``gs``) at the ``INFO`` level.
- ``logging.getLogger("pyx.filelocator")``: Logs every file lookup and its
  resolved path at the ``INFO`` level.

To inspect which external commands and font files PyX uses during a run, enable
``INFO`` logging in your script::

   import logging
   logging.basicConfig(level=logging.INFO)
