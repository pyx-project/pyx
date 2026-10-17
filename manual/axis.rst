.. module:: graph.axis
   :synopsis: Modular graph axes, ticks, partitioners, texters, painters, and raters

.. _axis:

****
Axes
****

Component Architecture
======================

Axes in PyX convert data values into normalized graph coordinates :math:`v \in [0, 1]`
and render the visual axis elements (baseline, tick marks, grid lines, tick
labels, and axis title). Although most commonly used inside a
:class:`graph.graphxy` or :class:`graph.graphxyz`, axes can also be drawn
standalone along any arbitrary path using :func:`graph.axis.pathaxis`.

Internally, each axis delegates its work to six modular components located in
submodules of :mod:`graph.axis`:

``axis`` (:mod:`graph.axis.axis`)
   Defines the mathematical mapping between data values and normalized graph
   coordinates :math:`[0, 1]`, orchestrates automatic range adjustment, and
   combines the partitioner, texter, painter, and rater to choose the optimal
   tick layout.

   Because an axis instance itself is stateless, a graph wraps each axis in an
   :class:`~graph.axis.axis.anchoredaxis` container that pairs the axis with a
   geometric :class:`~graph.axis.positioner.positioner` and holds per-graph range
   and tick data.

``tick`` (:mod:`graph.axis.tick`)
   Represents individual ticks and subticks placed along an axis, using exact
   rational arithmetic (:class:`~graph.axis.tick.rational`) to avoid
   floating-point rounding artifacts.

``parter`` (:mod:`graph.axis.parter`)
   Short for *partitioner*: generates one or more candidate lists of tick and
   subtick positions for a given data range.

``texter`` (:mod:`graph.axis.texter`)
   Formats numeric or rational tick positions into label strings (using decimal,
   scientific/exponential, or fraction notation).

``painter`` (:mod:`graph.axis.painter`)
   Paints the axis baseline, ticks, grid lines, tick labels, and axis title onto
   an axis canvas.

``rater`` (:mod:`graph.axis.rater`)
   Evaluates candidate tick partitionings by scoring the number of ticks/labels
   and checking the painted label boxes for overlaps or crowding. The candidate
   with the lowest penalty score is selected.

``positioner`` (:mod:`graph.axis.positioner`)
   Defines the geometric curve (straight line or arbitrary path), tick direction,
   and grid paths of an anchored axis on the canvas.

Customizing Axes and Subcomponents via Keyword Splitting
--------------------------------------------------------

Every axis, painter, and texter instance in :mod:`graph.axis` is callable
(implementing ``__call__`` via :func:`utils.merge_members_kwargs`) and supports
underscore-separated keyword forwarding (:func:`utils.kwsplit`). This means you
can customize nested components without verbose boilerplate:

.. code-block:: python

   from pyx import *

   # Equivalent ways to enable grid lines and set a custom label prefix on a linear axis:
   ax1 = graph.axis.linear(min=0, max=10,
                           painter=graph.axis.painter.regular(gridattrs=[color.gray(0.8)]),
                           texter=graph.axis.texter.default(mantissatexter_prefix=r"\$"))

   ax2 = graph.axis.linear(min=0, max=10,
                           painter_gridattrs=[color.gray(0.8)],
                           texter_mantissatexter_prefix=r"\$")


.. module:: graph.axis.axis
   :synopsis: Linear, logarithmic, bar, and split axes

Module :mod:`graph.axis.axis`: Axis Classes
===========================================

All classes in :mod:`graph.axis.axis` are also exposed directly in
:mod:`graph.axis` (e.g. ``graph.axis.linear``, ``graph.axis.log``,
``graph.axis.bar``).

Continuous Regular Axes (:class:`linear` and :class:`logarithmic`)
------------------------------------------------------------------

