.. module:: box
   :synopsis: Convex polygon and rectangular boxes for alignment and connectors

.. _box:

**************************************
Module :mod:`box`: Convex box handling
**************************************

The :mod:`box` module provides convex polygon (:class:`polygon`) and rectangular
(:class:`rect`) box classes with an associated reference point (``center``).
Boxes are used throughout PyX to represent the outer boundary and anchor point of
text labels (:class:`text.textbox`), align multiple objects along lines or
circles, tile objects with uniform spacing, and compute boundary intersections
for :mod:`connector` paths.

All direction arguments ``(dx, dy)`` in :mod:`box` are 2D direction vectors where
at least one of *dx* or *dy* must be non-zero (their length is normalized
automatically).


Class :class:`polygon`
======================

.. class:: polygon(corners=None, center=None)

   Represents a convex polygon defined by a sequence of ``(x, y)`` vertex tuples
   in *corners* ordered counter-clockwise, and an optional reference point
   ``(x, y)`` in *center* (in user units or PyX lengths). If *center* is
   ``None``, the arithmetic mean (centroid) of *corners* is used.

   A point-based base class :class:`polygon_pt` takes all coordinates in
   PostScript points.

   .. method:: path(centerradius=None)

      Returns a closed :class:`path.path` tracing the polygon's perimeter. If
      *centerradius* is given, an additional small circle of radius
      *centerradius* is included at the box's ``center``.

      .. tip::

         To round the corners of a box path, apply :class:`deformer.smoothed` to
         the returned path—for example,
         ``deformer.smoothed(0.2).deform(mybox.path())``.

   .. method:: transform(*trafos, keep_anchor=False)

      Applies one or more :class:`trafo.trafo` transformations in place to the
      polygon's corners (and to ``center``, unless ``keep_anchor=True``).

   .. method:: reltransform(*trafos)

      Applies one or more transformations in place relative to the box's
      ``center`` (translating ``center`` to the origin, applying *trafos*, and
      translating back).

   .. _fig_boxalign:
   .. figure:: boxalign.*
      :align: center

      Aligning boxes on a circle (:meth:`circlealign`) and along a line
      (:meth:`linealign`) for identical direction vectors and distances.

   .. method:: circlealignvector(a, dx, dy)
   .. method:: circlealignvector_pt(a_pt, dx, dy)

      Returns the displacement vector ``(vx, vy)`` required to move the box along
      the direction ``(dx, dy)`` so that its boundary touches a circle of radius
      *a* centered at the box's current ``center`` (see figure
      :ref:`fig_boxalign`).

   .. method:: linealignvector(a, dx, dy)
   .. method:: linealignvector_pt(a_pt, dx, dy)

      Returns the displacement vector ``(vx, vy)`` required to move the box along
      the direction ``(dx, dy)`` so that its boundary touches a line perpendicular
      to ``(dx, dy)`` at distance *a* from the box's current ``center`` (see
      figure :ref:`fig_boxalign`).

   .. method:: circlealign(a, dx, dy)
   .. method:: circlealign_pt(a_pt, dx, dy)

      Translates the box in place by :meth:`circlealignvector` and returns
      ``self``.

   .. method:: linealign(a, dx, dy)
   .. method:: linealign_pt(a_pt, dx, dy)

      Translates the box in place by :meth:`linealignvector` and returns
      ``self``.

   .. method:: extent(dx, dy)
   .. method:: extent_pt(dx, dy)

      Returns the total projected width of the box along the direction
      ``(dx, dy)``.

   .. method:: pointdistance(x, y)
   .. method:: pointdistance_pt(x_pt, y_pt)

      Returns the shortest Euclidean distance from an exterior point ``(x, y)``
      to the boundary of the box.

   .. method:: boxdistance(other)
   .. method:: boxdistance_pt(other, epsilon=1e-10)

      Returns the shortest Euclidean distance between ``self`` and another box
      *other*. Raises :exc:`BoxCrossError` if the two boxes intersect.

   .. method:: bbox()

      Returns the axis-aligned :class:`bbox.bbox_pt` enclosing the box.

.. exception:: BoxCrossError

   Raised by :meth:`polygon.boxdistance` when two boxes have intersecting edges.


Aligning and Tiling Lists of Boxes
==================================

.. function:: circlealignequal(polygons, a, dx, dy)
.. function:: circlealignequal_pt(polygons, a_pt, dx, dy)

   Computes the :meth:`~polygon.circlealignvector` for each box in *polygons* and
   translates all boxes by the longest of those vectors.

.. function:: linealignequal(polygons, a, dx, dy)
.. function:: linealignequal_pt(polygons, a_pt, dx, dy)

   Computes the :meth:`~polygon.linealignvector` for each box in *polygons* and
   translates all boxes by the longest of those vectors. Axis painters use this
   function when ``labelvequalize`` or ``labelhequalize`` is enabled so that all
   tick labels share a uniform baseline alignment.

.. function:: tile(polygons, a, dx, dy)
.. function:: tile_pt(polygons, a_pt, dx, dy)

   Translates the boxes in *polygons* sequentially along ``(dx, dy)`` with step
   size equal to the maximum box extent in direction ``(dx, dy)`` plus separation
   *a*, and returns the step size.


Class :class:`rect`
===================

.. class:: rect(x, y, width, height, relcenter=(0, 0), abscenter=(0, 0))

   Convenience subclass of :class:`polygon` representing an axis-aligned
   rectangle with lower-left corner ``(x, y)`` and dimensions *width* and
   *height* (in user units or PyX lengths). A point-based variant
   :class:`rect_pt` takes coordinates in PostScript points.

   The reference ``center`` of the rectangle is placed at

   .. math::

      (x + \text{relcenter}_x \cdot \text{width} + \text{abscenter}_x,\;
       y + \text{relcenter}_y \cdot \text{height} + \text{abscenter}_y)\ ,

   which defaults to the lower-left corner ``(x, y)`` when ``relcenter=(0, 0)``
   and ``abscenter=(0, 0)``. Set ``relcenter=(0.5, 0.5)`` to place the anchor at
   the geometric center of the rectangle.
