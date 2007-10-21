# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2005-2007 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2005-2007 André Wobst <wobsta@users.sourceforge.net>
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

from pyx import canvas, pswriter, trafo, unit
import t1file

try:
    set()
except NameError:
    # Python 2.3
    from sets import Set as set

#
# PSresources
#


class PST1file(pswriter.PSresource):

    """ PostScript font definition included in the prolog """

    def __init__(self, t1file, glyphnames, charcodes):
        """ include type 1 font t1file stripped to the given glyphnames"""
        self.type = "t1file"
        self.t1file = t1file
        self.id = t1file.name
        self.glyphnames = set(glyphnames)
        self.charcodes = set(charcodes)
        self.strip = 1

    def merge(self, other):
        self.glyphnames.update(other.glyphnames)
        self.charcodes.update(other.charcodes)

    def output(self, file, writer, registry):
        file.write("%%%%BeginFont: %s\n" % self.t1file.name)
        if self.strip:
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


class font:

    def text(self, x, y, charcodes, size_pt, **kwargs):
        return self.text_pt(unit.topt(x), unit.topt(y), charcodes, size_pt, **kwargs)


class T1font(font):

    def __init__(self, t1file):
        self.t1file = t1file
	self.name = t1file.name

    def text_pt(self, x, y, charcodes, size_pt, **kwargs):
        return T1text_pt(self, x, y, charcodes, size_pt, **kwargs)


class T1builtinfont(T1font):

    def __init__(self, name):
        self.name = name
	self.t1file = None


class selectedfont:

    def __init__(self, name, size_pt):
        self.name = name
        self.size_pt = size_pt

    def __eq__(self, other):
        return self.name == other.name and self.size_pt == other.size_pt

    def outputPS(self, file, writer):
        file.write("/%s %f selectfont\n" % (self.name, self.size_pt))


class T1text_pt(canvas.canvasitem):

    def __init__(self, font, x_pt, y_pt, charcodes, size_pt, decoding=None, slant=None): #, **features):
        # features: kerning, ligatures
        if decoding is not None:
            self.glyphnames = [decoding[character] for character in charcodes]
            self.reencode = True
        else:
            self.charcodes = charcodes
            self.reencode = False
        self.font = font
        self.x_pt = x_pt
        self.y_pt = y_pt
        self.size_pt = size_pt
        self.slant = slant

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
        # bbox += self.bbox()

        # register resources
        if self.font.t1file is not None:
            if self.reencode:
                registry.add(PST1file(self.font.t1file, self.glyphnames, []))
            else:
                registry.add(PST1file(self.font.t1file, [], self.charcodes))

        fontname = self.font.name
        if self.reencode:
            encodingname = self.getencodingname(context.encodings.setdefault(self.font.name, {}))
            encoding = context.encodings[self.font.name][encodingname]
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
        if self.reencode:
            charcodes = [encoding[glyphname] for glyphname in self.glyphnames]
        else:
            charcodes = self.charcodes
        for charcode in charcodes:
            if 32 < charcode < 127 and chr(charcode) not in "()[]<>\\":
                file.write("%s" % chr(charcode))
            else:
                file.write("\\%03o" % charcode)
        file.write(") show\n")
