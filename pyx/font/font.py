# -*- encoding: utf-8 -*-
#
#
# Copyright (C) 2005-2011 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2006-2011 Michael Schindler <m-schindler@users.sourceforge.net>
# Copyright (C) 2005-2011 André Wobst <wobsta@users.sourceforge.net>
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

from pyx import bbox, canvasitem, deco, path, pswriter, pdfwriter, trafo, unit
import t1file

try:
    set()
except NameError:
    # Python 2.3
    from sets import Set as set


##############################################################################
# PS resources
##############################################################################

class PST1file(pswriter.PSresource):

    """ PostScript font definition included in the prolog """

    def __init__(self, t1file, glyphnames, charcodes):
        """ include type 1 font t1file stripped to the given glyphnames"""
        self.type = "t1file"
        self.t1file = t1file
        self.id = t1file.name
        self.glyphnames = set(glyphnames)
        self.charcodes = set(charcodes)

    def merge(self, other):
        self.glyphnames.update(other.glyphnames)
        self.charcodes.update(other.charcodes)

    def output(self, file, writer, registry):
        file.write("%%%%BeginFont: %s\n" % self.t1file.name)
        if writer.strip_fonts:
            if self.glyphnames:
                file.write("%%Included glyphs: %s\n" % " ".join(self.glyphnames))
            if self.charcodes:
                file.write("%%Included charcodes: %s\n" % " ".join([str(charcode) for charcode in self.charcodes]))
            self.t1file.getstrippedfont(self.glyphnames, self.charcodes).outputPS(file, writer)
        else:
            self.t1file.outputPS(file, writer)
        file.write("\n%%EndFont\n")


_ReEncodeFont = pswriter.PSdefinition("ReEncodeFont", """{
  5 dict
  begin
    /newencoding exch def
    /newfontname exch def
    /basefontname exch def
    /basefontdict basefontname findfont def
    /newfontdict basefontdict maxlength dict def
    basefontdict {
      exch dup dup /FID ne exch /Encoding ne and
      { exch newfontdict 3 1 roll put }
      { pop pop }
      ifelse
    } forall
    newfontdict /FontName newfontname put
    newfontdict /Encoding newencoding put
    newfontname newfontdict definefont pop
  end
}""")


class PSreencodefont(pswriter.PSresource):

    """ reencoded PostScript font"""

    def __init__(self, basefontname, newfontname, encoding):
        """ reencode the font """

        self.type = "reencodefont"
        self.basefontname = basefontname
        self.id = self.newfontname = newfontname
        self.encoding = encoding

    def output(self, file, writer, registry):
        file.write("%%%%BeginResource: %s\n" % self.newfontname)
        file.write("/%s /%s\n[" % (self.basefontname, self.newfontname))
        vector = [None] * len(self.encoding)
        for glyphname, charcode in self.encoding.items():
            vector[charcode] = glyphname
        for i, glyphname in enumerate(vector):
            if i:
                if not (i % 8):
                    file.write("\n")
                else:
                    file.write(" ")
            file.write("/%s" % glyphname)
        file.write("]\n")
        file.write("ReEncodeFont\n")
        file.write("%%EndResource\n")


_ChangeFontMatrix = pswriter.PSdefinition("ChangeFontMatrix", """{
  5 dict
  begin
    /newfontmatrix exch def
    /newfontname exch def
    /basefontname exch def
    /basefontdict basefontname findfont def
    /newfontdict basefontdict maxlength dict def
    basefontdict {
      exch dup dup /FID ne exch /FontMatrix ne and
      { exch newfontdict 3 1 roll put }
      { pop pop }
      ifelse
    } forall
    newfontdict /FontName newfontname put
    newfontdict /FontMatrix newfontmatrix readonly put
    newfontname newfontdict definefont pop
  end
}""")


class PSchangefontmatrix(pswriter.PSresource):

    """ change font matrix of a PostScript font"""

    def __init__(self, basefontname, newfontname, newfontmatrix):
        """ change the font matrix """

        self.type = "changefontmatrix"
        self.basefontname = basefontname
        self.id = self.newfontname = newfontname
        self.newfontmatrix = newfontmatrix

    def output(self, file, writer, registry):
        file.write("%%%%BeginResource: %s\n" % self.newfontname)
        file.write("/%s /%s\n" % (self.basefontname, self.newfontname))
        file.write(str(self.newfontmatrix))
        file.write("\nChangeFontMatrix\n")
        file.write("%%EndResource\n")


