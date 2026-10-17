.. module:: svgfile
   :synopsis: Inclusion and parsing of Scalable Vector Graphics (SVG) files

.. _svgfile:

*****************************************
Module :mod:`svgfile`: SVG file inclusion
*****************************************

The :mod:`svgfile` module allows you to include external Scalable Vector Graphics
(SVG) files in a PyX :class:`canvas.canvas`, either by embedding the XML tree
directly in SVG output or by parsing the SVG vector paths and styles into a
native PyX canvas that can be exported to PostScript, EPS, PDF, and SVG:

.. code-block:: python

   from pyx import *

   c = canvas.canvas()
   c.insert(svgfile.svgfile(0, 0, "icon.svg", width=4, parsed=True))
   c.writePDFfile("output")


Class :class:`svgfile`
======================

.. class:: svgfile(x, y, filename, width=None, height=None, ratio=None, align="bl", parsed=False, resolution=96)

   Creates a canvas item representing the SVG file *filename* placed at ``(x, y)``
   (in user units or PyX lengths). A point-based variant :class:`svgfile_pt`
   takes ``x_pt``, ``y_pt``, ``width_pt``, and ``height_pt`` in PostScript
   points.

   +---------------------+---------------------------------------------------------------+
   | Argument            | Description                                                   |
   +=====================+===============================================================+
   | ``x``, ``y``        | Coordinates of the reference point at which the SVG graphic   |
   |                     | is placed.                                                    |
   +---------------------+---------------------------------------------------------------+
   | ``filename``        | Path to the SVG file, or an open binary file-like object.     |
   +---------------------+---------------------------------------------------------------+
   | ``width=None``      | Desired width of the graphic, or ``None`` to use its original |
   |                     | width (or compute from *height* and *ratio*).                 |
   +---------------------+---------------------------------------------------------------+
   | ``height=None``     | Desired height of the graphic, or ``None`` to use its         |
   |                     | original height (or compute from *width* and *ratio*).        |
   +---------------------+---------------------------------------------------------------+
   | ``ratio=None``      | Aspect ratio ``width / height`` used when only *width* or     |
   |                     | only *height* is specified. If ``None``, the SVG file's       |
   |                     | original aspect ratio is preserved.                           |
   +---------------------+---------------------------------------------------------------+
   | ``align="bl"``      | Two-character alignment string specifying how the SVG graphic |
   |                     | is aligned relative to ``(x, y)``. The first character sets   |
   |                     | vertical alignment (``"b"`` bottom, ``"c"`` center, ``"t"``   |
   |                     | top) and the second sets horizontal alignment (``"l"`` left,  |
   |                     | ``"c"`` center, ``"r"`` right).                               |
   +---------------------+---------------------------------------------------------------+
   | ``parsed=False``    | When ``False`` (default), embeds the raw SVG XML into SVG     |
   |                     | output. When ``True``, parses the SVG elements into a native  |
   |                     | PyX :class:`canvas.canvas` (stored in ``self.canvas``).       |
   +---------------------+---------------------------------------------------------------+
   | ``resolution=96``   | Assumed resolution in dots per inch (dpi) used to convert     |
   |                     | unitless SVG user coordinates (pixels) to physical units.     |
   +---------------------+---------------------------------------------------------------+


Unparsed vs. Parsed Mode
========================

Unparsed Mode (``parsed=False``)
--------------------------------

In unparsed mode, PyX reads only the root ``<svg>`` attributes (``width``,
``height``, and ``viewBox``) to determine the graphic's dimensions and copies the
SVG XML content directly into the output stream when writing an SVG file
(:meth:`canvas.canvas.writeSVGfile`). Unparsed mode supports the full SVG
specification (including filters, gradients, and CSS), but can only be written to
SVG output.

Parsed Mode (``parsed=True``)
-----------------------------

In parsed mode, PyX parses the SVG document into native PyX paths, styles,
transformations, and nested canvases stored in the instance's :attr:`canvas`
attribute. The parser supports ``<g>``, ``<svg>``, ``<path>`` (including full SVG
path data commands ``M``, ``L``, ``H``, ``V``, ``C``, ``S``, ``Q``, ``T``, ``A``,
``Z``), basic shapes (``<rect>``, ``<circle>``, ``<ellipse>``, ``<line>``,
``<polyline>``, ``<polygon>``), coordinate ``transform`` attributes, and stroke
and fill styles.

Parsed mode offers two major advantages:

1. **Cross-format output**: The included SVG graphic can be written to
   PostScript, EPS, PDF, and SVG alike.
2. **Direct path access**: Because ``self.canvas`` is a standard PyX
   :class:`canvas.canvas`, you can inspect or manipulate the parsed paths and
   sub-canvases directly in Python.


Coordinate Resolution (``resolution``)
======================================

Although SVG is a vector format, SVG files frequently specify ``width``,
``height``, or coordinates in unitless user coordinates (``px``) rather than
physical units (``pt``, ``mm``, ``cm``, ``in``). The *resolution* parameter
defines how many SVG user pixels correspond to one physical inch (72 PostScript
points):

* **96 dpi** (the default): Used by CSS, modern web browsers, and Inkscape 0.92+.
* **90 dpi**: Used by the original W3C SVG 1.1 specification and older versions
  of Inkscape.
* **72 dpi**: Used by Adobe Illustrator (where 1 user unit equals 1 PostScript
  point).

When an SVG file specifies physical units on its root ``width`` and ``height``
(as PyX's own SVG writer does) and ``parsed=True`` is used, the result is
completely independent of *resolution*.
