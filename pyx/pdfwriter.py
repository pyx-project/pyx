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

import copy, sys
import prolog, pykpathsea, unit, style
from t1strip import fullfont
try:
    import zlib
    haszlib = 1
except:
    haszlib = 0


class PDFobject:

    def __init__(self, writer, refno):
        self.refno = refno

    def outputPDFobject(self, file):
        self.filepos = file.tell()
        file.write("%i 0 obj\n" % self.refno)
        self.outputPDF(file)
        file.write("endobj\n")

    def outputPDF(self, file):
        raise NotImplementedError("outputPDF method has to be provided by PDFobject subclass")


class PDFcatalog(PDFobject):

    def __init__(self, writer, refno, document):
        PDFobject.__init__(self, writer, refno)
        self.pages = writer.addobject(PDFpages, document)

    def outputPDF(self, file):
        file.write("<<\n"
                   "/Type /Catalog\n"
                   "/Pages %i 0 R\n"
                   ">>\n" % self.pages.refno)


class PDFpages(PDFobject):

    def __init__(self, writer, refno, document):
        PDFobject.__init__(self, writer, refno)
        self.pages = []
        for page in document.pages:
            self.pages.append(writer.addobject(PDFpage, self.refno, page))

    def outputPDF(self, file):
        file.write("<<\n"
                   "/Type /Pages\n"
                   "/Kids [%s]\n"
                   "/Count %i\n"
                   ">>\n" % (" ".join(["%i 0 R" % page.refno
                                       for page in self.pages]),
                             len(self.pages)))


class PDFpage(PDFobject):

    def __init__(self, writer, refno, pagesrefno, page):
        PDFobject.__init__(self, writer, refno)
        self.pagesrefno = pagesrefno
        self.page = page
        self.bbox = page.canvas.bbox()
        self.pagetrafo = page.pagetrafo(self.bbox)
        if self.pagetrafo:
            self.bbox.transform(self.pagetrafo)
        self.content = writer.addobject(PDFcontent, page.canvas, self.pagetrafo)

    def outputPDF(self, file):
        file.write("<<\n"
                   "/Type /Page\n"
                   "/Parent %i 0 R\n" % self.pagesrefno)
        paperformat = self.page.paperformat
        file.write("/MediaBox [0 0 %d %d]\n" % (unit.topt(paperformat.width), unit.topt(paperformat.height)))
        file.write("/CropBox " )
        self.bbox.outputPDF(file)
        file.write("/Resources << /ProcSet [ /PDF ] >>\n"
                   "/Contents %i 0 R\n"
                   ">>\n" % (self.content.refno))


class PDFcontent(PDFobject):

    def __init__(self, writer, refno, canvas, pagetrafo):
        PDFobject.__init__(self, writer, refno)
        self.refno = refno
        self.canvas = canvas
        self.pagetrafo = pagetrafo
        self.contentlength = writer.addobject(PDFcontentlength)

    def outputPDF(self, file):
        file.write("<<\n"
                          "/Length %i 0 R\n" % (self.refno + 1))
        # if self.compress:
        #     self.write("/Filter /FlateDecode\n")
        file.write(">>\n")
        file.write("stream\n")
        self.beginstreampos = file.tell()

        # if self.compress:
        #     if self.compressstream is not None:
        #         raise RuntimeError("compression within compression")
        #     self.compressstream = zlib.compressobj(self.compresslevel)

        # apply a possible global transformation

        if self.pagetrafo:
            self.pagetrafo.outputPDF(file)
        style.linewidth.normal.outputPDF(file)
        self.canvas.outputPDF(file)

        # if self.compressstream is not None:
        #     self.file.write(self.compressstream.flush())
        #     self.compressstream = None

        self.contentlength.contentlength = file.tell() - self.beginstreampos
        file.write("endstream\n")


class PDFcontentlength(PDFobject):

    def __init__(self, writer, refno):
        PDFobject.__init__(self, writer, refno)
        self.contentlength = None

    def outputPDF(self, file):
        file.write("%d\n" % self.contentlength)


