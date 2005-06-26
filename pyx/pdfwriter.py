#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2005 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2005 André Wobst <wobsta@users.sourceforge.net>
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import copy, warnings
import unit, style
# from t1strip import fullfont
try:
    import zlib
    haszlib = 1
except:
    haszlib = 0


class PDFregistry:

    def __init__(self):
        self.types = {}
        # we need to keep the original order of the resources (for PDFcontentlength)
        self.resources = []

    def add(self, resource):
        """ register resource, merging it with an already registered resource of the same type and id"""
        resources = self.types.setdefault(resource.type, {})
        if resources.has_key(resource.id):
            resources[resource.id].merge(resource)
        else:
            self.resources.append(resource)
            resources[resource.id] = resource

    def getrefno(self, resource):
        return self.types[resource.type][resource.id].refno

    def mergeregistry(self, registry):
        for resource in registry.resources:
            self.add(resource)

    def write(self, file, writer, catalog):
        # first we set all refnos
        refno = 1

        # we recursively inserted the resources such that the topmost resources in
        # the dependency tree of the resources come last. Hence, we need to 
        # reverse the resources list before writing the output
        self.resources.reverse()
        for resource in self.resources:
            resource.refno = refno
            refno += 1

        # second, all objects are written, keeping the positions in the output file
        fileposes = []
        for resource in self.resources:
            fileposes.append(file.tell())
            file.write("%i 0 obj\n" % resource.refno)
            resource.outputPDF(file, writer, self)
            file.write("endobj\n")

        # xref
        xrefpos = file.tell()
        file.write("xref\n"
                   "0 %d\n"
                   "0000000000 65535 f \n" % refno)

        for filepos in fileposes:
            file.write("%010i 00000 n \n" % filepos)

        # trailer
        file.write("trailer\n"
                   "<<\n"
                   "/Size %i\n"
                   "/Root %i 0 R\n"
                   ">>\n"
                   "startxref\n"
                   "%i\n"
                   "%%%%EOF\n" % (refno, catalog.refno, xrefpos))


class PDFobject:

    def __init__(self, type, _id=None):
        self.type = type
        if _id is None:
            self.id = id(self)
        else:
            self.id = _id
        self.refno = None

    def merge(self, other):
        pass

    def outputPDF(self, file, writer, registry):
        raise NotImplementedError("outputPDF method has to be provided by PDFobject subclass")


class PDFcatalog(PDFobject):

    def __init__(self, document, registry):
        PDFobject.__init__(self, "catalog")
        self.PDFpages = PDFpages(document, registry)
        registry.add(self.PDFpages)

    def outputPDF(self, file, writer, registry):
        file.write("<<\n"
                   "/Type /Catalog\n"
                   "/Pages %i 0 R\n"
                   ">>\n" % registry.getrefno(self.PDFpages))


class PDFpages(PDFobject):

    def __init__(self, document, registry):
        PDFobject.__init__(self, "pages")
        self.PDFpagelist = []
        for pageno, page in enumerate(document.pages):
            page = PDFpage(page, pageno, self, registry)
            registry.add(page)
            self.PDFpagelist.append(page)

    def outputPDF(self, file, writer, registry):
        file.write("<<\n"
                   "/Type /Pages\n"
                   "/Kids [%s]\n"
                   "/Count %i\n"
                   ">>\n" % (" ".join(["%i 0 R" % registry.getrefno(page)
                                       for page in self.PDFpagelist]),
                             len(self.PDFpagelist)))


