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

"""
(La)TeX interface of PyX

This module provides the class tex, which can be inserted into a PyX canvas.
The method tex.text is used to print out text, while tex.textwd, tex.textht,
and tex.textdp appraise the width, height, and depth of a text, respectively.
"""

import canvas, os, string, tempfile, sys, md5, string, traceback, time, unit, math, types, color, StringIO

class _Attr:
    """base class for all PyX attributes (TODO: has to be defined somewhere else)"""
    pass

class _AttrTex(_Attr):
    """base class for all attributes handed to methods of class tex"""
    pass

class _AttrTexVal(_AttrTex):
    """an attribute, which has a value"""
    def __init__(self, value):
        self.value = value

class _AttrTexStr(_AttrTex):
    """makes a _AttrTexVal string-able"""
    def __str__(self):
        return str(self.value)

class _AttrTexCmp(_AttrTex):
    """makes a _AttrTexVal comparable"""
    def __cmp__(self, other):
        return cmp(self.value, other.value)
    __rcmp__ = __cmp__

class _AttrTexValStr(_AttrTexVal, _AttrTexStr):
    """an attribute with a string-able value"""
    pass

class _AttrTexValCmp(_AttrTexVal, _AttrTexCmp):
    """an attribute with a comparable value"""
    pass

class _AttrTexValCmpStr(_AttrTexVal, _AttrTexStr, _AttrTexCmp):
    """an attribute with a string-able and comparable value"""
    pass

class _halign(_AttrTexValCmp):
    """base attribute for halign, an comparable value"""
    pass

class halign:
    """ """
    left   = _halign("left")
    center = _halign("center")
    right  = _halign("right")
   
class hsize(_AttrTexStr):
    def __init__(self, value, canvas):
        self.value = canvas.unit.tpt(value)

class _valign(_AttrTexValCmpStr):
    pass

class valign:
    top    = _valign("vtop")
    bottom = _valign("vbox")

class _fontsize(_AttrTexValStr):
    pass

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

class _direction(_AttrTexValStr):
    pass

class direction(_direction):
    horizontal = _direction(0)
    vertical   = _direction(90)
    upsidedown = _direction(180)
    rvertical  = _direction(270)

class _style(_AttrTex):
    def __init__(self, praefix, suffix):
        self.praefix = praefix
        self.suffix = suffix
    def ModifyCmd(self, str):
        return self.praefix + str + self.suffix

class style:
    text = _style("", "")
    math = _style("$\displaystyle{}", "$")

class _msglevel(_AttrTexValCmp):
    pass

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

class _mode(_AttrTexValCmpStr):
    pass

class mode:
    TeX = _mode("TeX")
    LaTeX = _mode("LaTeX")

class latexsize(_AttrTexValStr):
    pass

class docclass(_AttrTexValStr):
    pass

class docopt(_AttrTexValStr):
    pass

class texfilename(_AttrTexValStr):
    pass

class _aextent(_AttrTexValCmpStr):
    pass

class _extent:
    wd = _aextent("wd")
    ht = _aextent("ht")
    dp = _aextent("dp")
   

class TexException(Exception):
    pass

class TexLeftParenthesisError(TexException):
    def __str__(self):
        return "no matching parenthesis for '{' found"

class TexRightParenthesisError(TexException):
    def __str__(self):
        return "no matching parenthesis for '}' found"

class _TexCmd:

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
        while (line != "") and (line[:-1] != self.EndMarkerStr()):
            msg = msg + line
            line = file.readline()
        if line == "":
            print "Traceback (innermost last):"
            traceback.print_list(self.Stack)
            print "(La)TeX Message:"
            print msg
            raise IOError
        else:
            # check if message can be ignored
            if self.msglevel == msglevel.showall:
                doprint = 0
                for c in msg:
                    if c not in string.whitespace:
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

class _DefCmd(_TexCmd):

    def __init__(self, DefCmd, Marker, Stack, msglevel):
        _TexCmd.__init__(self, Marker, Stack, msglevel)
        self.TexParenthesisCheck(DefCmd)
        self.DefCmd = DefCmd

    def write(self, canvas, file):
        self.WriteBeginMarker(file)
        file.write(self.DefCmd)
        self.WriteEndMarker(file)

class _CmdPut:

    def __init__(self, x, y, halign, direction, color):
        self.x = x
        self.y = y
        self.halign = halign
        self.direction = direction
        self.color = color

class _BoxCmd(_TexCmd):

    def __init__(self, DefCmdsStr, BoxCmd, style, fontsize, hsize, valign, Marker, Stack, msglevel):
        _TexCmd.__init__(self, Marker, Stack, msglevel)
        self.TexParenthesisCheck(BoxCmd)
        self.DefCmdsStr = DefCmdsStr
        self.BoxCmd = "{%s}" % BoxCmd # add another "{" to ensure, that everything goes into the Box
        self.CmdPuts = []
        self.CmdExtents = []

        self.BoxCmd = style.ModifyCmd(self.BoxCmd)
        if hsize:
            if valign:
                self.BoxCmd = "\\%s{\hsize%struept{%s}}" % (valign, hsize, self.BoxCmd, )
            else:
                self.BoxCmd = "\\vtop{\hsize%struept{%s}}" % (hsize, self.BoxCmd, )
        else:
            assert not valign, "hsize needed to use valign"
        self.BoxCmd = "\\setbox\\localbox=\\hbox{\\%s%s}%%\n" % (fontsize, self.BoxCmd, )

    def __cmp__(self, other):
        return cmp(self.BoxCmd, other.BoxCmd)
    __rcmp__ = __cmp__

    def write(self, canvas, file):

        self.WriteBeginMarker(file)
        file.write(self.BoxCmd)
        self.WriteEndMarker(file)
        for CmdExtent in self.CmdExtents:
            file.write("\\immediate\\write\\sizefile{%s:%s:%s:\\the\\%s\\localbox}%%\n" % (self.MD5(), CmdExtent, time.time(), CmdExtent, ))
        for CmdPut in self.CmdPuts:

            file.write("{\\vbox to0pt{\\kern%struept\\hbox{\\kern%struept\\ht\\localbox0pt" % (canvas.unit.tpt(-CmdPut.y), canvas.unit.tpt(CmdPut.x),))

            if CmdPut.direction != direction.horizontal:
                file.write("\\special{ps: gsave currentpoint currentpoint translate %s neg rotate neg exch neg exch translate }" % CmdPut.direction )
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
        s = md5.md5(self.DefCmdsStr + self.BoxCmd).digest()
        for c in s:
            i = ord(c)
            r = r + h[(i >> 4) & 0xF] + h[i & 0xF]
        return r

    def Put(self, x, y, halign, direction, color):
        self.CmdPuts.append(_CmdPut(x, y, halign, direction, color))

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


class _InstanceList:

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


