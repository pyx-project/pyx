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
import bpath

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
# arrowheads are simple PSCommands
#

class arrowhead(base.PSCommand):

    """represents and arrowhead, which is usually constructed by an
    arrow.attach call"""
  
    def __init__(self, abpath, size, angle, constriction):
        """arrow at pos (0: begin, !=0: end) of path with size,
        opening angle and relative constriction"""
        
        # first order conversion from pts to the bezier curve's
        # parametrization
          
        lbpel = abpath[0]
        tlen  = math.sqrt((lbpel.x3-lbpel.x2)*(lbpel.x3-lbpel.x2)+
                          (lbpel.y3-lbpel.y2)*(lbpel.y3-lbpel.y2))
  
        # TODO: why factor 0.5?
        len  = 0.5*unit.topt(size)/tlen
        ilen = constriction*len
        
        # get tip (ex, ey) and constriction point (cx, cy)
        tx, ty = abpath.begin()
        cx, cy = abpath.pos(ilen)
        
        # now we construct the template for our arrow but cutting
        # the path a the corresponding length
        arrowtemplate = abpath.split(len)[0]
  
        # from this template, we construct the two outer curves
        # of the arrow
        arrowl = arrowtemplate.transform(trafo.rotate(-angle/2.0, tx, ty))
        arrowr = arrowtemplate.transform(trafo.rotate( angle/2.0, tx, ty))
        
        # now come the joining backward parts
        # arrow3 = bpath.bline(*(arrowl.pos(ilen)+arrowr.pos(ilen)))
        arrow3a= bpath.bline(*(arrowl.end()+(cx,cy)))
        arrow3b= bpath.bline(*((cx,cy)+arrowr.end()))
        
        # and here the comlete arrow
        self.arrow = arrowl+arrow3a+arrow3b+arrowr.reverse()
        
    def bbox(self):
        return self.arrow.bbox()
  
    def write(self, file):
        for psop in (_newpath(),
                     self.arrow,
                     _gsave(),
                     linejoin.round, _stroke(), _grestore(), _fill()):
            psop.write(file)

#
# Path decorations (i.e. mainly arrows)
#

class PathDeco:
    
    """Path decorators
    
    In contrast to path styles, path decorators depend on the concrete
    path to which they are applied. In particular, they don't make
    sense without any path and can thus not be used in canvas.set!
    
    The corresponding path is passed as first argument in the
    constructor
    
    """

    def decoration(self, path):
        """return decoration of path as PSCommand"""
        pass

class arrow(PathDeco):
    
    """A general arrow"""

    def __init__(self, position, size, angle=45, constriction=0.8):
        self.position = position
        self.size = size
        self.angle = angle
        self.constriction = constriction

    def decoration(self, path):
        # convert to bpath if necessary
        if isinstance(path, bpath.bpath):
            abpath=path
        else:
            abpath=path.bpath()
            
        if self.position:
            abpath=abpath.reverse()

        return arrowhead(abpath, self.size, self.angle, self.constriction)
    
        
class barrow(arrow):
    
    """arrow at begin of path"""
    
    def __init__(self, size, angle=45, constriction=0.8):
        arrow.__init__(self, 0, size, angle, constriction)

_base = 5

barrow.tiny   = barrow("%f t pt" % (_base/math.sqrt(4)))
barrow.small  = barrow("%f t pt" % (_base/math.sqrt(2)))
barrow.normal = barrow("%f t pt" % _base)
barrow.large  = barrow("%f t pt" % (_base*math.sqrt(2)))
barrow.huge   = barrow("%f t pt" % (_base*math.sqrt(4)))
                
  
class earrow(arrow):
    
    """arrow at end of path"""
    
    def __init__(self, size, angle=45, constriction=0.8):
        arrow.__init__(self, 1, size, angle, constriction)

earrow.tiny   = earrow("%f t pt" % (_base/math.sqrt(4)))
earrow.small  = earrow("%f t pt" % (_base/math.sqrt(2)))
earrow.normal = earrow("%f t pt" % _base)
earrow.large  = earrow("%f t pt" % (_base*math.sqrt(2)))
earrow.huge   = earrow("%f t pt" % (_base*math.sqrt(4)))
      

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

class canvas(base.PSCommand):

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
                       isinstance(y, base.PSCommand) and x+y.bbox() or x,
                       self.PSOps,
                       bbox())

        if self.clip:
            obbox=obbox*self.clip.bbox()    # intersect with clipping bounding boxes

        return obbox.transform(self.trafo).enhance(1)
            
    def write(self, file):
        for cmd in self.PSOps:
            cmd.write(file)
            
    def insert(self, cmds, *styles):
        """insert one or more PSOps in the canvas applying styles if given

        returns the (last) cmd
        """

        # encapsulate in gsave/grestore command if necessary
        if styles:
            self.PSOps.append(_gsave())

        # add path styles if present
        if styles:
            self.set(*styles)

        if not type(cmds) in (types.TupleType, types.ListType):
            cmds = (cmds,)
            
        for cmd in cmds:
            if isinstance(cmd, canvas):
                self.PSOps.append(_gsave())
                
            self.PSOps.append(cmd)
            
            if isinstance(cmd, canvas):
                self.PSOps.append(_gsave())

            # save last command for return value
            lastcmd = cmd
           
        if styles:
            self.PSOps.append(_grestore())
           
        return lastcmd

    def set(self, *args):
        for arg in args:
            if not isinstance(arg, base.PSAttr):
                raise NotImplementedError, "can only set attribute"
            self.PSOps.append(arg)
        
    def draw(self, path, *args):
        self.insert((_newpath(), path, _stroke()),
                    *filter(lambda x: not isinstance(x, PathDeco), args))
        
        # add path decorations
        for deco in filter(lambda x: isinstance(x, PathDeco), args):
            self.insert(deco.decoration(path))
            
        return self
        
    def fill(self, path, *args):
        self.insert((_newpath(), path, _fill()), *args)
        return self

    def drawfilled(self, path, *args):
        self.insert((_newpath(), path, _gsave(), _stroke(), _grestore(), _fill()), *args)
        return self
