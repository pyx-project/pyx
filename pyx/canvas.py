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
# - Should we really set linewidth in canvas.writetofile. Why don't we
#   rely on the PS default (like for all other PathStyles)
# - How should we handle the passing of stroke and fill styles to
#   arrows? Calls, new instances, ...?


"""The canvas module provides a PostScript canvas class and related classes

A PostScript canvas is the pivotal object for the creation of (E)PS-Files.
It collects all the elements that should be displayed (PSCmds) together
with attributes if applicable. Furthermore, a canvas can be globally
transformed (i.e. translated, rotated, etc.) and clipped.

"""

import types, math, time
import pyx
import base
import bbox, unit, trafo
import path

# PostScript-procedure definitions
# cf. file: 5002.EPSF_Spec_v3.0.pdf     
# with important correction in EndEPSF: 
#   end operator is missing in the spec!

_PSProlog = """/BeginEPSF {
  /b4_Inc_state save def
  /dict_count countdictstack def
  /op_count count 1 sub def
  userdict begin
  /showpage { } def
  0 setgray 0 setlinecap
  1 setlinewidth 0 setlinejoin
  10 setmiterlimit [ ] 0 setdash newpath
  /languagelevel where
  {pop languagelevel
  1 ne
    {false setstrokeadjust false setoverprint
    } if
  } if
} bind def
/EndEPSF {
  end
  count op_count sub {pop} repeat
  countdictstack dict_count sub {end} repeat
  b4_Inc_state restore
} bind def"""

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

    def __init__(self, l):
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

