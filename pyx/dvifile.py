#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2002-2004 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2003-2004 Michael Schindler <m-schindler@users.sourceforge.net>
# Copyright (C) 2002-2004 André Wobst <wobsta@users.sourceforge.net>
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

import copy, cStringIO, exceptions, re, struct, string, sys
import unit, epsfile, bbox, base, canvas, color, trafo, path, prolog, pykpathsea

class fix_word:
    def __init__(self, word):
        if word >= 0:
            self.sign = 1
        else:
            self.sign = -1

        self.precomma = abs(word) >> 20
        self.postcomma = abs(word) & 0xFFFFF

    def __float__(self):
        return self.sign * (self.precomma + 1.0*self.postcomma/0xFFFFF)

    def __mul__(self, other):
        # hey, it's Q&D
        result = fix_word(0)

        result.sign = self.sign*other.sign
        c = self.postcomma*other.precomma + self.precomma*other.postcomma
        result.precomma = self.precomma*other.precomma + (c >> 20)
        result.postcomma = c & 0xFFFFF + ((self.postcomma*other.postcomma) >> 40)
        return result


class binfile:

    def __init__(self, filename, mode="r"):
        self.file = open(filename, mode)

    def close(self):
        self.file.close()

    def tell(self):
        return self.file.tell()

    def eof(self):
        return self.file.eof()

    def read(self, bytes):
        return self.file.read(bytes)

    def readint(self, bytes=4, signed=0):
        first = 1
        result = 0
        while bytes:
            value = ord(self.file.read(1))
            if first and signed and value > 127:
                value -= 256
            first = 0
            result = 256 * result + value
            bytes -= 1
        return result

    def readint32(self):
        return struct.unpack(">l", self.file.read(4))[0]

    def readuint32(self):
        return struct.unpack(">L", self.file.read(4))[0]

    def readint24(self):
        # XXX: checkme
        return struct.unpack(">l", "\0"+self.file.read(3))[0]

    def readuint24(self):
        # XXX: checkme
        return struct.unpack(">L", "\0"+self.file.read(3))[0]

    def readint16(self):
        return struct.unpack(">h", self.file.read(2))[0]

    def readuint16(self):
        return struct.unpack(">H", self.file.read(2))[0]

    def readchar(self):
        return struct.unpack("b", self.file.read(1))[0]

    def readuchar(self):
        return struct.unpack("B", self.file.read(1))[0]

    def readstring(self, bytes):
        l = self.readuchar()
        assert l <= bytes-1, "inconsistency in file: string too long"
        return self.file.read(bytes-1)[:l]

class stringbinfile(binfile):

    def __init__(self, s):
        self.file = cStringIO.StringIO(s)


# class tokenfile:
#     """ ascii file containing tokens separated by spaces.
#
#     Comments beginning with % are ignored. Strings containing spaces
#     are not handled correctly
#     """
#
#     def __init__(self, filename):
#         self.file = open(filename, "r")
#         self.line = None
#
#     def gettoken(self):
#         """ return next token or None if EOF """
#         while not self.line:
#             line = self.file.readline()
#             if line == "":
#                 return None
#             self.line = line.split("%")[0].split()
#         token = self.line[0]
#         self.line = self.line[1:]
#         return token
#
#     def close(self):
#         self.file.close()


##############################################################################
# TFM file handling
##############################################################################

class TFMError(exceptions.Exception): pass


class char_info_word:
    def __init__(self, word):
        self.width_index  = int((word & 0xFF000000L) >> 24) #make sign-safe
        self.height_index = (word & 0x00F00000) >> 20
        self.depth_index  = (word & 0x000F0000) >> 16
        self.italic_index = (word & 0x0000FC00) >> 10
        self.tag          = (word & 0x00000300) >> 8
        self.remainder    = (word & 0x000000FF)


