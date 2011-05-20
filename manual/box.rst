
.. module:: box

**************************************
Module :mod:`box`: Convex box handling
**************************************

This module has a quite internal character, but might still be useful from the
users point of view. It might also get further enhanced to cover a broader range
of standard arranging problems.

In the context of this module a box is a convex polygon having optionally a
center coordinate, which plays an important role for the box alignment. The
center might not at all be central, but it should be within the box. The
convexity is necessary in order to keep the problems to be solved by this module
quite a bit easier and unambiguous.

Directions (for the alignment etc.) are usually provided as pairs (dx, dy)
within this module. It is required, that at least one of these two numbers is
unequal to zero. No further assumptions are taken.


Polygon
=======

A polygon is the most general case of a box. It is an instance of the class
``polygon``. The constructor takes a list of points (which are (x, y) tuples) in
the keyword argument ``corners`` and optionally another (x, y) tuple as the
keyword argument ``center``. The corners have to be ordered counterclockwise. In
the following list some methods of this ``polygon`` class are explained:

``path(centerradius=None, bezierradius=None, beziersoftness=1)``:
   returns a path of the box; the center might be marked by a small circle of
   radius ``centerradius``; the corners might be rounded using the parameters
   ``bezierradius`` and ``beziersoftness``. For each corner of the box there may be
   one value for beziersoftness and two bezierradii. For convenience, it is not
   necessary to specify the whole list (for beziersoftness) and the whole list of
   lists (bezierradius) here. You may give a single value and/or a 2-tuple instead.

``transform(*trafos)``:
   performs a list of transformations to the box

``reltransform(*trafos)``:
   performs a list of transformations to the box relative to the box center

.. _fig_boxalign:
.. figure:: boxalign.*
   :align:  center

   circle and line alignment examples (equal direction and distance)

``circlealignvector(a, dx, dy)``:
   returns a vector (a tuple (x, y)) to align the box at a circle with radius ``a``
   in the direction (``dx``, ``dy``); see figure :ref:`fig_boxalign`

``linealignvector(a, dx, dy)``:
   as above, but align at a line with distance ``a``

``circlealign(a, dx, dy)``:
   as circlealignvector, but perform the alignment instead of returning the vector

``linealign(a, dx, dy)``:
   as linealignvector, but perform the alignment instead of returning the vector

``extent(dx, dy)``:
   extent of the box in the direction (``dx``, ``dy``)

``pointdistance(x, y)``:
   distance of the point (``x``, ``y``) to the box; the point must be outside of
   the box

``boxdistance(other)``:
   distance of the box to the box ``other``; when the boxes are overlapping,
   ``BoxCrossError`` is raised

``bbox()``:
   returns a bounding box instance appropriate to the box


Functions working on a box list
===============================

``circlealignequal(boxes, a, dx, dy)``:
   Performs a circle alignment of the boxes ``boxes`` using the parameters ``a``,
   ``dx``, and ``dy`` as in the ``circlealign`` method. For the length of the
   alignment vector its largest value is taken for all cases.

``linealignequal(boxes, a, dx, dy)``:
   as above, but performing a line alignment

``tile(boxes, a, dx, dy)``:
   tiles the boxes ``boxes`` with a distance ``a`` between the boxes (in addition
   the maximal box extent in the given direction (``dx``, ``dy``) is taken into
   account)


Rectangular boxes
=================

For easier creation of rectangular boxes, the module provides the specialized
class ``rect``. Its constructor first takes four parameters, namely the x, y
position and the box width and height. Additionally, for the definition of the
position of the center, two keyword arguments are available. The parameter
``relcenter`` takes a tuple containing a relative x, y position of the center
(they are relative to the box extent, thus values between ``0`` and ``1`` should
be used). The parameter ``abscenter`` takes a tuple containing the x and y
position of the center. This values are measured with respect to the lower left
corner of the box. By default, the center of the rectangular box is set to this
lower left corner.

