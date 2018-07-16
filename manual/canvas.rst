
.. module:: canvas

====================
Module :mod:`canvas`
====================

.. sectionauthor:: Jörg Lehmann <joerg@pyx-project.org>


In addition it
contains the class ``canvas.clip`` which allows clipping of the output.


Class :class:`canvas`
---------------------

This is the basic class of the canvas module. Instances of this class collect
visual elements like paths, other canvases, TeX or LaTeX elements. A canvas may
also be embedded in another one using its ``insert`` method. This may be useful
when you want to apply a transformation on a whole set of operations.

.. class:: canvas(attrs=[], texrunner=None, ipython_bboxenlarge=1*unit.t_pt)

   Construct a new canvas, applying the given *attrs*, which can be instances of
   :class:`trafo.trafo`, :class:`canvas.clip`, :class:`style.strokestyle` or
   :class:`style.fillstyle`.  The *texrunner* argument can be used to specify the
   texrunner instance used for the :meth:`text` method of the canvas.  If not
   specified, it defaults to *text.defaulttexrunner*. *ipython_bboxenlarge* defines
   the `bboxenlarge` :class:`document.page` for IPython's `_repr_png_` and `_repr_svg_`.

Paths can be drawn on the canvas using one of the following methods:


.. method:: canvas.draw(path, attrs)

   Draws *path* on the canvas applying the given *attrs*. Depending on the
   *attrs* the path will be filled, stroked, ornamented, or a combination
   thereof. For the common first two cases the following two convenience
   functions are provided.


.. method:: canvas.fill(path, attrs=[])

   Fills the given *path* on the canvas applying the given *attrs*.


.. method:: canvas.stroke(path, attrs=[])

   Strokes the given *path* on the canvas applying the given *attrs*.

Arbitrary allowed elements like other :class:`canvas` instances can be inserted
in the canvas using


.. method:: canvas.insert(item, attrs=[])

   Inserts an instance of :class:`base.canvasitem` into the canvas.  If *attrs* are
   present, *item* is inserted into a new :class:`canvas` instance with *attrs*
   as arguments passed to its constructor. Then this :class:`canvas` instance
   is inserted itself into the canvas.

Text output on the canvas is possible using


.. method:: canvas.text(x, y, text, attrs=[])

   Inserts *text* at position (*x*, *y*) into the canvas applying *attrs*. This is
   a shortcut for ``insert(texrunner.text(x, y, text, attrs))``.

To group drawing operations, layers can be used:


.. method:: canvas.layer( name, above=None, below=None)

   This method creates or gets a layer with name *name*.

   A layer is a canvas itself and can be used to combine drawing operations for
   ordering purposes, i.e., what is above and below each other. The layer name
   *name* is a dotted string, where dots are used to form a hierarchy of layer
   groups. When inserting a layer, it is put on top of its layer group except
   when another layer instance of this group is specified by means of the
   parameters *above* or *below*.


The :class:`canvas` class provides access to the total geometrical size of its
element:


.. method:: canvas.bbox()

   Returns the bounding box enclosing all elements of the canvas (see Sect. :mod:`bbox`).

A canvas also allows to set its TeX runner:


.. method:: canvas.settexrunner(texrunner)

   Sets a new *texrunner* for the canvas.

The contents of the canvas can be written to a file using the following
convenience methods, which wrap the canvas into a single page document.


.. method:: canvas.writeEPSfile(file, **kwargs)

   Writes the canvas to *file* using the EPS format. *file* either has to provide a
   write method or it is used as a string containing the filename (the extension
   ``.eps`` is appended automatically, if it is not present). This method
   constructs a single page document, passing *kwargs* to the
   :class:`document.page` constructor for all *kwargs* starting with ``page_``
   (without this prefix) and calls the :meth:`writeEPSfile` method of this
   :class:`document.document` instance passing the *file* and all *kwargs*
   starting with ``write_`` (without this prefix).


.. method:: canvas.writePSfile(file, *args, **kwargs)

   Similar to :meth:`writeEPSfile` but using the PS format.


.. method:: canvas.writePDFfile(file, *args, **kwargs)

   Similar to :meth:`writeEPSfile` but using the PDF format.


.. method:: canvas.writeSVGfile(file, *args, **kwargs)

   Similar to :meth:`writeEPSfile` but using the SVG format.


.. method:: canvas.writetofile(filename, *args, **kwargs)

   Determine the file type (EPS, PS, PDF, or SVG) from the file extension of *filename*
   and call the corresponding write method with the given arguments *arg* and
   *kwargs*.


.. method:: canvas.pipeGS(device, resolution=100, gscmd="gs", gsoptions=[], textalphabits=4, graphicsalphabits=4, ciecolor=False, input="eps", **kwargs)

   This method pipes the content of a canvas to the ghostscript interpreter
   to generate other output formats. The output is returned by means of a
   python BytesIO object. *device* specifies a ghostscript output device by
   a string. Depending on the ghostscript configuration ``"png16"``,
   ``"png16m"``, ``"png256"``, ``"png48"``, ``"pngalpha"``, ``"pnggray"``,
   ``"pngmono"``, ``"jpeg"``, and ``"jpeggray"`` might be available among
   others. See the output of ``gs --help`` and the ghostscript documentation
   for more information.

   *resolution* specifies the resolution in dpi (dots per inch). *gs* is the
   name of the ghostscript executable. *gsoptions* is a list of additional
   options passed to the ghostscript interpreter. *textalphabits* and
   *graphicsalphabits* are convenient parameters to set the ``TextAlphaBits``
   and ``GraphicsAlphaBits`` options of ghostscript. The addition of these
   options can be skipped by setting their values to ``None``. *ciecolor* adds
   the ``-dUseCIEColor`` flag to improve the CMYK to RGB color conversion.
   *input* can be either ``"eps"`` or ``"pdf"`` to select the input type to be
   passed to ghostscript (note slightly different features available in the
   different input types regarding e.g. :mod:`epsfile` inclusion and
   transparency).

   *kwargs* are passed to the :meth:`writeEPSfile` method (not counting the *file*
   parameter), which is used to generate the input for ghostscript. By that you
   gain access to the :class:`document.page` constructor arguments.

.. method:: canvas.writeGSfile(filename=None, device=None, **kwargs)

   This method is similar to pipeGS, but the content is written into the file
   *filename*. If filename is None it is auto-guessed from the script name. If
   filename is "-", the output is written to stdout. In both cases, a device
   needs to be specified to define the format (and the file suffix in case the
   filename is created from the script name).

   If device is None, but a filename with suffix is given, PNG files will
   be written using the png16m device and JPG files using the jpeg device.

   All other arguments are identical to those of the :meth:`canvas.pipeGS`.

For more information about the possible arguments of the :class:`document.page`
constructor, we refer to Sect. :mod:`document`.


Class :class:`clip`
---------------------

In addition the canvas module contains the class ``canvas.clip`` which allows for
clipping of the output by passing a clipping instance to the attrs parameter of
the canvas constructor.
