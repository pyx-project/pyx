#!/usr/bin/env python

from globex import *
from const import *

class TexCmdSaveStruc:
    def __init__(self, Cmd, MarkerBegin, MarkerEnd, Stack, IgnoreMsgLevel):
        self.Cmd = Cmd
        self.MarkerBegin = MarkerBegin
        self.MarkerEnd = MarkerEnd
        self.Stack = Stack
        self.IgnoreMsgLevel = IgnoreMsgLevel
            # 0 - ignore no messages (except empty "messages")
            # 1 - ignore messages inside proper "()"
            # 2 - ignore all messages without a line starting with "! "
            # 3 - ignore all messages

            # typically Level 1 shows all interesting messages (errors,
            # overfull boxes etc.) and Level 2 shows only error messages
            # Level 1 is the default Level

class TexException(Exception):
    pass

class TexLeftParenthesisError(TexException):
    def __str__(self):
        return "no matching parenthesis for '{' found"

class TexRightParenthesisError(TexException):
    def __str__(self):
        return "no matching parenthesis for '}' found"

class Canvas(Globex):

    ExportMethods = [ "amove", "aline", "rmove", "rline", 
                      "text", "textwd", "textht", "textdp" ]

    def __init__(self,width,height,basefilename,texinit,TexInitIgnoreMsgLevel):
        self.Width=width
        self.Height=height
        self.BaseFilename=basefilename
        self.TexAddToFile(texinit,TexInitIgnoreMsgLevel)
        self.PSInit()

