#!/usr/bin/env python
#
#
# Copyright (C) 2002 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2002 André Wobst <wobsta@users.sourceforge.net>
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


# this code will be part of PyX 0.2 (or 0.3, or ... ???)

import os, threading, Queue, traceback, re, struct
import graph, bbox, unit

###############################################################################
# joergl would mainly work here ...

###############################################################################
# this is the old stuff
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

_DVI_VERSION     = 2 # dvi version

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
_READ_POST      = 4
_READ_POSTPOST  = 5
_READ_DONE      = 6

class fix_word:
    def __init__(self, word):
        if word>=0:
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


class char_info_word:
    def __init__(self, word):
        self.width_index  = (word & 0xFF000000) >> 24
        self.height_index = (word & 0x00F00000) >> 20
        self.depth_index  = (word & 0x000F0000) >> 16
        self.italic_index = (word & 0x0000FC00) >> 10
        self.tag          = (word & 0x00000300) >> 8
        self.remainder    = (word & 0x000000FF)

        if self.width_index==0:
            raise TFMError, "width_index should not be zero"

class binfile(file): # TODO: we should not yet depend on python2.2

    def readint(self, bytes = 4, signed = 0):
        first = 1
        result = 0
        while bytes:
            value = ord(self.read(1))
            if first and signed and value > 127:
                value -= 256
            first = 0
            result = 256 * result + value
            bytes -= 1
        return result

    def readint32(self):
        return struct.unpack(">l", self.read(4))[0]
    
    def readuint32(self):
        return struct.unpack(">L", self.read(4))[0]

    def readint24(self):
        # XXX: checkme
        return struct.unpack(">l", "\0"+self.read(3))[0]

    def readuint24(self):
        # XXX: checkme
        return struct.unpack(">L", "\0"+self.read(3))[0]

    def readint16(self):
        return struct.unpack(">h", self.read(2))[0]
    
    def readuint16(self):
        return struct.unpack(">H", self.read(2))[0]

    def readchar(self):
        return struct.unpack("b", self.read(1))[0]

    def readuchar(self):
        return struct.unpack("B", self.read(1))[0]

    def readstring(self, bytes):
        l = self.readuchar()
        assert l<bytes-1, "inconsistency in file: string too long"
        return self.read(bytes-1)[:l]

class DVIError(Exception): pass

class TFMError(Exception): pass

class TFMFile:
    def __init__(self, name):
        self.file = binfile(name, "rb")

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

        if not (self.bc-1<=self.ec<=255 and 
                self.ne<=256 and 
                self.lf==6+self.lh+(self.ec-self.bc+1)+self.nw+self.nh+self.nd
                +self.ni+self.nl+self.nk+self.ne+self.np):
            raise TFMError, "error in TFM pre-header"

        #
        # read header
        #

        self.checksum = self.file.readint32()
        self.designsizeraw = self.file.readint32()
        assert self.designsizeraw>0, "invald design size"
        self.designsize = fix_word(self.designsizeraw)
        if self.lh>2:
            self.charcoding = self.file.readstring(40)
        else:
            self.charcoding = None

        if self.lh>12:
            self.fontfamily = self.file.readstring(20)
        else:
            self.fontfamily = None

        if self.lh>17:
            self.sevenbitsave = self.file.readuchar()
            # ignore the following two bytes
            self.file.readint16()
            facechar = self.file.readuchar()
            # decode ugly face specification into the Knuth suggested string
            if facechar<18:
                if facechar>=12:
                    self.face = "E"
                    facechar -= 12
                elif facechar>=6:
                    self.face = "C"
                    facechar -= 6
                else:
                    self.face = "R"

                if facechar>=4:
                    self.face = "L" + self.face
                    facechar -= 4
                elif facechar>=2:
                    self.face = "B" + self.face
                    facechar -= 2
                else:
                    self.face = "M" + self.face

                if facechar==1:
                    self.face = self.face[0] + "I" + self.face[1]
                else:
                    self.face = self.face[0] + "R" + self.face[1]

            else:
                self.face = None
        else:
            self.sevenbitsave = self.face = None

        if self.lh>18:
            # just ignore the rest
            self.file.read((self.lh-18)*4)

        #
        # read char_info
        #

        self.char_info = [None for charcode in range(self.ec+1)]
        
        for charcode in range(self.bc, self.ec+1):
            self.char_info[charcode] = char_info_word(self.file.readint32())

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


