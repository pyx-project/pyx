.. module:: graph
   :synopsis: 1D, 2D, and 3D data and function plotting

.. _graph:

******
Graphs
******

Introduction
============

PyX provides a flexible, publication-quality plotting system for 1D, 2D
(*x*–*y*), and 3D (*x*–*y*–*z*) data and mathematical functions. Its modular
component architecture (described in section :ref:`graph_components`) cleanly
separates graph geometry, data sources, plotting styles, legends (keys), and
axes.

A Minimal Plot
--------------

Creating a graph in PyX takes three steps:

1. Instantiate a graph object such as :class:`graph.graphxy`:

   .. code-block:: python

      from pyx import *
      g = graph.graphxy(width=8)

2. Call :meth:`~graph.graphxy.plot` with one or more data sources (and optional
   plot styles). For example, given a data file :file:`graph.dat` containing two
   columns of numbers:

   .. include:: graph.dat
      :literal:

   we can plot column 1 against column 2 with:

   .. code-block:: python

      g.plot(graph.data.file("graph.dat", x=1, y=2))

   When no explicit style list is passed to :meth:`~graph.graphxy.plot`, each
   data source uses its own default style—symbols (:class:`graph.style.symbol`)
   for tabular data such as :class:`graph.data.file`, and continuous lines
   (:class:`graph.style.line`) for analytical functions such as
   :class:`graph.data.function`.

3. Write the finished graph to a file. Because every graph instance is a
   subclass of :class:`canvas.canvas`, you can call any canvas output method (or
   insert the graph into another canvas):

   .. code-block:: python

      g.writeEPSfile("graph")

The resulting plot :file:`graph.eps` is shown in figure :ref:`fig_graph`.

.. _fig_graph:
.. figure:: graph.*
   :align: center

   A minimal scatter plot of the data in :file:`graph.dat`.

Combining Multiple Datasets and Functions
-----------------------------------------

You can overlay multiple datasets and analytical functions on the same graph by
calling :meth:`~graph.graphxy.plot` several times before writing the output. For
example, to plot the parabola :math:`y(x) = x^2` alongside the data file:

.. code-block:: python

   g.plot(graph.data.function("y(x)=x**2"))

.. _fig_graph2:
.. figure:: graph2.*
   :align: center

   Plotting tabular data from a file together with an analytical function.

Configuring Axes and Keyword-Splitting Shortcuts
------------------------------------------------

In the examples above, the *x* and *y* axes were created automatically as linear
axes (:class:`graph.axis.linear`) and their ranges were determined from the
plotted data. When plotting only an analytical function, or when you want fixed
axis bounds, titles, or logarithmic scaling, you can pass explicit axis
instances (see chapter :ref:`axis`):

.. include:: graph3.py
   :literal:

The resulting plot with a logarithmic *y*-axis is shown in figure
:ref:`fig_graph3`.

.. _fig_graph3:
.. figure:: graph3.*
   :align: center

   Plotting a function over a fixed *x*-range with a logarithmic *y*-axis.

.. tip::

   **Concise axis configuration via underscore keyword splitting**:
   Instead of instantiating :class:`graph.axis.linear` or
   :class:`graph.axis.painter.regular` explicitly just to set a few options, you
   can pass underscore-separated keyword arguments directly to
   :class:`graph.graphxy` (powered by :func:`utils.kwsplit`). For example:

   .. code-block:: python

      g = graph.graphxy(width=8,
                        x_min=0, x_max=10, x_title=r"$x$",
                        y_title=r"$f(x)$",
                        x_painter_gridattrs=[color.gray(0.8)])

   Here ``x_min``, ``x_max``, and ``x_title`` are automatically forwarded to the
   ``x`` axis, and ``x_painter_gridattrs`` is forwarded to the ``painter`` of the
   ``x`` axis!


.. _graph_components:

Component Architecture and Canvas Layers
========================================

PyX splits the work of constructing a graph across five cooperating modules:

``graph`` (:mod:`graph.graph`)
   Defines the overall geometry of the plot area using normalized *graph
   coordinates* :math:`v \in [0, 1]` along each dimension, manages the canvas
   layers, coordinates axis range adjustment and style selection, and provides
   geometric transformation methods between data coordinates, graph coordinates,
   and canvas coordinates.

``data`` (:mod:`graph.data`)
   Reads, generates, or transforms data columns (from files, Python lists, or
   mathematical expressions) and supplies points to the styles.

``style`` (:mod:`graph.style`)
   Translates data values into visual marks on the graph canvas (symbols, lines,
   error bars, histograms, bars, 3D surfaces, heatmaps/densities, arrows, and
   text labels).

``key`` (:mod:`graph.key`)
   Builds and positions the graph legend from the titles and style samples of the
   plotted items.

``axis`` (:mod:`graph.axis`)
   Maps data values to normalized graph coordinates :math:`[0, 1]` and partitions,
   formats, rates, and paints axis baselines, ticks, labels, titles, and grids
   (covered in detail in chapter :ref:`axis`).

Canvas Layer Ordering in a Graph
--------------------------------

Every :class:`graph.graph` instance is a :class:`canvas.canvas` pre-initialized
with nine named layers in back-to-front drawing order:

1. ``"background"`` — graph background fill and border
2. ``"grid"`` — axis grid lines
3. ``"filldata"`` — filled data regions (such as bars, rectangles, and density bitmaps)
4. ``"axes.baseline"`` — axis baselines
5. ``"axes.ticks"`` — axis tick marks
6. ``"axes.labels"`` — axis tick labels
7. ``"axes.title"`` — axis titles
8. ``"data"`` — stroked data lines, symbols, and error bars
9. ``"key"`` — graph legend (key)

Because drawing order is governed by these layers rather than the order in which
internal ``do*()`` methods are executed, grid lines always appear behind data
and axes labels always remain legible on top of grid lines. If you draw custom
annotations onto a graph canvas ``g``, you can target any layer directly via
``g.layer("filldata").fill(...)`` or ``g.layer("data").stroke(...)``.


.. module:: graph.graph
   :synopsis: 1D, 2D, and 3D graph geometries

Module :mod:`graph.graph`: Graph Geometry
=========================================

The classes :class:`graphxy`, :class:`graphx`, and :class:`graphxyz` are defined
in :mod:`graph.graph` and re-exported at the top level of :mod:`graph` as
``graph.graphxy``, ``graph.graphx``, and ``graph.graphxyz``.

2D Graphs (:class:`graphxy`)
----------------------------

.. class:: graphxy(xpos=0, ypos=0, width=None, height=None, ratio=goldenmean, key=None, backgroundattrs=None, axesdist=0.8*unit.v_cm, flipped=False, xaxisat=None, yaxisat=None, **axes)

   Constructs a two-dimensional *x*–*y* graph.

   * *xpos*, *ypos*: Lower-left corner of the plot area on the graph canvas (in
     user units or PyX lengths; default ``0``).
   * *width*, *height*, *ratio*: Dimensions of the rectangular plot area
     (excluding the space occupied by ticks, labels, and titles outside the box).
     At least *width* or *height* must be specified; if only one is given, the
     other is computed using *ratio* (which defaults to the golden ratio
     :math:`(1 + \sqrt{5})/2 \approx 1.618`).
   * *key*: Optional :class:`graph.key.key` instance to generate a graph legend,
     or ``None`` (default) to omit the legend.
   * *backgroundattrs*: List of fill/stroke attributes (e.g.
     ``[deco.filled([color.gray(0.95)])]``) used to draw the rectangular plot
     background in the ``"background"`` layer, or ``None`` (default) for a
     transparent background.
   * *axesdist*: Distance between multiple parallel axes stacked on the same side
     of the graph (default ``0.8 * unit.v_cm``).
   * *flipped*: When ``True``, swaps the geometric orientation of the *x* and *y*
     axes so that the *x*-axis runs vertically and the *y*-axis runs
     horizontally (default ``False``).
   * *xaxisat*, *yaxisat*: Data value along the orthogonal axis (*y* or *x*,
     respectively) at which the main ``x`` or ``y`` axis should be positioned
     inside the plot (for example, ``xaxisat=0, yaxisat=0`` to cross the axes at
     the origin). Setting *xaxisat* or *yaxisat* disables automatic creation of
     the opposite linked axis (``x2`` or ``y2``).
   * *\*\*axes*: Axis instances or underscore-split axis parameters. Valid axis
     names are ``x``, ``x2``, ``x3``, … and ``y``, ``y2``, ``y3``, ….

     - If neither ``x`` nor ``x2`` is specified, ``x`` defaults to
       :class:`graph.axis.linear`.
     - If ``x2`` (or ``y2``) is not specified and *xaxisat* (or *yaxisat*) is
       ``None``, PyX automatically creates a :class:`graph.axis.linkedaxis` at
       the opposite side of the plot box (top for ``x2``, right for ``y2``). Pass
       ``x2=None`` or ``y2=None`` to suppress the top or right axis.
     - Odd-numbered axes (``x``, ``x3``, … and ``y``, ``y3``, …) are placed at
       the bottom and left of the plot; even-numbered axes (``x2``, ``x4``, … and
       ``y2``, ``y4``, …) are placed at the top and right, spaced outward by
       *axesdist*.
     - Any keyword argument of the form ``<axisname>_<option>=...`` (such as
       ``x_min=0`` or ``y_painter_gridattrs=...``) is split via
       :func:`utils.kwsplit` and applied to the corresponding axis.

   .. attribute:: graphxy.axes

      Dictionary mapping axis names (``"x"``, ``"y"``, ``"x2"``, ``"y2"``, …) to
      their :class:`graph.axis.anchoredaxis` instances.

Plotting Data and Accessing Plot Items
--------------------------------------

.. method:: graphxy.plot(data, styles=None, rangewarning=1)

   Adds *data* (a :mod:`graph.data` instance, or an iterable of data instances)
   to the graph to be plotted with *styles* (a list of :mod:`graph.style`
   instances, or ``None`` to use ``data.defaultstyles``).

   Returns a :class:`plotitem` instance (or a list of :class:`plotitem` instances
   if *data* was an iterable). When the exact same *styles* list object is reused
   across multiple :meth:`plot` calls on the same graph, the styles automatically
   cycle through their changeable attributes (such as symbol shapes or dash
   patterns).

   .. tip::

      **Accessing plotted paths**:
      After calling ``g.doplot()`` (or ``g.finish()``), a :class:`plotitem`
      provides attribute access to data stored by its styles. In particular, when
      plotting with :class:`graph.style.line`, ``p = g.plot(...); g.doplot(); p.path``
      returns the plotted :class:`path.path` in canvas coordinates—ideal for
      filling the area between two curves using :meth:`path.path.joined`!

Graph Lifecycle and Finalization Methods
----------------------------------------

A graph accumulates data across :meth:`plot` calls and automatically finalizes
its layout and drawing when written to a file or when its :meth:`bbox` is
queried. If you want to query data positions (:meth:`pos`) or axis paths before
writing the file, call :meth:`dolayout` (or :meth:`finish`) explicitly. Calling
any ``do*()`` method multiple times is safe (subsequent calls are no-ops):

.. method:: graphxy.doranges()

   Computes automatic axis ranges from all plotted data sources and evaluates
   dynamic data sources (such as :class:`graph.data.function`).