class tfmfile:
    def __init__(self, name, debug=0):
        self.file = binfile(name, "rb")
        self.debug = debug

        #
        # read pre header
        #

        self.lf = self.file.readint16()
        self.lh = self.file.readint16()
        self.bc = self.file.readint16()
        self.ec = self.file.readint16()
        self.nw = self.file.readint16()
        self.nh = self.file.readint16()
        self.nd = self.file.readint16()
        self.ni = self.file.readint16()
        self.nl = self.file.readint16()
        self.nk = self.file.readint16()
        self.ne = self.file.readint16()
        self.np = self.file.readint16()

        if not (self.bc-1 <= self.ec <= 255 and
                self.ne <= 256 and
                self.lf == 6+self.lh+(self.ec-self.bc+1)+self.nw+self.nh+self.nd
                +self.ni+self.nl+self.nk+self.ne+self.np):
            raise TFMError, "error in TFM pre-header"

        if debug:
            print "lh=%d" % self.lh

        #
        # read header
        #

        self.checksum = self.file.readint32()
        self.designsizeraw = self.file.readint32()
        assert self.designsizeraw > 0, "invald design size"
        self.designsize = fix_word(self.designsizeraw)
        if self.lh > 2:
            assert self.lh > 11, "inconsistency in TFM file: incomplete field"
            self.charcoding = self.file.readstring(40)
        else:
            self.charcoding = None

        if self.lh > 12:
            assert self.lh > 16, "inconsistency in TFM file: incomplete field"
            self.fontfamily = self.file.readstring(20)
        else:
            self.fontfamily = None

        if self.debug:
            print "(FAMILY %s)" % self.fontfamily
            print "(CODINGSCHEME %s)" % self.charcoding
            print "(DESINGSIZE R %f)" % self.designsize

        if self.lh > 17:
            self.sevenbitsave = self.file.readuchar()
            # ignore the following two bytes
            self.file.readint16()
            facechar = self.file.readuchar()
            # decode ugly face specification into the Knuth suggested string
            if facechar < 18:
                if facechar >= 12:
                    self.face = "E"
                    facechar -= 12
                elif facechar >= 6:
                    self.face = "C"
                    facechar -= 6
                else:
                    self.face = "R"

                if facechar >= 4:
                    self.face = "L" + self.face
                    facechar -= 4
                elif facechar >= 2:
                    self.face = "B" + self.face
                    facechar -= 2
                else:
                    self.face = "M" + self.face

                if facechar == 1:
                    self.face = self.face[0] + "I" + self.face[1]
                else:
                    self.face = self.face[0] + "R" + self.face[1]

            else:
                self.face = None
        else:
            self.sevenbitsave = self.face = None

        if self.lh > 18:
            # just ignore the rest
            print self.file.read((self.lh-18)*4)

        #
        # read char_info
        #

        self.char_info = [None]*(self.ec+1)
        for charcode in range(self.bc, self.ec+1):
            self.char_info[charcode] = char_info_word(self.file.readint32())
            if self.char_info[charcode].width_index == 0:
                # disable character if width_index is zero
                self.char_info[charcode] = None

        #
        # read widths
        #

        self.width = [None for width_index in range(self.nw)]
        for width_index in range(self.nw):
            # self.width[width_index] = fix_word(self.file.readint32())
            self.width[width_index] = self.file.readint32()

        #
        # read heights
        #

        self.height = [None for height_index in range(self.nh)]
        for height_index in range(self.nh):
            # self.height[height_index] = fix_word(self.file.readint32())
            self.height[height_index] = self.file.readint32()

        #
        # read depths
        #

        self.depth = [None for depth_index in range(self.nd)]
        for depth_index in range(self.nd):
            # self.depth[depth_index] = fix_word(self.file.readint32())
            self.depth[depth_index] = self.file.readint32()

        #
        # read italic
        #

        self.italic = [None for italic_index in range(self.ni)]
        for italic_index in range(self.ni):
            # self.italic[italic_index] = fix_word(self.file.readint32())
            self.italic[italic_index] = self.file.readint32()

        #
        # read lig_kern
        #

        # XXX decode to lig_kern_command

        self.lig_kern = [None for lig_kern_index in range(self.nl)]
        for lig_kern_index in range(self.nl):
            self.lig_kern[lig_kern_index] = self.file.readint32()

        #
        # read kern
        #

        self.kern = [None for kern_index in range(self.nk)]
        for kern_index in range(self.nk):
            # self.kern[kern_index] = fix_word(self.file.readint32())
            self.kern[kern_index] = self.file.readint32()

        #
        # read exten
        #

        # XXX decode to extensible_recipe

        self.exten = [None for exten_index in range(self.ne)]
        for exten_index in range(self.ne):
            self.exten[exten_index] = self.file.readint32()

        #
        # read param
        #

        # XXX decode

        self.param = [None for param_index in range(self.np)]
        for param_index in range(self.np):
            self.param[param_index] = self.file.readint32()

        self.file.close()


# class FontEncoding:
#
#     def __init__(self, filename):
#         """ font encoding contained in filename """
#         encpath = pykpathsea.find_file(filename, pykpathsea.kpse_tex_ps_header_format)
#         encfile = tokenfile(encpath)
#
#         # name of encoding
#         self.encname = encfile.gettoken()
#         token = encfile.gettoken()
#         if token != "[":
#             raise RuntimeError("cannot parse encoding file '%s', expecting '[' got '%s'" % (filename, token))
#         self.encvector = []
#         for i in range(256):
#             token = encfile.gettoken()
#             if token is None or token=="]":
#                 raise RuntimeError("not enough charcodes in encoding file '%s'" % filename)
#             self.encvector.append(token)
#         if encfile.gettoken() != "]":
#             raise RuntimeError("too many charcodes in encoding file '%s'" % filename)
#         token = encfile.gettoken()
#         if token != "def":
#             raise RuntimeError("cannot parse encoding file '%s', expecting 'def' got '%s'" % (filename, token))
#         token = encfile.gettoken()
#         if token != None:
#             raise RuntimeError("encoding file '%s' too long" % filename)
#         encfile.close()
#
#     def encode(self, charcode):
#         return self.encvector[charcode]

##############################################################################
# Font handling
##############################################################################