class Font:
    def __init__(self, name, c, q, d, tfmconv):
        self.name = name
        path = os.popen("kpsewhich %s.tfm" % self.name, "r").readline()[:-1]
        self.tfmfile = TFMFile(path)

        if self.tfmfile.checksum!=c:
            raise DVIError("check sums do not agree: %d vs. %d" %
                           (self.checksum, c))
        
        self.tfmdesignsize = round(tfmconv*self.tfmfile.designsizeraw)

        if abs(self.tfmdesignsize - d)>2:
            raise DVIError("design sizes do not agree: %d vs. %d" %
                           (self.tfmdesignsize, d))


        if q<0 or q>134217728:
            raise DVIError("font '%s' not loaded: bad scale" % fontname)
        
        if d<0 or d>134217728:
            raise DVIError("font '%s' not loaded: bad design size" % fontname)

        self.alpha = 16;
        self.q = self.qorig = q
        while self.q>=8388608:
            self.q = self.q/2
            self.alpha *= 2

        self.beta = 256/self.alpha;
        self.alpha = self.alpha*self.q;

    def __str__(self):
        return "Font(%s)" % self.name

    __repr__ = __str__

    def convert(self, width):
        b0 = width >> 24
        b1 = (width >> 16) & 0xf
        b2 = (width >> 8 ) & 0xf
        b3 = (width      ) & 0xf
#        print width*self.qorig*16/ 16777216, (((((b3*self.q)/256)+(b2*self.q))/256)+(b1*self.q))/self.beta

        if b0==0:
            return (((((b3*self.q)/256)+(b2*self.q))/256)+(b1*self.q))/self.beta
        elif b0==255:
	    return (((((b3*self.q)/256)+(b2*self.q))/256)+(b1*self.q))/self.beta-self.alpha
        else:
            raise TFMError("error in font size")

    def __getattr__(self, attr):
        return self.tfmfile.__dict__[attr]

    def getwidth(self, charcode):
        return self.convert(self.tfmfile.width[self.char_info[charcode].width_index])

    def getheight(self, charcode):
        return self.convert(self.tfmfile.height[self.char_info[charcode].height_index])

    def getdepth(self, charcode):
        return self.convert(self.tfmfile.depth[self.char_info[charcode].depth_index])

    def getitalic(self, charcode):
        return self.convert(self.tfmfile.italic[self.char_info[charcode].italic_index])


