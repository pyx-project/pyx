#!/usr/bin/env python

import canvas, os, string, tempfile, sys, md5, string, traceback, time, unit, math, types

class _halign:
    def __init__(self, value):
        self.value = value
    def __cmp__(self, other):
        return cmp(self.value, other.value)
    __rcmp__ = __cmp__

class halign:
    left   = _halign("left")
    center = _halign("center")
    right  = _halign("right")
   
class _valign:
    def __init__(self, value):
        self.value = value
    def __cmp__(self, other):
        return cmp(self.value, other.value)
    __rcmp__ = __cmp__

class valign:
    top    = _valign("top")
    bottom = _valign("bottom")

class _fontsize:
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return self.value

class fontsize:
    tiny         = _fontsize("tiny")
    scriptsize   = _fontsize("scriptsize")
    footnotesize = _fontsize("footnotesize")
    small        = _fontsize("small")
    normalsize   = _fontsize("normalsize")
    large        = _fontsize("large")
    Large        = _fontsize("Large")
    LARGE        = _fontsize("LARGE")
    huge         = _fontsize("huge")
    Huge         = _fontsize("Huge")

class _angle:
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return str(self.value)

class angle:
    horizontal = _angle(0)
    vertical   = _angle(90)
    upsidedown = _angle(180)
    rvertical  = _angle(270)
    def deg(self, value):
        return _angle(value)
    def rad(self, value):
        return _angle(value * 180 / math.pi)

class _msglevel:
    showall     = 0
    hideload    = 1
    hidewarning = 2
    hideall     = 3
    def __init__(self, value):
        self.value = value
    def __cmp__(self, other):
        return cmp(self.value, other.value)
    __rcmp__ = __cmp__

class msglevel:
    showall     = _msglevel(_msglevel.showall)     # ignore no messages (except empty "messages")
    hideload    = _msglevel(_msglevel.hideload)    # ignore only messages inside proper "()"
    hidewarning = _msglevel(_msglevel.hidewarning) # ignore all messages without a line starting with "! "
    hideall     = _msglevel(_msglevel.hideall)     # ignore all messages
    # typically "hideload" shows all interesting messages (errors,
    # overfull boxes etc.) and "hidewarning" shows only error messages
    # level 1 is the default level

class _mode:
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return str(self.value)
    def __cmp__(self, other):
        return cmp(other.value)
    def __rcmp__(self, other):
        return self.value.__rcmp__(other.value)

class mode:
    TeX = "TeX"
    LaTeX = "LaTeX"

# structure to store TexCmds

class TexCmdSaveStruc:
    def __init__(self, Cmd, MarkerBegin, MarkerEnd, Stack, msglevel):
        self.Cmd = Cmd
        self.MarkerBegin = MarkerBegin
        self.MarkerEnd = MarkerEnd
        self.Stack = Stack
        self.msglevel = msglevel
class TexException(Exception):
    pass

class TexLeftParenthesisError(TexException):
    def __str__(self):
        return "no matching parenthesis for '{' found"

class TexRightParenthesisError(TexException):
    def __str__(self):
        return "no matching parenthesis for '}' found"