class PDFpage(PDFobject):

    def __init__(self, page, pageno, PDFpages, registry):
        PDFobject.__init__(self, "page", pageno)
        self.PDFpages = PDFpages
        self.page = page

        # every page uses its own registry in order to find out which
        # resources are used within the page. However, the
        # pageregistry is also merged in the global registry
        self.pageregistry = PDFregistry()

        self.bbox = page.canvas.bbox()
        self.bbox.enlarge(page.bboxenlarge)
        self.pagetrafo = page.pagetrafo(self.bbox)
        if self.pagetrafo:
            self.bbox.transform(self.pagetrafo)
        self.PDFcontent = PDFcontent(page.canvas, self.pagetrafo, self.pageregistry)
        self.pageregistry.add(self.PDFcontent)
        self.page.canvas.registerPDF(self.pageregistry)
        registry.mergeregistry(self.pageregistry)

    def outputPDF(self, file, writer, registry):
        file.write("<<\n"
                   "/Type /Page\n"
                   "/Parent %i 0 R\n" % registry.getrefno(self.PDFpages))
        paperformat = self.page.paperformat
        file.write("/MediaBox [0 0 %d %d]\n" % (unit.topt(paperformat.width), unit.topt(paperformat.height)))
        file.write("/CropBox " )
        self.bbox.outputPDF(file, writer)
        if self.pageregistry.types.has_key("font"):
            file.write("/Resources <<\n/ProcSet [ /PDF /Text ]\n")
            file.write("/Font << %s >>\n" % " ".join(["/%s %i 0 R" % (font.font.name, registry.getrefno(font))
                                                    for font in self.pageregistry.types["font"].values()]))
        else:
            file.write("/Resources << /ProcSet [ /PDF ]\n")

        file.write(">>\n")
        file.write("/Contents %i 0 R\n"
                   ">>\n" % registry.getrefno(self.PDFcontent))


class _compressstream:

    def __init__(self, file, compresslevel):
        self.file = file
        self.compressobj = zlib.compressobj(compresslevel)

    def write(self, string):
        self.file.write(self.compressobj.compress(string))

    def flush(self):
        self.file.write(self.compressobj.flush())


class PDFcontent(PDFobject):

    def __init__(self, canvas, pagetrafo, registry):
        PDFobject.__init__(self, "content")
        self.canvas = canvas
        self.pagetrafo = pagetrafo
        self.PDFcontentlength = PDFcontentlength()
        registry.add(self.PDFcontentlength)

    def outputPDF(self, file, writer, registry):
        file.write("<<\n"
                   "/Length %i 0 R\n" % registry.getrefno(self.PDFcontentlength))
        if writer.compress:
            file.write("/Filter /FlateDecode\n")
        file.write(">>\n")
        file.write("stream\n")
        beginstreampos = file.tell()

        if writer.compress:
            stream = _compressstream(file, writer.compresslevel)
        else:
            stream = file

        acontext = context()
        # apply a possible global transformation
        if self.pagetrafo:
            self.pagetrafo.outputPDF(stream, writer, acontext)
        style.linewidth.normal.outputPDF(stream, writer, acontext)

        self.canvas.outputPDF(stream, writer, acontext)
        if writer.compress:
            stream.flush()

        self.PDFcontentlength.contentlength = file.tell() - beginstreampos
        file.write("endstream\n")


class PDFcontentlength(PDFobject):

    def __init__(self):
        PDFobject.__init__(self, "_contentlength")

    def outputPDF(self, file, writer, registry):
        # initially we do not know about the content length
        # -> it has to be written into the instance later on
        file.write("%d\n" % self.contentlength)


class PDFfont(PDFobject):

    def __init__(self, font, usedchars, registry):
        PDFobject.__init__(self, "font", font.name)
        self.font = font
        self.usedchars = usedchars
        self.fontdescriptor = PDFfontdescriptor(self.font, registry)
        registry.add(self.fontdescriptor)
        if self.font.encoding:
            self.encoding = PDFencoding(self.font.encoding)
            registry.add(self.encoding)
        else:
            self.encoding = None

    def outputPDF(self, file, writer, registry):
        file.write("<<\n"
                   "/Type /Font\n"
                   "/Subtype /Type1\n")
        file.write("/Name /%s\n" % self.font.name)
        file.write("/BaseFont /%s\n" % self.font.basefontname)
        file.write("/FirstChar 0\n" # FIXME
                   "/LastChar 255\n") # FIXME
        file.write("/Widths\n"
                   "[")
        for i in range(256):
            if i and not (i % 8):
                file.write("\n")
            else:
                file.write(" ")
            try:
                width = self.font.metric.getwidth_ds(i)
            except IndexError:
                width = 0
            file.write("%f" % width)
        file.write(" ]\n")
        file.write("/FontDescriptor %d 0 R\n" % registry.getrefno(self.fontdescriptor))
        if self.encoding:
            file.write("/Encoding %d 0 R\n" % registry.getrefno(self.encoding))
        else:
            file.write("/Encoding /StandardEncoding\n")
        file.write(">>\n")


