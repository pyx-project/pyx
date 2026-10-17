.. _graphics:

**************
Basic graphics
**************

.. sectionauthor:: Jörg Lehmann <joerg@pyx-project.org>

The chapters in this part describe the core building blocks for creating
graphics in PyX and writing the result to PostScript, EPS, PDF, and SVG files.
Before diving into the reference chapters for individual modules, this chapter
introduces PyX's drawing model, path construction and geometric operations, the
attribute system (:mod:`attr`), path styles (:mod:`style`), and path decorators
(:mod:`deco`).


Introduction
============

The :mod:`path` module allows you to construct PostScript-like *paths*, which are
the primary geometric building blocks for drawings in PyX. A path represents an
arbitrary shape composed of straight line segments, circular or elliptical arc
segments, and cubic Bézier curves. A path does not need to be contiguous; it may
comprise several disconnected segments called *subpaths*.

Typically, a path is constructed by passing path primitives (:class:`path.moveto`,
:class:`path.lineto`, :class:`path.curveto`, etc.) to the :class:`path.path`
constructor. For example, the following snippet defines a path *p* consisting of
a straight line from :math:`(0, 0)` to :math:`(1, 1)`::

   from pyx import *
   p = path.path(path.moveto(0, 0), path.lineto(1, 1))

Equivalently, you can use the predefined :class:`path.path` subclass
:class:`path.line`::

   p = path.line(0, 0, 1, 1)

While geometric operations can already be performed on a path object itself (see
the next section), rendering the path requires a :class:`canvas.canvas`
instance, conventionally named *c*::

   c = canvas.canvas()

To draw the path on the canvas and write the figure to an EPS, PDF, or SVG file,
use :meth:`canvas.canvas.stroke` followed by one of the output methods::

   c.stroke(p)
   c.writeEPSfile("line")
   c.writePDFfile("line")
   c.writeSVGfile("line")

The file extension (``.eps``, ``.pdf``, or ``.svg``) is appended automatically
if not already present in the filename.

As a second example, let us define a path consisting of two disconnected
subpaths::

   cross = path.path(path.moveto(0, 0), path.rlineto(1, 1),
                     path.moveto(1, 0), path.rlineto(-1, 1))

The first subpath is a straight line from :math:`(0, 0)` to :math:`(1, 1)` using
:class:`path.rlineto`, whose coordinates are measured relative to the current
point. The second :class:`path.moveto` opens a new subpath starting at
:math:`(1, 0)` and ending at :math:`(0, 1)`. Even though the two lines intersect
at :math:`(1/2, 1/2)`, they remain separate subpaths. In general, every
occurrence of :class:`path.moveto` starts a new subpath. Consequently, a
rectangle should not be constructed as four separate subpaths::

   rect1 = path.path(path.moveto(0, 0), path.lineto(0, 1),
                     path.moveto(0, 1), path.lineto(1, 1),
                     path.moveto(1, 1), path.lineto(1, 0),
                     path.moveto(1, 0), path.lineto(0, 0))

which produces unjoined corners (see Fig. :ref:`fig_rects` a). Keeping the pen
down between corners produces a single open subpath (Fig. :ref:`fig_rects` b):

.. _fig_rects:
.. figure:: rects.*
   :align: center

   Rectangle consisting of (a) four separate lines, (b) one open path, and (c)
   one closed path. (d) Filling a path closes open subpaths automatically.

::

   rect2 = path.path(path.moveto(0, 0), path.lineto(0, 1),
                     path.lineto(1, 1), path.lineto(1, 0),
                     path.lineto(0, 0))

As visible in the lower-left corner of Fig. :ref:`fig_rects` b, an open path
whose start and end points coincide still has two unconnected line caps at its
origin. To properly join the start and end of the subpath, close it with
:class:`path.closepath` (Fig. :ref:`fig_rects` c)::

   rect3 = path.path(path.moveto(0, 0), path.lineto(0, 1),
                     path.lineto(1, 1), path.lineto(1, 0),
                     path.closepath())

:class:`path.closepath` adds a straight line segment from the current point back
to the initial point of the current subpath and joins the meeting edges using the
active line join style. Filling a path implicitly closes every open subpath, as
shown in Fig. :ref:`fig_rects` d::

   c.stroke(rect2, [deco.filled([color.grey(0.5)])])

