
.. _bbox_module:

.. module:: bbox

******************
Module :mod:`bbox`
******************

The :mod:`bbox`` module contains the definition of the :class:`bbox` class representing
bounding boxes of graphical elements like paths, canvases, etc. used in PyX.
Usually, you obtain ``bbox`` instances as return values of the corresponding
``bbox())`` method, but you may also construct a bounding box by yourself.


:class:`bbox` constructor
=========================

The ``bbox`` constructor accepts the following keyword arguments

+---------+-----------------------------------------------+
| keyword | description                                   |
+=========+===============================================+
| ``llx`` | ``None`` (default) for :math:`-\infty` or     |
|         | :math:`x`\ -position of the lower left corner |
|         | of the bbox (in user units)                   |
+---------+-----------------------------------------------+
| ``lly`` | ``None`` (default) for :math:`-\infty` or     |
|         | :math:`y`\ -position of the lower left corner |
|         | of the bbox (in user units)                   |
+---------+-----------------------------------------------+
| ``urx`` | ``None`` (default) for :math:`\infty` or      |
|         | :math:`x`\ -position of the upper right       |
|         | corner of the bbox (in user units)            |
+---------+-----------------------------------------------+
| ``ury`` | ``None`` (default) for :math:`\infty` or      |
|         | :math:`y`\ -position of the upper right       |
|         | corner of the bbox (in user units)            |
+---------+-----------------------------------------------+


:class:`bbox` methods
=====================

+-------------------------------------------+-----------------------------------------------+
| ``bbox`` method                           | function                                      |
+===========================================+===============================================+
| ``intersects(other)``                     | returns ``1`` if the ``bbox`` instance and    |
|                                           | ``other`` intersect with each other.          |
+-------------------------------------------+-----------------------------------------------+
| ``transformed(self, trafo)``              | returns ``self`` transformed by               |
|                                           | transformation ``trafo``.                     |
+-------------------------------------------+-----------------------------------------------+
| ``enlarged(all=0, bottom=None, left=None, | return the bounding box enlarged by the given |
| top=None, right=None)``                   | amount (in visual units). ``all`` is the      |
|                                           | default for all other directions, which is    |
|                                           | used whenever ``None`` is given for the       |
|                                           | corresponding direction.                      |
+-------------------------------------------+-----------------------------------------------+
| ``path()`` or ``rect()``                  | return the ``path`` corresponding to the      |
|                                           | bounding box rectangle.                       |
+-------------------------------------------+-----------------------------------------------+
| ``height()``                              | returns the height of the bounding box (in    |
|                                           | PyX lengths).                                 |
+-------------------------------------------+-----------------------------------------------+
| ``width()``                               | returns the width of the bounding box (in PyX |
|                                           | lengths).                                     |
+-------------------------------------------+-----------------------------------------------+
| ``top()``                                 | returns the :math:`y`\ -position of the top   |
|                                           | of the bounding box (in PyX lengths).         |
+-------------------------------------------+-----------------------------------------------+
| ``bottom()``                              | returns the :math:`y`\ -position of the       |
|                                           | bottom of the bounding box (in PyX lengths).  |
+-------------------------------------------+-----------------------------------------------+
| ``left()``                                | returns the :math:`x`\ -position of the left  |
|                                           | side of the bounding box (in PyX lengths).    |
+-------------------------------------------+-----------------------------------------------+
| ``right()``                               | returns the :math:`x`\ -position of the right |
|                                           | side of the bounding box (in PyX lengths).    |
+-------------------------------------------+-----------------------------------------------+

Furthermore, two bounding boxes can be added (giving the bounding box enclosing
both) and multiplied (giving the intersection of both bounding boxes).

