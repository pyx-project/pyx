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

# TODO:
# - should we improve on the arc length -> arg parametrization routine or
#   should we at least factor it out?
# - How should we handle the passing of stroke and fill styles to
#   arrows? Calls, new instances, ...?


"""The canvas module provides a PostScript canvas class and related classes

A PostScript canvas is the pivotal object for the creation of (E)PS-Files.
It collects all the elements that should be displayed (PSCmds) together
with attributes if applicable. Furthermore, a canvas can be globally
transformed (i.e. translated, rotated, etc.) and clipped.

"""

import types, math, string, StringIO, time
import attrlist, base, bbox, helper, path, unit, text, t1strip, pykpathsea, trafo, version

class prologitem:

    """Part of the PostScript Prolog"""

    def merge(self, other):
        """ try to merge self with other prologitem

        If the merge succeeds, return None. Otherwise return other.
        Raise ValueError, if conflicts arise!"""

        pass

    def write(self, file):
        """ write self in file """
        pass


class definition(prologitem):

    """ PostScript function definition included in the prolog """

    def __init__(self, id, body):
        self.id = id
        self.body = body

    def merge(self, other):
        if not isinstance(other, definition):
            return other
        if self.id==other.id:
            if self.body==other.body:
                return None
            raise ValueError("Conflicting function definitions!")
        else:
           return other

    def write(self, file):
        file.write("%%%%BeginRessource: %s\n" % self.id)
        file.write("%(body)s /%(id)s exch def\n" % self.__dict__)
        file.write("%%EndRessource\n")


# XXX: we have to define this here and not in text.py to avoid problems with cyclic imports!?
_ReEncodeFont = definition("ReEncodeFont", """{
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


class fontdefinition(prologitem):

    """ PostScript font definition included in the prolog """

    def __init__(self, font):
        self.basepsname = font.getbasepsname()
        self.fontfile = font.getfontfile()
        self.encfilename = font.getencodingfile()
        self.usedchars = font.usedchars

    def merge(self, other):
        if not isinstance(other, fontdefinition):
            return other
        if self.basepsname==other.basepsname:
            for i in range(len(self.usedchars)):
                self.usedchars[i] = self.usedchars[i] or other.usedchars[i]
            return None
        else:
            return other

    def write(self, file):
        if self.fontfile:
            file.write("%%%%BeginFont: %s\n" % self.basepsname)
            file.write("%Included char codes:")
            for i in range(len(self.usedchars)):
                if self.usedchars[i]:
                    file.write(" %d" % i)
            file.write("\n")
            pfbpath = pykpathsea.find_file(self.fontfile, pykpathsea.kpse_type1_format)
            if pfbpath is None:
                raise RuntimeError("cannot find type 1 font %s" % self.fontfile)
            encpath = pykpathsea.find_file(self.encfilename, pykpathsea.kpse_tex_ps_header_format)
            if encpath is None:
                raise RuntimeError("cannot find font encoding file %s" % self.encfilename)
            t1strip.t1strip(file, pfbpath, encpath, self.usedchars)
            file.write("%%EndFont\n")


class fontencoding(prologitem):

    """ PostScript font re-encoding vector included in the prolog """

    def __init__(self, font):
        self.name = font.getencoding()
        self.filename = font.getencodingfile()

    def merge(self, other):
        if not isinstance(other, fontencoding):
            return other
        if self.name==other.name:
            if self.filename==other.filename:
                return None
            raise ValueError("Conflicting encodings!")
        else:
           return other

    def write(self, file):
        file.write("%%%%BeginProcSet: %s\n" % self.name)
        path = pykpathsea.find_file(self.filename, pykpathsea.kpse_tex_ps_header_format)
        encfile = open(path, "r")
        file.write(encfile.read())
        encfile.close()


class fontreencoding(prologitem):

    """ PostScript font re-encoding directive included in the prolog """

    def __init__(self, font):
        self.psname = font.getpsname()
        self.basepsname = font.getbasepsname()
        self.encoding = font.getencoding()

    def merge(self, other):
        if not isinstance(other, fontreencoding):
            return other
        if self.psname==other.psname:
            if self.basepsname==other.basepsname and self.encoding==other.encoding:
                return None
            raise ValueError("Conflicting font reencodings!")
        else:
            return other

    def write(self, file):
        file.write("%%%%BeginProcSet: %s\n" % self.psname)
        file.write("/%s /%s %s ReEncodeFont\n" % (self.basepsname, self.psname, self.encoding))
        file.write("%%EndProcSet\n")


# known paperformats as tuple(width, height)

_paperformats = { "a4"      : ("210 t mm",  "297 t mm"),
                  "a3"      : ("297 t mm",  "420 t mm"),
                  "a2"      : ("420 t mm",  "594 t mm"),
                  "a1"      : ("594 t mm",  "840 t mm"),
                  "a0"      : ("840 t mm", "1188 t mm"),
                  "a0b"     : ("910 t mm", "1370 t mm"),
                  "letter"  : ("8.5 t in",   "11 t in"),
                  "legal"   : ("8.5 t in",   "14 t in")}


#
# Exceptions
#

class CanvasException(Exception): pass


class linecap(base.PathStyle):

    """linecap of paths"""

    def __init__(self, value=0):
        self.value=value

    def write(self, file):
        file.write("%d setlinecap\n" % self.value)

linecap.butt   = linecap(0)
linecap.round  = linecap(1)
linecap.square = linecap(2)


class linejoin(base.PathStyle):

    """linejoin of paths"""

    def __init__(self, value=0):
        self.value=value

    def write(self, file):
        file.write("%d setlinejoin\n" % self.value)

linejoin.miter = linejoin(0)
linejoin.round = linejoin(1)
linejoin.bevel = linejoin(2)


class miterlimit(base.PathStyle):

    """miterlimit of paths"""

    def __init__(self, value=10.0):
        self.value=value

    def write(self, file):
        file.write("%f setmiterlimit\n" % self.value)


miterlimit.lessthan180deg = miterlimit(1/math.sin(math.pi*180/360))
miterlimit.lessthan90deg  = miterlimit(1/math.sin(math.pi*90/360))
miterlimit.lessthan60deg  = miterlimit(1/math.sin(math.pi*60/360))
miterlimit.lessthan45deg  = miterlimit(1/math.sin(math.pi*45/360))
miterlimit.lessthan11deg  = miterlimit(10) # the default, approximately 11.4783 degress

class dash(base.PathStyle):

    """dash of paths"""

    def __init__(self, pattern=[], offset=0):
        self.pattern=pattern
        self.offset=offset

    def write(self, file):
        patternstring=""
        for element in self.pattern:
            patternstring=patternstring + `element` + " "

        file.write("[%s] %d setdash\n" % (patternstring, self.offset))


class linestyle(base.PathStyle):

    """linestyle (linecap together with dash) of paths"""

    def __init__(self, c=linecap.butt, d=dash([])):
        self.c=c
        self.d=d

    def write(self, file):
        self.c.write(file)
        self.d.write(file)

linestyle.solid      = linestyle(linecap.butt,  dash([]))
linestyle.dashed     = linestyle(linecap.butt,  dash([2]))
linestyle.dotted     = linestyle(linecap.round, dash([0, 3]))
linestyle.dashdotted = linestyle(linecap.round, dash([0, 3, 3, 3]))


class linewidth(base.PathStyle, unit.length):

    """linewidth of paths"""

    def __init__(self, l="0 cm"):
        unit.length.__init__(self, l=l, default_type="w")

    def write(self, file):
        file.write("%f setlinewidth\n" % unit.topt(self))

_base=0.02

linewidth.THIN   = linewidth("%f cm" % (_base/math.sqrt(32)))
linewidth.THIn   = linewidth("%f cm" % (_base/math.sqrt(16)))
linewidth.THin   = linewidth("%f cm" % (_base/math.sqrt(8)))
linewidth.Thin   = linewidth("%f cm" % (_base/math.sqrt(4)))
linewidth.thin   = linewidth("%f cm" % (_base/math.sqrt(2)))
linewidth.normal = linewidth("%f cm" % _base)
linewidth.thick  = linewidth("%f cm" % (_base*math.sqrt(2)))
linewidth.Thick  = linewidth("%f cm" % (_base*math.sqrt(4)))
linewidth.THick  = linewidth("%f cm" % (_base*math.sqrt(8)))
linewidth.THIck  = linewidth("%f cm" % (_base*math.sqrt(16)))
linewidth.THICk  = linewidth("%f cm" % (_base*math.sqrt(32)))
linewidth.THICK  = linewidth("%f cm" % (_base*math.sqrt(64)))


#
# Decorated path
#

class decoratedpath(base.PSCmd):
    """Decorated path

    The main purpose of this class is during the drawing
    (stroking/filling) of a path. It collects attributes for the
    stroke and/or fill operations.
    """

    def __init__(self,
                 path, strokepath=None, fillpath=None,
                 styles=None, strokestyles=None, fillstyles=None,
                 subdps=None):

        self.path = path

        # path to be stroked or filled (or None)
        self.strokepath = strokepath
        self.fillpath = fillpath

        # global style for stroking and filling and subdps
        self.styles = helper.ensurelist(styles)

        # styles which apply only for stroking and filling
        self.strokestyles = helper.ensurelist(strokestyles)
        self.fillstyles = helper.ensurelist(fillstyles)

        # additional elements of the path, e.g., arrowheads,
        # which are by themselves decoratedpaths
        self.subdps = helper.ensurelist(subdps)

    def addsubdp(self, subdp):
        """add a further decorated path to the list of subdps"""
        self.subdps.append(subdp)

    def bbox(self):
        return reduce(lambda x,y: x+y.bbox(),
                      self.subdps,
                      self.path.bbox())

    def prolog(self):
        result = []
        for style in list(self.styles) + list(self.fillstyles) + list(self.strokestyles):
            result.extend(style.prolog())
        return result

    def write(self, file):
        # draw (stroke and/or fill) the decoratedpath on the canvas
        # while trying to produce an efficient output, e.g., by
        # not writing one path two times

        # small helper
        def _writestyles(styles, file=file):
            for style in styles:
                style.write(file)

        # apply global styles
        if self.styles:
            _gsave().write(file)
            _writestyles(self.styles)

        if self.fillpath:
            _newpath().write(file)
            self.fillpath.write(file)

            if self.strokepath==self.fillpath:
                # do efficient stroking + filling
                _gsave().write(file)

                if self.fillstyles:
                    _writestyles(self.fillstyles)

                _fill().write(file)
                _grestore().write(file)

                if self.strokestyles:
                    _gsave().write(file)
                    _writestyles(self.strokestyles)

                _stroke().write(file)

                if self.strokestyles:
                    _grestore().write(file)
            else:
                # only fill fillpath - for the moment
                if self.fillstyles:
                    _gsave().write(file)
                    _writestyles(self.fillstyles)

                _fill().write(file)

                if self.fillstyles:
                    _grestore().write(file)

        if self.strokepath and self.strokepath!=self.fillpath:
            # this is the only relevant case still left
            # Note that a possible stroking has already been done.

            if self.strokestyles:
                _gsave().write(file)
                _writestyles(self.strokestyles)

            _newpath().write(file)
            self.strokepath.write(file)
            _stroke().write(file)

            if self.strokestyles:
                _grestore().write(file)

        if not self.strokepath and not self.fillpath:
            raise RuntimeError("Path neither to be stroked nor filled")

        # now, draw additional subdps
        for subdp in self.subdps:
            subdp.write(file)

        # restore global styles
        if self.styles:
            _grestore().write(file)

#
# Path decorators
#

class PathDeco:

    """Path decorators

    In contrast to path styles, path decorators depend on the concrete
    path to which they are applied. In particular, they don't make
    sense without any path and can thus not be used in canvas.set!

    """

    def decorate(self, dp):
        """apply a style to a given decoratedpath object dp

        decorate accepts a decoratedpath object dp, applies PathStyle
        by modifying dp in place and returning the new dp.
        """

        pass

#
# stroked and filled: basic PathDecos which stroked and fill,
# respectively the path
#

class stroked(PathDeco):

    """stroked is a PathDecorator, which draws the outline of the path"""

    def __init__(self, *styles):
        self.styles = list(styles)

    def decorate(self, dp):
        dp.strokepath = dp.path
        dp.strokestyles = self.styles

        return dp


class filled(PathDeco):

    """filled is a PathDecorator, which fills the interior of the path"""

    def __init__(self, *styles):
        self.styles = list(styles)

    def decorate(self, dp):
        dp.fillpath = dp.path
        dp.fillstyles = self.styles

        return dp

def _arrowheadtemplatelength(anormpath, size):
    "calculate length of arrowhead template (in parametrisation of anormpath)"
    # get tip (tx, ty)
    tx, ty = anormpath.begin()

    # obtain arrow template by using path up to first intersection
    # with circle around tip (as suggested by Michael Schindler)
    ipar = anormpath.intersect(path.circle(tx, ty, size))
    if ipar[0]:
        alen = ipar[0][0]
    else:
        # if this doesn't work, use first order conversion from pts to
        # the bezier curve's parametrization
        tlen = unit.topt(anormpath.tangent(0).arclength())
        try:
            alen = unit.topt(size)/tlen
        except ArithmeticError:
            # take maximum, we can get
            alen = anormpath.range()
        if alen>anormpath.range(): alen=anormpath().range()

    return alen


def _arrowhead(anormpath, size, angle, constriction):

    """helper routine, which returns an arrowhead for a normpath

    returns arrowhead at begin of anormpath with size,
    opening angle and relative constriction
    """

    alen = _arrowheadtemplatelength(anormpath, size)
    tx, ty = anormpath.begin()

    # now we construct the template for our arrow but cutting
    # the path a the corresponding length
    arrowtemplate = anormpath.split(alen)[0]

    # from this template, we construct the two outer curves
    # of the arrow
    arrowl = arrowtemplate.transformed(trafo.rotate(-angle/2.0, tx, ty))
    arrowr = arrowtemplate.transformed(trafo.rotate( angle/2.0, tx, ty))

    # now come the joining backward parts
    if constriction:
        # arrow with constriction

        # constriction point (cx, cy) lies on path
        cx, cy = anormpath.at(constriction*alen)

        arrowcr= path.line(*(arrowr.end()+(cx,cy)))

        arrow = arrowl.reversed() << arrowr << arrowcr
        arrow.append(path.closepath())
    else:
        # arrow without constriction
        arrow = arrowl.reversed() << arrowr
        arrow.append(path.closepath())

    return arrow

class arrow(PathDeco):

    """A general arrow"""

    def __init__(self,
                 position, size, angle=45, constriction=0.8,
                 styles=None, strokestyles=None, fillstyles=None):
        self.position = position
        self.size = size
        self.angle = angle
        self.constriction = constriction
        self.styles = helper.ensurelist(styles)
        self.strokestyles = helper.ensurelist(strokestyles)
        self.fillstyles = helper.ensurelist(fillstyles)

    def __call__(self, *styles):
        fillstyles = [ style for s in styles if isinstance(s, filled) 
                       for style in s.styles ]

        strokestyles = [ style for s in styles if isinstance(s, stroked) 
                         for style in s.styles ]

        styles = [ style for style in styles 
                   if not (isinstance(style, filled) or
                           isinstance(style, stroked)) ]

        return arrow(position=self.position,
                     size=self.size,
                     angle=self.angle,
                     constriction=self.constriction,
                     styles=styles,
                     strokestyles=strokestyles,
                     fillstyles=fillstyles)

    def decorate(self, dp):

        # TODO: error, when strokepath is not defined

        # convert to normpath if necessary
        if isinstance(dp.strokepath, path.normpath):
            anormpath=dp.strokepath
        else:
            anormpath=path.normpath(dp.path)

        if self.position:
            anormpath=anormpath.reversed()

        ahead = _arrowhead(anormpath, self.size, self.angle, self.constriction)

        dp.addsubdp(decoratedpath(ahead,
                                  strokepath=ahead, fillpath=ahead,
                                  styles=self.styles,
                                  strokestyles=self.strokestyles,
                                  fillstyles=self.fillstyles))

        alen = _arrowheadtemplatelength(anormpath, self.size)

        if self.constriction:
            ilen = alen*self.constriction
        else:
            ilen = alen

        # correct somewhat for rotation of arrow segments
        ilen = ilen*math.cos(math.pi*self.angle/360.0)

        # this is the rest of the path, we have to draw
        anormpath = anormpath.split(ilen)[1]

        # go back to original orientation, if necessary
        if self.position:
            anormpath=anormpath.reversed()

        # set the new (shortened) strokepath
        dp.strokepath=anormpath

        return dp


class barrow(arrow):

    """arrow at begin of path"""

    def __init__(self, size, angle=45, constriction=0.8,
                 styles=None, strokestyles=None, fillstyles=None):
        arrow.__init__(self,
                       position=0,
                       size=size,
                       angle=angle,
                       constriction=constriction,
                       styles=styles,
                       strokestyles=strokestyles,
                       fillstyles=fillstyles)

_base = unit.v_pt(4)

barrow.SMALL  = barrow(_base/math.sqrt(64))
barrow.SMALl  = barrow(_base/math.sqrt(32))
barrow.SMAll  = barrow(_base/math.sqrt(16))
barrow.SMall  = barrow(_base/math.sqrt(8))
barrow.Small  = barrow(_base/math.sqrt(4))
barrow.small  = barrow(_base/math.sqrt(2))
barrow.normal = barrow(_base)
barrow.large  = barrow(_base*math.sqrt(2))
barrow.Large  = barrow(_base*math.sqrt(4))
barrow.LArge  = barrow(_base*math.sqrt(8))
barrow.LARge  = barrow(_base*math.sqrt(16))
barrow.LARGe  = barrow(_base*math.sqrt(32))
barrow.LARGE  = barrow(_base*math.sqrt(64))


class earrow(arrow):

    """arrow at end of path"""

    def __init__(self, size, angle=45, constriction=0.8,
                 styles=[], strokestyles=[], fillstyles=[]):
        arrow.__init__(self,
                       position=1,
                       size=size,
                       angle=angle,
                       constriction=constriction,
                       styles=styles,
                       strokestyles=strokestyles,
                       fillstyles=fillstyles)


earrow.SMALL  = earrow(_base/math.sqrt(64))
earrow.SMALl  = earrow(_base/math.sqrt(32))
earrow.SMAll  = earrow(_base/math.sqrt(16))
earrow.SMall  = earrow(_base/math.sqrt(8))
earrow.Small  = earrow(_base/math.sqrt(4))
earrow.small  = earrow(_base/math.sqrt(2))
earrow.normal = earrow(_base)
earrow.large  = earrow(_base*math.sqrt(2))
earrow.Large  = earrow(_base*math.sqrt(4))
earrow.LArge  = earrow(_base*math.sqrt(8))
earrow.LARge  = earrow(_base*math.sqrt(16))
earrow.LARGe  = earrow(_base*math.sqrt(32))
earrow.LARGE  = earrow(_base*math.sqrt(64))

#
# clipping class
#

class clip(base.PSCmd):

    """class for use in canvas constructor which clips to a path"""

    def __init__(self, path):
        """construct a clip instance for a given path"""
        self.path = path

    def bbox(self):
        # as a PSCmd a clipping path has NO influence on the bbox...
        return bbox._bbox()

    def clipbbox(self):
        # ... but for clipping, we nevertheless need the bbox
        return self.path.bbox()

    def write(self, file):
        _newpath().write(file)
        self.path.write(file)
        _clip().write(file)

#
# some very primitive Postscript operators
#

class _newpath(base.PSOp):
    def write(self, file):
       file.write("newpath\n")


class _stroke(base.PSOp):
    def write(self, file):
       file.write("stroke\n")


class _fill(base.PSOp):
    def write(self, file):
        file.write("fill\n")


class _clip(base.PSOp):
    def write(self, file):
       file.write("clip\n")


class _gsave(base.PSOp):
    def write(self, file):
       file.write("gsave\n")


class _grestore(base.PSOp):
    def write(self, file):
       file.write("grestore\n")

#
#
#

class _canvas(base.PSCmd, attrlist.attrlist):

    """a canvas is a collection of PSCmds together with PSAttrs"""

    def __init__(self, *args):

        """construct a canvas

        The canvas can be modfied by supplying args, which have
        to be instances of one of the following classes:
         - trafo.trafo (leading to a global transformation of the canvas)
         - canvas.clip (clips the canvas)
         - base.PathStyle (sets some global attributes of the canvas)

        Note that, while the first two properties are fixed for the
        whole canvas, the last one can be changed via canvas.set()

        """

        self.PSOps     = []
        self.trafo     = trafo.trafo()
        self.clipbbox  = bbox._bbox()
        self.texrunner = text.defaulttexrunner

        for arg in args:
            if isinstance(arg, trafo._trafo):
                self.trafo = self.trafo*arg
                self.PSOps.append(arg)
            elif isinstance(arg, clip):
                self.clipbbox=(self.clipbbox*
                               arg.clipbbox().transformed(self.trafo))
                self.PSOps.append(arg)
            else:
                self.set(arg)

    def bbox(self):
        """returns bounding box of canvas"""
        obbox = reduce(lambda x,y:
                       isinstance(y, base.PSCmd) and x+y.bbox() or x,
                       self.PSOps,
                       bbox._bbox())

        # transform according to our global transformation and
        # intersect with clipping bounding box (which have already been
        # transformed in canvas.__init__())
        return obbox.transformed(self.trafo)*self.clipbbox

    def prolog(self):
        result = []
        for cmd in self.PSOps:
            result.extend(cmd.prolog())
        return result

    def write(self, file):
        _gsave().write(file)
        for cmd in self.PSOps:
            cmd.write(file)
        _grestore().write(file)

    def insert(self, PSOp, *args):
        """insert PSOp in the canvas.

        If args are given, then insert a canvas containing PSOp applying args.

        returns the PSOp

        """

        if args:
            sc = _canvas(*args)
            sc.insert(PSOp)
            self.PSOps.append(sc)
        else:
            self.PSOps.append(PSOp)

        return PSOp

    def set(self, *styles):
        """sets styles args globally for the rest of the canvas

        returns canvas

        """

        for style in styles:
            if not isinstance(style, base.PathStyle):
                raise NotImplementedError, "can only set PathStyle"

            self.insert(style)

        return self

    def draw(self, path, *args):
        """draw path on canvas using the style given by args

        The argument list args consists of PathStyles, which modify
        the appearance of the path, or PathDecos,
        which add some new visual elements to the path.

        returns the canvas

        """

        self.attrcheck(args, allowmulti=(base.PathStyle, PathDeco))

        dp = decoratedpath(path)

        # set global styles
        dp.styles = self.attrgetall(args, base.PathStyle, ())

        # add path decorations and modify path accordingly
        for deco in self.attrgetall(args, PathDeco, ()):
            dp = deco.decorate(dp)

        self.insert(dp)

        return self

    def stroke(self, path, *args):
        """stroke path on canvas using the style given by args

        The argument list args consists of PathStyles, which modify
        the appearance of the path, or PathDecos,
        which add some new visual elements to the path.

        returns the canvas

        """

        return self.draw(path, stroked(), *args)

    def fill(self, path, *args):
        """fill path on canvas using the style given by args

        The argument list args consists of PathStyles, which modify
        the appearance of the path, or PathDecos,
        which add some new visual elements to the path.

        returns the canvas

        """

        return self.draw(path, filled(), *args)

    def settexrunner(self, texrunner):
        """sets the texrunner to be used to within the text and _text methods"""

        self.texrunner = texrunner

    def text(self, x, y, atext, *args):
        """insert a text into the canvas

        inserts a textbox created by self.texrunner.text into the canvas

        returns the inserted textbox"""

        return self.insert(self.texrunner.text(x, y, atext, *args))


    def _text(self, x, y, atext, *args):
        """insert a text into the canvas

        inserts a textbox created by self.texrunner._text into the canvas

        returns the inserted textbox"""

        return self.insert(self.texrunner._text(x, y, atext, *args))

#
# canvas for patterns
#

class pattern(_canvas, base.PathStyle):

    def __init__(self, painttype=1, tilingtype=1, xstep=None, ystep=None, bbox=None, trafo=None):
        _canvas.__init__(self)
        self.id = "pattern%d" % id(self)
        # XXX: some checks are in order
        if painttype not in (1,2):
            raise ValueError("painttype must be 1 or 2")
        self.painttype = painttype
        if tilingtype not in (1,2,3):
            raise ValueError("tilingtype must be 1, 2 or 3")
        self.tilingtype = tilingtype
        self.xstep = xstep
        self.ystep = ystep
        self.patternbbox = bbox
        self.patterntrafo = trafo

    def bbox(self):
        return bbox._bbox()

    def write(self, file):
        file.write("%s setpattern\n" % self.id)

    def prolog(self):
        realpatternbbox = _canvas.bbox(self)
        if self.xstep is None:
           xstep = unit.topt(realpatternbbox.width())
        else:
           xstep = unit.topt(unit.length(self.xstep))
        if self.ystep is None:
            ystep = unit.topt(realpatternbbox.height())
        else:
           ystep = unit.topt(unit.length(self.ystep))
        if not xstep:
            raise ValueError("xstep in pattern cannot be zero")
        if not ystep:
            raise ValueError("ystep in pattern cannot be zero")
        patternbbox = self.patternbbox or realpatternbbox.enlarged("5 pt")

        patternprefix = string.join(("<<",
                                     "/PatternType 1",
                                     "/PaintType %d" % self.painttype,
                                     "/TilingType %d" % self.tilingtype,
                                     "/BBox[%s]" % str(patternbbox),
                                     "/XStep %g" % xstep,
                                     "/YStep %g" % ystep,
                                     "/PaintProc {\nbegin\n"),
                                    sep="\n")
        stringfile = StringIO.StringIO()
        _canvas.write(self, stringfile)
        patternproc = stringfile.getvalue()
        stringfile.close()
        patterntrafostring = self.patterntrafo is None and "matrix" or str(self.patterntrafo)
        patternsuffix = "end\n} bind\n>>\n%s\nmakepattern" % patterntrafostring

        pr = _canvas.prolog(self)
        pr.append(definition(self.id, string.join((patternprefix, patternproc, patternsuffix), "")))
        return pr

#
# The main canvas class
#

class canvas(_canvas):

    """a canvas is a collection of PSCmds together with PSAttrs"""

    def __init__(self, *args):

        """construct a canvas

        The canvas can be modfied by supplying args, which have
        to be instances of one of the following classes:
         - trafo.trafo (leading to a global transformation of the canvas)
         - canvas.clip (clips the canvas)
         - base.PathStyle (sets some global attributes of the canvas)

        Note that, while the first two properties are fixed for the
        whole canvas, the last one can be changed via canvas.set()

        """

        self.PSOps     = []
        self.trafo     = trafo.trafo()
        self.clipbbox  = bbox._bbox()
        self.texrunner = text.defaulttexrunner

        for arg in args:
            if isinstance(arg, trafo._trafo):
                self.trafo = self.trafo*arg
                self.PSOps.append(arg)
            elif isinstance(arg, clip):
                self.clipbbox=(self.clipbbox*
                               arg.clipbbox().transformed(self.trafo))
                self.PSOps.append(arg)
            else:
                self.set(arg)

    def writetofile(self, filename, paperformat=None, rotated=0, fittosize=0, margin="1 t cm",
                    bbox=None, bboxenlarge="1 t pt"):
        """write canvas to EPS file

        If paperformat is set to a known paperformat, the output will be centered on
        the page.

        If rotated is set, the output will first be rotated by 90 degrees.

        If fittosize is set, then the output is scaled to the size of the
        page (minus margin). In that case, the paperformat the specification
        of the paperformat is obligatory.

        The bbox parameter overrides the automatic bounding box determination.
        bboxenlarge may be used to enlarge the bbox of the canvas (or the
        manually specified bbox).
        """

        if filename[-4:]!=".eps":
            filename = filename + ".eps"

        try:
            file = open(filename, "w")
        except IOError:
            assert 0, "cannot open output file"                 # TODO: Fehlerbehandlung...

        abbox = bbox is not None and bbox or self.bbox()
        abbox = abbox.enlarged(bboxenlarge)
        ctrafo = None     # global transformation of canvas

        if rotated:
            ctrafo = trafo._rotate(90,
                                     0.5*(abbox.llx+abbox.urx),
                                     0.5*(abbox.lly+abbox.ury))

        if paperformat:
            # center (optionally rotated) output on page
            try:
                width, height = _paperformats[paperformat]
                width = unit.topt(width)
                height = unit.topt(height)
            except KeyError:
                raise KeyError, "unknown paperformat '%s'" % paperformat

            if not ctrafo: ctrafo=trafo.trafo()

            ctrafo = ctrafo._translated(0.5*(width -(abbox.urx-abbox.llx))-
                                       abbox.llx,
                                       0.5*(height-(abbox.ury-abbox.lly))-
                                       abbox.lly)

            if fittosize:
                # scale output to pagesize - margins
                margin=unit.topt(margin)

                if rotated:
                    sfactor = min((height-2*margin)/(abbox.urx-abbox.llx),
                                  (width-2*margin)/(abbox.ury-abbox.lly))
                else:
                    sfactor = min((width-2*margin)/(abbox.urx-abbox.llx),
                                  (height-2*margin)/(abbox.ury-abbox.lly))

                ctrafo = ctrafo._scaled(sfactor, sfactor, 0.5*width, 0.5*height)


        elif fittosize:
            assert 0, "must specify paper size for fittosize" # TODO: exception...

        # if there has been a global transformation, adjust the bounding box
        # accordingly
        if ctrafo: abbox = abbox.transformed(ctrafo)

        file.write("%!PS-Adobe-3.0 EPSF 3.0\n")
        abbox.write(file)
        file.write("%%%%Creator: PyX %s\n" % version.version)
        file.write("%%%%Title: %s\n" % filename)
        file.write("%%%%CreationDate: %s\n" %
                   time.asctime(time.localtime(time.time())))
        file.write("%%EndComments\n")

        file.write("%%BeginProlog\n")

        mergedprolog = []

        for pritem in self.prolog():
            for mpritem in mergedprolog:
                if mpritem.merge(pritem) is None: break
            else:
                mergedprolog.append(pritem)

        for pritem in mergedprolog:
            pritem.write(file)

        file.write("%%EndProlog\n")

        # again, if there has occured global transformation, apply it now
        if ctrafo: ctrafo.write(file)

        file.write("%f setlinewidth\n" % unit.topt(linewidth.normal))

        # here comes the actual content
        self.write(file)

        file.write("showpage\n")
        file.write("%%Trailer\n")
        file.write("%%EOF\n")