.. class:: linear(min=None, max=None, reverse=0, divisor=None, title=None, parter=parter.autolinear(), manualticks=[], rater=rater.linear(), maxworse=2, texter=texter.default(), painter=painter.regular(), linkpainter=painter.linked(), fallbackrange=None, **kwargs)

   A linear axis mapping :math:`[\text{min}, \text{max}]` linearly onto
   :math:`[0, 1]`. Also available under the short alias :class:`lin`.

   * *min*, *max*: Fixed lower and upper bounds of the axis. When left as
     ``None``, the bounds are determined automatically from the plotted data and
     extended to the nearest outer tick if allowed by *parter*. If ``min > max``,
     the bounds are swapped and *reverse* is toggled automatically.
   * *reverse*: When true, reverses the direction of the axis so values decrease
     from ``0`` to ``1`` in graph coordinates.
   * *divisor*: Optional number by which all data values are divided before
     partitioning and formatting ticks (for example, ``divisor=math.pi`` paired
     with ``texter=graph.axis.texter.rational(suffix=r"\pi")`` labels ticks in
     multiples of :math:`\pi`).
   * *title*: Axis title string, typeset using the graph's text engine.
   * *parter*: Partitioner instance (default :class:`parter.autolinear`) or
     ``None`` to draw only *manualticks*.
   * *manualticks*: List of :class:`~graph.axis.tick.tick` instances merged with
     the ticks generated by *parter* (manual ticks override automatic ticks at
     identical positions).
   * *rater*, *maxworse*: Rater instance (:class:`rater.linear`) and maximum
     number of consecutively worse partitioning candidates to explore before
     stopping the search in each direction.
   * *texter*: Texter instance (default :class:`texter.default`) used to format
     unlabeled ticks.
   * *painter*: Painter instance (default :class:`painter.regular`) used to draw
     the primary axis.
   * *linkpainter*: Painter instance (default :class:`painter.linked`) used when
     an opposite linked axis (such as ``x2`` or ``y2``) is created automatically.
   * *fallbackrange*: Minimal range width (or ``(min, max)`` tuple) used when the
     plotted data has zero span (for example, a constant function).
   * *\*\*kwargs*: Underscore-split keyword arguments forwarded to ``painter``,
     ``texter``, ``linkpainter``, ``parter``, or ``rater`` (e.g.
     ``painter_gridattrs=...``).

.. class:: lin(...)

   Alias for :class:`linear`.

.. class:: logarithmic(min=None, max=None, reverse=0, divisor=None, title=None, parter=parter.autologarithmic(), linearparter=parter.autolinear(extendtick=None), manualticks=[], maxworse=2, rater=rater.logarithmic(), texter=texter.default(), painter=painter.regular(), linkpainter=painter.linked(), fallbackrange=None, **kwargs)

   A logarithmic axis mapping positive (or negative) values logarithmically onto
   :math:`[0, 1]`. Also available under the short alias :class:`log`.

   All arguments work as in :class:`linear`, with defaults tailored for
   logarithmic scales (:class:`parter.autologarithmic` and
   :class:`rater.logarithmic`). If the data spans such a narrow interval that no
   valid logarithmic partitioning without overlapping labels can be found, the
   axis logs a warning and automatically falls back to *linearparter* (unless
   ``linearparter=None``).

.. class:: log(...)

   Alias for :class:`logarithmic`.

Discrete and Segmented Axes (:class:`bar`, :class:`nestedbar`, and :class:`split`)
----------------------------------------------------------------------------------

.. class:: bar(subaxes=None, defaultsubaxis=linear(painter=None, linkpainter=None, parter=None), dist=0.5, firstdist=None, lastdist=None, title=None, reverse=0, epsilon=1e-10, painter=painter.bar(), linkpainter=painter.linkedbar(), **kwargs)

   Discrete categorical axis for bar charts (:class:`graph.style.bar`). A bar
   axis maps a 2-tuple ``(name, subvalue)`` to a normalized graph coordinate:

   * ``name`` selects one of the discrete categories along the bar axis (ordered
     by their appearance in the data, or reversed when ``reverse=1``).
   * ``subvalue`` is converted by the subaxis associated with ``name`` and mapped
     into the sub-interval of :math:`[0, 1]` allocated to that category.

   * *subaxes*: Optional dictionary or sequence mapping category names to explicit
     subaxis instances; any category not in *subaxes* uses a copy of
     *defaultsubaxis*.
   * *dist*, *firstdist*, *lastdist*: Spacing between consecutive category
     intervals, before the first category, and after the last category, measured
     relative to a unit subaxis size of ``1`` (default ``dist=0.5``, with
     *firstdist* and *lastdist* defaulting to ``0.5 * dist``).
   * *\*\*kwargs*: Underscore-split keyword arguments forwarded to
     ``defaultsubaxis``, ``painter``, or ``linkpainter``.

