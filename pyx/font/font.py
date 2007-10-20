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

    def __init__(self, t1file, glyphnames):
        """ include type 1 font t1file stripped to the given glyphnames"""
        self.type = "t1file"
        self.t1file = t1file
        self.id = t1file.name
        self.usedglyphs = set(glyphnames)
        self.strip = 1

    def merge(self, other):
        self.usedglyphs.update(other.usedglyphs)

    def output(self, file, writer, registry):
        file.write("%%%%BeginFont: %s\n" % self.t1file.name)
        if self.strip:
            file.write("%%Included glyphs: %s\n" % " ".join(self.usedglyphs))
            self.t1file.getstrippedfont(self.usedglyphs).outputPS(file, writer)
        else:
            self.t1file.outputPS(file, writer)
        file.write("\n%%EndFont\n")


class PSencodefont(pswriter.PSresource):

    """ encoded and transformed PostScript font"""

    def __init__(self, basefontname, newfontname, encoding, newfontmatrix):
        """ include the font in the given encoding """

        self.type = "encodedfont"
        self.basefontname = basefontname
	self.id = self.newfontname = newfontname
        self.encoding = encoding
	self.newfontmatrix = newfontmatrix

    def output(self, file, writer, registry):
        file.write("%%%%BeginResource: %s\n" % self.newfontname)
        file.write("/%s /%s [\n" % (self.basefontname, self.newfontname))
        vector = [None] * len(self.encoding)
        for glyphname, codepoint in self.encoding.items():
            vector[codepoint] = glyphname
        for glyphname in vector:
            file.write("/%s " % glyphname)
        file.write("]\n") 
	if self.newfontmatrix:
	    file.write(str(self.newfontmatrix))
	else:
	    file.write("0")
	file.write(" ReEncodeFont\n")
        file.write("%%EndResource\n")


_ReEncodeFont = pswriter.PSdefinition("ReEncodeFont", """{
  6 dict
  begin
    /newfontmatrix exch def
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
    0 newfontmatrix ne { newfontdict /FontMatrix newfontmatrix readonly put } if
    newfontname newfontdict definefont pop
  end
}""")


class font:

    def text_pt(self, x, y, text, decoding, size, slant=0, **features):
        # features: kerning, ligatures
        glyphnames = [decoding[character] for character in text]
        return T1text_pt(self, x, y, glyphnames, size, slant)

    def text(self, x, y, text, decoding, size, **features):
        return self.text_pt(unit.topt(x), unit.topt(y), text, decoding, size, **features)


class T1font(font):

    def __init__(self, pfbname=None):
        self.t1file = t1file.PFBfile(pfbname)


class selectedfont:

    def __init__(self, name, size):
        self.name = name
        self.size = size

    def __eq__(self, other):
        return self.name == other.name and self.size == other.size

    def outputPS(self, file, writer):
	file.write("/%s %f selectfont\n" % (self.name, self.size))


class T1text_pt(canvas.canvasitem):

    def __init__(self, font, x_pt, y_pt, glyphnames, size, slant):
        self.font = font
        self.x_pt = x_pt
        self.y_pt = y_pt
        self.glyphnames = glyphnames
        self.size = size
        self.slant = slant

    def getencodingname(self, encodings):
        """returns the name of the encoding (in encodings) mapping self.glyphnames to codepoints
        If no such encoding can be found or extended, a new encoding is added to encodings
        """
        glyphnames = set(self.glyphnames)
        if len(glyphnames) > 256:
            raise ValueError("glyphs do not fit into one single encoding")
        for encodingname, encoding in encodings:
            glyphsmissing = []
            for glyphname in glyphnames:
                if glyphname not in encoding.keys():
                    glyphsmissing.append(glyphname)
            
            if glyphsmissing + len(encoding) < 256:
                # new glyphs fit in existing encoding which will thus be extended
                for glyphname in glyphsmissing:
                    encoding[glyphname] = len(encoding)
                return encodingname
        # create a new encoding for the glyphnames
        encodingname = "PyX%d" % len(encodings)
        encodings[encodingname] = dict([(glyphname, i) for i, glyphname in enumerate(glyphnames)])
        return encodingname

    def processPS(self, file, writer, context, registry, bbox):
        # bbox += self.bbox()

        encodingname = self.getencodingname(context.encodings.setdefault(self.font.t1file.name, {}))
        encoding = context.encodings[self.font.t1file.name][encodingname]

	if self.slant:
            newfontmatrix = trafo.trafo_pt(matrix=((1, self.slant), (0, 1))) * self.font.t1file.fontmatrix
	    newfontname = "%s-%s-slant%f" % (self.font.t1file.name, encodingname, self.slant)
	else:
	    newfontmatrix = None
	    newfontname = "%s-%s" % (self.font.t1file.name, encodingname)

        # register resources
        if self.font.t1file is not None:
            registry.add(PST1file(self.font.t1file, self.glyphnames))
        registry.add(_ReEncodeFont)
        registry.add(PSencodefont(self.font.t1file.name, newfontname, encoding, newfontmatrix))

        # select font if necessary
        sf = selectedfont(newfontname, self.size)
        if context.selectedfont is None or sf != context.selectedfont:
            context.selectedfont = sf
            sf.outputPS(file, writer)

        file.write("%f %f moveto (" % (self.x_pt, self.y_pt))
        for glyphname in self.glyphnames:
            codepoint = encoding[glyphname]
            if codepoint > 32 and codepoint < 127 and chr(codepoint) not in "()[]<>\\":
                file.write("%s" % chr(codepoint))
            else:
                file.write("\\%03o" % codepoint)
        file.write(") show\n")
