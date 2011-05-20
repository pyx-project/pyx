.. module:: trafo

*******************************************
Module :mod:`trafo`: Linear transformations
*******************************************


With the  ``trafo`` module PyX supports linear transformations, which can  then
be applied to canvases,  Bézier paths and other objects. It consists of the main
class ``trafo`` representing a general linear transformation and subclasses
thereof, which provide special operations like translation, rotation, scaling,
and mirroring.


Class trafo
===========

The ``trafo`` class represents a general linear transformation, which is defined
for a vector :math:`\vec{x}` as  ::

   XXX: translate this math
     \vec{x}' = \mathsf{A}\, \vec{x} + \vec{b}\ ,

where :math:`\mathsf{A}` is the transformation matrix and :math:`\vec{b}` the
translation vector. The transformation matrix must not be singular, *i.e.* we
require :math:`\det \mathsf{A} \ne 0`.

Multiple ``trafo`` instances can be multiplied, corresponding to a consecutive
application of the respective transformation. Note that ``trafo1*trafo2`` means
that ``trafo1`` is applied after ``trafo2``, *i.e.* the new transformation is
given  by :math:`\mathsf{A} = \mathsf{A}_1 \mathsf{A}_2` and :math:`\vec{b} =
\mathsf{A}_1 \vec{b}_2 + \vec{b}_1`.  Use the ``trafo`` methods described below,
if you prefer thinking the other way round. The inverse of a transformation can
be obtained via the ``trafo`` method ``inverse()``, defined by the inverse
:math:`\mathsf{A}^{-1}` of the transformation matrix and the translation vector
:math:`-\mathsf{A}^{-1}\vec{b}`.

The methods of the ``trafo`` class are summarized in the following table.

+-----------------------------------------+----------------------------------------------+
| ``trafo`` method                        | function                                     |
+=========================================+==============================================+
| ``__init__(matrix=((1,0),(0,1)),        | create new ``trafo`` instance with           |
| vector=(0,0)):``                        | transformation ``matrix`` and ``vector``.    |
+-----------------------------------------+----------------------------------------------+
| ``apply(x, y)``                         | apply ``trafo`` to point vector              |
|                                         | :math:`(\mathtt{x}, \mathtt{y})`.            |
+-----------------------------------------+----------------------------------------------+
| ``inverse()``                           | returns inverse transformation of ``trafo``. |
+-----------------------------------------+----------------------------------------------+
| ``mirrored(angle)``                     | returns ``trafo`` followed by mirroring at   |
|                                         | line through :math:`(0,0)` with  direction   |
|                                         | ``angle`` in degrees.                        |
+-----------------------------------------+----------------------------------------------+
| ``rotated(angle, x=None, y=None)``      | returns ``trafo`` followed by rotation by    |
|                                         | ``angle`` degrees around point               |
|                                         | :math:`(\mathtt{x}, \mathtt{y})`, or         |
|                                         | :math:`(0,0)`, if not given.                 |
+-----------------------------------------+----------------------------------------------+
| ``scaled(sx, sy=None, x=None, y=None)`` | returns ``trafo`` followed by scaling with   |
|                                         | scaling factor ``sx`` in :math:`x`\          |
|                                         | -direction, ``sy`` in :math:`y`\ -direction  |
|                                         | (:math:`\mathtt{sy}=\mathtt{sx}`, if not     |
|                                         | given) with scaling center                   |
|                                         | :math:`(\mathtt{x}, \mathtt{y})`, or         |
|                                         | :math:`(0,0)`, if not given.                 |
+-----------------------------------------+----------------------------------------------+
| ``translated(x, y)``                    | returns ``trafo`` followed by translation by |
|                                         | vector :math:`(\mathtt{x}, \mathtt{y})`.     |
+-----------------------------------------+----------------------------------------------+
| ``slanted(a, angle=0, x=None, y=None)`` | returns ``trafo`` followed by XXX            |
+-----------------------------------------+----------------------------------------------+


Subclasses of trafo
===================

The ``trafo`` module provides a number of subclasses of the ``trafo`` class,
each of which corresponds to one ``trafo`` method. They are listed in the
following table:

+----------------------------------------+----------------------------------------------+
| ``trafo`` subclass                     | function                                     |
+========================================+==============================================+
| ``mirror(angle)``                      | mirroring at line through :math:`(0,0)` with |
|                                        | direction  ``angle`` in degrees.             |
+----------------------------------------+----------------------------------------------+
| ``rotate(angle, x=None, y=None)``      | rotation by ``angle`` degrees around point   |
|                                        | :math:`(\mathtt{x}, \mathtt{y})`, or         |
|                                        | :math:`(0,0)`, if not given.                 |
+----------------------------------------+----------------------------------------------+
| ``scale(sx, sy=None, x=None, y=None)`` | scaling with scaling factor ``sx`` in        |
|                                        | :math:`x`\ -direction, ``sy`` in :math:`y`\  |
|                                        | -direction (:math:`\mathtt{sy}=\mathtt{sx}`, |
|                                        | if not given) with scaling center            |
|                                        | :math:`(\mathtt{x}, \mathtt{y})`, or         |
|                                        | :math:`(0,0)`, if not given.                 |
+----------------------------------------+----------------------------------------------+
| ``translate(x, y)``                    | translation by vector :math:`(\mathtt{x},    |
|                                        | \mathtt{y})`.                                |
+----------------------------------------+----------------------------------------------+
| ``slant(a, angle=0, x=None, y=None)``  | XXX                                          |
+----------------------------------------+----------------------------------------------+