.. class:: nestedbar(subaxes=None, defaultsubaxis=bar(dist=0, painter=None, linkpainter=None), dist=0.5, firstdist=None, lastdist=None, title=None, reverse=0, painter=painter.bar(), linkpainter=painter.linkedbar(), **kwargs)

   A two-level hierarchical bar axis for grouped side-by-side bar charts, where
   *defaultsubaxis* is itself a :class:`bar` axis with ``dist=0``. Data values
   passed to a :class:`nestedbar` axis have the nested tuple form
   ``((category, subcategory), subvalue)``.

.. class:: split(subaxes=None, defaultsubaxis=linear(), dist=0.5, firstdist=0, lastdist=0, title=None, reverse=0, painter=painter.split(), linkpainter=painter.linkedsplit(), **kwargs)

   A segmented continuous axis divided into multiple continuous sub-ranges
   separated by visual break markers (painted by :class:`painter.split`). Data
   values can be routed to subaxes automatically using
   :func:`graph.data.splitatvalue`.

.. class:: sizedlinear(size=1, **kwargs)
.. class:: autosizedlinear(**kwargs)

   Subclasses of :class:`linear` (also aliased as :class:`sizedlin` and
   :class:`autosizedlin`) for use as subaxes in a :class:`bar` or :class:`split`
   axis. :class:`sizedlinear` assigns a fixed relative width *size* to the
   subaxis, whereas :class:`autosizedlinear` scales the width of each subaxis
   proportionally to its data span ``max - min``.

Anchored, Linked, and Standalone Path Axes
------------------------------------------

.. class:: anchoredaxis(axis, textengine, errorname)

   Combines an :class:`_axis` instance with a :class:`positioner.positioner` and
   per-graph storage (``self.data`` and ``self.canvas``). Graph instances store
   their anchored axes in ``g.axes[name]``. Once the axis layout has been
   created, :class:`anchoredaxis` provides the following geometric methods:

   .. method:: basepath(x1=None, x2=None)
   .. method:: vbasepath(v1=None, v2=None)

      Returns a :class:`path.path` along the axis baseline between data values
      *x1* and *x2* (or graph coordinates *v1* and *v2*).

   .. method:: gridpath(x)
   .. method:: vgridpath(v)

      Returns the grid line :class:`path.path` across the graph at data value *x*
      (or graph coordinate *v*), or ``None`` if no grid path is defined.

   .. method:: tickpoint(x)
   .. method:: tickpoint_pt(x)
   .. method:: vtickpoint(v)
   .. method:: vtickpoint_pt(v)

      Returns the canvas coordinates ``(x, y)`` of the point on the axis baseline
      corresponding to data value *x* (or graph coordinate *v*).

   .. method:: tickdirection(x)
   .. method:: vtickdirection(v)

      Returns the unit normal vector ``(dx, dy)`` pointing toward the interior of
      the graph at data value *x* (or graph coordinate *v*).

.. class:: linkedaxis(linkedaxis=None, errorname="manual-linked", painter=_marker, **kwargs)

   An anchored axis that shares the data range, scaling, and tick positions of
   another :class:`anchoredaxis` instance *linkedaxis* (for example, to link an
   axis in one graph to the axis of an adjacent graph in a multi-panel figure).

   .. method:: setlinkedaxis(linkedaxis)

      Binds or updates the target *linkedaxis* after construction.

.. class:: anchoredpathaxis(path, axis, textengine=text.defaulttextengine, direction=1)
.. function:: pathaxis(path, axis, **kwargs)

   Creates and paints a standalone *axis* (which must have explicit *min* and
   *max* bounds) along an arbitrary geometric :class:`path.path`. *direction*
   specifies whether ticks point to the left (``1``, default) or right (``-1``)
   of the path tangent. :func:`pathaxis` immediately builds the axis and returns
   its painted :class:`canvas.canvas` so it can be inserted directly into any
   canvas:

   .. code-block:: python

      c = canvas.canvas()
      c.insert(graph.axis.pathaxis(path.curve(0, 0, 2, 2, 4, -2, 6, 0),
                                   graph.axis.linear(min=0, max=10)))


