.. module:: pattern
   :synopsis: Tiling patterns and predefined hatching fills

.. _pattern:

*********************
Module :mod:`pattern`
*********************

.. sectionauthor:: Jörg Lehmann <joerg@pyx-project.org>

The :mod:`pattern` module provides tiling patterns (:class:`pattern`) that can be
used as fill styles (and, in PostScript and SVG, stroke styles), along with
predefined parallel-line (:class:`hatched`) and grid (:class:`crosshatched`)
hatching patterns.


Class :class:`pattern`
======================

A :class:`pattern` is a specialized :class:`canvas.canvas` that also acts as a
:class:`style.fillstyle`. To define a custom tiling pattern, instantiate
:class:`pattern`, draw into it using standard canvas methods (:meth:`~canvas.canvas.stroke`,
:meth:`~canvas.canvas.fill`, :meth:`~canvas.canvas.text`, etc.), and then pass the
pattern instance as an attribute when filling a path:

.. code-block:: python

   from pyx import *

   p = pattern.pattern()
   p.fill(path.circle(0, 0, 0.1), [color.rgb.red])

   c = canvas.canvas()
   c.draw(path.rect(0, 0, 4, 2), [deco.filled([p]), deco.stroked()])
   c.writePDFfile("polkadots")

.. class:: pattern(painttype=1, tilingtype=1, xstep=None, ystep=None, bbox=None, trafo=None, bboxenlarge=None, **kwargs)

   Creates a new tiling pattern canvas. The constructor accepts the following
   arguments:

   * *painttype*: ``1`` (default) for a colored pattern whose colors are
     specified when drawing into the pattern canvas, or ``2`` for an uncolored
     pattern (supported in PostScript and PDF) whose color is determined at the
     time the pattern is used.
   * *tilingtype*: Controls how PostScript and PDF renderers adjust pattern
     spacing relative to device pixels:

     - ``1`` (default): Constant spacing between pattern cells (spaced by a
       multiple of a device pixel).
     - ``2``: Undistorted pattern cell (spacing between cells may vary by up to
       one device pixel).
     - ``3``: Constant spacing with faster tiling (allows slight cell distortion
       for faster rendering).

   * *xstep*: Horizontal repetition step between pattern cells (a PyX length or
     number in user units), or ``None`` (default) to use the width of the
     pattern's bounding box.
   * *ystep*: Vertical repetition step between pattern cells, or ``None``
     (default) to use the height of the pattern's bounding box.
   * *bbox*: Explicit :class:`bbox.bbox` for the pattern cell, or ``None``
     (default) to compute the bounding box automatically from the drawn items.
   * *trafo*: Optional :class:`trafo.trafo` applied to the pattern cell (for
     example, to rotate the tiling grid or shift its phase).
   * *bboxenlarge*: Optional length by which an automatically computed bounding
     box is enlarged on all sides (default ``None``).


Predefined Hatching Patterns
============================

For common technical drawings and bar charts, :mod:`pattern` provides ready-to-use
single-direction (:class:`hatched`) and orthogonal two-direction
(:class:`crosshatched`) line patterns:

.. class:: hatched(dist, angle, strokestyles=[])

   Creates a parallel-line hatching pattern with line spacing *dist* (a PyX
   length), rotation *angle* in degrees, and optional stroke attributes
   *strokestyles* (merged with ``[style.linewidth.THIN]``). Calling an existing
   :class:`hatched` instance ``h(dist=..., angle=..., strokestyles=...)`` returns
   a modified copy.

   Predefined instances are provided for four standard angles (``0``, ``45``,
   ``90``, and ``135`` degrees), each with 13 spacing scales ranging from
   ``SMALL`` to ``LARGE`` (scaled by powers of :math:`\sqrt{2}` around a base
   spacing of ``0.1 * unit.v_cm``):

   * :data:`hatched0` (vertical lines, ``angle=0``):
     ``hatched0.SMALL``, ``hatched0.SMALl``, ``hatched0.SMAll``,
     ``hatched0.SMall``, ``hatched0.Small``, ``hatched0.small``,
     ``hatched0.normal``, ``hatched0.large``, ``hatched0.Large``,
     ``hatched0.LArge``, ``hatched0.LARge``, ``hatched0.LARGe``,
     ``hatched0.LARGE``
   * :data:`hatched45` (diagonal lines at 45°): ``hatched45.SMALL`` … ``hatched45.LARGE``
   * :data:`hatched90` (horizontal lines, ``angle=90``): ``hatched90.SMALL`` … ``hatched90.LARGE``
   * :data:`hatched135` (diagonal lines at 135°): ``hatched135.SMALL`` … ``hatched135.LARGE``

.. class:: crosshatched(dist, angle, strokestyles=[])

   Creates a two-directional orthogonal cross-hatching pattern with grid spacing
   *dist*, rotation *angle* in degrees, and optional *strokestyles* (merged with
   ``[style.linewidth.THIN]``).

   Predefined instances with the same ``SMALL`` … ``normal`` … ``LARGE`` size
   attributes are available for two orientations:

   * :data:`crosshatched0` (horizontal and vertical grid, ``angle=0``)
   * :data:`crosshatched45` (diagonal grid at 45° and 135°, ``angle=45``)
