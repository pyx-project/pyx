.. _path:

*****
Paths
*****

.. module:: path
   :synopsis: PostScript-style paths and predefined geometric shapes

Paths are the geometric backbone of PyX. A path describes a sequence of connected
or disconnected line segments, circular or elliptical arcs, and cubic Bézier
curves in the plane.

PyX provides two complementary representations of paths:

1. :class:`path.path`: A PostScript-style path composed of arbitrary
   :class:`pathitem` instances (:class:`moveto`, :class:`lineto`,
   :class:`curveto`, :class:`arc`, :class:`closepath`, etc.). When written to
   PostScript or SVG, these path items map directly to native PostScript operators
   or SVG path commands.
2. :class:`normpath.normpath`: A *normalized path* consisting of a list of
   :class:`normpath.normsubpath` objects, which in turn contain only straight
   lines (:class:`normpath.normline_pt`) and cubic Bézier curves
   (:class:`normpath.normcurve_pt`) in absolute point coordinates, subject to a
   numerical accuracy *epsilon* (default :math:`10^{-5}\,\text{pt}`). All
   advanced geometric operations—such as computing arc lengths, finding
   intersections, splitting paths, or evaluating tangents and curvatures—are
   performed on normalized paths.

Because :class:`path.path` automatically delegates geometric queries to its
cached :meth:`path.normpath` representation, you can call methods like
:meth:`path.intersect`, :meth:`path.at`, :meth:`path.split`, or
:meth:`path.tangent` directly on any :class:`path.path` instance.


Constructing paths
==================

A :class:`path` can be constructed either by passing :class:`pathitem` instances
to :class:`path` or by using one of the predefined shape classes such as
:class:`line`, :class:`rect`, :class:`circle`, :class:`ellipse`, or
:class:`curve`.

For example, to construct a triangle with a rounded top corner and intersect it
with a circle::

   from pyx import *

   c = canvas.canvas()
   triangle = path.path(path.moveto(0, 0),
                        path.lineto(4, 0),
                        path.arct(2, 3, 0, 0, 0.5),
                        path.closepath())
   circle = path.circle(2, 1, 1.5)

   c.stroke(triangle)
   c.stroke(circle, [color.rgb.blue])

   # Mark all intersection points with small red circles
   for p in triangle.intersect(circle)[0]:
       x, y = triangle.at(p)
       c.fill(path.circle(x, y, 0.08), [color.rgb.red])

   c.writePDFfile("intersect")

Two paths can be combined in two different ways:

- **Addition** (``p = p1 + p2`` or ``p1 += p2``): Concatenates the subpaths of
  ``p1`` and ``p2`` into a single compound path without connecting the end of
  ``p1`` to the start of ``p2``.
- **Joining** (``p = p1 << p2`` or ``p = p1.joined(p2)`` or ``p1.join(p2)``):
  Connects the end of the last open subpath of ``p1`` to the beginning of the
  first open subpath of ``p2`` (inserting a straight line segment if the two
  endpoints do not coincide) so that they form a single continuous subpath.


Path items
==========

Every element passed to :class:`path` must be an instance of a subclass of
:class:`pathitem`. Each coordinate-accepting class has both a standard version
(taking coordinates in PyX user lengths or explicit :mod:`unit` lengths) and a
``_pt`` version (taking coordinates in PostScript points).

Subpath control
---------------

.. class:: moveto(x, y)
           moveto_pt(x_pt, y_pt)

   Starts a new subpath and sets the current point to :math:`(x, y)`.

.. class:: rmoveto(dx, dy)
           rmoveto_pt(dx_pt, dy_pt)

   Starts a new subpath and moves the current point by :math:`(\Delta x, \Delta y)`
   relative to the previous current point.

.. class:: closepath()

   Closes the current subpath by connecting the current point back to the
   starting point of the subpath with a straight line segment.


Straight lines
--------------

.. class:: lineto(x, y)
           lineto_pt(x_pt, y_pt)

   Appends a straight line segment from the current point to :math:`(x, y)`,
   which becomes the new current point.

.. class:: rlineto(dx, dy)
           rlineto_pt(dx_pt, dy_pt)

   Appends a straight line segment from the current point :math:`(x_0, y_0)` to
   :math:`(x_0 + \Delta x, y_0 + \Delta y)`, which becomes the new current point.