.. method:: graphxy.dolayout()

   Runs :meth:`doranges`, partitions and paints all axes, and fixes the geometry
   of the graph. After :meth:`dolayout` has run, coordinate conversion methods
   such as :meth:`pos` are ready to use.

.. method:: graphxy.dobackground()

   Draws the graph background if *backgroundattrs* was specified.

.. method:: graphxy.doaxes()

   Inserts the painted axis layers into the graph canvas.

.. method:: graphxy.dostyles()

   Selects changeable style attributes across all plotted datasets. Once
   :meth:`dostyles` has been called, no further :meth:`plot` calls are allowed.

.. method:: graphxy.doplotitem(plotitem)

   Draws a single *plotitem* onto the graph canvas.

.. method:: graphxy.doplot()

   Draws all remaining plot items onto the graph canvas.

.. method:: graphxy.dokeyitem(plotitem)

   Registers *plotitem* with the graph legend.

.. method:: graphxy.dokey()

   Paints and inserts the graph legend (:class:`graph.key.key`).

.. method:: graphxy.finish()

   Executes all pending lifecycle steps (:meth:`dobackground`, :meth:`doaxes`,
   :meth:`doplot`, and :meth:`dokey`). Called automatically before output or
   bounding-box calculation.

Coordinate Queries and Axis Positioning
---------------------------------------

.. method:: graphxy.pos(x, y, xaxis=None, yaxis=None)
.. method:: graphxy.pos_pt(x, y, xaxis=None, yaxis=None)

   Converts data values ``(x, y)`` along *xaxis* and *yaxis* (defaulting to
   ``self.axes["x"]`` and ``self.axes["y"]``) into canvas coordinates
   ``(xpos, ypos)`` (in user units for :meth:`pos`, or PostScript points for
   :meth:`pos_pt`). Requires :meth:`dolayout` to have been called if axis ranges
   are automatic.

.. method:: graphxy.vpos(vx, vy)
.. method:: graphxy.vpos_pt(vx, vy)

   Converts normalized graph coordinates ``(vx, vy)`` in :math:`[0, 1]^2` into
   canvas coordinates ``(xpos, ypos)``.

.. method:: graphxy.vgeodesic(vx1, vy1, vx2, vy2)
.. method:: graphxy.vgeodesic_el(vx1, vy1, vx2, vy2)

   Returns the geodesic path (:meth:`vgeodesic`) or path element
   (:meth:`vgeodesic_el`) connecting ``(vx1, vy1)`` to ``(vx2, vy2)`` in
   normalized graph coordinates (a straight line segment for :class:`graphxy`).

.. method:: graphxy.axisatv(axis, v)

   Translates the anchored *axis* to the normalized graph coordinate *v* along
   the orthogonal direction (must be called after :meth:`dolayout`).

.. index::
   single: xbasepath() (graphxy method)
   single: xvbasepath() (graphxy method)
   single: xgridpath() (graphxy method)
   single: xvgridpath() (graphxy method)
   single: xtickpoint() (graphxy method)
   single: xvtickpoint() (graphxy method)
   single: xtickdirection() (graphxy method)
   single: xvtickdirection() (graphxy method)
   single: ybasepath() (graphxy method)
   single: yvbasepath() (graphxy method)
   single: ygridpath() (graphxy method)
   single: yvgridpath() (graphxy method)
   single: ytickpoint() (graphxy method)
   single: xvtickpoint() (graphxy method)
   single: ytickdirection() (graphxy method)
   single: yvtickdirection() (graphxy method)

In addition, for the primary ``x`` and ``y`` axes, :class:`graphxy` exposes
shortcut methods ``Xbasepath``, ``Xvbasepath``, ``Xgridpath``, ``Xvgridpath``,
``Xtickpoint``, ``Xtickpoint_pt``, ``Xvtickpoint``, ``Xvtickpoint_pt``,
``Xtickdirection``, and ``Xvtickdirection`` (where ``X`` is ``x`` or ``y``) that
delegate directly to ``self.axes["x"]`` and ``self.axes["y"]`` (see
:class:`graph.axis.anchoredaxis`).

1D Graphs and Color Bars (:class:`graphx`)
------------------------------------------

.. class:: graphx(xpos=0, ypos=0, length=None, size=0.5*unit.v_cm, direction="vertical", key=None, backgroundattrs=None, axesdist=0.8*unit.v_cm, **kwargs)

   A one-dimensional specialization of :class:`graphxy` with a single active axis
   dimension (``x``, ``x2``, …) of length *length* and cross-sectional width
   *size* (default ``0.5 * unit.v_cm``), oriented either ``"vertical"`` (default)
   or ``"horizontal"``. :class:`graphx` is used automatically as the color scale
   legend (``keygraph``) for :class:`graph.style.rect`,
   :class:`graph.style.surface`, and :class:`graph.style.density` plots.

3D Graphs (:class:`graphxyz`)
-----------------------------