class PDFwriter:

    def __init__(self, document, filename, compress=1, compresslevel=6):
        sys.stderr.write("*** PyX Warning: writePDFfile is experimental and supports only a subset of PyX's features\n")

        if filename[-4:] != ".pdf":
            filename = filename + ".pdf"
        try:
            self.file = open(filename, "wb")
        except IOError:
            raise IOError("cannot open output file")

        if compress and not haszlib:
            compress = 0
            sys.stderr.write("*** PyX Warning: compression disabled due to missing zlib module\n")
        self.compress = compress
        self.compresslevel = compresslevel

        self.pdfobjects = []
        self.pdfobjectcount = 0

        self.file.write("%%PDF-1.4\n%%%s%s%s%s\n" % (chr(195), chr(182), chr(195), chr(169)))

        catalog = self.addobject(PDFcatalog, document)

        self.pdfobjects.reverse()
        for pdfobject in self.pdfobjects:
            pdfobject.outputPDFobject(self.file)

        # xref
        xrefpos = self.file.tell()
        self.file.write("xref\n"
                        "0 %d\n"
                        "0000000000 65535 f \n" % (len(self.pdfobjects)+1))
        for pdfobject in self.pdfobjects:
            self.file.write("%010i 00000 n \n" % pdfobject.filepos)

        # trailer
        self.file.write("trailer\n"
                        "<<\n"
                        "/Size %i\n"
                        "/Root %i 0 R\n"
                        ">>\n"
                        "startxref\n"
                        "%i\n"
                        "%%%%EOF\n" % (len(self.pdfobjects)+1, catalog.refno, xrefpos))
        self.file.close()

    def addobject(self, objectclass, *args, **kwargs):
        self.pdfobjectcount += 1
        pdfobject = objectclass(self, self.pdfobjectcount, *args, **kwargs)
        self.pdfobjects.append(pdfobject)
        return pdfobject