Here, the second argument to :meth:`canvas.canvas.stroke` is an attribute list
containing the decorator :data:`deco.filled`, which instructs PyX to fill the
interior of the stroked path with the given gray shade. Rectangles are, of
course, also available directly as :class:`path.rect`::

   rect = path.rect(0, 0, 1, 1)

where the first two arguments specify the lower-left corner and the last two
arguments specify the width and height. Full details on all path items and
predefined shapes are given in chapter :ref:`path` (and smooth Hobby–Knuth
splines in chapter :ref:`metapost`).


Path operations
===============

Often, you want to perform geometric calculations on paths before stroking or
filling them—such as intersecting two paths, splitting them at their
intersection points, and joining the resulting segments to form a new closed
contour.

Suppose you want to draw the radii from the center of a circle to its
intersection points with a straight line. The following code produces
Fig. :ref:`fig_radii`:

.. include:: radii.py
   :literal:

.. _fig_radii:
.. figure:: radii.*
   :align: center

   Intersection of a circle with a straight line yielding two radii.

After defining a circle centered at :math:`(0, 0)` with radius :math:`2` and a
straight line, calling ``circle.intersect(line)`` returns a 2-tuple of lists of
parameter values: the first list (*isects_circle*) contains the intersection
parameters along *circle*, and the second (*isects_line*) contains the
corresponding parameters along *line*. Passing each parameter to
:meth:`path.path.at` yields the :math:`(x, y)` coordinates of the intersection
point.

To shade the circular segment bounded by the line and the shorter arc (see
Fig. :ref:`fig_radii2`), we split both paths at their intersection parameters
and join the pieces::

   arc1, arc2 = circle.split(isects_circle)
   if arc1.arclen() < arc2.arclen():
       arc = arc1
   else:
       arc = arc2

   isects_line.sort()
   line1, line2, line3 = line.split(isects_line)

   segment = line2 << arc

.. _fig_radii2:
.. figure:: radii2.*
   :align: center

   Intersection of a circle with a line yielding two radii and a filled circular segment.

Splitting the closed circle at two points yields two arc segments, and
:meth:`path.path.arclen` selects the shorter one. Because
:meth:`path.path.split` requires an ascending list of parameter values,
*isects_line* is sorted before splitting the line into three pieces. Finally,
the ``<<`` operator joins the middle line segment *line2* and *arc* into a
single connected subpath so that filling works as expected (whereas ``+`` would
merely concatenate them as separate subpaths).

When working with path parameters, note that PyX converts paths into normalized
paths (:class:`normpath.normpath`) composed of straight lines and cubic Bézier
curves before performing geometric operations. Each elementary segment of a
normalized subpath spans a parameter interval of length :math:`1` (see
:class:`normpath.normpathparam`), and the start and end parameters of a path are
returned by :meth:`path.path.begin` and :meth:`path.path.end`. Alternatively,
all path methods that accept a parameter value also accept a PyX length
specifying the arc length measured from the start of the path::

   from math import pi
   r = 2
   pt1 = path.circle(0, 0, r).at(r * pi)
   pt2 = path.circle(0, 0, r).at(r * 3 * pi / 2)
   c.stroke(path.line(pt1[0], pt1[1], pt2[0], pt2[1]))


.. _graphics_attributes:

Attributes: Styles and Decorations
==================================

Attributes control the visual appearance and geometric processing of objects
when they are drawn. Orthogonal properties—such as line width, line style, color,
and arrowheads—are represented by distinct attribute classes and passed together
in a list as an optional argument to drawing methods::

   c.stroke(p, [style.linewidth.Thick, style.linestyle.dashed])

In fact, :meth:`canvas.canvas.stroke` and :meth:`canvas.canvas.fill` are
convenient shortcuts for :meth:`canvas.canvas.draw`: ``c.stroke(p, attrs)`` is
equivalent to ``c.draw(p, [deco.stroked] + list(attrs))``, and
``c.fill(p, attrs)`` is equivalent to ``c.draw(p, [deco.filled] + list(attrs))``.

PyX's attribute system provides three key mechanisms:

1. **Predefined attribute instances**: Many attribute classes attach commonly
   used instances as class attributes. For example, ``style.linewidth.Thick`` is
   a predefined :class:`style.linewidth` instance with width
   :math:`0.04\,\text{w cm}` (twice ``style.linewidth.normal``).