class DVIFile:

    def putchar(self, char, inch=1):
        x = self.pos[_POS_H] * self.conv * 1e-5
        y = self.pos[_POS_V] * self.conv * 1e-5
        ascii = (char > 32 and char < 128) and "(%s)" % chr(char) or "???"
        self.actpage.append(("c", unit.t_cm(x), unit.t_cm(y), char))
        print "type 0x%08x %s at (%.3f cm, %.3f cm)" % (char, ascii, x, y)
        if inch:
            self.pos[_POS_H] += self.fonts[self.activefont].getwidth(char)

    def putrule(self, height, width, inch=1):
        if height > 0 and width > 0:
            x1 = self.pos[_POS_H] * self.conv * 1e-5
            y1 = self.pos[_POS_V] * self.conv * 1e-5
            x2 = (self.pos[_POS_H] + width) * self.conv * 1e-5
            y2 = (self.pos[_POS_V] + height) * self.conv * 1e-5
            print "rule ((%.3f..%.3f cm), (%.3f..%.3f cm))" % (x1, x2, y1, y2)
            self.actpage.append(("r", x1, y1, x2, y2))
        if inch:
            pass # TODO: increment h

    def usefont(self, fontnum):
        self.activefont = fontnum
        self.actpage.append(("f", self.fonts[fontnum]))
        print "use font %i" % self.activefont

    def definefont(self, num, c, q, d, fontname):
        # c: checksum
        # q: scaling factor
        #    Note that q is actually s in large parts of the documentation.
        # d: design size
        
        self.fonts[num] =  Font(fontname, c, q, d, self.tfmconv)

        # m = round((1000.0*self.conv*q)/(self.trueconv*d));

    def __init__(self, filename):

        self.filename = filename
        file = binfile(self.filename, "rb")
        state = _READ_PRE
        stack = []
        
        # XXX max number of fonts
        self.fonts = [None for i in range(64)]
        self.activefont = None

        # here goes the result, for each page one list.
        self.pages = []

        # pointer to currently active page
        self.actpage = None

        while state != _READ_DONE:
            cmd = file.readuchar()
            if cmd == _DVI_NOP: pass

            elif state == _READ_PRE:
                if cmd == _DVI_PRE:
                    if file.readuchar() != _DVI_VERSION: raise DVIError
                    num = file.readuint32()
                    den = file.readuint32()
                    mag = file.readuint32()
                    
                    # self.trueconv = conv in DVIType docu
                    # if resolution = 254000.0

                    self.tfmconv = (25400000.0/num)*(den/473628672)/16.0;
                    self.trueconv = 1.0*num/den
                    self.conv = self.trueconv*(mag/1000.0)
                    
                    comment = file.read(file.readuchar())
                    state = _READ_NOPAGE
                else: raise DVIError

            elif state == _READ_NOPAGE:
                if cmd == _DVI_BOP:
                    print "page",
                    for i in range(10): print file.readuint32(),
                    print
                    file.readuint32()
                    self.pos = [0, 0, 0, 0, 0, 0]
                    self.pages.append([])
                    self.actpage = self.pages[-1]
                    state = _READ_PAGE
                elif cmd == _DVI_POST:
                    state = _READ_DONE # we skip the rest
                else: raise DVIError

            elif state == _READ_PAGE:
               if cmd >= _DVI_CHARMIN and cmd <= _DVI_CHARMAX:
                   self.putchar(cmd)
               elif cmd >= _DVI_SET1234 and cmd < _DVI_SET1234 + 4:
                   self.putchar(file.readint(cmd - _DVI_SET1234 + 1))
               elif cmd == _DVI_SETRULE:
                   self.putrule(file.readint32(), file.readint32())
               elif cmd >= _DVI_PUT1234 and cmd < _DVI_PUT1234 + 4:
                   self.putchar(file.readint(cmd - _DVI_PUT1234 + 1))
               elif cmd == _DVI_PUTRULE:
                   self.putrule(file.readint32(), file.readint32(), 0)
               elif cmd == _DVI_EOP:
                   state = _READ_NOPAGE
               elif cmd == _DVI_PUSH:
                   stack.append(tuple(self.pos))
               elif cmd == _DVI_POP:
                   self.pos = list(stack[-1])
                   del stack[-1]
               elif cmd >= _DVI_RIGHT1234 and cmd < _DVI_RIGHT1234 + 4:
                   self.pos[_POS_H] += file.readint(cmd - _DVI_RIGHT1234 + 1, 1)
               elif cmd == _DVI_W0:
                   self.pos[_POS_H] += self.pos[_POS_W]
               elif cmd >= _DVI_W1234 and cmd < _DVI_W1234 + 4:
                   self.pos[_POS_W] = file.readint(cmd - _DVI_W1234 + 1, 1)
                   self.pos[_POS_H] += self.pos[_POS_W]
               elif cmd == _DVI_X0:
                   self.pos[_POS_H] += self.pos[_POS_X]
               elif cmd >= _DVI_X1234 and cmd < _DVI_X1234 + 4:
                   self.pos[_POS_X] = file.readint(cmd - _DVI_X1234 + 1, 1)
                   self.pos[_POS_H] += self.pos[_POS_X]
               elif cmd >= _DVI_DOWN1234 and cmd < _DVI_DOWN1234 + 4:
                   self.pos[_POS_V] += file.readint(cmd - _DVI_DOWN1234 + 1, 1)
               elif cmd == _DVI_Y0:
                   self.pos[_POS_V] += self.pos[_POS_Y]
               elif cmd >= _DVI_Y1234 and cmd < _DVI_Y1234 + 4:
                   self.pos[_POS_Y] = file.readint(cmd - _DVI_Y1234 + 1, 1)
                   self.pos[_POS_V] += self.pos[_POS_Y]
               elif cmd == _DVI_Z0:
                   self.pos[_POS_V] += self.pos[_POS_Z]
               elif cmd >= _DVI_Z1234 and cmd < _DVI_Z1234 + 4:
                   self.pos[_POS_Z] = file.readint(cmd - _DVI_Z1234 + 1, 1)
                   self.pos[_POS_V] += self.pos[_POS_Z]
               elif cmd >= _DVI_FNTNUMMIN and cmd <= _DVI_FNTNUMMAX:
                   self.usefont(cmd - _DVI_FNTNUMMIN)
               elif cmd >= _DVI_FNT1234 and cmd < _DVI_FNT1234 + 4:
                   self.usefont(file.readint(cmd - _DVI_FNT1234 + 1, 1))
               elif cmd >= _DVI_SPECIAL1234 and cmd < _DVI_SPECIAL1234 + 4:
                   print "special %s" % file.read(file.readint(cmd - _DVI_SPECIAL1234 + 1))
               elif cmd >= _DVI_FNTDEF1234 and cmd < _DVI_FNTDEF1234 + 4:
                   if cmd==_DVI_FNTDEF1234:
                       num=file.readuchar()
                   elif cmd==_DVI_FNTDEF1234+1:
                       num=file.readuint16()
                   elif cmd==_DVI_FNTDEF1234+2:
                       num=file.readuint24()
                   elif cmd==_DVI_FNTDEF1234+3:
                       # Cool, here we have according to docu a signed int. Why?
                       num=file.readint32()

                   self.definefont(num,
                                   file.readint32(),
                                   file.readint32(),
                                   file.readint32(),
                                   file.read(file.readuchar()+file.readuchar()))
               else: raise DVIError

            else: raise DVIError # unexpected reader state

    def writeheader(self, file):
        """write PostScript font header"""
        for font in self.fonts:
            if font:
                file.write("%%%%BeginFont: %s\n" % font.name.upper())
                # pfbpath = os.popen("kpsewhich %s.pfb" % font.name, "r").readline()[:-1]
                os.system("pfb2pfa `kpsewhich %s.pfb` /tmp/f.pfa" % font.name)
                pfa = open("/tmp/f.pfa", "r")
                file.write(pfa.read())
                pfa.close()
                file.write("%%%%EndFont\n")

    def write(self, file, page):
        """write PostScript code for page into file"""
        print "dvifile(\"%s\").write() for page %s called" % (self.filename, page)
        for el in self.pages[page-1]:
            command, arg = el[0], el[1:]
