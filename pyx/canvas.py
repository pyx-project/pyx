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
# - _linewidth -> linewith ...
# - epsfile scaling, centering, ...


import unit, trafo, types, math

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

# known paperformats as tuple(width,

_paperformats = { "a4"      : ("210 t mm",  "297 t mm", 0), 
                  "a3"      : ("297 t mm",  "420 t mm", 0), 
                  "a2"      : ("420 t mm",  "594 t mm", 0), 
                  "a1"      : ("594 t mm",  "840 t mm", 0), 
                  "a0"      : ("840 t mm", "1188 t mm", 0), 
                  "letter"  : ("8.5 t in",   "11 t in", 0),
                  "a4_r"    : ("210 t mm",  "297 t mm", 1), 
                  "a3_r"    : ("297 t mm",  "420 t mm", 1), 
                  "a2_r"    : ("420 t mm",  "594 t mm", 1), 
                  "a1_r"    : ("594 t mm",  "840 t mm", 1), 
                  "a0_r"    : ("840 t mm", "1188 t mm", 1),
                  "letter_r": ("8.5 t in",   "11 t in", 1) }

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

#
# property classes
#

class PyxAttributes:
    def bbox(self):
        return bbox()

    def _PSCmd(self):
        return ""

    def write(self, file):
        file.write("%s\n" % self._PSCmd())


class _linecap(PyxAttributes):
    def __init__(self, value=0):
        self.value=value
        
    def _PSCmd(self):
        return "%d setlinecap" % self.value
        

class linecap(_linecap):
    butt   = _linecap(0)
    round  = _linecap(1)
    square = _linecap(2)


class _linejoin(PyxAttributes):
    def __init__(self, value=0):
        self.value=value
        
    def _PSCmd(self):
        return "%d setlinejoin" % self.value

 
class linejoin(_linejoin):
    miter = _linejoin(0)
    round = _linejoin(1)
    bevel = _linejoin(2)


class _miterlimit(PyxAttributes):
    def __init__(self, value=10.0):
        self.value=value
        
    def _PSCmd(self):
        return "%f setmiterlimit" % self.value
        

class miterlimit(_miterlimit):
    pass
    

class _dash(PyxAttributes):
    def __init__(self, pattern=[], offset=0):
        self.pattern=pattern
        self.offset=offset

    def _PSCmd(self):
        patternstring=""
        for element in self.pattern:
            patternstring=patternstring + `element` + " "
                              
        return "[%s] %d setdash" % (patternstring, self.offset)
        

class dash(_dash):
    pass
    
 
class _linestyle(PyxAttributes):
    def __init__(self, c=linecap.butt, d=dash([])):
        self.c=c
        self.d=d
    def _PSCmd(self):
        return self.c._PSCmd() + "\n" + self.d._PSCmd()
        
       
class linestyle(_linestyle):
    solid      = _linestyle(linecap.butt,  dash([]))
    dashed     = _linestyle(linecap.butt,  dash([2]))
    dotted     = _linestyle(linecap.round, dash([0, 3]))
    dashdotted = _linestyle(linecap.round, dash([0, 3, 3, 3]))
    
 
class _linewidth(PyxAttributes, unit.length):
    def __init__(self, l):
        unit.length.__init__(self, l=l, default_type="w")
    def _PSCmd(self):
        return "%f setlinewidth" % unit.topt(self)
    

class linewidth(_linewidth):
    _base      = 0.02
 
    THIN       = _linewidth("%f cm" % (_base/math.sqrt(32)))
    THIn       = _linewidth("%f cm" % (_base/math.sqrt(16)))
    THin       = _linewidth("%f cm" % (_base/math.sqrt(8)))
    Thin       = _linewidth("%f cm" % (_base/math.sqrt(4)))
    thin       = _linewidth("%f cm" % (_base/math.sqrt(2)))
    normal     = _linewidth("%f cm" % _base)
    thick      = _linewidth("%f cm" % (_base*math.sqrt(2)))
    Thick      = _linewidth("%f cm" % (_base*math.sqrt(4)))
    THick      = _linewidth("%f cm" % (_base*math.sqrt(8)))
    THIck      = _linewidth("%f cm" % (_base*math.sqrt(16)))
    THICk      = _linewidth("%f cm" % (_base*math.sqrt(32)))
    THICK      = _linewidth("%f cm" % (_base*math.sqrt(64)))

#
# main canvas class
#