.. class:: graphxyz(xpos=0, ypos=0, size=None, xscale=1, yscale=1, zscale=1/goldenmean, xy12axesat=None, xy12axesatname="z", projector=central(10, -30, 30), key=None, **axes)

   Constructs a three-dimensional *x*–*y*–*z* graph projected onto the 2D canvas.

   * *xpos*, *ypos*: Origin of the projected graph on the canvas.
   * *size*: Overall scaling length of the projected 3D box.
   * *xscale*, *yscale*, *zscale*: Relative scale factors along the three dimensions
     (default ``1``, ``1``, and ``1 / goldenmean``).
   * *xy12axesat*, *xy12axesatname*: Moves the bottom *x*–*y* plane (containing
     axes ``x``, ``x2``, ``y``, ``y2``) to the specified data value along axis
     *xy12axesatname* (default ``"z"``).
   * *projector*: A 3D-to-2D projection instance—either :class:`central`
     (perspective projection) or :class:`parallel` (orthographic/parallel
     projection), also accessible as class attributes ``graphxyz.central`` and
     ``graphxyz.parallel``.
   * *\*\*axes*: Supports up to four axes per dimension (``x``, ``x2``, ``x3``,
     ``x4``, ``y``, ``y2``, ``y3``, ``y4``, ``z``, ``z2``, ``z3``, ``z4``).
     ``x``, ``x2``, ``y``, ``y2`` border the bottom *x*–*y* plane (with ``x`` and
     ``y`` automatically placed along the front edges closest to the viewer);
     ``x3``, ``x4``, ``y3``, ``y4`` border the top *x*–*y* plane; and ``z``,
     ``z2``, ``z3``, ``z4`` run along the four vertical corners.

   In addition to 3D versions of :meth:`pos`, :meth:`vpos`, :meth:`vgeodesic`,
   and :meth:`vgeodesic_el` (each taking three coordinates *x*, *y*, *z*),
   :class:`graphxyz` provides depth and surface-normal angle queries used for
   occlusion sorting and 3D lighting:

   .. method:: graphxyz.vzindex(vx, vy, vz)

      Returns the normalized depth of ``(vx, vy, vz)`` in :math:`[-1, 1]`, where
      larger values are closer to the viewer.

   .. method:: graphxyz.vangle(vx1, vy1, vz1, vx2, vy2, vz2, vx3, vy3, vz3)

      Returns the cosine of the angle between the viewing ray through
      ``(vx1, vy1, vz1)`` and the plane spanned by the three points
      ``(vx1, vy1, vz1)``, ``(vx2, vy2, vz2)``, and ``(vx3, vy3, vz3)``.

.. class:: central(distance, phi, theta, anglefactor=math.pi/180)

   Central (perspective) 3D-to-2D projector.

   * *distance*: Distance of the viewer from the center of the graph in units of
     *xscale* / *yscale* / *zscale* (values around ``10`` give natural perspective;
     larger values approach parallel projection).
   * *phi*: Azimuthal viewing angle in the *x*–*y* plane (in degrees by default).
   * *theta*: Elevation angle above the *x*–*y* plane (in degrees by default).
   * *anglefactor*: Conversion factor from the angle unit of *phi* and *theta* to
     radians (default ``math.pi / 180``).

.. class:: parallel(phi, theta, anglefactor=math.pi/180)

   Parallel (orthographic) 3D-to-2D projector with azimuthal angle *phi* and
   elevation angle *theta*.


.. module:: graph.data
   :synopsis: Data sources for graphs

Module :mod:`graph.data`: Graph Data Sources
============================================

The classes in :mod:`graph.data` prepare tabular or functional data for
:meth:`graph.graphxy.plot`.

Tabular Data from Python Lists and Dictionaries
-----------------------------------------------

.. class:: values(title="user provided values", **columns)

   Creates a dataset from keyword arguments where each keyword name defines a
   column name and its value is a sequence (list, tuple, or NumPy array) of column
   values:

   .. code-block:: python

      g.plot(graph.data.values(x=[1, 2, 3, 4], y=[1, 4, 9, 16], title="Squares"))

.. class:: points(data, title="user provided points", addlinenumbers=1, **columns)

   Creates a dataset from a list of rows (*data*), where each row is a sequence
   of values ``[v1, v2, ...]``.

   * *\*\*columns*: Maps column names (such as ``x=1, y=2``) to column indices in
     each row.
   * *addlinenumbers*: When true (default), 1-based row numbers are placed in
     virtual column ``0``, and data columns in *data* are indexed starting at
     ``1``. When false, data columns in *data* are indexed starting at ``0``.

Reading Data from Files
-----------------------

.. class:: file(filename, commentpattern=defaultcommentpattern, columnpattern=defaultcolumnpattern, stringpattern=defaultstringpattern, skiphead=0, skiptail=0, every=1, title=notitle, context={}, copy=1, replacedollar=1, columncallback="__column__", **columns)

   Reads whitespace-separated or custom-formatted tabular data from *filename*
   (a file path or open text file object). Parsed files are cached in memory so
   multiple :class:`file` instances reading different columns from the same file
   only parse the file once.

   **Line and column parsing**:

   * Lines matching *commentpattern* (by default, lines starting with ``#``,
     ``!``, or ``%``, as well as blank lines) are skipped as comments.
   * If the last non-empty comment line immediately preceding the first data line
     contains tokens, those tokens are used as *file column names*.
   * Each data line is tokenized by repeatedly matching *stringpattern* (which by
     default extracts double-quoted strings ``"..."`` containing spaces) and
     *columnpattern* (which extracts whitespace-delimited tokens and converts
     them to ``float`` when possible, or keeps them as strings otherwise).
   * *skiphead* and *skiptail* skip the specified number of data rows at the
     beginning or end of the file, and *every* keeps only every *every*-th row.

   **Column definitions and mathematical expressions** (*\*\*columns*):

   Each keyword argument ``name=spec`` defines a named column passed to the
   plotting styles:

   * If ``spec`` is an integer, it selects the 1-based column number from the
     file (or ``0`` for the 1-based data row number).
   * If ``spec`` is a string, it can be either a file column name (from the
     header comment) or an arbitrary Python mathematical expression evaluated for
     each row. Inside the expression, you can reference file columns by their
     header names or via ``$1``, ``$2``, … (when ``replacedollar=1``), as well as
     all functions and constants in Python's :mod:`math` module (plus the
     built-in helpers listed in the table below) and any variables passed in the
     *context* dictionary.
   * When ``copy=1`` (default), all named columns from the file header are also
     passed through to the plotting styles automatically unless overridden by
     *\*\*columns*.
   * *title*: Legend title for the dataset. By default, PyX constructs a title
     automatically from *filename* and the column expressions; pass
     ``title=None`` to suppress the legend entry.

   **Example**:

   Given :file:`test.dat`:

   .. code-block:: text

      # A   B C
      1.234 1 2
      5.678 3 4

   calling:

   .. code-block:: python

      d = graph.data.file("test.dat", a=1, b="B", c="2*B+$3")

   produces columns ``a = [1.234, 5.678]``, ``b = [1.0, 3.0]``, and
   ``c = [4.0, 10.0]`` (along with ``A``, ``B``, and ``C`` since ``copy=1``).

   The default regular expression patterns on :class:`file` are:

   .. attribute:: file.defaultcommentpattern

      ``re.compile(r"(#+|!+|%+)\s*")``

   .. attribute:: file.defaultstringpattern

      ``re.compile(r"\"(.*?)\"(\s+|$)")``

   .. attribute:: file.defaultcolumnpattern

      ``re.compile(r"(.*?)(\s+|$)")``

