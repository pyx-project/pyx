
.. module:: canvas

====================
Module :mod:`canvas`
====================

.. sectionauthor:: Jörg Lehmann <joergl@users.sourceforge.net>


One of the central modules for the PostScript access in PyX is named ``canvas``.
Besides providing the class ``canvas``, which presents a collection of visual
elements like paths, other canvases, TeX or LaTeX elements, it contains the
class ``canvas.clip`` which allows clipping of the output.

A canvas may also be embedded in another one using its ``insert`` method. This
may be useful when you want to apply a transformation on a whole set of
operations..


Class canvas
------------

This is the basic class of the canvas module, which serves to collect various
graphical and text elements you want to write eventually to an (E)PS file.


.. class:: canvas(attrs=[], texrunner=None)

   Construct a new canvas, applying the given *attrs*, which can be instances of
   :class:`trafo.trafo`, :class:`canvas.clip`, :class:`style.strokestyle` or
   :class:`style.fillstyle`.  The *texrunner* argument can be used to specify the
   texrunner instance used for the :meth:`text` method of the canvas.  If not
   specified, it defaults to *text.defaulttexrunner*.

Paths can be drawn on the canvas using one of the following methods:


.. method:: canvas.draw(path, attrs)

   Draws *path* on the canvas applying the given *attrs*.


.. method:: canvas.fill(path, attrs=[])

   Fills the given *path* on the canvas applying the given *attrs*.


.. method:: canvas.stroke(path, attrs=[])

   Strokes the given *path* on the canvas applying the given *attrs*.

Arbitrary allowed elements like other :class:`canvas` instances can be inserted
in the canvas using


.. method:: canvas.insert(item, attrs=[])

   Inserts an instance of :class:`base.canvasitem` into the canvas.  If *attrs* are
   present, *item* is inserted into a new :class:`canvas`\ instance with *attrs* as
   arguments passed to its constructor is created. Then this :class:`canvas`
   instance is inserted itself into the canvas.

Text output on the canvas is possible using


.. method:: canvas.text(x, y, text, attrs=[])

   Inserts *text* at position (*x*, *y*) into the canvas applying *attrs*. This is
   a shortcut for ``insert(texrunner.text(x, y, text, attrs))``).

The :class:`canvas` class provides access to the total geometrical size of its
element:


.. method:: canvas.bbox()

   Returns the bounding box enclosing all elements of the canvas.

A canvas also allows one to set its TeX runner:


.. method:: canvas.settexrunner(texrunner)

   Sets a new *texrunner* for the canvas.

The contents of the canvas can be written using the following two convenience
methods, which wrap the canvas into a single page document.


.. method:: canvas.writeEPSfile(file, *args, **kwargs)

   Writes the canvas to *file* using the EPS format. *file* either has to provide a
   write method or it is used as a string containing the filename (the extension
   ``.eps`` is appended automatically, if it is not present). This method
   constructs a single page document, passing *args* and *kwargs* to the
   :class:`document.page` constructor and the calls the :meth:`writeEPSfile` method
   of this :class:`document.document` instance passing the *file*.


.. method:: canvas.writePSfile(file, *args, **kwargs)

   Similar to :meth:`writeEPSfile` but using the PS format.


.. method:: canvas.writePDFfile(file, *args, **kwargs)

   Similar to :meth:`writeEPSfile` but using the PDF format.


.. method:: canvas.writetofile(filename, *args, **kwargs)

   Determine the file type (EPS, PS, or PDF) from the file extension of *filename*
   and call the corresponding write method with the given arguments *arg* and
   *kwargs*.


.. method:: canvas.pipeGS(filename="-", device=None, resolution=100, gscommand="gs", gsoptions="", textalphabits=4, graphicsalphabits=4, ciecolor=False, input="eps", **kwargs)

   This method pipes the content of a canvas to the ghostscript interpreter
   directly to generate other output formats. At least *filename* or *device* must
   be set. *filename* specifies the name of the output file. No file extension will
   be added to that name in any case. When no *filename* is specified, the output
   is written to stdout. *device* specifies a ghostscript output device by a
   string. Depending on your ghostscript configuration ``"png16"``, ``"png16m"``,
   ``"png256"``, ``"png48"``, ``"pngalpha"``, ``"pnggray"``, ``"pngmono"``,
   ``"jpeg"``, and ``"jpeggray"`` might be available among others. See the output
   of ``gs --help`` and the ghostscript documentation for more information. When
   *filename* is specified but the device is not set, ``"png16m"`` is used when the
   filename ends in ``.png`` and ``"jpeg"`` is used when the filename ends in
   ``.jpg``.

   *resolution* specifies the resolution in dpi (dots per inch). *gscmd* is the
   command to be used to invoke ghostscript. *gsoptions* are an option string
   passed to the ghostscript interpreter. *textalphabits* are *graphicsalphabits*
   are conventient parameters to set the ``TextAlphaBits`` and
   ``GraphicsAlphaBits`` options of ghostscript. You can skip the addition of those
   option by set their value to ``None``. *ciecolor* adds the ``-dUseCIEColor``
   flag to improve the CMYK to RGB color conversion. *input* can be either
   ``"eps"`` or ``"pdf"`` to select the input type to be passed to ghostscript
   (note slightly different features available in the different input types).

   *kwargs* are passed to the :meth:`writeEPSfile` method (not counting the *file*
   parameter), which is used to generate the input for ghostscript. By that you
   gain access to the :class:`document.page` constructor arguments.

For more information about the possible arguments of the :class:`document.page`
constructor, we refer to Sect. :mod:`document`.

