#!/usr/bin/env python

import os, struct

# this code will be part of PyX 0.2 ... ;-)

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

class binfile(file):

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

        self.checksum = self.file.readuint32()
        self.designsize = fix_word(self.file.readint32())
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
            self.width[width_index] = fix_word(self.file.readint32())

        #
        # read heights
        #
            
        self.height = [None for height_index in range(self.nh)]
        for height_index in range(self.nh):
            self.height[height_index] = fix_word(self.file.readint32())

        #
        # read depths
        #

        self.depth = [None for depth_index in range(self.nd)]
        for depth_index in range(self.nd):
            self.depth[depth_index] = fix_word(self.file.readint32())

        #
        # read italic
        #

        self.italic = [None for italic_index in range(self.ni)]
        for italic_index in range(self.ni):
            self.italic[italic_index] = fix_word(self.file.readint32())
        
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
            self.kern[kern_index] = fix_word(self.file.readint32())

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
    def __init__(self, name):
        path = os.popen("kpsewhich %s.tfm" % name, "r").readline()[:-1]
        self.tfmfile = TFMFile(path)

    def __getattr__(self, attr):
        return self.tfmfile.__dict__[attr]

    def getwidth(self, charcode):
        return self.tfmfile.width[self.char_info[charcode].width_index] * self.designsize

    def getheight(self, charcode):
        return self.tfmfile.height[self.char_info[charcode].height_index] * self.designsize

    def getdepth(self, charcode):
        return self.tfmfile.depth[self.char_info[charcode].depth_index] * self.designsize

    def getitalic(self, charcode):
        return self.tfmfile.italic[self.char_info[charcode].italic_index] * self.designsize


class DVIFile:

    def char(self, char, inch=1):
        x = self.pos[_POS_H] * self.scale * 1e-5
        y = self.pos[_POS_V] * self.scale * 1e-5
        ascii = (char > 32 and char < 128) and "(%s)" % chr(char) or "???"
        print "type 0x%08x %s at (%.3f cm, %.3f cm)" % (char, ascii, x, y)
        if inch:
            # XXX what about scaling
            self.pos[_POS_H] += float(self.fonts[self.activefont].getwidth(char))

    def rule(self, height, width, inch=1):
        if height > 0 and width > 0:
            x1 = self.pos[_POS_H] * self.scale * 1e-5
            y1 = self.pos[_POS_V] * self.scale * 1e-5
            x2 = (self.pos[_POS_H] + width) * self.scale * 1e-5
            y2 = (self.pos[_POS_V] + height) * self.scale * 1e-5
            print "rule ((%.3f..%.3f cm), (%.3f..%.3f cm))" % (x1, x2, y1, y2)
        if inch:
            pass # TODO: increment h

    def __init__(self, name):

        file = binfile(name, "rb")
        state = _READ_PRE
        stack = []
        
        # XXX max number of fonts
        self.fonts = [None for i in range(64)]
        self.activefont = None

        while state != _READ_DONE:
            cmd = file.readuchar()
            if cmd == _DVI_NOP: pass

            elif state == _READ_PRE:
                if cmd == _DVI_PRE:
                    if file.readuchar() != _DVI_VERSION: raise DVIError
                    num = file.readuint32()
                    den = file.readuint32()
                    mag = file.readuint32()
                    self.scale = num*mag/1000.0/den
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
                    state = _READ_PAGE
                elif cmd == _DVI_POST:
                    state = _READ_DONE # we skip the rest
                else: raise DVIError

            elif state == _READ_PAGE:
               if cmd >= _DVI_CHARMIN and cmd <= _DVI_CHARMAX:
                   self.char(cmd)
               elif cmd >= _DVI_SET1234 and cmd < _DVI_SET1234 + 4:
                   self.char(file.readint(cmd - _DVI_SET1234 + 1))
               elif cmd == _DVI_SETRULE:
                   self.rule(file.readint32(), file.readint32())
               elif cmd >= _DVI_PUT1234 and cmd < _DVI_PUT1234 + 4:
                   self.char(file.readint(cmd - _DVI_PUT1234 + 1))
               elif cmd == _DVI_PUTRULE:
                   self.rule(file.readint32(), file.readint32(), 0)
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
                   self.activefont = cmd - _DVI_FNTNUMMIN
                   print "use font %i" % self.activefont
               elif cmd >= _DVI_FNT1234 and cmd < _DVI_FNT1234 + 4:
                   self.activefont = file.readint(cmd - _DVI_FNT1234 + 1, 1)
                   print "use font %i" % self.activefont
               elif cmd >= _DVI_SPECIAL1234 and cmd < _DVI_SPECIAL1234 + 4:
                   print "special %s" % file.read(file.readint(cmd - _DVI_SPECIAL1234 + 1))
               elif cmd >= _DVI_FNTDEF1234 and cmd < _DVI_FNTDEF1234 + 4:
                   num = file.readint(cmd - _DVI_FNTDEF1234 + 1)
                   file.readuint32()
                   file.readuint32()
                   file.readuint32()
                   fontname = file.read(file.readuchar()+file.readuchar())
                   self.fonts[num] = Font(fontname)
                   print "font %i is %s" % (num, fontname)

               else: raise DVIError

            else: raise DVIError # unexpected reader state

if __name__=="__main__":
    cmr10 = Font("cmr10")
    print cmr10.charcoding
    print cmr10.fontfamily
    print cmr10.face
    for charcode in range(cmr10.bc, cmr10.ec+1):
        print "%d\th=%f\tw=%f\td=%f\ti=%f" % (
            charcode,
            cmr10.getwidth(charcode),
            cmr10.getheight(charcode),
            cmr10.getdepth(charcode),
            cmr10.getitalic(charcode))
            
    DVIFile("test.dvi")
    
