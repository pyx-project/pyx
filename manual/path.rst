.. module:: path

==================
Module :mod:`path`
==================

.. sectionauthor:: Jörg Lehmann <joergl@users.sourceforge.net>


The :mod:`path` module defines several important classes which are documented in
the present section.


Class :class:`path` --- PostScript-like paths
---------------------------------------------

.. class:: path(*pathitems)

   This class represents a PostScript like path consisting of the path elements
   *pathitems*.

   All possible path items are described in Sect. :ref:`path_pathitem`. Note that
   there are restrictions on the first path element and likewise on each path
   element after a :class:`closepath` directive. In both cases, no current point is
   defined and the path element has to be an instance of one of the following
   classes: :class:`moveto`, :class:`arc`, and :class:`arcn`.

Instances of the class :class:`path` provide the following methods (in
alphabetic order):


.. method:: path.append(pathitem)

   Appends a *pathitem* to the end of the path.


.. method:: path.arclen()

   Returns the total arc length of the path.\ :math:`^\dagger`


.. method:: path.arclentoparam(lengths)

   Returns the parameter value(s) corresponding to the arc length(s) *lengths*.\
   :math:`^\dagger`


.. method:: path.at(params)

   Returns the coordinates (as 2-tuple) of the path point(s) corresponding to the
   parameter value(s) *params*.\ :math:`^\ddagger` :math:`^\dagger`


.. method:: path.atbegin()

   Returns the coordinates (as 2-tuple) of the first point of the path.\
   :math:`^\dagger`


.. method:: path.atend()

   Returns the coordinates (as 2-tuple) of the end point of the path.\
   :math:`^\dagger`


.. method:: path.bbox()

   Returns the bounding box of the path. Note that this returned bounding box may
   be too large, if the path contains any :class:`curveto` elements, since for
   these the control box, i.e., the bounding box enclosing the control points of
   the Bézier curve is returned.


.. method:: path.begin()

   Returns the parameter value (a :class:`normpathparam` instance) of the first
   point in the path.


.. method:: path.curveradius(param=None, arclen=None)

   Returns the curvature radius/radii (or None if infinite) at parameter value(s)
   params.\ :math:`^\ddagger` This is the inverse of the curvature at this
   parameter. Note that this radius can be negative or positive, depending on the
   sign of the curvature.\ :math:`^\dagger`


.. method:: path.end()

   Returns the parameter value (a :class:`normpathparam` instance) of the last
   point in the path.


.. method:: path.extend(pathitems)

   Appends the list *pathitems* to the end of the path.


.. method:: path.intersect(opath)

   Returns a tuple consisting of two lists of parameter values corresponding to the
   intersection points of the path with the other path *opath*, respectively.\
   :math:`^\dagger` For intersection points which are not farther apart then
   *epsilon* points, only one is returned.


.. method:: path.joined(opath)

   Appends *opath* to the end of the path, thereby merging the last subpath (which
   must not be closed) of the path with the first sub path of *opath* and returns
   the resulting new path.\ :math:`^\dagger`


.. method:: path.normpath(epsilon=None)

   Returns the equivalent :class:`normpath`. For the conversion and for later
   calculations with this :class:`normpath` and accuracy of *epsilon* points is
   used. If *epsilon* is *None*, the global *epsilon* of the :mod:`path` module is
   used.


.. method:: path.paramtoarclen(params)

   Returns the arc length(s) corresponding to the parameter value(s) *params*.\
   :math:`^\ddagger` :math:`^\dagger`


.. method:: path.range()

   Returns the maximal parameter value *param* that is allowed in the path methods.


.. method:: path.reversed()

   Returns the reversed path.\ :math:`^\dagger`


.. method:: path.rotation(params)

   Returns (a) rotations(s) which (each), which rotate the x-direction to the
   tangent and the y-direction to the normal at that param.\ :math:`^\dagger`


.. method:: path.split(params)

   Splits the path at the parameter values *params*, which have to be sorted in
   ascending order, and returns a corresponding list of :class:`normpath`
   instances.\ :math:`^\dagger`


.. method:: path.tangent(params, length=1)

   Return (a) :class:`line` instance(s) corresponding to the tangent vector(s) to
   the path at the parameter value(s) *params*.\ :math:`^\ddagger` The tangent
   vector will be scaled to the length *length*.\ :math:`^\dagger`