class tex:

    def __init__(self, unit, type = mode.TeX, latexstyle = "10pt", latexclass = "article", latexclassopt = "", texinit = "", msglevel = msglevel.hideload):
        self.unit = unit
        assert type == mode.TeX or type == mode.LaTeX, "invalid type"
        if type == mode.TeX:
            # TODO 7: error handling lts-file not found
            # TODO 3: other ways creating font sizes?
            texinit = open("lts/" + latexstyle + ".lts", "r").read() + texinit
        self.type = type
        self.latexclass = latexclass
        self.latexclassopt = latexclassopt
        self.TexAddCmd(texinit, msglevel)

        if len(os.path.basename(sys.argv[0])):
            basename = os.path.basename(sys.argv[0])
            if basename[-3:] == ".py":
                basename = basename[:-3]
            self.SizeFileName = os.path.join(os.getcwd(), basename + ".size")
        else:
            self.SizeFileName = os.path.join(os.getcwd(), "pyxput.size")

    TexMarker = "ThisIsThePyxTexMarker"
    TexMarkerBegin = TexMarker + "Begin"
    TexMarkerEnd = TexMarker + "End"

    TexCmds = [ ]
        # stores the TexCmds; note that the first element has a special
        # meaning: it is the initial command "texinit", which is added by
        # the constructor (there has to be always a - may be empty - initial
        # command) -- the TexParenthesisCheck is automaticlly called in
        # TexAddCmd for this initial command

    def TexParenthesisCheck(self, Cmd):

        'check for proper usage of "{" and "}" in Cmd'

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

    def TexCreateBoxCmd(self, Cmd, size, hsize, lvalign):

        'creates the TeX box \\localbox containing Cmd'

        self.TexParenthesisCheck(Cmd)

        # we add another "{" to ensure, that everything goes into the Cmd
        Cmd = "{" + Cmd + "}"

        CmdBegin = "\\setbox\\localbox=\\hbox{\\" + str(size)
        CmdEnd = "}"

        if hsize != None:
             if type(lvalign) == types.NoneType or lvalign == valign.top:
                  CmdBegin = CmdBegin + "\\vtop{\hsize" + str(hsize) + "truecm{"
                  CmdEnd = "}}" + CmdEnd
             elif lvalign == valign.bottom:
                  CmdBegin = CmdBegin + "\\vbox{\hsize" + str(hsize) + "truecm{"
                  CmdEnd = "}}" + CmdEnd
             else:
                  assert 0, "valign unknown"
        else:
             assert lvalign == None, "hsize needed to use valign"
        
        Cmd = CmdBegin + Cmd + CmdEnd + "\n"
        return Cmd
    
    def TexCopyBoxCmd(self, x, y, Cmd, lhalign, angle):

        'creates the TeX commands to put \\localbox at the current position'

        # TODO 3: color support

        CmdBegin = "{\\vbox to0pt{\\kern" + str(self.unit.tpt(-y)) + "truept\\hbox{\\kern" + str(self.unit.tpt(x)) + "truept\\ht\\localbox0pt"
        CmdEnd = "}\\vss}\\nointerlineskip}"

        if angle != None and angle != 0:
            CmdBegin = CmdBegin + "\\special{ps:gsave currentpoint currentpoint translate " + str(angle) + " rotate neg exch neg exch translate}"
            CmdEnd = "\\special{ps:currentpoint grestore moveto}" + CmdEnd

        if type(lhalign) == types.NoneType or lhalign == halign.center:
            CmdBegin = CmdBegin + "\kern-.5\wd\localbox"
        elif lhalign == halign.right:
            CmdBegin = CmdBegin + "\kern-\wd\localbox"

        Cmd = CmdBegin + "\\copy\\localbox" + CmdEnd + "\n"
        return Cmd

    def TexHexMD5(self, Cmd):

        'creates an MD5 hex string for texinit + Cmd'
    
        h = string.hexdigits
        r = ''
        s = md5.md5(self.TexCmds[0].Cmd + Cmd).digest()
        for c in s:
            i = ord(c)
            r = r + h[(i >> 4) & 0xF] + h[i & 0xF]
        return r
        
    def TexAddCmd(self, Cmd, lmsglevel):

        'save Cmd to TexCmds, store "stack[2:]" for later error report'
        
        if self.TexCmds == [ ]:
            self.TexParenthesisCheck(Cmd)

        try:
            raise ZeroDivisionError
        except ZeroDivisionError:
            Stack = traceback.extract_stack(sys.exc_info()[2].tb_frame.f_back.f_back)

        MarkerBegin = self.TexMarkerBegin + " [" + str(len(self.TexCmds)) + "]"
        MarkerEnd = self.TexMarkerEnd + " [" + str(len(self.TexCmds)) + "]"

        Cmd = "\\immediate\\write16{" + MarkerBegin + "}\n" + Cmd + "\\immediate\\write16{" + MarkerEnd + "}\n"
        self.TexCmds = self.TexCmds + [ TexCmdSaveStruc(Cmd, MarkerBegin, MarkerEnd, Stack, lmsglevel), ]

    def __str__(self):

        'run LaTeX&dvips for TexCmds, report errors, return postscript string'
    
        # TODO 7: file handling
        #         Be sure to delete all temporary files (signal handling???)
        #         and check for the files before reading them (including the
        #         dvi before it is converted by dvips and the resulting ps)

        WorkDir = os.getcwd()
        MkTemp = tempfile.mktemp()
        TempDir = os.path.dirname(MkTemp)
        TempName = os.path.basename(MkTemp)
        os.chdir(TempDir)

        file = open(TempName + ".tex", "w")

        file.write("\\nonstopmode\n")
        if self.type == mode.LaTeX:
            file.write("\\documentclass[" + self.latexclassopt + "]{" + self.latexclass + "}\n")
        file.write("\\hsize0truecm\n\\vsize0truecm\n\\hoffset-1truein\n\\voffset0truein\n")

        file.write(self.TexCmds[0].Cmd)

        file.write("\\newwrite\\sizefile\n\\newbox\\localbox\n\\newbox\\pagebox\n\\immediate\\openout\\sizefile=" + TempName + ".size\n")
        if self.type == mode.LaTeX:
            file.write("\\begin{document}\n")
        file.write("\\setbox\\pagebox=\\vbox{%\n")

        for Cmd in self.TexCmds[1:]:
            file.write(Cmd.Cmd)

        file.write("}\n\\immediate\\closeout\\sizefile\n\\shipout\\copy\\pagebox\n")
        if self.type == mode.TeX:
            file.write("\\end\n")

        if self.type == mode.LaTeX:
            file.write("\\end{document}\n")
        file.close()

        if os.system(string.lower(self.type) + " " + TempName + ".tex > " + TempName + ".out 2> " + TempName + ".err"):
            print "The " + self.type + " exit code was non-zero. This may happen due to mistakes within your\nLaTeX commands as listed below. Otherwise you have to check your local\nenvironment and the files \"" + TempName + ".tex\" and \"" + TempName + ".log\" manually."

        try:
            # check output
            file = open(TempName + ".out", "r")
            for Cmd in self.TexCmds:

                # read markers and identify the message
                line = file.readline()
                if line == None:
                    raise IOError
                while line[:-1] != Cmd.MarkerBegin:
                    line = file.readline()
                    if line == None:
                        raise IOError
                msg = ""
                line = file.readline()
                if line == None:
                    raise IOError
                while line[:-1] != Cmd.MarkerEnd:
                    msg = msg + line
                    line = file.readline()
                    if line == None:
                        raise IOError

                # check if message can be ignored
                if Cmd.msglevel == msglevel.showall:
                    doprint = 0
                    for c in msg:
                        if c not in " \t\r\n":
                            doprint = 1
                elif Cmd.msglevel == msglevel.hideload:
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
                elif Cmd.msglevel == msglevel.hidewarning:
                    doprint = 0
                    # the "\n" + msg instead of msg itself is needed, if
                    # the message starts with "! "
                    if string.find("\n" + msg, "\n! ") != -1 or string.find(msg, "\r! ") != -1:
                        doprint = 1
                elif Cmd.msglevel == msglevel.hideall:
                    doprint = 0
                else:
                    print "Traceback (innermost last):"
                    traceback.print_list(Cmd.Stack)
                    assert 0, "msglevel unknown"

                # print the message if needed
                if doprint:
                    print "Traceback (innermost last):"
                    traceback.print_list(Cmd.Stack)
                    print "LaTeX Message:"
                    print msg
            file.close()

        except IOError:
            print "Error reading the " + self.type + " output. Check your local environment and the files\n\"" + TempName + ".tex\" and \"" + TempName + ".log\"."
            raise
        
        # TODO 7: dvips error handling
        #         interface for modification of the dvips command line

        if os.system("TEXCONFIG=" + WorkDir + " dvips -P pyx -T1in,1in -o " + TempName + ".eps " + TempName + ".dvi > /dev/null 2>&1"):
            assert 0, "dvips exit code non-zero"

        result = str(canvas.epsfile(TempName + ".eps", clipping = 0))

        # merge new sizes
        
        try:
            OldSizeFile = open(self.SizeFileName, "r")
            OldSizes = OldSizeFile.readlines()
            OldSizeFile.close()
            os.unlink(self.SizeFileName)
        except IOError:
            OldSizes = []

        NewSizeFile = open(TempName + ".size", "r")
        NewSizes = NewSizeFile.readlines()

        SizeFile = open(self.SizeFileName, "w")
        SizeFile.writelines(NewSizes)

        for OldSize in OldSizes:
            OldSizeSplit = OldSize.split(":")
            for NewSize in NewSizes:
                if NewSize.split(":")[0:2] == OldSizeSplit[0:2]:
                    break
            else:
                if time.time() < float(OldSizeSplit[2]) + 60*60*24:   # we keep it for one day
                    SizeFile.write(OldSize)

        os.unlink(TempName + ".tex")
        os.unlink(TempName + ".log")
        os.unlink(TempName + ".dvi")
        os.unlink(TempName + ".eps")
        os.unlink(TempName + ".out")
        os.unlink(TempName + ".err")
        os.unlink(TempName + ".size")
        
        os.chdir(WorkDir)
        
        return result

    TexResults = None

    def TexResult(self, Str):
 
        'get sizes from previous LaTeX run'

        if self.TexResults == None:
            try:
                file = open(self.SizeFileName, "r")
                self.TexResults = file.readlines()
                file.close()
            except IOError:
                self.TexResults = [ ]

        for TexResult in self.TexResults:
            if TexResult[:len(Str)] == Str:
                string.rstrip(TexResult.split(":")[3])
                return unit.unit().convert_to(string.rstrip(TexResult.split(":")[3]).replace("pt"," t tpt"))
 
        return 1

    def text(self, x, y, Cmd, size = fontsize.normalsize, halign = None, hsize = None, valign = None, angle = None, lmsglevel = msglevel.hideload):

        'print Cmd at (x, y)'
        
        TexCreateBoxCmd = self.TexCreateBoxCmd(Cmd, size, hsize, valign)
        TexCopyBoxCmd = self.TexCopyBoxCmd(x, y, Cmd, halign, angle)
        self.TexAddCmd(TexCreateBoxCmd + TexCopyBoxCmd, lmsglevel)

    def textwd(self, Cmd, size = fontsize.normalsize, hsize = None, lmsglevel = msglevel.hideload):
    
        'get width of Cmd'

        TexCreateBoxCmd = self.TexCreateBoxCmd(Cmd, size, hsize, None)
        TexHexMD5 = self.TexHexMD5(TexCreateBoxCmd)
        self.TexAddCmd(TexCreateBoxCmd +
                       "\\immediate\\write\\sizefile{" + TexHexMD5 +
                       ":wd:" + str(time.time()) + ":\\the\\wd\\localbox}\n", lmsglevel)
        return self.TexResult(TexHexMD5 + ":wd:")

    def textht(self, Cmd, size = fontsize.normalsize, hsize = None, valign = None, lmsglevel = msglevel.hideload):

        'get height of Cmd'

        TexCreateBoxCmd = self.TexCreateBoxCmd(Cmd, size, hsize, valign)
        TexHexMD5 = self.TexHexMD5(TexCreateBoxCmd)
        self.TexAddCmd(TexCreateBoxCmd +
                       "\\immediate\\write\\sizefile{" + TexHexMD5 +
                       ":ht:" + str(time.time()) + ":\\the\\ht\\localbox}\n", lmsglevel)
        return self.TexResult(TexHexMD5 + ":ht:")

    def textdp(self, Cmd, size = fontsize.normalsize, hsize = None, valign = None, lmsglevel = msglevel.hideload):
   
        'get depth of Cmd'

        TexCreateBoxCmd = self.TexCreateBoxCmd(Cmd, size, hsize, valign)
        TexHexMD5 = self.TexHexMD5(TexCreateBoxCmd)
        self.TexAddCmd(TexCreateBoxCmd +
                       "\\immediate\\write\\sizefile{" + TexHexMD5 +
                       ":dp:" + str(time.time()) + ":\\the\\dp\\localbox}\n", lmsglevel)
        return self.TexResult(TexHexMD5 + ":dp:")