##############################################################################
# PDF resources
##############################################################################

class PDFfont(pdfwriter.PDFobject):

    def __init__(self, fontname, basefontname, charcodes, fontdescriptor, encoding, metric):
        pdfwriter.PDFobject.__init__(self, "font", fontname)

        self.fontname = fontname
        self.basefontname = basefontname
        self.charcodes = set(charcodes)
        self.fontdescriptor = fontdescriptor
        self.encoding = encoding
        self.metric = metric

    def merge(self, other):
        self.charcodes.update(other.charcodes)

    def write(self, file, writer, registry):
        file.write("<<\n"
                   "/Type /Font\n"
                   "/Subtype /Type1\n")
        file.write("/Name /%s\n" % self.fontname)
        file.write("/BaseFont /%s\n" % self.basefontname)
        firstchar = min(self.charcodes)
        lastchar = max(self.charcodes)
        file.write("/FirstChar %d\n" % firstchar)
        file.write("/LastChar %d\n" % lastchar)
        file.write("/Widths\n"
                   "[")
        if self.encoding:
            encoding = self.encoding.getvector()
        else:
            encoding = self.fontdescriptor.fontfile.t1file.encoding
        for i in range(firstchar, lastchar+1):
            if i:
                if not (i % 8):
                    file.write("\n")
                else:
                    file.write(" ")
            if i in self.charcodes:
                if self.metric is not None:
                    file.write("%i" % self.metric.width_ds(encoding[i]))
                else:
                    file.write("%i" % self.fontdescriptor.fontfile.t1file.getglyphinfo(encoding[i])[0])
            else:
                file.write("0")
        file.write(" ]\n")
        file.write("/FontDescriptor %d 0 R\n" % registry.getrefno(self.fontdescriptor))
        if self.encoding:
            file.write("/Encoding %d 0 R\n" % registry.getrefno(self.encoding))
        file.write(">>\n")


class PDFstdfont(pdfwriter.PDFobject):

    def __init__(self, basename):
        pdfwriter.PDFobject.__init__(self, "font", "stdfont-%s" % basename)
        self.name = basename # name is ignored by acroread
        self.basename = basename

    def write(self, file, writer, registry):
        file.write("<</BaseFont /%s\n" % self.basename)
        file.write("/Name /%s\n" % self.name)
        file.write("/Type /Font\n")
        file.write("/Subtype /Type1\n")
        file.write(">>\n")

# the 14 standard fonts that are always available in PDF
PDFTimesRoman           = PDFstdfont("Times-Roman")
PDFTimesBold            = PDFstdfont("Times-Bold")
PDFTimesItalic          = PDFstdfont("Times-Italic")
PDFTimesBoldItalic      = PDFstdfont("Times-BoldItalic")
PDFHelvetica            = PDFstdfont("Helvetica")
PDFHelveticaBold        = PDFstdfont("Helvetica-Bold")
PDFHelveticaOblique     = PDFstdfont("Helvetica-Oblique")
PDFHelveticaBoldOblique = PDFstdfont("Helvetica-BoldOblique")
PDFCourier              = PDFstdfont("Courier")
PDFCourierBold          = PDFstdfont("Courier-Bold")
PDFCourierOblique       = PDFstdfont("Courier-Oblique")
PDFCourierBoldOblique   = PDFstdfont("Courier-BoldOblique")
PDFSymbol               = PDFstdfont("Symbol")
PDFZapfDingbats         = PDFstdfont("ZapfDingbats")


class PDFfontdescriptor(pdfwriter.PDFobject):

    def __init__(self, fontname, fontfile, metric):
        pdfwriter.PDFobject.__init__(self, "fontdescriptor", fontname)
        self.fontname = fontname
        self.fontfile = fontfile
        self.metric = metric

    def write(self, file, writer, registry):
        file.write("<<\n"
                   "/Type /FontDescriptor\n"
                   "/FontName /%s\n" % self.fontname)
        if self.metric is not None:
            self.metric.writePDFfontinfo(file)
        else:
            self.fontfile.t1file.writePDFfontinfo(file)
        if self.fontfile is not None:
            file.write("/FontFile %d 0 R\n" % registry.getrefno(self.fontfile))
        file.write(">>\n")