class PSCommand:
    def bbox(self):
       return bbox()
       
    def write(self, file):
       pass

    def writetofile(self, filename, paperformat=None, fittosize=0, margin="1 t cm"):
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

        if paperformat:
            # center (optionally rotated) output on page
            try:
                width, height, rotated = _paperformats[paperformat]
                width = unit.topt(width)
                height = unit.topt(height)
            except KeyError:
                raise KeyError, "unknown paperformat '%s'" % paperformat

            ctrafo = trafo._translate(0.5*(width -(abbox.urx-abbox.llx))-abbox.llx, 
                                      0.5*(height-(abbox.ury-abbox.lly))-abbox.lly)
                                          
            if rotated:
                ctrafo = trafo._rotate(90, 0.5*width, 0.5*height)*ctrafo

            if fittosize:
                # scale output to pagesize - margins
                margin=unit.topt(margin)

                if rotated:
                    sfactor = min((height-2*margin)/(abbox.urx-abbox.llx), 
                                  (width-2*margin)/(abbox.ury-abbox.lly))
                else:
                    sfactor = min((width-2*margin)/(abbox.urx-abbox.llx), 
                                  (height-2*margin)/(abbox.ury-abbox.lly))

                ctrafo = (trafo._translate(0.5*width, 0.5*height)*
                          trafo.scale(sfactor)*
                          trafo._translate(-0.5*width, -0.5*height)*
                          ctrafo)
                          
            # adjust bounding box
            abbox = abbox.transform(ctrafo)
                
        elif fittosize:
              assert 0, "must specify paper size for fittosize" # TODO: exception...

        file.write("%!PS-Adobe-3.0 EPSF 3.0\n")
        abbox.write(file)
        file.write("%%Creator: pyx 0.0.1\n") 
        file.write("%%%%Title: %s.eps\n" % filename) 
        # file.write("%%CreationDate: %s" % ) 
        file.write("%%EndComments\n") 
        file.write("%%BeginProlog\n") 
        file.write(_PSProlog)
        file.write("\n%%EndProlog\n") 
        
        if ctrafo: ctrafo.write(file)   # add global transformation if necessary

        file.write("%f setlinewidth\n" % unit.topt(linewidth.normal))
        
        # here comes the actual content
        self.write(file)
        
        file.write("showpage\n")
        file.write("%%Trailer\n")
        file.write("%%EOF\n")
       

class _newpath(PSCommand):
    def write(self, file):
       file.write("newpath\n")
       

class _stroke(PSCommand):
    def write(self, file):
       file.write("stroke\n")
       

class _fill(PSCommand):
    def write(self, file):
        file.write("fill\n")
        

class _clip(PSCommand):
    def write(self, file):
       file.write("clip\n")
       

class _gsave(PSCommand):
    def write(self, file):
       file.write("gsave\n")
       

class _grestore(PSCommand):
    def write(self, file):
       file.write("grestore\n")
       

class _translate(PSCommand):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        
    def write(self, file):
        file.write("%f %f translate\n" % (self.x, self.y) )


class canvas(PSCommand):

    def __init__(self, *args, **kwargs):
        
        self.PSCmds = []
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
        obbox = reduce(lambda x,y: x+y.bbox(), self.PSCmds, bbox())

        if self.clip:
            obbox=obbox*self.clip.bbox()    # intersect with clipping bounding boxes

        return obbox.transform(self.trafo).enhance(1)
            
    def write(self, file):
        for cmd in self.PSCmds:
            cmd.write(file)
            
    def insert(self, cmds, *args):
        if args: 
           self.PSCmds.append(_gsave())
           self.set(*args)

        if type(cmds) in (types.TupleType, types.ListType):
           for cmd in list(cmds): 
              if isinstance(cmd, canvas): self.PSCmds.append(_gsave())
              self.PSCmds.append(cmd)
              if isinstance(cmd, canvas): self.PSCmds.append(_grestore())
        else: 
           if isinstance(cmds, canvas): self.PSCmds.append(_gsave())
           self.PSCmds.append(cmds)
           if isinstance(cmds, canvas): self.PSCmds.append(_grestore())
           
        if args:
           self.PSCmds.append(_grestore())
           
        return cmds

    def create(self, pyxclass, *args, **kwargs):
        instance = pyxclass( *args, **kwargs)
        return instance

    def set(self, *args):
        for arg in args: 
           self.insert(arg)
        
    def draw(self, path, *args):
        self.insert((_newpath(), path, _stroke()), *args)
        return self
        
    def fill(self, path, *args):
        self.insert((_newpath(), path, _fill()), *args)
        return self

    def drawfilled(self, path, *args):
        self.insert((_newpath(), path, _gsave(), _stroke(), _grestore(), _fill()), *args)
        return self