class tex(_InstanceList):

    def __init__(self, *styleparams):
        self.AllowedInstances(styleparams, [_mode, texfilename, latexsize, docclass, docopt, ])
        self.mode = self.ExtractInstance(styleparams, _mode, mode.TeX)
        self.texfilename = self.ExtractInstance(styleparams, texfilename)
        if self.mode == mode.TeX:
            self.AllowedInstances(styleparams, [_mode, latexsize, texfilename])
            self.latexsize = self.ExtractInstance(styleparams, latexsize, latexsize("10pt"))
        else:
            self.AllowedInstances(styleparams, [_mode, docclass, docopt, texfilename])
            self.docclass = self.ExtractInstance(styleparams, docclass, docclass("article"))
            self.docopt = self.ExtractInstance(styleparams, docopt)
        self.DefCmds = []
        self.DefCmdsStr = None
        self.BoxCmds = []
        self.DoneRunTex = 0

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

        if self.mode == mode.TeX:
            # TODO: other ways for creating font sizes?
            LtsName = os.path.join(os.path.dirname(__file__), "lts", str(self.latexsize) + ".lts")
            self.define(open(LtsName, "r").read())
            self.define("\\hsize0truein%\n\\vsize0truein%\n\\hoffset-1truein%\n\\voffset-1truein")
        if self.mode == mode.LaTeX:
            if self.docopt:
                self.define("\\documentclass[" + str(self.docopt) + "]{" + str(self.docclass) + "}")
            else:
                self.define("\\documentclass{" + str(self.docclass) + "}")
            self.define("\\hsize0truein%\n\\vsize0truein%\n\\hoffset-1truein%\n\\voffset-1truein")



    def GetStack(self):
        return traceback.extract_stack(sys._getframe().f_back.f_back.f_back)
    
    def execute(self, command):
        if os.system(command):
            print "The exit code of the following command was non-zero:"
            print command
            print "Usually, additional information causing this trouble appears closeby."
            print "However, you may check the origin by keeping all temporary files."
            print "In order to achieve this, you have to specify a texfilename in the"
            print "constructor of the class pyx.tex. You can then try to run the command"
            print "by yourself."

    def RunTex(self, acanvas):

        'run LaTeX&dvips for TexCmds, report errors, return postscript string'
    
        # TODO: improve file handling (although it's quite usable now, those things can always be improved)

        if self.DoneRunTex:
            return

        WorkDir = os.getcwd()
        if self.texfilename:
            MkTemp = str(self.texfilename)
        else:
            storetempdir = tempfile.tempdir
            tempfile.tempdir = "."
            MkTemp = tempfile.mktemp()
            tempfile.tempdir = storetempdir
        TempDir = os.path.dirname(MkTemp)
        TempName = os.path.basename(MkTemp)
        try:
            os.chdir(TempDir)
        except:
            pass

        texfile = open(TempName + ".tex", "w")

        texfile.write("\\nonstopmode%\n")
        texfile.write("\\def\PyX{P\\kern-.25em\\lower.5ex\\hbox{Y}\\kern-.2em X}%\n")
        texfile.write("\\newwrite\\sizefile%\n\\newbox\\localbox%\n\\newbox\\pagebox%\n\\immediate\\openout\\sizefile=" + TempName + ".size%\n")

        for Cmd in self.DefCmds:
            Cmd.write(acanvas, texfile)

        texfile.write("\\setbox\\pagebox=\\vbox{%\n")

        for Cmd in self.BoxCmds:
            Cmd.write(acanvas, texfile)

        texfile.write("}\n\\immediate\\closeout\\sizefile\n\\shipout\\copy\\pagebox\n")
        if self.mode == mode.TeX:
            texfile.write("\\end\n")

        if self.mode == mode.LaTeX:
            texfile.write("\\end{document}\n")
        texfile.close()

        if self.mode == mode.LaTeX:
            auxfile = open(TempName + ".aux", "w")
            auxfile.write("\\relax\n")
            auxfile.close()

        self.execute("TEXINPUTS=" + WorkDir + ": " + string.lower(str(self.mode)) + " " + TempName + ".tex > " + TempName + ".texout 2> " + TempName + ".texerr")

        try:
            outfile = open(TempName + ".texout", "r")
            for Cmd in self.DefCmds + self.BoxCmds:
                Cmd.CheckMarkerError(outfile)
            outfile.close()
        except IOError:
            print "An unexpected error occured while reading the (La)TeX output."
            print "May be, you just have no disk space available. Or something badly"
            print "in your commands caused (La)TeX to give up completely. Or your"
            print "(La)TeX installation might be broken at all."
            print "You may try to check the origin by keeping all temporary files."
            print "In order to achieve this, you have to specify a texfilename in the"
            print "constructor of the class pyx.tex. You can then try to run (La)TeX"
            print "by yourself."

        if not os.access(TempName + ".dvi", 0):
            print "Can't find the dvi file which should be produced by (La)TeX."
            print "May be, you just have no disk space available. Or something badly"
            print "in your commands caused (La)TeX to give up completely. Or your"
            print "(La)TeX installation might be broken at all."
            print "You may try to check the origin by keeping all temporary files."
            print "In order to achieve this, you have to specify a texfilename in the"
            print "constructor of the class pyx.tex. You can then try to run (La)TeX"
            print "by yourself."

        else:
            self.execute("dvips -O0in,11in -E -o " + TempName + ".eps " + TempName + ".dvi > " + TempName + ".dvipsout 2> " + TempName + ".dvipserr")
            if not os.access(TempName + ".eps", 0):
                print "Error reading the eps file which should be produced by dvips."
                print "May be, you just have no disk space available. Or something badly"
                print "in your commands caused dvips to give up completely. Or your"
                print "(La)TeX installation might be broken at all."
                print "You may try to check the origin by keeping all temporary files."
                print "In order to achieve this, you have to specify a texfilename in the"
                print "constructor of the class pyx.tex. You can then try to run dvips"
                print "by yourself."
            else:
                epsfile = canvas.epsfile(TempName + ".eps", translatebb = 0)
                self.bbox = epsfile.bbox(acanvas)
                epsdatafile = StringIO.StringIO()
                epsfile.write(acanvas, epsdatafile)
                self.epsdata = epsdatafile.getvalue()

        # merge new sizes
        
        OldSizes = self.Sizes

        try:
            NewSizeFile = open(TempName + ".size", "r")
            NewSizes = NewSizeFile.readlines()
        except IOError:
            NewSizes = []

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

        if not self.texfilename:
            for suffix in ("tex", "log", "aux", "size", "dvi", "eps", "texout", "texerr", "dvipsout", "dvipserr", ):
                try:
                    os.unlink(TempName + "." + suffix)
                except:
                    pass
        
        os.chdir(WorkDir)
        self.DoneRunTex = 1

    def bbox(self, acanvas):
        self.RunTex(acanvas)
        return self.bbox

    def write(self, acanvas, file):
        self.RunTex(acanvas)
        file.writelines(self.epsdata)
       
    def define(self, Cmd, *styleparams):

        if len(self.BoxCmds):
            assert 0, "tex definitions not allowed after output commands"

        self.DoneRunTex = 0

        self.AllowedInstances(styleparams, [_msglevel, ])

        self.DefCmds.append(_DefCmd(Cmd + "%\n",
                                    len(self.DefCmds)+ len(self.BoxCmds),
                                    self.GetStack(),
                                    self.ExtractInstance(styleparams, _msglevel, msglevel.hideload)))

    def InsertCmd(self, Cmd, styleparams):

        if not len(self.BoxCmds):
            if self.mode == mode.LaTeX:
                self.define("\\begin{document}")
            self.DefCmdsStr = reduce(lambda x,y: x + y.DefCmd, self.DefCmds, "")

        MyCmd = _BoxCmd(self.DefCmdsStr,
                        Cmd,
                        self.ExtractInstance(styleparams, _style, style.text),
                        self.ExtractInstance(styleparams, _fontsize, fontsize.normalsize),
                        self.ExtractInstance(styleparams, hsize),
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
        
        self.DoneRunTex = 0

        self.AllowedInstances(styleparams, [_style, _fontsize, _halign, hsize, _valign, _direction, _msglevel, color.color, ])
        
        self.InsertCmd(Cmd, styleparams).Put(x,
                                             y,
                                             self.ExtractInstance(styleparams, _halign, halign.left),
                                             self.ExtractInstance(styleparams, _direction, direction.horizontal),
                                             self.ExtractInstance(styleparams, color.color, color.grey.black))

    def textwd(self, Cmd, *styleparams):
    
        'get width of Cmd'

        self.DoneRunTex = 0

        self.AllowedInstances(styleparams, [_style, _fontsize, _msglevel, ])
        return self.InsertCmd(Cmd, styleparams).Extent(_extent.wd, self.Sizes)

    def textht(self, Cmd, *styleparams):
    
        'get height of Cmd'

        self.DoneRunTex = 0

        self.AllowedInstances(styleparams, [_style, _fontsize, hsize, _valign, _msglevel, ])
        return self.InsertCmd(Cmd, styleparams).Extent(_extent.ht, self.Sizes)

    def textdp(self, Cmd, *styleparams):
    
        'get depth of Cmd'

        self.DoneRunTex = 0

        self.AllowedInstances(styleparams, [_style, _fontsize, hsize, _valign, _msglevel, ])
        return self.InsertCmd(Cmd, styleparams).Extent(_extent.dp, self.Sizes)

