import sys, prolog, pykpathsea
from t1strip import fullfont
try:
    import zlib
    haszlib = 1
except:
    haszlib = 0

import style

PDFcatalog = "Catalog"
PDFpages = "Pages"
PDFpage = "Page%i"
PDFmediabox = "MediaBox%i"
PDFresources = "Resources%i"
PDFcontents = "Contents%i"
PDFcontentslength = "ContentsLength%i"
PDFfont = "Font%s"
PDFwidths = "Widths%s"
PDFfontdescriptor = "FontDescriptor%s"
PDFfontfile = "FontFile%s"

class pdfwriter:

    def __init__(self, filename, compress=1, compresslevel=6):
        self.file = open(filename, "wb")
        if compress and not haszlib:
            compress = 0
            sys.stderr.write("*** PyXWarning: compression disabled due to missing zlib module\n")
        self.compress = compress
        self.compresslevel = compresslevel

        self.compressstream = None
        self.refdict = {} # id -> ref-no
        self.refs = [] # refno - 1 -> filepos
        self.pages = 0

        self.write("%%PDF-1.4\n%%%s%s%s%s\n" % (chr(195), chr(182), chr(195), chr(169)))

    def write(self, str):
        if self.compressstream is not None:
            self.file.write(self.compressstream.compress(str))
        else:
            self.file.write(str)

    def beginobj(self, object):
        self.refs.append(self.file.tell())
        ref = len(self.refs)
        self.refdict[object] = ref
        self.write("%i 0 obj\n" % ref)

    def endobj(self):
        self.write("endobj\n")

    def beginstream(self):
        self.write("stream\n")
        self.beginstreampos = self.file.tell()
        if self.compress:
            if self.compressstream is not None:
                raise RuntimeError("compression within compression")
            self.compressstream = zlib.compressobj(self.compresslevel)

    def endstream(self):
        if self.compressstream is not None:
            self.file.write(self.compressstream.flush())
            self.compressstream = None
        length = self.file.tell() - self.beginstreampos
        self.write("endstream\n")
        return length

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

    def close(self):
        # page objects and pages object
        # XXX: note that the page objects and the pages object refer to each other
        pagesref = len(self.refs) + self.pages + 1
        for page in range(self.pages):
            self.beginobj(PDFpage % page)
            self.write("<<\n"
                       "/Type /Page\n"
                       "/Parent %i 0 R\n"
                       "/MediaBox %i 0 R\n"
                       "/Resources %i 0 R\n"
                       "/Contents %i 0 R\n"
                       ">>\n" % (pagesref,
                                 self.refdict[PDFmediabox % page],
                                 self.refdict[PDFresources % page],
                                 self.refdict[PDFcontents % page]))
            self.endobj()
        self.beginobj(PDFpages)
        self.write("<<\n"
                   "/Type /Pages\n"
                   "/Kids [%s]\n"
                   "/Count %i\n"
                   ">>\n" % (" ".join(["%i 0 R" % self.refdict[PDFpage % page]
                                       for page in range(self.pages)]),
                             self.pages))
        self.endobj()
        assert pagesref == self.refdict[PDFpages]

        # catalog
        self.beginobj(PDFcatalog)
        self.write("<<\n"
                   "/Type /Catalog\n"
                   "/Pages %i 0 R\n"
                   ">>\n" % self.refdict[PDFpages])
        self.endobj()

        # xref
        xrefpos = self.file.tell()
        self.write("xref\n"
                   "0 %d\n"
                   "0000000000 65535 f \n" % (len(self.refs)+1))
        for ref in self.refs:
            self.file.write("%010i 00000 n \n" % ref)

        # trailer
        self.write("trailer\n"
                   "<<\n"
                   "/Size %i\n"
                   "/Root %i 0 R\n"
                   ">>\n"
                   "startxref\n"
                   "%i\n"
                   "%%%%EOF\n" % (len(self.refs)+1, self.refdict[PDFcatalog], xrefpos))
        self.file.close()