2. **Attribute merging and clearing**: When an attribute list is merged (for
   example, when user attributes are appended to default attributes), later
   instances of an exclusive attribute family automatically override earlier
   ones::

      # The following two calls are equivalent:
      c.stroke(p, [style.linewidth.Thick, style.linewidth.thin])
      c.stroke(p, [style.linewidth.thin])

   Every exclusive attribute class also provides a ``.clear`` attribute that
   removes any preceding instance of that class from the attribute list::

      # The following two calls are equivalent:
      c.stroke(p, [style.linewidth.Thick, style.linewidth.clear])
      c.stroke(p)

   Furthermore, ``attr.clear`` removes *all* preceding attributes from an
   attribute list.
3. **Customizing predefined instances by calling them**: Predefined decorator
   and deformer instances can be called with new arguments to return a modified
   copy. For example, ``deco.filled`` is already an instance of the fill
   decorator, and calling ``deco.filled([color.rgb.green])`` creates a new fill
   decorator with a local green fill color::

      c.stroke(p, [deco.filled([color.rgb.green])])

   Similarly, calling ``deco.earrow(angle=30)`` or
   ``deco.earrow.Large([color.rgb.red])`` returns a customized end-arrow
   decorator.

The main attribute categories in PyX are summarized below:

+----------------------------+------------------------------------+-------------------------------------+
| Attribute category         | Description                        | Examples                            |
+============================+====================================+=====================================+
| :class:`deco.deco`         | Path decorators specifying how a   | :data:`deco.stroked`,               |
|                            | path is drawn or ornamented        | :data:`deco.filled`,                |
|                            |                                    | :class:`deco.arrow`,                |
|                            |                                    | :class:`deco.text`                  |
+----------------------------+------------------------------------+-------------------------------------+
| :class:`style.strokestyle` | Styles used when stroking a path   | :class:`style.linecap`,             |
|                            |                                    | :class:`style.linejoin`,            |
|                            |                                    | :class:`style.miterlimit`,          |
|                            |                                    | :class:`style.dash`,                |
|                            |                                    | :class:`style.linestyle`,           |
|                            |                                    | :class:`style.linewidth`,           |
|                            |                                    | :class:`color.color`,               |
|                            |                                    | :class:`color.transparency`         |
+----------------------------+------------------------------------+-------------------------------------+
| :class:`style.fillstyle`   | Styles used when filling a path    | :class:`color.color`,               |
|                            |                                    | :class:`color.transparency`,        |
|                            |                                    | :class:`pattern.pattern`,           |
|                            |                                    | :class:`style.fillrule`             |
+----------------------------+------------------------------------+-------------------------------------+
| :class:`baseclasses.deformer` | Geometric path deformers        | :class:`deformer.cycloid`,          |
|                            |                                    | :class:`deformer.smoothed`,         |
|                            |                                    | :class:`deformer.parallel`          |
+----------------------------+------------------------------------+-------------------------------------+
| :class:`text.textattr`     | Attributes used for text           | :class:`text.halign`,               |
|                            | typesetting                        | :class:`text.valign`,               |
|                            |                                    | :class:`text.vshift`,               |
|                            |                                    | :data:`text.mathmode`,              |
|                            |                                    | :data:`text.phantom`,               |
|                            |                                    | :class:`text.size`,                 |
|                            |                                    | :class:`text.parbox`                |
+----------------------------+------------------------------------+-------------------------------------+
| :class:`trafo.trafo_pt`    | Affine coordinate transformations  | :class:`trafo.mirror`,              |
|                            |                                    | :class:`trafo.rotate`,              |
|                            |                                    | :class:`trafo.scale`,               |
|                            |                                    | :class:`trafo.slant`,               |
|                            |                                    | :class:`trafo.translate`            |
+----------------------------+------------------------------------+-------------------------------------+


.. _attr:

The attribute system: :mod:`attr`
=================================

.. module:: attr
   :synopsis: Attribute hierarchy, merging, and cycling

Whenever a list of attributes is passed to a PyX method, the :mod:`attr` module
checks that only allowed attribute classes are present, resolves overrides and
clearings, and enforces ordering constraints. It also provides *changeable
attributes* that cycle through attribute lists when plotting multiple datasets
in :mod:`graph`.

.. class:: attr()

   Base class of all attributes in PyX (colors, decorators, styles, deformers,
   text attributes, and transformations). Its :meth:`merge` method appends
   ``self`` to an attribute list *attrs* and returns the updated list.

.. class:: exclusiveattr(exclusiveclass)

   Base class for attributes that swallow all preceding attributes in an
   attribute list that are instances of *exclusiveclass*.

.. class:: sortbeforeattr(beforetheclasses)

   Base class for attributes that place themselves immediately before the first
   attribute in the list that is an instance of any class in *beforetheclasses*.

.. class:: sortbeforeexclusiveattr(exclusiveclass, beforetheclasses)

   Combines :class:`exclusiveattr` and :class:`sortbeforeattr`: removes all
   other instances of *exclusiveclass* and places itself before any instance of
   *beforetheclasses*.

.. class:: clearclass(clearclass)

   Creates an attribute (customarily bound as ``SomeAttr.clear``) whose
   :meth:`merge` method removes all preceding instances of *clearclass* from an
   attribute list.

.. data:: clear

   An attribute instance that removes *all* preceding attributes in an attribute
   list when merged.

.. class:: changeattr()

   Base class for changeable attributes resolved via :meth:`select(index, total)`
   when plotting multiple datasets in a graph.

.. class:: changelist(attrs, cyclic=1)

   A :class:`changeattr` initialized with a list *attrs* of attribute choices:

   - *attrs*: List of attributes to step through as datasets are plotted.
   - *cyclic*: If true (default ``1``), selection wraps around modulo
     ``len(attrs)`` after reaching the end of the list; otherwise, selecting an
     index beyond ``len(attrs) - 1`` returns ``None``.

   For example, to cycle through three colors across curves in a graph::

      mycolors = attr.changelist([color.rgb.red, color.rgb.green, color.rgb.blue])

.. class:: multichangeattr(changeattrs)

   A :class:`changeattr` initialized with a dictionary or list *changeattrs* of
   :class:`changeattr` instances indexed by the total number *total* of
   selections, delegating ``select(index, total)`` to
   ``changeattrs[total].select(index, total)``.

.. function:: mergeattrs(attrs)

   Merges the attribute list *attrs* by calling each attribute's :meth:`merge`
   method in sequence and returns the resulting list.

.. function:: getattrs(attrs, getclasses)

   Returns a list of all attributes in *attrs* that are instances of any class
   in *getclasses*.

.. function:: checkattrs(attrs, allowedclasses)

   Checks that every element in *attrs* is an instance of at least one class in
   *allowedclasses*, raising :exc:`TypeError` otherwise.

.. function:: refineattrs(attrs, defaults, allowedclasses, allow_none=True)

   Combines validation and merging: returns ``None`` if *allow_none* is true and
   *attrs* is ``None``, otherwise validates *attrs* against *allowedclasses* and
   returns ``mergeattrs(defaults + attrs)``.

.. function:: selectattrs(attrs, index, total)
              selectattr(attr, index, total)

   Evaluates all :class:`changeattr` instances in *attrs* (or a single *attr*)
   for 0-based selection *index* out of *total* items.


.. _style:

Styles: :mod:`style`
====================

.. module:: style
   :synopsis: Path stroke and fill styles

The :mod:`style` module provides classes that set PostScript, PDF, and SVG
stroke and fill state parameters. Every style class provides a ``.clear``
attribute (an :class:`attr.clearclass` instance) to remove preceding instances
of that style from an attribute list.

Stroke styles
-------------

All stroke styles inherit from :class:`strokestyle`:

.. class:: linecap(value=0)

   Controls the shape of the ends of open subpaths when they are stroked:

   - ``linecap.butt`` (``0``, default): The stroke is squared off flush at the
     endpoint of the path with no projection beyond it.
   - ``linecap.round`` (``1``): A semicircular arc with a diameter equal to the
     line width is drawn around the endpoint.
   - ``linecap.square`` (``2``): The stroke continues beyond the endpoint for
     half the line width and is squared off.
   - ``linecap.clear``: Clears any preceding :class:`linecap` setting.