class PDFfontfile(pdfwriter.PDFobject):

    def __init__(self, t1file, glyphnames, charcodes):
        pdfwriter.PDFobject.__init__(self, "fontfile", t1file.name)
        self.t1file = t1file
        self.glyphnames = set(glyphnames)
        self.charcodes = set(charcodes)

    def merge(self, other):
        self.glyphnames.update(other.glyphnames)
        self.charcodes.update(other.charcodes)

    def write(self, file, writer, registry):
        if writer.strip_fonts:
            self.t1file.getstrippedfont(self.glyphnames, self.charcodes).outputPDF(file, writer)
        else:
            self.t1file.outputPDF(file, writer)


class PDFencoding(pdfwriter.PDFobject):

    def __init__(self, encoding, name):
        pdfwriter.PDFobject.__init__(self, "encoding", name)
        self.encoding = encoding

    def getvector(self):
        # As self.encoding might be appended after the constructur has set it,
        # we need to defer the calculation until the whole content was constructed.
        vector = [None] * len(self.encoding)
        for glyphname, charcode in self.encoding.items():
            vector[charcode] = glyphname
        return vector

    def write(self, file, writer, registry):
        file.write("<<\n"
                   "/Type /Encoding\n"
                   "/Differences\n"
                   "[0")
        for i, glyphname in enumerate(self.getvector()):
            if i:
                if not (i % 8):
                    file.write("\n")
                else:
                    file.write(" ")
            file.write("/%s" % glyphname)
        file.write("]\n"
                   ">>\n")


##############################################################################
# basic PyX text output
##############################################################################

class font:

    def text(self, x, y, charcodes, size_pt, **kwargs):
        return self.text_pt(unit.topt(x), unit.topt(y), charcodes, size_pt, **kwargs)


class T1font(font):

    def __init__(self, t1file, metric):
        self.t1file = t1file
        self.name = t1file.name
        self.metric = metric

    def text_pt(self, x, y, charcodes, size_pt, **kwargs):
        return T1text_pt(self, x, y, charcodes, size_pt, **kwargs)


class T1builtinfont(T1font):

    def __init__(self, name, metric):
        self.name = name
        self.t1file = None
        self.metric = metric


class selectedfont:

    def __init__(self, name, size_pt):
        self.name = name
        self.size_pt = size_pt

    def __ne__(self, other):
        return self.name != other.name or self.size_pt != other.size_pt

    def outputPS(self, file, writer):
        file.write("/%s %f selectfont\n" % (self.name, self.size_pt))

    def outputPDF(self, file, writer):
        file.write("/%s %f Tf\n" % (self.name, self.size_pt))


class text_pt(canvasitem.canvasitem):

    pass


