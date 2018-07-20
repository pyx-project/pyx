
.. module:: document

======================
Module :mod:`document`
======================

.. sectionauthor:: Jörg Lehmann <joerg@pyx-project.org>

The document module contains two classes: :class:`document` and :class:`page`. A
:class:`document` consists of one or several :class:`page`\ s.


Class :class:`page`
-------------------

A :class:`page` is a thin wrapper around a :class:`canvas`, which defines some
additional properties of the page.


.. class:: page(canvas, pagename=None, paperformat=None, rotated=0, centered=1, fittosize=0, margin=1 * unit.t_cm, bboxenlarge=1 * unit.t_pt, bbox=None)

   Construct a new :class:`page` from the given :class:`canvas` instance. A string
   *pagename* and the *paperformat* can be defined. See below, for a list of known
   paper formats. If *rotated* is set, the output is rotated by 90 degrees on the
   page. If *centered* is set, the output is centered on the given paperformat. If
   *fittosize* is set, the output is scaled to fill the full page except for a
   given *margin*.  Normally, the bounding box of the canvas is calculated
   automatically from the bounding box of its elements. In any case, the bounding
   box is enlarged on all sides by *bboxenlarge*. Alternatively, you may specify
   the *bbox* manually.

Class :class:`document`
-----------------------


.. class:: document(pages=[])

   Construct a :class:`document` consisting of a given list of *pages*.

A :class:`document` can be written to a file using one of the following methods:


.. method:: document.writeEPSfile(file, title=None, stripfonts=True, textaspath=False, meshasbitmap=False, meshasbitmapresolution=300)

   Write a single page :class:`document` to an EPS file or to stdout if *file* is
   set to *-*. *title* is used as the document title, *stripfonts* enabled
   font stripping (removal of unused glyphs), *textaspath* converts all text
   to paths instead of using fonts in the output, *meshasbitmap* converts
   meshs (like 3d surface plots) to bitmaps (to reduce complexity in the
   output) and *meshasbitmapresolution* is the resolution of this conversion
   in dots per inch.


.. method:: document.writePSfile(file, writebbox=False, title=None, stripfonts=True, textaspath=False, meshasbitmap=False, meshasbitmapresolution=300)

   Write :class:`document` to a PS file or to to stdout if *file* is set to
   *-*. *writebbox* add the page bounding boxes to the output. All other
   parameters are identical to the :meth:`writeEPSfile` method.


.. method:: document.writePDFfile(file, title=None, author=None, subject=None, keywords=None, fullscreen=False, writebbox=False, compress=True, compresslevel=6, stripfonts=True, textaspath=False, meshasbitmap=False, meshasbitmapresolution=300)

   Write :class:`document` to a PDF file or to stdout if *file* is set to *-*.
   *author*, *subject*, and *keywords* are used for the document author,
   subject, and keyword information, respectively. *fullscreen* enabled
   fullscreen mode when the document is opened, *writebbox* enables writing of
   the crop box to each page, *compress* enables output stream compression and
   *compresslevel* sets the compress level to be used (from 1 to 9). All other
   parameters are identical to the :meth:`writeEPSfile`.


.. method:: document.writeSVGfile(file, textaspath=True, meshasbitmapresolution=300)

   Write :class:`document` to a SVG file or to stdout if *file* is set to *-*.
   The *textaspath* and *meshasbitmapresolution* have the same meaning as
   in :meth:`writeEPSfile`. However, not the different default for
   *textaspath* due to the missing SVG font support by current browsers.
   In addition, there is no *meshasbitmap* flag, as meshs are always stored
   using bitmaps in SVG.


.. method:: document.writetofile(filename, *args, **kwargs)

   Determine the file type (EPS, PS, PDF, or SVG) from the file extension of *filename*
   and call the corresponding write method with the given arguments *arg* and
   *kwargs*.


Class :class:`paperformat`
--------------------------


.. class:: paperformat(width, height, name=None)

   Define a :class:`paperformat` with the given *width* and *height* and the
   optional *name*.

Predefined paperformats are listed in the following table

+--------------------------------------+--------+----------+---------+
| instance                             | name   | width    | height  |
+======================================+========+==========+=========+
| :const:`document.paperformat.A0`     | A0     | 840 mm   | 1188 mm |
+--------------------------------------+--------+----------+---------+
| :const:`document.paperformat.A0b`    |        | 910 mm   | 1370 mm |
+--------------------------------------+--------+----------+---------+
| :const:`document.paperformat.A1`     | A1     | 594 mm   | 840 mm  |
+--------------------------------------+--------+----------+---------+
| :const:`document.paperformat.A2`     | A2     | 420 mm   | 594 mm  |
+--------------------------------------+--------+----------+---------+
| :const:`document.paperformat.A3`     | A3     | 297 mm   | 420 mm  |
+--------------------------------------+--------+----------+---------+
| :const:`document.paperformat.A4`     | A4     | 210 mm   | 297 mm  |
+--------------------------------------+--------+----------+---------+
| :const:`document.paperformat.A5`     | A5     | 148.5 mm | 210 mm  |
+--------------------------------------+--------+----------+---------+
| :const:`document.paperformat.Letter` | Letter | 8.5 inch | 11 inch |
+--------------------------------------+--------+----------+---------+
| :const:`document.paperformat.Legal`  | Legal  | 8.5 inch | 14 inch |
+--------------------------------------+--------+----------+---------+

