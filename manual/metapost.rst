.. module:: metapost.path

===========================
Module :mod:`metapost.path`
===========================

.. sectionauthor:: Michael Schindler <m-schindler@users.sourceforge.net>

The :mod:`metapost` subpackage provides some of the path functionality of the
MetaPost program. The :mod:`metapost.path` presents the path construction
facility of MetaPost.

Similarly to the :mod:`normpath`, there is a short length *epsilon* (always in
Postscript points pt) used as accuracy of numerical operations, such as
calculating angles from short path elements, or for omitting such short path
elements, etc. The default value is :math:`10^{-5}` and can be changed using
the module function :func:`metapost.set`.


Class :class:`path` --- MetaPost-like paths
-------------------------------------------

.. class:: path(pathitems, epsilon=None)

   This class represents a MetaPost-like path which is created from the given
   list of knots and curves/lines. It can find an optimal way through given
   points.

   At points (knots), you can either specify a given tangent direction (angle
   in degrees) or a certain *curlyness* (relative to the curvature at the other
   end of a curve), or nothing. In the latter case, both the tangent and the
   *mock* curvature (an approximation to the real curvature, introduced by J. D.
   Hobby in MetaPost) will be continuous.

   The shape of the cubic Bezier curves between two points is controlled by
   its *tension*, unless you choose to set the control points manually.

   All possible path items are described below. They are either :ref:`knots` or
   :ref:`links`. Note that there is no explicit `closepath` class. Whether the
   path is open or closed depends on the type of knots used, begin endpoints or
   not. Note also that the number of knots and links must be equal for closed
   paths, and that you cannot create a path comprising closed subpaths.

   The *epsilon* argument governs the accuracy of the calculations implied in
   creating the path (see above). The value *None* means fallback to the
   default epsilon of the module.

Instances of the class :class:`path` inherit all properties of the Postscript
paths in :mod:`path`.


.. _knots:

Knots
-----

.. class:: beginknot(x, y, curl=1, angle=None)

   The first knot, starting an open path at the coordinates (*x*, *y*). The
   properties of the curve in that point can either be given by its curlyness
   (default) or the angle of its tangent vector (in degrees). The *curl*
   parameter is (as in MetaPost) the ratio of the curvatures at this point and
   at the other point of the curve connecting it.

.. class:: startknot(x, y, curl=1, angle=None)

   Synonym for :class:`beginknot`.

.. class:: endknot(x, y, curl=1, angle=None)

   The last knot of an open path. Curlyness and angle are the same as in
   :class:`beginknot`.

.. class:: smoothknot(x, y)

   This knot is the standard knot of MetaPost. It guarantees continuous tangent
   vectors and *mock curvatures* of the two curves it connects.

   Note: If one of the links is a line, the knot is changed to a
   :class:`roughknot` with either a specified angle (if the *keepangles*
   parameter is set in the line) or with *curl=1*.

.. class:: roughknot(x, y, left_curl=1, right_curl=None, left_angle=None, right_angle=None)

   This knot is a possibly non-smooth knot, connecting two curves or lines. At
   each side of the knot (left/right) you can specify either the curlyness or
   the tangent angle.

   Note: If one of the links is a line with the *keepangles* parameter set, the
   angles will be set eplicitly, regardless of any curlyness set.

.. class:: knot(x, y)

   Synonym for :class:`smoothknot`.


.. _links:

Links
-----

.. class:: line(keepangles=False)

   A straight line which corresponds to the MetaPost command "--". The option
   *keepangles* will guarantee a continuous tangent. (The curvature may become
   discontinuous, however.) This behavior is achieved by turning adjacent knots
   into roughknots with specified angles. Note that a smoothknot and a
   roughknot with given curlyness do behave differently near a line.

.. class:: tensioncurve(ltension=1, latleast=False, rtension=None, ratleast=None)

   The standard type of curve in MetaPost. It corresponds to the MetaPost
   command ".." or to "..." if the *atleast* parameters are set to True. The
   tension parameters indicate the tensions at the beginning (l) and the end
   (r) of the curve. Set the parameters (l/r)atleast to True if you want to
   avoid inflection points.

.. class:: controlcurve(lcontrol, rcontrol)

   A cubic Bezier curve which has its control points explicity set, similar to
   the :class:`path.curveto` class of the Postscript paths. The control points
   at the beginning (l) and the end (r) must be coordinate pairs (x, y).

.. class:: curve(ltension=1, latleast=False, rtension=None, ratleast=None)

   Synonym for :class:`tensioncurve`.