.. module:: graph.axis.timeaxis
   :synopsis: Axes for Python datetime data

Module :mod:`graph.axis.timeaxis`: Date and Time Axes
=====================================================

The :mod:`graph.axis.timeaxis` module provides classes for plotting Python
:class:`datetime.datetime` (or :class:`datetime.date`) objects along a
continuous axis:

.. class:: timeaxis(min=None, max=None, reverse=0, divisor=None, title=None, parter=timeparter(), manualticks=[], rater=rater.linear(), maxworse=2, texter=timetexter(), painter=painter.regular(), linkpainter=painter.linked(), fallbackrange=None, **kwargs)

   A continuous axis whose data bounds and values are Python
   :class:`datetime.datetime` instances.

.. class:: timetick(dt, ticklevel=0, labellevel=0, label=None, labelattrs=[])

   A tick positioned at a :class:`datetime.datetime` value (or initialized from
   ``(year, month, day[, hour[, minute[, second]]])`` positional arguments).

.. class:: timeparter(variants=defaultvariants)

   Partitioner that places ticks and subticks at calendar-aligned intervals (days,
   weeks, months, hours, etc.).

.. class:: timetexter(format="%Y-%m-%d")

   Formats :class:`timetick` positions using :meth:`datetime.datetime.strftime`
   with the given *format* string.


.. module:: graph.axis.tick
   :synopsis: Rational numbers and axis ticks

Module :mod:`graph.axis.tick`: Axis Ticks
=========================================

.. class:: rational(x, power=1, floatprecision=10)

   Exact rational number ``num / denom`` used internally by partitioners and
   texters to avoid floating-point rounding errors. *x* can be:

   * A ``float`` (converted using precision *floatprecision*),
   * A decimal or fraction string (such as ``"0.25"`` or ``"1/3"``),
   * A 2-tuple of integers ``(num, denom)``, or
   * Any object with ``.num`` and ``.denom`` integer attributes (or a Python
     :class:`fractions.Fraction`).

   If *power* is given, the rational number is raised to the integer exponent
   *power*.

.. class:: tick(x, ticklevel=0, labellevel=0, label=None, labelattrs=[], power=1, floatprecision=10)

   Represents a tick mark and/or label at position *x* (interpreted as a
   :class:`rational`). Instances of :class:`tick` can be passed to the
   ``manualticks`` list of any regular axis:

   .. code-block:: python

      ax = graph.axis.linear(min=0, max=4,
                             manualticks=[graph.axis.tick.tick(math.pi, label=r"$\pi$")])

   * *ticklevel*: Non-negative integer specifying the tick hierarchy level
     (``0`` for a major tick, ``1`` for a subtick, ``2`` for a sub-subtick, etc.),
     or ``None`` to draw no tick mark at this position.
   * *labellevel*: Non-negative integer specifying the label hierarchy level
     (``0`` for a major label, ``1`` for a sublabel, etc.), or ``None`` to omit
     the label at this position.
   * *label*: Explicit label string, or ``None`` to let the axis's :mod:`~graph.axis.texter`
     generate the label automatically.
   * *labelattrs*: Additional text attributes applied to this specific tick's
     label.


.. module:: graph.axis.parter
   :synopsis: Automatic and manual axis partitioners

Module :mod:`graph.axis.parter`: Axis Partitioners
==================================================

Partitioners generate candidate lists of :class:`~graph.axis.tick.tick` instances
for a given axis range.

Linear Partitioners
-------------------

.. class:: linear(tickdists=None, labeldists=None, extendtick=0, extendlabel=None, epsilon=1e-10)
.. class:: lin(...)

   Places ticks at fixed equidistant intervals specified in *tickdists* (a list
   of intervals ``[major_step, subtick_step, ...]``, where each step can be a
   number, string, or :class:`~graph.axis.tick.rational`).

   * *labeldists*: Optional list of step sizes for labeled ticks. When ``None``
     (default), labels are placed at major ticks (level ``0``) only.
   * *extendtick*, *extendlabel*: Tick or label level (default ``0`` for
     *extendtick*, ``None`` for *extendlabel*) to which an auto-ranged axis is
     expanded if the data exceeds the outermost tick by more than *epsilon*.

.. class:: autolinear(variants=defaultvariants, extendtick=0, epsilon=1e-10)
.. class:: autolin(...)

   Automatically generates candidate :class:`linear` partitionings by scaling the
   base step patterns in *variants* by powers of 10 to match the data span.

   .. attribute:: autolinear.defaultvariants

      ``[[1, 1/2], [2, 1], [5/2, 5/4], [5, 5/2]]`` (represented as
      :class:`~graph.axis.tick.rational` pairs of ``[tick_step, subtick_step]``).

Logarithmic Partitioners
------------------------

.. class:: preexp(pres, exp)

   Specifies a repeating sequence of logarithmic tick positions of the form
   :math:`p_i \cdot \text{exp}^n` for all integers :math:`n` and prefixes
   :math:`p_i \in \text{pres}`.

.. class:: logarithmic(tickpreexps=None, labelpreexps=None, extendtick=0, extendlabel=None, epsilon=1e-10)
.. class:: log(...)

   Places ticks on a logarithmic axis according to the list of :class:`preexp`
   instances in *tickpreexps* (for ticks, subticks, …) and *labelpreexps* (for
   labels, sublabels, …).

   Predefined :class:`preexp` constants on :class:`logarithmic`:

   * :attr:`logarithmic.pre1exp` — powers of 10 (:math:`10^n`)
   * :attr:`logarithmic.pre125exp` — :math:`1, 2, 5 \times 10^n`
   * :attr:`logarithmic.pre1to9exp` — :math:`1, 2, \dots, 9 \times 10^n`
   * :attr:`logarithmic.pre1exp2`, :attr:`~logarithmic.pre1exp3`,
     :attr:`~logarithmic.pre1exp4`, :attr:`~logarithmic.pre1exp5` — steps of
     :math:`10^{2n}`, :math:`10^{3n}`, :math:`10^{4n}`, :math:`10^{5n}`

.. class:: autologarithmic(variants=defaultvariants, extendtick=0, extendlabel=None, epsilon=1e-10)
.. class:: autolog(...)

   Evaluates candidate logarithmic tick and label patterns from *variants* (ordered
   from densest to sparsest) for rating by the axis rater.


.. module:: graph.axis.texter
   :synopsis: Tick label formatters

Module :mod:`graph.axis.texter`: Axis Texters
=============================================

Texters format the numeric value of each :class:`~graph.axis.tick.tick` whose
``labellevel`` is not ``None`` and whose ``label`` is not already set manually.
All texters are callable so you can clone and tweak them via keyword arguments.

.. class:: default(multiplicationtex=r"\cdot{}", multiplicationunicode="·", base=Fraction(10), skipmantissaunity=skipmantissaunity.all, minusunity="-", minexponent=4, minnegexponent=None, uniformexponent=True, mantissatexter=decimal(), basetexter=decimal(), exponenttexter=decimal(), labelattrs=[text.mathmode], **kwargs)

   The default texter for linear and logarithmic axes. Formats moderate numbers
   in plain decimal notation and automatically switches to scientific notation
   (:math:`m \cdot 10^e`) for large or small exponents, producing a
   :class:`text.MultiEngineText` that works seamlessly with both TeX/LaTeX
   engines and :class:`text.UnicodeEngine`.

   * *multiplicationtex*, *multiplicationunicode*: Multiplication symbol placed
     between the mantissa and base for TeX engines and :class:`text.UnicodeEngine`,
     respectively.
   * *base*: Exponent base (default ``Fraction(10)``).
   * *skipmantissaunity*: Controls when a mantissa of ``1`` is omitted (so
     :math:`1 \cdot 10^5` is written simply as :math:`10^5`):

     - :attr:`skipmantissaunity.never` (``0``): Always write :math:`1 \cdot 10^e`.
     - :attr:`skipmantissaunity.each` (``1``): Omit ``1`` on any individual tick
       whose mantissa is unity.
     - :attr:`skipmantissaunity.all` (``2``, default): Omit ``1`` only when *all*
       exponentially formatted ticks on the axis have a mantissa of unity (as on
       a standard logarithmic axis).

   * *minexponent*, *minnegexponent*: Minimum positive exponent (default ``4``,
     i.e. :math:`10^4`) and minimum negative exponent magnitude (defaults to
     *minexponent*, i.e. :math:`10^{-4}`) at which exponential notation is used.
   * *uniformexponent*: When ``True`` (default), if any non-zero tick on the axis
     triggers exponential notation, all non-zero ticks on the axis are formatted
     in exponential notation for visual consistency.
   * *mantissatexter*, *basetexter*, *exponenttexter*: :class:`decimal` texters
     used to format the mantissa, base, and exponent (can also be configured via
     underscore-split keywords such as ``mantissatexter_equalprecision=True``).
   * *labelattrs*: Text attributes added to each formatted tick (default
     ``[text.mathmode]``).

