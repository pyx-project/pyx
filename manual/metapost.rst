.. _metapost:

********************
MetaPost-like paths
********************

.. module:: metapost.path
   :synopsis: Smooth spline paths using the Hobby-Knuth MetaPost algorithm

In addition to constructing paths with explicit Bézier control points via
:mod:`path`, PyX provides the :mod:`metapost.path` module, which implements the
spline-choosing algorithm of John Hobby and Donald Knuth from MetaPost. Instead
of specifying control points manually, you specify a sequence of *knots* (points
through which the curve must pass, optionally with tangent angles or endpoint
curvatures) separated by *links* (such as smooth curves with adjustable tension
or straight lines). PyX then solves the global system of equations to determine
cubic Bézier control points that maintain continuous tangents and "mock"
curvatures at all interior smooth knots.

The resulting :class:`metapost.path.path` is a subclass of
:class:`normpath.normpath`, so it supports all standard PyX path and normalized
path operations (such as stroking, filling, intersecting, splitting, and
deforming).


Example
=======

To draw a closed smooth curve passing through four points, and an open curve with
prescribed start and end tangent angles::

   from pyx import *
   from pyx.metapost.path import beginknot, endknot, smoothknot, roughknot, curve, line

   c = canvas.canvas()

   # Closed smooth loop through three knots
   closed_loop = metapost.path.path([
       smoothknot(0, 0), curve(),
       smoothknot(2, 1), curve(),
       smoothknot(1, 2.5), curve()
   ])
   c.stroke(closed_loop, [color.rgb.blue])

   # Open curve starting at 45 degrees and ending with a straight line segment
   open_curve = metapost.path.path([
       beginknot(3, 0, angle=45), curve(ltension=1.2),
       smoothknot(4.5, 1.5), line(keepangles=True),
       endknot(6, 0.5)
   ])
   c.stroke(open_curve, [color.rgb.red])

   c.writePDFfile("metapost")


Path construction: :class:`path`
================================

.. class:: path(elems, epsilon=None)

   Constructs a :class:`normpath.normpath` from a list *elems* of alternating
   knots and links.

   - If *elems* begins with a :class:`beginknot` and ends with an
     :class:`endknot`, an open path is constructed.
   - If *elems* contains only interior knots (:class:`smoothknot` or
     :class:`roughknot`) and links, the last link connects the last knot back to
     the first knot, forming a closed path.
   - Multiple open subpaths can be constructed within a single :class:`path` by
     placing an :class:`endknot` followed immediately by a new
     :class:`beginknot` (without a link between them).
   - *epsilon* specifies the numerical precision in points used for the resulting
     :class:`normpath.normsubpath` (defaulting to the module-level precision set
     via :func:`set`).

.. function:: set(epsilon=None)

   Sets the module-level default precision *epsilon* in points (initially
   ``1e-5``).


Knots
=====

Knots define the points through which the path passes and specify boundary or
continuity conditions for the incoming (left) and outgoing (right) curve
segments. Every knot class is available both in a user-length version (where
angles are given in **degrees**) and a ``_pt`` version (where coordinates are
given in points and angles in **radians**).

.. class:: beginknot(x, y, curl=1, angle=None)
           beginknot_pt(x_pt, y_pt, curl=1, angle=None)
           startknot(x, y, curl=1, angle=None)

   Starts an open subpath at :math:`(x, y)`. You may specify either the relative
   endpoint curvature *curl* (default ``1``, meaning the curvature at the
   endpoint matches that of the adjacent knot) or an explicit outgoing tangent
   direction *angle* (in degrees for :class:`beginknot`, or radians for
   :class:`beginknot_pt`). :class:`startknot` is an alias for :class:`beginknot`.

.. class:: endknot(x, y, curl=1, angle=None)
           endknot_pt(x_pt, y_pt, curl=1, angle=None)

   Ends an open subpath at :math:`(x, y)`. You may specify either the relative
   endpoint curvature *curl* (default ``1``) or an explicit incoming tangent
   direction *angle* (in degrees for :class:`endknot`, or radians for
   :class:`endknot_pt`).

.. class:: smoothknot(x, y)
           smoothknot_pt(x_pt, y_pt)
           knot(x, y)

   An interior knot at :math:`(x, y)` where both the tangent direction and the
   mock curvature are continuous across the knot. :class:`knot` is an alias for
   :class:`smoothknot`.

.. class:: roughknot(x, y, lcurl=1, rcurl=None, langle=None, rangle=None)
           roughknot_pt(x_pt, y_pt, lcurl=1, rcurl=None, langle=None, rangle=None)

   An interior knot at :math:`(x, y)` where the curve may have a corner or
   prescribed left/right curls or tangent angles.

   - On the incoming (left) side, specify either *lcurl* (default ``1``) or
     *langle* (incoming tangent angle).
   - On the outgoing (right) side, specify either *rcurl* or *rangle* (outgoing
     tangent angle). If neither *rcurl* nor *rangle* is given, the right-side
     condition defaults to the same type and value as the left-side condition
     (so ``roughknot(x, y, langle=30)`` produces a smooth tangent at 30 degrees,
     whereas ``roughknot(x, y, langle=30, rangle=90)`` produces a sharp corner).


Links
=====

Links are placed between consecutive knots in the list passed to :class:`path`
and determine how the two knots are connected.

.. class:: tensioncurve(ltension=1, latleast=False, rtension=None, ratleast=None)
           curve(ltension=1, latleast=False, rtension=None, ratleast=None)

   Connects two knots with a cubic Bézier spline segment determined by the
   MetaPost solver.

   - *ltension*: Tension at the starting (left) knot of the segment (default
     ``1``; must be at least ``0.75``). Higher tension pulls the curve tighter
     toward a straight line between the knots.
   - *latleast*: When ``True``, corresponds to MetaPost's ``tension atleast``
     directive at the starting knot, which increases the tension automatically
     if needed to avoid inflection points near the knot.
   - *rtension*: Tension at the ending (right) knot of the segment (defaults to
     *ltension* when ``None``).
   - *ratleast*: When ``True``, applies ``tension atleast`` at the ending knot
     (defaults to *latleast* when ``None``).

   :class:`curve` is an alias for :class:`tensioncurve`.

.. class:: controlcurve(lcontrol, rcontrol)
           controlcurve_pt(lcontrol_pt, rcontrol_pt)

   Connects two knots with a cubic Bézier curve whose two control points are set
   explicitly to the coordinate 2-tuples *lcontrol* and *rcontrol* (in user
   coordinates or points). Adjacent smooth curves on either side of those knots
   will adapt their tangents and curvatures to match this explicit segment.

.. class:: line(keepangles=False)

   Connects two knots with a straight line segment.

   - When *keepangles* is ``False`` (the default), the straight line acts as an
     endpoint boundary for adjacent curves (equivalent to ``--`` in MetaPost),
     allowing corners at the knots.
   - When *keepangles* is ``True``, the tangent directions of the curves entering
     the left knot and leaving the right knot are constrained to match the angle
     of the straight line segment (equivalent to ``---`` in MetaPost), ensuring a
     smooth tangent transition into and out of the straight segment.
