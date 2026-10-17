.. module:: bitmap
   :synopsis: Bitmap image containers, JPEG/PNM readers, and canvas placement

.. _bitmap:

*******
Bitmaps
*******

Introduction
============

Although PyX is primarily designed for scalable vector graphics, the
:mod:`bitmap` module provides full support for embedding raster (bitmap) images
in PostScript, EPS, PDF, and SVG output. You can construct images directly from
raw byte buffers in Python, load JPEG or PNM (PBM/PGM/PPM/PAM) files natively, or
pass any `Pillow (PIL) <https://python-pillow.org/>`_ ``Image`` object directly
to :class:`bitmap`.

Example: Creating a Bitmap from Raw Bytes
-----------------------------------------

To create a bitmap from raw binary pixel data, first wrap the byte buffer in an
:class:`image` instance and then place it at a canvas position with
:class:`bitmap`:

.. code-block:: python

   from pyx import *

   image_bw = bitmap.image(2, 2, "L", b"\0\377\377\0")
   image_rgb = bitmap.image(3, 2, "RGB", b"\77\77\77\177\177\177\277\277\277"
                                         b"\377\0\0\0\377\0\0\0\377")

   bitmap_bw = bitmap.bitmap(0, 1, image_bw, height=0.8)
   bitmap_rgb = bitmap.bitmap(0, 0, image_rgb, height=0.8)

   c = canvas.canvas()
   c.insert(bitmap_bw)
   c.insert(bitmap_rgb)
   c.writeEPSfile("bitmap")

Here ``image_bw`` is a :math:`2\times 2` 8-bit grayscale (``"L"``) image
containing two black (``0``) and two white (``255``) pixels, ordered row by row
from the top-left corner. ``image_rgb`` is a :math:`3\times 2` RGB image whose
top row contains three shades of gray and whose bottom row contains red, green,
and blue pixels. Because raw :class:`image` buffers do not carry DPI metadata,
we specify ``height=0.8`` when constructing the :class:`bitmap` canvas items.
Figure :ref:`fig_bitmap` shows the resulting output.

.. _fig_bitmap:
.. figure:: bitmap.*
   :align: center

   Placing grayscale and RGB :class:`bitmap` instances on a canvas.


Image Containers and File Readers
=================================

.. class:: image(width, height, mode, data, compressed=None, palette=None)

   Container for 8-bit-per-channel pixel data.

   * *width*, *height*: Image dimensions in pixels.
   * *mode*: Color mode string. Supported modes are:

     - ``"L"`` (8-bit grayscale), ``"RGB"`` (24-bit RGB), ``"CMYK"`` (32-bit CMYK)
     - Modes with an 8-bit alpha channel: ``"LA"``, ``"RGBA"``, ``"CMYKA"``
       (trailing alpha) or ``"AL"``, ``"ARGB"``, ``"ACMYK"`` (leading alpha)
     - ``"P"`` (8-bit palette-indexed color, requiring a :class:`palette`
       instance in *palette*)

   * *data*: A ``bytes`` object containing the pixel values row by row from top
     left to bottom right. For uncompressed data, ``len(data)`` must equal
     ``len(mode) * width * height``.
   * *compressed*: ``None`` for uncompressed pixel bytes, or ``"Flate"`` /
     ``"DCT"`` if *data* is already Flate- or JPEG-compressed.
   * *palette*: Optional :class:`palette` instance when ``mode="P"``.

.. class:: jpegimage(file)

   Reads a JPEG/JFIF image from *file* (either a filename string or an open
   binary file-like object). :class:`jpegimage` parses the JPEG headers to
   extract the pixel dimensions, color components (``"L"``, ``"RGB"``, or
   ``"CMYK"``), and embedded DPI resolution (if present), and embeds the
   DCT-compressed stream directly into the output without decoding and
   re-encoding—preserving 100% of the original image quality and minimizing file
   size.

.. class:: pnmimage(file)

   Reads a Netpbm PNM image (PBM, PGM, PPM, or PAM, in either ASCII or binary
   format, including 1-bit, 8-bit, and 16-bit images) from *file* (a filename
   string or an open binary file-like object).


Placing Bitmaps on a Canvas
===========================

.. class:: bitmap(xpos, ypos, image, width=None, height=None, ratio=None, PSstoreimage=0, PSmaxstrlen=4093, PSbinexpand=1, compressmode="Flate", flatecompresslevel=6, dctquality=75, dctoptimize=0, dctprogression=0)

   Creates a canvas item that places *image* with its lower-left corner at
   ``(xpos, ypos)`` (in user units or PyX lengths). A point-based variant
   :class:`bitmap_pt` takes ``xpos_pt``, ``ypos_pt``, ``width_pt``, and
   ``height_pt`` in PostScript points, and the lower-level base class
   :class:`bitmap_trafo` accepts an arbitrary :class:`trafo.trafo_pt` mapping the
   unit square to the target image rectangle.

   * *image*: An instance of :class:`image`, :class:`jpegimage`,
     :class:`pnmimage`, or any Pillow (``PIL.Image``) object.
   * *width*, *height*, *ratio*: Target physical dimensions of the bitmap on the
     canvas. If *image* does not provide DPI metadata (in ``image.info["dpi"]``),
     at least *width* or *height* must be specified. When only one dimension is
     given, the other is computed from *ratio* (or from the pixel aspect ratio if
     ``ratio=None``).
   * *PSstoreimage*: When true, stores the compressed image data in PostScript
     interpreter memory as a reusable resource rather than streaming it inline.
     This avoids duplicating image bytes when the same bitmap is drawn multiple
     times in PostScript output.
   * *PSmaxstrlen*: Maximum PostScript string length (default ``4093``) used when
     *PSstoreimage* is enabled.
   * *PSbinexpand*: Expansion factor (``1`` or ``2``) used when converting
     low-bit-depth PIL images for PostScript output.
   * *compressmode*: Stream compression method used in PostScript and PDF output:
     ``"Flate"`` (lossless zlib compression, the default for uncompressed
     images), ``"DCT"`` (JPEG compression, supported for :class:`jpegimage` and
     Pillow images), or ``None`` (uncompressed). When *image* is already
     compressed (such as a :class:`jpegimage`), *compressmode* is automatically
     set to ``None`` so the compressed stream is passed through untouched.
   * *flatecompresslevel*: Zlib compression level (``1``–``9``, default ``6``)
     when ``compressmode="Flate"``.
   * *dctquality*, *dctoptimize*, *dctprogression*: JPEG encoding parameters passed
     to Pillow when ``compressmode="DCT"``. Keep ``dctprogression=0`` and
     ``dctoptimize=0`` for maximum PostScript printer compatibility.

   .. note::

      * **Alpha channels (transparency)**: Images with an alpha channel
        (``"LA"``, ``"RGBA"``, ``"CMYKA"``, etc.) are automatically split into a
        color image and a soft-mask (``/SMask``) in PDF output, or exported as
        RGBA PNG data in SVG output. Standard PostScript does not support soft
        masks and logs a warning while ignoring the alpha channel.
      * **SVG output**: When writing SVG output, :class:`bitmap` embeds the image
        as a base64-encoded ``data:image/png`` or ``data:image/jpeg`` URI inside
        an SVG ``<image>`` element.