.. class:: decimal(prefix="", infix="", suffix="", equalprecision=False, decimalsep=".", thousandsep="", thousandthpartsep="", plus="", minus="-", period=r"\overline{%s}", labelattrs=[text.mathmode])

   Formats ticks in fixed-point decimal notation.

   * *prefix*, *infix*, *suffix*: Strings inserted before the sign, immediately
     after the sign, and at the end of the number, respectively.
   * *equalprecision*: When ``True``, pads all decimal tick labels on the axis
     with trailing zeros to match the tick with the most decimal places.
   * *decimalsep*, *thousandsep*, *thousandthpartsep*: Separators for the decimal
     point and 3-digit groups in the integer and fractional parts.
   * *plus*, *minus*: Sign strings for non-negative and negative values.
   * *period*: Format string with a single ``%s`` placeholder used to render
     repeating decimal periods (default ``r"\overline{%s}"``).

.. class:: rational(prefix="", infix="", suffix="", numprefix="", numinfix="", numsuffix="", denomprefix="", denominfix="", denomsuffix="", plus="", minus="-", minuspos=0, over=r"{{%s}\over{%s}}", equaldenom=False, skip1=True, skipnum0=True, skipnum1=True, skipdenom1=True, labelattrs=[text.mathmode])

   Formats ticks as exact reduced fractions :math:`\frac{a}{b}` (especially
   useful for axes partitioned in multiples of :math:`\pi` or rational fractions).

   * *prefix*, *infix*, *suffix*: Strings placed around the entire fraction.
   * *numprefix*, *numinfix*, *numsuffix*: Strings placed around the numerator
     (for example, ``numsuffix=r"\pi"``).
   * *denomprefix*, *denominfix*, *denomsuffix*: Strings placed around the
     denominator.
   * *minuspos*: Placement of the sign: ``0`` (in front of the fraction), ``1``
     (in the numerator), or ``-1`` (in the denominator).
   * *over*: Format string with two ``%s`` placeholders for numerator and
     denominator (default ``r"{{%s}\over{%s}}"``; use ``r"{{%s}/{%s}}"`` for
     inline slash fractions).
   * *equaldenom*: When ``True``, expresses all fractions on the axis over their
     least common denominator instead of reducing each fraction individually.
   * *skip1*, *skipnum0*, *skipnum1*, *skipdenom1*: Booleans controlling automatic
     simplification when the fraction is :math:`\pm 1`, the numerator is ``0`` or
     :math:`\pm 1`, or the denominator is ``1``.


.. module:: graph.axis.painter
   :synopsis: Axis painters

Module :mod:`graph.axis.painter`: Axis Painters
===============================================

Painters draw the visual representation of an axis onto an :class:`axiscanvas`.

Helper Classes (:class:`rotatetext` and :class:`ticklength`)
------------------------------------------------------------

.. class:: rotatetext(direction, epsilon=1e-10)

   Computes a :class:`trafo.rotate` transformation for axis labels or titles
   at angle *direction* (in degrees) relative to the inward tick direction,
   automatically flipping the text by 180° whenever it would otherwise appear
   upside-down.

   .. attribute:: rotatetext.parallel

      ``rotatetext(90)`` — orients text parallel to the axis baseline.

   .. attribute:: rotatetext.orthogonal

      ``rotatetext(180)`` — orients text perpendicular to the axis baseline.