.. class:: linejoin(value=0)

   Controls the shape of corners where two path segments meet when stroked:

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
   ``linejoin.miter`` is active. When two segments meet at a sharp interior
   angle :math:`\varphi` such that :math:`1 / \sin(\varphi / 2)` exceeds
   *value*, the corner is beveled instead of mitered. Predefined instances
   correspond to minimum interior angles before beveling occurs:

   - ``miterlimit.lessthan180deg`` (``1 / sin(pi * 180 / 360) = 1.0``)
   - ``miterlimit.lessthan90deg`` (``1 / sin(pi * 90 / 360)``)
   - ``miterlimit.lessthan60deg`` (``1 / sin(pi * 60 / 360) = 2.0``)
   - ``miterlimit.lessthan45deg`` (``1 / sin(pi * 45 / 360)``)
   - ``miterlimit.lessthan11deg`` (``10``, default, corresponding to
     approximately :math:`11.4783^\circ`)
   - ``miterlimit.clear``: Clears any preceding :class:`miterlimit` setting.

.. class:: dash(pattern=[], offset=0, rellengths=1)

   Defines a dash pattern for stroked paths:

   - *pattern*: List or tuple of numbers specifying alternating lengths of
     dashes and gaps.
   - *offset*: Phase offset at which the dash pattern starts (default ``0``).
   - *rellengths*: When true (default ``1``), dash and gap lengths in *pattern*
     are scaled relative to the current line width (in units of the default line
     width); when false (``0``), they are interpreted in raw PostScript points.
   - ``dash.clear``: Clears any preceding :class:`dash` setting.

.. class:: linestyle(c=linecap.butt, d=dash([]))

   Combines a :class:`linecap` *c* and a :class:`dash` pattern *d*:

   - ``linestyle.solid``: ``linecap.butt`` with ``dash([])``.
   - ``linestyle.dashed``: ``linecap.butt`` with ``dash([2])``.
   - ``linestyle.dotted``: ``linecap.round`` with ``dash([0, 2])``.
   - ``linestyle.dashdotted``: ``linecap.round`` with ``dash([0, 2, 2, 2])``.
   - ``linestyle.clear``: Clears any preceding :class:`linestyle` setting.

.. class:: linewidth(width)

   Sets the stroke width to the PyX length *width* (using the ``w``-scale if a
   plain number is given). Predefined line widths form a geometric progression
   around ``linewidth.normal`` (``0.02 * unit.w_cm``, approximately ``0.567 pt``)
   with factor :math:`\sqrt{2}`:

   - ``linewidth.THIN``: :math:`\text{normal} / \sqrt{32} = \text{normal} / 4\sqrt{2}`
   - ``linewidth.THIn``: :math:`\text{normal} / \sqrt{16} = \text{normal} / 4`
   - ``linewidth.THin``: :math:`\text{normal} / \sqrt{8} = \text{normal} / 2\sqrt{2}`
   - ``linewidth.Thin``: :math:`\text{normal} / \sqrt{4} = \text{normal} / 2`
   - ``linewidth.thin``: :math:`\text{normal} / \sqrt{2}`
   - ``linewidth.normal``: ``0.02 * unit.w_cm`` (default)
   - ``linewidth.thick``: :math:`\text{normal} \cdot \sqrt{2}`
   - ``linewidth.Thick``: :math:`\text{normal} \cdot \sqrt{4} = \text{normal} \cdot 2`
   - ``linewidth.THick``: :math:`\text{normal} \cdot \sqrt{8} = \text{normal} \cdot 2\sqrt{2}`
   - ``linewidth.THIck``: :math:`\text{normal} \cdot \sqrt{16} = \text{normal} \cdot 4`
   - ``linewidth.THICk``: :math:`\text{normal} \cdot \sqrt{32} = \text{normal} \cdot 4\sqrt{2}`
   - ``linewidth.THICK``: :math:`\text{normal} \cdot \sqrt{64} = \text{normal} \cdot 8`
   - ``linewidth.clear``: Clears any preceding :class:`linewidth` setting.

A visual chart of all predefined line caps, joins, miter limits, line styles,
and line widths is given in :ref:`pathstyles`.


Fill styles
-----------

All fill styles inherit from :class:`fillstyle`:

.. class:: fillrule(even_odd)

   Selects the rule used to determine the interior of self-intersecting or
   compound closed paths when filling:

   - ``fillrule.nonzero_winding`` (``even_odd=0``, default): Uses the nonzero
     winding number rule.
   - ``fillrule.even_odd`` (``even_odd=1``): Uses the alternating even-odd rule.
   - ``fillrule.clear``: Clears any preceding :class:`fillrule` setting.