.. class:: multilineto_pt(points_pt)

   Appends straight line segments from the current point through a sequence of
   coordinate pairs ``[(x1_pt, y1_pt), (x2_pt, y2_pt), ...]`` in points. This
   class is provided for performance when constructing polylines with many
   vertices.


Circular arcs
-------------

.. class:: arc(x, y, r, angle1, angle2)
           arc_pt(x_pt, y_pt, r_pt, angle1, angle2)

   Appends a counterclockwise circular arc centered at :math:`(x, y)` with
   radius *r* from *angle1* to *angle2* (in degrees). If the path already has a
   current point in an open subpath, a straight line segment is first added from
   the current point to the starting point of the arc; otherwise, the arc starts
   a new subpath. After the arc is added, the current point is the endpoint of
   the arc at *angle2*.

.. class:: arcn(x, y, r, angle1, angle2)
           arcn_pt(x_pt, y_pt, r_pt, angle1, angle2)

   Same as :class:`arc`, except that the arc is drawn in the clockwise direction
   from *angle1* down to *angle2*.

.. class:: arct(x1, y1, x2, y2, r)
           arct_pt(x1_pt, y1_pt, x2_pt, y2_pt, r_pt)

   Appends a circular arc of radius *r* that is tangent both to the line from the
   current point :math:`(x_0, y_0)` to :math:`(x_1, y_1)` and to the line from
   :math:`(x_1, y_1)` to :math:`(x_2, y_2)`. A straight line segment is first
   drawn from :math:`(x_0, y_0)` to the first point of tangency :math:`(x_{t,1},
   y_{t,1})`, followed by the tangent arc ending at the second point of tangency
   :math:`(x_{t,2}, y_{t,2})`, which becomes the new current point:

   .. figure:: arct.*
      :align: center


Bézier curves
-------------

.. class:: curveto(x1, y1, x2, y2, x3, y3)
           curveto_pt(x1_pt, y1_pt, x2_pt, y2_pt, x3_pt, y3_pt)

   Appends a cubic Bézier curve from the current point :math:`(x_0, y_0)` to
   :math:`(x_3, y_3)` with first control point :math:`(x_1, y_1)` and second
   control point :math:`(x_2, y_2)`. The parametric curve is given by

   .. math::

      \mathbf{B}(t) = (1-t)^3 \mathbf{P}_0 + 3(1-t)^2 t \mathbf{P}_1
                    + 3(1-t) t^2 \mathbf{P}_2 + t^3 \mathbf{P}_3,
      \quad t \in [0, 1].

   After the curve is added, :math:`(x_3, y_3)` becomes the new current point.

.. class:: rcurveto(dx1, dy1, dx2, dy2, dx3, dy3)
           rcurveto_pt(dx1_pt, dy1_pt, dx2_pt, dy2_pt, dx3_pt, dy3_pt)

   Appends a cubic Bézier curve whose control points and endpoint are specified
   relative to the current point :math:`(x_0, y_0)` before the operation:
   :math:`(x_0 + \Delta x_1, y_0 + \Delta y_1)`,
   :math:`(x_0 + \Delta x_2, y_0 + \Delta y_2)`, and
   :math:`(x_0 + \Delta x_3, y_0 + \Delta y_3)`.

.. class:: multicurveto_pt(points_pt)

   Appends multiple cubic Bézier curves from a sequence of 6-tuples
   ``[(x1_pt, y1_pt, x2_pt, y2_pt, x3_pt, y3_pt), ...]`` in points, provided for
   performance when constructing paths with many curve segments.


Class :class:`path`
===================