#
# TeX part
#

    TexMarker = "ThisIsThePyxTexMarker"
    TexMarkerBegin = TexMarker + "Begin"
    TexMarkerEnd = TexMarker + "End"

    TexCmds = [ ]
        # stores the TexCmds; note that the first element has a different
        # meaning: it is the initial command "texinit", which is added by
        # the constructor (there has to be always a - may be empty - initial
        # command) -- the TexParenthesisCheck is automaticlly called in
        # TexAddToFile for this initial command

    def TexParenthesisCheck(self, Cmd):

        'check for the proper usage of "{" and "}" in Cmd'

        depth = 0
        esc = 0
        for c in Cmd:
            if c == "{" and not esc:
                depth = depth + 1
            if c == "}" and not esc:
                depth = depth - 1
                if depth < 0:
                    raise TexRightParenthesisError
            if c == "\\":
                esc = (esc + 1) % 2
            else:
                esc = 0
        if depth > 0:
            raise TexLeftParenthesisError

    def TexCreateBoxCmd(self, Cmd, hsize, valign):

        'creates the TeX box \\localbox containing Cmd'

        self.TexParenthesisCheck(Cmd)

        # we add another "{" to ensure, that everything goes into the Cmd
        Cmd = "{" + Cmd + "}"

        CmdBegin = "\\setbox\\localbox=\\hbox{"
        CmdEnd = "}"

        if hsize != None:
             isnumber(hsize)
             if valign == top or valign == None:
                  CmdBegin = CmdBegin + "\\vtop{\hsize" + str(hsize) + "truecm{"
                  CmdEnd = "}}" + CmdEnd
             elif valign == bottom:
                  CmdBegin = CmdBegin + "\\vbox{\hsize" + str(hsize) + "truecm{"
                  CmdEnd = "}}" + CmdEnd
             else:
                  assert "valign unknown"
        else:
             if valign != None:
                  assert "hsize needed to use valign"
        
        Cmd = CmdBegin + Cmd + CmdEnd + "\n"
        return Cmd
    
    def TexCopyBoxCmd(self, Cmd, halign, angle):

        'creates the TeX commands to put \\localbox at the current position'

        # TODO (?): Farbunterstützung

        CmdBegin = "{\\vbox to0pt{\\kern" + str(self.Height - self.y) + "truecm\\hbox{\\kern" + str(self.x) + "truecm\\ht\\localbox0pt"
        CmdEnd = "}\\vss}\\nointerlineskip}"

        if angle != None and angle != 0:
            isnumber(angle)
            CmdBegin = CmdBegin + "\\special{ps:gsave currentpoint currentpoint translate " + str(angle) + " rotate neg exch neg exch translate}"
            CmdEnd = "\\special{ps:currentpoint grestore moveto}" + CmdEnd

        if halign != None:
            if halign == left:
                pass
            elif halign == center:
                CmdBegin = CmdBegin + "\kern-.5\wd\localbox"
            elif halign == right:
                CmdBegin = CmdBegin + "\kern-\wd\localbox"
            else:
                assert "halign unknown"

        Cmd = CmdBegin + "\\copy\\localbox" + CmdEnd + "\n"
        return Cmd

    def TexHexMD5(self, Cmd):

        'creates an MD5 hex string for texinit + Cmd'
    
        import md5, string
        h = string.hexdigits
        r = ''
        s = md5.md5(self.TexCmds[0].Cmd + Cmd).digest()
        for c in s:
            i = ord(c)
            r = r + h[(i >> 4) & 0xF] + h[i & 0xF]
        return r
        
    def TexAddToFile(self, Cmd, IgnoreMsgLevel):

        'save Cmd to TexCmds, store "stack[2:]" for later error report'
        
        if self.TexCmds == [ ]:
            self.TexParenthesisCheck(Cmd)

        import sys,traceback
        try:
            raise ZeroDivisionError
        except ZeroDivisionError:
            Stack = traceback.extract_stack(sys.exc_info()[2].tb_frame.f_back.f_back)

        MarkerBegin = self.TexMarkerBegin + " [" + str(len(self.TexCmds)) + "]"
        MarkerEnd = self.TexMarkerEnd + " [" + str(len(self.TexCmds)) + "]"

        Cmd = "\\immediate\\write16{" + MarkerBegin + "}\n" + Cmd + "\\immediate\\write16{" + MarkerEnd + "}\n"
        self.TexCmds = self.TexCmds + [ TexCmdSaveStruc(Cmd, MarkerBegin, MarkerEnd, Stack, IgnoreMsgLevel), ]

    def TexRun(self):

        'run LaTeX&dvips for TexCmds, add postscript to canvas, report errors'
    
        # TODO: clean file handling. Be sure to delete all temporary files (signal handling???) and check for the files before reading them (including the dvi-file before it's converted by dvips)

        import os

        file = open(self.BaseFilename + ".tex", "w")

        file.write("""\\nonstopmode
\\hsize21truecm
\\vsize29.7truecm
\\hoffset-1truein
\\voffset-1truein\n""")

        file.write(self.TexCmds[0].Cmd)

        file.write("""\\newwrite\\sizefile
\\newbox\\localbox
\\newbox\\pagebox
\\immediate\\openout\\sizefile=""" + self.BaseFilename + """.size
\\setbox\\pagebox=\\vbox{""")

        for Cmd in self.TexCmds[1:]:
            file.write(Cmd.Cmd)

        file.write("""}
\\immediate\\closeout\sizefile
\\shipout\\copy\\pagebox
\\end""")
#%\\setlength{\\unitlength}{1truecm}
#%\\begin{picture}(0,""" + str(self.Height) + """)(0,0)
#%\\put(0,0){\line(1,1){1}}
#%\\put(2,2){\line(1,1){1}}
#%\\put(0,3){\line(1,-1){1}}
#%\\put(2,1){\line(1,-1){1}}
#%\\multiput(0,0)(1,0){11}{\line(0,1){20}}
#%\\multiput(0,0)(0,1){21}{\line(1,0){10}}
#%\\end{picture}%
        file.close()

        if os.system("tex " + self.BaseFilename + " > " + self.BaseFilename + ".stdout 2> " + self.BaseFilename + ".stderr"):
            print "The LaTeX exit code was non-zero. This may happen due to mistakes within your\nLaTeX commands as listed below. Otherwise you have to check your local\nenvironment and the files \"" + self.BaseFilename + ".tex\" and \"" + self.BaseFilename + ".log\" manually."

        try:
            # check LaTeX output
            file = open(self.BaseFilename + ".stdout", "r")
            for Cmd in self.TexCmds:
            # TODO: readline blocks if eof is reached, but we want an exception

                # read markers and identify the message
                line = file.readline()
                while line[:-1] != Cmd.MarkerBegin:
                    line = file.readline()
                msg = ""
                line = file.readline()
                while line[:-1] != Cmd.MarkerEnd:
                    msg = msg + line
                    line = file.readline()

                # check if message can be ignored
                if Cmd.IgnoreMsgLevel == 0:
                    doprint = 0
                    for c in msg:
                        if c not in " \t\r\n":
                            doprint = 1
                elif Cmd.IgnoreMsgLevel == 1:
                    depth = 0
                    doprint = 0
                    for c in msg:
                        if c == "(":
                            depth = depth + 1
                        elif c == ")":
                            depth = depth - 1
                            if depth < 0:
                                doprint = 1
                        elif depth == 0 and c not in " \t\r\n":
                            doprint = 1
                elif Cmd.IgnoreMsgLevel == 2:
                    doprint = 0
                    import string
                    # the "\n" + msg instead of msg itself is needed, if
                    # the message starts with "! "
                    if string.find("\n" + msg, "\n! ") != -1 or string.find(msg, "\r! ") != -1:
                        doprint = 1
                elif Cmd.IgnoreMsgLevel == 3:
                    doprint = 0
                else:
                    print "Traceback (innermost last):"
                    traceback.print_list(Cmd.Stack)
                    assert "IgnoreMsgLevel not in range(4)"

                # print the message if needed
                if doprint:
                    import traceback
                    print "Traceback (innermost last):"
                    traceback.print_list(Cmd.Stack)
                    print "LaTeX Message:"
                    print msg
            file.close()

        except IOError:
            print "Error reading the LaTeX output. Check your local environment and the files\n\"" + self.BaseFilename + ".tex\" and \"" + self.BaseFilename + ".log\"."
            raise
        
        # TODO: ordentliche Fehlerbehandlung,
        #       Schnittstelle zur Kommandozeile
        if os.system("dvips -P pyx -T" + str(self.Width) + "cm," + str(self.Height) + "cm -o " + self.BaseFilename + ".tex.eps " + self.BaseFilename + " > /dev/null 2>&1"):
            assert "dvips exit code non-zero"
        
    TexResults = None

    def TexResult(self, Str):
 
        'get sizes from previous LaTeX run'

        if self.TexResults == None:
            try:
                file = open(self.BaseFilename + ".size", "r")
                self.TexResults = file.readlines()
                file.close()
            except IOError:
                self.TexResults = [ ]

        for TexResult in self.TexResults:
            if TexResult[:len(Str)] == Str:
                return TexResult[len(Str):-1]
 
        return 1

    def text(self, Cmd, halign = None, hsize = None, valign = None, angle = None, IgnoreMsgLevel = 1):

        'print Cmd at the current position'
        
        TexCreateBoxCmd = self.TexCreateBoxCmd(Cmd, hsize, valign)
        TexCopyBoxCmd = self.TexCopyBoxCmd(Cmd, halign, angle)
        self.TexAddToFile(TexCreateBoxCmd + TexCopyBoxCmd, IgnoreMsgLevel)

    def textwd(self, Cmd, hsize = None, IgnoreMsgLevel = 1):
    
        'get width of Cmd'

        TexCreateBoxCmd = self.TexCreateBoxCmd(Cmd, hsize, None)
        TexHexMD5=self.TexHexMD5(TexCreateBoxCmd)
        self.TexAddToFile(TexCreateBoxCmd +
                          "\\immediate\\write\\sizefile{" + TexHexMD5 +
                          ":wd:\\the\\wd\\localbox}\n", IgnoreMsgLevel)
        return self.TexResult(TexHexMD5 + ":wd:")

    def textht(self, Cmd, hsize=None, valign=None, IgnoreMsgLevel = 1):

        'get height of Cmd'

        TexCreateBoxCmd = self.TexCreateBoxCmd(Cmd, hsize, valign)
        TexHexMD5=self.TexHexMD5(TexCreateBoxCmd)
        self.TexAddToFile(TexCreateBoxCmd +
                          "\\immediate\\write\\sizefile{" + TexHexMD5 +
                          ":ht:\\the\\ht\\localbox}\n", IgnoreMsgLevel)
        return self.TexResult(TexHexMD5 + ":ht:")

    def textdp(self, Cmd, hsize=None, valign=None, IgnoreMsgLevel = 1):
   
        'get depth of Cmd'

        TexCreateBoxCmd = self.TexCreateBoxCmd(Cmd, hsize, valign)
        TexHexMD5=self.TexHexMD5(TexCreateBoxCmd)
        self.TexAddToFile(TexCreateBoxCmd +
                          "\\immediate\\write\\sizefile{" + TexHexMD5 +
                          ":dp:\\the\\dp\\localbox}\n", IgnoreMsgLevel)
        return self.TexResult(TexHexMD5 + ":dp:")

