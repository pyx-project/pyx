.. _deformer:

*********
Deformers
*********

.. module:: deformer
   :synopsis: Geometric path deformers

Deformers take an existing path and replace it with a geometrically modified
:class:`normpath.normpath`—for example, rounding sharp corners, constructing an
offset curve at a constant parallel distance, or wrapping a spring-like cycloid
along the path.

All deformers inherit from :class:`baseclasses.deformer` and can be used in two
ways:

1. **As drawing attributes** passed to :meth:`canvas.canvas.stroke`,
   :meth:`canvas.canvas.fill`, or :meth:`canvas.canvas.draw`. When drawing a path,
   PyX applies all deformers in the attribute list in order before applying
   decorators and styles::

      from pyx import *

      c = canvas.canvas()
      p = path.rect(0, 0, 3, 2)
      c.stroke(p, [style.linestyle.dotted])
      c.stroke(p, [deformer.smoothed(0.5), color.rgb.red])
      c.writePDFfile("smoothed")

2. **Directly as path transformations** by calling the deformer's
   :meth:`~smoothed.deform` method on a path or normalized path to obtain the
   deformed :class:`normpath.normpath` for further geometric operations (such as
   intersections or splitting)::

      rounded_rect = deformer.smoothed(0.5).deform(path.rect(0, 0, 3, 2))

Every deformer instance is also callable: calling an existing instance with
keyword arguments returns a new deformer with those parameters updated. Each
deformer class also provides a ``.clear`` attribute (e.g.
``deformer.smoothed.clear``, ``deformer.cycloid.clear``) to remove preceding
instances of that deformer from an attribute list.


Corner smoothing: :class:`smoothed`
===================================

.. class:: smoothed(radius, softness=1, obeycurv=0, relskipthres=0.01)
           cornersmoothed(radius, softness=1, obeycurv=0, relskipthres=0.01)

   Replaces corners between consecutive segments of a path with smooth cubic
   Bézier curves. Within each subpath item, the path is cut back at arc length
   *radius* from the corner (or at the midpoint of the segment if the segment is
   shorter than ``2 * radius``), and the removed corner is bridged as follows:

   - **Between two straight lines**: Two optimized cubic Bézier curves are
     inserted whose curvature vanishes at the transition points to the straight
     lines and whose curvature derivative vanishes at the midpoint of the corner.
     The shape is controlled by *softness* :math:`\in (0, 1]`.
   - **When at least one adjacent segment is curved**: A single cubic Bézier
     curve is inserted that matches the tangents and curvatures of the adjacent
     segments at the cut points.

   Parameters:

   - *radius*: Arc-length distance from each corner at which the original path is
     cut and replaced by the smoothing curve(s).
   - *softness*: Factor in :math:`(0, 1]` controlling how tightly corners between
     straight lines are rounded (default ``1``). Smaller values produce sharper
     bends closer to the original corner.
   - *obeycurv*: When ``0`` (the default), only the magnitude of the curvature is
     matched at curved segments while its sign is chosen to avoid cusps or loops;
     when ``1``, the signed curvature of the adjacent curve is strictly
     preserved.
   - *relskipthres*: Segments shorter than ``relskipthres * radius`` are skipped
     during smoothing (default ``0.01``).

   :class:`cornersmoothed` is the canonical class name; :class:`smoothed` is
   provided as a convenient alias.

   .. method:: deform(basepath)

      Returns a new :class:`normpath.normpath` with all corners of *basepath*
      smoothed.


Parallel offset curves: :class:`parallel`
=========================================

.. class:: parallel(distance, relerr=0.05, sharpoutercorners=False, dointersection=True, checkdistanceparams=[0.5], lookforcurvatures=11, searchstep=0.01, debug=None)

   Constructs a parallel offset curve at a constant normal *distance* from the
   original path.

   A positive *distance* offsets the curve to the **left** of the original path
   (relative to its parameterization direction); a negative *distance* offsets
   it to the **right**. For a counter-clockwise closed path (such as
   :class:`path.rect` or :class:`path.circle`), a negative *distance* therefore
   expands the shape outward, while a positive *distance* shrinks it inward.

   The parallel path is constructed in two stages:

   1. For each segment of the normalized path, an offset line or cubic Bézier
      approximation is built. At convex corners, either a circular arc of radius
      ``abs(distance)`` is inserted around the corner (default) or the offset
      segments are extended to a sharp corner (*sharpoutercorners=True*). Regions
      where the original curve bends more tightly than ``1 / distance`` toward
      the offset side are split at points of infinite curvature.
   2. When *dointersection* is ``True`` (the default), self-intersections and
      loops in the offset path are detected and trimmed away so that only the
      true envelope at distance ``abs(distance)`` from the original path remains.

   Parameters:

   - *distance*: Signed normal offset distance (PyX length).
   - *relerr*: Maximum allowed relative error ``relerr * abs(distance)`` when
     approximating offset Bézier curves (default ``0.05``).
   - *sharpoutercorners*: When ``True``, outer (convex) corners are joined with
     sharp mitered lines instead of circular arcs (default ``False``).
   - *dointersection*: When ``True`` (default), self-intersecting loops in the
     offset curve are removed. Set to ``False`` to keep the raw untrimmed offset
     curve.
   - *checkdistanceparams*: List of parameter values in :math:`(0, 1)` at which
     the normal distance between the original curve and its cubic Bézier
     approximation is verified before subdividing (default ``[0.5]``).
   - *lookforcurvatures*: Number of sample points per curve segment used to
     locate critical curvature crossings :math:`\kappa = 1 / \text{distance}`
     (default ``11``).

   .. method:: deform(basepath)

      Returns the offset :class:`normpath.normpath` at *distance* from
      *basepath*.


Spring / coil paths: :class:`cycloid`
=====================================

.. class:: cycloid(radius=0.5*unit.t_cm, halfloops=10, skipfirst=1*unit.t_cm, skiplast=1*unit.t_cm, curvesperhloop=3, sign=1, turnangle=45)

   Wraps a cycloid (the 2D projection of a 3D helical spring) along the path,
   using the original path as the central axis of the coil. This deformer is
   commonly used in physics and engineering diagrams to draw springs, inductors,
   or gluons.

   Parameters:

   - *radius*: Radius of the cycloid loops perpendicular to the base path
     (default ``0.5 * unit.t_cm``).
   - *halfloops*: Total number of half-loops along the deformed portion of the
     path (default ``10``).
   - *skipfirst*: Arc length at the beginning of each subpath left undeformed as
     a lead-in segment (default ``1 * unit.t_cm``).
   - *skiplast*: Arc length at the end of each subpath left undeformed as a
     lead-out segment (default ``1 * unit.t_cm``).
   - *curvesperhloop*: Number of cubic Bézier segments used to approximate each
     half-loop (default ``3``).
   - *sign*: ``1`` (default) to start the first half-loop to the left of the
     path, or ``-1`` to start to the right.
   - *turnangle*: Viewing angle in degrees of the 3D helix projection (default
     ``45``). Setting ``turnangle=0`` produces a sine-like wave without loops;
     increasing ``turnangle`` toward ``90`` produces tightly overlapping circular
     coils.

   .. method:: deform(basepath)

      Returns a new :class:`normpath.normpath` with the cycloid wrapped along
      each subpath of *basepath* (subpaths shorter than
      ``skipfirst + skiplast + 2 * radius * sin(turnangle)`` are left unchanged
      with a warning).