_ReEncodeFont = prolog.definition("ReEncodeFont", """{
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

#
# PostScript font selection and output primitives
#

class _begintextobject(base.canvasitem):
    def outputPS(self, file):
        pass
    
    def outputPDF(self, file):
        file.write("BT\n")


class _endtextobject(base.canvasitem):
    def outputPS(self, file):
        pass
    
    def outputPDF(self, file):
        file.write("ET\n")


class _selectfont(base.canvasitem):
    def __init__(self, name, size):
        self.name = name
        self.size = size

    def outputPS(self, file):
        file.write("/%s %f selectfont\n" % (self.name, self.size))

    def outputPDF(self, file):
        file.write("/%s %f Tf\n" % (self.name, self.size))


class selectfont(_selectfont):
    def __init__(self, font):
        _selectfont.__init__(self, font.getpsname(), font.getsize_pt())
        self.font = font

    def prolog(self):
        result = [prolog.fontdefinition(self.font,
                                        self.font.getbasepsname(),
                                        self.font.getfontfile(),
                                        self.font.getencodingfile(),
                                        self.font.usedchars)]
        if self.font.getencoding():
            result.append(_ReEncodeFont)
            result.append(prolog.fontencoding(self.font.getencoding(), self.font.getencodingfile()))
            result.append(prolog.fontreencoding(self.font.getpsname(), self.font.getbasepsname(), self.font.getencoding()))
        return result


class _show(base.canvasitem):

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 0
        self.height = 0
        self.depth = 0
        self.chars = []

    def addchar(self, width, height, depth, char):
        self.width += width
        if height > self.height:
            self.height = height
        if depth > self.depth:
            self.depth = depth
        self.chars.append(char)

    def bbox(self):
        return bbox.bbox_pt(self.x, self.y-self.depth, self.x+self.width, self.y+self.height)

    def outputPS(self, file):
        outstring = ""
        for char in self.chars:
            if char > 32 and char < 127 and chr(char) not in "()[]<>\\":
                ascii = "%s" % chr(char)
            else:
                ascii = "\\%03o" % char
            outstring += ascii
        file.write("%g %g moveto (%s) show\n" % (self.x, self.y, outstring))

    def outputPDF(self, file):
        outstring = ""
        for char in self.chars:
            if char > 32 and char < 127 and chr(char) not in "()[]<>\\":
                ascii = "%s" % chr(char)
            else:
                ascii = "\\%03o" % char
            outstring += ascii
        # file.write("%f %f Td (%s) Tj\n" % (self.x, self.y, outstring))
        file.write("1 0 0 1 %f %f Tm (%s) Tj\n" % (self.x, self.y, outstring))


class fontmapping:

    tokenpattern = re.compile(r'"(.*?)("\s+|"$|$)|(.*?)(\s+|$)')

    def __init__(self, s):
        """ construct font mapping from line s of font mapping file """
        self.texname = self.basepsname = self.fontfile = None

        # standard encoding
        self.encodingfile = None

        # supported postscript fragments occuring in psfonts.map
        self.reencodefont = self.extendfont = self.slantfont = None

        tokens = []
        while len(s):
            match = self.tokenpattern.match(s)
            if match:
                if match.groups()[0]:
                    tokens.append('"%s"' % match.groups()[0])
                else:
                    tokens.append(match.groups()[2])
                s = s[match.end():]
            else:
                raise RuntimeError("wrong syntax")

        for token in tokens:
            if token.startswith("<"):
                if token.startswith("<<"):
                    # XXX: support non-partial download here
                    self.fontfile = token[2:]
                elif token.startswith("<["):
                    self.encodingfile = token[2:]
                elif token.endswith(".pfa") or token.endswith(".pfb"):
                    self.fontfile = token[1:]
                elif token.endswith(".enc"):
                    self.encodingfile = token[1:]
                else:
                    raise RuntimeError("wrong syntax")
            elif token.startswith('"'):
                pscode = token[1:-1].split()
                # parse standard postscript code fragments
                while pscode:
                    try:
                        arg, cmd = pscode[:2]
                    except:
                        raise RuntimeError("Unsupported Postscript fragment '%s'" % pscode)
                    pscode = pscode[2:]
                    if cmd == "ReEncodeFont":
                        self.reencodefont = arg
                    elif cmd == "ExtendFont":
                        self.extendfont = arg
                    elif cmd == "SlantFont":
                        self.slantfont = arg
                    else:
                        raise RuntimeError("Unsupported Postscript fragment '%s %s'" % (arg, cmd))
            else:
                if self.texname is None:
                    self.texname = token
                else:
                    self.basepsname = token
        if self.basepsname is None:
            self.basepsname = self.texname

    def __str__(self):
        return ("'%s' is '%s' read from '%s' encoded as '%s'" %
                (self.texname, self.basepsname, self.fontfile, repr(self.encodingfile)))

# generate fontmap

def readfontmap(filenames):
    """ read font map from filename (without path) """
    fontmap = {}
    for filename in filenames:
        mappath = pykpathsea.find_file(filename, pykpathsea.kpse_fontmap_format)
        # try also the oft-used registration as dvips config file
        if not mappath:
            mappath = pykpathsea.find_file(filename, pykpathsea.kpse_dvips_config_format)
        if not mappath:
            raise RuntimeError("cannot find font mapping file '%s'" % filename)
        mapfile = open(mappath, "r")
        lineno = 0
        for line in mapfile.readlines():
            lineno += 1
            line = line.rstrip()
            if not (line=="" or line[0] in (" ", "%", "*", ";" , "#")):
                try:
                    fm = fontmapping(line)
                except RuntimeError, e:
                    sys.stderr.write("*** PyX Warning: Ignoring line %i in mapping file '%s': %s\n" % (lineno, filename, e))
                else:
                    fontmap[fm.texname] = fm
        mapfile.close()
    return fontmap


class font:
    def __init__(self, name, c, q, d, tfmconv, conv, debug=0):
        self.name = name
        self.q = q                  # desired size of font (fix_word) in tex points
        self.d = d                  # design size of font (fix_word) in tex points
        self.tfmconv = tfmconv      # conversion factor from tfm units to dvi units
        self.conv = conv            # conversion factor from dvi units to PostScript points
        tfmpath = pykpathsea.find_file("%s.tfm" % self.name, pykpathsea.kpse_tfm_format)
        if not tfmpath:
            raise TFMError("cannot find %s.tfm" % self.name)
        self.tfmfile = tfmfile(tfmpath, debug)

        # We only check for equality of font checksums if none of them
        # is zero. The case c == 0 happend in some VF files and
        # according to the VFtoVP documentation, paragraph 40, a check
        # is only performed if tfmfile.checksum > 0. Anyhow, being
        # more generous here seems to be reasonable
        if self.tfmfile.checksum != c and self.tfmfile.checksum != 0 and c !=0:
            raise DVIError("check sums do not agree: %d vs. %d" %
                           (self.tfmfile.checksum, c))

        # tfmfile.designsizeraw is the design size of the font as a fix_word
        if abs(self.tfmfile.designsizeraw - d) > 2:
            raise DVIError("design sizes do not agree: %d vs. %d" % (self.tfmfile.designsizeraw, d))
        if q < 0 or q > 134217728:
            raise DVIError("font '%s' not loaded: bad scale" % self.name)
        if d < 0 or d > 134217728:
            raise DVIError("font '%s' not loaded: bad design size" % self.name)

        self.scale = 1.0*q/d

        # for bookkeeping of used characters
        self.usedchars = [0] * 256

    def __str__(self):
        return "font %s designed at %g tex pts used at %g tex pts" % (self.name, 
                                                                      16.0*self.d/16777216L,
                                                                      16.0*self.q/16777216L)


    __repr__ = __str__

    def getsize_pt(self):
        """ return size of font in (PS) points """
        # The factor 16L/16777216L=2**(-20) converts a fix_word (here self.q)
        # to the corresponding float. Furthermore, we have to convert from TeX
        # points to points, hence the factor 72/72.27.
        return 16L*self.q/16777216L*72/72.27

    def _convert_tfm_to_dvi(self, length):
        return int(round(16L*length*self.q/16777216L*self.tfmconv))

    def _convert_tfm_to_pt(self, length):
        return int(round(16L*length*self.q/16777216L*self.tfmconv)) * self.conv

    # routines returning lengths as integers in dvi units

    def getwidth_dvi(self, charcode):
        return self._convert_tfm_to_dvi(self.tfmfile.width[self.tfmfile.char_info[charcode].width_index])

    def getheight_dvi(self, charcode):
        return self._convert_tfm_to_dvi(self.tfmfile.height[self.tfmfile.char_info[charcode].height_index])

    def getdepth_dvi(self, charcode):
        return self._convert_tfm_to_dvi(self.tfmfile.depth[self.tfmfile.char_info[charcode].depth_index])

    def getitalic_dvi(self, charcode):
        return self._convert_tfm_to_dvi(self.tfmfile.italic[self.tfmfile.char_info[charcode].italic_index])

    # routines returning lengths as floats in PostScript points

    def getwidth_pt(self, charcode):
        return self._convert_tfm_to_pt(self.tfmfile.width[self.tfmfile.char_info[charcode].width_index])

    def getheight_pt(self, charcode):
        return self._convert_tfm_to_pt(self.tfmfile.height[self.tfmfile.char_info[charcode].height_index])

    def getdepth_pt(self, charcode):
        return self._convert_tfm_to_pt(self.tfmfile.depth[self.tfmfile.char_info[charcode].depth_index])

    def getitalic_pt(self, charcode):
        return self._convert_tfm_to_pt(self.tfmfile.italic[self.tfmfile.char_info[charcode].italic_index])

    def markcharused(self, charcode):
        self.usedchars[charcode] = 1

    def mergeusedchars(self, otherfont):
        for i in range(len(self.usedchars)):
            self.usedchars[i] = self.usedchars[i] or otherfont.usedchars[i]

    def clearusedchars(self):
        self.usedchars = [0] * 256


class type1font(font):
    def __init__(self, name, c, q, d, tfmconv, conv, fontmap, debug=0):
        font.__init__(self, name, c, q, d, tfmconv, conv, debug)
        self.fontmapping = fontmap.get(name)
        if self.fontmapping is None:
            raise RuntimeError("no information for font '%s' found in font mapping file, aborting" % name)

    def getbasepsname(self):
        return self.fontmapping.basepsname

    def getpsname(self):
        if self.fontmapping.reencodefont:
            return "%s-%s" % (self.fontmapping.basepsname, self.fontmapping.reencodefont)
        else:
            return self.fontmapping.basepsname

    def getfontfile(self):
        return self.fontmapping.fontfile

    def getencoding(self):
        return self.fontmapping.reencodefont

    def getencodingfile(self):
        return self.fontmapping.encodingfile


class virtualfont(font):
    def __init__(self, name, c, q, d, tfmconv, conv, fontmap, debug=0):
        font.__init__(self, name, c, q, d, tfmconv, conv, debug)
        fontpath = pykpathsea.find_file(name, pykpathsea.kpse_vf_format)
        if fontpath is None or not len(fontpath):
            raise RuntimeError
        self.vffile = vffile(fontpath, self.scale, tfmconv, conv, fontmap, debug > 1)

    def getfonts(self):
        """ return fonts used in virtual font itself """
        return self.vffile.getfonts()

    def getchar(self, cc):
        """ return dvi chunk corresponding to char code cc """
        return self.vffile.getchar(cc)


##############################################################################
# DVI file handling
##############################################################################

_DVI_CHARMIN     =   0 # typeset a character and move right (range min)
_DVI_CHARMAX     = 127 # typeset a character and move right (range max)
_DVI_SET1234     = 128 # typeset a character and move right
_DVI_SETRULE     = 132 # typeset a rule and move right
_DVI_PUT1234     = 133 # typeset a character
_DVI_PUTRULE     = 137 # typeset a rule
_DVI_NOP         = 138 # no operation
_DVI_BOP         = 139 # beginning of page
_DVI_EOP         = 140 # ending of page
_DVI_PUSH        = 141 # save the current positions (h, v, w, x, y, z)
_DVI_POP         = 142 # restore positions (h, v, w, x, y, z)
_DVI_RIGHT1234   = 143 # move right
_DVI_W0          = 147 # move right by w
_DVI_W1234       = 148 # move right and set w
_DVI_X0          = 152 # move right by x
_DVI_X1234       = 153 # move right and set x
_DVI_DOWN1234    = 157 # move down
_DVI_Y0          = 161 # move down by y
_DVI_Y1234       = 162 # move down and set y
_DVI_Z0          = 166 # move down by z
_DVI_Z1234       = 167 # move down and set z
_DVI_FNTNUMMIN   = 171 # set current font (range min)
_DVI_FNTNUMMAX   = 234 # set current font (range max)
_DVI_FNT1234     = 235 # set current font
_DVI_SPECIAL1234 = 239 # special (dvi extention)
_DVI_FNTDEF1234  = 243 # define the meaning of a font number
_DVI_PRE         = 247 # preamble
_DVI_POST        = 248 # postamble beginning
_DVI_POSTPOST    = 249 # postamble ending

_DVI_VERSION     = 2   # dvi version

# position variable indices
_POS_H           = 0
_POS_V           = 1
_POS_W           = 2
_POS_X           = 3
_POS_Y           = 4
_POS_Z           = 5

# reader states
_READ_PRE       = 1
_READ_NOPAGE    = 2
_READ_PAGE      = 3
_READ_POST      = 4 # XXX not used
_READ_POSTPOST  = 5 # XXX not used
_READ_DONE      = 6


class DVIError(exceptions.Exception): pass

# save and restore colors

class _savecolor(base.canvasitem):
    def outputPS(self, file):
        file.write("currentcolor currentcolorspace\n")

    def outputPDF(self, file):
        file.write("q\n")


class _restorecolor(base.canvasitem):
    def outputPS(self, file):
        file.write("setcolorspace setcolor\n")

    def outputPDF(self, file):
        file.write("Q\n")

class _savetrafo(base.canvasitem):
    def outputPS(self, file):
        file.write("matrix currentmatrix\n")

    def outputPDF(self, file):
        file.write("q\n")


class _restoretrafo(base.canvasitem):
    def outputPS(self, file):
        file.write("setmatrix\n")

    def outputPDF(self, file):
        file.write("Q\n")


class dvifile:

    def __init__(self, filename, fontmap, debug=0):
        """ opens the dvi file and reads the preamble """
        self.filename = filename
        self.fontmap = fontmap
        self.debug = debug

        self.fonts = {}
        self.activefont = None

        # stack of fonts and fontscale currently used (used for VFs)
        self.fontstack = []
        self.stack = []

        # pointer to currently active page
        self.actpage = None

        # currently active output: show instance currently used and
        # the corresponding type 1 font
        self.activeshow = None
        self.activetype1font = None

        # stack for self.file, self.fonts and self.stack, needed for VF inclusion
        self.statestack = []

        self.file = binfile(self.filename, "rb")

        # currently read byte in file (for debugging output)
        self.filepos = None

        self._read_pre()

    # helper routines

    def flushout(self):
        """ flush currently active string """
        if self.activeshow is not None:
            if self.debug:
                print "[%s]" % "".join([chr(char) for char in self.activeshow.chars])
            self.actpage.insert(self.activeshow)
            self.activeshow = None

    def begintext(self):
        """ activate the font if is not yet active, closing a currently active
        text object and flushing the output"""
        if isinstance(self.activefont, type1font):
            self.endtext()
            if self.activetype1font != self.activefont and self.activefont:
                self.actpage.insert(_begintextobject())
                self.actpage.insert(selectfont(self.activefont))
                self.activetype1font = self.activefont

    def endtext(self):
        self.flushout()
        if self.activetype1font:
            self.actpage.insert(_endtextobject())
            self.activetype1font = None

    def putrule(self, height, width, advancepos=1):
        self.endtext()
        x1 =  self.pos[_POS_H] * self.conv
        y1 = -self.pos[_POS_V] * self.conv
        w = width * self.conv
        h = height * self.conv

        if height > 0 and width > 0:
            if self.debug:
                pixelw = int(width*self.trueconv*self.mag/1000.0)
                if pixelw < width*self.conv: pixelw += 1
                pixelh = int(height*self.trueconv*self.mag/1000.0)
                if pixelh < height*self.conv: pixelh += 1

                print ("%d: %srule height %d, width %d (%dx%d pixels)" %
                       (self.filepos, advancepos and "set" or "put", height, width, pixelh, pixelw))
            self.actpage.fill(path.rect_pt(x1, y1, w, h))
        else:
            if self.debug:
                print ("%d: %srule height %d, width %d (invisible)" %
                       (self.filepos, advancepos and "set" or "put", height, width))

        if advancepos:
            if self.debug:
                print (" h:=%d+%d=%d, hh:=%d" %
                   (self.pos[_POS_H], width, self.pos[_POS_H]+width, 0))
            self.pos[_POS_H] += width

    def putchar(self, char, advancepos=1):
        dx = advancepos and self.activefont.getwidth_dvi(char) or 0

        if self.debug:
            print ("%d: %schar%d h:=%d+%d=%d, hh:=%d" %
                   (self.filepos,
                    advancepos and "set" or "put",
                    char,
                    self.pos[_POS_H], dx, self.pos[_POS_H]+dx,
                    0))

        if isinstance(self.activefont, type1font):
            if self.activeshow is None:
                self.begintext()
                self.activeshow = _show(self.pos[_POS_H] * self.conv, -self.pos[_POS_V] * self.conv)
            width = self.activefont.getwidth_dvi(char)  * self.conv
            height = self.activefont.getheight_dvi(char) * self.conv
            depth = self.activefont.getdepth_dvi(char) * self.conv
            self.activeshow.addchar(width, height, depth, char)

            self.activefont.markcharused(char)
            self.pos[_POS_H] += dx
        else:
            # virtual font handling
            afterpos = list(self.pos)
            afterpos[_POS_H] += dx
            self._push_dvistring(self.activefont.getchar(char), self.activefont.getfonts(), afterpos,
                                 self.activefont.getsize_pt())


        if not advancepos:
            # XXX: correct !?
            self.flushout()

    def usefont(self, fontnum):
        if self.debug:
            print ("%d: fntnum%i current font is %s" %
                   (self.filepos,
                    fontnum, self.fonts[fontnum].name))

        self.activefont = self.fonts[fontnum]
        self.begintext()

    def definefont(self, cmdnr, num, c, q, d, fontname):
        # cmdnr: type of fontdef command (only used for debugging output)
        # c:     checksum
        # q:     scaling factor (fix_word)
        #        Note that q is actually s in large parts of the documentation.
        # d:     design size (fix_word)

        try:
            font = virtualfont(fontname, c, q/self.tfmconv, d/self.tfmconv, self.tfmconv, self.conv, self.fontmap, self.debug > 1)
        except (TypeError, RuntimeError):
            font = type1font(fontname, c, q/self.tfmconv, d/self.tfmconv, self.tfmconv, self.conv, self.fontmap, self.debug > 1)

        self.fonts[num] = font

        if self.debug:
            print "%d: fntdef%d %i: %s" % (self.filepos, cmdnr, num, fontname)

#            scale = round((1000.0*self.conv*q)/(self.trueconv*d))
#            m = 1.0*q/d
#            scalestring = scale!=1000 and " scaled %d" % scale or ""
#            print ("Font %i: %s%s---loaded at size %d DVI units" %
#                   (num, fontname, scalestring, q))
#            if scale!=1000:
#                print " (this font is magnified %d%%)" % round(scale/10)

    def special(self, s):
        x =  self.pos[_POS_H] * self.conv
        y = -self.pos[_POS_V] * self.conv
        if self.debug:
            print "%d: xxx '%s'" % (self.filepos, s)
        if not s.startswith("PyX:"):
            if s.startswith("Warning:"):
                sys.stderr.write("*** PyX Warning: ignoring special '%s'\n" % s)
                return
            else:
                raise RuntimeError("the special '%s' cannot be handled by PyX, aborting" % s)

        # it is in general not safe to continue using the currently active font because
        # the specials may involve some gsave/grestore operations
        self.endtext()

        command, args = s[4:].split()[0], s[4:].split()[1:]
        if command=="color_begin":
            if args[0]=="cmyk":
                c = color.cmyk(float(args[1]), float(args[2]), float(args[3]), float(args[4]))
            elif args[0]=="gray":
                c = color.gray(float(args[1]))
            elif args[0]=="hsb":
                c = color.hsb(float(args[1]), float(args[2]), float(args[3]))
            elif args[0]=="rgb":
                c = color.rgb(float(args[1]), float(args[2]), float(args[3]))
            elif args[0]=="RGB":
                c = color.rgb(int(args[1])/255.0, int(args[2])/255.0, int(args[3])/255.0)
            elif args[0]=="texnamed":
                try:
                    c = getattr(color.cmyk, args[1])
                except AttributeError:
                    raise RuntimeError("unknown TeX color '%s', aborting" % args[1])
            else:
                raise RuntimeError("color model '%s' cannot be handled by PyX, aborting" % args[0])
            self.actpage.insert(_savecolor())
            self.actpage.insert(c)
        elif command=="color_end":
            self.actpage.insert(_restorecolor())
        elif command=="rotate_begin":
            self.actpage.insert(_savetrafo())
            self.actpage.insert(trafo.rotate_pt(float(args[0]), x, y))
        elif command=="rotate_end":
            self.actpage.insert(_restoretrafo())
        elif command=="scale_begin":
            self.actpage.insert(_savetrafo())
            self.actpage.insert(trafo.scale_pt(float(args[0]), float(args[1]), x, y))
        elif command=="scale_end":
            self.actpage.insert(_restoretrafo())
        elif command=="epsinclude":
            # parse arguments
            argdict = {}
            for arg in args:
                name, value = arg.split("=")
                argdict[name] = value

            # construct kwargs for epsfile constructor
            epskwargs = {}
            epskwargs["filename"] = argdict["file"]
            epskwargs["bbox"] = bbox.bbox_pt(float(argdict["llx"]), float(argdict["lly"]),
                                           float(argdict["urx"]), float(argdict["ury"]))
            if argdict.has_key("width"):
                epskwargs["width"] = float(argdict["width"]) * unit.t_pt
            if argdict.has_key("height"):
                epskwargs["height"] = float(argdict["height"]) * unit.t_pt
            if argdict.has_key("clip"):
               epskwargs["clip"] = int(argdict["clip"])
            self.actpage.insert(epsfile.epsfile(x * unit.t_pt, y * unit.t_pt, **epskwargs))
        elif command=="marker":
            if len(args) != 1:
                raise RuntimeError("marker contains spaces")
            for c in args[0]:
                if c not in string.digits + string.letters + "@":
                    raise RuntimeError("marker contains invalid characters")
            if self.actpage.markers.has_key(args[0]):
                raise RuntimeError("marker name occurred several times")
            self.actpage.markers[args[0]] = x * unit.t_pt, y * unit.t_pt
        else:
            raise RuntimeError("unknown PyX special '%s', aborting" % command)
        self.begintext()

    # routines for pushing and popping different dvi chunks on the reader

    def _push_dvistring(self, dvi, fonts, afterpos, fontsize):
        """ push dvi string with defined fonts on top of reader
        stack. Every positions gets scaled relatively by the factor
        scale. After the interpreting of the dvi chunk has been finished,
        continue with self.pos=afterpos. The designsize of the virtual
        font is passed as a fix_word

        """

        if self.debug:
            print "executing new dvi chunk"
        self.statestack.append((self.file, self.fonts, self.activefont, afterpos, self.stack, self.conv, self.tfmconv))

        # units in vf files are relative to the size of the font and given as fix_words
        # which can be converted to floats by diving by 2**20
        oldconv = self.conv
        self.conv = fontsize/2**20
        rescale = self.conv/oldconv

        self.file = stringbinfile(dvi)
        self.fonts = fonts
        self.stack = []
        self.filepos = 0

        # rescale self.pos in order to be consistent with the new scaling
        self.pos = map(lambda x, rescale=rescale:1.0*x/rescale, self.pos)

        # since tfmconv converts from tfm units to dvi units, rescale it as well
        self.tfmconv /= rescale

        self.usefont(0)

    def _pop_dvistring(self):
        self.flushout()
        if self.debug:
            print "finished executing dvi chunk"
        self.file.close()
        self.file, self.fonts, self.activefont, self.pos, self.stack, self.conv, self.tfmconv = self.statestack.pop()

    # routines corresponding to the different reader states of the dvi maschine

    def _read_pre(self):
        afile = self.file
        while 1:
            self.filepos = afile.tell()
            cmd = afile.readuchar()
            if cmd == _DVI_NOP:
                pass
            elif cmd == _DVI_PRE:
                if afile.readuchar() != _DVI_VERSION: raise DVIError
                num = afile.readuint32()
                den = afile.readuint32()
                self.mag = afile.readuint32()

                # for the interpretation of all quantities, two conversion factors
                # are relevant:
                # - self.tfmconv (tfm units->dvi units)
                # - self.conv (dvi units-> (PostScript) points)

                self.tfmconv = (25400000.0/num)*(den/473628672.0)/16.0

                # calculate self.conv as described in the DVIType docu

                # resolution in dpi
                self.resolution = 300.0
                # self.trueconv = conv in DVIType docu
                self.trueconv = (num/254000.0)*(self.resolution/den)

                # self.conv is the conversion factor from the dvi units
                # to (PostScript) points. It consists of
                # - self.mag/1000.0:   magstep scaling
                # - self.trueconv:     conversion from dvi units to pixels
                # - 1/self.resolution: conversion from pixels to inch
                # - 72               : conversion from inch to points
                self.conv = self.mag/1000.0*self.trueconv/self.resolution*72

                comment = afile.read(afile.readuchar())
                return
            else:
                raise DVIError

    def readpage(self, pageid=None):
        """ reads a page from the dvi file

        This routine reads a page from the dvi file which is
        returned as a canvas. When there is no page left in the
        dvifile, None is returned and the file is closed properly."""


        while 1:
            self.filepos = self.file.tell()
            cmd = self.file.readuchar()
            if cmd == _DVI_NOP:
                pass
            elif cmd == _DVI_BOP:
                # self.endtext()
                ispageid = [self.file.readuint32() for i in range(10)]
                #if ispageid[:3] != [ord("P"), ord("y"), ord("X")] or ispageid[4:] != [0, 0, 0, 0, 0, 0]:
                if pageid is not None and ispageid != pageid:
                    raise DVIError("invalid pageid")
                if self.debug:
                    print "%d: beginning of page %i" % (self.filepos, ispageid[0])
                self.file.readuint32()
                break
            elif cmd == _DVI_POST:
                self.file.close()
                return None # nothing left
            else:
                raise DVIError

        actpage = canvas.canvas()
        self.actpage = actpage # XXX should be removed ...
        self.actpage.markers = {}
        self.pos = [0, 0, 0, 0, 0, 0]
        self.activetype1font = None

        # Since we do not know which dvi pages the actual PS file contains later on,
        # we have to keep track of used char informations separately for each dvi page.
        # In order to do so, the already defined fonts have to be copied and their
        # used char informations have to be reset
        for nr in self.fonts.keys():
            self.fonts[nr] = copy.copy(self.fonts[nr])
            self.fonts[nr].clearusedchars()

        while 1:
            afile = self.file
            self.filepos = afile.tell()
            try:
                cmd = afile.readuchar()
            except struct.error:
                # we most probably (if the dvi file is not corrupt) hit the end of a dvi chunk,
                # so we have to continue with the rest of the dvi file
                self._pop_dvistring()
                continue
            if cmd == _DVI_NOP:
                pass
            if cmd >= _DVI_CHARMIN and cmd <= _DVI_CHARMAX:
                self.putchar(cmd)
            elif cmd >= _DVI_SET1234 and cmd < _DVI_SET1234 + 4:
                self.putchar(afile.readint(cmd - _DVI_SET1234 + 1))
            elif cmd == _DVI_SETRULE:
                self.putrule(afile.readint32(), afile.readint32())
            elif cmd >= _DVI_PUT1234 and cmd < _DVI_PUT1234 + 4:
                self.putchar(afile.readint(cmd - _DVI_PUT1234 + 1), advancepos=0)
            elif cmd == _DVI_PUTRULE:
                self.putrule(afile.readint32(), afile.readint32(), 0)
            elif cmd == _DVI_EOP:
                self.endtext()
                if self.debug:
                    print "%d: eop" % self.filepos
                    print
                return actpage
            elif cmd == _DVI_PUSH:
                self.stack.append(list(self.pos))
                if self.debug:
                    print "%d: push" % self.filepos
                    print ("level %d:(h=%d,v=%d,w=%d,x=%d,y=%d,z=%d,hh=,vv=)" %
                           (( len(self.stack)-1,)+tuple(self.pos)))
            elif cmd == _DVI_POP:
                self.flushout()
                self.pos = self.stack.pop()
                if self.debug:
                    print "%d: pop" % self.filepos
                    print ("level %d:(h=%d,v=%d,w=%d,x=%d,y=%d,z=%d,hh=,vv=)" %
                           (( len(self.stack),)+tuple(self.pos)))
            elif cmd >= _DVI_RIGHT1234 and cmd < _DVI_RIGHT1234 + 4:
                self.flushout()
                dh = afile.readint(cmd - _DVI_RIGHT1234 + 1, 1)
                if self.debug:
                    print ("%d: right%d %d h:=%d%+d=%d, hh:=" %
                           (self.filepos,
                            cmd - _DVI_RIGHT1234 + 1,
                            dh,
                            self.pos[_POS_H],
                            dh,
                            self.pos[_POS_H]+dh))
                self.pos[_POS_H] += dh
            elif cmd == _DVI_W0:
                self.flushout()
                if self.debug:
                    print ("%d: w0 %d h:=%d%+d=%d, hh:=" %
                           (self.filepos,
                            self.pos[_POS_W],
                            self.pos[_POS_H],
                            self.pos[_POS_W],
                            self.pos[_POS_H]+self.pos[_POS_W]))
                self.pos[_POS_H] += self.pos[_POS_W]
            elif cmd >= _DVI_W1234 and cmd < _DVI_W1234 + 4:
                self.flushout()
                self.pos[_POS_W] = afile.readint(cmd - _DVI_W1234 + 1, 1)
                if self.debug:
                    print ("%d: w%d %d h:=%d%+d=%d, hh:=" %
                           (self.filepos,
                            cmd - _DVI_W1234 + 1,
                            self.pos[_POS_W],
                            self.pos[_POS_H],
                            self.pos[_POS_W],
                            self.pos[_POS_H]+self.pos[_POS_W]))
                self.pos[_POS_H] += self.pos[_POS_W]
            elif cmd == _DVI_X0:
                self.flushout()
                self.pos[_POS_H] += self.pos[_POS_X]
            elif cmd >= _DVI_X1234 and cmd < _DVI_X1234 + 4:
                self.flushout()
                self.pos[_POS_X] = afile.readint(cmd - _DVI_X1234 + 1, 1)
                self.pos[_POS_H] += self.pos[_POS_X]
            elif cmd >= _DVI_DOWN1234 and cmd < _DVI_DOWN1234 + 4:
                self.flushout()
                dv = afile.readint(cmd - _DVI_DOWN1234 + 1, 1)
                if self.debug:
                    print ("%d: down%d %d v:=%d%+d=%d, vv:=" %
                           (self.filepos,
                            cmd - _DVI_DOWN1234 + 1,
                            dv,
                            self.pos[_POS_V],
                            dv,
                            self.pos[_POS_V]+dv))
                self.pos[_POS_V] += dv
            elif cmd == _DVI_Y0:
                self.flushout()
                if self.debug:
                    print ("%d: y0 %d v:=%d%+d=%d, vv:=" %
                           (self.filepos,
                            self.pos[_POS_Y],
                            self.pos[_POS_V],
                            self.pos[_POS_Y],
                            self.pos[_POS_V]+self.pos[_POS_Y]))
                self.pos[_POS_V] += self.pos[_POS_Y]
            elif cmd >= _DVI_Y1234 and cmd < _DVI_Y1234 + 4:
                self.flushout()
                self.pos[_POS_Y] = afile.readint(cmd - _DVI_Y1234 + 1, 1)
                if self.debug:
                    print ("%d: y%d %d v:=%d%+d=%d, vv:=" %
                           (self.filepos,
                            cmd - _DVI_Y1234 + 1,
                            self.pos[_POS_Y],
                            self.pos[_POS_V],
                            self.pos[_POS_Y],
                            self.pos[_POS_V]+self.pos[_POS_Y]))
                self.pos[_POS_V] += self.pos[_POS_Y]
            elif cmd == _DVI_Z0:
                self.flushout()
                self.pos[_POS_V] += self.pos[_POS_Z]
            elif cmd >= _DVI_Z1234 and cmd < _DVI_Z1234 + 4:
                self.flushout()
                self.pos[_POS_Z] = afile.readint(cmd - _DVI_Z1234 + 1, 1)
                self.pos[_POS_V] += self.pos[_POS_Z]
            elif cmd >= _DVI_FNTNUMMIN and cmd <= _DVI_FNTNUMMAX:
                self.usefont(cmd - _DVI_FNTNUMMIN)
            elif cmd >= _DVI_FNT1234 and cmd < _DVI_FNT1234 + 4:
                self.usefont(afile.readint(cmd - _DVI_FNT1234 + 1, cmd == _DVI_FNT1234 + 3))
            elif cmd >= _DVI_SPECIAL1234 and cmd < _DVI_SPECIAL1234 + 4:
                self.special(afile.read(afile.readint(cmd - _DVI_SPECIAL1234 + 1)))
            elif cmd >= _DVI_FNTDEF1234 and cmd < _DVI_FNTDEF1234 + 4:
                if cmd == _DVI_FNTDEF1234:
                    num = afile.readuchar()
                elif cmd == _DVI_FNTDEF1234+1:
                    num = afile.readuint16()
                elif cmd == _DVI_FNTDEF1234+2:
                    num = afile.readuint24()
                elif cmd == _DVI_FNTDEF1234+3:
                    # Cool, here we have according to docu a signed int. Why?
                    num = afile.readint32()
                self.definefont(cmd-_DVI_FNTDEF1234+1,
                                num,
                                afile.readint32(),
                                afile.readint32(),
                                afile.readint32(),
                                afile.read(afile.readuchar()+afile.readuchar()))
            else:
                raise DVIError


##############################################################################
# VF file handling
##############################################################################

_VF_LONG_CHAR  = 242              # character packet (long version)
_VF_FNTDEF1234 = _DVI_FNTDEF1234  # font definition
_VF_PRE        = _DVI_PRE         # preamble
_VF_POST       = _DVI_POST        # postamble

_VF_ID         = 202              # VF id byte

class VFError(exceptions.Exception): pass

class vffile:
    def __init__(self, filename, scale, tfmconv, conv, fontmap, debug=0):
        self.filename = filename
        self.scale = scale
        self.tfmconv = tfmconv
        self.conv = conv
        self.fontmap = fontmap
        self.debug = debug
        self.fonts = {}            # used fonts
        self.widths = {}           # widths of defined chars
        self.chardefs = {}         # dvi chunks for defined chars

        afile = binfile(self.filename, "rb")

        cmd = afile.readuchar()
        if cmd == _VF_PRE:
            if afile.readuchar() != _VF_ID: raise VFError
            comment = afile.read(afile.readuchar())
            self.cs = afile.readuint32()
            self.ds = afile.readuint32()
        else:
            raise VFError

        while 1:
            cmd = afile.readuchar()
            if cmd >= _VF_FNTDEF1234 and cmd < _VF_FNTDEF1234 + 4:
                # font definition
                if cmd == _VF_FNTDEF1234:
                    num = afile.readuchar()
                elif cmd == _VF_FNTDEF1234+1:
                    num = afile.readuint16()
                elif cmd == _VF_FNTDEF1234+2:
                    num = afile.readuint24()
                elif cmd == _VF_FNTDEF1234+3:
                    num = afile.readint32()
                c = afile.readint32()
                s = afile.readint32()     # relative scaling used for font (fix_word)
                d = afile.readint32()     # design size of font
                fontname = afile.read(afile.readuchar()+afile.readuchar())

                # rescaled size of font: s is relative to the scaling
                # of the virtual font itself.  Note that realscale has
                # to be a fix_word (like s)
                reals = int(self.scale * float(fix_word(self.ds))*s)

                # print ("defining font %s -- VF scale: %g, VF design size: %g, relative font size: %g => real size: %g" %
                #        (fontname, self.scale, fix_word(self.ds), fix_word(s), fix_word(reals))
                #        )
                # reald = int(d)

                # XXX allow for virtual fonts here too
                self.fonts[num] =  type1font(fontname, c, reals, d, self.tfmconv, self.conv, self.fontmap, self.debug > 1)
            elif cmd == _VF_LONG_CHAR:
                # character packet (long form)
                pl = afile.readuint32()   # packet length
                cc = afile.readuint32()   # char code (assumed unsigned, but anyhow only 0 <= cc < 255 is actually used)
                tfm = afile.readuint24()  # character width
                dvi = afile.read(pl)      # dvi code of character
                self.widths[cc] = tfm
                self.chardefs[cc] = dvi
            elif cmd < _VF_LONG_CHAR:
                # character packet (short form)
                cc = afile.readuchar()    # char code
                tfm = afile.readuint24()  # character width
                dvi = afile.read(cmd)
                self.widths[cc] = tfm
                self.chardefs[cc] = dvi
            elif cmd == _VF_POST:
                break
            else:
                raise VFError

        afile.close()

    def getfonts(self):
        return self.fonts

    def getchar(self, cc):
        return self.chardefs[cc]