.. class:: ticklength(initial, factor)

   A changeable attribute (:class:`attr.changeattr`) that generates a geometric
   progression of visual lengths :math:`\text{initial} \cdot \text{factor}^k` for
   major ticks (:math:`k = 0`), subticks (:math:`k = 1`), sub-subticks
   (:math:`k = 2`), etc.

   Predefined instances with ``factor = 1 / goldenmean`` and base length
   ``0.12 * unit.v_cm`` scaled by powers of :math:`\sqrt{2}` are provided as
   class attributes: ``ticklength.SHORT``, ``ticklength.SHORt``,
   ``ticklength.SHOrt``, ``ticklength.SHort``, ``ticklength.Short``,
   ``ticklength.short``, ``ticklength.normal``, ``ticklength.long``,
   ``ticklength.Long``, ``ticklength.LOng``, ``ticklength.LONg``, and
   ``ticklength.LONG``.

Painter Classes
---------------

.. class:: regular(innerticklength=ticklength.normal, outerticklength=None, tickattrs=[], gridattrs=None, basepathattrs=[], labeldist=0.3*unit.v_cm, labelattrs=[], labeldirection=None, labelhequalize=0, labelvequalize=1, titledist=0.3*unit.v_cm, titleattrs=[], titledirection=rotatetext.parallel, titlepos=0.5, textengine=None)

   Default painter for continuous axes (:class:`~graph.axis.axis.linear`,
   :class:`~graph.axis.axis.logarithmic`, :class:`~graph.axis.timeaxis.timeaxis`).

   * *innerticklength*, *outerticklength*: Visual length (or changeable
     :class:`ticklength`) of ticks pointing inside and outside the graph, or
     ``None`` to omit inner or outer ticks.
   * *tickattrs*: Stroke attributes for ticks (supports changeable attributes to
     style major ticks and subticks differently), or ``None`` to suppress ticks.
   * *gridattrs*: Stroke attributes for grid lines across the graph (for example,
     ``[color.gray(0.8)]`` or
     ``[attr.changelist([style.linestyle.solid, style.linestyle.dotted])]``), or
     ``None`` (default) to disable grid lines.
   * *basepathattrs*: Stroke attributes for the axis baseline (merged with
     ``[style.linecap.square]``), or ``None`` to omit the baseline.
   * *labeldist*: Visual distance between the axis baseline (or outer ticks) and
     the tick labels (default ``0.3 * unit.v_cm``).
   * *labelattrs*: Text attributes for tick labels (merged with
     ``[text.halign.center, text.vshift.mathaxis]``), or ``None`` to suppress
     tick labels.
   * *labeldirection*: Optional :class:`rotatetext` instance to rotate tick
     labels relative to the axis.
   * *labelhequalize*, *labelvequalize*: Aligns all tick labels along a common
     horizontal or vertical line on straight vertical or horizontal axes.
   * *titledist*, *titleattrs*, *titledirection*, *titlepos*: Distance, text
     attributes (or ``None`` to hide), rotation (:attr:`rotatetext.parallel` by
     default), and normalized position (:math:`0.5` = centered) of the axis
     title.
   * *textengine*: Optional text engine override (defaults to the graph's text
     engine).

.. class:: linked(innerticklength=ticklength.short, outerticklength=None, tickattrs=[], gridattrs=None, basepathattrs=[], labeldist=0.3*unit.v_cm, labelattrs=None, labeldirection=None, labelhequalize=0, labelvequalize=1, titledist=0.3*unit.v_cm, titleattrs=None, titledirection=rotatetext.parallel, titlepos=0.5, textengine=None)

   Subclass of :class:`regular` used by default for opposite linked axes
   (``x2``, ``y2``), with ``innerticklength=ticklength.short`` and labels and
   titles disabled (``labelattrs=None, titleattrs=None``).

.. class:: bar(innerticklength=None, outerticklength=None, tickattrs=[], basepathattrs=[], namedist=0.3*unit.v_cm, nameattrs=[], namedirection=None, namepos=0.5, namehequalize=0, namevequalize=1, titledist=0.3*unit.v_cm, titleattrs=[], titledirection=rotatetext.parallel, titlepos=0.5, textengine=None)
.. class:: linkedbar(...)

   Painters for :class:`~graph.axis.axis.bar` and
   :class:`~graph.axis.axis.nestedbar` axes. The ``name*`` parameters control the
   placement and formatting of the categorical bar labels, while
   *innerticklength* and *outerticklength* optionally mark the boundaries of each
   bar subaxis. :class:`linkedbar` disables category names and the axis title by
   default.

