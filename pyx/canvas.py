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
# - canvas.__init__() rewrite
# - check the factor 0.5 in arrowhead and PathDeco.modfication
# - should we improve on the arc length -> arg parametrization routine or
#   should we at least factor it out in bpath.bpath?
# - PathDeco cannot be a PSAttr (because it cannot be set via canvas.set())

"""The canvas module provides a PostScript canvas class and related classes
"""

import types, math
import base
import bbox, unit, trafo
import bpath

# PostScript-procedure definitions
# cf. file: 5002.EPSF_Spec_v3.0.pdf     

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


#
# Exceptions
#
    
class CanvasException(Exception): pass

#
# Path style classes
#
# note that as usual in PyX most classes have default instances as members

class PathStyle(base.PSAttr):
    
    """style modifiers for paths"""
    
    pass


class linecap(PathStyle):

    """linecap of paths"""
    
    def __init__(self, value=0):
        self.value=value
        
    def write(self, file):
        file.write("%d setlinecap\n" % self.value)

linecap.butt   = linecap(0)
linecap.round  = linecap(1)
linecap.square = linecap(2)


class linejoin(PathStyle):

    """linejoin of paths"""
    
    def __init__(self, value=0):
        self.value=value
        
    def write(self, file):
        file.write("%d setlinejoin\n" % self.value)

linejoin.miter = linejoin(0)
linejoin.round = linejoin(1)
linejoin.bevel = linejoin(2)


class miterlimit(PathStyle):

    """miterlimit of paths"""
    
    def __init__(self, value=10.0):
        self.value=value
        
    def write(self, file):
        file.write("%f setmiterlimit\n" % self.value)
        

class dash(PathStyle):

    """dash of paths"""
    
    def __init__(self, pattern=[], offset=0):
        self.pattern=pattern
        self.offset=offset

    def write(self, file):
        patternstring=""
        for element in self.pattern:
            patternstring=patternstring + `element` + " "
                              
        file.write("[%s] %d setdash\n" % (patternstring, self.offset))
        

class linestyle(PathStyle):

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
    
 
class linewidth(PathStyle, unit.length):

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
# arrowheads are simple PSCmds
#

class arrowhead(base.PSCmd):

    """represents an arrowhead (usually constructed via arrow.decoration)"""
  
    def __init__(self, abpath, size, angle, constriction):
        """arrow at pos (0: begin, !=0: end) of path with size,
        opening angle and relative constriction"""
        
        # first order conversion from pts to the bezier curve's
        # parametrization
          
        lbpel = abpath[0]
        tlen  = math.sqrt((lbpel.x3-lbpel.x2)*(lbpel.x3-lbpel.x2)+
                          (lbpel.y3-lbpel.y2)*(lbpel.y3-lbpel.y2))
  
        # TODO: why factor 0.5?
        alen  = 0.5*unit.topt(size)/tlen
        if alen>len(abpath): alen=len(abpath)
        
        # get tip (tx, ty)
        tx, ty = abpath.begin()
        
        # now we construct the template for our arrow but cutting
        # the path a the corresponding length
        arrowtemplate = abpath.split(alen)[0]
  
        # from this template, we construct the two outer curves
        # of the arrow
        arrowl = arrowtemplate.transform(trafo.rotate(-angle/2.0, tx, ty))
        arrowr = arrowtemplate.transform(trafo.rotate( angle/2.0, tx, ty))
        
        # now come the joining backward parts
        if constriction:
            # arrow with constriction

            # constriction point (cx, cy) lies on path
            cx, cy = abpath.pos(constriction*alen)
            
            arrow3a= bpath.bline(*(arrowl.end()+(cx,cy)))
            arrow3b= bpath.bline(*((cx,cy)+arrowr.end()))

            # define the complete arrow
            self.arrow = arrowl+arrow3a+arrow3b+arrowr.reverse()
        else:
            # arrow without constriction
            arrow3 = bpath.bline(*(arrowl.end()+arrowr.end()))
                                 
            # define the complete arrow
            self.arrow = arrowl+arrow3+arrowr.reverse()
        
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
        """return decoration of path as PSCmd"""
        pass

    def modification(self, path):
        """return modified path"""
    

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

    def modification(self, path):
        # convert to bpath if necessary
        if isinstance(path, bpath.bpath):
            abpath=path
        else:
            abpath=path.bpath()
            
        if self.position:
            abpath=abpath.reverse()
        
        # the following lines are copied from arrowhead.init()
        
        # first order conversion from pts to the bezier curve's
        # parametrization
          
        lbpel = abpath[0]
        tlen  = math.sqrt((lbpel.x3-lbpel.x2)*(lbpel.x3-lbpel.x2)+
                          (lbpel.y3-lbpel.y2)*(lbpel.y3-lbpel.y2))
  
        # TODO: why factor 0.5?
        alen  = 0.5*unit.topt(self.size)/tlen
        if alen>len(abpath): alen=len(abpath)

        if self.constriction:
            ilen = alen*self.constriction
        else:
            ilen = alen

        # correct somewhat for rotation of arrow segments
        ilen = ilen*math.cos(math.pi*self.angle/360.0)

        # this is the rest of the path, we have to draw
        abpath = abpath.split(ilen)[1]

        # go back to original orientation, if necessary
        if self.position:
            abpath=abpath.reverse()

        return abpath
    
        
class barrow(arrow):
    
    """arrow at begin of path"""
    
    def __init__(self, size, angle=45, constriction=0.8):
        arrow.__init__(self, 0, size, angle, constriction)

