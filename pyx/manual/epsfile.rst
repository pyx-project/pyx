
.. module:: epsfile

*****************************************
Module :mod:`epsfile`: EPS file inclusion
*****************************************

With the help of the ``epsfile.epsfile`` class, you can easily embed another EPS
file in your canvas, thereby scaling, aligning the content at discretion. The
most simple example looks like

   ::

      from pyx import *
      c = canvas.canvas()
      c.insert(epsfile.epsfile(0, 0, "file.eps"))
      c.writeEPSfile("output")


All relevant parameters are passed to the ``epsfile.epsfile`` constructor. They
are summarized in the following table:

+---------------------+-----------------------------------------------+
| argument name       | description                                   |
+=====================+===============================================+
| ``x``               | :math:`x`\ -coordinate of position.           |
+---------------------+-----------------------------------------------+
| ``y``               | :math:`y`\ -coordinate of position.           |
+---------------------+-----------------------------------------------+
| ``filename``        | Name of the EPS file (including a possible    |
|                     | extension).                                   |
+---------------------+-----------------------------------------------+
| ``width=None``      | Desired width of EPS graphics or ``None`` for |
|                     | original width. Cannot be combined with scale |
|                     | specification.                                |
+---------------------+-----------------------------------------------+
| ``height=None``     | Desired height of EPS graphics or ``None``    |
|                     | for original height. Cannot be combined with  |
|                     | scale specification.                          |
+---------------------+-----------------------------------------------+
| ``scale=None``      | Scaling factor for EPS graphics or ``None``   |
|                     | for no scaling. Cannot be combined with width |
|                     | or height specification.                      |
+---------------------+-----------------------------------------------+
| ``align="bl"``      | Alignment of EPS graphics. The first          |
|                     | character specifies the vertical alignment:   |
|                     | ``b`` for bottom, ``c`` for center, and ``t`` |
|                     | for top. The second character fixes the       |
|                     | horizontal alignment: ``l`` for left, ``c``   |
|                     | for center ``r`` for right.                   |
+---------------------+-----------------------------------------------+
| ``clip=1``          | Clip to bounding box of EPS file?             |
+---------------------+-----------------------------------------------+
| ``translatebbox=1`` | Use lower left corner of bounding box of EPS  |
|                     | file? Set to :math:`0` with care.             |
+---------------------+-----------------------------------------------+
| ``bbox=None``       | If given, use ``bbox`` instance instead of    |
|                     | bounding box of EPS file.                     |
+---------------------+-----------------------------------------------+
| ``kpsearch=0``      | Search for file using the kpathsea library.   |
+---------------------+-----------------------------------------------+

.. _epsfile:

