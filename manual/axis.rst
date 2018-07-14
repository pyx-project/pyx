
.. module:: graph.axis

****
Axes
****


Component architecture
======================

Axes are a fundamental component of graphs although there might be applications
outside of the graph system. Internally axes are constructed out of components,
which handle different tasks axes need to fulfill:

axis
   Implements the conversion of a data value to a graph coordinate of range [0:1].
   It does also handle the proper usage of the components in complicated tasks
   (*i.e.* combine the partitioner, texter, painter and rater to find the best
   partitioning).

   An anchoredaxis is a container to combine an axis with an positioner and provide
   a storage area for all kind of axis data. That way axis instances are reusable
   (they do not store any data locally). The anchoredaxis and the positioner are
   created by a graph corresponding to its geometry.

tick
   Ticks are plotted along the axis. They might be labeled with text as well.

partitioner, we use "parter" as a short form
   Creates one or several choices of tick lists suitable to a certain axis range.

texter
   Creates labels for ticks when they are not set manually.

painter
   Responsible for painting the axis.

rater
   Calculate ratings, which can be used to select the best suitable partitioning.

positioner
   Defines the position of an axis.

The names above map directly to modules which are provided in the directory
:file:`graph/axis` except for the anchoredaxis, which is part of the axis module
as well. Sometimes it might be convenient to import the axis directory directly
rather than to access iit through the graph. This would look like::

   from pyx import *
   graph.axis.painter() # and the like

   from pyx.graph import axis
   axis.painter() # this is shorter ...

In most cases different implementations are available through different classes,
which can be combined in various ways. There are various axis examples
distributed with PyX, where you can see some of the features of the axis with a
few lines of code each. Hence we can here directly come to the reference of the
available components.


.. module:: graph.axis.axis

Module :mod:`graph.axis.axis`: Axes
===================================

The following classes are part of the module :mod:`graph.axis.axis`. However,
there is a shortcut to access those classes via ``graph.axis`` directly.

Instances of the following classes can be passed to the *\*\*axes* keyword
arguments of a graph. Those instances should only be used once.


.. class:: linear(min=None, max=None, reverse=0, divisor=None, title=None, parter=parter.autolinear(), manualticks=[], density=1, maxworse=2, rater=rater.linear(), texter=texter.mixed(), painter=painter.regular(), linkpainter=painter.linked(), fallbackrange=None)

   This class provides a linear axis. *min* and *max* define the axis range. When
   not set, they are adjusted automatically by the data to be plotted in the graph.
   Note, that some data might want to access the range of an axis (*e.g.* the
   :class:`function` class when no range was provided there) or you need to specify
   a range when using the axis without plugging it into a graph (*e.g.* when
   drawing an axis along a path). In cases where the data provides a range of zero
   (e.g. a when plotting a constant function), then a *fallbackrange* can be set to
   guarantee a minimal range of the axis.

   *reverse* can be set to indicate a reversed axis starting with bigger values
   first. Alternatively you can fix the axis range by *min* and *max* accordingly.
   When divisor is set, it is taken to divide all data range and position
   informations while creating ticks. You can create ticks not taking into account
   a factor by that. *title* is the title of the axis.

   *parter* is a partitioner instance, which creates suitable ticks for the axis
   range. Those ticks are merged with ticks manually given  by *manualticks* before
   proceeding with rating, painting *etc.* Manually placed ticks win against those
   created by the partitioner. For automatic partitioners, which are able to
   calculate several possible tick lists for a given axis range, the *density* is a
   (linear) factor to favour more or less ticks. It should not be stressed to much
   (its likely, that the result would be unappropriate or not at all valid in terms
   of rating label distances). But within a range of say 0.5 to 2 (even bigger for
   large graphs) it can help to get less or more ticks than the default would lead
   to. *maxworse* is the number of trials with more and less ticks when a better
   rating was already found. *rater* is a rater instance, which rates the ticks and
   the label distances for being best suitable. It also takes into account
   *density*. The rater is only needed, when the partitioner creates several tick
   lists.

   *texter* is a texter instance. It creates labels for those ticks, which claim to
   have a label, but do not have a label string set already. Ticks created by
   partitioners typically receive their label strings by texters. The *painter* is
   finally used to construct the output. Note, that usually several output
   constructions are needed, since the rater is also used to rate the distances
   between the labels for an optimum. The *linkedpainter* is used as the axis
   painter, when automatic link axes are created by the :meth:`createlinked`
   method.


.. class:: lin(...)

   This class is an abbreviation of :class:`linear` described above.


.. class:: logarithmic(min=None, max=None, reverse=0, divisor=None, title=None, parter=parter.autologarithmic(), manualticks=[], density=1, maxworse=2, rater=rater.logarithmic(), texter=texter.mixed(), painter=painter.regular(), linkpainter=painter.linked(), fallbackrange=None)

   This class provides a logarithmic axis. All parameters work like
   :class:`linear`. Only two parameters have a different default: *parter* and
   *rater*. Furthermore and most importantly, the mapping between data and graph
   coordinates is logarithmic.


.. class:: log(...)

   This class is an abbreviation of :class:`logarithmic` described above.


.. class:: bar(subaxes=None, defaultsubaxis=linear(painter=None, linkpainter=None, parter=None, texter=None), dist=0.5, firstdist=None, lastdist=None, title=None, reverse=0, painter=painter.bar(), linkpainter=painter.linkedbar())

   This class provides an axis suitable for a bar style. It handles a discrete set
   of values and maps them to distinct ranges in graph coordinates. For that, the
   axis gets a tuple of two values.

   The first item is taken to be one of the discrete values valid on this axis. The
   discrete values can be any hashable type and the order of the subaxes is defined
   by the order the data is received or the inverse of that when *reverse* is set.

   The second item is passed to the corresponding subaxis. The result of the
   conversion done by the subaxis is mapped to the graph coordinate range reserved
   for this subaxis. This range is defined by a size attribute of the subaxis,
   which can be added to any axis. (see the sized linear axes described below for
   some axes already having a size argument). When no size information is available
   for a subaxis, a size value of 1 is used. The baraxis itself calculates its size
   by suming up the sizes of its subaxes plus *firstdist*, *lastdist* and *dist*
   times the number of subaxes minus 1.

   *subaxes* should be a list or a dictionary mapping a discrete value of the bar
   axis to the corresponding subaxis. When no subaxes are set or data is received
   for an unknown discrete axis value, instances of defaultsubaxis are used as the
   subaxis for this discrete value.

   *dist* is used as the spacing between the ranges for each distinct value. It is
   measured in the same units as the subaxis results, thus the default value of
   ``0.5`` means half the width between the distinct values as the width for each
   distinct value. *firstdist* and *lastdist* are used before the first and after
   the last value. When set to ``None``, half of *dist* is used.

   *title* is the title of the split axes and *painter* is a specialized painter
   for an bar axis and *linkpainter* is used as the painter, when automatic link
   axes are created by the :meth:`createlinked` method.


.. class:: nestedbar(subaxes=None, defaultsubaxis=bar(dist=0, painter=None, linkpainter=None), dist=0.5, firstdist=None, lastdist=None, title=None, reverse=0, painter=painter.bar(), linkpainter=painter.linkedbar())

   This class is identical to the bar axis except for the different default value
   for defaultsubaxis.


.. class:: split(subaxes=None, defaultsubaxis=linear(), dist=0.5, firstdist=0, lastdist=0, title=None, reverse=0, painter=painter.split(), linkpainter=painter.linkedsplit())

   This class is identical to the bar axis except for the different default value
   for defaultsubaxis, firstdist, lastdist, painter, and linkedpainter.

Sometimes you want to alter the default size of 1 of the subaxes. For that you
have to add a size attribute to the axis data. The two classes
:class:`sizedlinear` and :class:`autosizedlinear` do that for linear axes. Their
short names are :class:`sizedlin` and :class:`autosizedlin`.
:class:`sizedlinear` extends the usual linear axis by an first argument *size*.
:class:`autosizedlinear` creates the size out of its data range automatically
but sets an :class:`autolinear` parter with *extendtick* being ``None`` in order
to disable automatic range modifications while painting the axis.

The :mod:`axis` module also contains classes implementing so called anchored
axes, which combine an axis with an positioner and a storage place for axis
related data. Since these features are not interesting for the average PyX user,
we'll not go into all the details of their parameters and except for some handy
axis position methods:


.. class:: anchoredaxis()

