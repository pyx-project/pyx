#!/usr/bin/env python

import string, re, tex, unit, trafo
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

#
# helper class for EPS files
#

bbpattern = re.compile( r"^%%BoundingBox:\s+([+-]?\d+)\s+([+-]?\d+)\s+([+-]?\d+)\s+([+-]?\d+)\s*$" )

class epsfile:

    def __init__(self, filename, x = "0 t m", y = "0 t m", unit = unit.unit(), clip = 1, translatebb = 1, showbb = 0):
        self.unit        = unit
        self.x           = unit.pt(x)
        self.y           = unit.pt(y)
        self.filename     = filename
        self.clip        = clip
        self.translatebb = translatebb
        self.showbb      = showbb
        self._ReadEPSBoundingBox()                         

    def _ReadEPSBoundingBox(self):
        'determines bounding box of EPS file filename as 4-tuple (llx, lly, urx, ury)'
        try:
            file = open(self.filename,"r")
        except:
            assert 0, "cannot open EPS file"	# TODO: Fehlerbehandlung

        while 1:
            line=file.readline()
            if not line:
                assert "bounding box not found in EPS file"
                raise IOError			# TODO: Fehlerbehandlung
            if line=="%%EndComments\n": 
                # TODO: BoundingBox-Deklaration kann auch an Ende von Datei verschoben worden sein
                assert "bounding box not found in EPS file"
                raise IOError			# TODO: Fehlerbehandlung
            
            bbmatch = bbpattern.match(line)
            if bbmatch is not None:
               (self.llx, self.lly, self.urx, self.ury) = map(int, bbmatch.groups())		# conversion strings->int
               break

    def __str__(self):
        try:
	    file=open(self.filename,"r")
	except:
	    assert "cannot open EPS file"	                          # TODO: Fehlerbehandlung

        preamble = "BeginEPSF\n"
        preamble = preamble + "%f %f translate\n" % (self.x, self.y)
        if self.translatebb:
            preamble = preamble + "%f %f translate\n" % (-self.llx, -self.lly)
        if self.showbb:
            preamble = preamble + "newpath\n%f %f moveto\n%f 0 rlineto\n0 %f rlineto\n%f 0 rlineto\nclosepath\nstroke\n" % ( self.llx, self.lly, self.urx-self.llx, self.ury-self.lly, -(self.urx-self.llx))
        if self.clip:
            preamble = preamble + "%f %f %f %f rect\n" % ( self.llx, self.lly, self.urx-self.llx,self.ury-self.lly)
            preamble = preamble + "clip newpath\n"
        preamble = preamble + "%%%%BeginDocument: %s\n" % self.filename
        
        return preamble + file.read() + "%%EndDocument\nEndEPSF\n"

#
# Exceptions
#
    
class CanvasException(Exception): pass

#
# property classes
#

class _linecap:
    def __init__(self, value=0):
        self.value=value
    def _PSCmd(self, canvas):
        return "%d setlinecap" % self.value

class linecap:
    butt   = _linecap(0)
    round  = _linecap(1)
    square = _linecap(2)

class _linejoin:
    def __init__(self, value=0):
        self.value=value
    def _PSCmd(self, canvas):
        return "%d setlinejoin" % self.value
 
class linejoin(_linejoin):
    miter = _linejoin(0)
    round = _linejoin(1)
    bevel = _linejoin(2)

linejoinmiter=_linejoin(0)

class _miterlimit:
    def __init__(self, value=10.0):
        self.value=value
    def _PSCmd(self, canvas):
        return "%f setmiterlimit" % self.value

class miterlimit(_miterlimit):
    pass

class _dash:
    def __init__(self, pattern=[], offset=0):
        self.pattern=pattern
        self.offset=offset
    def _PSCmd(self, canvas):
        patternstring=""
        for element in self.pattern:
            patternstring=patternstring + `element` + " "
                              
        return "[%s] %d setdash" % (patternstring, self.offset)

class dash(_dash):
    pass
 
