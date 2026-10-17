.. module:: connector
   :synopsis: Connecting paths (lines, arcs, curves, and polylines) between boxes

.. _connector:

***********************
Module :mod:`connector`
***********************

The :mod:`connector` module constructs paths (:class:`normpath.normpath`
subclasses) that connect two :class:`box.polygon` instances (such as
:class:`text.textextbox_pt` / :class:`text.unicodetextbox_pt` objects or
:class:`box.rect` boxes) using straight lines, circular arcs, cubic Bézier
curves, or two-segment polylines.

Geometry, Angles, and Bulges
============================

All connector classes take two box instances (*box1* and *box2*) as their first
two arguments and construct a path leading from *box1* to *box2*:

1. The geometric curve is constructed between the centers (``box1.center`` and
   ``box2.center``) of the two boxes.
2. The path is then trimmed at its intersections with the boundary outlines of
   *box1* and *box2*.
3. Finally, the trimmed path can be shortened at its start and end by the
   distances specified in *boxdists* (a 2-element sequence ``[dist1, dist2]``,
   defaulting to ``[0, 0]``).

.. code-block:: python

   from pyx import *

   c = canvas.canvas()
   b1 = c.text(0, 0, "Start", [text.halign.center, text.vshift.mathaxis])
   b2 = c.text(4, 1, "End", [text.halign.center, text.vshift.mathaxis])

   c.stroke(connector.arc(b1, b2, boxdists=[0.2, 0.2]), [deco.earrow.normal])

Angles and Bulge Parameters
---------------------------

Connectors that bend (:class:`arc`, :class:`curve`, and :class:`twolines`) are
parameterized by tangent angles and/or bulge distances (illustrated in figure
:ref:`fig_connector`):

* **Relative vs. absolute angles**:
  Relative angles (*relangle*, *relangle1*, *relangle2*) are measured in degrees
  relative to the straight line connecting ``box1.center`` to ``box2.center``.
  Absolute angles (*absangle1*, *absangle2*) are measured counter-clockwise from
  the positive *x*-axis. Whenever both an absolute and a relative angle are
  specified for the same endpoint, the absolute angle takes precedence.
* **Bulge distances**:
  Bulge parameters (*relbulge* and *absbulge*) control how far the connector
  deviates from the straight line between the box centers. *relbulge* is a
  dimensionless fraction of the center-to-center distance, whereas *absbulge* is
  an absolute PyX length. If both *relbulge* and *absbulge* are given, their
  contributions are summed.

.. _fig_connector:
.. figure:: connector.*
   :align: center

   Geometric meaning of the angle and bulge parameters for :class:`connector.arc`
   (left) and :class:`connector.curve` (right).


Connector Classes
=================

Each connector class is available both in user units (e.g. :class:`line`,
:class:`arc`, :class:`curve`, :class:`twolines`) and in PostScript points (with a
``_pt`` suffix, where *boxdists* and *absbulge* are given in points).

.. class:: line(box1, box2, boxdists=(0, 0))

   Connects *box1* and *box2* with a straight line segment between their centers,
   trimmed at the box outlines and shortened by *boxdists*.

.. class:: arc(box1, box2, relangle=45, absbulge=None, relbulge=None, boxdists=[0, 0])

   Connects *box1* and *box2* with a circular arc.

   * *relangle*: Angle (in degrees) between the chord connecting the box centers
     and the arc's tangent at the centers (default ``45``).
   * *absbulge*, *relbulge*: Maximum perpendicular distance (sagitta) between the
     arc and the straight chord connecting the box centers. Specifying either
     *absbulge* or *relbulge* overrides *relangle*.

.. class:: curve(box1, box2, relangle1=45, relangle2=45, absangle1=None, absangle2=None, absbulge=0, relbulge=0.39, boxdists=[0, 0])

   Connects *box1* and *box2* with a cubic Bézier curve. Here the bulge specifies
   the distance from each box center to the corresponding Bézier control point
   along the departure/arrival tangent direction (see the right panel of figure
   :ref:`fig_connector` for sign conventions).

   * *relangle1*, *relangle2*: Departure and arrival tangent angles relative to
     the center-to-center line (default ``45`` for both).
   * *absangle1*, *absangle2*: Absolute departure and arrival tangent angles in
     degrees (override *relangle1* / *relangle2* if given).
   * *absbulge*, *relbulge*: Control-point distances (default ``relbulge=0.39``,
     which closely approximates a circular arc when ``relangle1 = relangle2 = 45``).

.. class:: twolines(box1, box2, absangle1=None, absangle2=None, relangle1=None, relangle2=None, relangleM=None, length1=None, length2=None, bezierradius=None, beziersoftness=1, arcradius=None, boxdists=[0, 0])

   Connects *box1* and *box2* with a two-segment polyline meeting at an
   intermediate corner point. You must supply an unambiguous combination of two
   constraints chosen from the departure angle (*absangle1* or *relangle1*),
   arrival angle (*absangle2* or *relangle2*), interior angle between the two
   segments (*relangleM*), first segment length (*length1*), or second segment
   length (*length2*).