class DecoratedPath(base.PSCmd):
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
        self.styles = styles or []
        
        # styles which apply only for stroking and filling
        self.strokestyles = strokestyles or []
        self.fillstyles = fillstyles or []
        
        # additional elements of the path, e.g., arrowheads,
        # which are by themselves DecoratedPaths
        self.subdps = subdps or []

    def addsubdp(self, subdp):
        """add a further decorated path to the list of subdps"""
        
        self.subdps.append(subdp)

    def bbox(self):
        return reduce(lambda x,y: x+y.bbox(),
                      self.subdps,
                      self.path.bbox())


    def write(self, file):
        # draw (stroke and/or fill) the DecoratedPath on the canvas
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
        """apply a style to a given DecoratedPath object dp

        decorate accepts a DecoratedPath object dp, applies PathStyle
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
        self.styles=list(styles)

    def decorate(self, dp):
        dp.strokepath=dp.path
        dp.strokestyles=self.styles

        return dp


class filled(PathDeco):

    """filled is a PathDecorator, which fills the interior of the path"""

    def __init__(self, *styles):
        self.styles=list(styles)

    def decorate(self, dp):
        dp.fillpath=dp.path
        dp.fillstyles=self.styles

        return dp


#
# _arrowhead: helper routine
#

def _arrowhead(anormpath, size, angle, constriction):

    """helper routine, which returns an arrowhead for a normpath

    returns arrowhead at pos (0: begin, !=0: end) of anormpath with size,
    opening angle and relative constriction
    """

    # first order conversion from pts to the bezier curve's
    # parametrization

    tlen = unit.topt(anormpath.tangent(0).arclength())

    alen  = unit.topt(size)/tlen

    if alen>anormpath.range(): alen=anormpath().range()

    # get tip (tx, ty)
    tx, ty = anormpath.begin()

    # now we construct the template for our arrow but cutting
    # the path a the corresponding length
    arrowtemplate = anormpath.split(alen)[0]

    # from this template, we construct the two outer curves
    # of the arrow
    arrowl = arrowtemplate.transformed(trafo.rotation(-angle/2.0, tx, ty))
    arrowr = arrowtemplate.transformed(trafo.rotation( angle/2.0, tx, ty))

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
        self.styles = styles or []
        self.strokestyles = strokestyles or []
        self.fillstyles = fillstyles or []

    def __call__(self, *styles):
        fillstyles = reduce(lambda x, y:list(x)+(y.styles or []),
                            filter(lambda x: isinstance(x, filled),
                                   styles),
                            [])

        strokestyles = reduce(lambda x, y:list(x)+(y.styles or []),
                              filter(lambda x: isinstance(x, stroked),
                                     styles),
                            [])

        styles = filter(lambda x:
                        not (isinstance(x,filled) or
                             isinstance(x,stroked)),
                        styles)


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

        dp.addsubdp(DecoratedPath(ahead,
                                  strokepath=ahead, fillpath=ahead,
                                  styles=self.styles,
                                  strokestyles=self.strokestyles,
                                  fillstyles=self.fillstyles))

        # the following lines are copied from arrowhead.init()
        # TODO: can this be done better?

        # first order conversion from pts to the bezier curve's
        # parametrization

        tlen = unit.topt(anormpath.tangent(0).arclength())

        alen  = unit.topt(self.size)/tlen
        if alen>anormpath.range(): alen=anormpath().range()

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

_base = 4

barrow.SMALL  = barrow("%f v pt" % (_base/math.sqrt(64)))
barrow.SMALl  = barrow("%f v pt" % (_base/math.sqrt(32)))
barrow.SMAll  = barrow("%f v pt" % (_base/math.sqrt(16)))
barrow.SMall  = barrow("%f v pt" % (_base/math.sqrt(8)))
barrow.Small  = barrow("%f v pt" % (_base/math.sqrt(4)))
barrow.small  = barrow("%f v pt" % (_base/math.sqrt(2)))
barrow.normal = barrow("%f v pt" % _base)
barrow.large  = barrow("%f v pt" % (_base*math.sqrt(2)))
barrow.Large  = barrow("%f v pt" % (_base*math.sqrt(4)))
barrow.LArge  = barrow("%f v pt" % (_base*math.sqrt(8)))
barrow.LARge  = barrow("%f v pt" % (_base*math.sqrt(16)))
barrow.LARGe  = barrow("%f v pt" % (_base*math.sqrt(32)))
barrow.LARGE  = barrow("%f v pt" % (_base*math.sqrt(64)))
                
  
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

    
earrow.SMALL  = earrow("%f v pt" % (_base/math.sqrt(64)))
earrow.SMALl  = earrow("%f v pt" % (_base/math.sqrt(32)))
earrow.SMAll  = earrow("%f v pt" % (_base/math.sqrt(16)))
earrow.SMall  = earrow("%f v pt" % (_base/math.sqrt(8)))
earrow.Small  = earrow("%f v pt" % (_base/math.sqrt(4)))
earrow.small  = earrow("%f v pt" % (_base/math.sqrt(2)))
earrow.normal = earrow("%f v pt" % _base)
earrow.large  = earrow("%f v pt" % (_base*math.sqrt(2)))
earrow.Large  = earrow("%f v pt" % (_base*math.sqrt(4)))
earrow.LArge  = earrow("%f v pt" % (_base*math.sqrt(8)))
earrow.LARge  = earrow("%f v pt" % (_base*math.sqrt(16)))
earrow.LARGe  = earrow("%f v pt" % (_base*math.sqrt(32)))
earrow.LARGE  = earrow("%f v pt" % (_base*math.sqrt(64)))

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
        return bbox.bbox()

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
# The main canvas class
#

class canvas(base.PSCmd):

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

        self.PSOps    = []
        self.trafo    = trafo.trafo()
        self.clipbbox = bbox.bbox()

        for arg in args:
            if isinstance(arg, trafo._trafo):
                # XXX or: self.trafo = arg*self.trafo
                self.trafo = self.trafo*arg
                self.PSOps.append(arg)
            elif isinstance(arg, clip):
                self.clipbbox=(self.clipbbox*
                               arg.clipbbox().transform(self.trafo))
                self.PSOps.append(arg)
            else:
                self.set(arg)

    def bbox(self):
        """returns bounding box of canvas"""
        obbox = reduce(lambda x,y:
                       isinstance(y, base.PSCmd) and x+y.bbox() or x,
                       self.PSOps,
                       bbox.bbox())
        
        # transform according to our global transformation and
        # intersect with clipping bounding box (which have already been
        # transformed in canvas.__init__())
        return obbox.transform(self.trafo)*self.clipbbox
            
    def write(self, file):
        for cmd in self.PSOps:
            cmd.write(file)

    def writetofile(self, filename, paperformat=None, rotated=0, fittosize=0, margin="1 t cm"):
        """write canvas to EPS file

        If paperformat is set to a known paperformat, the output will be centered on 
        the page.

        If rotated is set, the output will first be rotated by 90 degrees.

        If fittosize is set, then the output is scaled to the size of the
        page (minus margin). In that case, the paperformat the specification
        of the paperformat is obligatory.

        returns the canvas

        """

        if filename[-4:]!=".eps":
            filename = filename + ".eps"

        try:
            file = open(filename, "w")
        except IOError:
            assert 0, "cannot open output file"                 # TODO: Fehlerbehandlung...

        abbox=self.bbox().enhance("1 t pt")
        ctrafo=None     # global transformation of canvas

        if rotated:
            ctrafo = trafo._rotation(90,
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

            ctrafo = ctrafo._translate(0.5*(width -(abbox.urx-abbox.llx))-
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
                    
                ctrafo = ctrafo._scale(sfactor, sfactor, 0.5*width, 0.5*height)
                          
                
        elif fittosize:
            assert 0, "must specify paper size for fittosize" # TODO: exception...

        # if there has been a global transformation, adjust the bounding box
        # accordingly
        if ctrafo: abbox = abbox.transform(ctrafo) 

        file.write("%!PS-Adobe-3.0 EPSF 3.0\n")
        abbox.write(file)
        file.write("%%%%Creator: PyX %s\n" % pyx.__version__) 
        file.write("%%%%Title: %s\n" % filename) 
        file.write("%%%%CreationDate: %s\n" %
                   time.asctime(time.localtime(time.time())))
        file.write("%%EndComments\n")
        
        file.write("%%BeginProlog\n") 
        file.write(_PSProlog)
        file.write("\n%%EndProlog\n") 

        # again, if there has occured global transformation, apply it now
        if ctrafo: ctrafo.write(file)   

        file.write("%f setlinewidth\n" % unit.topt(linewidth.normal))
        
        # here comes the actual content
        self.write(file)
        
        file.write("showpage\n")
        file.write("%%Trailer\n")
        file.write("%%EOF\n")

        return self
            
    def insert(self, *PSOps):
        """insert one or more PSOps in the canvas 

        All canvases will be encapsulated in a gsave/grestore pair.
        
        returns the (last) PSOp
        
        """
        
        for PSOp in PSOps:
            if isinstance(PSOp, canvas):
                self.PSOps.append(_gsave())
                
            self.PSOps.append(PSOp)
            
            if isinstance(PSOp, canvas):
                self.PSOps.append(_grestore())

            # save last command for return value
            lastop = PSOp
            
        return lastop

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

        dp = DecoratedPath(path)

        # XXX: use attrlist
        if [x for x in args if not (isinstance(x, base.PathStyle) or 
                                    isinstance(x, PathDeco))]:
            raise ValueError("Only instances of base.PathStyle or canvas.PathDeco are allowed")

        # set global styles
        dp.styles = filter(lambda x: isinstance(x, base.PathStyle), args)
        
        # add path decorations and modify path accordingly
        for deco in filter(lambda x: isinstance(x, PathDeco), args):
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
