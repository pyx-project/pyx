# -*- encoding: utf-8 -*-
#
#
# Copyright (C) 2002-2012 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2002-2012 André Wobst <wobsta@users.sourceforge.net>
#
# This file is part of PyX (http://pyx.sourceforge.net/).
#
# PyX is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# PyX is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyX; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

"""The canvas module provides a PostScript canvas class and related classes

A canvas holds a collection of all elements and corresponding attributes to be
displayed. """

import cStringIO, os, sys, string, tempfile, warnings
import attr, canvasitem, deco, deformer, document, font, pycompat, style, trafo
import bbox as bboxmodule

def _wrappedindocument(method):
    def wrappedindocument(self, file=None, **kwargs):
        page_kwargs = {}
        write_kwargs = {}
        for name, value in kwargs.items():
            if name.startswith("page_"):
                page_kwargs[name[5:]] = value
            elif name.startswith("write_"):
                write_kwargs[name[6:]] = value
            else:
                warnings.warn("Keyword argument %s of %s method should be prefixed with 'page_'" %
                                (name, method.__name__), DeprecationWarning)
                page_kwargs[name] = value
        d = document.document([document.page(self, **page_kwargs)])
        self.__name__ = method.__name__
        self.__doc__ = method.__doc__
        return method(d, file, **write_kwargs)
    return wrappedindocument

#
# clipping class
#

class clip(canvasitem.canvasitem):

    """class for use in canvas constructor which clips to a path"""

    def __init__(self, path):
        """construct a clip instance for a given path"""
        self.path = path

    def bbox(self):
        # as a canvasitem a clipping path has NO influence on the bbox...
        return bboxmodule.empty()

    def clipbbox(self):
        # ... but for clipping, we nevertheless need the bbox
        return self.path.bbox()

    def processPS(self, file, writer, context, registry, bbox):
        file.write("newpath\n")
        self.path.outputPS(file, writer)
        file.write("clip\n")

    def processPDF(self, file, writer, context, registry, bbox):
        self.path.outputPDF(file, writer)
        file.write("W n\n")


#
# general canvas class
#