.. method:: anchoredaxis.basepath(x1=None, x2=None)

   Returns a path instance for the base path. *x1* and *x2* define the axis range,
   the base path should cover. For ``None`` the beginning and end of the path is
   taken, which might cover a longer range, when the axis is embedded as a subaxis.
   For that case, a ``None`` value extends the range to the point of the middle
   between two subaxes or the beginning or end of the whole axis, when the subaxis
   is the first or last of the subaxes.


.. method:: anchoredaxis.vbasepath(v1=None, v2=None)

   Like :meth:`basepath` but in graph coordinates.


.. method:: anchoredaxis.gridpath(x)

   Returns a path instance for the grid path at position *x*. Might return ``None``
   when no grid path is available.


.. method:: anchoredaxis.vgridpath(v)

   Like :meth:`gridpath` but in graph coordinates.


.. method:: anchoredaxis.tickpoint(x)

   Returns the position of *x* as a tuple ``(x, y)``.


.. method:: anchoredaxis.vtickpoint(v)

   Like :meth:`tickpoint` but in graph coordinates.


.. method:: anchoredaxis.tickdirection(x)

   Returns the direction of a tick at *x* as a tuple ``(dx, dy)``. The tick
   direction points inside of the graph.


.. method:: anchoredaxis.vtickdirection(v)

   Like :meth:`tickdirection` but in graph coordinates.


.. method:: anchoredaxis.vtickdirection(v)

   Like :meth:`tickdirection` but in graph coordinates.

However, there are two anchored axes implementations :class:`linkedaxis` and
:class:`anchoredpathaxis` which are available to the user to create special
forms of anchored axes.


.. class:: linkedaxis(linkedaxis=None, errorname="manual-linked", painter=_marker)

   This class implements an anchored axis to be passed to a graph constructor to
   manually link the axis to another anchored axis instance *linkedaxis*. Note that
   you can skip setting the value of *linkedaxis* in the constructor, but set it
   later on by the :meth:`setlinkedaxis` method described below. *errorname* is
   printed within error messages when the data is used and some problem occurs.
   *painter* is used for painting the linked axis instead of the *linkedpainter*
   provided by the *linkedaxis*.


.. method:: linkedaxis.setlinkedaxis(linkedaxis)

   This method can be used to set the *linkedaxis* after constructing the axis. By
   that you can create several graph instances with cycled linked axes.


.. class:: anchoredpathaxis(path, axis, direction=1)

   This class implements an anchored axis the path *path*. *direction* defines the
   direction of the ticks. Allowed values are ``1`` (left) and ``-1`` (right).

The :class:`anchoredpathaxis` contains as any anchored axis after calling its
:meth:`create` method the painted axis in the :attr:`canvas` member attribute.
The function :func:`pathaxis` has the same signature like the
:class:`anchoredpathaxis` class, but immediately creates the axis and returns
the painted axis.


.. module:: graph.axis.tick

Module :mod:`graph.axis.tick`: Axes ticks
=========================================

The following classes are part of the module :mod:`graph.axis.tick`.


.. class:: rational(x, power=1, floatprecision=10)

   This class implements a rational number with infinite precision. For that it
   stores two integers, the numerator ``num`` and a denominator ``denom``. Note
   that the implementation of rational number arithmetics is not at all complete
   and designed for its special use case of axis partitioning in PyX preventing any
   roundoff errors.

   *x* is the value of the rational created by a conversion from one of the
   following input values:

* A float. It is converted to a rational with finite precision determined by
     *floatprecision*.

* A string, which is parsed to a rational number with full precision. It is also
     allowed to provide a fraction like ``"1/3"``.

* A sequence of two integers. Those integers are taken as numerator and
     denominator of the rational.

* An instance defining instance variables ``num`` and ``denom`` like
     :class:`rational` itself.

   *power* is an integer to calculate ``x**power``. This is useful at certain
   places in partitioners.


