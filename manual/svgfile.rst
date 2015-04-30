
.. module:: svgfile

*****************************************
Module :mod:`svgfile`: SVG file inclusion
*****************************************

With the help of the ``svgfile.svgfile`` class, you can easily embed another SVG
file in your canvas, thereby scaling, aligning the content at discretion. The
most simple example looks like

   ::

      from pyx import *
      c = canvas.canvas()
      c.insert(svgfile.svgfile(0, 0, "file.svg"))
      c.writeSVGfile("output")


All relevant parameters are passed to the ``svgfile.svgfile`` constructor. They
are summarized in the following table:

+---------------------+-----------------------------------------------+
| argument name       | description                                   |
+=====================+===============================================+
| ``x``               | :math:`x`\ -coordinate of position.           |
+---------------------+-----------------------------------------------+
| ``y``               | :math:`y`\ -coordinate of position.           |
+---------------------+-----------------------------------------------+
| ``filename``        | Name of the SVG file.                         |
+---------------------+-----------------------------------------------+
| ``width=None``      | Desired width of SVG graphics or ``None`` for |
|                     | original width.                               |
+---------------------+-----------------------------------------------+
| ``height=None``     | Desired height of SVG graphics or ``None``    |
|                     | for original height.                          |
+---------------------+-----------------------------------------------+
| ``ratio=None``      | For a given width or height set the other     |
|                     | dimension with the given ratio. If ``None``   |
|                     | and either width or height is set, the other  |
|                     | dimension is scaled proportionally, which     |
|                     | is different from a ratio ``1``.              |
+---------------------+-----------------------------------------------+
| ``parsed=False``    | Parsed mode flag, see below.                  |
+---------------------+-----------------------------------------------+
| ``resolution=96``   | SVG resolution in "dpi", see below.           |
+---------------------+-----------------------------------------------+

In parsed mode a filled PyX canvas containing the SVG data is created. At the
moment the parser handles paths with styles, transformations, canvas nesting
etc. but no other SVG constructs. While some features might be added in the
future, the parsed mode will probably always have limitations, like not being
able to take into account CSS styling and other things. On the other hand the
parsed mode has some major advantages. You can access the paths as PyX paths
within the canvas and you can output the parsed SVG data to PostScript and PDF.

Even though SVG is a vector format, inserting an SVG file depends on a
resolution most of the time. This resolution defines the unit scale, when no
unit like ``pt``, ``in``, ``mm``, or ``cm`` is used. This user unit is meant to
be pixels, thus viewer programs are adviced to use the screen resolution. Tools
to SVG files often use 90 dpi as in the w3.org SVG Recommendation. However,
note that Adobe (R) Illustrator (R) uses 72 dpi. In browsers 96 dpi is commonly
used, which is thus set as the default. However, all this might vary between
plattforms and configurations.

Note that the SVG output of PyX defines the its size using units. Still, when
reading such a file in un-parsed mode PyX need to make assumtions on how the
final viewer will insert (i.e. scale and position) the SVG file, thus needing a
resolution. Only in parsed mode it becomes resolution independent.

Unfortunately it is rather uncommon to store the size of the SVG in coordinates
with units. You then need to provide the correct resolution in both modes,
parsed and unparsed, to get proper alignment.