Transforming Existing Datasets and Other File Formats
-----------------------------------------------------

.. class:: data(data, title=notitle, context={}, copy=1, replacedollar=1, columncallback="__column__", **columns)

   Wraps an existing :mod:`graph.data` instance *data* and derives new columns or
   mathematical expressions from its columns using the same keyword syntax as
   :class:`file`.

.. class:: conffile(filename, title=notitle, context={}, copy=1, replacedollar=1, columncallback="__column__", **columns)

   Reads tabular data from an INI-style configuration file parsed by Python's
   :mod:`configparser` module. Each ``[section]`` in the file becomes one data
   row, with ``option = value`` entries acting as named columns.

.. class:: cbdfile(filename, minrank=None, maxrank=None, title=notitle, context={}, copy=1, replacedollar=1, columncallback="__column__", **columns)

   Reads vector coastline/boundary segments from a CIA World DataBank (``.cbd``)
   binary file, filtering segments by rank between *minrank* and *maxrank*.

Analytical and Parametric Functions
-----------------------------------

.. class:: function(expression, title=notitle, min=None, max=None, points=100, context={})

   Generates data points by evaluating a mathematical function of one variable.

   * *expression*: String assignment specifying the dependent axis variable, the
     independent axis variable in parentheses, and the formula—for example,
     ``"y(x) = sin(x) / x"`` or ``"x(y) = y**2"``.
   * *min*, *max*: Domain of the independent variable. If omitted, the range of
     the corresponding graph axis is used automatically.
   * *points*: Number of sample points (default ``100``), spaced uniformly in
     graph coordinates (so a logarithmic axis is sampled logarithmically).
   * *title*: Legend title (defaults to *expression*; set to ``None`` to hide).
   * *context*: Dictionary of external Python variables or callables accessible
     within *expression*.

.. class:: paramfunction(varname, min, max, expression, title=notitle, points=100, context={})

   Generates data points from a parametric curve in 2D or 3D as the parameter
   *varname* varies linearly from *min* to *max* over *points* samples.

   * *expression*: Tuple assignment mapping the parameter *varname* to two or
     three axis coordinates—for example,
     ``"x, y = cos(t), sin(t)"`` or ``"x, y, z = cos(t), sin(t), 0.1*t"``.

Built-in Functions in Mathematical Expressions
----------------------------------------------

All mathematical expressions in :class:`file`, :class:`data`, :class:`function`,
and :class:`paramfunction` have access to every function and constant in Python's
standard :mod:`math` module (``sin``, ``cos``, ``tan``, ``asin``, ``acos``,
``atan``, ``atan2``, ``sinh``, ``cosh``, ``tanh``, ``exp``, ``log``, ``log10``,
``sqrt``, ``hypot``, ``pi``, ``e``, etc.), plus the following convenience
functions:

+------------------+------------------------------------------------------+
| Name             | Definition                                           |
+==================+======================================================+
| ``neg(x)``       | ``-x``                                               |
+------------------+------------------------------------------------------+
| ``abs(x)``       | ``abs(x)``                                           |
+------------------+------------------------------------------------------+
| ``sgn(x)``       | ``-1`` if ``x < 0`` else ``1``                       |
+------------------+------------------------------------------------------+
| ``sind(x)``      | ``math.sin(math.pi / 180 * x)`` (sine in degrees)    |
+------------------+------------------------------------------------------+
| ``cosd(x)``      | ``math.cos(math.pi / 180 * x)`` (cosine in degrees)  |
+------------------+------------------------------------------------------+
| ``tand(x)``      | ``math.tan(math.pi / 180 * x)`` (tangent in degrees) |
+------------------+------------------------------------------------------+
| ``asind(x)``     | ``180 / math.pi * math.asin(x)`` (in degrees)        |
+------------------+------------------------------------------------------+
| ``acosd(x)``     | ``180 / math.pi * math.acos(x)`` (in degrees)        |
+------------------+------------------------------------------------------+
| ``atand(x)``     | ``180 / math.pi * math.atan(x)`` (in degrees)        |
+------------------+------------------------------------------------------+
| ``norm(x, y)``   | ``math.hypot(x, y)``                                 |
+------------------+------------------------------------------------------+
| ``splitatvalue`` | See :func:`splitatvalue` below                       |
+------------------+------------------------------------------------------+

.. function:: splitatvalue(value, *splitpoints)

   Splits a coordinate value into discontinuous sections at *splitpoints* (useful
   with split axes; see :class:`graph.axis.split`). Returns a tuple
   ``(section, value)``. With a single split point ``s1``, ``section`` is ``0``
   when ``value <= s1`` and ``1`` otherwise. With multiple split points,
   ``section`` alternates between ``0``, ``None`` (ignored gap between the first
   and second split points), ``1``, ``None``, ``2``, etc.


