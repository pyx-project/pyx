#!/usr/bin/env python

# TODO:
# - think a little bit more about abstractcanvas, canvas, and subcanvas

# current issues:
#  - __del__ is not necessarily run immediately (we had this problem before), so that some important 
#    cleanup of the canvas (grestore!) maybe doesn't happen at the right moment!
#  - how to deal with the units? How do transformation classes no of them? Should u2p & friends
#    be moved to another place?


from const import *
from unit import unit
import string

linecap_butt   = 0
linecap_round  = 1
linecap_square = 2

linejoin_miter = 0
linejoin_round = 1
linejoin_bevel = 2

linestyle_solid      = (linecap_butt,  [])
linestyle_dashed     = (linecap_butt,  [2])
linestyle_dotted     = (linecap_round, [0, 3])
linestyle_dashdotted = (linecap_round, [0, 3, 3, 3])

# PostScript-procedure definitions
# cf. file: 5002.EPSF_Spec_v3.0.pdf     

PSProlog = """
/rect {
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

class epsfile:
    epsname           = ""
    (llx,lly,urx,ury) = (0,0,0,0)

    def __init__(self, epsname):
        self.epsname = epsname
        self._ReadEPSBoundBox()                         

    def _ReadEPSBoundingBox(self):
        'determines bounding box of EPS file epsname as 4-tuple (llx, lly, urx, ury)'
        try:
            epsfile=open(epsname,"r")
        except:
            assert "cannot open EPS file"	# TODO: Fehlerbehandlung

        import re

        bbpattern = re.compile( r"^%%BoundingBox:\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$" )

        while 1:
            line=epsfile.readline()
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
        epsfile.close()

    def __string__(self):
        try:
	    epsfile=open(epsname,"r")
	except:
	    assert "cannot open EPS file"	                          # TODO: Fehlerbehandlung

	       # "%f %f translate\n" % (x, y) +                             # we are already at this position
	return """BeginEPSF
	       %f %f translate 
	       %f %f %f %f rect
	       clip newpath
	       %%BeginDocument: %s""" % (-self.llx, -self.lly, 
                                         self.llx, self.lly, self.urx-self.llx,self.ury-self.lly, 
                                         self.epsname) + epsfile.read() + "%%EndDocument\nEndEPSF\n"

#
# Exceptions
#
    
class CanvasException(Exception): pass

#
# classes
#

class canvas(unit):

    PSCmds = []

    def __init__(self, **kwargs):
        from trafo import transformation
        
        self.trafo = kwargs.get("trafo", transformation())
        self.unit = kwargs.get("units", unit())
        
        self._PSAddCmd("%f %f scale" % (1/unit_ps, 1/unit_ps))
        self._PSAddCmd("[" + `self.trafo` + " ] concat")
    
    def __string__(self):
        return reduce(lambda x,y: x + ("%s\n" % y), PSCmds)

    def _PSAddCmd(self, cmd):
        self.PSCmds.append(cmd);

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
        self._PSAddCmd("%f %f translate" % (x, y))
        
    def canvas(self, **kwargs):
        subcanvas = canvas(**kwargs)
        self._gsave()
        self._PSAddCmd(subcanvas)
        self._grestore()
        return subcanvas
        
    def tex(self, **kwargs):
        texcanvas = tex(self, **kwargs)
        self._translate(0,0)
        self._PSAddCmd(texcanvas)
        return texcanvas
	
    def draw(self, path):
        self._newpath()
        path.draw(self)
	self._stroke()
        return self
	
    def fill(self, path):
        self._newpath()
        path.fill(self)
	self._fill()
        return self

    def setlinecap(self, cap):
	self._PSAddCmd("%d setlinecap" % cap)
        return self

    def setlinejoin(self, join):
	self._PSAddCmd("%d setlinejoin" % join)
        return self
	
    def setmiterlimit(self, limit):
	self._PSAddCmd("%f setmiterlimit" % limit)
        return self

    def setdash(self, pattern, offset=0):
    	patternstring=""
    	for element in pattern:
		patternstring=patternstring + `element` + " "
    	
    	self._PSAddCmd("[%s] %d setdash" % (patternstring, offset))
        return self

    def setlinestyle(self, style, offset=0):
        self.setlinecap(style[0])
	self.setdash   (style[1], offset)
        return self

        
    def write(self, filename, width, height, **kwargs):
        try:
  	    self.file = open(self.filename + ".eps", "w")
	except IOError:
	    assert "cannot open output file"		        # TODO: Fehlerbehandlung...

        file.write("%!PS-Adobe-3.0 EPSF 3.0\n")
        file.write("%%BoundingBox: 0 0 %d %d\n" % (1000,1000))  # TODO: richtige Boundingbox!
        file.write("%%Creator: pyx 0.0.1\n") 
        file.write("%%Title: %s.eps\n" % self.BaseFilename) 
        # file.write("%%CreationDate: %s" % ) 
        file.write("%%EndComments\n") 
        file.write("%%BeginProlog\n") 
        file.write(PSProlog)
        file.write("%%EndProlog\n") 
        file.write("%f setlinewidth\n" % self.w2p(0.02))	# TODO: fixme
        file.write(self)


if __name__=="__main__":
    c=canvas()

    from tex import *
    from path import *
    from trafo import *
    from graph import *

    t=c.tex()

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
    print "Höhe von 'Hello world!' in large: ",t.textht("Hello world!", size = large)
    print "Höhe von 'Hello world!' in Large: ",t.textht("Hello world!", size = Large)
    print "Höhe von 'Hello world' in huge: ",t.textht("Hello world!", size = huge)
    print "Tiefe von 'Hello world!': ",t.textdp("Hello world!")
    print "Tiefe von 'was mit q': ",t.textdp("was mit q")
    t.text(5, 1, "Hello world!")
    t.text(5, 2, "Hello world!", halign = center)
    t.text(5, 3, "Hello world!", halign = right)
    for angle in (-90,-80,-70,-60,-50,-40,-30,-20,-10,0,10,20,30,40,50,60,70,80,90):
        t.text(11+angle/10, 5, str(angle), angle = angle)
	t.text(11+angle/10, 6, str(angle), angle = angle, halign = center)
	t.text(11+angle/10, 7, str(angle), angle=angle, halign=right)
    for pos in range(1,21):
        t.text(pos, 7.5, ".")
   
    p=path([ moveto(5,12), 
             lineto(7,12), 
	     moveto(5,10), 
	     lineto(5,14), 
	     moveto(7,10), 
	     lineto(7,14)])
   
    c.setlinestyle(linestyle_dotted)
    t.text(5, 12, "a b c d e f g h i j k l m n o p q r s t u v w x y z", hsize = 2)
    c.draw(p)

    p=path([ moveto(10,12), 
             lineto(12,12), 
	     moveto(10,10), 
	     lineto(10,14), 
	     moveto(12,10), 
	     lineto(12,14)])
    c.setlinestyle(linestyle_dashdotted)
    t.text(10, 12, "a b c d e f g h i j k l m n o p q r s t u v w x y z", hsize = 2, valign = bottom)
    c.draw(p)

    p=path([moveto(5,15), arc(5,15, 1, 0, 45), closepath()])
    c.draw(p)

    p=path([moveto(5,17), curveto(6,18, 5,16, 7,15)])
    c.draw(p)
    
    for angle in range(20):
       c.subcanvas(trafo=translate(10,10)*rotate(angle)).draw(p)

    c.setlinestyle(linestyle_solid)
    g=GraphXY(c, t, 10, 15, 8, 6)
    g.plot(Function("5*sin(x)"))
    g.plot(Function("(x+5)*x*(x-5)/100"))
    g.run()

    c=write("example", 21, 29.7)