Colors (:ref:`color`), transparency (:class:`color.transparency`), and patterns
(:ref:`pattern`) inherit from both :class:`strokestyle` and :class:`fillstyle`.


.. _deco:

Decorators: :mod:`deco`
=======================

.. module:: deco
   :synopsis: Path decorators

Unlike styles, which only set graphics state parameters, path decorators depend
on the concrete path to which they are applied: they specify whether the path is
stroked or filled and can attach additional graphical ornaments (such as
arrowheads, text labels, hatching lines, or braces) or exclude intervals of the
path from stroking. All path decorators inherit from :class:`deco`.


Stroking and filling
--------------------

.. data:: stroked

   A decorator that strokes the outline of the path. Calling
   ``deco.stroked(styles=[])`` returns a new stroke decorator with a list
   *styles* of :class:`style.strokestyle` instances (such as
   :class:`style.linewidth`, :class:`style.linestyle`, or :class:`color.color`)
   applied locally only to the stroked outline, without affecting fills or
   ornaments on the same path.

   - ``deco.stroked`` can be passed directly in an attribute list when no local
     stroke styles are needed.
   - ``deco.stroked.clear`` removes any preceding ``deco.stroked`` decorator
     from an attribute list.

.. data:: filled

   A decorator that fills the interior of the path. Calling
   ``deco.filled(styles=[])`` returns a new fill decorator with a list *styles*
   of :class:`style.fillstyle` instances (such as :class:`color.color`,
   :class:`pattern.pattern`, or :class:`style.fillrule`) applied locally only to
   the fill operation.

   - ``deco.filled`` can be passed directly in an attribute list when no local
     fill styles are needed.
   - ``deco.filled.clear`` removes any preceding ``deco.filled`` decorator from
     an attribute list.


Arrows
------

.. class:: arrow(attrs=[], pos=1, reversed=0, size=_base, angle=45, constriction=0.8)

   A decorator that attaches an arrowhead to a path. The outer contours of the
   arrowhead are constructed by cutting a segment of arc length *size* from the
   path itself and rotating it by :math:`\pm \text{angle}/2` around the tip, so
   arrowheads along curved paths naturally curve to follow the path's geometry.

   Parameters:

   - *attrs*: List of decorators (:class:`deco`), fill styles
     (:class:`style.fillstyle`), and stroke styles (:class:`style.strokestyle`)
     controlling how the arrowhead path is drawn. *attrs* is merged with the
     default attributes ``[style.linestyle.solid, deco.filled]``. Thus, by
     default arrowheads are filled (and not stroked); passing ``deco.stroked``
     in *attrs* also strokes the arrowhead outline (using a solid line style by
     default even if the main path is dashed), and passing
     ``[deco.stroked, deco.filled.clear]`` draws an unfilled, stroked arrowhead.
   - *pos*: Relative arc-length position :math:`\in [0, 1]` along the path at
     which the arrowhead is placed (default ``1``, the end of the path; ``0`` is
     the beginning of the path).
   - *reversed*: When ``0`` (default), the arrowhead points forward along the
     direction of the path; when ``1``, it points backward against the direction
     of the path. When an arrowhead sits strictly at the beginning
     (``pos=0, reversed=1``) or end (``pos=1, reversed=0``) of the path, the
     stroked main path is automatically shortened so that its line cap does not
     protrude through the sharp tip of the arrowhead.
   - *size*: Arc length of the arrowhead sides (default
     ``_base = 6 * unit.v_pt``).
   - *angle*: Opening angle of the arrowhead in degrees (default ``45``).
   - *constriction*: Ratio of the indented back-center distance to the arrowhead
     length (default ``0.8``). Setting ``constriction=None`` disables the
     indentation and yields a triangular arrowhead with a straight base.
   - ``arrow.clear``: Clears any preceding :class:`arrow` decorator from an
     attribute list.

   Calling an existing :class:`arrow` instance with keyword or positional
   arguments ``arrow(attrs=None, pos=None, reversed=None, size=None, angle=None,
   constriction=...)`` returns a new :class:`arrow` instance with the specified
   parameters overridden.

