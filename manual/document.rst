.. _document:

*********
Documents
*********

.. module:: document
   :synopsis: Multi-page documents, pages, paper formats, and output writers

While a :class:`canvas.canvas` represents an unbounded 2D drawing surface, the
:mod:`document` module places one or more canvases onto physical pages with
optional paper formats, margins, centering, rotation, and scaling, and writes the
resulting single- or multi-page document to PostScript, EPS, PDF, or SVG files.


Creating single- and multi-page documents
=========================================

For a single-page figure without specific page layout options, you can call
:meth:`canvas.canvas.writeEPSfile`, :meth:`canvas.canvas.writePDFfile`, or
:meth:`canvas.canvas.writeSVGfile` directly on a canvas. Internally, those
methods create a :class:`page` and a :class:`document` for you.

To create a multi-page PostScript or PDF document, or to control page layout
explicitly, wrap each :class:`canvas.canvas` in a :class:`page` and collect them
in a :class:`document`::

   from pyx import *

   d = document.document()

   for i in range(1, 4):
       c = canvas.canvas()
       c.text(0, 0, f"Page {i}", [text.halign.center])
       d.append(document.page(c, paperformat=document.paperformat.A4, centered=1))

   d.writePSfile("multipage")
   d.writePDFfile("multipage")


Class :class:`page`
===================

.. class:: page(canvas, pagename=None, paperformat=None, rotated=0, centered=1, fittosize=0, margin=1*unit.t_cm, bboxenlarge=1*unit.t_pt, bbox=None)

   Wraps a :class:`canvas.canvas` as a document page and configures its placement
   and bounding box.

   Parameters:

   - *canvas*: The :class:`canvas.canvas` containing the page graphics.
   - *pagename*: Optional string naming the page (written in the ``%%Page:`` DSC
     comment in PostScript output; defaults to the 1-based page number).
   - *paperformat*: Optional :class:`paperformat` instance (such as
     ``document.paperformat.A4`` or ``document.paperformat.Letter``) defining the
     physical dimensions of the page.
   - *rotated*: When set to ``1`` (or ``True``), rotates the page content by
     90 degrees counterclockwise (landscape orientation) on the specified
     *paperformat* (default ``0``).
   - *centered*: When set to ``1`` (default) and a *paperformat* is specified,
     centers the canvas bounding box on the paper.
   - *fittosize*: When set to ``1`` and a *paperformat* is specified, scales the
     canvas uniformly so that its bounding box fits within the paper dimensions
     minus *margin* on all four sides (default ``0``).
   - *margin*: Margin around the page content used when *fittosize* is enabled
     (default ``1 * unit.t_cm``).
   - *bboxenlarge*: Amount by which the automatically computed canvas bounding
     box is enlarged on all four sides to account for finite line widths at the
     edges of the figure (default ``1 * unit.t_pt``).
   - *bbox*: Explicit :class:`bbox.bbox` overriding the canvas's automatically
     computed bounding box (when specified, *bboxenlarge* is not applied).


Class :class:`paperformat`
==========================

.. class:: paperformat(width, height, name=None)

   Defines a paper size of the given *width* and *height* (PyX lengths) and
   optional PostScript media *name*.

   Predefined standard paper formats available as attributes of
   :class:`paperformat` are:

   ================== ============================ =========================
   Attribute          Dimensions                   Notes
   ================== ============================ =========================
   ``paperformat.A5`` 148.5 mm |times| 210 mm      ISO A5
   ``paperformat.A4`` 210 mm |times| 297 mm        ISO A4
   ``paperformat.A3`` 297 mm |times| 420 mm        ISO A3
   ``paperformat.A2`` 420 mm |times| 594 mm        ISO A2
   ``paperformat.A1`` 594 mm |times| 840 mm        ISO A1
   ``paperformat.A0`` 840 mm |times| 1188 mm       ISO A0
   ``paperformat.A0b`` 910 mm |times| 1370 mm      Oversized poster format
   ``paperformat.Letter`` 8.5 inch |times| 11 inch US Letter
   ``paperformat.Legal`` 8.5 inch |times| 14 inch  US Legal
   ================== ============================ =========================


Class :class:`document` and output writers
==========================================