class canvas(canvasitem.canvasitem):

    """a canvas holds a collection of canvasitems"""

    def __init__(self, attrs=None, texrunner=None):

        """construct a canvas

        The canvas can be modfied by supplying a list of attrs, which have
        to be instances of one of the following classes:
         - trafo.trafo (leading to a global transformation of the canvas)
         - canvas.clip (clips the canvas)
         - style.strokestyle, style.fillstyle (sets some global attributes of the canvas)

        Note that, while the first two properties are fixed for the
        whole canvas, the last one can be changed via canvas.set().

        The texrunner instance used for the text method can be specified
        using the texrunner argument. It defaults to text.defaulttexrunner

        """

        self.items = []
        self.trafo = trafo.trafo()
        self.clipbbox = None
        self.layers = {}
        if attrs is None:
            attrs = []
        if texrunner is not None:
            self.texrunner = texrunner
        else:
            # prevent cyclic imports
            import text
            self.texrunner = text.defaulttexrunner

        attr.checkattrs(attrs, [trafo.trafo_pt, clip, style.strokestyle, style.fillstyle])
        # We have to reverse the trafos such that the PostScript concat operators
        # are in the right order. Correspondingly, we below multiply the current self.trafo
        # from the right.
        # Note that while for the stroke and fill styles the order doesn't matter at all,
        # this is not true for the clip operation.
        for aattr in attrs[::-1]:
            if isinstance(aattr, trafo.trafo_pt):
                self.trafo = self.trafo * aattr
            elif isinstance(aattr, clip):
                if self.clipbbox is None:
                    self.clipbbox = aattr.clipbbox().transformed(self.trafo)
                else:
                    self.clippbox *= aattr.clipbbox().transformed(self.trafo)
            self.items.append(aattr)

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        return self.items[i]

    def _repr_png_(self):
        """
        Automatically represent as PNG graphic when evaluated in IPython notebook.
        """
        return self.pipeGS(device="png16m", seekable=True).getvalue()

    def bbox(self):
        """returns bounding box of canvas

        Note that this bounding box doesn't take into account the linewidths, so
        is less accurate than the one used when writing the output to a file.
        """
        obbox = bboxmodule.empty()
        for cmd in self.items:
            obbox += cmd.bbox()

        # transform according to our global transformation and
        # intersect with clipping bounding box (which has already been
        # transformed in canvas.__init__())
        obbox.transform(self.trafo)
        if self.clipbbox is not None:
            obbox *= self.clipbbox
        return obbox

    def processPS(self, file, writer, context, registry, bbox):
        context = context()
        if self.items:
            file.write("gsave\n")
            nbbox = bboxmodule.empty()
            for item in self.items:
                item.processPS(file, writer, context, registry, nbbox)
            # update bounding bbox
            nbbox.transform(self.trafo)
            if self.clipbbox is not None:
                nbbox *= self.clipbbox
            bbox += nbbox
            file.write("grestore\n")

    def processPDF(self, file, writer, context, registry, bbox):
        context = context()
        context.trafo = context.trafo * self.trafo
        if self.items:
            file.write("q\n") # gsave
            nbbox = bboxmodule.empty()
            for item in self.items:
                if isinstance(item, style.fillstyle):
                    context.fillstyles.append(item)
                if not writer.text_as_path:
                    if isinstance(item, font.text_pt):
                        if not context.textregion:
                            file.write("BT\n")
                            context.textregion = 1
                    else:
                        if context.textregion:
                            file.write("ET\n")
                            context.textregion = 0
                            context.selectedfont = None
                item.processPDF(file, writer, context, registry, nbbox)
            if context.textregion:
                file.write("ET\n")
                context.textregion = 0
                context.selectedfont = None
            # update bounding bbox
            nbbox.transform(self.trafo)
            if self.clipbbox is not None:
                nbbox *= self.clipbbox
            bbox += nbbox
            file.write("Q\n") # grestore

    def layer(self, name, above=None, below=None):
        """create or get a layer with name

        A layer is a canvas itself and can be used to combine drawing
        operations for ordering purposes, i.e., what is above and below each
        other. The layer name is a dotted string, where dots are used to form
        a hierarchy of layer groups. When inserting a layer, it is put on top
        of its layer group except when another layer of this group is specified
        by means of the parameters above or below.

        """
        try:
            group, layer = name.split(".", 1)
        except ValueError:
            if not name in self.layers:
                self.layers[name] = self.insert(canvas(texrunner=self.texrunner), after=above, before=below)
            return self.layers[name]
        else:
            if not group in self.layers:
                self.layers[group] = self.insert(canvas(texrunner=self.texrunner))
            return self.layers[group].layer(layer, above=above, below=below)

    def insert(self, item, attrs=None, before=None, after=None):
        """insert item in the canvas.

        If attrs are passed, a canvas containing the item is inserted applying
        attrs. If one of before or after is not None, the new item is
        positioned accordingly in the canvas.

        returns the item, possibly wrapped in a canvas

        """

        if not isinstance(item, canvasitem.canvasitem):
            raise ValueError("only instances of canvasitem.canvasitem can be inserted into a canvas")

        if attrs:
            sc = canvas(attrs)
            sc.insert(item)
            item = sc

        if before is not None:
            if after:
                raise ValueError("before and after cannot be specified at the same time")
            self.items.insert(self.items.index(before), item)
        elif after is not None:
            self.items.insert(self.items.index(after)+1, item)
        else:
            self.items.append(item)
        return item

    def draw(self, path, attrs):
        """draw path on canvas using the style given by args

        The argument attrs consists of PathStyles, which modify
        the appearance of the path, PathDecos, which add some new
        visual elements to the path, or trafos, which are applied
        before drawing the path.

        """

        attrs = attr.mergeattrs(attrs)
        attr.checkattrs(attrs, [deco.deco, deformer.deformer, style.fillstyle, style.strokestyle, style.fillrule])

        for adeformer in attr.getattrs(attrs, [deformer.deformer]):
            path = adeformer.deform(path)

        styles = attr.getattrs(attrs, [style.fillstyle, style.strokestyle])
        fillrule, = attr.getattrs(attrs, [style.fillrule]) or [style.fillrule.nonzero_winding]
        dp = deco.decoratedpath(path, styles=styles, fillrule=fillrule)

        # add path decorations and modify path accordingly
        for adeco in attr.getattrs(attrs, [deco.deco]):
            adeco.decorate(dp, self.texrunner)

        self.insert(dp)

    def stroke(self, path, attrs=[]):
        """stroke path on canvas using the style given by args

        The argument attrs consists of PathStyles, which modify
        the appearance of the path, PathDecos, which add some new
        visual elements to the path, or trafos, which are applied
        before drawing the path.

        """

        self.draw(path, [deco.stroked]+list(attrs))

    def fill(self, path, attrs=[]):
        """fill path on canvas using the style given by args

        The argument attrs consists of PathStyles, which modify
        the appearance of the path, PathDecos, which add some new
        visual elements to the path, or trafos, which are applied
        before drawing the path.

        """

        self.draw(path, [deco.filled]+list(attrs))

    def settexrunner(self, texrunner):
        """sets the texrunner to be used to within the text and text_pt methods"""

        self.texrunner = texrunner

    def text(self, x, y, atext, *args, **kwargs):
        """insert a text into the canvas

        inserts a textbox created by self.texrunner.text into the canvas

        returns the inserted textbox"""

        return self.insert(self.texrunner.text(x, y, atext, *args, **kwargs))


    def text_pt(self, x, y, atext, *args):
        """insert a text into the canvas

        inserts a textbox created by self.texrunner.text_pt into the canvas

        returns the inserted textbox"""

        return self.insert(self.texrunner.text_pt(x, y, atext, *args))

    writeEPSfile = _wrappedindocument(document.document.writeEPSfile)
    writePSfile = _wrappedindocument(document.document.writePSfile)
    writePDFfile = _wrappedindocument(document.document.writePDFfile)
    writetofile = _wrappedindocument(document.document.writetofile)


    def _gscmd(self, device, filename, resolution=100, gscmd="gs", gsoptions="",
               textalphabits=4, graphicsalphabits=4, ciecolor=False, **kwargs):

        allowed_chars = string.ascii_letters + string.digits + "_-./"
        if filename.translate(string.maketrans("", ""), allowed_chars):
            raise ValueError("for security reasons, only characters, digits and the characters '_-./' are allowed in filenames")

        gscmd += " -dEPSCrop -dNOPAUSE -dQUIET -dBATCH -r%i -sDEVICE=%s -sOutputFile=%s" % (resolution, device, filename)
        if gsoptions:
            gscmd += " %s" % gsoptions
        if textalphabits is not None:
            gscmd += " -dTextAlphaBits=%i" % textalphabits
        if graphicsalphabits is not None:
            gscmd += " -dGraphicsAlphaBits=%i" % graphicsalphabits
        if ciecolor:
            gscmd += " -dUseCIEColor"

        return gscmd, kwargs

    def writeGSfile(self, filename=None, device=None, input="eps", **kwargs):
        """
        convert EPS or PDF output to a file via Ghostscript

        If filename is None it is auto-guessed from the script name. If
        filename is "-", the output is written to stdout. In both cases, a
        device needs to be specified to define the format.

        If device is None, but a filename with suffix is given, PNG files will
        be written using the png16m device and JPG files using the jpeg device.
        """
        if filename is None:
            if not sys.argv[0].endswith(".py"):
                raise RuntimeError("could not auto-guess filename")
            if device.startswith("png"):
                filename = sys.argv[0][:-2] + "png"
            elif device.startswith("jpeg"):
                filename = sys.argv[0][:-2] + "jpg"
            else:
                filename = sys.argv[0][:-2] + device
        if device is None:
            if filename.endswith(".png"):
                device = "png16m"
            elif filename.endswith(".jpg"):
                device = "jpeg"
            else:
                raise RuntimeError("could not auto-guess device")

        gscmd, kwargs = self._gscmd(device, filename, **kwargs)

        if input == "eps":
            gscmd += " -"
            stdin = pycompat.popen(gscmd, "wb")
            self.writeEPSfile(stdin, **kwargs)
            stdin.close()
        elif input == "pdf":
            # PDF files need to be accesible by random access and thus we need to create
            # a temporary file
            fd, fname = tempfile.mkstemp()
            f = os.fdopen(fd, "wb")
            gscmd += " %s" % fname
            self.writePDFfile(f, **kwargs)
            f.close()
            os.system(gscmd)
            os.unlink(fname)
        else:
            raise RuntimeError("input 'eps' or 'pdf' expected")


    def pipeGS(self, device, input="eps", seekable=False, **kwargs):
        """
        returns a pipe with the Ghostscript output of the EPS or PDF of the canvas

        If seekable is True, a StringIO instance will be returned instead of a
        pipe to allow random access.
        """

        gscmd, kwargs = self._gscmd(device, "-", **kwargs)

        if input == "eps":
            gscmd += " -"
            # we can safely ignore that the input and output pipes could block each other,
            # because Ghostscript has to read the full input before writing the output
            stdin, stdout = pycompat.popen2(gscmd)
            self.writeEPSfile(stdin, **kwargs)
            stdin.close()
        elif input == "pdf":
            # PDF files need to be accesible by random access and thus we need to create
            # a temporary file
            fd, fname = tempfile.mkstemp()
            f = os.fdopen(fd, "wb")
            gscmd += " %s" % fname
            self.writePDFfile(f, **kwargs)
            f.close()
            stdout = pycompat.popen(gscmd, "rb")
            os.unlink(fname)
        else:
            raise RuntimeError("input 'eps' or 'pdf' expected")

        if seekable:
            # the read method of a pipe object may not return the full content
            f = cStringIO.StringIO()
            while True:
                data = stdout.read()
                if not data:
                   break
                f.write(data)
            stdout.close()
            f.seek(0)
            return f
        else:
            return stdout
