
.. module:: epsfile

*****************************************
Module :mod:`epsfile`: EPS file inclusion
*****************************************

With the help of the :class:`epsfile.epsfile` class, you can easily embed
another EPS file in your canvas, scaling and aligning the content at
discretion. The simplest example looks like

   ::

      from pyx import *
      c = canvas.canvas()
      c.insert(epsfile.epsfile(0, 0, "file.eps"))
      c.writeEPSfile("output")


.. class:: epsfile(x, y, filename, width=None, height=None, scale=None, align="bl", clip=1, translatebbox=True, bbox=None, kpsearch=False)

   All relevant parameters are passed to the :class:`epsfile.epsfile`
   constructor. They are summarized in the following table:

+------------------------+-----------------------------------------------+
| argument name          | description                                   |
+========================+===============================================+
| ``x``                  | :math:`x`\ -coordinate of position.           |
+------------------------+-----------------------------------------------+
| ``y``                  | :math:`y`\ -coordinate of position.           |
+------------------------+-----------------------------------------------+
| ``filename``           | Name of the EPS file (including a possible    |
|                        | extension).                                   |
+------------------------+-----------------------------------------------+
| ``width=None``         | Desired width of EPS graphics or ``None`` for |
|                        | original width. Cannot be combined with scale |
|                        | specification.                                |
+------------------------+-----------------------------------------------+
| ``height=None``        | Desired height of EPS graphics or ``None``    |
|                        | for original height. Cannot be combined with  |
|                        | scale specification.                          |
+------------------------+-----------------------------------------------+
| ``scale=None``         | Scaling factor for EPS graphics or ``None``   |
|                        | for no scaling. Cannot be combined with width |
|                        | or height specification.                      |
+------------------------+-----------------------------------------------+
| ``align="bl"``         | Alignment of EPS graphics. The first          |
|                        | character specifies the vertical alignment:   |
|                        | ``b`` for bottom, ``c`` for center, and ``t`` |
|                        | for top. The second character fixes the       |
|                        | horizontal alignment: ``l`` for left, ``c``   |
|                        | for center, and ``r`` for right.              |
+------------------------+-----------------------------------------------+
| ``clip=1``             | Clip to bounding box of EPS file?             |
+------------------------+-----------------------------------------------+
| ``translatebbox=True`` | Translate the EPS graphics such that the      |
|                        | lower left corner of its bounding box is at   |
|                        | the origin? Set to :math:`0` with care.       |
+------------------------+-----------------------------------------------+
| ``bbox=None``          | If given, use ``bbox`` instance instead of    |
|                        | bounding box of EPS file.                     |
+------------------------+-----------------------------------------------+
| ``kpsearch=False``     | Search for file using the kpathsea library.   |
+------------------------+-----------------------------------------------+

Note that :class:`epsfile.epsfile` embeds the EPS graphics directly when
generating PostScript output. When generating PDF output, the EPS file is
converted to a bitmap using Ghostscript (`pipeGS`). To embed vector graphics in
PDF output directly, use the :mod:`pdffile` module instead.

.. _epsfile:
