#!/usr/bin/env python

from const import *
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


class canvas:

    def __init__(self,width,height,basefilename):
        self.Width=width
        self.Height=height
        self.BaseFilename=basefilename
        self.PSInit()

    PSPositionCorrect = 0		# does actual PS position coincide with our x,y
    
    def __del__(self):
        print "canvas.__del__()"
    
    def PSCmd(self, cmd):
        try:
            self.PSFile.write("%s\n" % cmd)
	except IOError:
	    assert "cannot write to output file"	# TODO: Fehlerbehandlung...
	    
	
    def PSInit(self):
        try:
	    self.PSFile = open(self.BaseFilename + ".eps", "w")
	except IOError:
	    assert "cannot open output file"		# TODO: Fehlerbehandlung...
	
        self.PSFile.write("%!PS-Adobe-3.0 EPSF 3.0\n")
        self.PSFile.write("%%BoundingBox: 0 0 %d %d\n" % (1000,1000)) # TODO: richtige Boundingbox!
        self.PSFile.write("%%Creator: pyx 0.0.1\n") 
        self.PSFile.write("%%Title: %s.eps\n" % self.BaseFilename) 
        # self.PSFile.write("%%CreationDate: %s\n" % ) 
        self.PSFile.write("%%EndComments\n") 
        self.PSFile.write("%%BeginProlog\n") 

	# PostScript-procedure definitions
	# cf. file: 5002.EPSF_Spec_v3.0.pdf     
	self.PSCmd("""
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
} bind def""")
        self.PSFile.write("%%EndProlog\n") 
        
	self.PSCmd("0.2 setlinewidth")
	self.newpath()
	self.amove(0,0)

    def PSEnd(self):
    	self.stroke()
	self.PSFile.close()
	
    def PSGetEPSBoundingBox(self, epsname):
    
        'returns bounding box of EPS file epsname as 4-tuple (llx, lly, urx, ury)'
	
        try:
	    epsfile=open(epsname,"r")
	except:
	    assert "cannot open EPS file"	# TODO: Fehlerbehandlung

	import regex

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
	
    def PSInsertEPS(self, epsname):
    
        'Insert EPS file epsname at current position'
	
	(llx, lly, urx, ury) = self.PSGetEPSBoundingBox(epsname)
	
        try:
	    epsfile=open(epsname,"r")
	except:
	    assert "cannot open EPS file"	# TODO: Fehlerbehandlung

	self.PSCmd("BeginEPSF")
	self.PSCmd("%f %f translate" % (self.x, self.y)) 
	self.PSCmd("%f %f translate" % (-llx, -lly)) 
	self.PSCmd("%f %f %f %f rect" % (llx, lly, urx-llx,ury-lly)) 
	self.PSCmd("clip newpath")
	self.PSCmd("%%BeginDocument: %s" % epsname)
	self.PSCmd(epsfile.read())  	
	self.PSCmd("%%EndDocument")
	self.PSCmd("EndEPSF")

    def PScm2po(self, x, y=None): 
    
        'convert from cm to points'
	
        convfaktor=28.346456693
	
    	if y==None:
	    return convfaktor * x
	else:
	    return (convfaktor*x, convfaktor*y)

    def PSUpdatePosition(self):
        if self.PSPositionCorrect == 0:		# actual PS position doesn't coincide with our x,y
	    self.PSCmd("%f %f moveto" % self.PScm2po(self.x,self.y))
	    self.PSPositionCorrect = 1

    def stroke(self):
    	self.PSCmd("stroke")
	self.PSPositionCorrect = 0		# in fact, current point is undefined after stroke
	
    def newpath(self):
    	self.PSCmd("newpath")
	self.PSPositionCorrect = 0		# in fact, current point is undefined after newpath
	
    def closepath(self):
    	self.PSCmd("closepath")
	    
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
	self.PSCmd("%f %f lineto" % self.PScm2po(x,y))
    
    def rline(self,x,y):
        #isnumber(x)
        #isnumber(y)
	
	self.PSUpdatePosition()			# insert moveto if needed
        (self.x, self.y)=(self.x+x,self.y+y)
	self.PSCmd("%f %f rlineto" % self.PScm2po(x,y))

    def setlinecap(self, cap):
        #isnumber(cap)

	self.PSCmd("%d setlinecap" % cap)

    def setlinejoin(self, join):
        #isnumber(join)

	self.PSCmd("%d setlinejoin" % join)
	
    def setmiterlimit(self, limit):
        #isnumber(join)

	self.PSCmd("%f setmiterlimit" % limit)

    def setdash(self, pattern, offset=0):
    	patternstring=""
    	for element in pattern:
		patternstring=patternstring + `element` + " "
    	
    	self.PSCmd("[%s] %d setdash" % (patternstring, offset))

    def setlinestyle(self, style, offset=0):
        self.setlinecap(style[0])
	self.setdash   (style[1], offset)

if __name__=="__main__":
    c=canvas(21, 29.7, "example")

    from tex import *
    t=tex(c)
    t.c=c

    #for x in range(11):
    #    amove(x,0)
    #    rline(0,20)
    #for y in range(21):
    #   amove(0,y)
    #   rline(10,0)

    c.amove(1,1)
    c.aline(2,2)
    c.amove(1,2)
    c.aline(2,1)


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

    #DefaultTex.TexRun()
    #text("a b c d e f g h i j k l m n o p q r s t u v w x y z",hsize=2,valign=bottom)