#            print "\t", command, arg
            if command=="c":
                x, y, c = arg
                file.write("%f %f moveto (%c) show\n" %
                           (unit.topt(x), unit.topt(y), c))
            elif command=="f":
                file.write("/%s findfont\n" % arg[0].name.upper())
                file.write("%d scalefont\n" % 10)
                file.write("setfont\n")

        

#if __name__=="__main__":
#    cmr10 = Font("cmr10")
#    print cmr10.charcoding
#    print cmr10.fontfamily
#    print cmr10.face
#    for charcode in range(cmr10.bc, cmr10.ec+1):
#       print "%d\th=%f\tw=%f\td=%f\ti=%f" % (
#            charcode,
#            cmr10.getwidth(charcode),
#            cmr10.getheight(charcode),
#            cmr10.getdepth(charcode),
#            cmr10.getitalic(charcode))
            
#    dvifile = DVIFile("test.dvi")
#    print [font for font in dvifile.fonts if font]

# end of old stuff
###############################################################################

###############################################################################
# wobsta would mainly work here ...

class TexResultError(Exception):

    def __init__(self, description, texrunner):
        self.description = description
        self.texrunner = texrunner

    def __str__(self):
        return ("%s\n" % self.description +
                "The expression passed to TeX was:\n" +
                "%s\n" % self.texrunner.expression +
                "The return message from TeX was:\n"
                "%s" % self.texrunner.texresult)

class TexResultWarning(TexResultError): pass

class texcheckres: pass

