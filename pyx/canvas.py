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


import re, unit, trafo, types
from math import sqrt

# PostScript-procedure definitions
# cf. file: 5002.EPSF_Spec_v3.0.pdf     

PSProlog = """/rect {
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

# helper routine for bbox manipulations

def _nmin(x, y):
    """ minimum of two values, where None represents +infinity, not -infinity as
    in standard min iplementation of python"""
    if x is None: return y
    if y is None: return x
    return min(x,y)

#
# class representing bounding boxes
#


class bbox:

    ' class for bounding boxes '

    def __init__(self, llx=None, lly=None, urx=None, ury=None):
	self.llx=llx
	self.lly=lly
	self.urx=urx
	self.ury=ury
    
    def __add__(self, other):
        ' join two bboxes '

        return bbox(_nmin(self.llx, other.llx), _nmin(self.lly, other.lly),
                    max(self.urx, other.urx), max(self.ury, other.ury))
    

    def __mul__(self, other):
        ' intersect two bboxes '

        return bbox(max(self.llx, other.llx), max(self.lly, other.lly),
                    _nmin(self.urx, other.urx), _nmin(self.ury, other.ury))

    def intersects(self, other):
        ' check, if two bboxes intersect eachother '
        
        return not (self.llx > other.urx or
                    self.lly > other.ury or
                    self.urx < other.llx or
                    self.ury < other.lly)

    def write(self, file):
        file.write("%%%%BoundingBox: %d %d %d %d\n" % (self.llx-1, self.lly-1, self.urx+1, self.ury+1)) 

    def __str__(self):
	return "%s %s %s %s" % (self.llx, self.lly, self.urx, self.ury)
    
#
# helper class for EPS files
#

bbpattern = re.compile( r"^%%BoundingBox:\s+([+-]?\d+)\s+([+-]?\d+)\s+([+-]?\d+)\s+([+-]?\d+)\s*$" )


class epsfile:

    def __init__(self, filename, x = "0 t m", y = "0 t m",
                 clip = 1, translatebb = 1, showbb = 0):
        self.x           = unit.topt(x)
        self.y           = unit.topt(y)
        self.filename    = filename
        self.clip        = clip
        self.translatebb = translatebb
        self.showbb      = showbb

    def getbbox(self, translatebb):
        'returns bounding box of EPS file filename as 4-tuple (llx, lly, urx, ury)'
        
        try:
            file = open(self.filename,"r")
        except:
            assert 0, "cannot open EPS file"	# TODO: Fehlerbehandlung

        while 1:
            line=file.readline()
            if not line:
                assert 0, "bounding box not found in EPS file"
                raise IOError			# TODO: Fehlerbehandlung
            if line=="%%EndComments\n": 
                # TODO: BoundingBox-Deklaration kann auch an Ende von Datei verschoben worden sein
                assert 0, "bounding box not found in EPS file"
                raise IOError			# TODO: Fehlerbehandlung
            
            bbmatch = bbpattern.match(line)
            if bbmatch is not None:
               (llx, lly, urx, ury) = map(int, bbmatch.groups()) # conversion strings->int
               if translatebb:
                   (llx, lly, urx, ury) = (0, 0, urx - llx, ury - lly)
	       return bbox(llx, lly, urx, ury)

    def bbox(self):
        return self.getbbox(self.translatebb)

    def write(self, file):
	mybbox = self.getbbox(0)

        try:
	    epsfile=open(self.filename,"r")
	except:
	    assert 0, "cannot open EPS file"	               # TODO: Fehlerbehandlung

        file.write("BeginEPSF\n")
        file.write("%f %f translate\n" % (self.x, self.y))
	
        if self.translatebb:
            file.write("%f %f translate\n" % (-mybbox.llx, -mybbox.lly))
	    
        if self.showbb:
            file.write("newpath\n")
            file.write("%f %f %f %f rect\n" % (mybbox.llx, 
	                                       mybbox.lly, 
	                                       mybbox.urx-mybbox.llx,
					       mybbox.ury-mybbox.lly))
	    file.write("stroke\n")
	    
        if self.clip:
            file.write("%f %f %f %f rect\n" % (mybbox.llx, 
	                                       mybbox.lly, 
	                                       mybbox.urx-mybbox.llx,
					       mybbox.ury-mybbox.lly))
            file.write("clip newpath\n")

        file.write("%%%%BeginDocument: %s\n" % self.filename)
        file.write(epsfile.read()) 
        file.write("%%EndDocument\nEndEPSF\n")

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
        file.write(self._PSCmd())

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

linejoinmiter=_linejoin(0)

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
 
    THIN       = _linewidth("%f cm" % (_base/sqrt(32)))
    THIn       = _linewidth("%f cm" % (_base/sqrt(16)))
    THin       = _linewidth("%f cm" % (_base/sqrt(8)))
    Thin       = _linewidth("%f cm" % (_base/sqrt(4)))
    thin       = _linewidth("%f cm" % (_base/sqrt(2)))
    normal     = _linewidth("%f cm" % _base)
    thick      = _linewidth("%f cm" % (_base*sqrt(2)))
    Thick      = _linewidth("%f cm" % (_base*sqrt(4)))
    THick      = _linewidth("%f cm" % (_base*sqrt(8)))
    THIck      = _linewidth("%f cm" % (_base*sqrt(16)))
    THICk      = _linewidth("%f cm" % (_base*sqrt(32)))
    THICK      = _linewidth("%f cm" % (_base*sqrt(64)))

#
# main canvas class
#

class CanvasCmds:
    def bbox(self):
       return bbox()
       
    def write(self, file):
       pass

class _newpath(CanvasCmds):
    def write(self, file):
       file.write("newpath")

class _stroke(CanvasCmds):
    def write(self, file):
       file.write("stroke")

class _fill(CanvasCmds):
    def write(self, file):
        file.write("fill")

class _clip(CanvasCmds):
    def write(self, file):
       file.write("clip")

class _gsave(CanvasCmds):
    def write(self, file):
       file.write("gsave")

class _grestore(CanvasCmds):
    def write(self, file):
       file.write("grestore")

class _translate(CanvasCmds):
    def __init__(self, x, y):
        self.x = unit.topt(x)
        self.y = unit.topt(y)
        
    def write(self, file):
        file.write("%f %f translate" % (self.x, self.y) )


class canvas(CanvasCmds):

    def __init__(self, *args, **kwargs):
        
        self.PSCmds = []
 	self.trafo  = trafo.transformation()

        for arg in args:
  	    if isinstance(arg, trafo.transformation):
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
            
        # we have to transform all four corner points of the bbox
        (llx, lly)=self.trafo.apply((obbox.llx, obbox.lly))
        (lrx, lry)=self.trafo.apply((obbox.urx, obbox.lly))
        (urx, ury)=self.trafo.apply((obbox.urx, obbox.ury))
        (ulx, uly)=self.trafo.apply((obbox.llx, obbox.ury))

        # now, by sorting, we obtain the lower left and upper right corner
        # of the new bounding box. 

	abbox= bbox(min(llx, lrx, urx, ulx)-1, min(lly, lry, ury, uly)-1,
                    max(llx, lrx, urx, ulx)+1, max(lly, lry, ury, uly)+1)
 
	return abbox
    
    def write(self, file):
        for cmd in self.PSCmds:
            cmd.write(file)
            file.write("\n")
            

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

    def writetofile(self, filename):
        try:
  	    file = open(filename + ".eps", "w")
	except IOError:
	    assert 0, "cannot open output file"		        # TODO: Fehlerbehandlung...

        file.write("%!PS-Adobe-3.0 EPSF 3.0\n")
	abbox=self.bbox()
	abbox.write(file)
        file.write("%%Creator: pyx 0.0.1\n") 
        file.write("%%%%Title: %s.eps\n" % filename) 
        # file.write("%%CreationDate: %s" % ) 
        file.write("%%EndComments\n") 
        file.write("%%BeginProlog\n") 
        file.write(PSProlog)
        file.write("\n%%EndProlog\n") 
        file.write("%f setlinewidth\n" % unit.topt(linewidth.normal))
        
        # here comes the actual content
        self.write(file)
        
        file.write("\nshowpage\n")
        file.write("%%Trailer\n")
        file.write("%%EOF\n")