#
# PS code
#

    PSPositionCorrect = 0		# does actual PS position coincide with our x,y
    
    def PSCmd(self, cmd):
        try:
            self.PSFile.write("%s\n" % cmd)
	except IOError:
	    assert "cannot write to output file"	# TODO: Fehlerbehandlung...
	    
	
    def PSInit(self):
        try:
	    self.PSFile = open(self.BaseFilename + ".ps", "w")
	except IOError:
	    assert "cannot open output file"		# TODO: Fehlerbehandlung...
	
        self.PSFile.write("%!\n")
        #self.PSFile.write("%%%%BoundingBox: 0 0 %d %d\n" % (self.Height*72, self.Width*72)) # TODO: das geht so nicht ...

	# PostScript-procedure definitions
	# cf. file: 5002.EPSF_Spec_v3.0.pdf     
	self.PSCmd("""
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
        
	self.PSCmd("0.02 setlinewidth")
	self.PSCmd("newpath")
	self.amove(0,0)

    def PSEnd(self):
    	self.PSCmd("stroke")
    	#self.PSFile.write("0 -508 translate\n")
	self.PSInsertEPS(self.BaseFilename + ".tex.eps")
	self.PSFile.close()
	
    def PSInsertEPS(self, epsname):
        try:
	    epsfile=open(epsname,"r")
	except:
	    assert "cannot open EPS file"	# TODO: Fehlerbehandlung

	self.PSCmd("BeginEPSF")
	self.PSCmd(epsfile.read())  	
	self.PSCmd("EndEPSF")

    def PScm2po(self, x, y=None): 
        # convfaktor=28.452756
        convfaktor=28.346456693
	
    	if y==None:
	    return convfaktor * x
	else:
	    return (convfaktor*x, convfaktor*y)

    def PSUpdatePosition(self):
        if self.PSPositionCorrect == 0:		# actual PS position doesn't coincide with our x,y
	    self.PSCmd("%f %f moveto" % self.PScm2po(self.x,self.y))
	    self.PSPositionCorrect = 1
	    
    def amove(self,x,y):
        isnumber(x)
        isnumber(y)
	
        (self.x, self.y)=(x,y)
	self.PSPositionCorrect = 0 			 
	
    def rmove(self,x,y):
        isnumber(x)
        isnumber(y)
	
        (self.x, self.y)=(self.x+x,self.y+y)
	self.PSPositionCorrect = 0 			 
	
    def aline(self,x,y):
        isnumber(x)
        isnumber(y)
	
	self.PSUpdatePosition()			# insert moveto if needed
        (self.x, self.y)=(x,y)
	self.PSCmd("%f %f lineto" % self.PScm2po(x,y))
    
    def rline(self,x,y):
        isnumber(x)
        isnumber(y)
	
	self.PSUpdatePosition()			# insert moveto if needed
        (self.x, self.y)=(self.x+x,self.y+y)
	self.PSCmd("%f %f rlineto" % self.PScm2po(x,y))


def canvas(width, height, basefilename, texinit="", TexInitIgnoreMsgLevel=1):
    DefaultCanvas=Canvas(width, height, basefilename, texinit, TexInitIgnoreMsgLevel)
    DefaultCanvas.AddNamespace("DefaultCanvas", GetCallerGlobalNamespace())


if __name__=="__main__":
    canvas(21, 29.7, "example")

    #for x in range(11):
    #    amove(x,0)
    #    rline(0,20)
    #for y in range(21):
    #   amove(0,y)
    #   rline(10,0)

    amove(1,1)
    aline(2,2)
    amove(1,2)
    aline(2,1)


    print "Breite von 'Hello world!': ",textwd("Hello world!")
    print "Höhe von 'Hello world!': ",textht("Hello world!")
    print "Tiefe von 'Hello world!': ",textdp("Hello world!")
    print "Tiefe von 'was mit q': ",textdp("was mit q")
    amove(5,1)
    text("Hello world!")
    amove(5,2)
    text("Hello world!",halign=center)
    amove(5,3)
    text("Hello world!",halign=right)
    for angle in (-90,-80,-70,-60,-50,-40,-30,-20,-10,0,10,20,30,40,50,60,70,80,90):
        amove(11+angle/10,5)
        text(str(angle),angle=angle)
	amove(11+angle/10,6)
	text(str(angle),angle=angle,halign=center)
	amove(11+angle/10,7)
	text(str(angle),angle=angle,halign=right)
    for pos in range(1,21):
        amove(pos,7.5)
        text(".")
        
    amove(5,12)
    text("a b c d e f g h i j k l m n o p q r s t u v w x y z",hsize=2)
    aline(7,12)
    amove(5,10)
    aline(5,14)
    amove(7,10)
    aline(7,14)

    amove(10,12)
    text("a b c d e f g h i j k l m n o p q r s t u v w x y z",hsize=2,valign=bottom)
    aline(12,12)
    amove(10,10)
    aline(10,14)
    amove(12,10)
    aline(12,14)

    #amove(5,20)
    #text("$\\left\\{\\displaystyle\\frac{1}{2}\\right\\}$")

    DefaultCanvas.TexRun()
    DefaultCanvas.PSEnd()
