
*******
Bitmaps
*******


Introduction
============

PyX focuses on the creation of scaleable vector graphics. However, PyX also
allows for the output of bitmap images. Still, the support for creation and
handling of bitmap images is quite limited. On the other hand the interfaces are
built that way, that its trivial to combine PyX with the "Python Image Library",
also known as "PIL".

The creation of a bitmap can be performed out of some unpacked binary data by
first creating image instances::

   from pyx import *
   image_bw = bitmap.image(2, 2, "L", "\0\377\377\0")
   image_rgb = bitmap.image(3, 2, "RGB", "\77\77\77\177\177\177\277\277\277"
                                         "\377\0\0\0\377\0\0\0\377")

Now ``image_bw`` is a :math:`2\times2` grayscale image. The bitmap data is
provided by a string, which contains two black (``"\0" == chr(0)``) and two
white (``"\377" == chr(255)``) pixels. Currently the values per (colour) channel
is fixed to 8 bits. The coloured image ``image_rgb`` has :math:`3\times2` pixels
containing a row of 3 different gray values and a row of the three colours red,
green, and blue.

The images can then be wrapped into ``bitmap`` instances by::

   bitmap_bw = bitmap.bitmap(0, 1, image_bw, height=0.8)
   bitmap_rgb = bitmap.bitmap(0, 0, image_rgb, height=0.8)

When constructing a ``bitmap`` instance you have to specify a certain position
by the first two arguments fixing the bitmaps lower left corner. Some optional
arguments control further properties. Since in this example there is no
information about the dpi-value of the images, we have to specify at least a
``width`` or a ``height`` of the bitmap.

The bitmaps are now to be inserted into a canvas::

   c = canvas.canvas()
   c.insert(bitmap_bw)
   c.insert(bitmap_rgb)
   c.writeEPSfile("bitmap")

Figure :ref:`fig_bitmap` shows the resulting output.

.. _fig_bitmap:
.. figure:: bitmap.*
   :align:  center

   An introductory bitmap example.


.. module:: bitmap

Bitmap :mod:`module`: Bitmap support
====================================


.. class:: image(width, height, mode, data, compressed=None)

   This class is a container for image data. *width* and *height* are the size of
   the image in pixel. *mode* is one of ``"L"``, ``" RGB"`` or ``"CMYK"`` for
   grayscale, rgb, or cmyk colours, respectively. *data* is the bitmap data as a
   string, where each single character represents a colour value with ordinal range
   ``0`` to ``255``. Each pixel is described by the appropriate number of colour
   components according to *mode*. The pixels are listed row by row one after the
   other starting at the upper left corner of the image.

   *compressed* might be set to ``" Flate"`` or ``"DCT"`` to provide already
   compressed data. Note that those data will be passed to PostScript without
   further checks, *i.e.* this option is for experts only.


.. class:: jpegimage(file)

   This class is specialized to read data from a JPEG/JFIF-file. *file* is either
   an open file handle (it only has to provide a :meth:`read` method; the file
   should be opened in binary mode) or a string. In the latter case
   :class:`jpegimage` will try to open a file named like *file* for reading.

   The contents of the file is checked for some JPEG/JFIF format markers in order
   to identify the size and dpi resolution of the image for further usage. These
   checks will typically fail for invalid data. The data are not uncompressed, but
   directly inserted into the output stream (for invalid data the result will be
   invalid PostScript). Thus there is no quality loss by recompressing the data as
   it would occur when recompressing the uncompressed stream with the lossy jpeg
   compression method.


.. class:: bitmap(xpos, ypos, image, width=None, height=None, ratio=None, storedata=0, maxstrlen=4093, compressmode="Flate", flatecompresslevel=6, dctquality=75, dctoptimize=1, dctprogression=0)

   *xpos* and *ypos* are the position of the lower left corner of the image. This
   position might be modified by some additional transformations when inserting the
   bitmap into a canvas. *image* is an instance of :class:`image` or
   :class:`jpegimage` but it can also be an image instance from the "Python Image
   Library".

   *width*, *height*, and *ratio* adjust the size of the image. At least *width* or
   *height* needs to be given, when no dpi information is available from *image*.

   *storedata* is a flag indicating, that the (still compressed) image data should
   be put into the printers memory instead of writing it as a stream into the
   PostScript file. While this feature consumes memory of the PostScript
   interpreter, it allows for multiple usage of the image without including the
   image data several times in the PostScript file.

   *maxstrlen* defines a maximal string length when *storedata* is enabled. Since
   the data must be kept in the PostScript interpreters memory, it is stored in
   strings. While most interpreters do not allow for an arbitrary string length (a
   common limit is 65535 characters), a limit for the string length is set. When
   more data need to be stored, a list of strings will be used. Note that lists are
   also subject to some implementation limits. Since a typical value is 65535
   entries, in combination a huge amount of memory can be used.

   Valid values for *compressmode* currently are ``"Flate"`` (zlib compression),
   ``"DCT"`` (jpeg compression), or ``None`` (disabling the compression). The zlib
   compression makes use of the zlib module as it is part of the standard Python
   distribution. The jpeg compression is available for those *image* instances
   only, which support the creation of a jpeg-compressed stream, *e.g.* images from
   the "Python Image Library" with jpeg support installed. The compression must be
   disabled when the image data is already compressed.

   *flatecompresslevel* is a parameter of the zlib compression. *dctquality*,
   *dctoptimize*, and *dctprogression* are parameters of the jpeg compression.
   Note, that the progression feature of the jpeg compression should be turned off
   in order to produce valid PostScript. Also the optimization feature is known to
   produce errors on certain printers.

