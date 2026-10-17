.. module:: unit
   :synopsis: Multi-component scalable lengths and unit conversions

.. _module_unit:
.. _unit:

******************
Module :mod:`unit`
******************

.. sectionauthor:: Jörg Lehmann <joerg@pyx-project.org>

The :mod:`unit` module provides classes and functions for specifying, scaling,
and converting lengths in PyX. Every length in PyX combines a numerical value,
a measurement unit (``"m"``, ``"cm"``, ``"mm"``, ``"inch"``, or ``"pt"``), and a
combination of five semantic length categories:

``"t"`` (**true** length)
   Unscaled physical length. True lengths ignore all user scaling factors and are
   returned by PyX measurement methods such as :meth:`path.path.arclength` or
   :meth:`bbox.bbox.width`.

``"u"`` (**user** length)
   The default category for geometric coordinates, positions, and path
   dimensions. Plain numbers passed to non-``_pt`` PyX classes and methods are
   automatically interpreted as user lengths in the current default unit.

``"v"`` (**visual** length)
   Used for the size of visual ornaments such as arrowheads, graph symbols, and
   axis tick marks. Scaling visual lengths changes the size of markers and labels
   without altering the overall geometry of a diagram.

``"w"`` (**width** length)
   Used for line widths (:class:`style.linewidth`). Scaling width lengths lets
   you thicken or thin all strokes globally (for example, when preparing a figure
   for a presentation or high-DPI print).

``"x"`` (**TeX** length)
   Used to scale all TeX/LaTeX and :class:`text.UnicodeEngine` text output.

Because a :class:`length` instance stores all five components independently, you
can freely add lengths of different types—such as ``1 * unit.u_cm + 2 * unit.v_mm``—and
PyX will resolve the combined length using the active scaling factors when
drawing.


Configuring Units and Scaling Factors
=====================================

Unless specified otherwise, plain numbers in PyX are interpreted in terms of the
default unit, which is ``"cm"`` (1 centimeter). You can change the default unit
and the scaling factors for the four scalable length categories using
:func:`unit.set`:

.. function:: set(uscale=None, vscale=None, wscale=None, xscale=None, defaultunit=None)

   Updates the scaling factors for user (*uscale*), visual (*vscale*), width
   (*wscale*), and TeX (*xscale*) lengths, or changes *defaultunit* (which must
   be one of ``"m"``, ``"cm"``, ``"mm"``, ``"inch"``, or ``"pt"``). Any argument
   left as ``None`` retains its current setting.

For example, to double all line widths and increase text size by 20% for a slide
deck while keeping the figure dimensions unchanged:

.. code-block:: python

   from pyx import *
   unit.set(wscale=2.0, xscale=1.2)

Or to work in inches instead of centimeters throughout your script:

.. code-block:: python

   unit.set(defaultunit="inch")


Class :class:`length`
=====================

.. class:: length(f=0, type="u", unit=None)

   Constructs a length with numerical factor *f*, length category *type*
   (one of ``"u"``, ``"v"``, ``"w"``, ``"x"``, or ``"t"``; default ``"u"``), and
   measurement *unit* (one of ``"m"``, ``"cm"``, ``"mm"``, ``"inch"``, or
   ``"pt"``; defaults to the active *defaultunit*).

   :class:`length` instances support full arithmetic and comparison operations:

   * **Addition and subtraction** (``l1 + l2``, ``l1 - l2``): Sums or subtracts
     another :class:`length` component-wise. If a plain number is added or
     subtracted, it is first converted to a user length in the current default
     unit.
   * **Multiplication and division by a scalar** (``c * l``, ``l / c``): Scales
     all five components of ``l`` by the number ``c``, returning a new
     :class:`length`.
   * **Division of two lengths** (``l1 / l2``): Converts both lengths to meters
     using the current scaling factors and returns their dimensionless ``float``
     ratio.
   * **Comparisons** (``l1 == l2``, ``l1 < l2``, etc.): Evaluates both lengths in
     meters using the current scaling factors and compares the resulting values.


Predefined Length Constants
===========================

