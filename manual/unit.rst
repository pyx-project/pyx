
.. module:: unit

.. _module_unit:

******************
Module :mod:`unit`
******************

.. sectionauthor:: Jörg Lehmann <joerg@pyx-project.org>




With the ``unit`` module PyX makes available classes and functions for the
specification and manipulation of lengths. As usual, lengths consist of a number
together with a measurement unit, e.g., 1 cm, 50 points, 0.42 inch.  In
addition, lengths in PyX are composed of the five types "true", "user",
"visual", "width", and "TeX", e.g., 1 user cm, 50 true points, 0.42 visual + 0.2
width inch.  As their names indicate, they serve different purposes. True
lengths are not scalable and are mainly used for return values of PyX functions.
The other length types can be rescaled by the user and differ with respect to
the type of object they are applied to:

user length:
   used for lengths of graphical objects like positions etc.

visual length:
   used for sizes of visual elements, like arrows, graph symbols, axis ticks, etc.

width length:
   used for line widths

TeX length:
   used for all TeX and LaTeX output

When not specified otherwise, all types of lengths are interpreted in terms of a
default unit, which, by default, is 1 cm. You may change this default unit by
using the module level function


.. function:: set(uscale=None, vscale=None, wscale=None, xscale=None, defaultunit=None)

   When *uscale*, *vscale*, *wscale*, or *xscale* is not `None`, the
   corresponding scaling factor(s) is redefined to the given number. When
   *defaultunit* is not `None`,  the default unit is set to the given
   value, which has to be one of ``"cm"``, ``"mm"``, ``"inch"``, or ``"pt"``.

For instance, if you only want thicker lines for a publication version of your
figure, you can just rescale all width lengths using  ::

   unit.set(wscale=2)

Or suppose, you are used to specify length in imperial units. In this,
admittedly rather unfortunate case, just use  ::

   unit.set(defaultunit="inch")

at the beginning of your program.


Class :class:`length`
=====================


.. class:: length(f, type="u", unit=None)

   The constructor of the :class:`length` class expects as its first argument a
   number *f*, which represents the prefactor of the given length. By default this
   length is interpreted as a user length (``type="u"``) in units of the current
   default unit (see :func:`set` function of the :mod:`unit` module). Optionally, a
   different *type* may be specified, namely ``"u"`` for user lengths, ``"v"`` for
   visual lengths, ``"w"`` for width lengths, ``"x"`` for TeX length, and ``"t"``
   for true lengths. Furthermore, a different unit may be specified using the
   *unit* argument. Allowed values are ``"cm"``, ``"mm"``, ``"inch"``, and
   ``"pt"``.

Instances of the :class:`length` class support addition and substraction either
by another :class:`length` or by a number which is then interpeted as being a
user length in  default units, multiplication by a number and division either by
another :class:`length` in which case a float is returned or by a number in
which case a :class:`length` instance is returned. When two lengths are
compared, they are first converted to meters (using the currently set scaling),
and then the resulting values are compared.


Predefined length instances
===========================

A number of ``length`` instances are already predefined, which only differ in
there values for ``type`` and ``unit``. They are summarized in the following
table

+-----------------+--------+--------+
| name            | type   | unit   |
+=================+========+========+
| :const:`m`      | user   | m      |
+-----------------+--------+--------+
| :const:`cm`     | user   | cm     |
+-----------------+--------+--------+
| :const:`mm`     | user   | mm     |
+-----------------+--------+--------+
| :const:`inch`   | user   | inch   |
+-----------------+--------+--------+
| :const:`pt`     | user   | points |
+-----------------+--------+--------+
| :const:`t_m`    | true   | m      |
+-----------------+--------+--------+
| :const:`t_cm`   | true   | cm     |
+-----------------+--------+--------+
| :const:`t_mm`   | true   | mm     |
+-----------------+--------+--------+
| :const:`t_inch` | true   | inch   |
+-----------------+--------+--------+
| :const:`t_pt`   | true   | points |
+-----------------+--------+--------+
| :const:`u_m`    | user   | m      |
+-----------------+--------+--------+
| :const:`u_cm`   | user   | cm     |
+-----------------+--------+--------+
| :const:`u_mm`   | user   | mm     |
+-----------------+--------+--------+
| :const:`u_inch` | user   | inch   |
+-----------------+--------+--------+
| :const:`u_pt`   | user   | points |
+-----------------+--------+--------+
| :const:`v_m`    | visual | m      |
+-----------------+--------+--------+
| :const:`v_cm`   | visual | cm     |
+-----------------+--------+--------+
| :const:`v_mm`   | visual | mm     |
+-----------------+--------+--------+
| :const:`v_inch` | visual | inch   |
+-----------------+--------+--------+
| :const:`v_pt`   | visual | points |
+-----------------+--------+--------+
| :const:`w_m`    | width  | m      |
+-----------------+--------+--------+
| :const:`w_cm`   | width  | cm     |
+-----------------+--------+--------+
| :const:`w_mm`   | width  | mm     |
+-----------------+--------+--------+
| :const:`w_inch` | width  | inch   |
+-----------------+--------+--------+
| :const:`w_pt`   | width  | points |
+-----------------+--------+--------+
| :const:`x_m`    | TeX    | m      |
+-----------------+--------+--------+
| :const:`x_cm`   | TeX    | cm     |
+-----------------+--------+--------+
| :const:`x_mm`   | TeX    | mm     |
+-----------------+--------+--------+
| :const:`x_inch` | TeX    | inch   |
+-----------------+--------+--------+
| :const:`x_pt`   | TeX    | points |
+-----------------+--------+--------+

Thus, in order to specify, e.g., a length of 5 width points, just use
``5*unit.w_pt``.


Conversion functions
====================

If you want to know the value of a PyX length in certain units, you may use the
predefined conversion functions which are given in the following table

+---------------+--------------------------+
| function      | result                   |
+===============+==========================+
| ``tom(l)``    | ``l`` in units of m      |
+---------------+--------------------------+
| ``tocm(l)``   | ``l`` in units of cm     |
+---------------+--------------------------+
| ``tomm(l)``   | ``l`` in units of mm     |
+---------------+--------------------------+
| ``toinch(l)`` | ``l`` in units of inch   |
+---------------+--------------------------+
| ``topt(l)``   | ``l`` in units of points |
+---------------+--------------------------+

If ``l`` is not yet a ``length`` instance but a number, it first is interpreted
as a user length in the default units.

