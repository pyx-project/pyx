
.. module:: deformer

======================================
Module :mod:`deformer`: Path deformers
======================================

The :mod:`deformer` module provides techniques to generate modulated paths. All
classes in the :mod:`deformer` module can be used as attributes when
drawing/stroking paths onto a canvas. Alternatively new paths can be created by
deforming an existing path by means of the :meth:`deform` method.

All classes of the :mod:`deformer` module provide the following methods:


.. class:: deformer()

.. method:: deformer.__call__((specific parameters for the class))

   Returns a deformer with modified parameters


.. method:: deformer.deform(path)

   Returns the deformed normpath on the basis of the *path*. This method allows
   using the deformers outside of a drawing call.

The deformer classes are the following:


.. class:: cycloid(radius, halfloops=10, skipfirst=1*unit.t_cm, skiplast=1*unit.t_cm, curvesperhloop=3, sign=1, turnangle=45)

   This deformer creates a cycloid around a path. The outcome looks similar to a 3D
   spring stretched along the original path.

   *radius*: the radius of the cycloid (this is the radius of the 3D spring)

   *halfloops*: the number of half-loops of the cycloid

   *skipfirst* and *skiplast*: the lengths on the original path not to be bent to a
   cycloid

   *curvesperhloop*: the number of Bezier curves to approximate a half-loop

   *sign*: for ``sign>=0`` the cycloid starts to the left of the path, whereas
   for ``sign<0`` it starts to the right.

   *turnangle*: the angle of perspective on the 3D spring. At ``turnangle=0``
   results in a sinusoidal curve, whereas for ``turnangle=90`` one essentially
   obtains a circle.


.. class:: smoothed(radius, softness=1, obeycurv=0, relskipthres=0.01)

   This deformer creates a smoothed variant of the original path. The smoothing is
   done on the basis of the corners of the original path, not on a global scope!
   Therefore, the result might not be what one would draw by hand. At each corner
   (or wherever two path elements meet) a piece of twice the *radius*
   is taken out of the original path and replaced by a curve. This curve is
   determined by the tangent directions and the curvatures at its endpoints. Both
   are taken from the original path, and therefore, the new curve fits into the gap
   in a *geometrically smooth* way. Path elements that are shorter than
   *radius* :math:`\times` *relskipthres* are ignored.

   The new curve smoothing the corner consists either of one or of two Bezier
   curves, depending on the surrounding path elements. If there are straight lines
   before and after the new curve, then two Bezier curves are used. This optimises
   the bending of curves in rectangular boxes or polygons. Here, the curves have an
   additional degree of freedom that can be set with *softness* :math:`\in(0,1]`.
   If one of the concerned path elements is curved, only one Bezier curve is used
   that is (not always uniquely) determined by its geometrical constraints. There
   are, nevertheless, some *caveats*:

   A curve that strictly obeys the sign and magnitude of the curvature might not
   look very smooth in some cases. Especially when connecting a curved with a
   straight piece, the smoothed path contains unwanted overshootings. To prevent
   this, the parameter default *obeycurv=0* releases the curvature constraints a
   little: The curvature may then change its sign (still looks smooth for human
   eyes) or, in more extreme cases, even its magnitude (does not look so smooth).
   If you really need a geometrically smooth path on the basis of Bezier curves,
   then set *obeycurv=1*.


.. class:: parallel(distance, relerr=0.05, sharpoutercorners=0, dointersection=1, checkdistanceparams=[0.5], lookforcurvatures=11)

   This deformer creates a parallel curve to a given path. The result is similar to
   what is usually referred to as the *set with constant distance* to the set of
   points on the path. It differs in one important respect, because the *distance*
   parameter in the deformer is a signed distance. The resulting parallel normpath
   is constructed on the level of the original pathitems. For each of them a
   parallel pathitem is constructed. Then, they are connected by circular arcs (or
   by sharp edges) around the corners of the original path. Later, everything that
   is nearer to the original path than distance is cut away.

   There are some caveats:

   * When the original path is too curved then the parallel path would contain
     points with infinte curvature. The resulting path stops at such points and
     leaves the too strongly curved piece out.

   * When the original path contains on or more self-intersections, then the
     resulting parallel path is not continuous in the parameterisation of the
     original path. This may result in the surprising behaviour that a piece
     that corresponding to a "later" parameter value is followed by an
     "earlier" one.

   The parameters are the following:

   *distance* is the minimal (signed) distance between the original and the
   parallel paths.

   *relerr* is the allowed relative error in the distance.

   *sharpoutercorners* connects the parallel pathitems by a wegde made of
   straight lines, instead of taking circular arcs. This preserves the angle of
   the original corners.

   *dointersection* is a boolean for performing the last step, the intersection
   step, in the path construction. Setting this to 0 gives the full parallel path,
   which can be favourable for self-intersecting paths.

   *checkdistanceparams* is a list of parameter values in the interval (0,1) where
   the distance is checked on each parallel pathitem.

   *lookforcurvatures* is the number of points per normpathitem where its curvature
   is checked for critical values.