class T1text_pt(text_pt):

    def __init__(self, font, x_pt, y_pt, charcodes, size_pt, decoding=None, slant=None, ignorebbox=False, kerning=False, ligatures=False, spaced_pt=0):
        if decoding is not None:
            self.glyphnames = [decoding[character] for character in charcodes]
            self.decode = True
        else:
            self.charcodes = charcodes
            self.decode = False
        self.font = font
        self.x_pt = x_pt
        self.y_pt = y_pt
        self.size_pt = size_pt
        self.slant = slant
        self.ignorebbox = ignorebbox
        self.kerning = kerning
        self.ligatures = ligatures
        self.spaced_pt = spaced_pt

        if self.kerning and not self.decode:
            raise ValueError("decoding required for font metric access (kerning)")
        if self.ligatures and not self.decode:
            raise ValueError("decoding required for font metric access (ligatures)")
        if self.ligatures:
            self.glyphnames = self.font.metric.resolveligatures(self.glyphnames)

    def bbox(self):
        if self.font.metric is None:
            raise ValueError("metric missing")
        if not self.decode:
            raise ValueError("decoding required for font metric access (bbox)")
        return bbox.bbox_pt(self.x_pt,
                            self.y_pt+self.font.metric.depth_pt(self.glyphnames, self.size_pt),
                            self.x_pt+self.font.metric.width_pt(self.glyphnames, self.size_pt),
                            self.y_pt+self.font.metric.height_pt(self.glyphnames, self.size_pt))

    def getencodingname(self, encodings):
        """returns the name of the encoding (in encodings) mapping self.glyphnames to codepoints
        If no such encoding can be found or extended, a new encoding is added to encodings
        """
        glyphnames = set(self.glyphnames)
        if len(glyphnames) > 256:
            raise ValueError("glyphs do not fit into one single encoding")
        for encodingname, encoding in encodings.items():
            glyphsmissing = []
            for glyphname in glyphnames:
                if glyphname not in encoding.keys():
                    glyphsmissing.append(glyphname)

            if len(glyphsmissing) + len(encoding) < 256:
                # new glyphs fit in existing encoding which will thus be extended
                for glyphname in glyphsmissing:
                    encoding[glyphname] = len(encoding)
                return encodingname
        # create a new encoding for the glyphnames
        encodingname = "encoding%d" % len(encodings)
        encodings[encodingname] = dict([(glyphname, i) for i, glyphname in enumerate(glyphnames)])
        return encodingname

    def processPS(self, file, writer, context, registry, bbox):
        if not self.ignorebbox:
            bbox += self.bbox()

        if writer.text_as_path:
            if self.decode:
                if self.kerning:
                    data = self.font.metric.resolvekernings(self.glyphnames, self.size_pt)
                else:
                    data = self.glyphnames
            else:
                data = self.charcodes
            textpath = path.path()
            x_pt = self.x_pt
            y_pt = self.y_pt
            for i, value in enumerate(data):
                if self.kerning and i % 2:
                    if value is not None:
                        x_pt += value
                else:
                    if i:
                        x_pt += self.spaced_pt
                    glyphpath, wx_pt, wy_pt = self.font.t1file.getglyphpathwxwy_pt(value, self.size_pt, convertcharcode=not self.decode)
                    textpath += glyphpath.transformed(trafo.translate_pt(x_pt, y_pt))
                    x_pt += wx_pt
                    y_pt += wy_pt
            deco.decoratedpath(textpath, fillstyles=[]).processPS(file, writer, context, registry, bbox)
        else:
            # register resources
            if self.font.t1file is not None:
                if self.decode:
                    registry.add(PST1file(self.font.t1file, self.glyphnames, []))
                else:
                    registry.add(PST1file(self.font.t1file, [], self.charcodes))

            fontname = self.font.name
            if self.decode:
                encodingname = self.getencodingname(writer.encodings.setdefault(self.font.name, {}))
                encoding = writer.encodings[self.font.name][encodingname]
                newfontname = "%s-%s" % (fontname, encodingname)
                registry.add(_ReEncodeFont)
                registry.add(PSreencodefont(fontname, newfontname, encoding))
                fontname = newfontname

            if self.slant:
                newfontmatrix = trafo.trafo_pt(matrix=((1, self.slant), (0, 1))) * self.font.t1file.fontmatrix
                newfontname = "%s-slant%f" % (fontname, self.slant)
                registry.add(_ChangeFontMatrix)
                registry.add(PSchangefontmatrix(fontname, newfontname, newfontmatrix))
                fontname = newfontname

            # select font if necessary
            sf = selectedfont(fontname, self.size_pt)
            if context.selectedfont is None or sf != context.selectedfont:
                context.selectedfont = sf
                sf.outputPS(file, writer)

            file.write("%f %f moveto (" % (self.x_pt, self.y_pt))
            if self.decode:
                if self.kerning:
                    data = self.font.metric.resolvekernings(self.glyphnames, self.size_pt)
                else:
                    data = self.glyphnames
            else:
                data = self.charcodes
            for i, value in enumerate(data):
                if self.kerning and i % 2:
                    if value is not None:
                        file.write(") show\n%f 0 rmoveto (" % (value+self.spaced_pt))
                    elif self.spaced_pt:
                        file.write(") show\n%f 0 rmoveto (" % self.spaced_pt)
                else:
                    if i and not self.kerning and self.spaced_pt:
                        file.write(") show\n%f 0 rmoveto (" % self.spaced_pt)
                    if self.decode:
                        value = encoding[value]
                    if 32 < value < 127 and chr(value) not in "()[]<>\\":
                        file.write("%s" % chr(value))
                    else:
                        file.write("\\%03o" % value)
            file.write(") show\n")

    def processPDF(self, file, writer, context, registry, bbox):
        if not self.ignorebbox:
            bbox += self.bbox()

        if writer.text_as_path:
            if self.decode:
                if self.kerning:
                    data = self.font.metric.resolvekernings(self.glyphnames, self.size_pt)
                else:
                    data = self.glyphnames
            else:
                data = self.charcodes
            textpath = path.path()
            x_pt = self.x_pt
            y_pt = self.y_pt
            for i, value in enumerate(data):
                if self.kerning and i % 2:
                    if value is not None:
                        x_pt += value
                else:
                    if i:
                        x_pt += self.spaced_pt
                    glyphpath, wx_pt, wy_pt = self.font.t1file.getglyphpathwxwy_pt(value, self.size_pt, convertcharcode=not self.decode)
                    textpath += glyphpath.transformed(trafo.translate_pt(x_pt, y_pt))
                    x_pt += wx_pt
                    y_pt += wy_pt
            deco.decoratedpath(textpath, fillstyles=[]).processPDF(file, writer, context, registry, bbox)
        else:
            if self.decode:
                encodingname = self.getencodingname(writer.encodings.setdefault(self.font.name, {}))
                encoding = writer.encodings[self.font.name][encodingname]
                charcodes = [encoding[glyphname] for glyphname in self.glyphnames]
            else:
                charcodes = self.charcodes

            # create resources
            fontname = self.font.name
            if self.decode:
                newfontname = "%s-%s" % (fontname, encodingname)
                _encoding = PDFencoding(encoding, newfontname)
                fontname = newfontname
            else:
                _encoding = None
            if self.font.t1file is not None:
                if self.decode:
                    fontfile = PDFfontfile(self.font.t1file, self.glyphnames, [])
                else:
                    fontfile = PDFfontfile(self.font.t1file, [], self.charcodes)
            else:
                fontfile = None
            fontdescriptor = PDFfontdescriptor(self.font.name, fontfile, self.font.metric)
            font = PDFfont(fontname, self.font.name, charcodes, fontdescriptor, _encoding, self.font.metric)

            # register resources
            if fontfile is not None:
                registry.add(fontfile)
            registry.add(fontdescriptor)
            if _encoding is not None:
                registry.add(_encoding)
            registry.add(font)

            registry.addresource("Font", fontname, font, procset="Text")

            if self.slant is None:
                slantvalue = 0
            else:
                slantvalue = self.slant

            # select font if necessary
            sf = selectedfont(fontname, self.size_pt)
            if context.selectedfont is None or sf != context.selectedfont:
                context.selectedfont = sf
                sf.outputPDF(file, writer)

            if self.kerning:
                file.write("1 0 %f 1 %f %f Tm [(" % (slantvalue, self.x_pt, self.y_pt))
            else:
                file.write("1 0 %f 1 %f %f Tm (" % (slantvalue, self.x_pt, self.y_pt))
            if self.decode:
                if self.kerning:
                    data = self.font.metric.resolvekernings(self.glyphnames)
                else:
                    data = self.glyphnames
            else:
                data = self.charcodes
            for i, value in enumerate(data):
                if self.kerning and i % 2:
                    if value is not None:
                        file.write(")%f(" % (-value-self.spaced_pt))
                    elif self.spaced_pt:
                        file.write(")%f(" % (-self.spaced_pt))
                else:
                    if i and not self.kerning and self.spaced_pt:
                        file.write(")%f(" % (-self.spaced_pt))
                    if self.decode:
                        value = encoding[value]
                    if 32 <= value <= 127 and chr(value) not in "()[]<>\\":
                        file.write("%s" % chr(value))
                    else:
                        file.write("\\%03o" % value)
            if self.kerning:
                file.write(")] TJ\n")
            else:
                file.write(") Tj\n")
