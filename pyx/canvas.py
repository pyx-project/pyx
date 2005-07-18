#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2002-2005 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2002-2005 André Wobst <wobsta@users.sourceforge.net>
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

#
# canvas item
#

class canvasitem:

    """Base class for everything which can be inserted into a canvas"""

    def bbox(self):
        """return bounding box of canvasitem or None"""
        pass
    
    def registerPS(self, registry):
        """register resources needed for the canvasitem in the PS registry"""
        pass

    def registerPDF(self, registry):
        """register resources needed for the canvasitem in the PDF registry"""
        pass

    def outputPS(self, file, writer, context):
        """write PS code corresponding to canvasitem to file

        - file has to provide a write(string) method
        - writer is the PSwriter used for the output
        - context is used for keeping track of the graphics state, in particular
        for the emulation of PS behaviour regarding fill and stroke styles, for
        keeping track of the currently selected font as well as of text regions.
        """
        pass

    def outputPDF(self, file, writer, context):
        """write PDF code corresponding to canvasitem to file using the given writer
        and context.

        - file has to provide a write(string) method
        - writer contains properties like whether streamcompression is used.
        - context is used for keeping track of the graphics state, in particular
        for the emulation of PS behaviour regarding fill and stroke styles, for
        keeping track of the currently selected font as well as of text regions.
        """
        pass




import attr, deco, deformer, document, style, trafo, type1font


#
# clipping class
#

class clip(canvasitem):

    """class for use in canvas constructor which clips to a path"""

    def __init__(self, path):
        """construct a clip instance for a given path"""
        self.path = path

    def bbox(self):
        # as a canvasitem a clipping path has NO influence on the bbox...
        return None

    def clipbbox(self):
        # ... but for clipping, we nevertheless need the bbox
        return self.path.bbox()

    def outputPS(self, file, writer, context):
        file.write("newpath\n")
        self.path.outputPS(file, writer, context)
        file.write("clip\n")

    def outputPDF(self, file, writer, context):
        self.path.outputPDF(file, writer, context)
        file.write("W n\n")


#
# general canvas class
#

class _canvas(canvasitem):

    """a canvas holds a collection of canvasitems"""

    def __init__(self, attrs=[], texrunner=None):

        """construct a canvas

        The canvas can be modfied by supplying args, which have
        to be instances of one of the following classes:
         - trafo.trafo (leading to a global transformation of the canvas)
         - canvas.clip (clips the canvas)
         - style.strokestyle, style.fillstyle (sets some global attributes of the canvas)

        Note that, while the first two properties are fixed for the
        whole canvas, the last one can be changed via canvas.set().

        The texrunner instance used for the text method can be specified
        using the texrunner argument. It defaults to text.defaulttexrunner

        """

        self.items     = []
        self.trafo     = trafo.trafo()
        self.clipbbox  = None
        if texrunner is not None:
            self.texrunner = texrunner
        else:
            # prevent cyclic imports
            import text
            self.texrunner = text.defaulttexrunner

        for attr in attrs:
            if isinstance(attr, trafo.trafo_pt):
                self.trafo = self.trafo*attr
                self.items.append(attr)
            elif isinstance(attr, clip):
                if self.clipbbox is None:
                    self.clipbbox = attr.clipbbox().transformed(self.trafo)
                else:
                    self.clippbox *= attr.clipbbox().transformed(self.trafo)
                self.items.append(attr)
            else:
                self.set([attr])

    def bbox(self):
        """returns bounding box of canvas"""
        obbox = None
        for cmd in self.items:
            abbox = cmd.bbox()
            if obbox is None:
                obbox = abbox
            elif abbox is not None:
                obbox += abbox

        # transform according to our global transformation and
        # intersect with clipping bounding box (which has already been
        # transformed in canvas.__init__())
        if obbox is not None and self.clipbbox is not None:
            return obbox.transformed(self.trafo)*self.clipbbox
        elif obbox is not None:
            return obbox.transformed(self.trafo)
        else:
            return self.clipbbox

    def registerPS(self, registry):
        for item in self.items:
            item.registerPS(registry)

    def registerPDF(self, registry):
        for item in self.items:
            item.registerPDF(registry)

    def outputPS(self, file, writer, context):
        context = context()
        if self.items:
            file.write("gsave\n")
            for item in self.items:
                item.outputPS(file, writer, context)
            file.write("grestore\n")

    def outputPDF(self, file, writer, context):
        context = context()
        if self.items:
            file.write("q\n") # gsave
            for item in self.items:
                if isinstance(item, type1font.text_pt):
                    if not context.textregion:
                        file.write("BT\n")
                        context.textregion = 1
                else:
                    if context.textregion:
                        file.write("ET\n")
                        context.textregion = 0
                        context.font = None
                item.outputPDF(file, writer, context)
            if context.textregion:
                file.write("ET\n")
                context.textregion = 0
                context.font = None
            file.write("Q\n") # grestore

    def insert(self, item, attrs=None):
        """insert item in the canvas.

        If attrs are passed, a canvas containing the item is inserted applying attrs.

        returns the item

        """

        if not isinstance(item, canvasitem):
            raise RuntimeError("only instances of base.canvasitem can be inserted into a canvas")

        if attrs:
            sc = _canvas(attrs)
            sc.insert(item)
            self.items.append(sc)
        else:
            self.items.append(item)

        return item

    def set(self, attrs):
        """sets styles args globally for the rest of the canvas
        """

        attr.checkattrs(attrs, [style.strokestyle, style.fillstyle])
        for astyle in attrs:
            self.insert(astyle)

    def draw(self, path, attrs):
        """draw path on canvas using the style given by args

        The argument attrs consists of PathStyles, which modify
        the appearance of the path, PathDecos, which add some new
        visual elements to the path, or trafos, which are applied
        before drawing the path.

        """

        attrs = attr.mergeattrs(attrs)
        attr.checkattrs(attrs, [deco.deco, deformer.deformer, style.fillstyle, style.strokestyle])

        for adeformer in attr.getattrs(attrs, [deformer.deformer]):
            path = adeformer.deform(path)

        styles = attr.getattrs(attrs, [style.fillstyle, style.strokestyle])
        dp = deco.decoratedpath(path, styles=styles)

        # add path decorations and modify path accordingly
        for adeco in attr.getattrs(attrs, [deco.deco]):
            dp = adeco.decorate(dp)

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

#
# user canvas class which adds a few convenience methods for single page output
#

def _wrappedindocument(method):
    def wrappedindocument(self, filename, *args, **kwargs):
        d = document.document([document.page(self, *args, **kwargs)])
        return method(d, filename)
    return wrappedindocument

class canvas(_canvas):

    """a canvas holds a collection of canvasitems"""

    writeEPSfile = _wrappedindocument(document.document.writeEPSfile)
    writePSfile = _wrappedindocument(document.document.writePSfile)
    writePDFfile = _wrappedindocument(document.document.writePDFfile)
    writetofile = _wrappedindocument(document.document.writetofile)
