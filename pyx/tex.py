#!/usr/bin/env python

import canvas, os, string, tempfile, sys, md5, string, traceback, time, unit, math, types, color

# TODO: AttribCmdValue, AttribStrValue(AttribCmpValue)

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
   
class hsize(unit.length):
    pass

_hsize = hsize
   
class _valign:
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return str(self.value)
    def __cmp__(self, other):
        return cmp(self.value, other.value)
    __rcmp__ = __cmp__

class valign:
    top    = _valign("vtop")
    bottom = _valign("vbox")

class _fontsize:
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return str(self.value)

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

class _direction:
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return str(self.value)

class direction(_direction):
    horizontal = _direction(0)
    vertical   = _direction(90)
    upsidedown = _direction(180)
    rvertical  = _direction(270)
    def __init__(self, value = 0):
        _direction.__init__(self, value)
    def deg(self, value):
        return _direction(value)
    def rad(self, value):
        return _direction(value * 180 / math.pi)

class _msglevel:
    def __init__(self, value):
        self.value = value
    def __cmp__(self, other):
        return cmp(self.value, other.value)
    __rcmp__ = __cmp__

class msglevel:
    #
    # this class defines levels for displaying TeX/LaTeX messages:
    # msglevel.showall    -- shows all messages
    # msglevel.hideload   -- ignores messages inside proper "()"
    # msglevel.hidewaring -- ignore all messages without a line starting with "! "
    # msglevel.hideall    -- ignore all messages
    #
    # typically msglevel.hideload shows all interesting messages (errors, overfull boxes etc.)
    # while msglevel.hidewarning shows only error messages
    #
    # msglevel.hideload is the default level
    #
    showall     = _msglevel(0)
    hideload    = _msglevel(1)
    hidewarning = _msglevel(2)
    hideall     = _msglevel(3)

class _mode:
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return str(self.value)
    def __cmp__(self, other):
        return cmp(other.value)
    __rcmp__ = __cmp__

class mode:
    TeX = "TeX"
    LaTeX = "LaTeX"

class _extent:
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return str(self.value)
    def __cmp__(self, other):
        return cmp(self.value, other.value)
    __rcmp__ = __cmp__

class extent:
    wd = _extent("wd")
    ht = _extent("ht")
    dp = _extent("dp")
   

class TexException(Exception):
    pass

class TexLeftParenthesisError(TexException):
    def __str__(self):
        return "no matching parenthesis for '{' found"

class TexRightParenthesisError(TexException):
    def __str__(self):
        return "no matching parenthesis for '}' found"

class TexCmd:

    PyxMarker = "PyxMarker"
    BeginPyxMarker = "Begin" + PyxMarker
    EndPyxMarker = "End" + PyxMarker

    def __init__(self, Marker, Stack, msglevel):
        self.Marker = Marker
        self.Stack = Stack
        self.msglevel = msglevel

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

    def BeginMarkerStr(self):
        return "%s[%s]" % (self.BeginPyxMarker, self.Marker, )
    
    def WriteBeginMarker(self, file):
        file.write("\\immediate\\write16{%s}%%\n" % self.BeginMarkerStr())

    def EndMarkerStr(self):
        return "%s[%s]" % (self.EndPyxMarker, self.Marker, )

    def WriteEndMarker(self, file):
        file.write("\\immediate\\write16{%s}%%\n" % self.EndMarkerStr())

    def CheckMarkerError(self, file):
        # read markers and identify the message
        line = file.readline()
        while line[:-1] != self.BeginMarkerStr():
            line = file.readline()
        msg = ""
        line = file.readline()
        while line[:-1] != self.EndMarkerStr():
            msg = msg + line
            line = file.readline()

        # check if message can be ignored
        if self.msglevel == msglevel.showall:
            doprint = 0
            for c in msg:
                if c not in " \t\r\n":
                    doprint = 1
        elif self.msglevel == msglevel.hideload:
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
        elif self.msglevel == msglevel.hidewarning:
            doprint = 0
            # the "\n" + msg instead of msg itself is needed, if
            # the message starts with "! "
            if string.find("\n" + msg, "\n! ") != -1 or string.find(msg, "\r! ") != -1:
                doprint = 1
        elif self.msglevel == msglevel.hideall:
            doprint = 0
        else:
            assert 0, "msglevel unknown"

        # print the message if needed
        if doprint:
            print "Traceback (innermost last):"
            traceback.print_list(self.Stack)
            print "(La)TeX Message:"
            print msg

class DefCmd(TexCmd):

    def __init__(self, DefCmd, Marker, Stack, msglevel):
        TexCmd.__init__(self, Marker, Stack, msglevel)
        self.TexParenthesisCheck(DefCmd)
        self.DefCmd = DefCmd

    def write(self, canvas, file):
        self.WriteBeginMarker(file)
        file.write(self.DefCmd)
        self.WriteEndMarker(file)

class CmdPut:

    def __init__(self, x, y, halign, direction, color):
        self.x = x
        self.y = y
        self.halign = halign
        self.direction = direction
        self.color = color

class BoxCmd(TexCmd):

    def __init__(self, DefCmdsStr, BoxCmd, fontsize, hsize, valign, Marker, Stack, msglevel):
        TexCmd.__init__(self, Marker, Stack, msglevel)
        self.TexParenthesisCheck(BoxCmd)
        self.DefCmdsStr = DefCmdsStr
        self.BoxCmd = "{%s}" % BoxCmd # add another "{" to ensure, that everything goes into the Box
        self.fontsize = fontsize
        self.hsize = hsize
        self.valign = valign
        self.CmdPuts = []
        self.CmdExtents = []

    def GetBoxCmd(self, canvas = None):
        # we're in trouble here:
        # we want to get extents of a BoxCmd, but we have no units
        # -> we don't evaluate the hsize for that case
        BoxCmd = self.BoxCmd
        if self.hsize:
            if canvas:
                hsize = str(canvas.unit.tpt(self.hsize))
            else:
                hsize = str(self.hsize)
            if self.valign:
                BoxCmd = "\\%s{\hsize%struept{%s}}" % (self.valign, hsize, BoxCmd, )
            else:
                BoxCmd = "\\%s{\hsize%struept{%s}}" % (valign.top, hsize, BoxCmd, )
        else:
            assert not self.valign, "hsize needed to use valign"
        return "\\setbox\\localbox=\\hbox{\\%s%s}%%\n" % (str(self.fontsize), BoxCmd, )

    def __cmp__(self, other):
        return cmp(self.GetBoxCmd(), other.GetBoxCmd())
    __rcmp__ = __cmp__

    def write(self, canvas, file):

        self.WriteBeginMarker(file)
        file.write(self.GetBoxCmd(canvas))
        self.WriteEndMarker(file)
        for CmdExtent in self.CmdExtents:
            file.write("\\immediate\\write\\sizefile{%s:%s:%s:\\the\\%s\\localbox}%%\n" % (self.MD5(), CmdExtent, time.time(), CmdExtent, ))
        for CmdPut in self.CmdPuts:

            # TODO: remove the ugly 11in!!!

            file.write("{\\vbox to0pt{\\kern" + str(11*72.27+canvas.unit.tpt(-CmdPut.y)) + "truept\\hbox{\\kern" + str(canvas.unit.tpt(CmdPut.x)) + "truept\\ht\\localbox0pt")

            if CmdPut.direction != direction.horizontal:
                file.write("\\special{ps: gsave currentpoint currentpoint translate " + str(CmdPut.direction) + " rotate neg exch neg exch translate }")
            if CmdPut.color != color.grey.black:
                file.write("\\special{ps: ")
                CmdPut.color.write(canvas, file)
                file.write(" }")
            if CmdPut.halign == halign.left:
                pass
            elif CmdPut.halign == halign.center:
                file.write("\kern-.5\wd\localbox")
            elif CmdPut.halign == halign.right:
                file.write("\kern-\wd\localbox")
            else:
                assert 0, "halign unknown"
            file.write("\\copy\\localbox")

            if CmdPut.color != color.grey.black:
                file.write("\\special{ps: ")
                color.grey.black.write(canvas, file)
                file.write(" }")
            if CmdPut.direction != direction.horizontal:
                file.write("\\special{ps: currentpoint grestore moveto }")
            file.write("}\\vss}\\nointerlineskip}%\n")

    def MD5(self):

        'creates an MD5 hex string for texinit + Cmd'
    
        h = string.hexdigits
        r = ''
        s = md5.md5(self.DefCmdsStr + self.GetBoxCmd()).digest()
        for c in s:
            i = ord(c)
            r = r + h[(i >> 4) & 0xF] + h[i & 0xF]
        return r

    def Put(self, x, y, halign, direction, color):
        self.CmdPuts.append(CmdPut(x, y, halign, direction, color))

    def Extent(self, extent, Sizes):

        'get sizes from previous LaTeX run'

        if extent not in self.CmdExtents:
            self.CmdExtents.append(extent)

        Str = self.MD5() + ":" + str(extent)
        for Size in Sizes:
            if Size[:len(Str)] == Str:
                string.rstrip(Size.split(":")[3])
                return unit.length(string.rstrip(Size.split(":")[3]).replace("pt"," t tpt"))
        return unit.length("10 t tpt")


class InstanceList:

    def AllowedInstances(self, Instances, AllowedClassesOnce, AllowedClassesMultiple = []):
        for i in range(len(Instances)):
            for j in range(len(AllowedClassesOnce)):
                if isinstance(Instances[i], AllowedClassesOnce[j]):
                    del AllowedClassesOnce[j]
                    break
            else:
                for j in range(len(AllowedClassesMultiple)):
                    if isinstance(Instances[i], AllowedClassesMultiple[j]):
                        break
                else:
                    assert 0, "instance not allowed"

    def ExtractInstance(self, Instances, Class, DefaultInstance = None):
        for Instance in Instances:
            if isinstance(Instance, Class):
                return Instance
        return DefaultInstance

    def ExtractInstances(self, Instances, Class, DefaultInstances = []):
        Result = []
        for Instance in Instances:
            if isinstance(Instance, Class):
                Result = Result + [ Instance, ]
        if len(Result) == 0:
            return DefaultInstance
        else:
            return Result


class tex(InstanceList):

    def __init__(self, type = mode.TeX, latexstyle = "10pt", latexclass = "article", latexclassopt = ""):
        self.type = type
        self.latexclass = latexclass
        self.latexclassopt = latexclassopt
        self.DefCmds = []
        self.DefCmdsStr = None
        self.BoxCmds = []

        if len(os.path.basename(sys.argv[0])):
            basename = os.path.basename(sys.argv[0])
            if basename[-3:] == ".py":
                basename = basename[:-3]
            self.SizeFileName = os.path.join(os.getcwd(), basename + ".size")
        else:
            self.SizeFileName = os.path.join(os.getcwd(), "pyxput.size")
        try:
            file = open(self.SizeFileName, "r")
            self.Sizes = file.readlines()
            file.close()
        except IOError:
            self.Sizes = [ ]

        if type == mode.TeX:
            # TODO 7: error handling lts-file not found
            # TODO 3: other ways for creating font sizes?
            self.define(open("lts/" + latexstyle + ".lts", "r").read())

    def GetStack(self):
        try:
            raise ZeroDivisionError
        except ZeroDivisionError:
            return traceback.extract_stack(sys.exc_info()[2].tb_frame.f_back.f_back)
    
    def bbox(self, acanvas):
	return canvas.bbox()

    def write(self, acanvas, file):

        'run LaTeX&dvips for TexCmds, report errors, return postscript string'
    
        # TODO 7: improve file handling
        #         Be sure to delete all temporary files (signal handling???)
        #         and check for the files before reading them (including the
        #         dvi before it is converted by dvips and the resulting ps)

        WorkDir = os.getcwd()
        MkTemp = tempfile.mktemp()
        TempDir = os.path.dirname(MkTemp)
        TempName = os.path.basename(MkTemp)
        os.chdir(TempDir)

        texfile = open(TempName + ".tex", "w")

        texfile.write("\\nonstopmode\n")
        if self.type == mode.LaTeX:
            texfile.write("\\documentclass[" + self.latexclassopt + "]{" + self.latexclass + "}\n")
        texfile.write("\\hsize0truein\n\\vsize0truein\n\\hoffset-1truein\n\\voffset-1truein\n")

        for Cmd in self.DefCmds:
            Cmd.write(acanvas, texfile)

        texfile.write("\\newwrite\\sizefile\n\\newbox\\localbox\n\\newbox\\pagebox\n\\immediate\\openout\\sizefile=" + TempName + ".size\n")
        if self.type == mode.LaTeX:
            texfile.write("\\begin{document}\n")
        texfile.write("\\setbox\\pagebox=\\vbox{%\n")

        for Cmd in self.BoxCmds:
            Cmd.write(acanvas, texfile)

        texfile.write("}\n\\immediate\\closeout\\sizefile\n\\shipout\\copy\\pagebox\n")
        if self.type == mode.TeX:
            texfile.write("\\end\n")

        if self.type == mode.LaTeX:
            texfile.write("\\end{document}\n")
        texfile.close()

        if os.system(string.lower(self.type) + " " + TempName + ".tex > " + TempName + ".out 2> " + TempName + ".err"):
            print "The " + self.type + " exit code was non-zero. This may happen due to mistakes within your\nLaTeX commands as listed below. Otherwise you have to check your local\nenvironment and the files \"" + TempName + ".tex\" and \"" + TempName + ".log\" manually."

        # TODO 7: what happens if *.out doesn't exists?
        outfile = open(TempName + ".out", "r")
        for Cmd in self.DefCmds + self.BoxCmds:
            Cmd.CheckMarkerError(outfile)
        outfile.close()
        
        # TODO 7: dvips error handling
        #         interface for modification of the dvips command line

        if os.system("dvips -E -o " + TempName + ".eps " + TempName + ".dvi > /dev/null 2>&1"):
            assert 0, "dvips exit code non-zero"

        canvas.epsfile(TempName + ".eps", translatebb = 0).write(acanvas, file)

        # merge new sizes
        
        OldSizes = self.Sizes

        NewSizeFile = open(TempName + ".size", "r")
        NewSizes = NewSizeFile.readlines()

        if (len(NewSizes) != 0) or (len(OldSizes) != 0):
            SizeFile = open(self.SizeFileName, "w")
            SizeFile.writelines(NewSizes)

            for OldSize in OldSizes:
                OldSizeSplit = OldSize.split(":")
                for NewSize in NewSizes:
                    if NewSize.split(":")[0:2] == OldSizeSplit[0:2]:
                        break
                else:
                    if time.time() < float(OldSizeSplit[2]) + 60*60*24:   # we keep size results for one day
                        SizeFile.write(OldSize)

        os.unlink(TempName + ".tex")
        os.unlink(TempName + ".log")
        os.unlink(TempName + ".dvi")
        os.unlink(TempName + ".eps")
        os.unlink(TempName + ".out")
        os.unlink(TempName + ".err")
        os.unlink(TempName + ".size")
        
        os.chdir(WorkDir)
       
    def define(self, Cmd, *styleparams):

        if len(self.BoxCmds):
            assert 0, "tex definitions not allowed after output commands"

        self.AllowedInstances(styleparams, [_msglevel, ])

        self.DefCmds.append(DefCmd(Cmd,
                                   len(self.DefCmds)+ len(self.BoxCmds),
                                   self.GetStack(),
                                   self.ExtractInstance(styleparams, _msglevel, msglevel.hideload)))

    def InsertCmd(self, Cmd, styleparams):

        if not self.DefCmdsStr:
            self.DefCmdsStr = reduce(lambda x,y: x + y.DefCmd, self.DefCmds, "")

        MyCmd = BoxCmd(self.DefCmdsStr,
                       Cmd,
                       self.ExtractInstance(styleparams, _fontsize, fontsize.normalsize),
                       self.ExtractInstance(styleparams, _hsize),
                       self.ExtractInstance(styleparams, _valign),
                       len(self.DefCmds)+ len(self.BoxCmds),
                       self.GetStack(),
                       self.ExtractInstance(styleparams, _msglevel, msglevel.hideload))
        if MyCmd not in self.BoxCmds:
            self.BoxCmds.append(MyCmd)
        for Cmd in self.BoxCmds:
            if Cmd == MyCmd:
                UseCmd = Cmd    # we could use MyBoxCmd directly if we have just inserted it before
                                # (that's due to the side effect, that append doesn't make a copy of the element,
                                # but we ignore this here -- we don't want to depend on this side effect)
        return UseCmd

    def text(self, x, y, Cmd, *styleparams):

        'print Cmd at (x, y)'

        self.AllowedInstances(styleparams, [_fontsize, _halign, _hsize, _valign, _direction, _msglevel, color.color, ])
        
        self.InsertCmd(Cmd, styleparams).Put(x,
                                             y,
                                             self.ExtractInstance(styleparams, _halign, halign.left),
                                             self.ExtractInstance(styleparams, _direction, direction.horizontal),
                                             self.ExtractInstance(styleparams, color.color, color.grey.black))

    def textwd(self, Cmd, *styleparams):
    
        'get width of Cmd'

        self.AllowedInstances(styleparams, [_fontsize, _msglevel, ])
        return self.InsertCmd(Cmd, styleparams).Extent(extent.wd, self.Sizes)

    def textht(self, Cmd, *styleparams):
    
        'get height of Cmd'

        self.AllowedInstances(styleparams, [_fontsize, _hsize, _valign, _msglevel, ])
        return self.InsertCmd(Cmd, styleparams).Extent(extent.ht, self.Sizes)

    def textdp(self, Cmd, *styleparams):
    
        'get depth of Cmd'

        self.AllowedInstances(styleparams, [_fontsize, _hsize, _valign, _msglevel, ])
        return self.InsertCmd(Cmd, styleparams).Extent(extent.dp, self.Sizes)