class _linestyle:
    def __init__(self, c=linecap.butt, d=dash([])):
        self.c=c
        self.d=d
    def _PSCmd(self, canvas):
        return self.c._PSCmd(canvas) + "\n" + self.d._PSCmd(canvas)
       
class linestyle(_linestyle):
    solid      = _linestyle(linecap.butt,  dash([]))
    dashed     = _linestyle(linecap.butt,  dash([2]))
    dotted     = _linestyle(linecap.round, dash([0, 3]))
    dashdotted = _linestyle(linecap.round, dash([0, 3, 3, 3]))
 
class _linewidth(unit.length):
    def __init__(self, l):
        unit.length.__init__(self, l=l, default_type="w")
    def _PSCmd(self, canvas):
        return "%f setlinewidth" % canvas.unit.pt(self)
    

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

class canvas:

    def __init__(self, *args, **kwargs):
        
        self.PSCmds = []
        self.unit   = kwargs.get("unit", unit.unit())

        for arg in args:
            self.set(*args)
    
    def __str__(self):
        return reduce(lambda x,y: x + "\n%s" % str(y), self.PSCmds, "")

    def _write(self, file):
        for cmd in self.PSCmds:
           file.write(str(cmd) + "\n")

    def _PSAddCmd(self, cmd):
        self.PSCmds.append(cmd)

    def _newpath(self):
    	self._PSAddCmd("newpath")

    def _stroke(self):
    	self._PSAddCmd("stroke")

    def _fill(self):
    	self._PSAddCmd("fill")

    def _gsave(self):
        self._PSAddCmd("gsave")
	
    def _grestore(self):
        self._PSAddCmd("grestore")

    def _translate(self, x, y):
        self._PSAddCmd("%f %f translate" % self.unit.pt((x, y)))
        
    def create(self, pyxclass, *args, **kwargs):
        instance = pyxclass(unit = self.unit.copy(), *args, **kwargs)
        return instance

    def stick(self, instance):
        self._gsave() # we need this at the moment for subcanvas, but it should be avoided here!
        self._PSAddCmd(instance)
        self._grestore()
        return self
        
    def insert(self, pyxclass, *args, **kwargs):
        instance = self.create(pyxclass, *args, **kwargs)
        self.stick(instance)
        return instance

    def set(self, *args):
        for arg in args: 
           self._PSAddCmd(arg._PSCmd(self))
	
    def draw(self, path, *args):
        if args: 
           self._gsave()
           self.set(*args)
        self._newpath()
        path.draw(self)
	self._stroke()
        if args:
           self._grestore()
        return self
	
    def fill(self, path, *args):
        if args: 
           self._gsave()
           self.set(*args)
        self._newpath()
        path.draw(self)
	self._fill()
        if args:
           self._grestore()
        return self

    def write(self, filename, width, height, **kwargs):
        try:
  	    file = open(filename + ".eps", "w")
	except IOError:
	    assert "cannot open output file"		        # TODO: Fehlerbehandlung...

        file.write("%!PS-Adobe-3.0 EPSF 3.0\n")
        file.write("%%%%BoundingBox: 0 0 %d %d\n" % (1000,1000))  # TODO: richtige Boundingbox!
        file.write("%%Creator: pyx 0.0.1\n") 
        file.write("%%%%Title: %s.eps\n" % filename) 
        # file.write("%%CreationDate: %s" % ) 
        file.write("%%EndComments\n") 
        file.write("%%BeginProlog\n") 
        file.write(PSProlog)
        file.write("\n%%EndProlog\n") 
        file.write("%f setlinewidth\n" % self.unit.pt(linewidth.normal))
        self._write(file)
        file.write("\nshowpage\n")
        file.write("%%Trailer\n")
        file.write("%%EOF\n")