#         # During the creating of object other objects may already have been added.
#         # We have to make sure that we add the object at the right place in the
#         # object list:
#         i = len(self.pdfobjects)
#         while i > 0 and self.pdfobjects[i-1].refno > pdfobject.refno:
#             i -= 1
#         self.pdfobjects.insert(i, pdfobject)
#         return pdfobject



    def page(self, abbox, canvas, mergedprolog, ctrafo):
        # media box
        self.beginobj(PDFmediabox % self.pages)
        abbox.outputPDF(self)
        self.endobj()

        # insert resources
        for pritem in mergedprolog:
            if isinstance(pritem, prolog.fontdefinition):
                if pritem.filename:
                    # fontfile
                    fontdata = open(pykpathsea.find_file(pritem.filename, pykpathsea.kpse_type1_format)).read()
                    if fontdata[0:2] != fullfont._PFB_ASCII:
                        raise RuntimeError("PFB_ASCII mark expected")
                    length1 = fullfont.pfblength(fontdata[2:6])
                    if fontdata[6+length1:8+length1] != fullfont._PFB_BIN:
                        raise RuntimeError("PFB_BIN mark expected")
                    length2 = fullfont.pfblength(fontdata[8+length1:12+length1])
                    if fontdata[12+length1+length2:14+length1+length2] != fullfont._PFB_ASCII:
                        raise RuntimeError("PFB_ASCII mark expected")
                    length3 = fullfont.pfblength(fontdata[14+length1+length2:18+length1+length2])
                    if fontdata[18+length1+length2+length3:20+length1+length2+length3] != fullfont._PFB_DONE:
                        raise RuntimeError("PFB_DONE mark expected")
                    if len(fontdata) != 20 + length1 + length2 + length3:
                        raise RuntimeError("end of pfb file expected")

                    # we might be allowed to skip the third part ...
                    if fontdata[18+length1+length2:18+length1+length2+length3].replace("\n", "").replace("\r", "").replace("\t", "").replace(" ", "") == "0"*512 + "cleartomark":
                        length3 = 0

                    uncompresseddata = fontdata[6:6+length1] + fontdata[12+length1:12+length1+length2] + fontdata[18+length1+length2:18+length1+length2+length3]
                    compresseddata = zlib.compress(uncompresseddata)

                    self.beginobj(PDFfontfile % pritem.font.getpsname())
                    self.write("<<\n"
                               "/Length %d\n"
                               "/Length1 %d\n"
                               "/Length2 %d\n"
                               "/Length3 %d\n"
                               "/Filter /FlateDecode\n"
                               ">>\n"
                               "stream\n" % (len(compresseddata), length1, length2, length3))
                    #file.write(fontdata[6:6+length1])
                    #file.write(fontdata[12+length1:12+length1+length2])
                    #file.write(fontdata[18+length1+length2:18+length1+length2+length3])
                    self.write(compresseddata)
                    self.write("endstream\n")
                    self.endobj()

                    # fontdescriptor
                    self.beginobj(PDFfontdescriptor % pritem.font.getpsname())
                    self.write("<<\n"
                               "/Type /FontDescriptor\n"
                               "/FontName /%s\n"
                               "/Flags 4\n" # FIXME
                               "/FontBBox [-10 -10 1000 1000]\n" # FIXME
                               "/ItalicAngle 0\n" # FIXME
                               "/Ascent 20\n" # FIXME
                               "/Descent -5\n" # FIXME
                               "/CapHeight 15\n" # FIXME
                               "/StemV 3\n" # FIXME
                               "/FontFile %d 0 R\n" # FIXME
                               # "/CharSet \n" # fill in when stripping
                               ">>\n" % (pritem.font.getbasepsname(),
                                         self.refdict[PDFfontfile % pritem.font.getpsname()]))
                    self.endobj()


                # width
                self.beginobj(PDFwidths % pritem.font.getpsname())
                self.write("[\n")
                for i in range(256):
                    try:
                        width = pritem.font.getwidth_pt(i)*1000/pritem.font.getsize_pt()
                    except:
                        width = 0
                    self.write("%f\n" % width)
                self.write("]\n")
                self.endobj()

                # font
                self.beginobj(PDFfont % pritem.font.getpsname())
                self.write("<<\n"
                           "/Type /Font\n"
                           "/Subtype /Type1\n"
                           "/Name /%s\n"
                           "/BaseFont /%s\n"
                           "/FirstChar 0\n"
                           "/LastChar 255\n"
                           "/Widths %d 0 R\n"
                           "/FontDescriptor %d 0 R\n"
                           "/Encoding /StandardEncoding\n" # FIXME
                           ">>\n" % (pritem.font.getpsname(), pritem.font.getbasepsname(),
                                     self.refdict[PDFwidths % pritem.font.getpsname()],
                                     self.refdict[PDFfontdescriptor % pritem.font.getpsname()]))
                self.endobj()

        # resources
        self.beginobj(PDFresources % self.pages)
        self.write("<<\n")
        if len([pritem for pritem in mergedprolog if isinstance(pritem, prolog.fontdefinition)]):
            self.write("/Font\n"
                       "<<\n")
            for pritem in mergedprolog:
                if isinstance(pritem, prolog.fontdefinition):
                    self.write("/%s %d 0 R\n" % (pritem.font.getpsname(),
                                                 self.refdict[PDFfont % pritem.font.getpsname()]))
            self.write(">>\n")
        self.write(">>\n")
        self.endobj()

        # contents
        contentslengthref = len(self.refs) + 2
        self.beginobj(PDFcontents % self.pages)
        self.write("<<\n"
                   "/Length %i 0 R\n" % contentslengthref)
        if self.compress:
            self.write("/Filter /FlateDecode\n")
        self.write(">>\n")
        self.beginstream()
        # apply a possible global transformation
        if ctrafo: ctrafo.outputPDF(self)
        style.linewidth.normal.outputPDF(self)
        canvas.outputPDF(self)
        contentslength = self.endstream()
        self.endobj()

        # contents length
        self.beginobj(PDFcontentslength % self.pages)
        self.write("%i\n" % contentslength)
        self.endobj()
        assert contentslengthref == self.refdict[PDFcontentslength % self.pages]

        self.pages += 1

# some ideas...

class context:

    def __init__(self):
        self.colorspace = None
        self.linewidth = None

class contextstack:

    def __init__(self):
        self.stack = []
        self.context = context()

    def save(self):
        self.stack.append(copy.copy(self.context))

    def restore(self):
        self.context = self.stack.pop()