Rather than instantiating :class:`length` directly, it is usually most
convenient to multiply a number by one of the predefined unit constants in
:mod:`unit`—for example, ``5 * unit.w_pt`` or ``1.5 * unit.v_cm``:

+-----------------+--------+---------------+
| Constant        | Type   | Unit          |
+=================+========+===============+
| :const:`m`      | user   | meters        |
+-----------------+--------+---------------+
| :const:`cm`     | user   | centimeters   |
+-----------------+--------+---------------+
| :const:`mm`     | user   | millimeters   |
+-----------------+--------+---------------+
| :const:`inch`   | user   | inches        |
+-----------------+--------+---------------+
| :const:`pt`     | user   | points (1/72")|
+-----------------+--------+---------------+
| :const:`t_m`    | true   | meters        |
+-----------------+--------+---------------+
| :const:`t_cm`   | true   | centimeters   |
+-----------------+--------+---------------+
| :const:`t_mm`   | true   | millimeters   |
+-----------------+--------+---------------+
| :const:`t_inch` | true   | inches        |
+-----------------+--------+---------------+
| :const:`t_pt`   | true   | points (1/72")|
+-----------------+--------+---------------+
| :const:`u_m`    | user   | meters        |
+-----------------+--------+---------------+
| :const:`u_cm`   | user   | centimeters   |
+-----------------+--------+---------------+
| :const:`u_mm`   | user   | millimeters   |
+-----------------+--------+---------------+
| :const:`u_inch` | user   | inches        |
+-----------------+--------+---------------+
| :const:`u_pt`   | user   | points (1/72")|
+-----------------+--------+---------------+
| :const:`v_m`    | visual | meters        |
+-----------------+--------+---------------+
| :const:`v_cm`   | visual | centimeters   |
+-----------------+--------+---------------+
| :const:`v_mm`   | visual | millimeters   |
+-----------------+--------+---------------+
| :const:`v_inch` | visual | inches        |
+-----------------+--------+---------------+
| :const:`v_pt`   | visual | points (1/72")|
+-----------------+--------+---------------+
| :const:`w_m`    | width  | meters        |
+-----------------+--------+---------------+
| :const:`w_cm`   | width  | centimeters   |
+-----------------+--------+---------------+
| :const:`w_mm`   | width  | millimeters   |
+-----------------+--------+---------------+
| :const:`w_inch` | width  | inches        |
+-----------------+--------+---------------+
| :const:`w_pt`   | width  | points (1/72")|
+-----------------+--------+---------------+
| :const:`x_m`    | TeX    | meters        |
+-----------------+--------+---------------+
| :const:`x_cm`   | TeX    | centimeters   |
+-----------------+--------+---------------+
| :const:`x_mm`   | TeX    | millimeters   |
+-----------------+--------+---------------+
| :const:`x_inch` | TeX    | inches        |
+-----------------+--------+---------------+
| :const:`x_pt`   | TeX    | points (1/72")|
+-----------------+--------+---------------+


Conversion Functions
====================

To evaluate a :class:`length` (or a plain number, which is treated as a user
length in the current default unit) as a ``float`` in a specific physical unit
taking the current scaling factors into account, use the following conversion
functions:

+-------------------+----------------------------------------------------+
| Function          | Return value (``float``)                           |
+===================+====================================================+
| :func:`tom(l)`    | Value of ``l`` in meters.                          |
+-------------------+----------------------------------------------------+
| :func:`tocm(l)`   | Value of ``l`` in centimeters.                     |
+-------------------+----------------------------------------------------+
| :func:`tomm(l)`   | Value of ``l`` in millimeters.                     |
+-------------------+----------------------------------------------------+
| :func:`toinch(l)` | Value of ``l`` in inches.                          |
+-------------------+----------------------------------------------------+
| :func:`topt(l)`   | Value of ``l`` in PostScript points (1/72 inch).   |
+-------------------+----------------------------------------------------+

.. note::

   PyX internals use :func:`topt` extensively at the boundary between user-facing
   methods and low-level ``_pt`` classes.