if __name__=="__main__":
    from tex   import *
    from path  import *
    from trafo import *
    from graph import *
    from color import *
    import unit

    c=canvas.canvas(unit=unit.unit())
    t=c.insert(tex)
 
    #for x in range(11):
    #    amove(x,0)
    #    rline(0,20)
    #for y in range(21):
    #   amove(0,y)
    #   rline(10,0)
 
    c.draw(path( [moveto(1,1), 
                  lineto(2,2), 
                  moveto(1,2), 
                  lineto(2,1) ] 
        	)
          )


    c.draw(line(1, 1, 1,2)) 
 
    print "Breite von 'Hello world!': ",t.textwd("Hello  world!")
    print "Höhe von 'Hello world!': ",t.textht("Hello world!")
    print "Höhe von 'Hello world!' in large: ",t.textht("Hello world!", fontsize.large)
    print "Höhe von 'Hello world!' in Large: ",t.textht("Hello world!", fontsize.Large)
    print "Höhe von 'Hello world' in huge: ",t.textht("Hello world!", fontsize.huge)
    print "Tiefe von 'Hello world!': ",t.textdp("Hello world!")
    print "Tiefe von 'was mit q': ",t.textdp("was mit q")
    print "Tiefe von 'was mit q': ",t.textdp("was mit q")
    t.text(5, 1, "Hello world!")
    t.text(5, 2, "Hello world!", halign.center)
    t.text(5, 3, "Hello world!", halign.right)
    for angle in (-90,-80,-70,-60,-50,-40,-30,-20,-10,0,10,20,30,40,50,60,70,80,90):
        t.text(11+angle/10, 5, str(angle), direction(angle))
        t.text(11+angle/10, 6, str(angle), direction(angle), halign.center)
        t.text(11+angle/10, 7, str(angle), direction(angle), halign.right)
    for pos in range(1,21):
        t.text(pos, 7.5, ".")
   
    p=path([ moveto(5,12), 
             lineto(7,12), 
             moveto(5,10), 
             lineto(5,14), 
             moveto(7,10), 
             lineto(7,14)])
   
    c.set(canvas.linestyle.dotted)
    t.text(5, 12, "a b c d e f g h i j k l m n o p q r s t u v w x y z", hsize("2 cm"))
    c.draw(p)
 
    p=path([ moveto(10,12), 
             lineto(12,12), 
             moveto(10,10), 
             lineto(10,14), 
             moveto(12,10), 
             lineto(12,14)])
    c.set(canvas.linestyle.dashdotted, rgb(1,0,0))
    t.text("10 cm", 12, "a b c d e f g h i j k l m n o p q r s t u v w x y z", hsize("2 cm"), valign.bottom, grey(0.5))
    c.draw(p)
 
    p=path([moveto(5,15), arc(5,15, 1, 0, 45), closepath()])
    c.fill(p, canvas.linestyle.dotted, canvas.linewidth.THICK)
 
    p=path([moveto(5,17), curveto(6,18, 5,16, 7,15)])
    c.draw(p, canvas.linestyle.dashed)

   
    for angle in range(20):
       s=c.insert(canvas.canvas,translate(10,10)*rotate(angle)).draw(p, canvas.linestyle.dashed, canvas.linewidth(0.01*angle), grey((20-angle)/20.0))
 
    c.set(linestyle.solid)
    g=GraphXY(c, t, 10, 15, 8, 6, y2=LinAxis())
    df = DataFile("testdata")
    g.plot(Data(df, x=2, y=3))
    g.plot(Data(df, x=2, y2=4))
    g.plot(Data(df, x=2, y=5))
    g.plot(Data(df, x=2, y=6))
    g.plot(Data(df, x=2, y=7))
    g.plot(Data(df, x=2, y=8))
    #g.plot(Function("0.01*sin(x)",Points=10000))
    g.plot(Function("0.01*sin(x)"))
    g.plot(Function("x=2*sin(1000*y)"))
    g.run()
    
    c.insert(canvas.canvas, scale(0.5, 0.4).rotate(10).translate("2 cm","200 mm")).insert(epsfile,"ratchet_f.eps")
    c.insert(canvas.canvas, scale(0.2, 0.1).rotate(10).translate("6 cm","180 mm")).insert(epsfile,"ratchet_f.eps")
    
    c.draw(path([moveto("5 cm", "5 cm"), rlineto(0.1,0.1)]), linewidth.THICK)

    c.write("example", 21, 29.7)