.. module:: graph.style
   :synopsis: Plotting styles for graphs

Module :mod:`graph.style`: Graph Styles
=======================================

Graph styles control how data columns are rendered visually inside a graph. The
*styles* argument of :meth:`graph.graphxy.plot` accepts a list of style
instances, allowing you to combine multiple styles for a single dataset—for
example, ``[graph.style.line(), graph.style.symbol(), graph.style.errorbar()]``.

Hidden Data-Provider Styles
---------------------------

Several styles (:class:`pos`, :class:`range`, :class:`barpos`,
:class:`stackedbarpos`, and :class:`gridpos`) are *hidden styles*: they do not
draw marks themselves (except for optional baseline paths), but instead read data
columns and compute graph-coordinate positions in a shared ``sharedata`` object
consumed by visible styles. Because PyX automatically inserts the required
default hidden style whenever a visible style is used, you only need to
instantiate a hidden style explicitly when you want to customize its column name
mapping (*usenames*) or baseline (*fromvalue*).

.. class:: pos(usenames={}, epsilon=1e-10)

   Hidden style that reads one data column per graph axis (matching the axis name
   ``"x"``, ``"y"``, ``"z"``, or mapped via the dictionary *usenames*) and
   computes the normalized graph position. Points outside :math:`[0, 1]` by more
   than *epsilon* are marked as out of bounds.

.. class:: range(usenames={}, epsilon=1e-10)

   Hidden style that reads interval/uncertainty bounds for one or more axes ``X``
   (or mapped via *usenames*). For each axis ``X``, you can supply any of the
   following column combinations:

   +------------------+---------------------------------------------------------------+
   | Column Name(s)   | Meaning                                                       |
   +==================+===============================================================+
   | ``Xmin``, ``Xmax``| Explicit lower and upper bounds :math:`[X_{\min}, X_{\max}]`. |
   +------------------+---------------------------------------------------------------+
   | ``dX``           | Symmetric uncertainty :math:`X \pm \Delta X` (requires column |
   |                  | ``X``).                                                       |
   +------------------+---------------------------------------------------------------+
   | ``dXmin``,       | Asymmetric uncertainties :math:`[X - \Delta X_{\min},\;       |
   | ``dXmax``        | X + \Delta X_{\max}]` (requires column ``X``).                |
   +------------------+---------------------------------------------------------------+

Symbols, Lines, Impulses, and Error Bars
----------------------------------------

.. class:: symbol(symbol=changecross, size=0.2*unit.v_cm, symbolattrs=[])

   Draws a marker symbol at each data point. This is the default style for all
   tabular data sources (:class:`~graph.data.file`, :class:`~graph.data.values`,
   :class:`~graph.data.points`, etc.).

   * *symbol*: A symbol drawing callable with signature
     ``symbol(c, x_pt, y_pt, size_pt, attrs)`` or a changeable attribute cycling
     through symbol callables.
   * *size*: Visual diameter of the symbol (default ``0.2 * unit.v_cm``).
   * *symbolattrs*: Stroke/fill/color attributes merged with
     ``defaultsymbolattrs`` (``[deco.stroked]``).

   **Predefined symbol shapes** (class attributes on :class:`symbol`):

   * :attr:`symbol.cross` — diagonal cross :math:`\times` (stroke only)
   * :attr:`symbol.plus` — orthogonal plus :math:`+` (stroke only)
   * :attr:`symbol.square` — square (can be stroked, filled, or both)
   * :attr:`symbol.triangle` — equilateral triangle (can be stroked, filled, or both)
   * :attr:`symbol.circle` — circle (can be stroked, filled, or both)
   * :attr:`symbol.diamond` — diamond Rhombus (can be stroked, filled, or both)

   **Changeable symbol lists** (automatically cycle across datasets when the same
   :class:`symbol` instance is reused):

   * :attr:`symbol.changecross` — ``attr.changelist([cross, plus, square, triangle, circle, diamond])``
   * :attr:`symbol.changeplus` — ``attr.changelist([plus, square, triangle, circle, diamond, cross])``
   * :attr:`symbol.changesquare` — ``attr.changelist([square, triangle, circle, diamond, cross, plus])``
   * :attr:`symbol.changetriangle` — ``attr.changelist([triangle, circle, diamond, cross, plus, square])``
   * :attr:`symbol.changecircle` — ``attr.changelist([circle, diamond, cross, plus, square, triangle])``
   * :attr:`symbol.changediamond` — ``attr.changelist([diamond, cross, plus, square, triangle, circle])``
   * :attr:`symbol.changesquaretwice` — repeats each closed shape twice: ``[square, square, triangle, triangle, circle, circle, diamond, diamond]``
   * :attr:`symbol.changetriangletwice` — ``[triangle, triangle, circle, circle, diamond, diamond, square, square]``
   * :attr:`symbol.changecircletwice` — ``[circle, circle, diamond, diamond, square, square, triangle, triangle]``
   * :attr:`symbol.changediamondtwice` — ``[diamond, diamond, square, square, triangle, triangle, circle, circle]``

   **Changeable stroke/fill decorators** (useful in *symbolattrs* alongside the
   ``*twice`` symbol lists above):

   * :attr:`symbol.changestrokedfilled` — ``attr.changelist([deco.stroked, deco.filled])``
   * :attr:`symbol.changefilledstroked` — ``attr.changelist([deco.filled, deco.stroked])``

.. class:: line(lineattrs=[], epsilon=1e-10)

   Connects consecutive data points with geodesic segments clipped to the graph
   boundary. This is the default style for :class:`graph.data.function` and
   :class:`graph.data.paramfunction`.

   * *lineattrs*: Stroke attributes merged with ``defaultlineattrs``
     (``[line.changelinestyle]``).
   * :attr:`line.changelinestyle`:
     ``attr.changelist([style.linestyle.solid, style.linestyle.dashed, style.linestyle.dotted, style.linestyle.dashdotted])``.

.. class:: impulses(lineattrs=[], fromvalue=0, frompathattrs=[], valueaxisindex=1)

   Draws vertical (when ``valueaxisindex=1``) or horizontal (when
   ``valueaxisindex=0``) impulse stems from a baseline value *fromvalue* (or from
   the bottom/left graph boundary if ``fromvalue=None``) to each data point. When
   *fromvalue* is not ``None``, the baseline is stroked using *frompathattrs*.

.. class:: errorbar(size=0.1*unit.v_cm, errorbarattrs=[], epsilon=1e-10)

   Draws error bars with perpendicular end caps of visual length *size* using the
   interval bounds provided by :class:`range` (such as ``dy``, ``ymin``/``ymax``,
   or ``dymin``/``dymax``). Error bars extending outside the plot area are
   clipped to the graph boundary and their out-of-bounds caps are omitted.

Text Labels and Vector Arrows
-----------------------------

.. class:: text(textname="text", dxname=None, dyname=None, dxunit=0.3*unit.v_cm, dyunit=0.3*unit.v_cm, textdx=0*unit.v_cm, textdy=0.3*unit.v_cm, textattrs=[])

   Places a text label (read from column *textname*) at each data point, offset
   by ``(textdx, textdy)``—or by per-point offsets read from columns *dxname* and
   *dyname* multiplied by *dxunit* and *dyunit*. *textattrs* is merged with
   ``[text.halign.center, text.vshift.mathaxis]``.

.. class:: arrow(linelength=0.25*unit.v_cm, arrowsize=0.15*unit.v_cm, lineattrs=[], arrowattrs=[], arrowpos=0.5, epsilon=1e-10, decorator=deco.earrow)

   Draws 2D vector field arrows at each data point using two additional data
   columns:

   * ``size``: Scale factor multiplying both *linelength* and *arrowsize*.
   * ``angle``: Direction angle in degrees counter-clockwise from the positive
     *x*-axis.

   *arrowpos* controls how each arrow segment is anchored at the data point
   (``0`` starts at the point, ``0.5`` centers the arrow on the point, and ``1``
   ends at the point).

Histograms and Bar Charts
-------------------------

.. class:: histogram(lineattrs=[], steps=0, fromvalue=0, frompathattrs=[], fillable=0, rectkey=0, autohistogramaxisindex=0, autohistogrampointpos=0.5, epsilon=1e-10)

   Plots a 2D histogram.

   * *lineattrs*: Attributes used to draw the histogram outline (merged with
     ``[deco.stroked]``).
   * *steps*: When ``0`` (default), draws full vertical box outlines for each
     bin; when ``1``, draws only the upper step contour.
   * *fromvalue*, *frompathattrs*: Baseline value and stroke attributes for the
     histogram base (or ``fromvalue=None`` to start at the axis boundary).
   * *fillable*: When true, closes the histogram path along the baseline and
     graph boundaries so that passing ``deco.filled([...])`` in *lineattrs*
     cleanly fills the area under the histogram.
   * *rectkey*: When true, draws a filled/stroked rectangle in the graph legend
     instead of a line segment.

   **Specifying bin widths (equal vs. variable bin widths)**:

   * *Equal-width bins (automatic)*: If you supply only point coordinates ``x``
     and ``y`` (with at least two data points), :class:`histogram` automatically
     computes equal bin widths along axis *autohistogramaxisindex* (``0`` for
     *x*, ``1`` for *y*). *autohistogrampointpos* specifies where the given data
     coordinate sits within each bin: ``0.5`` (default) centers each bin on the
     data point, ``0`` places the bin to the right of the data point, and ``1``
     places the bin to the left.
   * *Variable-width bins (explicit ranges)*: To plot a histogram with unequal
     bin widths, supply range columns for the bin axis (such as ``xmin`` and
     ``xmax``, or ``x`` and ``dx``, as consumed by :class:`range`) alongside the
     height column ``y``. Whenever range columns are present for the bin axis,
     :class:`histogram` uses the exact interval :math:`[x_{\min}, x_{\max}]` of
     each bin.

.. class:: barpos(fromvalue=None, frompathattrs=[], epsilon=1e-10)

   Hidden style that computes bar positions along a :class:`graph.axis.bar` (or
   :class:`graph.axis.nestedbar`) axis. For a bar axis named ``X`` (e.g. ``x``),
   the categorical bar names are read from column ``Xname`` (e.g. ``xname``) and
   the bar heights are read from the continuous axis column (e.g. ``y``). To plot
   grouped bars side by side on a :class:`graph.axis.nestedbar` axis, pass a
   2-tuple ``(category, subcategory)`` in ``Xname`` (for example,
   ``xname="$1, 0"`` and ``xname="$1, 1"``).

.. class:: stackedbarpos(stackname, addontop=0, epsilon=1e-10)

   Hidden style that stacks a new bar series on top of the previous bar series,
   reading the upper coordinate (or the incremental height when ``addontop=1``)
   from column *stackname*.

.. class:: bar(barattrs=[], epsilon=1e-10, gradient=color.gradient.RedBlack)

   Draws filled rectangular (2D) or prism (3D) bars using the positions computed
   by :class:`barpos` or :class:`stackedbarpos`. *barattrs* is merged with
   ``[color.gradient.Rainbow, deco.stroked([color.gray.black])]``, so multiple
   bar series in a grouped or stacked bar chart automatically receive distinct
   colors from ``gradient.Rainbow``.