class _texcheckresstart(texcheckres):

    def check(self, texrunner):
        if not texrunner.texresult.startswith("This is TeX, Version 3."):
            raise TexResultError("TeX starting message missing", texrunner)
        if texrunner.texresult.find("OK, entering \scrollmode...") == -1:
            raise TexResultError("switching to scrollmode seemingly failed", texrunner)

texcheckres.start = _texcheckresstart()

class _readpipe(threading.Thread):

    def __init__(self, pipe, expectqueue, gotevent, gotqueue):
        threading.Thread.__init__(self)
        self.setDaemon(1)
        self.pipe = pipe
        self.expect = None
        self.expectqueue = expectqueue
        self.gotevent = gotevent
        self.gotqueue = gotqueue
        self.start()

    def run(self):
        while 1:
            read = self.pipe.readline()
            try:
                self.expect = self.expectqueue.get_nowait()
            except Queue.Empty:
                pass
            if len(read):
                self.gotqueue.put(read)
            if self.expect is not None and read.find(self.expect) != -1:
                self.expect = None
                self.gotevent.set()


class textbox(graph._rectbox):

    def __init__(self, left, right, height, depth, texrunner, page):
        graph._rectbox.__init__(self, -left, -depth, right, height)
        self.texrunner = texrunner
        self.page = page
        # the following is temporary (for the bbox method)
        self.left = left
        self.right = right
        self.height = height
        self.depth = depth

    def bbox(self):
        # should be done within rectbox or alignbox (by the way, the name should be changed)
        return bbox.bbox(-self.left, -self.depth, self.right, self.height)

    def write(self, file):
        self.texrunner.write(file, self.page)


class TexRunsError(Exception): pass
class TexDoneError(Exception): pass
class TexNotInDefineModeError(Exception): pass