.. class:: split(breaklinesdist=0.05*unit.v_cm, breaklineslength=0.5*unit.v_cm, breaklinesangle=-60, titledist=0.3*unit.v_cm, titleattrs=[], titledirection=rotatetext.parallel, titlepos=0.5, textengine=None)
.. class:: linkedsplit(...)

   Painters for :class:`~graph.axis.axis.split` axes, drawing parallel break
   slashes separated by *breaklinesdist* of length *breaklineslength* at angle
   *breaklinesangle* (in degrees) between adjacent subaxes.


.. module:: graph.axis.rater
   :synopsis: Rating of candidate axis partitionings

Module :mod:`graph.axis.rater`: Axis Raters
===========================================

When an automatic partitioner (:class:`~graph.axis.parter.autolinear` or
:class:`~graph.axis.parter.autologarithmic`) produces multiple candidate tick
lists, an axis :class:`rater` assigns a non-negative penalty score to each
candidate (where smaller scores are better):

1. **Tick count and range rating**: Scores the number of ticks, subticks, and
   labels against target optima (:class:`cube`) and penalizes excessive range
   expansion beyond the data bounds.
2. **Label layout rating**: For the top-ranked candidates, paints the axis and
   checks the spacing between adjacent label boxes (:class:`distance`). Any
   candidate whose labels overlap is rejected completely.

.. class:: cube(opt, left=None, right=None, weight=1)

   Cubic penalty function :math:`\text{weight} \cdot ((x - \text{opt}) / (\text{other} - \text{opt}))^3`
   evaluating how far a count :math:`x` deviates from the optimal value *opt*,
   where *other* is *left* (default ``0``) for :math:`x < \text{opt}` and *right*
   (default ``3 * opt``) for :math:`x > \text{opt}`.

.. class:: distance(opt=1*unit.v_cm, weight=0.1)

   Rates the visual separation between adjacent tick label boxes against the
   optimal separation *opt* (rejecting negative separations where labels overlap).

.. class:: rater(ticks, labels, range, distance=distance(1*unit.v_cm), density=1)

   Combines lists of :class:`cube` raters for *ticks* and *labels* at each hierarchy
   level, a :class:`cube` rater for *range* extension, and a :class:`distance`
   rater for label spacing. Increasing *density* (e.g. ``density=1.5`` or ``2``)
   scales the optimal tick and label counts upward to favor denser ticks;
   decreasing *density* (e.g. ``density=0.7``) favors fewer ticks.

.. class:: linear(ticks=[cube(4), cube(10, weight=0.5)], labels=[cube(4)], range=cube(1, weight=2), **kwargs)
.. class:: lin(...)

   Default rater for linear axes.

.. class:: logarithmic(ticks=[cube(5, right=20), cube(20, right=100, weight=0.5)], labels=[cube(5, right=20), cube(5, right=20, weight=0.5)], range=cube(1, weight=2), **kwargs)
.. class:: log(...)

   Default rater for logarithmic axes.


.. module:: graph.axis.positioner
   :synopsis: Geometric positioning of axes

Module :mod:`graph.axis.positioner`: Axis Positioners
=====================================================

Positioner instances define the geometric placement of an axis on a canvas and
are created automatically by :class:`graph.graphxy`, :class:`graph.graphxyz`,
and :func:`graph.axis.pathaxis`. Every positioner implements the following
interface:

.. class:: _positioner()

   .. method:: vbasepath(v1=None, v2=None)

      Returns the :class:`path.path` of the axis baseline between normalized
      graph coordinates *v1* and *v2*.

   .. method:: vgridpath(v)

      Returns the grid line :class:`path.path` at normalized coordinate *v*, or
      ``None`` if no grid is defined.

   .. method:: vtickpoint_pt(v)

      Returns ``(x_pt, y_pt)`` in PostScript points on the baseline at normalized
      coordinate *v*.

   .. method:: vtickdirection(v)

      Returns the unit normal vector ``(dx, dy)`` pointing toward the graph
      interior at normalized coordinate *v*.
