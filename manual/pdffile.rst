.. module:: pdffile
   :synopsis: Native vector inclusion of PDF pages

.. _pdffile:

*****************************************
Module :mod:`pdffile`: PDF file inclusion
*****************************************

The :mod:`pdffile` module embeds pages from external PDF files directly as native
vector PDF Form XObjects when generating PDF output, preserving all vector paths,
embedded fonts, images, and resources:

.. code-block:: python

   from pyx import *

   c = canvas.canvas()
   c.insert(pdffile.pdffile(0, 0, "diagram.pdf", page=1, width=8))
   c.writePDFfile("output")


Class :class:`pdffile`
======================

.. class:: pdffile(x, y, filename, width=None, height=None, ratio=None, scale=None, align="bl", clip=1, translatebbox=1, bbox=None, page=1, kpsearch=0)

   Creates a canvas item representing page *page* of the external PDF file
   *filename* placed at ``(x, y)`` (in user units or PyX lengths). A point-based
   variant :class:`pdffile_pt` takes ``x``, ``y``, ``width``, and ``height`` in
   PostScript points.

   +------------------------+---------------------------------------------------------------+
   | Argument               | Description                                                   |
   +========================+===============================================================+
   | ``x``, ``y``           | Coordinates of the reference point at which the PDF page is   |
   |                        | placed.                                                       |
   +------------------------+---------------------------------------------------------------+
   | ``filename``           | Path to the PDF file, or an open binary file-like object.     |
   +------------------------+---------------------------------------------------------------+
   | ``width=None``         | Desired width of the graphic, or ``None`` to use its natural  |
   |                        | bounding-box width (or compute from *height* and *ratio*).    |
   |                        | Cannot be combined with *scale*.                              |
   +------------------------+---------------------------------------------------------------+
   | ``height=None``        | Desired height of the graphic, or ``None`` to use its natural |
   |                        | bounding-box height (or compute from *width* and *ratio*).    |
   |                        | Cannot be combined with *scale*.                              |
   +------------------------+---------------------------------------------------------------+
   | ``ratio=None``         | Aspect ratio ``width / height`` used when only *width* or     |
   |                        | only *height* is specified. If ``None``, the PDF page's       |
   |                        | original aspect ratio is preserved.                           |
   +------------------------+---------------------------------------------------------------+
   | ``scale=None``         | Uniform scaling factor, or ``None`` for no scaling. Cannot be |
   |                        | combined with *width*, *height*, or *ratio*.                  |
   +------------------------+---------------------------------------------------------------+
   | ``align="bl"``         | Two-character alignment string specifying how the PDF page is |
   |                        | aligned relative to ``(x, y)``. The first character sets      |
   |                        | vertical alignment (``"b"`` bottom, ``"c"`` center, ``"t"``   |
   |                        | top) and the second sets horizontal alignment (``"l"`` left,  |
   |                        | ``"c"`` center, ``"r"`` right).                               |
   +------------------------+---------------------------------------------------------------+
   | ``clip=1``             | When true (default), clips the included page to its bounding  |
   |                        | box.                                                          |
   +------------------------+---------------------------------------------------------------+
   | ``translatebbox=1``    | When true (default), translates the PDF page so that the      |
   |                        | lower-left corner of its bounding box sits at the reference   |
   |                        | origin before scaling and alignment.                          |
   +------------------------+---------------------------------------------------------------+
   | ``bbox=None``          | Optional :class:`bbox.bbox` overriding the page's ``CropBox`` |
   |                        | (or ``MediaBox`` if no ``CropBox`` is defined).               |
   +------------------------+---------------------------------------------------------------+
   | ``page=1``             | 1-based page number of the PDF file to include.               |
   +------------------------+---------------------------------------------------------------+
   | ``kpsearch=0``         | When true, locates *filename* via the TeX ``kpathsea`` file   |
   |                        | search system (:mod:`filelocator`).                           |
   +------------------------+---------------------------------------------------------------+

.. note::

   Because :class:`pdffile` embeds the page's content stream and resource
   dictionary directly as a PDF Form XObject, it is supported when writing PDF
   output (:meth:`canvas.canvas.writePDFfile` and
   :meth:`document.document.writePDFfile`).