class texrunner:

    def __init__(self):
        self.texruns = 0
        self.texdone = 0
        self.definemode = 1
        self.mode = "tex"
        self.docclass = "article"
        self.docopt = None
        self.auxfilename = None
        self.waitfortex = 3
        self.executeid = -1
        self.page = -1
        self.texfilename = "notemprightnow"
        self.usefiles = None

    def execute(self, expression, *checks):
        if not self.texruns:
            texfile = open("%s.tex" % self.texfilename, "w") # start with filename -> creates dvi file with that name
            texfile.write("\\relax\n")
            texfile.close()
            self.texinput, self.texoutput = os.popen4("%s %s" % (self.mode, self.texfilename), "t", 0)
            self.expectqueue = Queue.Queue()
            self.gotevent = threading.Event()
            self.gotqueue = Queue.Queue()
            self.readoutput = _readpipe(self.texoutput, self.expectqueue, self.gotevent, self.gotqueue)
            self.texruns = 1
            olddefinemode = self.definemode
            self.definemode = 1
            # self.execute("\\raiseerror") # timeout test
            self.execute("\\raiseerror%\ns\n" + # switch to nonstop-mode
                         "\\def\\PyX{P\\kern-.3em\\lower.5ex\hbox{Y}\kern-.18em X}%\n" +
                         "\\newbox\\PyXBox%\n" +
                         "\\def\\ProcessPyXBox#1{%\n" +
                         "\\immediate\\write16{PyXBox(page=#1," +
                                                     "wd=\\the\\wd\\PyXBox," +
                                                     "ht=\\the\\ht\\PyXBox," +
                                                     "dp=\\the\\dp\\PyXBox)}%\n" +
                         "{\\count0=80\\count1=121\\count2=88\\count3=#1\\shipout\\copy\\PyXBox}}%\n" +
                         "\\def\\ProcessPyXFinished#1{\\immediate\\write16{ProcessPyXFinishedMarker(#1)}}",
                         texcheckres.start)
            os.remove("%s.tex" % self.texfilename)
            if self.mode == "latex":
                if self.docopt is not None:
                    self.execute("\\documentclass[%s]{%s}" % (self.docopt, self.docclass))
                else:
                    self.execute("\\documentclass{%s}" % self.docclass)
            self.definemode = olddefinemode
        self.executeid += 1
        if expression is not None:
            self.expectqueue.put("ProcessPyXFinishedMarker(%i)" % self.executeid)
            if self.definemode:
                self.expression = ("%s%%\n" % expression +
                                   "\\ProcessPyXFinished{%i}%%\n" % self.executeid)
            else:
                self.page += 1
                self.expression = ("\\setbox\\PyXBox=\\hbox{{%s}}%%\n" % expression +
                                   "\\ProcessPyXBox{%i}%%\n" % self.page +
                                   "\\ProcessPyXFinished{%i}%%\n" % self.executeid)
            self.texinput.write(self.expression)
        else:
            self.expectqueue.put("Transcript written on %s.log" % self.texfilename)
            if self.mode == "latex":
                self.expression = "\\end{document}\n"
            else:
                self.expression = "\\end\n"
            self.texinput.write(self.expression)
        self.gotevent.wait(self.waitfortex)
        nogotevent = not self.gotevent.isSet()
        self.gotevent.clear()
        try:
            self.texresult = ""
            while 1:
                self.texresult += self.gotqueue.get_nowait()
        except Queue.Empty:
            pass
        if nogotevent:
            raise TexResultError("TeX didn't respond as expected within %i seconds." % self.waitfortex, self)
        else:
            for check in checks:
                try:
                    check.check(self)
                except TexResultWarning:
                    traceback.print_exc()
        if expression is None:
            self.texruns = 0
            self.texdone = 1

    def write(self, file, page):
        if not self.texdone:
            self.page += 1
            _default.execute(None)
            self.dvifile = DVIFile("%s.dvi" % self.texfilename)
            self.dvifile.writeheader(file)
        # XXX: the following is a temporary hack to allow the insertion
        # of the header on the first call of the write funtion
        else:
            return self.dvifile.write(file, page)

    def set(self, mode=None, waitfortex=None):
        if self.texruns:
            raise TexRunsError
        if self.texdone:
            raise TexDoneError
        if mode is not None:
            if mode != "tex" and mode != "latex":
                raise ValueError("mode \"tex\" or \"latex\" expected")
            self.mode = mode
        if waitfortex is not None:
            self.waitfortex = waitfortex

    def define(self, expression, *args):
        if self.texdone:
            raise TexDoneError
        if not self.definemode:
            raise TexNotInDefineModeError
        self.execute(expression)

    PyXBoxPattern = re.compile(r"PyXBox\(page=(?P<page>\d+),wd=(?P<wd>-?\d*((\d\.?)|(\.?\d))\d*)pt,ht=(?P<ht>-?\d*((\d\.?)|(\.?\d))\d*)pt,dp=(?P<dp>-?\d*((\d\.?)|(\.?\d))\d*)pt\)")

    def text(self, expression, *args):
        if self.texdone:
            raise TexDoneError
        if self.definemode:
            if self.mode == "latex":
                self.execute("\\begin{document}")
            self.definemode = 0
        self.execute(expression)
        match = self.PyXBoxPattern.search(self.texresult)
        if not match or int(match.group("page")) != self.page:
            raise TexResultError("box extents not found", self)
        else:
            left = 0
            right, height, depth = map(lambda x: float(x) * 72.0 / 72.27, match.group("wd", "ht", "dp"))
        return textbox(left, right, height, depth, self, self.executeid)

_default = texrunner()
set = _default.set
define = _default.define
text = _default.text

###############################################################################

if __name__=="__main__":

    res1 = text("\\hbox{$x$}")
    print res1.bbox()
    res2 = text("test", 1, 1)
    res3 = text("bla und nochmals bla", 2, 2)
    print res2.bbox()
    print res3.bbox()

    file = open("test.ps", "w")
    
    file.write("%!PS-Adobe-3.0 EPSF 3.0\n")
    file.write("%%BoundingBox: -10 -10 100 100\n")
    file.write("%%EndComments\n")

    file.write("%%BeginProlog\n")

    # res*.collectfontheader ???
    # we need to find a way to write the headers in the PS prolog!
    res1.write(file)
    
    file.write("%%EndProlog\n")

    
    res1.write(file)
    res3.write(file)
    res2.write(file)
    
    file.write("showpage\n")
    file.write("%%Trailer\n")
    file.write("%%EOF\n")


