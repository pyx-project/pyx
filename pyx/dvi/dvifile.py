# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2002-2006 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2003-2004,2006,2007 Michael Schindler <m-schindler@users.sourceforge.net>
# Copyright (C) 2002-2006 André Wobst <wobsta@users.sourceforge.net>
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

import cStringIO, exceptions, re, struct, string, sys, warnings, math
from pyx import unit, epsfile, bbox, canvas, color, trafo, path, pykpathsea, reader, type1font
import tfmfile, texfont


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

class _savecolor(canvas.canvasitem):
    def processPS(self, file, writer, context, registry, bbox):
        file.write("currentcolor currentcolorspace\n")

    def processPDF(self, file, writer, context, registry, bbox):
        file.write("q\n")


class _restorecolor(canvas.canvasitem):
    def processPS(self, file, writer, context, registry, bbox):
        file.write("setcolorspace setcolor\n")

    def processPDF(self, file, writer, context, registry, bbox):
        file.write("Q\n")

class _savetrafo(canvas.canvasitem):
    def processPS(self, file, writer, context, registry, bbox):
        file.write("matrix currentmatrix\n")

    def processPDF(self, file, writer, context, registry, bbox):
        file.write("q\n")


class _restoretrafo(canvas.canvasitem):
    def processPS(self, file, writer, context, registry, bbox):
        file.write("setmatrix\n")

    def processPDF(self, file, writer, context, registry, bbox):
        file.write("Q\n")


class DVIfile:

    def __init__(self, filename, debug=0, debugfile=sys.stdout):
        """ opens the dvi file and reads the preamble """
        self.filename = filename
        self.debug = debug
        self.debugfile = debugfile
        self.debugstack = []

        self.fonts = {}
        self.activefont = None

        # stack of fonts and fontscale currently used (used for VFs)
        self.fontstack = []
        self.stack = []

        # pointer to currently active page
        self.actpage = None

        # stack for self.file, self.fonts and self.stack, needed for VF inclusion
        self.statestack = []

        self.file = reader.reader(self.filename)

        # currently read byte in file (for debugging output)
        self.filepos = None

        self._read_pre()

    # helper routines

    def flushtext(self):
        """ finish currently active text object """
        if self.activetext:
            # self.actpage.insert(self.activefont.text_pt(self.pos[_POS_H] * self.pyxconv, -self.pos[_POS_V] * self.pyxconv, font))
            self.actpage.insert(self.activefont.text(self.pos[_POS_H], self.pos[_POS_V], self.activetext))

        if self.debug and self.activetext:
            self.debugfile.write("[%s]\n" % "".join([chr(char) for char in self.activetext]))

        self.activetext = []

    def putrule(self, height, width, advancepos=1):
        self.flushtext()
        x1 =  self.pos[_POS_H] * self.pyxconv
        y1 = -self.pos[_POS_V] * self.pyxconv
        w = width * self.pyxconv
        h = height * self.pyxconv

        if height > 0 and width > 0:
            if self.debug:
                self.debugfile.write("%d: %srule height %d, width %d (???x??? pixels)\n" %
                                     (self.filepos, advancepos and "set" or "put", height, width))
            self.actpage.fill(path.rect_pt(x1, y1, w, h))
        else:
            if self.debug:
                self.debugfile.write("%d: %srule height %d, width %d (invisible)\n" %
                                     (self.filepos, advancepos and "set" or "put", height, width))

        if advancepos:
            if self.debug:
                self.debugfile.write(" h:=%d+%d=%d, hh:=???\n" %
                                     (self.pos[_POS_H], width, self.pos[_POS_H]+width))
            self.pos[_POS_H] += width

    def putchar(self, char, advancepos=1, id1234=0):
        dx = advancepos and self.activefont.getwidth_dvi(char) or 0

        if self.debug:
            self.debugfile.write("%d: %s%s%d h:=%d+%d=%d, hh:=???\n" %
                                 (self.filepos,
                                  advancepos and "set" or "put",
                                  id1234 and "%i " % id1234 or "char",
                                  char,
                                  self.pos[_POS_H], dx, self.pos[_POS_H]+dx))

        if isinstance(self.activefont, texfont.virtualfont):
            # virtual font handling
            afterpos = list(self.pos)
            afterpos[_POS_H] += dx
            self._push_dvistring(self.activefont.getchar(char), self.activefont.getfonts(), afterpos,
                                 self.activefont.getsize_pt())
        else:
            self.activetext.append(char)
            self.pos[_POS_H] += dx

        if not advancepos:
            self.flushtext()

    def usefont(self, fontnum, id1234=0):
        self.flushtext()
        self.activefont = self.fonts[fontnum]
        if self.debug:
            self.debugfile.write("%d: fnt%s%i current font is %s\n" %
                                 (self.filepos,
                                  id1234 and "%i " % id1234 or "num",
                                  fontnum,
                                  self.fonts[fontnum].name))


    def definefont(self, cmdnr, num, c, q, d, fontname):
        # cmdnr: type of fontdef command (only used for debugging output)
        # c:     checksum
        # q:     scaling factor (fix_word)
        #        Note that q is actually s in large parts of the documentation.
        # d:     design size (fix_word)

        try:
            afont = texfont.virtualfont(fontname, c, q/self.tfmconv, d/self.tfmconv, self.tfmconv, self.pyxconv, self.debug > 1)
        except (TypeError, RuntimeError):
            afont = texfont.TeXfont(fontname, c, q/self.tfmconv, d/self.tfmconv, self.tfmconv, self.pyxconv, self.debug > 1)

        self.fonts[num] = afont

        if self.debug:
            self.debugfile.write("%d: fntdef%d %i: %s\n" % (self.filepos, cmdnr, num, fontname))