.. class:: changebar(barattrs=[])

   Variant of :class:`bar` that cycles the changeable attributes in *barattrs*
   from bar to bar *within* a single dataset rather than across multiple
   datasets.

Rectangles, Grids, Surfaces, and Density Plots
----------------------------------------------

.. class:: rect(colorname="color", gradient=color.gradient.Gray, coloraxis=None, keygraph=_autokeygraph, mincolor=None, maxcolor=None)

   Fills axis-aligned rectangles (defined by :class:`range` bounds on *x* and
   *y*) with colors mapped from column *colorname* via *gradient*.

   * *coloraxis*: Axis instance (defaults to :class:`graph.axis.linear`) mapping
     values in *colorname* to :math:`[0, 1]`.
   * *keygraph*: A :class:`graph.graphx` instance drawn beside the main graph as
     a color bar legend. By default, a vertical :class:`graph.graphx` is created
     automatically; pass ``keygraph=None`` to omit the color bar.
   * *mincolor*, *maxcolor*: Optional colors used for values falling below or
     above the range of *coloraxis*.

.. class:: gridpos(index1=0, index2=1, epsilon=1e-10)

   Hidden style that organizes point data along graph dimensions *index1* and
   *index2* into a structured 2D rectangular mesh.

.. class:: grid(gridlines1=1, gridlines2=1, gridattrs=[], epsilon=1e-10)

   Strokes a wireframe mesh in 2D or 3D along the first (*gridlines1*) and/or
   second (*gridlines2*) mesh directions provided by :class:`gridpos`.

.. class:: surface(gridlines1=0.05, gridlines2=0.05, gridcolor=None, backcolor=color.gray.black, mincolor=None, maxcolor=None, **kwargs)

   Draws a smoothly shaded 2D or 3D surface over the rectangular mesh provided by
   :class:`gridpos` using a Gouraud-shaded triangle mesh (each grid cell is
   subdivided into four triangles).

   * *gridlines1*, *gridlines2*, *gridcolor*: If *gridcolor* is set, draws narrow
     triangle strips of fractional width *gridlines1* and *gridlines2* in
     *gridcolor* along the cell boundaries.
   * *backcolor*: Color used for triangles facing away from the viewer (or
     ``None`` to color both sides identically).
   * **Coloring**: Accepts the same *colorname*, *gradient*, *coloraxis*,
     *keygraph*, *mincolor*, and *maxcolor* arguments as :class:`rect`. If no
     *colorname* column is present in the data, :class:`surface` automatically
     computes 3D lighting from the viewing angle and distance using
     :meth:`lighting`. Note that Gouraud shading meshes in PostScript/PDF require
     Gray, RGB, or CMYK colors; wrap HSB gradients in :class:`color.rgbgradient`
     or :class:`color.cmykgradient`.

.. class:: density(epsilon=1e-10, Nearest=False, **kwargs)

   Renders a 2D pseudocolor heatmap as an embedded :mod:`bitmap` image over an
   equidistantly spaced grid (in graph coordinates). Accepts the same
   *colorname*, *gradient*, *coloraxis*, *keygraph*, *mincolor*, and *maxcolor*
   arguments as :class:`rect`. Because :class:`density` embeds a compact raster
   bitmap rather than a triangle mesh, it produces much smaller files than
   :class:`surface` for large 2D grids and avoids PDF viewer anti-aliasing seams.


.. module:: graph.key
   :synopsis: Graph legends (keys)

Module :mod:`graph.key`: Graph Keys (Legends)
=============================================

.. class:: key(dist=0.2*unit.v_cm, pos="tr", hpos=None, vpos=None, hinside=1, vinside=1, hdist=0.6*unit.v_cm, vdist=0.4*unit.v_cm, symbolwidth=0.5*unit.v_cm, symbolheight=0.25*unit.v_cm, symbolspace=0.2*unit.v_cm, textattrs=[], columns=1, columndist=0.5*unit.v_cm, border=0.3*unit.v_cm, keyattrs=None)

   Creates a graph legend to be passed to the ``key`` argument of
   :class:`graph.graphxy` or :class:`graph.graphxyz`.

   * *pos*: Two-character alignment string positioning the legend relative to the
     plot box: vertical position ``"t"`` (top), ``"m"`` (middle), or ``"b"``
     (bottom) followed by horizontal position ``"l"`` (left), ``"c"`` (center),
     or ``"r"`` (right). Default is ``"tr"`` (top right).
   * *hpos*, *vpos*: Explicit relative horizontal and vertical positions in
     :math:`[0, 1]` (alternative to *pos*; cannot be combined with *pos*).
   * *hinside*, *vinside*: ``1`` (default) to place the legend inside the plot
     box, or ``0`` to place it outside the plot box (for example, ``pos="tl",
     hinside=0`` places the legend to the left of the top-left corner).
   * *hdist*, *vdist*: Horizontal and vertical margin between the legend and the
     reference corner of the plot box.
   * *dist*: Vertical baseline separation between consecutive entries.
   * *symbolwidth*, *symbolheight*, *symbolspace*: Dimensions of the style preview
     swatch and horizontal gap between the swatch and the dataset title.
   * *textattrs*: Text attributes applied to legend labels (merged with
     ``[text.vshift.mathaxis]``).
   * *columns*, *columndist*: Number of legend columns (default ``1``) and
     horizontal spacing between columns.
   * *keyattrs*, *border*: Optional draw attributes (such as
     ``[deco.filled([color.gray.white]), deco.stroked()]``) used to draw a box around
     the legend, padded on all sides by *border* (default ``0.3 * unit.v_cm``).
