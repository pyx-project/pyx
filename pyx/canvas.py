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
# - arrows
# - epsfile ".eps" detection

import types, math
import base, unit, trafo

# PostScript-procedure definitions
# cf. file: 5002.EPSF_Spec_v3.0.pdf     

_PSProlog = """/rect {
  4 2 roll moveto 
  1 index 0 rlineto 
  0 exch rlineto 
  neg 0 rlineto 
  closepath 
} bind def
/BeginEPSF {
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
  count op_count sub {pop} repeat % Clean up stacks
  countdictstack dict_count sub {end} repeat
  b4_Inc_state restore
} bind def"""

# known paperformats as tuple(width, height)

_paperformats = { "a4"      : ("210 t mm",  "297 t mm"), 
                  "a3"      : ("297 t mm",  "420 t mm"), 
                  "a2"      : ("420 t mm",  "594 t mm"), 
                  "a1"      : ("594 t mm",  "840 t mm"), 
                  "a0"      : ("840 t mm", "1188 t mm"), 
                  "a0b"     : ("910 t mm", "1350 t mm"), 
                  "letter"  : ("8.5 t in",   "11 t in"),
                  "legal"   : ("8.5 t in",   "14 t in")}

# helper routine for bbox manipulations

def _nmin(x, y):
    """minimum of two values, where None represents +infinity, not -infinity as
    in standard min iplementation of python"""
    if x is None: return y
    if y is None: return x
    return min(x,y)

#
# class representing bounding boxes
#

class bbox:

    """class for bounding boxes"""

    def __init__(self, llx=None, lly=None, urx=None, ury=None):
        self.llx=llx
        self.lly=lly
        self.urx=urx
        self.ury=ury
    
    def __add__(self, other):
        """join two bboxes"""

        return bbox(_nmin(self.llx, other.llx), _nmin(self.lly, other.lly),
                    max(self.urx, other.urx), max(self.ury, other.ury))

    def __mul__(self, other):
        """intersect two bboxes"""

        return bbox(max(self.llx, other.llx), max(self.lly, other.lly),
                    _nmin(self.urx, other.urx), _nmin(self.ury, other.ury))

    def __str__(self):
        return "%s %s %s %s" % (self.llx, self.lly, self.urx, self.ury)

    def write(self, file):
        file.write("%%%%BoundingBox: %d %d %d %d\n" %
                   (self.llx-1, self.lly-1, self.urx+1, self.ury+1))
        # TODO: add HighResBBox

    def intersects(self, other):
        """check, if two bboxes intersect eachother"""
        
        return not (self.llx > other.urx or
                    self.lly > other.ury or
                    self.urx < other.llx or
                    self.ury < other.lly)

    def transform(self, trafo):
        """return bbox transformed by trafo"""
        # we have to transform all four corner points of the bbox
        (llx, lly)=trafo._apply(self.llx, self.lly)
        (lrx, lry)=trafo._apply(self.urx, self.lly)
        (urx, ury)=trafo._apply(self.urx, self.ury)
        (ulx, uly)=trafo._apply(self.llx, self.ury)

        # now, by sorting, we obtain the lower left and upper right corner
        # of the new bounding box. 

        return bbox(min(llx, lrx, urx, ulx), min(lly, lry, ury, uly),
                    max(llx, lrx, urx, ulx), max(lly, lry, ury, uly))

    def enhance(self, size):
        """return bbox enhanced in all directions by size pts"""
        return bbox(self.llx-size, self.lly-size, 
                    self.urx+size, self.ury+size)
    
#
# Exceptions
#
    
class CanvasException(Exception): pass


class PathStyle(base.PSAttr):
    """Style modifiers for paths"""
    pass


class linecap(PathStyle):
    def __init__(self, value=0):
        self.value=value
        
    def write(self, file):
        file.write("%d setlinecap\n" % self.value)

linecap.butt   = linecap(0)
linecap.round  = linecap(1)
linecap.square = linecap(2)


