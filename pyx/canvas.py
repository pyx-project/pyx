#!/usr/bin/env python

from const import *
import string
import regex

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

unit_ps		= 1.0

unit_u2p	= 28.346456693*unit_ps
unit_v2p	= 28.346456693*unit_ps
unit_w2p	= 28.346456693*unit_ps

class canvas:

    PSCmds = [] 				# stores all PS commands of the canvas

    isCanvas = 1				# identifies a canvas
    
    PSPositionCorrect = 0			# does actual PS position coincide with our x,y
    
    def __init__(self, base, width, height ):
        self.Width=width
        self.Height=height
	if type(base)==type(""):
	    self.BaseFilename = base
	    self.isPrimaryCanvas = 1
	else: 
#	    try: 
	    	if base.isCanvas: self.isPrimaryCanvas = 0
#	    except:
#	        assert("base should be either a filename or a canvas")
        self.PSInit()

    
    def __del__(self):
        self.PSRun()
    
    def PSAddCmd(self, cmd):
        self.PSCmds = self.PSCmds + [ cmd ]
	
    def PSInit(self):
    	if self.isPrimaryCanvas:
           self.PSAddCmd("%!PS-Adobe-3.0 EPSF 3.0")
           self.PSAddCmd("%%BoundingBox: 0 0 %d %d" % (1000,1000)) # TODO: richtige Boundingbox!
           self.PSAddCmd("%%Creator: pyx 0.0.1") 
           self.PSAddCmd("%%Title: %s.eps" % self.BaseFilename) 
           # self.PSAddCmd("%%CreationDate: %s" % ) 
           self.PSAddCmd("%%EndComments") 
           self.PSAddCmd("%%BeginProlog") 
	   self.PSAddCmd(PSProlog)
           self.PSAddCmd("%%EndProlog") 

	   
        self.gsave()						# encapsulate canvas
	self.PSAddCmd("%f %f scale" % (1/unit_ps, 1/unit_ps))
        self.PSAddCmd("%f setlinewidth" % self.w2p(0.02))	# TODO: fixme
	self.newpath()						# delete eventually
	self.amove(0,0)						#       ""

    def PSRun(self):
    	self.stroke()						# delete eventually
	self.grestore()						# canvas has been encapsulated
	
	if self.isPrimaryCanvas:
           try:
  	      PSFile = open(self.BaseFilename + ".eps", "w")
	   except IOError:
	      assert "cannot open output file"		# TODO: Fehlerbehandlung...
  	   for cmd in self.PSCmds:
	      PSFile.write("%s\n" % cmd)
	   PSFile.close()
        else:
  	   for cmd in self.PSCmds:			# maybe, we should be more efficient here
	      self.base.PSAddCmd(cmd)
	      
    def PSGetEPSBoundingBox(self, epsname):
    
        'returns bounding box of EPS file epsname as 4-tuple (llx, lly, urx, ury)'
	
        try:
	    epsfile=open(epsname,"r")
	except:
	    assert "cannot open EPS file"	# TODO: Fehlerbehandlung

