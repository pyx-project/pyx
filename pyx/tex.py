#!/usr/bin/env python

from globex import *
from const import *

# tex processor types

TeX="TeX"
LaTeX="LaTeX"

# tex size constants

tiny = "tiny"
scriptsize = "scriptsize"
footnotesize = "footnotesize"
small = "small"
normalsize = "normalsize"
large = "large"
Large = "Large"
LARGE = "LARGE"
huge = "huge"
Huge = "Huge"

# structure to store TexCmds

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

            # typically level 1 shows all interesting messages (errors,
            # overfull boxes etc.) and level 2 shows only error messages
            # level 1 is the default level

class TexException(Exception):
    pass

class TexLeftParenthesisError(TexException):
    def __str__(self):
        return "no matching parenthesis for '{' found"

class TexRightParenthesisError(TexException):
    def __str__(self):
        return "no matching parenthesis for '}' found"

class Tex(Globex):

    ExportMethods = [ "text", "textwd", "textht", "textdp" ]

    def __init__(self, canvas, type = "TeX", texinit = "", TexInitIgnoreMsgLevel = 1):
        if type != TeX or type != LaTeX:
            assert "unknown type"
        self.type = type
        self.canvas = canvas
        self.TexAddToFile(texinit,TexInitIgnoreMsgLevel)

    TexMarker = "ThisIsThePyxTexMarker"
    TexMarkerBegin = TexMarker + "Begin"
    TexMarkerEnd = TexMarker + "End"

    TexCmds = [ ]
        # stores the TexCmds; note that the first element has a special
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

        CmdBegin = "{\\vbox to0pt{\\kern" + str(self.canvas.Height - self.canvas.y) + "truecm\\hbox{\\kern" + str(self.canvas.x) + "truecm\\ht\\localbox0pt"
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

        import os, string

        file = open(self.canvas.BaseFilename + ".tex", "w")

        if self.type == TeX:
            file.write("""\\nonstopmode
\\hsize21truecm
\\vsize29.7truecm
\\hoffset-1truein
\\voffset-1truein\n""")

        if self.type == LaTeX:
            file.write("""\\nonstopmode
\\documentclass{article}
\\hsize21truecm
\\vsize29.7truecm
\\hoffset-1truein
\\voffset-1truein\n""")

        file.write(self.TexCmds[0].Cmd)

        if self.type == TeX:
            file.write("""\\newwrite\\sizefile
\\newbox\\localbox
\\newbox\\pagebox
\\immediate\\openout\\sizefile=""" + self.canvas.BaseFilename + """.size
\\setbox\\pagebox=\\vbox{%\n""")

        if self.type == LaTeX:
            file.write("""\\newwrite\\sizefile
\\newbox\\localbox
\\newbox\\pagebox
\\immediate\\openout\\sizefile=""" + self.canvas.BaseFilename + """.size
\\begin{document}
\\setbox\\pagebox=\\vbox{%\n""")

        for Cmd in self.TexCmds[1:]:
            file.write(Cmd.Cmd)

        if self.type == TeX:
            file.write("""}
\\immediate\\closeout\sizefile
\\shipout\\copy\\pagebox
\\end\n""")

        if self.type == LaTeX:
            file.write("""}
\\immediate\\closeout\sizefile
\\shipout\\copy\\pagebox
\\end{document}\n""")

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

        if os.system(string.lower(self.type) +" " + self.canvas.BaseFilename + " > " + self.canvas.BaseFilename + ".stdout 2> " + self.canvas.BaseFilename + ".stderr"):
            print "The " + self.type + " exit code was non-zero. This may happen due to mistakes within your\nLaTeX commands as listed below. Otherwise you have to check your local\nenvironment and the files \"" + self.canvas.BaseFilename + ".tex\" and \"" + self.canvas.BaseFilename + ".log\" manually."

        try:
            # check output
            file = open(self.canvas.BaseFilename + ".stdout", "r")
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
            print "Error reading the " + self.type + " output. Check your local environment and the files\n\"" + self.canvas.BaseFilename + ".tex\" and \"" + self.canvas.BaseFilename + ".log\"."
            raise
        
        # TODO: ordentliche Fehlerbehandlung,
        #       Schnittstelle zur Kommandozeile
        if os.system("dvips -P pyx -T" + str(self.canvas.Width) + "cm," + str(self.canvas.Height) + "cm -o " + self.canvas.BaseFilename + ".tex.eps " + self.canvas.BaseFilename + " > /dev/null 2>&1"):
            assert "dvips exit code non-zero"
        
    TexResults = None

    def TexResult(self, Str):
 
        'get sizes from previous LaTeX run'

        if self.TexResults == None:
            try:
                file = open(self.canvas.BaseFilename + ".size", "r")
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


def tex(texinit = "", TexInitIgnoreMsgLevel = 1):
    exec "canvas=DefaultCanvas" in GetCallerGlobalNamespace(),locals()
    DefaultTex=Tex(canvas, TeX, texinit, TexInitIgnoreMsgLevel)
    DefaultTex.AddNamespace("DefaultTex", GetCallerGlobalNamespace())

def latex(texinit = "", TexInitIgnoreMsgLevel = 1):
    exec "canvas=DefaultCanvas" in GetCallerGlobalNamespace(),locals()
    DefaultTex=Tex(canvas, LaTeX, texinit, TexInitIgnoreMsgLevel)
    DefaultTex.AddNamespace("DefaultTex", GetCallerGlobalNamespace())