class linejoin(PathStyle):
    def __init__(self, value=0):
        self.value=value
        
    def write(self, file):
        file.write("%d setlinejoin\n" % self.value)

linejoin.miter = linejoin(0)
linejoin.round = linejoin(1)
linejoin.bevel = linejoin(2)


class miterlimit(PathStyle):
    def __init__(self, value=10.0):
        self.value=value
        
    def write(self, file):
        file.write("%f setmiterlimit\n" % self.value)
        

class dash(PathStyle):
    def __init__(self, pattern=[], offset=0):
        self.pattern=pattern
        self.offset=offset

    def write(self, file):
        patternstring=""
        for element in self.pattern:
            patternstring=patternstring + `element` + " "
                              
        file.write("[%s] %d setdash\n" % (patternstring, self.offset))
        

class linestyle(PathStyle):
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
    
 
class linewidth(PathStyle, unit.length):

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
# Path decorations (i.e. mainly arrows)
#

class PathDeco(base.PSCommand, base.PSAttr):
    """Path decorators

    In contrast to path styles, path decorators depend on the concrete
    path to which they are applied. In particular, they don't make
    sense without any path and can thus not be used in canvas.set!

    The corresponding path is passed as first argument in the
    constructor

    """
    pass

class arrow(PathDeco):
    """A general arrow"""

    def __init__(self, bpath, position, size, angle=45, constriction=0.8):
        """constructs an arrow at pos (0: begin, !=0: end) of path with size,
        opening angle and relative constriction"""

        # convert to bpath if necessary
        if not isinstance(bpath, bpath.bpath):
            bpath=bpath.bpath()

        if position:
            bpath=bpath.reverse()

        # first order conversion from pts to the bezier curve's
        # parametrization
        
        lbpel = bp[0]
        tlen  = math.sqrt((lbpel.x3-lbpel.x2)*(lbpel.x3-lbpel.x2)+
                          (lbpel.y3-lbpel.y2)*(lbpel.y3-lbpel.y2))

        # TODO: why factor 0.5?
        len  = 0.5*unit.topt(size)/tlen
        ilen = constriction*len

        # get end point (ex, ey) and constriction point (cx, cy)
        ex, ey = lbpel[0]
        cx, cy = bp[ilen]

        # now we construct the template for our arrow but cutting
        # the path a the corresponding length
        arrowtemplate = bp.split(len)[0]

        # from this template, we construct the two outer curves
        # of the arrow
        arrowl = arrowtemplate.transform(trafo.rotate(-aangle, ex, ey))
        arrowr = arrowtemplate.transform(trafo.rotate( aangle, ex, ey))

        # now come the joining backward parts
        arrow3 = bpath.bline(*(arrowl.pos(0)+arrowr.pos(0)))
        arrow3a= bpath.bline(*(arrowr.pos(0)+(mx,my)))
        arrow3b= bpath.bline(*((mx,my)+arrowl.pos(0)))

        # and here the comlete arrow
        self.arrow = arrowl+arrowr.reverse()+arrow3a+arrow3b

    def bbox(self):
        return self.arrow.bbox()

    def write(self, file):
        for psop in (_newpath(), self.arrow,
                     _gsave(),
                     canvas.linejoin.round, _stroke(), _grestore(), _fill())):
            psop.write(file)

    
class barrow(arrow):
    """arrow at begin of path"""
    def __init__(self, bpath, size, angle=45, constriction=0.8):
        arrow.__int__(self, bpath, position=0, size, angle, constriction)


class earrow(arrow):
    """arrow at end of path"""
    def __init__(self, bpath, size="5 t pt", angle=45, constriction=0.8):
        arrow.__int__(self, bpath, position=1, size, angle, constriction)


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
# PSCommand class
#