.. class:: tick(x, ticklevel=0, labellevel=0, label=None, labelattrs=[], power=1, floatprecision=10)

   This class implements ticks based on rational numbers. Instances of this class
   can be passed to the ``manualticks`` parameter of a regular axis.

   The parameters *x*, *power*, and *floatprecision* share its meaning with
   :class:`rational`.

   A tick has a tick level (*i.e.* markers at the axis path) and a label lavel
   (*e.i.* place text at the axis path), *ticklevel* and *labellevel*. These are
   non-negative integers or *None*. A value of ``0`` means a regular tick or label,
   ``1`` stands for a subtick or sublabel, ``2`` for subsubtick or subsublabel and
   so on. ``None`` means omitting the tick or label. *label* is the text of the
   label. When not set, it can be created automatically by a texter. *labelattrs*
   are the attributes for the labels.


.. module:: graph.axis.parter

Module :mod:`graph.axis.parter`: Axes partitioners
==================================================

The following classes are part of the module :mod:`graph.axis.parter`. Instances
of the classes can be passed to the parter keyword argument of regular axes.


.. class:: linear(tickdists=None, labeldists=None, extendtick=0, extendlabel=None, epsilon=1e-10)

   Instances of this class creates equally spaced tick lists. The distances between
   the ticks, subticks, subsubticks *etc.* starting from a tick at zero are given
   as first, second, third *etc.* item of the list *tickdists*. For a tick
   position, the lowest level wins, *i.e.* for ``[2, 1]`` even numbers will have
   ticks whereas subticks are placed at odd integer. The items of *tickdists* might
   be strings, floats or tuples as described for the *pos* parameter of class
   :class:`tick`.

   *labeldists* works equally for placing labels. When *labeldists* is kept
   ``None``, labels will be placed at each tick position, but sublabels *etc.* will
   not be used. This copy behaviour is also available *vice versa* and can be
   disabled by an empty list.

   *extendtick* can be set to a tick level for including the next tick of that
   level when the data exceeds the range covered by the ticks by more than
   *epsilon*. *epsilon* is taken relative to the axis range. *extendtick* is
   disabled when set to ``None`` or for fixed range axes. *extendlabel* works
   similar to *extendtick* but for labels.


.. class:: lin(...)

   This class is an abbreviation of :class:`linear` described above.


.. class:: autolinear(variants=defaultvariants, extendtick=0, epsilon=1e-10)

   Instances of this class creates equally spaced tick lists, where the distance
   between the ticks is adjusted to the range of the axis automatically. Variants
   are a list of possible choices for *tickdists* of :class:`linear`. Further
   variants are build out of these by multiplying or dividing all the values by
   multiples of ``10``. *variants* should be ordered that way, that the number of
   ticks for a given range will decrease, hence the distances between the ticks
   should increase within the *variants* list. *extendtick* and *epsilon* have the
   same meaning as in :class:`linear`.


.. attribute:: autolinear.defaultvariants

   ``[[tick.rational((1, 1)), tick.rational((1, 2))], [tick.rational((2, 1)),
   tick.rational((1, 1))], [tick.rational((5, 2)), tick.rational((5, 4))],
   [tick.rational((5, 1)), tick.rational((5, 2))]]``


.. class:: autolin(...)

   This class is an abbreviation of :class:`autolinear` described above.


.. class:: preexp(pres, exp)

   This is a storage class defining positions of ticks on a logarithmic scale. It
   contains a list *pres* of positions :math:`p_i` and *exp*, a multiplicator
   :math:`m`. Valid tick positions are defined by :math:`p_im^n` for any integer
   :math:`n`.


.. class:: logarithmic(tickpreexps=None, labelpreexps=None, extendtick=0, extendlabel=None, epsilon=1e-10)

   Instances of this class creates tick lists suitable to logarithmic axes. The
   positions of the ticks, subticks, subsubticks *etc.* are defined by the first,
   second, third *etc.* item of the list *tickpreexps*, which are all
   :class:`preexp` instances.

   *labelpreexps* works equally for placing labels. When *labelpreexps* is kept
   ``None``, labels will be placed at each tick position, but sublabels *etc.* will
   not be used. This copy behaviour is also available *vice versa* and can be
   disabled by an empty list.

   *extendtick*, *extendlabel* and *epsilon* have the same meaning as in
   :class:`linear`.

Some :class:`preexp` instances for the use in :class:`logarithmic` are available
as instance variables (should be used read-only):


.. attribute:: logarithmic.pre1exp5

   ``preexp([tick.rational((1, 1))], 100000)``


.. attribute:: logarithmic.pre1exp4

   ``preexp([tick.rational((1, 1))], 10000)``


