.. module:: trafo
   :synopsis: Affine transformations (translation, rotation, scaling, mirroring, and slanting)

.. _trafo:

*******************************************
Module :mod:`trafo`: Linear transformations
*******************************************

The :mod:`trafo` module provides affine (linear plus translation) coordinate
transformations. Because :class:`trafo` inherits from :class:`baseclasses.deformer`,
transformation instances can be used seamlessly in several ways across PyX:

* Passed in the attribute list of :meth:`canvas.canvas.stroke`,
  :meth:`canvas.canvas.fill`, :meth:`canvas.canvas.draw`,
  :meth:`canvas.canvas.insert`, or :meth:`canvas.canvas.text` to transform
  individual graphical objects.
* Passed to ``canvas.canvas([trafo.scale(2)])`` or ``c.set([trafo.rotate(45)])``
  to transform the coordinate system of an entire canvas.
* Applied directly to a path via ``p.transformed(t)`` or ``t.deform(p)``, or to a
  bounding box via ``b.transformed(t)``.


Mathematical Definition and Composition
=======================================

An affine transformation maps a 2D point vector :math:`\vec{x} = (x, y)^T` to

.. math::

   \vec{x}' = \mathsf{A}\, \vec{x} + \vec{b}\ ,

where :math:`\mathsf{A}` is a non-singular :math:`2\times 2` matrix
(:math:`\det \mathsf{A} \ne 0`) and :math:`\vec{b}` is a 2D translation vector.

Transformations can be composed in two ways:

1. **Multiplication** (``t1 * t2``):
   Multiplying two transformations corresponds to matrix composition—``t1 * t2``
   applies ``t2`` *first*, followed by ``t1``:

   .. math::

      \mathsf{A} = \mathsf{A}_1 \mathsf{A}_2, \qquad
      \vec{b} = \mathsf{A}_1 \vec{b}_2 + \vec{b}_1\ .

2. **Chained methods** (``t.translated(...)``, ``t.rotated(...)``, etc.):
   Every :class:`trafo` instance provides methods that return a new
   transformation obtained by applying the new operation *after* ``t``. Thus
   ``t.rotated(45)`` is equivalent to ``trafo.rotate(45) * t``:

   .. code-block:: python

      # Translate by (2, 1) first, then rotate by 30 degrees around the origin:
      t = trafo.translate(2, 1).rotated(30)
      # Equivalent to:
      t = trafo.rotate(30) * trafo.translate(2, 1)


Class :class:`trafo`
====================

.. class:: trafo(matrix=((1, 0), (0, 1)), vector=(0, 0))

   Constructs an affine transformation with :math:`2\times 2` transformation
   *matrix* ``((a11, a12), (a21, a22))`` and translation *vector* ``(bx, by)``
   (where ``bx`` and ``by`` are PyX lengths or numbers in user units).

   For internal point-based coordinates, :class:`trafo_pt` takes ``vector``
   directly in PostScript points. The module-level constant
   :data:`trafo.identity` provides a preconstructed identity transformation.

   .. method:: apply(x, y)

      Applies the transformation to the point ``(x, y)`` (in user units or PyX
      lengths) and returns the transformed point as a tuple of two true lengths
      ``(tx, ty)``.

   .. method:: apply_pt(x_pt, y_pt)

      Applies the transformation to the point ``(x_pt, y_pt)`` in PostScript
      points and returns ``(tx_pt, ty_pt)`` in points.

   .. method:: deform(path)

      Returns a transformed copy of *path* (equivalent to
      ``path.transformed(self)``).

   .. method:: inverse()

      Returns the inverse transformation :math:`\mathsf{A}^{-1}` with translation
      vector :math:`-\mathsf{A}^{-1}\vec{b}`.

   .. method:: mirrored(angle)

      Returns ``self`` followed by a reflection across the line through the
      origin at *angle* degrees counter-clockwise from the positive *x*-axis.

   .. method:: rotated(angle, x=None, y=None)

      Returns ``self`` followed by a counter-clockwise rotation by *angle*
      degrees around the center ``(x, y)`` (or ``(0, 0)`` if omitted). Also
      available in point coordinates as :meth:`rotated_pt`.

   .. method:: scaled(sx, sy=None, x=None, y=None)

      Returns ``self`` followed by scaling by *sx* in the *x*-direction and *sy*
      in the *y*-direction (if *sy* is ``None``, uniform scaling ``sy = sx`` is
      used) relative to the center ``(x, y)`` (or ``(0, 0)`` if omitted). Also
      available in point coordinates as :meth:`scaled_pt`.

   .. method:: slanted(a, angle=0, x=None, y=None)

      Returns ``self`` followed by a shear (slant) of factor *a* along the
      direction *angle* (in degrees) relative to ``(x, y)`` (or ``(0, 0)`` if
      omitted). Also available in point coordinates as :meth:`slanted_pt`.

   .. method:: translated(x, y)

      Returns ``self`` followed by a translation by ``(x, y)``. Also available in
      point coordinates as :meth:`translated_pt`.


Standard Transformation Subclasses
==================================

For each transformation operation, :mod:`trafo` provides a dedicated subclass of
:class:`trafo` (along with a corresponding ``_pt`` class taking coordinates in
PostScript points):

.. class:: mirror(angle=0)

   Reflection across the line through the origin ``(0, 0)`` at *angle* degrees
   from the positive *x*-axis.

.. class:: rotate(angle, x=None, y=None)
.. class:: rotate_pt(angle, x=None, y=None)

   Counter-clockwise rotation by *angle* degrees around the point ``(x, y)``, or
   around ``(0, 0)`` if *x* and *y* are omitted.

.. class:: scale(sx, sy=None, x=None, y=None)
.. class:: scale_pt(sx, sy=None, x=None, y=None)

   Scaling by factor *sx* along the *x*-axis and *sy* along the *y*-axis
   (defaults to ``sy = sx`` for uniform scaling) centered at ``(x, y)``, or at
   ``(0, 0)`` if *x* and *y* are omitted.

.. class:: slant(a, angle=0, x=None, y=None)
.. class:: slant_pt(a, angle=0, x=None, y=None)

   Shear transformation by factor *a* along the direction *angle* (in degrees)
   centered at ``(x, y)``, or at ``(0, 0)`` if *x* and *y* are omitted. For
   ``angle=0``, this maps :math:`(x, y) \mapsto (x + a y, y)`.

.. class:: translate(x, y)
.. class:: translate_pt(x, y)

   Translation by the vector ``(x, y)``.