class PDFfontdescriptor(PDFobject):

    def __init__(self, font, registry):
        PDFobject.__init__(self, "fontdescriptor")
        self.font = font
        self.fontfile = PDFfontfile(self.font)
        registry.add(self.fontfile)

    def outputPDF(self, file, writer, registry):
        file.write("<<\n"
                   "/Type /FontDescriptor\n"
                   "/FontName /%s\n" % self.font.basefontname)
        file.write("/Flags %d\n" % self.font.flags)
        file.write("/FontBBox [%d %d %d %d]\n" % self.font.fontbbox)
        file.write("/ItalicAngle %d\n" % self.font.italicangle)
        file.write("/Ascent %d\n" % self.font.ascent)
        file.write("/Descent %d\n" % self.font.descent)
        file.write("/CapHeight %d\n" % self.font.capheight)
        file.write("/StemV %d\n" % self.font.vstem)
        file.write("/FontFile %d 0 R\n" % registry.getrefno(self.fontfile))
        # file.write("/CharSet \n") # fill in when stripping
        file.write(">>\n")

class PDFfontfile(PDFobject):

    def __init__(self, font):
        PDFobject.__init__(self, "fontfile", font.filename)
        self.font = font

    def outputPDF(self, file, writer, registry):
        # we might be allowed to skip the third part ...
        if (self.font.fontdata3.replace("\n", "")
                                    .replace("\r", "")
                                    .replace("\t", "")
                                    .replace(" ", "")) == "0"*512 + "cleartomark":
            length3 = 0
            fontdata3 = ""
        else:
            fontdata3 = self.font.fontdata3
        data = self.font.fontdata1 + self.font.fontdata2 + fontdata3
        
        if writer.compress:
            data = zlib.compress(data)

        file.write("<<\n"
                   "/Length %d\n"
                   "/Length1 %d\n"
                   "/Length2 %d\n"
                   "/Length3 %d\n" % (len(data), self.font.length1, self.font.length2, length3))
        if writer.compress:
            file.write("/Filter /FlateDecode\n")
        file.write(">>\n"
                   "stream\n")
        file.write(data)
        file.write("\nendstream\n")

class PDFencoding(PDFobject):

    def __init__(self, encoding):
        PDFobject.__init__(self, "encoding", encoding.name)
        self.encoding = encoding

    def outputPDF(self, file, writer, registry):
        file.write("<<\n"
                   "/Type /Encoding\n"
                   "/Differences\n"
                   "[ 0 %s ]\n" % "".join(self.encoding.encvector))
        file.write(">>\n")



class PDFwriter:

    def __init__(self, document, filename, compress=0, compresslevel=6):
        warnings.warn("writePDFfile is experimental and supports only a subset of PyX's features")

        if filename[-4:] != ".pdf":
            filename = filename + ".pdf"
        try:
            file = open(filename, "wb")
        except IOError:
            raise IOError("cannot open output file")

        if compress and not haszlib:
            compress = 0
            warnings.warn("compression disabled due to missing zlib module")
        self.compress = compress
        self.compresslevel = compresslevel

        file.write("%%PDF-1.4\n%%%s%s%s%s\n" % (chr(195), chr(182), chr(195), chr(169)))

        # the PDFcatalog class automatically builds up the pdfobjects from a document
        registry = PDFregistry()
        catalog = PDFcatalog(document, registry)
        registry.add(catalog)
        registry.write(file, self, catalog)
        file.close()


class context:

    def __init__(self):
        self.linewidth_pt = None
        self.colorspace = None
        self.strokeattr = 1
        self.fillattr = 1
        self.font = None
        self.textregion = 0

    def __call__(self, **kwargs):
        newcontext = copy.copy(self)
        for key, value in kwargs.items():
            setattr(newcontext, key, value)
        return newcontext