.. class:: document(pages=None)

   Represents a sequence of :class:`page` instances.

   - *pages*: Optional initial list of :class:`page` instances (defaults to an
     empty list).

   .. method:: append(page)

      Appends a :class:`page` instance to the document.

   .. method:: writeEPSfile(file=None, title=None, stripfonts=True, textaspath=False, meshasbitmap=False, meshasbitmapresolution=300)

      Writes a single-page document as an Encapsulated PostScript (EPS) file.
      Raises :exc:`ValueError` if the document does not contain exactly one page.

   .. method:: writePSfile(file=None, writebbox=False, title=None, stripfonts=True, textaspath=False, meshasbitmap=False, meshasbitmapresolution=300)

      Writes the document as a PostScript (PS) file.

   .. method:: writePDFfile(file=None, title=None, author=None, subject=None, keywords=None, fullscreen=False, writebbox=False, compress=True, compresslevel=6, stripfonts=True, textaspath=False, meshasbitmap=False, meshasbitmapresolution=300)

      Writes the document as a PDF file.

   .. method:: writeSVGfile(file=None, textaspath=True, meshasbitmapresolution=300)

      Writes a single-page document as an SVG 1.1 file. Raises :exc:`ValueError`
      if the document does not contain exactly one page.

   .. method:: writetofile(filename, **kwargs)

      Determines the output writer from the extension of *filename* (``.eps``,
      ``.ps``, ``.pdf``, or ``.svg``) and writes the document with the given
      *kwargs*.


Writer options
--------------

In all output methods above, *file* may be:

- a filename string (the appropriate file extension ``.eps``, ``.ps``, ``.pdf``,
  or ``.svg`` is appended automatically if not already present),
- an open binary writable stream (such as an :class:`io.BytesIO` instance),
- ``"-"`` to write the binary output to standard output (``sys.stdout.buffer``),
  or
- ``None`` to derive the base filename automatically from the running script name
  ``sys.argv[0]`` (replacing ``.py`` with the appropriate extension).

.. note::

   For reproducible builds, both the PostScript and PDF writers honor the
   ``SOURCE_DATE_EPOCH`` environment variable when writing creation timestamps.

The keyword arguments controlling the output writers are:

- *stripfonts* (bool, default ``True``; EPS, PS, PDF): When ``True``, embedded
  Type 1 and OpenType fonts are subsetted so that only the glyphs actually used
  in the document are included, substantially reducing file size.
- *textaspath* (bool, default ``False`` for EPS/PS/PDF and ``True`` for SVG):
  When ``True``, all text glyphs are converted into vector outline paths instead
  of embedding font resources. In SVG output, this defaults to ``True`` so that
  SVG files render identically in all browsers and vector editors without
  requiring SVG font support.
- *meshasbitmap* (bool, default ``False``; EPS, PS, PDF): When ``True``, Gouraud-shaded
  triangular meshes (:mod:`mesh`, used e.g. by :class:`graph.style.surface`) are
  rasterized into a bitmap image instead of using native PostScript Level 3 / PDF
  shading objects. This avoids rendering artifacts and large file sizes in some
  viewers and printers. (In SVG output, meshes are always rendered as bitmaps.)
- *meshasbitmapresolution* (int, default ``300``): Resolution in DPI used when
  rasterizing meshes into bitmaps.
- *writebbox* (bool, default ``False``; PS, PDF): In PostScript output, writes
  ``%%BoundingBox`` and ``%%PageBoundingBox`` comments even when a paper format
  is used. In PDF output, writes a ``/CropBox`` entry alongside the ``/MediaBox``
  when a paper format is used.
- *title* (str or ``None``; EPS, PS, PDF): Document title metadata.
- *author*, *subject*, *keywords* (str or ``None``; PDF): Document metadata
  strings written to the PDF ``/Info`` dictionary.
- *fullscreen* (bool, default ``False``; PDF): Requests that the PDF viewer open
  the document in full-screen presentation mode (``/PageMode /FullScreen``).
- *compress* (bool, default ``True``; PDF) and *compresslevel* (int, default
  ``6``; PDF): Controls ``zlib``/Flate compression of PDF content and font
  streams.
