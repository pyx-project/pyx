.. _canvas:

******
Canvas
******

.. module:: canvas
   :synopsis: Canvas container and drawing operations

A :class:`canvas` is the central workspace in PyX. It acts both as a drawing
surface—providing methods to stroke, fill, and draw paths and to typeset
text—and as a hierarchical container that groups canvas items (paths, text boxes,
sub-canvases, bitmaps, and embedded EPS, PDF, or SVG files) with shared visual
attributes, transformations, clipping paths, and drawing layers.


Working with canvases
=====================

Drawing and grouping
--------------------

Every drawing operation on a canvas (:meth:`canvas.stroke`, :meth:`canvas.fill`,
:meth:`canvas.draw`, :meth:`canvas.text`) creates a :class:`baseclasses.canvasitem`
and inserts it into the canvas via :meth:`canvas.insert`, returning the inserted
item.

Because a :class:`canvas` is itself a :class:`baseclasses.canvasitem`, you can
create sub-canvases, draw on them in local coordinates, and insert them into a
parent canvas with transformations or styles applied to the entire group::

   from pyx import *

   # Create a reusable sub-canvas in local coordinates
   badge = canvas.canvas()
   badge.fill(path.circle(0, 0, 0.5), [color.rgb.red])
   badge.text(0, 0, "1", [text.halign.center, text.valign.middle, color.gray.white])

   # Insert the sub-canvas multiple times at different positions and scales
   c = canvas.canvas()
   c.insert(badge, [trafo.translate(1, 1)])
   c.insert(badge, [trafo.scale(1.5), trafo.translate(3, 1)])

   c.writePDFfile("badges")


Layers
------

By default, items on a canvas are drawn in the exact order in which they are
inserted (later items paint over earlier items). When constructing complex
figures, it is often convenient to organize drawing operations into named
*layers* (such as ``"background"``, ``"fill"``, ``"main"``, ``"labels"``) whose
back-to-front order is independent of when individual items are added.

The :meth:`canvas.layer` method creates or retrieves a sub-canvas associated with
a layer name and allows you to position it relative to existing layers using the
*above* and *below* parameters::

   c = canvas.canvas()
   bg = c.layer("background")
   fg = c.layer("foreground", above="background")

   # Even if we draw on fg first and bg second, bg is rendered behind fg
   fg.text(1, 1, "Foreground text", [text.halign.center, text.valign.middle])
   bg.fill(path.rect(0, 0.5, 2, 1), [color.rgb.yellow])


Clipping
--------

A canvas can be clipped to the interior of an arbitrary closed :class:`path.path`
by passing a :class:`clip` instance in the canvas constructor's *attrs* list::

   clipped = canvas.canvas([canvas.clip(path.circle(1, 1, 1))])
   clipped.fill(path.rect(0, 0, 2, 2), [color.rgb.blue])

   c = canvas.canvas()
   c.insert(clipped)


Class :class:`canvas`
=====================

.. class:: canvas(attrs=[], textengine=None)

   Constructs a new canvas.

   - *attrs*: Optional list of canvas-wide attributes applied to all contents of
     the canvas. Allowed attributes are :class:`style.strokestyle`,
     :class:`style.fillstyle` (including :class:`color.color` and
     :class:`pattern.pattern`), :class:`trafo.trafo_pt`, and :class:`clip`.
   - *textengine*: Optional text engine instance (such as a custom
     :class:`text.TexEngine`, :class:`text.LatexEngine`, or
     :class:`text.UnicodeEngine`) used by :meth:`text` and :meth:`text_pt` on
     this canvas. When ``None`` (the default), ``text.defaulttextengine`` is used
     at the time :meth:`text` is called.

   .. attribute:: items

      List of :class:`baseclasses.canvasitem` objects contained in the canvas.

   .. attribute:: layers

      Dictionary mapping layer names to their corresponding sub-canvas instances.

   .. attribute:: trafo

      The cumulative :class:`trafo.trafo_pt` transformation applied to the
      canvas.

   .. method:: bbox()

      Returns the enclosing :class:`bbox.bbox` of all items in the canvas (taking
      canvas transformations and any :class:`clip` path into account). Note that
      for stroked paths, the bounding box reflects the geometric path rather than
      the stroke width.

   .. method:: draw(path, attrs)

      Draws *path* on the canvas according to the attributes in *attrs*, which
      may contain :class:`baseclasses.deformer`, :class:`baseclasses.deco`,
      :class:`style.strokestyle`, :class:`style.fillstyle`, and
      :class:`trafo.trafo_pt` instances. Returns the inserted
      :class:`deco.decoratedpath` canvas item.

   .. method:: stroke(path, attrs=[])

      Strokes *path* on the canvas; equivalent to
      ``self.draw(path, [deco.stroked] + list(attrs))``. Returns the inserted
      :class:`deco.decoratedpath` canvas item.

   .. method:: fill(path, attrs=[])

      Fills *path* on the canvas; equivalent to
      ``self.draw(path, [deco.filled] + list(attrs))``. Returns the inserted
      :class:`deco.decoratedpath` canvas item.

   .. method:: insert(item, attrs=[])

      Inserts *item* (an instance of :class:`baseclasses.canvasitem`, such as
      another :class:`canvas`, a :class:`text.textbox_pt`, a
      :class:`bitmap.bitmap`, an :class:`epsfile.epsfile`, a
      :class:`pdffile.pdffile`, or an :class:`svgfile.svgfile`) into the canvas.
      If *attrs* is non-empty, *item* is wrapped in a sub-canvas with *attrs*
      applied. Returns *item*.

   .. method:: layer(name, above=None, below=None)

      Creates or retrieves the layer sub-canvas identified by the string *name*.
      Dotted names (such as ``"axes.ticks"``) create nested sub-layers inside the
      parent layer ``"axes"``.

      - *above*: Name of an existing layer immediately above which the layer
        should be positioned.
      - *below*: Name of an existing layer immediately below which the layer
        should be positioned (cannot be combined with *above*).

      Returns the :class:`canvas` instance representing the layer.

   .. method:: text(x, y, expr, textattrs=[], **kwargs)
               text_pt(x_pt, y_pt, expr, textattrs=[], **kwargs)

      Typesets *expr* at :math:`(x, y)` (in PyX user lengths or points) using the
      canvas's text engine, inserts the resulting text box into the canvas, and
      returns it. See :meth:`text.SingleEngine.text_pt` for details on
      *textattrs* and *kwargs*.

   .. method:: settextengine(textengine)

      Sets the text engine (:class:`text.TexEngine`, :class:`text.LatexEngine`,
      or :class:`text.UnicodeEngine`) to be used by subsequent :meth:`text` and
      :meth:`text_pt` calls on this canvas.


