
.. module:: color

*******************
Module :mod:`color`
*******************


Color models
============

PostScript provides different color models. They are available to PyX by
different color classes, which just pass the colors down to the PostScript
level. This implies, that there are no conversion routines between different
color models available. However, some color model conversion routines are
included in Python's standard library in the module ``colorsym``. Furthermore
also the comparison of colors within a color model is not supported, but might
be added in future versions at least for checking color identity and for
ordering gray colors.

There is a class for each of the supported color models, namely ``gray``,
``rgb``, ``cmyk``, and ``hsb``. The constructors take variables appropriate for
the color model. Additionally, a list of named colors is given in appendix
:ref:`colorname`.


Example
=======

   ::

      from pyx import *

      c = canvas.canvas()

      c.fill(path.rect(0, 0, 7, 3), [color.gray(0.8)])
      c.fill(path.rect(1, 1, 1, 1), [color.rgb.red])
      c.fill(path.rect(3, 1, 1, 1), [color.rgb.green])
      c.fill(path.rect(5, 1, 1, 1), [color.rgb.blue])

      c.writeEPSfile("color")


The file ``color.eps`` is created and looks like:

.. _fig_color:
.. figure:: color.*
   :align:  center

   Color example


Color gradients
===============

The color module provides a class :class:`gradient` for continous transitions between
colors. A list of named gradients is available in appendix :ref:`gradientname`. 

Note that all predefined non-gray gradients are defined in the RGB color space,
except for `gradient.Rainbow`, `gradient.ReverseRainbow`, `gradient.Hue`, and
`gradient.ReverseHue`, which are naturally defined in the HSB color space. Converted
RGB and CMYK versions of these latter gradients are also defined under the names
`rgbgradient.Rainbow` and `cmykgradient.Rainbow`, etc.


.. class:: gradient()

   This class defines the methods for the ``gradient``.

   .. function:: getcolor(parameter)

      Returns the color that corresponds to *parameter* (must be between *min* and
      *max*).


   .. function:: select(index, n_indices)

      When a total number of *n_indices* different colors is needed from the gradient,
      this method returns the *index*-th color.

.. class:: functiongradient_cmyk(f_c, f_m, f_y, f_k)
.. class:: functiongradient_gray(f_gray)
.. class:: functiongradient_hsb(f_g, f_s, f_b)
.. class:: functiongradient_rgb(f_r, f_g, f_b)

   This class provides an arbitray transition between colors of the same color
   model.

   The functions *f_c*, etc. map the values [0, 1] to the respective components
   of the color model.

.. function:: lineargradient_cmyk(mincolor, maxcolor)
.. function:: lineargradient_gray(mincolor, maxcolor)
.. function:: lineargradient_hsb(mincolor, maxcolor)
.. function:: lineargradient_rgb(mincolor, maxcolor)

   These factory functors for the corresponding *functiongradient_* classes
   provide a linear transition between two given instances of the same color
   class. The linear interpolation is performed on the color components of the
   specific color model.

   *mincolor* and *maxcolor* must be colors of the corresponding color class.

.. class:: class rgbgradient(gradient)

   This class takes an arbitrary gradient and converts it into one in the RGB color model.
   This is useful for instance in bitmap output, where only certain color models
   are supported in Postscript/PDF.

.. class:: class cmykgradient(gradient)

   This class takes an arbitrary gradient and converts it into one in the CMYK color mode.
   This is useful for instance in bitmap output, where only certain color models
   are supported in Postscript/PDF.



Transparency
============


.. class:: transparency(value)

   Instances of this class will make drawing operations (stroking, filling) to
   become partially transparent. *value* defines the transparency factor in the
   range ``0`` (opaque) to ``1`` (transparent).

   Transparency is available in PDF output only since it is not supported by
   PostScript. However, for certain ghostscript devices (for example the pdf
   backend as used by ps2pdf) proprietary PostScript extension allows for
   transparency in PostScript code too. PyX creates such PostScript proprietary
   code, but issues a warning when doing so.

