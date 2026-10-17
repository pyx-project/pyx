.. module:: color
   :synopsis: Color models, named colors, gradients, and transparency

.. _color:

*******************
Module :mod:`color`
*******************

The :mod:`color` module provides classes representing colors in four device color
spaces (:class:`gray`, :class:`rgb`, :class:`cmyk`, and :class:`hsb`), continuous
color gradients (:class:`gradient`), and opacity attributes
(:class:`transparency`). Because all color and transparency instances act as both
:class:`style.strokestyle` and :class:`style.fillstyle` attributes, they can be
passed directly to :meth:`canvas.canvas.stroke`, :meth:`canvas.canvas.fill`,
:meth:`canvas.canvas.draw`, :meth:`canvas.canvas.text`, or
:meth:`canvas.canvas.set`.


Color Models and Named Colors
=============================

PyX provides four color classes corresponding to standard PostScript/PDF color
models. All color component values are floating-point numbers in the range
``[0.0, 1.0]``:

.. class:: gray(g)

   Grayscale color with intensity *g* from ``0.0`` (black) to ``1.0`` (white).
   ``grey`` is provided as an alias for :class:`gray`.

   .. method:: gray()
   .. method:: rgb()
   .. method:: cmyk()
   .. method:: hsb()

      Converts the color to a :class:`gray`, :class:`rgb`, :class:`cmyk`, or
      :class:`hsb` instance.

.. class:: rgb(r=0.0, g=0.0, b=0.0)

   RGB color with red (*r*), green (*g*), and blue (*b*) components in
   ``[0.0, 1.0]``. Provides conversion methods :meth:`gray`, :meth:`rgb`,
   :meth:`cmyk`, and :meth:`hsb`, as well as :meth:`rgbhex` (returning a
   ``"#RRGGBB"`` hex string).

.. class:: cmyk(c=0.0, m=0.0, y=0.0, k=0.0)

   CMYK color with cyan (*c*), magenta (*m*), yellow (*y*), and black/key (*k*)
   ink components in ``[0.0, 1.0]``. Provides conversion methods :meth:`gray`,
   :meth:`rgb`, :meth:`cmyk`, and :meth:`hsb`.

.. class:: hsb(h=0.0, s=0.0, b=0.0)

   HSB (hue, saturation, brightness) color with *h*, *s*, and *b* in
   ``[0.0, 1.0]``. Provides conversion methods :meth:`gray`, :meth:`rgb`,
   :meth:`cmyk`, and :meth:`hsb`.

In addition to constructing colors numerically, PyX predefines a rich palette of
named colors as attributes on :class:`gray`, :class:`rgb`, and :class:`cmyk`
(such as ``color.gray.black``, ``color.rgb.red``, ``color.cmyk.CornflowerBlue``).
All predefined named colors are illustrated in appendix :ref:`colorname`.

Color Conversion Configuration
------------------------------

When converting between RGB, CMYK, and Grayscale via ``c.rgb()``, ``c.cmyk()``,
or ``c.gray()``, PyX uses configurable transfer functions that can be adjusted
via :func:`color.set`:

.. autofunction:: set

Example
-------

.. code-block:: python

   from pyx import *

   c = canvas.canvas()

   c.fill(path.rect(0, 0, 7, 3), [color.gray(0.8)])
   c.fill(path.rect(1, 1, 1, 1), [color.rgb.red])
   c.fill(path.rect(3, 1, 1, 1), [color.rgb.green])
   c.fill(path.rect(5, 1, 1, 1), [color.rgb.blue])

   c.writeEPSfile("color")

The resulting figure is shown in figure :ref:`fig_color`.

.. _fig_color:
.. figure:: color.*
   :align: center

   Filling rectangles with grayscale and predefined RGB colors.


Color Gradients
===============

The :class:`gradient` hierarchy represents continuous transitions across a color
space parameterized by a floating-point value in :math:`[0, 1]`. Gradients serve
two roles in PyX:

1. **Continuous color scales** (used by :class:`deco.colorgradient`,
   :class:`graph.style.rect`, :class:`graph.style.surface`, and
   :class:`graph.style.density`) via :meth:`gradient.getcolor`.
2. **Changeable attributes** (:class:`attr.changeattr`) that automatically step
   through *N* evenly spaced colors across a multi-dataset plot or
   :class:`graph.style.bar` chart via :meth:`gradient.select`.

All predefined gradients are listed and illustrated in appendix
:ref:`gradientname`. Note that all predefined non-gray gradients are defined in
the RGB color space except for ``gradient.Rainbow``, ``gradient.ReverseRainbow``,
``gradient.Hue``, and ``gradient.ReverseHue``, which are defined in HSB space;
pre-converted RGB and CMYK versions of those four are provided as
``rgbgradient.Rainbow``, ``cmykgradient.Rainbow``, etc.

.. class:: gradient()

   Base class for all color gradients.

   .. method:: getcolor(parameter)

      Returns the :class:`color` instance corresponding to *parameter* in
      ``[0.0, 1.0]``.

   .. method:: select(index, n_indices)

      Implements the :class:`attr.changeattr` interface: returns the *index*-th
      color out of *n_indices* evenly spaced samples along the gradient
      (evaluating ``getcolor(index / (n_indices - 1))`` when ``n_indices > 1``,
      or ``getcolor(0)`` when ``n_indices == 1``).

.. class:: functiongradient_gray(f_gray)
.. class:: functiongradient_rgb(f_r, f_g, f_b)
.. class:: functiongradient_cmyk(f_c, f_m, f_y, f_k)
.. class:: functiongradient_hsb(f_h, f_s, f_b)

   Constructs a custom gradient in the respective color space where each
   component callable ``f_*(x)`` maps a parameter :math:`x \in [0, 1]` to a
   component value in :math:`[0, 1]`.

.. function:: lineargradient_gray(mincolor, maxcolor)
.. function:: lineargradient_rgb(mincolor, maxcolor)
.. function:: lineargradient_cmyk(mincolor, maxcolor)
.. function:: lineargradient_hsb(mincolor, maxcolor)

   Factory functions that return a :class:`functiongradient_*` instance
   interpolating linearly between *mincolor* (at ``0.0``) and *maxcolor* (at
   ``1.0``) in the respective color space.

.. class:: rgbgradient(gradient)
.. class:: cmykgradient(gradient)

   Wraps an existing *gradient* (such as an HSB gradient) and converts all
   returned colors to :class:`rgb` or :class:`cmyk`. This is particularly useful
   for :class:`graph.style.surface` and :class:`graph.style.density` plots in
   PostScript and PDF, which require shading meshes and bitmaps to use Gray, RGB,
   or CMYK color spaces rather than HSB.


Transparency
============

.. class:: transparency(value)

   Makes stroking and filling operations partially transparent, where *value* is
   in the range ``0.0`` (completely opaque) to ``1.0`` (completely transparent).

   .. note::

      Transparency is natively supported in PDF and SVG output. Standard
      PostScript does not support alpha transparency; when writing PostScript or
      EPS, PyX emits a Ghostscript-specific transparency extension (supported by
      ``ps2pdf``) and logs a warning.