.. attribute:: logarithmic.pre1exp3

   ``preexp([tick.rational((1, 1))], 1000)``


.. attribute:: logarithmic.pre1exp2

   ``preexp([tick.rational((1, 1))], 100)``


.. attribute:: logarithmic.pre1exp

   ``preexp([tick.rational((1, 1))], 10)``


.. attribute:: logarithmic.pre125exp

   ``preexp([tick.rational((1, 1)), tick.rational((2, 1)), tick.rational((5, 1))],
   10)``


.. attribute:: logarithmic.pre1to9exp

   ``preexp([tick.rational((1, 1)) for x in range(1, 10)], 10)``


.. class:: log(...)

   This class is an abbreviation of :class:`logarithmic` described above.


.. class:: autologarithmic(variants=defaultvariants, extendtick=0, extendlabel=None, epsilon=1e-10)

   Instances of this class creates tick lists suitable to logarithmic axes, where
   the distance between the ticks is adjusted to the range of the axis
   automatically. Variants are a list of tuples with possible choices for
   *tickpreexps* and *labelpreexps* of :class:`logarithmic`. *variants* should be
   ordered that way, that the number of ticks for a given range will decrease
   within the *variants* list.

   *extendtick*, *extendlabel* and *epsilon* have the same meaning as in
   :class:`linear`.


.. attribute:: autologarithmic.defaultvariants

   ``[([log.pre1exp, log.pre1to9exp], [log.pre1exp, log.pre125exp]), ([log.pre1exp,
   log.pre1to9exp], None), ([log.pre1exp2, log.pre1exp], None), ([log.pre1exp3,
   log.pre1exp], None), ([log.pre1exp4, log.pre1exp], None), ([log.pre1exp5,
   log.pre1exp], None)]``


.. class:: autolog(...)

   This class is an abbreviation of :class:`autologarithmic` described above.


.. module:: graph.axis.texter

Module :mod:`graph.axis.texter`: Axes texter
============================================

The following classes are part of the module :mod:`graph.axis.texter`. Instances
of the classes can be passed to the texter keyword argument of regular axes.
Texters are used to define the label text for ticks, which request to have a
label, but for which no label text has been specified so far. A typical case are
ticks created by partitioners described above.


.. class:: decimal(prefix="", infix="", suffix="", equalprecision=False, decimalsep=".", thousandsep="", thousandthpartsep="", plus="", minus="-", period=r"\\overline{%s}", labelattrs=[text.mathmode])

   Instances of this class create decimal formatted labels.

   The strings *prefix*, *infix*, and *suffix* are added to the label at the
   beginning, immediately after the plus or minus, and at the end, respectively.

   *equalprecision* forces the same number of digits after *decimalsep*, even
   when the tailing digits are zero.

   *decimalsep*, *thousandsep*, and *thousandthpartsep* are strings used to
   separate integer from fractional part and three-digit groups in the integer and
   fractional part. The strings *plus* and *minus* are inserted in front of the
   unsigned value for non-negative and negative numbers, respectively.

   The format string *period* should generate a period. It must contain one string
   insert operators ``%s`` for the period.

   *labelattrs* is a list of attributes to be added to the label attributes given
   in the painter. It should be used to setup TeX features like ``text.mathmode``.
   Text format options like ``text.size`` should instead be set at the painter.


