#!/usr/bin/env python

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


class DVIError(Exception): pass

class dvifile:

    def char(self, char, inch=1):
        x = self.pos[_POS_H] * self.scale * 1e-5
        y = self.pos[_POS_V] * self.scale * 1e-5
        ascii = (char > 32 and char < 128) and "(%s)" % chr(char) or "???"
        print "type 0x%08x %s at (%.3f cm, %.3f cm)" % (char, ascii, x, y)
        if inch:
            pass # TODO: increment h

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

        while state != _READ_DONE:
            cmd = file.readint(1)
            if cmd == _DVI_NOP: pass

            elif state == _READ_PRE:
                if cmd == _DVI_PRE:
                    if file.readint(bytes = 1) != _DVI_VERSION: raise DVIError
                    num = file.readint()
                    den = file.readint()
                    mag = file.readint()
                    self.scale = num*mag/1000.0/den
                    comment = file.read(file.readint(1))
                    state = _READ_NOPAGE
                else: raise DVIError

            elif state == _READ_NOPAGE:
                if cmd == _DVI_BOP:
                    print "page",
                    for i in range(10): print file.readint(),
                    print
                    file.readint()
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
                   self.rule(file.readint(4, 1), file.readint(4, 1))
               elif cmd >= _DVI_PUT1234 and cmd < _DVI_PUT1234 + 4:
                   self.char(file.readint(cmd - _DVI_PUT1234 + 1))
               elif cmd == _DVI_PUTRULE:
                   self.rule(file.readint(4, 1), file.readint(4, 1), 0)
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
                   print "use font %i" % (cmd - _DVI_FNTNUMMIN)
               elif cmd >= _DVI_FNT1234 and cmd < _DVI_FNT1234 + 4:
                   print "use font %i" % file.readint(cmd - _DVI_FNT1234 + 1, 1)
               elif cmd >= _DVI_SPECIAL1234 and cmd < _DVI_SPECIAL1234 + 4:
                   print "special %s" % file.read(file.readint(cmd - _DVI_SPECIAL1234 + 1))
               elif cmd >= _DVI_FNTDEF1234 and cmd < _DVI_FNTDEF1234 + 4:
                   num = file.readint(cmd - _DVI_FNTDEF1234 + 1)
                   file.readint(4), file.readint(4), file.readint(4)
                   print "font %i is %s" % (num, file.read(file.readint(1)+
                                                           file.readint(1)))
               else: raise DVIError

            else: raise DVIError # unexpected reader state

dvifile("test.dvi")


