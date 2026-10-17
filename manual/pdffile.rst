
.. module:: pdffile

*****************************************
Module :mod:`pdffile`: PDF file inclusion
*****************************************

With the help of the :class:`pdffile.pdffile` class, you can easily embed a
page from another PDF file in your canvas when generating PDF output, scaling
and aligning the content at discretion. The simplest example looks like

   ::

      from pyx import *
      c = canvas.canvas()
      c.insert(pdffile.pdffile(0, 0, "file.pdf"))
      c.writePDFfile("output")


.. class:: pdffile(x, y, filename, width=None, height=None, scale=None, align="bl", clip=1, translatebbox=True, bbox=None, page=1, kpsearch=False)

   All relevant parameters are passed to the :class:`pdffile.pdffile`
   constructor. They are summarized in the following table:

+------------------------+-----------------------------------------------+
| argument name          | description                                   |
+========================+===============================================+
| ``x``                  | :math:`x`\ -coordinate of position.           |
+------------------------+-----------------------------------------------+
| ``y``                  | :math:`y`\ -coordinate of position.           |
+------------------------+-----------------------------------------------+
| ``filename``           | Name of the PDF file (or a binary file-like   |
|                        | object).                                      |
+------------------------+-----------------------------------------------+
| ``width=None``         | Desired width of PDF graphics or ``None`` for |
|                        | original width. Cannot be combined with scale |
|                        | specification.                                |
+------------------------+-----------------------------------------------+
| ``height=None``        | Desired height of PDF graphics or ``None``    |
|                        | for original height. Cannot be combined with  |
|                        | scale specification.                          |
+------------------------+-----------------------------------------------+
| ``scale=None``         | Scaling factor for PDF graphics or ``None``   |
|                        | for no scaling. Cannot be combined with width |
|                        | or height specification.                      |
+------------------------+-----------------------------------------------+
| ``align="bl"``         | Alignment of PDF graphics. The first          |
|                        | character specifies the vertical alignment:   |
|                        | ``b`` for bottom, ``c`` for center, and ``t`` |
|                        | for top. The second character fixes the       |
|                        | horizontal alignment: ``l`` for left, ``c``   |
|                        | for center, and ``r`` for right.              |
+------------------------+-----------------------------------------------+
| ``clip=1``             | Clip to bounding box of the PDF page?         |
+------------------------+-----------------------------------------------+
| ``translatebbox=True`` | Translate the PDF graphics such that the      |
|                        | lower left corner of its bounding box is at   |
|                        | the origin? Set to :math:`0` with care.       |
+------------------------+-----------------------------------------------+
| ``bbox=None``          | If given, use ``bbox`` instance instead of    |
|                        | the bounding box (``CropBox`` or              |
|                        | ``MediaBox``) of the PDF page.                |
+------------------------+-----------------------------------------------+
| ``page=1``             | 1-based page number of the PDF file to        |
|                        | include.                                      |
+------------------------+-----------------------------------------------+
| ``kpsearch=False``     | Search for file using the kpathsea library.   |
+------------------------+-----------------------------------------------+

The included PDF page is embedded as a PDF Form XObject along with its
referenced resources, so inclusion is only supported when generating PDF
output.

.. _pdffile:
