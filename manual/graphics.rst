.. _graphics:

**************
Basic graphics
**************

The chapters in this part describe the core building blocks for creating
graphics in PyX and writing the result to PostScript, EPS, PDF, and SVG files.
Before diving into the reference chapters for individual modules, this chapter
provides a tour of PyX's drawing architecture, its attribute system
(:mod:`attr`), path styles (:mod:`style`), and path decorators (:mod:`deco`).


Overview of the drawing model
=============================

Drawing in PyX revolves around two fundamental objects:

- **Paths** (:class:`path.path` and :class:`normpath.normpath`) define purely
  mathematical geometry—lines, Bézier curves, arcs, circles, rectangles, and
  splines—without any intrinsic visual appearance such as line thickness or
  color.
- **Canvases** (:class:`canvas.canvas`) act as containers and drawing surfaces
  that combine paths, text boxes, bitmaps, external vector graphics, and nested
  sub-canvases with visual attributes.


Paths
-----

Consider the introductory example::

   from pyx import *

   c = canvas.canvas()
   c.stroke(path.line(0, 0, 3, 2))
   c.writeEPSfile("line")
   c.writePDFfile("line")
   c.writeSVGfile("line")

The :mod:`path` module provides classes for constructing PostScript-like paths.
Simple geometric shapes are available directly as predefined path classes:

- :class:`path.line`: A straight line segment between two points :math:`(x_1, y_1)`
  and :math:`(x_2, y_2)`.
- :class:`path.curve`: A cubic Bézier curve defined by a start point, two control
  points, and an end point.
- :class:`path.rect`: A closed rectangle defined by its lower-left corner
  :math:`(x, y)`, width, and height.
- :class:`path.circle`: A closed circle defined by its center :math:`(x, y)` and
  radius :math:`r`.
- :class:`path.ellipse`: A closed ellipse defined by its center :math:`(x, y)`,
  semi-axes :math:`(a, b)`, and rotation angle.

Arbitrary compound paths can be built from elementary path items (:class:`path.moveto`,
:class:`path.lineto`, :class:`path.curveto`, :class:`path.arc`,
:class:`path.closepath`, and their relative counterparts), or from smooth
Hobby–Knuth splines via :mod:`metapost.path`::

   p = path.path(path.moveto(0, 0), path.lineto(2, 0), path.lineto(1, 2), path.closepath())

Every path can also be converted into a *normalized path*
(:class:`normpath.normpath`), which represents all segments strictly in terms of
straight lines and cubic Bézier curves and supports geometric operations such as
finding intersections, splitting at parameters or arc lengths, computing tangent
frames and curvatures, and joining subpaths. See :ref:`path` and :ref:`metapost`
for details.


Drawing on the canvas
---------------------

Once a path has been constructed, it is rendered onto a :class:`canvas.canvas`
using one of three drawing methods:

- :meth:`canvas.canvas.stroke`: Strokes the outline of the path.
- :meth:`canvas.canvas.fill`: Fills the interior of the path.
- :meth:`canvas.canvas.draw`: Performs arbitrary combinations of stroking,
  filling, and decorating as specified by a list of attributes.

In fact, ``c.stroke(p, attrs)`` and ``c.fill(p, attrs)`` are simply convenient
shortcuts for ``c.draw(p, [deco.stroked] + list(attrs))`` and
``c.draw(p, [deco.filled] + list(attrs))``. Thus, to fill a rectangle with red
and simultaneously stroke its border in blue with a thick line, you can write::

   c.draw(path.rect(0, 0, 3, 2),
          [deco.filled([color.rgb.red]),
           deco.stroked([color.rgb.blue, style.linewidth.Thick])])

Canvases also support hierarchical composition: a canvas can be inserted into
another canvas via :meth:`canvas.canvas.insert`, optionally with transformations
(such as translations, rotations, or scalings) applied to the inserted group,
and organized into z-ordered drawing layers via :meth:`canvas.canvas.layer`.
When a canvas represents a finished figure, you can write it directly to a file
using :meth:`canvas.canvas.writeEPSfile`, :meth:`canvas.canvas.writePDFfile`,
:meth:`canvas.canvas.writeSVGfile`, or :meth:`canvas.canvas.writetofile`, or
combine multiple canvases as pages of a :class:`document.document`.


Attributes, styles, decorators, and deformers
---------------------------------------------

The visual appearance and geometric modification of paths and canvases are
controlled uniformly by passing lists of *attributes*. PyX distinguishes four
kinds of attributes that can be passed to :meth:`canvas.canvas.draw`,
:meth:`canvas.canvas.stroke`, and :meth:`canvas.canvas.fill`:

1. **Styles** (:mod:`style`, :mod:`color`, :mod:`pattern`): Control PostScript /
   PDF / SVG graphics state properties. They are subdivided into
   :class:`style.strokestyle` (such as :class:`style.linewidth`,
   :class:`style.linestyle`, :class:`style.linecap`, :class:`style.linejoin`,
   :class:`style.miterlimit`) and :class:`style.fillstyle` (such as
   :class:`style.fillrule` and :class:`pattern.pattern`). Colors
   (:class:`color.color`), transparency (:class:`color.transparency`), and
   patterns inherit from both :class:`style.strokestyle` and
   :class:`style.fillstyle`, so they can be used both for stroking and filling.
2. **Decorators** (:mod:`deco`): Determine *how* a path is rendered or add
   graphical elements to it. The fundamental decorators are :class:`deco.stroked`
   and :class:`deco.filled`, which accept their own local style lists (e.g.,
   ``deco.filled([color.rgb.red])``). Additional decorators attach arrowheads
   (:class:`deco.earrow`, :class:`deco.barrow`), labels (:class:`deco.text`,
   :class:`deco.curvedtext`), arbitrary canvas items (:class:`deco.insert`), or
   color gradients (:class:`deco.colorgradient`) along the path.
3. **Deformers** (:mod:`deformer`): Geometrically transform a path into a new
   normalized path *before* decorators and styles are applied—for example,
   rounding corners (:class:`deformer.smoothed`), offsetting a parallel curve
   (:class:`deformer.parallel`), or winding a spring-like coil along the path
   (:class:`deformer.cycloid`).
4. **Transformations** (:mod:`trafo`): Apply affine coordinate transformations
   (:class:`trafo.translate`, :class:`trafo.rotate`, :class:`trafo.scale`,
   :class:`trafo.slant`, :class:`trafo.mirror`) to the path or canvas item.


.. _attr:

The attribute system: :mod:`attr`
=================================

.. module:: attr
   :synopsis: Attribute hierarchy, merging, and cycling

Both casual users and developers benefit from understanding how PyX processes
attribute lists. Whenever a list of attributes is passed to a PyX method (or
combined with default attributes), the :mod:`attr` module validates their types,
resolves overrides, removes cleared attributes, and sorts order-dependent
attributes.

For example, if a function supplies ``[style.linewidth.thin,
style.linestyle.dashed]`` by default and the user appends
``[style.linewidth.thick, style.linestyle.clear]``, PyX merges the combined list:
``style.linewidth.thick`` replaces ``style.linewidth.thin`` (because
``linewidth`` is an exclusive attribute), and ``style.linestyle.clear`` removes
``style.linestyle.dashed`` completely.

For developers implementing custom attributes or graph styles, :mod:`attr`
provides the following base classes and helper functions:

.. class:: attr()

   Base class for all attributes in PyX. Multiple instances of a plain
   :class:`attr` subclass can coexist in a merged attribute list.

.. class:: exclusiveattr(exclusiveclass=None)

   Base class for attributes that are mutually exclusive within a family
   *exclusiveclass*. When an attribute list is merged, only the last instance
   belonging to *exclusiveclass* is retained. For example, all
   :class:`style.linewidth` instances share ``style.linewidth`` as their
   *exclusiveclass*, so specifying a new line width overrides any earlier line
   width in the same list.

.. class:: clearclass(clear)

   Creates an attribute class (customarily bound as ``SomeAttr.clear``) that
   removes all preceding instances of *clear* from an attribute list when merged.
   For example, ``style.linestyle.clear`` clears any previously set line style,
   and ``deco.stroked.clear`` suppresses stroking on a path.

.. class:: sortbeforeattr(beforeclasses)
           sortbeforeexclusiveattr(exclusiveclass, beforeclasses)

   Base classes for attributes whose relative order matters (such as text
   attributes in :mod:`text`, where e.g. :class:`text.valign` must be applied
   outside :class:`text.parbox`). During :func:`mergeattrs`, instances are
   ordered so that they appear before any attribute belonging to *beforeclasses*,
   or raise a :exc:`TypeError` if the user placed them in a conflicting order.

.. class:: changeattr()

   Base class for changeable attributes that vary across a sequence of plot
   items in :mod:`graph`. When a graph plots multiple datasets with the same
   style, it calls :func:`selectattrs` with the current dataset index and total
   count.

.. class:: changelist(attrs)

   A :class:`changeattr` initialized with a list *attrs* of attributes. When
   selected for dataset index *index* (0-based), it returns
   ``attrs[index % len(attrs)]`` (cycling through the list). If an entry in
   *attrs* is ``None``, that attribute is omitted for that step.

   For example, to cycle through three colors when plotting multiple curves in a
   graph::

      mycolors = attr.changelist([color.rgb.red, color.rgb.green, color.rgb.blue])

.. class:: cyclingchangelist(lists)

   A :class:`changeattr` that takes a list of attribute lists and cycles through
   all combinations, varying the first list fastest, then the second, and so on.

.. function:: mergeattrs(attrs)

   Returns a new list of attributes with all overrides (:class:`exclusiveattr`),
   clearings (:class:`clearclass`), and ordering constraints
   (:class:`sortbeforeattr`) resolved.

.. function:: checkattrs(attrs, allowed)

   Verifies that every element in *attrs* is an instance of at least one class in
   the sequence *allowed*, raising :exc:`TypeError` otherwise.

.. function:: getattrs(attrs, get)

   Returns a sub-list of *attrs* containing only instances of the classes in
   *get*.

.. function:: selectattr(attr, index, total)
              selectattrs(attrs, index, total)

   Resolves any :class:`changeattr` instances for the given *index* out of
   *total* items and returns the resulting attribute or merged attribute list.


.. _style:

Styles: :mod:`style`
====================

.. module:: style
   :synopsis: Path stroke and fill styles

The :mod:`style` module provides classes that set PostScript, PDF, and SVG
stroke and fill state parameters. Every style class provides a ``.clear``
attribute (created via :class:`attr.clearclass`) to remove that style from an
attribute list.

Stroke styles
-------------

All stroke styles inherit from :class:`strokestyle`:

.. class:: linecap(value=0)

   Controls the shape of the ends of open subpaths when they are stroked. Four
   predefined instances are available as class attributes:

   - ``linecap.butt`` (``0``, default): The stroke is squared off flush at the
     endpoint of the path with no projection beyond it.
   - ``linecap.round`` (``1``): A semicircular arc with a diameter equal to the
     line width is drawn around the endpoint.
   - ``linecap.square`` (``2``): The stroke continues beyond the endpoint for
     half the line width and is squared off.
   - ``linecap.clear``: Clears any preceding :class:`linecap` setting.

.. class:: linejoin(value=0)

   Controls the shape of corners where two path segments meet when stroked.
   Four predefined instances are available as class attributes:

   - ``linejoin.miter`` (``0``, default): The outer edges of the two segments
     are extended until they meet at a sharp point (subject to
     :class:`miterlimit`).
   - ``linejoin.round`` (``1``): A circular arc with a diameter equal to the
     line width rounds off the corner.
   - ``linejoin.bevel`` (``2``): The meeting segments are finished with butt
     caps and the resulting notch is filled with a triangle.
   - ``linejoin.clear``: Clears any preceding :class:`linejoin` setting.

.. class:: miterlimit(value=10.0)

   Limits the ratio of the miter length to the line width when
   ``linejoin.miter`` is active. When two segments meet at a sharp angle such
   that the ratio :math:`1 / \sin(\varphi / 2)` exceeds *value*, the join is
   automatically beveled instead of mitered. Predefined instances correspond to
   minimum interior angles:

   - ``miterlimit.lessthan180deg`` (``1.0``)
   - ``miterlimit.lessthan90deg`` (``1.41421356``)
   - ``miterlimit.lessthan60deg`` (``2.0``)
   - ``miterlimit.lessthan45deg`` (``2.61312593``)
   - ``miterlimit.lessthan30deg`` (``3.86370331``)
   - ``miterlimit.lessthan22p5deg`` (``5.12583090``)
   - ``miterlimit.lessthan15deg`` (``7.66129758``)
   - ``miterlimit.lessthan11deg`` (``10.0``, default)
   - ``miterlimit.lessthan10deg`` (``11.47371325``)
   - ``miterlimit.lessthan5deg`` (``22.92558553``)
   - ``miterlimit.lessthan2deg`` (``57.29868850``)
   - ``miterlimit.lessthan1deg`` (``114.59301347``)
   - ``miterlimit.clear``: Clears any preceding :class:`miterlimit` setting.

.. class:: dash(pattern=(), offset=0, linelength=unit.w_pt)

   Defines a dash pattern for stroked paths. *pattern* is a tuple or list of
   numbers specifying alternating lengths of dashes and gaps, measured in
   multiples of *linelength* (which defaults to ``1 * unit.w_pt`` so that dashes
   scale with the current line width unless ``linelength`` is overridden).
   *offset* specifies the phase at which the pattern starts.

   Predefined instances are:

   - ``dash.clear``: Clears any preceding :class:`dash` setting.

.. class:: linedist(dist=unit.w_pt)

   Specifies the base unit length used by :class:`dash` patterns without
   altering the dash pattern itself. ``linedist.clear`` removes any preceding
   :class:`linedist` setting.

.. class:: linestyle(c=linecap.butt, d=dash())

   Combines a :class:`linecap` and a :class:`dash` pattern. Setting a
   :class:`linestyle` overrides both :class:`linecap` and :class:`dash` (and vice
   versa). Five predefined line styles are provided:

   - ``linestyle.solid``: ``linecap.butt`` with solid line ``dash(())``.
   - ``linestyle.dashed``: ``linecap.butt`` with ``dash((2,))``.
   - ``linestyle.dotted``: ``linecap.round`` with ``dash((0, 2))``.
   - ``linestyle.dashdotted``: ``linecap.round`` with ``dash((0, 2, 2, 2))``.
   - ``linestyle.clear``: Clears any preceding :class:`linestyle`,
     :class:`linecap`, or :class:`dash` setting.

.. class:: linewidth(width)

   Sets the stroke width to the PyX length *width* (converted using the
   ``w``-scale by default if a plain number is given). Predefined line widths
   form a geometric progression around ``linewidth.normal``
   (``0.02 * unit.w_cm``, i.e. approximately ``0.567 pt``) with factor
   :math:`\sqrt{2}`:

   - ``linewidth.THIN``: :math:`\text{normal} / 8`
   - ``linewidth.THIn``: :math:`\text{normal} / 4\sqrt{2}`
   - ``linewidth.THin``: :math:`\text{normal} / 4`
   - ``linewidth.Thin``: :math:`\text{normal} / 2\sqrt{2}`
   - ``linewidth.thin``: :math:`\text{normal} / 2`
   - ``linewidth.normal``: ``0.02 * unit.w_cm`` (default)
   - ``linewidth.thick``: :math:`\text{normal} \cdot \sqrt{2}`
   - ``linewidth.Thick``: :math:`\text{normal} \cdot 2`
   - ``linewidth.THick``: :math:`\text{normal} \cdot 2\sqrt{2}`
   - ``linewidth.THIck``: :math:`\text{normal} \cdot 4`
   - ``linewidth.THICk``: :math:`\text{normal} \cdot 4\sqrt{2}`
   - ``linewidth.THICK``: :math:`\text{normal} \cdot 8`
   - ``linewidth.clear``: Clears any preceding :class:`linewidth` setting.

A visual table of all predefined line styles and widths is given in
:ref:`pathstyles`.


Fill styles
-----------

All fill styles inherit from :class:`fillstyle`:

.. class:: fillrule(even_odd=0)

   Selects the rule used to determine the interior of self-intersecting or
   compound closed paths when filling:

   - ``fillrule.nonzero_winding`` (``even_odd=0``, default): Uses the nonzero
     winding number rule.
   - ``fillrule.even_odd`` (``even_odd=1``): Uses the alternating even-odd rule.
   - ``fillrule.clear``: Clears any preceding :class:`fillrule` setting.

Colors (:ref:`color`) and patterns (:ref:`pattern`) also act as fill styles (as
well as stroke styles).


.. _deco:

Decorators: :mod:`deco`
=======================

.. module:: deco
   :synopsis: Path decorators

Unlike styles, which only alter graphics state variables, decorators determine
the drawing operations performed on a path or attach additional graphical
elements (such as arrowheads, text, or markers) to it. All decorators inherit
from :class:`baseclasses.deco`.

Every decorator class provides a default instance at the class level where
appropriate (so you can write ``[deco.stroked]`` or ``[deco.earrow]`` without
parentheses) and supports calling an existing instance with new arguments to
create a customized copy (e.g., ``deco.earrow.Large([color.rgb.red])``).


Stroking and filling
--------------------

.. class:: stroked(styles=[])

   Decorates a path by stroking its outline. *styles* is an optional list of
   :class:`style.strokestyle` instances (such as :class:`style.linewidth`,
   :class:`style.linestyle`, or :class:`color.color`) applied locally only to the
   stroked outline, without affecting fills or other decorators on the same
   path.

   - ``deco.stroked`` can be used directly without instantiation when no local
     styles are needed.
   - ``deco.stroked.clear`` removes any preceding :class:`stroked` decorator from
     an attribute list (useful when a graph style strokes a path by default, and
     you only want to fill it).

.. class:: filled(styles=[])

   Decorates a path by filling its interior. *styles* is an optional list of
   :class:`style.fillstyle` instances (such as :class:`color.color`,
   :class:`pattern.pattern`, or :class:`style.fillrule`) applied locally only to
   the fill operation.

   - ``deco.filled`` can be used directly without instantiation.
   - ``deco.filled.clear`` removes any preceding :class:`filled` decorator from
     an attribute list.


Arrows
------

.. class:: arrow(attrs=[], pos=1, reversed=0, size=_base, angle=45, constriction=None)
           barrow(attrs=[], size=_base, angle=45, constriction=None)
           earrow(attrs=[], size=_base, angle=45, constriction=None)

   Attaches an arrowhead to a path. :class:`barrow` places an arrowhead at the
   beginning of the path (``pos=0, reversed=1``), :class:`earrow` places an
   arrowhead at the end of the path (``pos=1, reversed=0``), and :class:`arrow`
   allows arbitrary placement along the relative arc-length position *pos*
   :math:`\in [0, 1]`. When placed at the beginning or end of the path, the
   underlying path is automatically shortened slightly so that its stroked tip
   does not poke through the sharp point of the arrowhead.

   Parameters:

   - *attrs*: List of stroke/fill styles and decorators (:class:`stroked`,
     :class:`filled`, :class:`style.strokestyle`, :class:`style.fillstyle`)
     controlling the appearance of the arrowhead. By default, arrowheads are both
     filled and stroked with ``style.linejoin.round`` and ``style.linestyle.solid``.
     Passing ``deco.filled.clear`` in *attrs* produces an open, stroked-only
     two-barb arrowhead; passing ``deco.stroked.clear`` produces a purely filled
     arrowhead.
   - *size*: Characteristic length of the arrowhead (default ``_base = 0.15 *
     unit.v_cm``).
   - *angle*: Opening angle of the arrowhead in degrees (default ``45``).
   - *constriction*: Ratio of the indented back-center distance to the full
     arrowhead length. When ``None`` (the default), a standard constriction of
     ``0.8`` is used. When set to ``False``, no constriction is used, yielding a
     triangular arrowhead with a straight base.

   Existing arrow instances can be called to override any parameter, e.g.
   ``deco.earrow.Large([color.rgb.red], angle=30)``.

   Both :class:`barrow` and :class:`earrow` provide predefined instances scaled
   by powers of :math:`\sqrt{2}` around the base size:

   - ``.SMALL``, ``.SMALl``, ``.SMAll``, ``.SMall``, ``.Small``, ``.small``,
     ``.normal``, ``.large``, ``.Large``, ``.LARGE``, ``.huge``, ``.Huge``
   - ``.SMArr``, ``.smarr``, ``.sMarr``, ``.SmArr``: Shorthand variants combining
     small/normal sizes with narrower/wider angles.
   - ``.clear``: Removes any preceding :class:`barrow` or :class:`earrow` from an
     attribute list.

   See :ref:`arrows` in the Appendix for a visual overview of all predefined
   arrows.


Text and canvas item decorators
-------------------------------

.. class:: text(text, textattrs=[], angle=0, textdist=0.1*unit.v_cm, relarclenpos=0.5, arclenfrombegin=None, arclenfromend=None, texrunner=None)

   Typesets *text* and attaches it at a point along the path.

   - *text*: String to typeset.
   - *textattrs*: List of text attributes (defaulting to
     ``[text.halign.center, text.vshift.mathaxis]`` merged with *textattrs*).
   - *angle*: Angle in degrees by which the text label is rotated relative to horizontal
     (and determining the direction in which the label is displaced by *textdist*
     from the path).
   - *textdist*: Distance between the anchor point on the path and the text box
     (default ``0.1 * unit.v_cm``).
   - *relarclenpos*: Relative arc-length position :math:`\in [0, 1]` along the
     path (default ``0.5``, the midpoint). Ignored if *arclenfrombegin* or
     *arclenfromend* is specified.
   - *arclenfrombegin*: Distance from the start of the path (cannot be combined
     with *arclenfromend*).
   - *arclenfromend*: Distance from the end of the path (cannot be combined with
     *arclenfrombegin*).
   - *texrunner*: Optional text engine instance (defaults to
     ``text.defaulttextengine``).

.. class:: curvedtext(text, textattrs=[], relarclenpos=0.5, arclenfrombegin=None, arclenfromend=None, exclude=None, singlecharmode=True, texrunner=None)

   Typesets *text* character-by-character so that its baseline follows the local
   tangent of the curved path:

   .. code-block:: python

      c.stroke(path.curve(0, 0, 1, 2, 3, -1, 4, 1),
               [deco.curvedtext("Text along a curve", [text.vshift.mathaxis], exclude=0.1)])

   - *text*: String to typeset along the path.
   - *textattrs*: List of text attributes, transformations, or fill styles.
     Horizontal alignment attributes (:attr:`text.halign.left`,
     :attr:`text.halign.center`, :attr:`text.halign.right`) control how the text
     span is aligned relative to the anchor point on the path.
   - *relarclenpos*, *arclenfrombegin*, *arclenfromend*: Specify the anchor
     position along the path in the same way as in :class:`deco.text`.
   - *exclude*: When set to a PyX length (e.g. ``0.1``), cuts out the underlying
     path where the text sits, leaving a padding of *exclude* on both sides of
     the text.
   - *singlecharmode*: Passed to the text engine (default ``True``, required for
     individual characters in DVI output to be positioned and rotated separately
     along the curve).
   - *texrunner*: Optional text engine instance.

.. class:: insert(canvasitem, attrs=[], relarclenpos=0.5, arclenfrombegin=None, arclenfromend=None, exclude=None)

   Inserts an arbitrary *canvasitem* (such as a :class:`canvas.canvas` or a
   filled symbol) aligned with the local tangent coordinate frame of the path at
   the position specified by *relarclenpos*, *arclenfrombegin*, or
   *arclenfromend*. If *exclude* is set to a length, the underlying path is split
   and removed across the horizontal extent of *canvasitem* enlarged by
   *exclude*.


Diagnostic and gradient decorators
----------------------------------

.. class:: shownormpath(styles=[], clearer=[])

   A diagnostic decorator that visualizes the control polygon, knots, and tangent
   directions of each :class:`normpath.normsubpathitem` in a path. This is
   particularly useful when inspecting curves, font outlines, or path deformers.

.. class:: colorgradient(grad, styles=[], steps=20)

   Splits the path into *steps* equal-arc-length segments and draws each segment
   with the color sampled from the :class:`color.gradient` *grad* along with
   *styles* (defaulting to ``[deco.stroked]`` if neither :class:`stroked` nor
   :class:`filled` is present in *styles*).