.. data:: barrow
          earrow

   Predefined :class:`arrow` instances for placing an arrowhead at the beginning
   of a path (``barrow = arrow(pos=0, reversed=1)``) or at the end of a path
   (``earrow = arrow()``). Both ``barrow`` and ``earrow`` can be used directly
   in an attribute list (e.g. ``[deco.earrow]``), called to override parameters
   (e.g. ``deco.earrow([color.rgb.red], angle=30)``), or cleared via
   ``deco.barrow.clear`` / ``deco.earrow.clear`` (which alias ``arrow.clear``).

   Both ``barrow`` and ``earrow`` provide 13 predefined size instances as
   attributes, forming a geometric progression with factor :math:`\sqrt{2}`
   around ``_base = 6 * unit.v_pt``:

   - ``barrow.SMALL``, ``earrow.SMALL``: ``size = _base / sqrt(64)`` (:math:`\text{base} / 8`)
   - ``barrow.SMALl``, ``earrow.SMALl``: ``size = _base / sqrt(32)`` (:math:`\text{base} / 4\sqrt{2}`)
   - ``barrow.SMAll``, ``earrow.SMAll``: ``size = _base / sqrt(16)`` (:math:`\text{base} / 4`)
   - ``barrow.SMall``, ``earrow.SMall``: ``size = _base / sqrt(8)`` (:math:`\text{base} / 2\sqrt{2}`)
   - ``barrow.Small``, ``earrow.Small``: ``size = _base / sqrt(4)`` (:math:`\text{base} / 2`)
   - ``barrow.small``, ``earrow.small``: ``size = _base / sqrt(2)``
   - ``barrow.normal``, ``earrow.normal``: ``size = _base`` (``6 * unit.v_pt``)
   - ``barrow.large``, ``earrow.large``: ``size = _base * sqrt(2)``
   - ``barrow.Large``, ``earrow.Large``: ``size = _base * sqrt(4)`` (:math:`\text{base} \cdot 2`)
   - ``barrow.LArge``, ``earrow.LArge``: ``size = _base * sqrt(8)`` (:math:`\text{base} \cdot 2\sqrt{2}`)
   - ``barrow.LARge``, ``earrow.LARge``: ``size = _base * sqrt(16)`` (:math:`\text{base} \cdot 4`)
   - ``barrow.LARGe``, ``earrow.LARGe``: ``size = _base * sqrt(32)`` (:math:`\text{base} \cdot 4\sqrt{2}`)
   - ``barrow.LARGE``, ``earrow.LARGE``: ``size = _base * sqrt(64)`` (:math:`\text{base} \cdot 8`)

   Each predefined size instance is itself an :class:`arrow` instance and can be
   called to customize its attributes, angle, or constriction—for example,
   ``deco.earrow.Large([deco.filled([color.rgb.red]), style.linewidth.normal])``
   or ``deco.earrow.normal(constriction=None)``. See :ref:`arrows` in the
   Appendix for a visual illustration.


Text decorators
---------------

.. class:: text(text, textattrs=[], angle=0, relangle=None, textdist=0.2, relarclenpos=0.5, arclenfrombegin=None, arclenfromend=None, texrunner=None)

   Typesets *text* and attaches the resulting text box at a point along the
   path:

   - *text*: String to typeset.
   - *textattrs*: List of text attributes merged with the defaults
     ``[text.halign.center, text.vshift.mathaxis]``.
   - *angle*: Absolute angle in degrees (measured counter-clockwise from the
     positive *x*-axis) specifying the direction in which the text box is
     displaced by *textdist* via :meth:`box.box.linealign` (default ``0``).
   - *relangle*: Angle in degrees relative to the path's local tangent direction
     at the anchor point. When not ``None``, overrides *angle*.
   - *textdist*: Distance between the anchor point on the path and the aligned
     text box (default ``0.2``).
   - *relarclenpos*: Relative arc-length position :math:`\in [0, 1]` along the
     path (default ``0.5``, the midpoint). Used when neither *arclenfrombegin*
     nor *arclenfromend* is given.
   - *arclenfrombegin*: Arc length from the beginning of the path to the anchor
     point (mutually exclusive with *arclenfromend*).
   - *arclenfromend*: Arc length from the end of the path to the anchor point
     (mutually exclusive with *arclenfrombegin*).
   - *texrunner*: Optional text engine instance (defaults to the canvas's text
     engine).