.. class:: path(*pathitems)

   Constructs a path from the given *pathitems*.

   A :class:`path` instance supports sequence indexing (``p[i]`` returns the
   *i*-th :class:`pathitem`), ``len(p)`` (number of path items), ``p1 + p2`` and
   ``p1 += p2`` (concatenating subpaths), and ``p1 << p2`` (joining paths via
   :meth:`joined`).

   .. note::

      In the methods below, any parameter *params* that specifies a location (or
      a list/tuple of locations) along the path accepts either:

      - a :class:`normpath.normpathparam` instance (as returned by :meth:`begin`,
        :meth:`end`, :meth:`arclentoparam`, or :meth:`intersect`), or
      - a PyX length (or number in user units, or in points for ``_pt`` methods),
        which is automatically interpreted as the arc length measured from the
        beginning of the path!

      Furthermore, methods decorated to accept *params* or *lengths* (such as
      :meth:`at`, :meth:`arclentoparam`, :meth:`paramtoarclen`,
      :meth:`curvature_pt`, :meth:`rotation`, :meth:`tangent`, and :meth:`trafo`)
      return a single value when passed a single parameter, and a list of values
      when passed a sequence of parameters.

   .. method:: append(apathitem)

      Appends a single :class:`pathitem` to the path in place.

   .. method:: extend(pathitems)

      Appends an iterable of :class:`pathitem` instances to the path in place.

   .. method:: arclen()
               arclen_pt()

      Returns the total arc length of the path as a PyX length (or in points).

   .. method:: arclentoparam(lengths)
               arclentoparam_pt(lengths_pt)

      Returns the :class:`normpath.normpathparam` instance(s) corresponding to
      the given arc length(s).

   .. method:: paramtoarclen(params)
               paramtoarclen_pt(params)

      Returns the arc length(s) (as PyX lengths or in points) corresponding to
      the given :class:`normpath.normpathparam` instance(s).

   .. method:: at(params)
               at_pt(params)

      Returns the coordinate tuple ``(x, y)`` of PyX lengths (or ``(x_pt, y_pt)``
      in points) at the specified parameter(s) or arc length(s).

   .. method:: atbegin()
               atbegin_pt()

      Returns the coordinate tuple ``(x, y)`` (or ``(x_pt, y_pt)``) of the start
      point of the first subpath.

   .. method:: atend()
               atend_pt()

      Returns the coordinate tuple ``(x, y)`` (or ``(x_pt, y_pt)``) of the end
      point of the last subpath.

   .. method:: begin()

      Returns the :class:`normpath.normpathparam` corresponding to the beginning
      of the path.

   .. method:: end()

      Returns the :class:`normpath.normpathparam` corresponding to the end of
      the path.

   .. method:: bbox()

      Returns the exact :class:`bbox.bbox` enclosing the path.

   .. method:: curvature_pt(params)

      Returns the signed curvature in :math:`\text{pt}^{-1}` at the specified
      parameter(s) or arc length(s) in points. The curvature is positive when
      the path turns to the left (counterclockwise) and negative when it turns to
      the right.

   .. method:: intersect(other)

      Intersects the path with *other* (another :class:`path` or
      :class:`normpath.normpath`) and returns a 2-tuple ``(params_self,
      params_other)`` of lists of :class:`normpath.normpathparam` instances for
      the intersection points along ``self`` and ``other``, sorted along
      ``self``.

   .. method:: join(other)

      Joins *other* to the end of ``self`` in place and returns ``self``.

   .. method:: joined(other)

      Returns a new path consisting of ``self`` and *other* joined together
      (also available via the ``<<`` operator: ``self << other``).

   .. method:: normpath(epsilon=...)

      Converts the path into a :class:`normpath.normpath` instance. When
      *epsilon* is omitted, the default normalized path is cached on the path
      instance.

   .. method:: path()

      Returns ``self`` (provided so that :class:`path` and
      :class:`normpath.normpath` can be used interchangeably).

   .. method:: reversed()

      Returns a new :class:`normpath.normpath` with the orientation of all
      subpaths reversed.

   .. method:: rotation(params)
               rotation_pt(params)

      Returns a :class:`trafo.trafo` rotation at *params* (or arc lengths) that
      rotates the positive *x*-axis onto the unit tangent vector of the path and
      the positive *y*-axis onto the left-hand normal vector.

   .. method:: split(params)
               split_pt(params)

      Splits the normalized path at the given parameter(s) or arc length(s) and
      returns a list of :class:`normpath.normpath` segments. Note thateven when a
      single split point is passed, a list of two path segments is returned.

   .. method:: tangent(params, length=1)
               tangent_pt(params, length_pt)

      Returns a :class:`normpath.normpath` line segment of length *length*
      (default 1 user unit) starting at the point *params* and pointing in the
      tangent direction of the path.

   .. method:: trafo(params)
               trafo_pt(params)

      Returns a :class:`trafo.trafo` transformation at *params* (or arc lengths)
      that maps the origin :math:`(0, 0)` to the point on the path and rotates
      the coordinate axes so that the local *x*-axis points along the path
      tangent and the local *y*-axis points along the left-hand normal.

   .. method:: transformed(trafo)

      Returns a new :class:`normpath.normpath` transformed according to the
      affine transformation *trafo*.


Normalized paths: :mod:`normpath`
=================================