.. method:: path.trafo(params)

   Returns (a) trafo(s) which (each) translate to a point on the path corresponding
   to the param, rotate the x-direction to the tangent and the y-direction to the
   normal in that point.\ :math:`^\dagger`


.. method:: path.transformed(trafo)

   Returns the path transformed according to the linear transformation *trafo*.
   Here, ``trafo`` must be an instance of the :class:`trafo.trafo` class.\
   :math:`^\dagger`

Some notes on the above:

* The :math:`\dagger` denotes methods which require a prior conversion of the
  path into a :class:`normpath` instance. This is done automatically (using the
  precision *epsilon* set globally using :meth:`path.set`). If you need a
  different *epsilon* for a normpath, you also can perform the conversion
  manually.

* Instead of using the :meth:`joined` method, you can also join two paths
  together with help of the ``<<`` operator, for instance ``p = p1 << p2``.

* :math:`^\ddagger` In these methods, *params* may either be a single value or a
  list. In the latter case, the result of the method will be a list consisting of
  the results for every parameter.  The parameter itself may either be a length
  (or a number which is then interpreted as a user length) or an instance of the
  class :class:`normpathparam`. In the former case, the length refers to the arc
  length along the path.


.. _path_pathitem:

Path elements
-------------

The class :class:`pathitem` is the superclass of all PostScript path
construction primitives. It is never used directly, but only by instantiating
its subclasses, which correspond one by one to the PostScript primitives.

Except for the path elements ending in ``_pt``, all coordinates passed to the
path elements can be given as number (in which case they are interpreted as user
units with the currently set default type) or in PyX lengths.

The following operation move the current point and open a new subpath:


.. class:: moveto(x, y)

   Path element which sets the current point to the absolute coordinates (*x*,
   *y*). This operation opens a new subpath.


.. class:: rmoveto(dx, dy)

   Path element which moves the current point by (*dx*, *dy*).  This operation
   opens a new subpath.

Drawing a straight line can be accomplished using:


.. class:: lineto(x, y)

   Path element which appends a straight line from the current point to the point
   with absolute coordinates (*x*, *y*), which becomes the new current point.


.. class:: rlineto(dx, dy)

   Path element which appends a straight line from the current point to the a point
   with relative coordinates (*dx*, *dy*), which becomes the new current point.

For the construction of arc segments, the following three operations are
available:


.. class:: arc(x, y, r, angle1, angle2)

   Path element which appends an arc segment in counterclockwise direction with
   absolute coordinates (*x*, *y*) of the center and  radius *r* from *angle1* to
   *angle2* (in degrees).  If before the operation, the current point is defined, a
   straight line is from the current point to the beginning of the arc segment is
   prepended. Otherwise, a subpath, which thus is the first one in the path, is
   opened. After the operation, the current point is at the end of the arc segment.


.. class:: arcn(x, y, r, angle1, angle2)

   Path element which appends an arc segment in clockwise direction with absolute
   coordinates (*x*, *y*) of the center and  radius *r* from *angle1* to *angle2*
   (in degrees).  If before the operation, the current point is defined, a straight
   line is from the current point to the beginning of the arc segment is prepended.
   Otherwise, a subpath, which thus is the first one in the path, is opened. After
   the operation, the current point is at the end of the arc segment.


.. class:: arct(x1, y1, x2, y2, r)

   Path element which appends an arc segment of radius *r* connecting between
   (*x1*, *y1*) and (*x2*, *y2*). ---

Bézier curves can be constructed using: \


.. class:: curveto(x1, y1, x2, y2, x3, y3)

   Path element which appends a Bézier curve with the current point as first
   control point and the other control points (*x1*, *y1*), (*x2*, *y2*), and
   (*x3*, *y3*).


.. class:: rcurveto(dx1, dy1, dx2, dy2, dx3, dy3)

   Path element which appends a Bézier curve with the current point as first
   control point and the other control points defined relative to the current point
   by the coordinates (*dx1*, *dy1*), (*dx2*, *dy2*), and (*dx3*, *dy3*).

Note that when calculating the bounding box (see Sect. :mod:`bbox`) of Bézier
curves, PyX uses for performance reasons the so-called control box, i.e., the
smallest rectangle enclosing the four control points of the Bézier curve. In
general, this is not the smallest rectangle enclosing the Bézier curve.

Finally, an open subpath can be closed using:


.. class:: closepath()

   Path element which closes the current subpath.

For performance reasons, two non-PostScript path elements are defined,  which
perform multiple identical operations:


.. class:: multilineto_pt(points_pt)

   Path element which appends straight line segments starting from the current
   point and going through the list of points given  in the *points_pt* argument.
   All coordinates have to  be given in PostScript points.


.. class:: multicurveto_pt(points_pt)

   Path element which appends Bézier curve segments starting from the current point
   and going through the list of each three control points given in the *points_pt*
   argument. Thus, *points_pt* must be a sequence of 6-tuples.


.. _path_normpath:

Class :class:`normpath`
-----------------------

The :class:`normpath` class is used internally for all non-trivial path
operations, i.e. the ones marked by a :math:`\dagger` in the description of the
:class:`path` above. It represents a path as a list of subpaths, which are
instances of the class :class:`normsubpath`. These :class:`normsubpath`\ s
themselves consist of a list of :class:`normsubpathitems` which are either
straight lines (:class:`normline`) or Bézier curves (:class:`normcurve`).

A given path can easily be converted to the corresponding :class:`normpath`
using the method with this name::

   np = p.normpath()

Additionally, you can specify the accuracy (in points) which is used in all
:class:`normpath` calculations by means of the argument *epsilon*, which
defaults to to :math:`10^{-5}` points. This default value can be changed using
the module function :func:`path.set`.

To construct a :class:`normpath` from a list of :class:`normsubpath` instances,
you pass them to the :class:`normpath` constructor:


.. class:: normpath(normsubpaths=[])

   Construct a :class:`normpath` consisting of *subnormpaths*, which is a list of
   :class:`subnormpath` instances.

Instances of :class:`normpath` offers all methods of regular :class:`path`\ s,
which also have the same semantics. An exception are the methods :meth:`append`
and :meth:`extend`. While they allow for adding of instances of
:class:`subnormpath` to the :class:`normpath` instance, they also keep the
functionality of a regular path and allow for regular path elements to be
appended. The later are converted to the proper normpath representation during
addition.

In addition to the :class:`path` methods, a :class:`normpath` instance also
offers the following methods, which operate on the instance itself, i.e., modify
it in place.


.. method:: normpath.join(other)

   Join *other*, which has to be a :class:`path` instance, to the :class:`normpath`
   instance.


.. method:: normpath.reverse()

   Reverses the :class:`normpath` instance.


.. method:: normpath.transform(trafo)

   Transforms the :class:`normpath` instance according to the linear transformation
   *trafo*.

Finally, we remark that the sum of a :class:`normpath` and a :class:`path`
always yields a :class:`normpath`.


Class :class:`normsubpath`
--------------------------


.. class:: normsubpath(normsubpathitems=[], closed=0, epsilon=1e-5)

   Construct a :class:`normsubpath` consisting of *normsubpathitems*, which is a
   list of :class:`normsubpathitem` instances. If *closed* is set, the
   :class:`normsubpath` will be closed, thereby appending a straight line segment
   from the first to the last point, if it is not already present. All calculations
   with the :class:`normsubpath` are performed with an accuracy of *epsilon*.

Most :class:`normsubpath` methods behave like the ones of a :class:`path`.

Exceptions are:


.. method:: normsubpath.append(anormsubpathitem)

   Append the *anormsubpathitem* to the end of the :class:`normsubpath` instance.
   This is only possible if the :class:`normsubpath` is not closed, otherwise an
   exception is raised.


.. method:: normsubpath.extend(normsubpathitems)

   Extend the :class:`normsubpath` instances by *normsubpathitems*, which has to be
   a list of :class:`normsubpathitem` instances. This is only possible if the
   :class:`normsubpath` is not closed, otherwise an exception is raised.


.. method:: normsubpath.close()

   Close the :class:`normsubpath` instance, thereby appending a straight line
   segment from the first to the last point, if it is not already present.


.. _path_predefined:

Predefined paths
----------------


For convenience, some oft-used paths are already predefined. All of them are
subclasses of the :class:`path` class.


.. class:: line(x0, y0, x1, y1)

   A straight line from the point (*x0*, *y0*) to the point (*x1*, *y1*).


.. class:: curve(x0, y0, x1, y1, x2, y2, x3, y3)

   A Bézier curve with  control points  (*x0*, *y0*), :math:`\dots`, (*x3*, *y3*).\


.. class:: rect(x, y, w, h)

   A closed rectangle with lower left point (*x*, *y*), width *w*, and height *h*.


.. class:: circle(x, y, r)

   A closed circle with center (*x*, *y*) and radius *r*.

