.. module:: epsfile
   :synopsis: Inclusion of Encapsulated PostScript (EPS) files

.. _epsfile:

*****************************************
Module :mod:`epsfile`: EPS file inclusion
*****************************************

The :mod:`epsfile` module allows you to embed external Encapsulated PostScript
(EPS) files into a PyX :class:`canvas.canvas`, with full control over position,
scaling, alignment, and clipping:

.. code-block:: python

   from pyx import *

   c = canvas.canvas()
   c.insert(epsfile.epsfile(0, 0, "figure.eps", width=6, align="cc"))
   c.writeEPSfile("output")


Class :class:`epsfile`
======================

.. class:: epsfile(x, y, filename, width=None, height=None, scale=None, align="bl", clip=1, translatebbox=True, bbox=None, kpsearch=False)

   Creates a canvas item representing the external EPS file *filename* placed at
   ``(x, y)`` (in user units or PyX lengths).

   +--------------------------+---------------------------------------------------------------+
   | Argument                 | Description                                                   |
   +==========================+===============================================================+
   | ``x``, ``y``             | Coordinates of the reference point at which the EPS graphic   |
   |                          | is placed.                                                    |
   +--------------------------+---------------------------------------------------------------+
   | ``filename``             | Path to the EPS file.                                         |
   +--------------------------+---------------------------------------------------------------+
   | ``width=None``           | Desired width of the graphic, or ``None`` to use its natural  |
   |                          | bounding-box width (or scale proportionally from *height*).   |
   |                          | Cannot be combined with *scale*.                              |
   +--------------------------+---------------------------------------------------------------+
   | ``height=None``          | Desired height of the graphic, or ``None`` to use its natural |
   |                          | bounding-box height (or scale proportionally from *width*).   |
   |                          | Cannot be combined with *scale*.                              |
   +--------------------------+---------------------------------------------------------------+
   | ``scale=None``           | Uniform scaling factor, or ``None`` for no scaling. Cannot be |
   |                          | combined with *width* or *height*.                            |
   +--------------------------+---------------------------------------------------------------+
   | ``align="bl"``           | Two-character alignment string specifying how the graphic is  |
   |                          | aligned relative to ``(x, y)``. The first character sets      |
   |                          | vertical alignment (``"b"`` bottom, ``"c"`` center, ``"t"``   |
   |                          | top) and the second sets horizontal alignment (``"l"`` left,  |
   |                          | ``"c"`` center, ``"r"`` right).                               |
   +--------------------------+---------------------------------------------------------------+
   | ``clip=1``               | When true (default), clips the EPS graphic to its bounding    |
   |                          | box.                                                          |
   +--------------------------+---------------------------------------------------------------+
   | ``translatebbox=True``   | When true (default), translates the EPS graphic so that the   |
   |                          | lower-left corner of its bounding box sits at the reference   |
   |                          | origin before scaling and alignment.                          |
   +--------------------------+---------------------------------------------------------------+
   | ``bbox=None``            | Optional :class:`bbox.bbox` overriding the ``%%BoundingBox``  |
   |                          | / ``%%HiResBoundingBox`` comments read from the EPS file.     |
   +--------------------------+---------------------------------------------------------------+
   | ``kpsearch=False``       | When true, locates *filename* via the TeX ``kpathsea`` file   |
   |                          | search system (:mod:`config`).                                |
   +--------------------------+---------------------------------------------------------------+

Output Format Compatibility
---------------------------

* **PostScript and EPS output**: The EPS file is embedded directly as vector
  PostScript inside a ``BeginDocument`` / ``EndDocument`` wrapper.
* **PDF output**: Because PDF viewers cannot execute arbitrary PostScript code,
  PyX automatically rasterizes the included EPS file to a PNG bitmap using
  Ghostscript (:meth:`canvas.canvas.pipeGS`) when writing PDF output. To include
  vector graphics natively in PDF output, convert the file to PDF and use the
  :mod:`pdffile` module instead.