.. module:: normpath
   :synopsis: Normalized paths, subpaths, and path parameterization

While casual users rarely need to instantiate classes from :mod:`normpath`
directly, PyX developers and advanced users working with intersections, path
splitting, or custom decorators and deformers interact closely with
:class:`normpath`, :class:`normsubpath`, and :class:`normpathparam`.

Why normalized paths?
---------------------

PostScript paths can contain arcs, relative displacements, and unclosed or
implicitly connected subpaths. Evaluating intersections or arc-length integrals
directly on such heterogeneous items would be error-prone and slow. PyX
therefore normalizes any :class:`path.path` into a :class:`normpath`:

- A :class:`normpath` is a list of :class:`normsubpath` instances.
- Each :class:`normsubpath` is a contiguous open or closed chain of
  :class:`normsubpathitem` instances—exclusively :class:`normline_pt` (straight
  lines) and :class:`normcurve_pt` (cubic Bézier curves)—together with a
  precision length *epsilon* (default :math:`10^{-5}\,\text{pt}`).
- Line or curve segments shorter than *epsilon* are accumulated as a
  ``skippedline`` rather than creating degenerate zero-length items with
  undefined tangents, and are merged into the adjacent segment once the
  accumulated displacement exceeds *epsilon*.

.. function:: set(epsilon=None)

   Sets the global default accuracy *epsilon* in points (initially ``1e-5``) used
   when constructing new :class:`normsubpath` instances.


Class :class:`normpathparam`
----------------------------

.. class:: normpathparam(normpath, normsubpathindex, normsubpathparam)

   Identifies a point along *normpath*. Here *normsubpathindex* is the integer
   index of the :class:`normsubpath` within *normpath*, and *normsubpathparam* is
   a floating-point parameter :math:`t` along that subpath, where the integer
   part :math:`\lfloor t \rfloor` selects the :class:`normsubpathitem` and the
   fractional part :math:`t - \lfloor t \rfloor \in [0, 1]` is the parameter on
   that line or Bézier curve.

   :class:`normpathparam` instances support rich arithmetic and comparisons via
   arc length:

   - Adding or subtracting a PyX length (e.g. ``p + 0.5*unit.t_cm`` or ``p - 1``)
     moves along the path by that arc length and returns the resulting
     :class:`normpathparam`!
   - Adding or subtracting two :class:`normpathparam` instances belonging to the
     same :class:`normpath`, or multiplying/dividing a :class:`normpathparam` by
     a scalar factor, operates on their arc lengths and returns the corresponding
     :class:`normpathparam`.
   - Comparing two :class:`normpathparam` instances (``p1 < p2``, ``p1 == p2``)
     compares their positions ``(normsubpathindex, normsubpathparam)`` along the
     path; comparing a :class:`normpathparam` with a length compares its arc
     length from the start of the path with that length.

   .. method:: arclen()
               arclen_pt()

      Returns the arc length from the beginning of the :class:`normpath` up to
      this parameter position as a PyX length (or in points).


Class :class:`normpath`
-----------------------

.. class:: normpath(normsubpaths=None)

   Constructs a normalized path from a list of :class:`normsubpath` instances (or
   an empty list if ``None``).

   :class:`normpath` provides all the geometric and manipulation methods of
   :class:`path.path` (:meth:`path.path.append`, :meth:`path.path.extend`,
   :meth:`path.path.arclen`, :meth:`path.path.arclen_pt`,
   :meth:`path.path.arclentoparam`, :meth:`path.path.arclentoparam_pt`,
   :meth:`path.path.at`, :meth:`path.path.at_pt`, :meth:`path.path.atbegin`,
   :meth:`path.path.atbegin_pt`, :meth:`path.path.atend`,
   :meth:`path.path.atend_pt`, :meth:`path.path.bbox`, :meth:`path.path.begin`,
   :meth:`path.path.end`, :meth:`path.path.curvature_pt`,
   :meth:`path.path.intersect`, :meth:`path.path.join`,
   :meth:`path.path.joined`, :meth:`path.path.normpath`,
   :meth:`path.path.paramtoarclen`, :meth:`path.path.paramtoarclen_pt`,
   :meth:`path.path.reversed`, :meth:`path.path.rotation`,
   :meth:`path.path.rotation_pt`, :meth:`path.path.split`,
   :meth:`path.path.split_pt`, :meth:`path.path.tangent`,
   :meth:`path.path.tangent_pt`, :meth:`path.path.trafo`,
   :meth:`path.path.trafo_pt`, and :meth:`path.path.transformed`), plus:

   .. method:: copy()

      Returns a deep copy of the :class:`normpath` and all its subpaths.

   .. method:: path()

      Converts the :class:`normpath` back into an equivalent :class:`path.path`
      consisting of :class:`path.moveto_pt`, :class:`path.lineto_pt`,
      :class:`path.curveto_pt`, and :class:`path.closepath` items.

   Indexing ``np[i]`` returns the *i*-th :class:`normsubpath`, and ``len(np)``
   returns the number of subpaths.