.. class:: curvedtext(text, textattrs=[], relarclenpos=0.5, arclenfrombegin=None, arclenfromend=None, texrunner=None, exclude=None)

   Typesets *text* in ``singlecharmode`` so that each character is individually
   positioned and rotated to follow the local tangent of the curved path:

   .. code-block:: python

      c.stroke(path.curve(0, 0, 1, 2, 3, -1, 4, 1),
               [deco.curvedtext("Text along a curve", [text.vshift.mathaxis], exclude=0.1)])

   - *text*: String to typeset along the path.
   - *textattrs*: List of text attributes, transformations, or fill styles
     (merged with default ``[text.halign.center]``).
   - *relarclenpos*, *arclenfrombegin*, *arclenfromend*: Specify the anchor
     position along the path in the same way as in :class:`deco.text`.
   - *texrunner*: Optional text engine instance.
   - *exclude*: When set to a PyX length (e.g. ``0.1``), cuts out the stroked
     underlying path across the horizontal extent of each character enlarged on
     both sides by *exclude*.


Hatching, gradient, brace, and diagnostic decorators
----------------------------------------------------

.. class:: linehatched(dist, angle, strokestyles=[], cross=0)

   Fills the interior of a path by clipping a set of parallel stroked lines
   spaced by *dist* at angle *angle* (in degrees) to the path. Unlike
   PostScript/PDF tiling patterns (:mod:`pattern`), :class:`linehatched` draws
   explicit vector lines clipped to the path and is therefore supported by all
   output backends and printers. It acts simultaneously as an exclusive
   :class:`linehatched` attribute and clears ``deco.filled``.

   - *dist*: Spacing between adjacent hatch lines.
   - *angle*: Angle of the hatch lines in degrees.
   - *strokestyles*: List of :class:`style.strokestyle` instances merged with
     ``[style.linewidth.THIN]``.
   - *cross*: When true (``1``), draws a second orthogonal set of hatch lines at
     ``angle + 90``.
   - ``linehatched.clear``: Clears any preceding :class:`linehatched` decorator.

   Predefined instances are provided for single hatching at
   :math:`0^\circ, 45^\circ, 90^\circ, 135^\circ` (``linehatched0``,
   ``linehatched45``, ``linehatched90``, ``linehatched135``) and cross-hatching
   at :math:`0^\circ` and :math:`45^\circ` (``crosslinehatched0``,
   ``crosslinehatched45``). Each predefined instance provides 13 spacing
   variants scaled by powers of :math:`\sqrt{2}` around ``0.1 * unit.v_cm``:
   ``.SMALL``, ``.SMALl``, ``.SMAll``, ``.SMall``, ``.Small``, ``.small``,
   ``.normal``, ``.large``, ``.Large``, ``.LArge``, ``.LARge``, ``.LARGe``, and
   ``.LARGE``.

.. class:: colorgradient(grad, attrs=[], steps=20)

   Splits the path into *steps* segments of equal arc length and strokes each
   segment with the color sampled from the :class:`color.gradient` *grad*
   merged with *attrs*.

.. class:: brace(reverse=1, stretch=None, dist=None, fillattrs=[], totalheight=12*unit.x_pt, barthickness=0.5*unit.x_pt, innerstrokesthickness=0.25*unit.x_pt, outerstrokesthickness=0.25*unit.x_pt, innerstrokesrelheight=0.6, outerstrokesrelheight=0.7, innerstrokesangle=30, outerstrokesangle=25, slantstrokesangle=5, innerstrokessmoothness=2.0, outerstrokessmoothness=2.5, middlerelpos=0.5)

   Draws a curly brace between the start point and end point of a path (usually
   used with :meth:`canvas.canvas.draw` so the connecting line itself is not
   stroked). Predefined brace instances are ``leftbrace``, ``rightbrace``,
   ``belowbrace``, ``abovebrace``, and ``straightbrace``, and ``brace.clear``
   removes any preceding :class:`brace` decorator.

.. class:: shownormpath(normline_attrs=[], normcurve_attrs=[], endpoint_size=0.05*unit.v_cm, endpoint_attrs=[], controlline_attrs=[], controlpoint_size=0.05*unit.v_cm, controlpoint_attrs=[])

   A diagnostic decorator that visualizes the structure of a normalized path:
   straight segments (:class:`normpath.normline_pt`) are stroked in blue by
   default, cubic Bézier segments (:class:`normpath.normcurve_pt`) in green,
   Bézier control polygons with red dashed lines and filled red control points,
   and segment endpoints with filled black circles. Passing ``None`` for any of
   the ``*_attrs`` arguments disables drawing that element.
