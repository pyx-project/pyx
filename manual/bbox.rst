.. _bbox_module:
.. _bbox:

.. module:: bbox
   :synopsis: Axis-aligned bounding boxes

******************
Module :mod:`bbox`
******************

The :mod:`bbox` module defines axis-aligned bounding boxes (:class:`bbox`,
:class:`bbox_pt`, and :class:`empty`) used throughout PyX to compute the spatial
extent of paths, text boxes, canvases, and pages. While you most commonly obtain
a bounding box by calling an object's ``bbox()`` method (such as
:meth:`canvas.canvas.bbox` or :meth:`path.path.bbox`), you can also construct and
manipulate bounding boxes directly—for example, to pass a custom clipping or page
bounding box to :meth:`canvas.canvas.writeEPSfile` or :class:`document.page`.


Constructing Bounding Boxes
===========================

.. class:: bbox(llx, lly, urx, ury)

   Constructs a bounding box with lower-left corner ``(llx, lly)`` and
   upper-right corner ``(urx, ury)`` specified in user units or PyX lengths.

.. class:: bbox_pt(llx_pt, lly_pt, urx_pt, ury_pt)

   Constructs a bounding box with coordinates ``(llx_pt, lly_pt)`` and
   ``(urx_pt, ury_pt)`` specified directly in PostScript points. All ``bbox()``
   methods on PyX objects return :class:`bbox_pt` instances.

.. class:: empty()

   Constructs an empty bounding box (containing no points, with ``llx_pt=None``).
   An empty bounding box evaluates to ``False`` in a boolean context
   (``bool(bbox.empty()) == False``), whereas any non-empty bounding box
   evaluates to ``True``.


Set Operations and Methods
==========================

Two bounding boxes ``b1`` and ``b2`` can be combined using arithmetic operators:

* **Union** (``b1 + b2`` or ``b1 += b2``): Returns the smallest bounding box
  enclosing both ``b1`` and ``b2``. Adding an :class:`empty` bounding box leaves
  the other bounding box unchanged.
* **Intersection** (``b1 * b2`` or ``b1 *= b2``): Returns the overlapping region
  of ``b1`` and ``b2`` (or an :class:`empty` bounding box if either input is
  empty).

In addition, :class:`bbox` and :class:`bbox_pt` provide the following methods
(where measurement methods without a ``_pt`` suffix return true PyX lengths
:data:`unit.t_pt`, and ``_pt`` variants take or return plain floats in PostScript
points):

+---------------------------------------------------------+---------------------------------------------------------------+
| Method                                                  | Description                                                   |
+=========================================================+===============================================================+
| ``copy()``                                              | Returns a copy of the bounding box.                           |
+---------------------------------------------------------+---------------------------------------------------------------+
| ``set(other)``                                          | Copies the coordinates of *other* into ``self``.              |
+---------------------------------------------------------+---------------------------------------------------------------+
| ``intersects(other)``                                   | Returns ``True`` if ``self`` and *other* overlap (and neither |
|                                                         | is empty), or ``False``/``0`` otherwise.                      |
+---------------------------------------------------------+---------------------------------------------------------------+
| ``includepoint_pt(x_pt, y_pt)``                         | Expands ``self`` in place to include the point                |
|                                                         | ``(x_pt, y_pt)``.                                             |
+---------------------------------------------------------+---------------------------------------------------------------+
| ``transform(trafo)``                                    | Transforms the four corners of ``self`` in place by *trafo*   |
|                                                         | and updates ``self`` to their enclosing axis-aligned box.     |
+---------------------------------------------------------+---------------------------------------------------------------+
| ``transformed(trafo)``                                  | Returns a new bounding box enclosing ``self`` after           |
|                                                         | transformation by *trafo*.                                    |
+---------------------------------------------------------+---------------------------------------------------------------+
| ``enlarge(all=0, bottom=None, left=None,``              | Expands ``self`` in place on each side by the specified PyX   |
| ``top=None, right=None)``                               | lengths (using *all* for any side left as ``None``). Also     |
|                                                         | available as ``enlarge_pt(...)``.                             |
+---------------------------------------------------------+---------------------------------------------------------------+
| ``enlarged(all=0, bottom=None, left=None,``             | Returns a new bounding box expanded on each side by the       |
| ``top=None, right=None)``                               | specified amounts (using *all* for any side left as           |
|                                                         | ``None``). Also available as ``enlarged_pt(...)``.            |
+---------------------------------------------------------+---------------------------------------------------------------+
| ``path()`` / ``rect()``                                 | Returns a rectangular :class:`path.rect_pt` path tracing the  |
|                                                         | boundary of the bounding box.                                 |
+---------------------------------------------------------+---------------------------------------------------------------+
| ``width()`` / ``width_pt()``                            | Returns the horizontal width of the bounding box.             |
+---------------------------------------------------------+---------------------------------------------------------------+
| ``height()`` / ``height_pt()``                          | Returns the vertical height of the bounding box.              |
+---------------------------------------------------------+---------------------------------------------------------------+
| ``left()`` / ``left_pt()``                              | Returns the *x*-coordinate of the left edge (``llx``).        |
+---------------------------------------------------------+---------------------------------------------------------------+
| ``right()`` / ``right_pt()``                            | Returns the *x*-coordinate of the right edge (``urx``).       |
+---------------------------------------------------------+---------------------------------------------------------------+
| ``bottom()`` / ``bottom_pt()``                          | Returns the *y*-coordinate of the bottom edge (``lly``).      |
+---------------------------------------------------------+---------------------------------------------------------------+
| ``top()`` / ``top_pt()``                                | Returns the *y*-coordinate of the top edge (``ury``).         |
+---------------------------------------------------------+---------------------------------------------------------------+
| ``center()`` / ``center_pt()``                          | Returns the ``(x, y)`` coordinates of the center of the       |
|                                                         | bounding box.                                                 |
+---------------------------------------------------------+---------------------------------------------------------------+
| ``lowrestuple_pt()``                                    | Returns ``(floor(llx_pt), floor(lly_pt), ceil(urx_pt),``      |
|                                                         | ``ceil(ury_pt))`` as integer points (used for PostScript      |
|                                                         | ``%%BoundingBox``).                                           |
+---------------------------------------------------------+---------------------------------------------------------------+
| ``highrestuple_pt()``                                   | Returns ``(llx_pt, lly_pt, urx_pt, ury_pt)`` in exact         |
|                                                         | floating-point points (used for ``%%HiResBoundingBox``).      |
+---------------------------------------------------------+---------------------------------------------------------------+