Class :class:`normsubpath` and subpath items
--------------------------------------------

.. class:: normsubpath(normsubpathitems=[], closed=0, epsilon=_marker)

   Represents a single connected open or closed normalized subpath.

   - *normsubpathitems*: List of :class:`normline_pt` and :class:`normcurve_pt`
     instances. Adjacent items must share endpoints within *epsilon*.
   - *closed*: Boolean or integer flag indicating whether the subpath is closed.
   - *epsilon*: Precision threshold in points (defaults to the module-level
     ``normpath._epsilon = 1e-5``, or ``None`` to disable filtering of short
     segments).

   Key attributes and methods:

   .. attribute:: normsubpathitems

      The list of :class:`normline_pt` and :class:`normcurve_pt` items in the
      subpath.

   .. attribute:: closed

      Whether the subpath is closed.

   .. attribute:: epsilon

      Accuracy threshold in points for this subpath.

   .. method:: append(anormsubpathitem)
               extend(normsubpathitems)

      Appends one or more :class:`normsubpathitem` instances to an open subpath,
      automatically coalescing segments shorter than :attr:`epsilon`.

   .. method:: close()

      Closes the subpath in place, appending a closing :class:`normline_pt` back
      to the start point if necessary.

   .. method:: segments(params)

      Takes a sequence of at least two subpath parameter floats and returns a
      list of :class:`normsubpath` instances for the segments between consecutive
      parameters.

   .. method:: pathitems()

      Returns the list of :class:`path.pathitem` instances representing this
      subpath.

.. class:: normline_pt(x0_pt, y0_pt, x1_pt, y1_pt)

   A normalized straight line segment from ``(x0_pt, y0_pt)`` to
   ``(x1_pt, y1_pt)`` in points.

.. class:: normcurve_pt(x0_pt, y0_pt, x1_pt, y1_pt, x2_pt, y2_pt, x3_pt, y3_pt)

   A normalized cubic Bézier curve segment with control points ``(x0_pt, y0_pt)``
   through ``(x3_pt, y3_pt)`` in points.


Predefined shapes
=================

.. module:: path
   :noindex:

For convenience, :mod:`path` provides subclasses of :class:`path` for common
geometric primitives, each in a user-length version and a ``_pt`` version:

.. class:: line(x1, y1, x2, y2)
           line_pt(x1_pt, y1_pt, x2_pt, y2_pt)

   A straight line segment from :math:`(x_1, y_1)` to :math:`(x_2, y_2)`.

.. class:: curve(x0, y0, x1, y1, x2, y2, x3, y3)
           curve_pt(x0_pt, y0_pt, x1_pt, y1_pt, x2_pt, y2_pt, x3_pt, y3_pt)

   A single cubic Bézier curve from :math:`(x_0, y_0)` to :math:`(x_3, y_3)` with
   control points :math:`(x_1, y_1)` and :math:`(x_2, y_2)`.

.. class:: rect(x, y, width, height)
           rect_pt(x_pt, y_pt, width_pt, height_pt)

   A closed axis-aligned rectangle with lower-left corner :math:`(x, y)`,
   *width*, and *height*.

.. class:: circle(x, y, radius, arcepsilon=0.1)
           circle_pt(x_pt, y_pt, radius_pt, arcepsilon=0.1)

   A closed circle with center :math:`(x, y)` and *radius* (constructed from a
   counterclockwise arc from ``arcepsilon`` to ``360 - arcepsilon`` degrees
   closed with :class:`closepath`).

.. class:: ellipse(x, y, a, b, angle, **kwargs)
           ellipse_pt(x_pt, y_pt, a_pt, b_pt, angle, **kwargs)

   A closed ellipse centered at :math:`(x, y)` with semi-axes *a* and *b*, where
   the first axis *a* is rotated counterclockwise by *angle* degrees relative to
   the positive *x*-axis.