#        import regex

	bbpattern = regex.compile(
	     "^%%BoundingBox:[\t ]+\([0-9]+\)[\t ]+\([0-9]+\)[\t ]+\([0-9]+\)[\t ]+\([0-9]+\)[\t ]*$")

	while 1:
	    line=epsfile.readline()
	    if not line:
	        assert "bounding box not found in EPS file"
		raise IOError			# TODO: Fehlerbehandlung
	    if line=="%%EndComments\n": 
		# TODO: BoundingBox-Deklaration kann auch an Ende von Datei verschoben worden sein
	        assert "bounding box not found in EPS file"
		raise IOError			# TODO: Fehlerbehandlung
	    if bbpattern.match(line)>0:
	        (llx, lly, urx, ury) = map(eval,(bbpattern.group(1), bbpattern.group(2), bbpattern.group(3), bbpattern.group(4)))
		break
        epsfile.close()
	return (llx, lly, urx, ury)

    def u2p(self, lengths):
    	if isnumber(lengths): 
	    return lengths*unit_u2p
	else: 
	    return tuple(map(lambda x:x*unit_u2p, lengths))
	
    def v2p(self, lengths):
    	if isnumber(lengths): 
	    return lengths*unit_v2p
	else: 
	    return tuple(map(lambda x:x*unit_v2p, lengths))
	
    def w2p(self, lengths):
    	if type(lengths)==type(0.0): 
	    return lengths*unit_w2p
	else: 
	    return tuple(map(lambda x:x*unit_w2p, lengths))
	
    def PSInsertEPS(self, epsname):
    
        'Insert EPS file epsname at current position'
	
	(llx, lly, urx, ury) = self.PSGetEPSBoundingBox(epsname)
	
        try:
	    epsfile=open(epsname,"r")
	except:
	    assert "cannot open EPS file"	# TODO: Fehlerbehandlung

	self.PSAddCmd("BeginEPSF")
	self.PSAddCmd("%f %f translate" % self.u2p((self.x, self.y)) ) 
	self.PSAddCmd("%f %f translate" % self.u2p((-llx, -lly)) )
	self.PSAddCmd("%f %f %f %f rect" % self.u2p((llx, lly, urx-llx,ury-lly)))
	self.PSAddCmd("clip newpath")
	self.PSAddCmd("%%BeginDocument: %s" % epsname)
	self.PSAddCmd(epsfile.read())  	
	self.PSAddCmd("%%EndDocument")
	self.PSAddCmd("EndEPSF")


    def PSUpdatePosition(self):
        if self.PSPositionCorrect == 0:		# actual PS position doesn't coincide with our x,y
	    self.PSAddCmd("%f %f moveto" % self.u2p((self.x,self.y)))
	    self.PSPositionCorrect = 1

    def stroke(self):
    	self.PSAddCmd("stroke")
	self.PSPositionCorrect = 0		# in fact, current point is undefined after stroke
	
    def newpath(self):
    	self.PSAddCmd("newpath")
	self.PSPositionCorrect = 0		# in fact, current point is undefined after newpath
	
    def closepath(self):
    	self.PSAddCmd("closepath")

    def draw(self,path):
        path.draw(self)

    def amove(self,x,y):
        #isnumber(x)
        #isnumber(y)
	
        (self.x, self.y)=(x,y)
	self.PSPositionCorrect = 0 			 
	
    def rmove(self,x,y):
        #isnumber(x)
        #isnumber(y)
	
        (self.x, self.y)=(self.x+x,self.y+y)
	self.PSPositionCorrect = 0 			 
	
    def aline(self,x,y):
        #isnumber(x)
        #isnumber(y)
	
	self.PSUpdatePosition()			# insert moveto if needed
        (self.x, self.y)=(x,y)
	self.PSAddCmd("%f %f lineto" % self.u2p((x,y)))
    
    def rline(self,x,y):
        #isnumber(x)
        #isnumber(y)
	
	self.PSUpdatePosition()			# insert moveto if needed
        (self.x, self.y)=(self.x+x,self.y+y)
	self.PSAddCmd("%f %f rlineto" % self.u2p((x,y)))

    def setlinecap(self, cap):
        #isnumber(cap)

	self.PSAddCmd("%d setlinecap" % cap)

    def setlinejoin(self, join):
        #isnumber(join)

	self.PSAddCmd("%d setlinejoin" % join)
	
    def setmiterlimit(self, limit):
        #isnumber(join)

	self.PSAddCmd("%f setmiterlimit" % limit)

    def setdash(self, pattern, offset=0):
    	patternstring=""
    	for element in pattern:
		patternstring=patternstring + `element` + " "
    	
    	self.PSAddCmd("[%s] %d setdash" % (patternstring, offset))

    def setlinestyle(self, style, offset=0):
        self.setlinecap(style[0])
	self.setdash   (style[1], offset)

    def gsave(self):
        self.PSAddCmd("gsave")
	
    def grestore(self):
        self.PSAddCmd("grestore")
    

if __name__=="__main__":
    c=canvas("example", 21, 29.7)

    from tex import *
    from path import *
    t=tex(c)
    #t.c=c

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

    #c.amove(1,1)
    #c.aline(2,2)
    #c.amove(1,2)
    #c.aline(2,1)


    print "Breite von 'Hello world!': ",t.textwd("Hello world!")
    print "Höhe von 'Hello world!': ",t.textht("Hello world!")
    print "Höhe von 'Hello world!' in large: ",t.textht("Hello world!", size = large)
    print "Höhe von 'Hello world!' in Large: ",t.textht("Hello world!", size = Large)
    print "Höhe von 'Hello world' in huge: ",t.textht("Hello world!", size = huge)
    print "Tiefe von 'Hello world!': ",t.textdp("Hello world!")
    print "Tiefe von 'was mit q': ",t.textdp("was mit q")
    c.amove(5,1)
    t.text("Hello world!")
    c.amove(5,2)
    t.text("Hello world!",halign=center)
    c.amove(5,3)
    t.text("Hello world!",halign=right)
    for angle in (-90,-80,-70,-60,-50,-40,-30,-20,-10,0,10,20,30,40,50,60,70,80,90):
        c.amove(11+angle/10,5)
        t.text(str(angle),angle=angle)
	c.amove(11+angle/10,6)
	t.text(str(angle),angle=angle,halign=center)
	c.amove(11+angle/10,7)
	t.text(str(angle),angle=angle,halign=right)
    for pos in range(1,21):
        c.amove(pos,7.5)
        t.text(".")
   
    c.stroke()
    c.setlinestyle(linestyle_dotted)
    c.amove(5,12)
    t.text("a b c d e f g h i j k l m n o p q r s t u v w x y z",hsize=2)
    c.aline(7,12)
    c.amove(5,10)
    c.aline(5,14)
    c.amove(7,10)
    c.aline(7,14)

    c.stroke()
    c.setlinestyle(linestyle_dashdotted)
    c.amove(10,12)
    t.text("a b c d e f g h i j k l m n o p q r s t u v w x y z",hsize=2,valign=bottom)
    c.aline(12,12)
    c.amove(10,10)
    c.aline(10,14)
    c.amove(12,10)
    c.aline(12,14)
    t.TexRun()