.. class:: default(multiplication_tex=r"\cdot{}", multiplication_unicode="·", base=Fraction(10), skipmantissaunity=skipmantissaunity.all, minusunity="-", minexponent=4, minnegexponent=None, uniformexponent=True, mantissatexter=decimal(), basetexter=decimal(), exponenttexter=decimal(), labelattrs=[text.mathmode])

   Instances of this class create decimal formatted labels with an exponential.

   multiplication_tex and multiplication_unicode are the strings to indicate
   the multiplication between the mantissa and the base number for the
   TexEngine and the UnicodeEngine, respecitvely

   base is the number of the base of the exponent

   skipmantissaunity is either skipmantissaunity.never (never skip the unity
   mantissa), skipmantissaunity.each (skip the unity mantissa whenever it occurs
   for each label separately), or skipmantissaunity.all (skip the unity mantissa
   whenever if all labels happen to be mantissafixed with unity)

   minusunity is used as the output of -unity for the mantissa

   minexponent is the minimal positive exponent value to be printed by exponential
   notation

   minnegexponent is the minimal negative exponent value to be printed by
   exponential notation, for None it is considered to be equal to minexponent

   uniformexponent forces all numbers to be written in exponential notation when at
   least one label excets the limits for non-exponential notiation

   mantissatexter, basetexter, and exponenttexter generate the texts for the
   mantissa, basetexter, and exponenttexter

   labelattrs is a list of attributes to be added to the label attributes given
   in the painter"""


.. class:: rational(prefix="", infix="", suffix="", numprefix="", numinfix="", numsuffix="", denomprefix="", denominfix="", denomsuffix="", plus="", minus="-", minuspos=0, over=r"%s\\over%s", equaldenom=False, skip1=True, skipnum0=True, skipnum1=True, skipdenom1=True, labelattrs=[text.mathmode])

   Instances of this class create labels formated as fractions.

   The strings *prefix*, *infix*, and *suffix* are added to the label at the
   beginning, immediately after the plus or minus, and at the end, respectively.
   The strings *numprefix*, *numinfix*, and *numsuffix* are added to the labels
   numerator accordingly whereas *denomprefix*, *denominfix*, and *denomsuffix* do
   the same for the denominator.

   The strings *plus* and *minus* are inserted in front of the unsigned value. The
   position of the sign is defined by *minuspos* with values ``1`` (at the
   numerator), ``0`` (in front of the fraction), and ``-1`` (at the denominator).

   The format string *over* should generate the fraction. It must contain two
   string insert operators ``%s``, the first for the numerator and the second for
   the denominator. An alternative to the default is ``"{{%s}/{%s}}"``.

   Usually, the numerator and denominator are canceled, while, when *equaldenom* is
   set, the least common multiple of all denominators is used.

   The boolean *skip1* indicates, that only the prefix, plus or minus, the infix
   and the suffix should be printed, when the value is ``1`` or ``-1`` and at least
   one of *prefix*, *infix* and *suffix* is present.

   The boolean *skipnum0* indicates, that only a ``0`` is printed when the
   numerator is zero.

   *skipnum1* is like *skip1* but for the numerator.

   *skipdenom1* skips the denominator, when it is ``1`` taking into account
   *denomprefix*, *denominfix*, *denomsuffix* *minuspos* and the sign of the
   number.

   *labelattrs* has the same meaning as for *decimal*.


.. module:: graph.axis.painter

Module :mod:`graph.axis.painter`: Axes painter
==============================================

The following classes are part of the module :mod:`graph.axis.painter`.
Instances of the painter classes can be passed to the painter keyword argument
of regular axes.


.. class:: rotatetext(direction, epsilon=1e-10)

   This helper class is used in direction arguments of the painters below to
   prevent axis labels and titles being written upside down. In those cases the
   text will be rotated by 180 degrees. *direction* is an angle to be used relative
   to the tick direction. *epsilon* is the value by which 90 degrees can be
   exceeded before an 180 degree rotation is performed.

The following two class variables are initialized for the most common
applications:


.. attribute:: rotatetext.parallel

   ``rotatetext(90)``


.. attribute:: rotatetext.orthogonal

   ``rotatetext(180)``


.. class:: ticklength(initial, factor)

   This helper class provides changeable PyX lengths starting from an initial value
   *initial* multiplied by *factor* again and again. The resulting lengths are thus
   a geometric series.

There are some class variables initialized with suitable values for tick
stroking. They are named ``ticklength.SHORT``, ``ticklength.SHORt``, …,
``ticklength.short``, ``ticklength.normal``, ``ticklength.long``, …,
``ticklength.LONG``. ``ticklength.normal`` is initialized with a length of
``0.12`` and the reciprocal of the golden mean as ``factor`` whereas the others
have a modified initial value obtained by multiplication with or division by
appropriate multiples of  :math:`\sqrt{2}`.


.. class:: regular(innerticklength=ticklength.normal, outerticklength=None, tickattrs=[], gridattrs=None, basepathattrs=[], labeldist="0.3 cm", labelattrs=[], labeldirection=None, labelhequalize=0, labelvequalize=1, titledist="0.3 cm", titleattrs=[], titledirection=rotatetext.parallel, titlepos=0.5, texrunner=None)

   Instances of this class are painters for regular axes like linear and
   logarithmic axes.

   *innerticklength* and *outerticklength* are visual PyX lengths of the ticks,
   subticks, subsubticks *etc.* plotted along the axis inside and outside of the
   graph. Provide changeable attributes to modify the lengths of ticks compared to
   subticks *etc.* ``None`` turns off the ticks inside and outside the graph,
   respectively.

   *tickattrs* and *gridattrs* are changeable stroke attributes for the ticks and
   the grid, where ``None`` turns off the feature. *basepathattrs* are stroke
   attributes for the axis or ``None`` to turn it off. *basepathattrs* is merged
   with ``[style.linecap.square]``.

   *labeldist* is the distance of the labels from the axis base path as a visual
   PyX length. *labelattrs* is a list of text attributes for the labels. It is
   merged with ``[text.halign.center, text.vshift.mathaxis]``. *labeldirection* is
   an instance of *rotatetext* to rotate the labels relative to the axis tick
   direction or ``None``.

   The boolean values *labelhequalize* and *labelvequalize* force an equal
   alignment of all labels for straight vertical and horizontal axes, respectively.

   *titledist* is the distance of the title from the rest of the axis as a visual
   PyX length. *titleattrs* is a list of text attributes for the title. It is
   merged with ``[text.halign.center, text.vshift.mathaxis]``. *titledirection* is
   an instance of *rotatetext* to rotate the title relative to the axis tick
   direction or ``None``. *titlepos* is the position of the title in graph
   coordinates.

   *texrunner* is the texrunner instance to create axis text like the axis title or
   labels. When not set the texrunner of the graph instance is taken to create the
   text.


.. class:: linked(innerticklength=ticklength.short, outerticklength=None, tickattrs=[], gridattrs=None, basepathattrs=[], labeldist="0.3 cm", labelattrs=None, labeldirection=None, labelhequalize=0, labelvequalize=1, titledist="0.3 cm", titleattrs=None, titledirection=rotatetext.parallel, titlepos=0.5, texrunner=None)

   This class is identical to :class:`regular` up to the default values of
   *labelattrs* and *titleattrs*. By turning off those features, this painter is
   suitable for linked axes.


.. class:: bar(innerticklength=None, outerticklength=None, tickattrs=[], basepathattrs=[], namedist="0.3 cm", nameattrs=[], namedirection=None, namepos=0.5, namehequalize=0, namevequalize=1, titledist="0.3 cm", titleattrs=[], titledirection=rotatetext.parallel, titlepos=0.5, texrunner=None)

   Instances of this class are suitable painters for bar axes.

   *innerticklength* and *outerticklength* are visual PyX lengths to mark the
   different bar regions along the axis inside and outside of the graph. ``None``
   turns off the ticks inside and outside the graph, respectively. *tickattrs* are
   stroke attributes for the ticks or ``None`` to turn all ticks off.

   The parameters with prefix *name* are identical to their *label* counterparts in
   :class:`regular`. All other parameters have the same meaning as in
   :class:`regular`.


.. class:: linkedbar(innerticklength=None, outerticklength=None, tickattrs=[], basepathattrs=[], namedist="0.3 cm", nameattrs=None, namedirection=None, namepos=0.5, namehequalize=0, namevequalize=1, titledist="0.3 cm", titleattrs=None, titledirection=rotatetext.parallel, titlepos=0.5, texrunner=None)

   This class is identical to :class:`bar` up to the default values of *nameattrs*
   and *titleattrs*. By turning off those features, this painter is suitable for
   linked bar axes.


.. class:: split(breaklinesdist="0.05 cm", breaklineslength="0.5 cm", breaklinesangle=-60, titledist="0.3 cm", titleattrs=[], titledirection=rotatetext.parallel, titlepos=0.5, texrunner=None)

   Instances of this class are suitable painters for split axes.

   *breaklinesdist* and *breaklineslength* are the distance between axes break
   markers in visual PyX lengths. *breaklinesangle* is the angle of the axis break
   marker with respect to the base path of the axis. All other parameters have the
   same meaning as in :class:`regular`.


.. class:: linkedsplit(breaklinesdist="0.05 cm", breaklineslength="0.5 cm", breaklinesangle=-60, titledist="0.3 cm", titleattrs=None, titledirection=rotatetext.parallel, titlepos=0.5, texrunner=None)

   This class is identical to :class:`split` up to the default value of
   *titleattrs*. By turning off this feature, this painter is suitable for linked
   split axes.


.. module:: graph.axis.rater

Module :mod:`graph.axis.rater`: Axes rater
==========================================

The rating of axes is implemented in :mod:`graph.axis.rater`. When an axis
partitioning scheme returns several partitioning possibilities, the partitions
need to be rated by a positive number. The axis partitioning rated lowest is
considered best.

The rating consists of two steps. The first takes into account only the number
of ticks, subticks, labels and so on in comparison to optimal numbers.
Additionally, the extension of the axis range by ticks and labels is taken into
account. This rating leads to a preselection of possible partitions. In the
second step, after the layout of preferred partitionings has been calculated,
the distance of  the labels in a partition is taken into account as well at a
smaller weight factor by default. Thereby partitions with overlapping labels
will be rejected completely. Exceptionally sparse or dense labels will receive a
bad rating as well.


.. class:: cube(opt, left=None, right=None, weight=1)

   Instances of this class provide a number rater. *opt* is the optimal value. When
   not provided, *left* is set to ``0`` and *right* is set to ``3*opt``. Weight is
   a multiplicator to the result.

   The rater calculates ``width*((x-opt)/(other-opt))**3`` to rate the value ``x``,
   where ``other`` is *left* (``x``<*opt*) or *right* (``x``>*opt*).


.. class:: distance(opt, weight=0.1)

   Instances of this class provide a rater for a list of numbers. The purpose is to
   rate the distance between label boxes. *opt* is the optimal value.

   The rater calculates the sum of ``weight*(opt/x-1)`` (``x``<*opt*) or
   ``weight*(x/opt-1)`` (``x``>*opt*) for all elements ``x`` of the list. It
   returns this value divided by the number of elements in the list.


.. class:: rater(ticks, labels, range, distance)

   Instances of this class are raters for axes partitionings.

   *ticks* and *labels* are both lists of number rater instances, where the first
   items are used for the number of ticks and labels, the second items are used for
   the number of subticks (including the ticks) and sublabels (including the
   labels) and so on until the end of the list is reached or no corresponding ticks
   are available.

   *range* is a number rater instance which rates the range of the ticks relative
   to the range of the data.

   *distance* is an distance rater instance.


.. class:: linear(ticks=[cube(4), cube(10, weight=0.5)], labels=[cube(4)], range=cube(1, weight=2), distance=distance("1 cm"))

   This class is suitable to rate partitionings of linear axes. It is equal to
   :class:`rater` but defines predefined values for the arguments.


.. class:: lin(...)

   This class is an abbreviation of :class:`linear` described above.


.. class:: logarithmic(ticks=[cube(5, right=20), cube(20, right=100, weight=0.5)], labels=[cube(5, right=20), cube(5, right=20, weight=0.5)], range=cube(1, weight=2), distance=distance("1 cm"))

   This class is suitable to rate partitionings of logarithmic axes. It is equal to
   :class:`rater` but defines predefined values for the arguments.


.. class:: log(...)

   This class is an abbreviation of :class:`logarithmic` described above.


.. module:: graph.axis.positioners

Module :mod:`graph.axis.positioner`: Axes positioners
=====================================================

The position of an axis is defined by an instance of a class providing the
following methods:


.. class:: positioner()

.. method:: positioner.vbasepath(v1=None, v2=None)

   Returns a path instance for the base path. *v1* and *v2* define the axis range
   in graph coordinates the base path should cover.


.. method:: positioner.vgridpath(v)

   Returns a path instance for the grid path at position *v* in graph coordinates.
   The method might return ``None`` when no grid path is available (for an axis
   along a path for example).


.. method:: positioner.vtickpoint_pt(v)

   Returns the position of *v* in graph coordinates as a tuple ``(x, y)`` in
   points.


.. method:: positioner.vtickdirection(v)

   Returns the direction of a tick at *v* in graph coordinates as a tuple ``(dx,
   dy)``. The tick direction points inside of the graph.

The module contains several implementations of those positioners, but since the
positioner instances are created by graphs etc. as needed, the details are not
interesting for the average PyX user.