Output and Ghostscript conversion methods
-----------------------------------------

For single-page figures, :class:`canvas` provides shortcut methods that wrap the
canvas in a :class:`document.page` and a single-page :class:`document.document`
and write the output directly. Any keyword arguments accepted by
:class:`document.page` (such as ``paperformat``, ``rotated``, ``centered``,
``fittosize``, ``margin``, ``bboxenlarge``, ``bbox``) as well as any keyword
arguments accepted by the respective writer (such as ``title``, ``stripfonts``,
``textaspath``, ``writebbox``; see :ref:`document`) can be passed directly to
these methods:

   .. method:: writeEPSfile(file=None, **kwargs)
               writePSfile(file=None, **kwargs)
               writePDFfile(file=None, **kwargs)
               writeSVGfile(file=None, **kwargs)

      Writes the canvas to an EPS, PostScript, PDF, or SVG file. *file* can be a
      filename string (the extension ``.eps``, ``.ps``, ``.pdf``, or ``.svg`` is
      appended automatically if omitted), a binary writable stream, ``"-"`` to
      write to ``sys.stdout.buffer``, or ``None`` to derive the filename
      automatically from ``sys.argv[0]``.

   .. method:: writetofile(filename, **kwargs)

      Determines the output format from the extension of *filename* (``.eps``,
      ``.ps``, ``.pdf``, or ``.svg``) and writes the canvas accordingly.

   .. method:: pipeGS(filename=None, device="png16m", resolution=100, gs="gs", gsoptions=[], textalphabits=4, graphicsalphabits=4, ciecolor=False, input="eps", **kwargs)

      Renders the canvas using Ghostscript (``gs``) into any output format
      supported by Ghostscript (such as PNG or JPEG).

      - *filename*: Output filename. If *filename* does not end with a file
        extension and *device* starts with ``"png"`` or ``"jpeg"``, the extension
        ``.png`` or ``.jpg`` is appended automatically. If *filename* is ``None``,
        the base name is derived from ``sys.argv[0]``. If *filename* is ``"-"``,
        Ghostscript writes to standard output and :meth:`pipeGS` returns the
        resulting output as a :class:`bytes` object!
      - *device*: Ghostscript output device (default ``"png16m"`` for 24-bit RGB
        PNG; use e.g. ``"pngalpha"`` for PNG with transparent background or
        ``"jpeg"`` for JPEG).
      - *resolution*: Rendering resolution in DPI (default ``100``).
      - *gs*: Ghostscript executable name (default ``"gs"``).
      - *gsoptions*: Additional command-line option strings passed to Ghostscript.
      - *textalphabits*, *graphicsalphabits*: Antialiasing subsampling factors
        (default ``4``; pass ``None`` to omit).
      - *ciecolor*: When ``True``, passes ``-dUseCIEColor`` to Ghostscript.
      - *input*: Format piped from PyX into Ghostscript: ``"eps"`` (default) or
        ``"pdf"``.
      - *kwargs*: Additional keyword arguments forwarded to :class:`document.page`
        and the EPS/PDF writer.


Class :class:`clip`
===================

.. class:: clip(path)

   Constructs a clipping attribute from the closed :class:`path.path` *path*.
   When passed in the *attrs* list of :class:`canvas`, all drawing inside that
   canvas is restricted to the interior of *path*.