_base = 2

barrow.SMALL  = barrow("%f t pt" % (_base/math.sqrt(64)))
barrow.SMALl  = barrow("%f t pt" % (_base/math.sqrt(32)))
barrow.SMAll  = barrow("%f t pt" % (_base/math.sqrt(16)))
barrow.SMall  = barrow("%f t pt" % (_base/math.sqrt(8)))
barrow.Small  = barrow("%f t pt" % (_base/math.sqrt(4)))
barrow.small  = barrow("%f t pt" % (_base/math.sqrt(2)))
barrow.normal = barrow("%f t pt" % _base)
barrow.large  = barrow("%f t pt" % (_base*math.sqrt(2)))
barrow.Large  = barrow("%f t pt" % (_base*math.sqrt(4)))
barrow.LArge  = barrow("%f t pt" % (_base*math.sqrt(8)))
barrow.LARge  = barrow("%f t pt" % (_base*math.sqrt(16)))
barrow.LARGe  = barrow("%f t pt" % (_base*math.sqrt(32)))
barrow.LARGE  = barrow("%f t pt" % (_base*math.sqrt(64)))
                
  
class earrow(arrow):
    
    """arrow at end of path"""
    
    def __init__(self, size, angle=45, constriction=0.8):
        arrow.__init__(self, 1, size, angle, constriction)

earrow.SMALL  = earrow("%f t pt" % (_base/math.sqrt(64)))
earrow.SMALl  = earrow("%f t pt" % (_base/math.sqrt(32)))
earrow.SMAll  = earrow("%f t pt" % (_base/math.sqrt(16)))
earrow.SMall  = earrow("%f t pt" % (_base/math.sqrt(8)))
earrow.Small  = earrow("%f t pt" % (_base/math.sqrt(4)))
earrow.small  = earrow("%f t pt" % (_base/math.sqrt(2)))
earrow.normal = earrow("%f t pt" % _base)
earrow.large  = earrow("%f t pt" % (_base*math.sqrt(2)))
earrow.Large  = earrow("%f t pt" % (_base*math.sqrt(4)))
earrow.LArge  = earrow("%f t pt" % (_base*math.sqrt(8)))
earrow.LARge  = earrow("%f t pt" % (_base*math.sqrt(16)))
earrow.LARGe  = earrow("%f t pt" % (_base*math.sqrt(32)))
earrow.LARGE  = earrow("%f t pt" % (_base*math.sqrt(64)))

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

    def __init__(self, *args, **kwargs):

        """construct a canvas

        TODO: documentation of options

        """

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
        """returns bounding box of canvas"""
        obbox = reduce(lambda x,y:
                       isinstance(y, base.PSCmd) and x+y.bbox() or x,
                       self.PSOps,
                       bbox.bbox())

        if self.clip:
            obbox=obbox*self.clip.bbox()    # intersect with clipping bounding boxes

        return obbox.transform(self.trafo).enhance(1)
            
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
        file.write("%%Creator: pyx 0.0.1\n") 
        file.write("%%%%Title: %s.eps\n" % filename) 
        # file.write("%%CreationDate: %s" % ) 
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
            
    def insert(self, PSOps, *styles):
        """insert one or more PSOps in the canvas applying styles if given

        If styles are present, the PSOps are encapsulated with gsave/grestore.
        The same happens upon insertion of a canvas.
        
        returns the (last) PSOp
        
        """

        # encapsulate in gsave/grestore command if necessary
        if styles:
            self.PSOps.append(_gsave())

        # add path styles if present
        if styles:
            self.set(*styles)

        if not type(PSOps) in (types.TupleType, types.ListType):
            PSOps = (PSOps,)
            
        for PSOp in PSOps:
            if isinstance(PSOp, canvas):
                self.PSOps.append(_gsave())
                
            self.PSOps.append(PSOp)
            
            if isinstance(PSOp, canvas):
                self.PSOps.append(_gsave())

            # save last command for return value
            lastop = PSOp
           
        if styles:
            self.PSOps.append(_grestore())
           
        return lastop

    def set(self, *args):

        """sets PSAttrs args globally for the rest of the canvas

        returns canvas

        """
        
        for arg in args:
            if not isinstance(arg, base.PSAttr):
                raise NotImplementedError, "can only set attribute"
            self.PSOps.append(arg)

        return self
        
    def draw(self, path, *args):
        """draw path/bpath on canvas using the style given by args

        The argument list args consists of PSAttrs, which modify
        the appearance of the path. Some of the may be PathDecos,
        which add some new visual elements to the path.

        returns the canvas

        """
        # add path decorations and modify path accordingly
        for deco in filter(lambda x: isinstance(x, PathDeco), args):
            self.insert(deco.decoration(path))
            path=deco.modification(path)

        self.insert((_newpath(), path, _stroke()),
                    *filter(lambda x: not isinstance(x, PathDeco), args))
        
        return self
        
    def fill(self, path, *args):
        """fill path/bpath on canvas using the style given by args

        The argument list args consists of PSAttrs, which modify
        the appearance of the path.

        returns the canvas

        """

        self.insert((_newpath(), path, _fill()), *args)
        return self

    def drawfilled(self, path, *args):
        """fill path/bpath on canvas using the style given by args

        The argument list args consists of PSAttrs, which modify
        the appearance of the path.

        returns the canvas

        """

        self.insert((_newpath(), path, _gsave(), _stroke(), _grestore(), _fill()), *args)
        return self