class PSCommand:

    """ PSCommand is the base class of all visible elements

    Visible elements, are those, that can be embedded in the Canvas
    and possed a bbox. Furthermore, they can write themselves to
    an open file and to an EPS file
    
    """
    
    def bbox(self):
       raise NotImplementedError, "cannot call virtual method bbox()"
       
    def write(self, file):
        raise NotImplementedError, "cannot call virtual method write()"

    def writetofile(self, filename, paperformat=None, rotated=0, fittosize=0, margin="1 t cm"):
        """write canvas to EPS file

        If paperformat is set to a known paperformat, the output will be centered on 
        the page (and optionally rotated)

        If fittosize is set as well, then the output is scaled to the size of the
        page (minus margin).

        """
        try:
            file = open(filename + ".eps", "w")
        except IOError:
            assert 0, "cannot open output file"                 # TODO: Fehlerbehandlung...

        abbox=self.bbox()
        ctrafo=None     # global transformation of canvas

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
        if ctrafo:
            abbox = abbox.transform(ctrafo) 

        file.write("%!PS-Adobe-3.0 EPSF 3.0\n")
        abbox.write(file)
        file.write("%%Creator: pyx 0.0.1\n") 
        file.write("%%%%Title: %s.eps\n" % filename) 
        # file.write("%%CreationDate: %s" % ) 
        file.write("%%EndComments\n") 
        file.write("%%BeginProlog\n") 
        file.write(_PSProlog)
        file.write("\n%%EndProlog\n") 

        # now apply a potential global transformation
        if ctrafo: ctrafo.write(file)   

        file.write("%f setlinewidth\n" % unit.topt(linewidth.normal))
        
        # here comes the actual content
        self.write(file)
        
        file.write("showpage\n")
        file.write("%%Trailer\n")
        file.write("%%EOF\n")

#
# The main canvas class
#

class canvas(PSCommand):

    """a canvas is a collection of PSCommands together with PSAttrs"""

    def __init__(self, *args, **kwargs):
        
        self.PSOps = []
        self.trafo  = trafo.trafo()

        for arg in args:
            if isinstance(arg, trafo._trafo):
                self.trafo=arg*self.trafo
            self.set(arg)

        # clipping comes last...
        # TODO: integrate this better; do we need a class clip?

        self.clip   = kwargs.get("clip", None)
        if self.clip:
            self.insert((_newpath(), self.clip, _clip()))     # insert clipping path

    def bbox(self):
        obbox = reduce(lambda x,y:
                       isinstance(y, PSCommand) and x+y.bbox() or x,
                       self.PSOps,
                       bbox())

        if self.clip:
            obbox=obbox*self.clip.bbox()    # intersect with clipping bounding boxes

        return obbox.transform(self.trafo).enhance(1)
            
    def write(self, file):
        for cmd in self.PSOps:
            cmd.write(file)
            
    def insert(self, cmds, *args):
        if args: 
           self.PSOps.append(_gsave())
           self.set(*args)

        if type(cmds) in (types.TupleType, types.ListType):
           for cmd in list(cmds): 
              if isinstance(cmd, canvas): self.PSOps.append(_gsave())
              self.PSOps.append(cmd)
              if isinstance(cmd, canvas): self.PSOps.append(_grestore())
        else: 
           if isinstance(cmds, canvas): self.PSOps.append(_gsave())
           self.PSOps.append(cmds)
           if isinstance(cmds, canvas): self.PSOps.append(_grestore())
           
        if args:
           self.PSOps.append(_grestore())
           
        return cmds

    def set(self, *args):
        for arg in args:
            assert isinstance(arg, base.PSAttr), "can only set attributes"
            self.PSOps.append(arg)
        
    def draw(self, path, *args):
        self.insert((_newpath(), path, _stroke()), *args)
        return self
        
    def fill(self, path, *args):
        self.insert((_newpath(), path, _fill()), *args)
        return self

    def drawfilled(self, path, *args):
        self.insert((_newpath(), path, _gsave(), _stroke(), _grestore(), _fill()), *args)
        return self