#            scale = round((1000.0*self.conv*q)/(self.trueconv*d))
#            m = 1.0*q/d
#            scalestring = scale!=1000 and " scaled %d" % scale or ""
#            print ("Font %i: %s%s---loaded at size %d DVI units" %
#                   (num, fontname, scalestring, q))
#            if scale!=1000:
#                print " (this font is magnified %d%%)" % round(scale/10)

    def special(self, s):
        x =  self.pos[_POS_H] * self.pyxconv
        y = -self.pos[_POS_V] * self.pyxconv
        if self.debug:
            self.debugfile.write("%d: xxx '%s'\n" % (self.filepos, s))
        if not s.startswith("PyX:"):
            warnings.warn("ignoring special '%s'" % s)
            return

        # it is in general not safe to continue using the currently active font because
        # the specials may involve some gsave/grestore operations
        self.flushtext()

        command, args = s[4:].split()[0], s[4:].split()[1:]
        if command == "color_begin":
            if args[0] == "cmyk":
                c = color.cmyk(float(args[1]), float(args[2]), float(args[3]), float(args[4]))
            elif args[0] == "gray":
                c = color.gray(float(args[1]))
            elif args[0] == "hsb":
                c = color.hsb(float(args[1]), float(args[2]), float(args[3]))
            elif args[0] == "rgb":
                c = color.rgb(float(args[1]), float(args[2]), float(args[3]))
            elif args[0] == "RGB":
                c = color.rgb(int(args[1])/255.0, int(args[2])/255.0, int(args[3])/255.0)
            elif args[0] == "texnamed":
                try:
                    c = getattr(color.cmyk, args[1])
                except AttributeError:
                    raise RuntimeError("unknown TeX color '%s', aborting" % args[1])
            elif args[0] == "pyxcolor":
                # pyx.color.cmyk.PineGreen or
                # pyx.color.cmyk(0,0,0,0.0)
                pat = re.compile(r"(pyx\.)?(color\.)?(?P<model>(cmyk)|(rgb)|(grey)|(gray)|(hsb))[\.]?(?P<arg>.*)")
                sd = pat.match(" ".join(args[1:]))
                if sd:
                    sd = sd.groupdict()
                    if sd["arg"][0] == "(":
                        numpat = re.compile(r"[+-]?((\d+\.\d*)|(\d*\.\d+)|(\d+))([eE][+-]\d+)?")
                        arg = tuple([float(x[0]) for x in numpat.findall(sd["arg"])])
                        try:
                            c = getattr(color, sd["model"])(*arg)
                        except TypeError or AttributeError:
                            raise RuntimeError("cannot access PyX color '%s' in TeX, aborting" % " ".join(args[1:]))
                    else:
                        try:
                            c = getattr(getattr(color, sd["model"]), sd["arg"])
                        except AttributeError:
                            raise RuntimeError("cannot access PyX color '%s' in TeX, aborting" % " ".join(args[1:]))
                else:
                    raise RuntimeError("cannot access PyX color '%s' in TeX, aborting" % " ".join(args[1:]))
            else:
                raise RuntimeError("color model '%s' cannot be handled by PyX, aborting" % args[0])
            self.actpage.insert(_savecolor())
            self.actpage.insert(c)
        elif command == "color_end":
            self.actpage.insert(_restorecolor())
        elif command == "rotate_begin":
            self.actpage.insert(_savetrafo())
            self.actpage.insert(trafo.rotate_pt(float(args[0]), x, y))
        elif command == "rotate_end":
            self.actpage.insert(_restoretrafo())
        elif command == "scale_begin":
            self.actpage.insert(_savetrafo())
            self.actpage.insert(trafo.scale_pt(float(args[0]), float(args[1]), x, y))
        elif command == "scale_end":
            self.actpage.insert(_restoretrafo())
        elif command == "epsinclude":
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
        elif command == "marker":
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

    # routines for pushing and popping different dvi chunks on the reader

    def _push_dvistring(self, dvi, fonts, afterpos, fontsize):
        """ push dvi string with defined fonts on top of reader
        stack. Every positions gets scaled relatively by the factor
        scale. After the interpreting of the dvi chunk has been finished,
        continue with self.pos=afterpos. The designsize of the virtual
        font is passed as a fix_word

        """

        #if self.debug:
        #    self.debugfile.write("executing new dvi chunk\n")
        self.debugstack.append(self.debug)
        self.debug = 0

        self.statestack.append((self.file, self.fonts, self.activefont, afterpos, self.stack, self.pyxconv, self.tfmconv))

        # units in vf files are relative to the size of the font and given as fix_words
        # which can be converted to floats by diving by 2**20
        oldpyxconv = self.pyxconv
        self.pyxconv = fontsize/2**20
        rescale = self.pyxconv/oldpyxconv

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
        self.flushtext()
        #if self.debug:
        #    self.debugfile.write("finished executing dvi chunk\n")
        self.debug = self.debugstack.pop()

        self.file.close()
        self.file, self.fonts, self.activefont, self.pos, self.stack, self.pyxconv, self.tfmconv = self.statestack.pop()

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

                # For the interpretation of the lengths in dvi and tfm files, 
                # three conversion factors are relevant:
                # - self.tfmconv: tfm units -> dvi units
                # - self.pyxconv: dvi units -> (PostScript) points
                # - self.conv:    dvi units -> pixels
                self.tfmconv = (25400000.0/num)*(den/473628672.0)/16.0

                # calculate conv as described in the DVIType docu using 
                # a given resolution in dpi
                self.resolution = 300.0
                self.conv = (num/254000.0)*(self.resolution/den)

                # self.pyxconv is the conversion factor from the dvi units
                # to (PostScript) points. It consists of
                # - self.mag/1000.0:   magstep scaling
                # - self.conv:         conversion from dvi units to pixels
                # - 1/self.resolution: conversion from pixels to inch
                # - 72               : conversion from inch to points
                self.pyxconv = self.mag/1000.0*self.conv/self.resolution*72

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
                ispageid = [self.file.readuint32() for i in range(10)]
                if pageid is not None and ispageid != pageid:
                    raise DVIError("invalid pageid")
                if self.debug:
                    self.debugfile.write("%d: beginning of page %i\n" % (self.filepos, ispageid[0]))
                self.file.readuint32()
                break
            elif cmd == _DVI_POST:
                self.file.close()
                return None # nothing left
            else:
                raise DVIError

        self.actpage = canvas.canvas()
        self.actpage.markers = {}
        self.pos = [0, 0, 0, 0, 0, 0]

        # list of codepoints to be output
        self.activetext = []

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
                self.putchar(afile.readint(cmd - _DVI_SET1234 + 1), id1234=cmd-_DVI_SET1234+1)
            elif cmd == _DVI_SETRULE:
                self.putrule(afile.readint32(), afile.readint32())
            elif cmd >= _DVI_PUT1234 and cmd < _DVI_PUT1234 + 4:
                self.putchar(afile.readint(cmd - _DVI_PUT1234 + 1), advancepos=0, id1234=cmd-_DVI_SET1234+1)
            elif cmd == _DVI_PUTRULE:
                self.putrule(afile.readint32(), afile.readint32(), 0)
            elif cmd == _DVI_EOP:
                self.flushtext()
                if self.debug:
                    self.debugfile.write("%d: eop\n \n" % self.filepos)
                return self.actpage
            elif cmd == _DVI_PUSH:
                self.stack.append(list(self.pos))
                if self.debug:
                    self.debugfile.write("%s: push\n"
                                         "level %d:(h=%d,v=%d,w=%d,x=%d,y=%d,z=%d,hh=???,vv=???)\n" %
                                         ((self.filepos, len(self.stack)-1) + tuple(self.pos)))
            elif cmd == _DVI_POP:
                self.flushtext()
                self.pos = self.stack.pop()
                if self.debug:
                    self.debugfile.write("%s: pop\n"
                                         "level %d:(h=%d,v=%d,w=%d,x=%d,y=%d,z=%d,hh=???,vv=???)\n" %
                                         ((self.filepos, len(self.stack)) + tuple(self.pos)))
            elif cmd >= _DVI_RIGHT1234 and cmd < _DVI_RIGHT1234 + 4:
                self.flushtext()
                dh = afile.readint(cmd - _DVI_RIGHT1234 + 1, 1)
                if self.debug:
                    self.debugfile.write("%d: right%d %d h:=%d%+d=%d, hh:=???\n" %
                                         (self.filepos,
                                          cmd - _DVI_RIGHT1234 + 1,
                                          dh,
                                          self.pos[_POS_H],
                                          dh,
                                          self.pos[_POS_H]+dh))
                self.pos[_POS_H] += dh
            elif cmd == _DVI_W0:
                self.flushtext()
                if self.debug:
                    self.debugfile.write("%d: w0 %d h:=%d%+d=%d, hh:=???\n" %
                                         (self.filepos,
                                          self.pos[_POS_W],
                                          self.pos[_POS_H],
                                          self.pos[_POS_W],
                                          self.pos[_POS_H]+self.pos[_POS_W]))
                self.pos[_POS_H] += self.pos[_POS_W]
            elif cmd >= _DVI_W1234 and cmd < _DVI_W1234 + 4:
                self.flushtext()
                self.pos[_POS_W] = afile.readint(cmd - _DVI_W1234 + 1, 1)
                if self.debug:
                    self.debugfile.write("%d: w%d %d h:=%d%+d=%d, hh:=???\n" %
                                         (self.filepos,
                                          cmd - _DVI_W1234 + 1,
                                          self.pos[_POS_W],
                                          self.pos[_POS_H],
                                          self.pos[_POS_W],
                                          self.pos[_POS_H]+self.pos[_POS_W]))
                self.pos[_POS_H] += self.pos[_POS_W]
            elif cmd == _DVI_X0:
                self.flushtext()
                if self.debug:
                    self.debugfile.write("%d: x0 %d h:=%d%+d=%d, hh:=???\n" %
                                         (self.filepos,
                                          self.pos[_POS_X],
                                          self.pos[_POS_H],
                                          self.pos[_POS_X],
                                          self.pos[_POS_H]+self.pos[_POS_X]))
                self.pos[_POS_H] += self.pos[_POS_X]
            elif cmd >= _DVI_X1234 and cmd < _DVI_X1234 + 4:
                self.flushtext()
                self.pos[_POS_X] = afile.readint(cmd - _DVI_X1234 + 1, 1)
                if self.debug:
                    self.debugfile.write("%d: x%d %d h:=%d%+d=%d, hh:=???\n" %
                                         (self.filepos,
                                          cmd - _DVI_X1234 + 1,
                                          self.pos[_POS_X],
                                          self.pos[_POS_H],
                                          self.pos[_POS_X],
                                          self.pos[_POS_H]+self.pos[_POS_X]))
                self.pos[_POS_H] += self.pos[_POS_X]
            elif cmd >= _DVI_DOWN1234 and cmd < _DVI_DOWN1234 + 4:
                self.flushtext()
                dv = afile.readint(cmd - _DVI_DOWN1234 + 1, 1)
                if self.debug:
                    self.debugfile.write("%d: down%d %d v:=%d%+d=%d, vv:=???\n" %
                                         (self.filepos,
                                          cmd - _DVI_DOWN1234 + 1,
                                          dv,
                                          self.pos[_POS_V],
                                          dv,
                                          self.pos[_POS_V]+dv))
                self.pos[_POS_V] += dv
            elif cmd == _DVI_Y0:
                self.flushtext()
                if self.debug:
                    self.debugfile.write("%d: y0 %d v:=%d%+d=%d, vv:=???\n" %
                                         (self.filepos,
                                          self.pos[_POS_Y],
                                          self.pos[_POS_V],
                                          self.pos[_POS_Y],
                                          self.pos[_POS_V]+self.pos[_POS_Y]))
                self.pos[_POS_V] += self.pos[_POS_Y]
            elif cmd >= _DVI_Y1234 and cmd < _DVI_Y1234 + 4:
                self.flushtext()
                self.pos[_POS_Y] = afile.readint(cmd - _DVI_Y1234 + 1, 1)
                if self.debug:
                    self.debugfile.write("%d: y%d %d v:=%d%+d=%d, vv:=???\n" %
                                         (self.filepos,
                                          cmd - _DVI_Y1234 + 1,
                                          self.pos[_POS_Y],
                                          self.pos[_POS_V],
                                          self.pos[_POS_Y],
                                          self.pos[_POS_V]+self.pos[_POS_Y]))
                self.pos[_POS_V] += self.pos[_POS_Y]
            elif cmd == _DVI_Z0:
                self.flushtext()
                if self.debug:
                    self.debugfile.write("%d: z0 %d v:=%d%+d=%d, vv:=???\n" %
                                         (self.filepos,
                                          self.pos[_POS_Z],
                                          self.pos[_POS_V],
                                          self.pos[_POS_Z],
                                          self.pos[_POS_V]+self.pos[_POS_Z]))
                self.pos[_POS_V] += self.pos[_POS_Z]
            elif cmd >= _DVI_Z1234 and cmd < _DVI_Z1234 + 4:
                self.flushtext()
                self.pos[_POS_Z] = afile.readint(cmd - _DVI_Z1234 + 1, 1)
                if self.debug:
                    self.debugfile.write("%d: z%d %d v:=%d%+d=%d, vv:=???\n" %
                                         (self.filepos,
                                          cmd - _DVI_Z1234 + 1,
                                          self.pos[_POS_Z],
                                          self.pos[_POS_V],
                                          self.pos[_POS_Z],
                                          self.pos[_POS_V]+self.pos[_POS_Z]))
                self.pos[_POS_V] += self.pos[_POS_Z]
            elif cmd >= _DVI_FNTNUMMIN and cmd <= _DVI_FNTNUMMAX:
                self.usefont(cmd - _DVI_FNTNUMMIN, 0)
            elif cmd >= _DVI_FNT1234 and cmd < _DVI_FNT1234 + 4:
                # note that according to the DVI docs, for four byte font numbers,
                # the font number is signed. Don't ask why!
                fntnum = afile.readint(cmd - _DVI_FNT1234 + 1, cmd == _DVI_FNT1234 + 3)
                self.usefont(fntnum, id1234=cmd-_DVI_FNT1234+1)
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
    def __init__(self, filename, scale, tfmconv, pyxconv, fontmap, debug=0):
        self.filename = filename
        self.scale = scale
        self.tfmconv = tfmconv
        self.pyxconv = pyxconv
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
                # XXX: check rounding
                reals = int(round(self.scale * (16*self.ds/16777216L) * s))

                # print ("defining font %s -- VF scale: %g, VF design size: %d, relative font size: %d => real size: %d" %
                #        (fontname, self.scale, self.ds, s, reals)
                #        )

                # XXX allow for virtual fonts here too
                self.fonts[num] =  font(fontname, c, reals, d, self.tfmconv, self.pyxconv, self.fontmap, self.debug > 1)
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


