#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2002-2003 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2002-2003 André Wobst <wobsta@users.sourceforge.net>
# Copyright (C) 2003 Michael Schindler <m-schindler@users.sourceforge.net>
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

import glob, os, threading, Queue, traceback, re, tempfile, sys, atexit, time
import config, helper, unit, box, canvas, trafo, version, attr, style, dvifile

###############################################################################
# texmessages
# - please don't get confused:
#   - there is a texmessage (and a texmessageparsed) attribute within the
#     texrunner; it contains TeX/LaTeX response from the last command execution
#   - instances of classes derived from the class texmessage are used to
#     parse the TeX/LaTeX response as it is stored in the texmessageparsed
#     attribute of a texrunner instance
#   - the multiple usage of the name texmessage might be removed in the future
# - texmessage instances should implement _Itexmessage
###############################################################################

class TexResultError(Exception):
    """specialized texrunner exception class
    - it is raised by texmessage instances, when a texmessage indicates an error
    - it is raised by the texrunner itself, whenever there is a texmessage left
      after all parsing of this message (by texmessage instances)"""

    def __init__(self, description, texrunner):
        self.description = description
        self.texrunner = texrunner

    def __str__(self):
        """prints a detailed report about the problem
        - the verbose level is controlled by texrunner.errordebug"""
        if self.texrunner.errordebug >= 2:
            return ("%s\n" % self.description +
                    "The expression passed to TeX was:\n"
                    "  %s\n" % self.texrunner.expr.replace("\n", "\n  ").rstrip() +
                    "The return message from TeX was:\n"
                    "  %s\n" % self.texrunner.texmessage.replace("\n", "\n  ").rstrip() +
                    "After parsing this message, the following was left:\n"
                    "  %s" % self.texrunner.texmessageparsed.replace("\n", "\n  ").rstrip())
        elif self.texrunner.errordebug == 1:
            firstlines = self.texrunner.texmessageparsed.split("\n")
            if len(firstlines) > 5:
                firstlines = firstlines[:5] + ["(cut after 5 lines, increase errordebug for more output)"]
            return ("%s\n" % self.description +
                    "The expression passed to TeX was:\n"
                    "  %s\n" % self.texrunner.expr.replace("\n", "\n  ").rstrip() +
                    "After parsing the return message from TeX, the following was left:\n" +
                    reduce(lambda x, y: "%s  %s\n" % (x,y), firstlines, "").rstrip())
        else:
            return self.description


class TexResultWarning(TexResultError):
    """as above, but with different handling of the exception
    - when this exception is raised by a texmessage instance,
      the information just get reported and the execution continues"""
    pass


class _Itexmessage:
    """validates/invalidates TeX/LaTeX response"""

    def check(self, texrunner):
        """check a Tex/LaTeX response and respond appropriate
        - read the texrunners texmessageparsed attribute
        - if there is an problem found, raise an appropriate
          exception (TexResultError or TexResultWarning)
        - remove any valid and identified TeX/LaTeX response
          from the texrunners texmessageparsed attribute
          -> finally, there should be nothing left in there,
             otherwise it is interpreted as an error"""


class texmessage: pass


class _texmessagestart(texmessage):
    """validates TeX/LaTeX startup"""

    __implements__ = _Itexmessage

    startpattern = re.compile(r"This is [-0-9a-zA-Z\s_]*TeX")

    def check(self, texrunner):
        m = self.startpattern.search(texrunner.texmessageparsed)
        if not m:
            raise TexResultError("TeX startup failed", texrunner)
        texrunner.texmessageparsed = texrunner.texmessageparsed[m.end():]
        try:
            texrunner.texmessageparsed = texrunner.texmessageparsed.split("%s.tex" % texrunner.texfilename, 1)[1]
        except (IndexError, ValueError):
            raise TexResultError("TeX running startup file failed", texrunner)
        try:
            texrunner.texmessageparsed = texrunner.texmessageparsed.split("*! Undefined control sequence.\n<*> \\raiseerror\n               %\n", 1)[1]
        except (IndexError, ValueError):
            raise TexResultError("TeX scrollmode check failed", texrunner)


class _texmessagenoaux(texmessage):
    """allows for LaTeXs no-aux-file warning"""

    __implements__ = _Itexmessage

    def check(self, texrunner):
        try:
            s1, s2 = texrunner.texmessageparsed.split("No file %s.aux." % texrunner.texfilename, 1)
            texrunner.texmessageparsed = s1 + s2
        except (IndexError, ValueError):
            try:
                s1, s2 = texrunner.texmessageparsed.split("No file %s%s%s.aux." % (os.curdir,
                                                                                   os.sep,
                                                                                    texrunner.texfilename), 1)
                texrunner.texmessageparsed = s1 + s2
            except (IndexError, ValueError):
                pass


class _texmessageinputmarker(texmessage):
    """validates the PyXInputMarker"""

    __implements__ = _Itexmessage

    def check(self, texrunner):
        try:
            s1, s2 = texrunner.texmessageparsed.split("PyXInputMarker:executeid=%s:" % texrunner.executeid, 1)
            texrunner.texmessageparsed = s1 + s2
        except (IndexError, ValueError):
            raise TexResultError("PyXInputMarker expected", texrunner)


class _texmessagepyxbox(texmessage):
    """validates the PyXBox output"""

    __implements__ = _Itexmessage

    pattern = re.compile(r"PyXBox:page=(?P<page>\d+),lt=-?\d*((\d\.?)|(\.?\d))\d*pt,rt=-?\d*((\d\.?)|(\.?\d))\d*pt,ht=-?\d*((\d\.?)|(\.?\d))\d*pt,dp=-?\d*((\d\.?)|(\.?\d))\d*pt:")

    def check(self, texrunner):
        m = self.pattern.search(texrunner.texmessageparsed)
        if m and m.group("page") == str(texrunner.page):
            texrunner.texmessageparsed = texrunner.texmessageparsed[:m.start()] + texrunner.texmessageparsed[m.end():]
        else:
            raise TexResultError("PyXBox expected", texrunner)


class _texmessagepyxpageout(texmessage):
    """validates the dvi shipout message (writing a page to the dvi file)"""

    __implements__ = _Itexmessage

    def check(self, texrunner):
        try:
            s1, s2 = texrunner.texmessageparsed.split("[80.121.88.%s]" % texrunner.page, 1)
            texrunner.texmessageparsed = s1 + s2
        except (IndexError, ValueError):
            raise TexResultError("PyXPageOutMarker expected", texrunner)


class _texmessagetexend(texmessage):
    """validates TeX/LaTeX finish"""

    __implements__ = _Itexmessage

    def check(self, texrunner):
        try:
            s1, s2 = texrunner.texmessageparsed.split("(%s.aux)" % texrunner.texfilename, 1)
            texrunner.texmessageparsed = s1 + s2
        except (IndexError, ValueError):
            try:
                s1, s2 = texrunner.texmessageparsed.split("(%s%s%s.aux)" % (os.curdir,
                                                                        os.sep,
                                                                        texrunner.texfilename), 1)
                texrunner.texmessageparsed = s1 + s2
            except (IndexError, ValueError):
                pass
        try:
            s1, s2 = texrunner.texmessageparsed.split("(see the transcript file for additional information)", 1)
            texrunner.texmessageparsed = s1 + s2
        except (IndexError, ValueError):
            pass
        dvipattern = re.compile(r"Output written on %s\.dvi \((?P<page>\d+) pages?, \d+ bytes\)\." % texrunner.texfilename)
        m = dvipattern.search(texrunner.texmessageparsed)
        if texrunner.page:
            if not m:
                raise TexResultError("TeX dvifile messages expected", texrunner)
            if m.group("page") != str(texrunner.page):
                raise TexResultError("wrong number of pages reported", texrunner)
            texrunner.texmessageparsed = texrunner.texmessageparsed[:m.start()] + texrunner.texmessageparsed[m.end():]
        else:
            try:
                s1, s2 = texrunner.texmessageparsed.split("No pages of output.", 1)
                texrunner.texmessageparsed = s1 + s2
            except (IndexError, ValueError):
                raise TexResultError("no dvifile expected", texrunner)
        try:
            s1, s2 = texrunner.texmessageparsed.split("Transcript written on %s.log." % texrunner.texfilename, 1)
            texrunner.texmessageparsed = s1 + s2
        except (IndexError, ValueError):
            raise TexResultError("TeX logfile message expected", texrunner)


class _texmessageemptylines(texmessage):
    """validates "*-only" (TeX/LaTeX input marker in interactive mode) and empty lines"""

    __implements__ = _Itexmessage

    def check(self, texrunner):
        texrunner.texmessageparsed = texrunner.texmessageparsed.replace("*\n", "")
        texrunner.texmessageparsed = texrunner.texmessageparsed.replace("\n", "")


class _texmessageload(texmessage):
    """validates inclusion of arbitrary files
    - the matched pattern is "(<filename> <arbitrary other stuff>)", where
      <fielname> is a readable file and other stuff can be anything
    - "(" and ")" must be used consistent (otherwise this validator just does nothing)
    - this is not always wanted, but we just assume that file inclusion is fine"""

    __implements__ = _Itexmessage

    pattern = re.compile(r" *\((?P<filename>[^()\s\n]+)[^()]*\) *")

    def baselevels(self, s, maxlevel=1, brackets="()"):
        """strip parts of a string above a given bracket level
        - return a modified (some parts might be removed) version of the string s
          where all parts inside brackets with level higher than maxlevel are
          removed
        - if brackets do not match (number of left and right brackets is wrong
          or at some points there were more right brackets than left brackets)
          just return the unmodified string"""
        level = 0
        highestlevel = 0
        res = ""
        for c in s:
            if c == brackets[0]:
                level += 1
                if level > highestlevel:
                    highestlevel = level
            if level <= maxlevel:
                res += c
            if c == brackets[1]:
                level -= 1
        if level == 0 and highestlevel > 0:
            return res

    def check(self, texrunner):
        lowestbracketlevel = self.baselevels(texrunner.texmessageparsed)
        if lowestbracketlevel is not None:
            m = self.pattern.search(lowestbracketlevel)
            while m:
                if os.access(m.group("filename"), os.R_OK):
                    lowestbracketlevel = lowestbracketlevel[:m.start()] + lowestbracketlevel[m.end():]
                else:
                    break
                m = self.pattern.search(lowestbracketlevel)
            else:
                texrunner.texmessageparsed = lowestbracketlevel


class _texmessageloadfd(_texmessageload):
    """validates the inclusion of font description files (fd-files)
    - works like _texmessageload
    - filename must end with .fd and no further text is allowed"""

    pattern = re.compile(r" *\((?P<filename>[^)]+.fd)\) *")


class _texmessagegraphicsload(_texmessageload):
    """validates the inclusion of files as the graphics packages writes it
    - works like _texmessageload, but using "<" and ">" as delimiters
    - filename must end with .eps and no further text is allowed"""

    pattern = re.compile(r" *<(?P<filename>[^>]+.eps)> *")

    def baselevels(self, s, brackets="<>", **args):
        return _texmessageload.baselevels(self, s, brackets=brackets, **args)


class _texmessageignore(_texmessageload):
    """validates any TeX/LaTeX response
    - this might be used, when the expression is ok, but no suitable texmessage
      parser is available
    - PLEASE: - consider writing suitable tex message parsers
              - share your ideas/problems/solutions with others (use the PyX mailing lists)"""

    __implements__ = _Itexmessage

    def check(self, texrunner):
        texrunner.texmessageparsed = ""


texmessage.start = _texmessagestart()
texmessage.noaux = _texmessagenoaux()
texmessage.inputmarker = _texmessageinputmarker()
texmessage.pyxbox = _texmessagepyxbox()
texmessage.pyxpageout = _texmessagepyxpageout()
texmessage.texend = _texmessagetexend()
texmessage.emptylines = _texmessageemptylines()
texmessage.load = _texmessageload()
texmessage.loadfd = _texmessageloadfd()
texmessage.graphicsload = _texmessagegraphicsload()
texmessage.ignore = _texmessageignore()


###############################################################################
# textattrs
###############################################################################

_textattrspreamble = ""

class textattr:
    "a textattr defines a apply method, which modifies a (La)TeX expression"

class halign(attr.exclusiveattr, textattr):

    def __init__(self, hratio):
        self.hratio = hratio
        attr.exclusiveattr.__init__(self, halign)

    def apply(self, expr):
        return r"\gdef\PyXHAlign{%.5f}%s" % (self.hratio, expr)

halign.center = halign(0.5)
halign.right = halign(1)
halign.clear = attr.clearclass(halign)
halign.left = halign.clear


class _localattr: pass

class _mathmode(attr.attr, textattr, _localattr):
    "math mode"

    def apply(self, expr):
        return r"$\displaystyle{%s}$" % expr

mathmode = _mathmode()
nomathmode = attr.clearclass(_mathmode)


defaultsizelist = ["normalsize", "large", "Large", "LARGE", "huge", "Huge", None, "tiny", "scriptsize", "footnotesize", "small"]

class size(attr.sortbeforeattr, textattr, _localattr):
    "font size"

    def __init__(self, expr, sizelist=defaultsizelist):
        attr.sortbeforeattr.__init__(self, [_mathmode])
        if helper.isinteger(expr):
            if expr >= 0 and expr < sizelist.index(None):
                self.size = sizelist[expr]
            elif expr < 0 and expr + len(sizelist) > sizelist.index(None):
                self.size = sizelist[expr]
            else:
                raise IndexError("index out of sizelist range")
        else:
            self.size = expr

    def apply(self, expr):
        return r"\%s{%s}" % (self.size, expr)

for s in defaultsizelist:
    if s is not None:
        setattr(size, s, size(s))
del s

_textattrspreamble += "\\newbox\\PyXBoxVBox%\n\\newdimen\PyXDimenVBox%\n"

class parbox_pt(attr.sortbeforeexclusiveattr, textattr):

    top = 1
    middle = 2
    bottom = 3

    def __init__(self, width, baseline=top):
        self.width = width
        self.baseline = baseline
        attr.sortbeforeexclusiveattr.__init__(self, parbox_pt, [_localattr])

    def apply(self, expr):
        if self.baseline == self.top:
            return r"\linewidth%.5ftruept\vtop{\hsize\linewidth{%s}}" % (self.width * 72.27 / 72, expr)
        elif self.baseline == self.middle:
            return r"\linewidth%.5ftruept\setbox\PyXBoxVBox=\hbox{{\vtop{\hsize\linewidth{%s}}}}\PyXDimenVBox=0.5\dp\PyXBoxVBox\setbox\PyXBoxVBox=\hbox{{\vbox{\hsize\linewidth{%s}}}}\advance\PyXDimenVBox by -0.5\dp\PyXBoxVBox\lower\PyXDimenVBox\box\PyXBoxVBox" % (self.width, expr, expr)
        elif self.baseline == self.bottom:
            return r"\linewidth%.5ftruept\vbox{\hsize\linewidth{%s}}" % (self.width * 72.27 / 72, expr)
        else:
            RuntimeError("invalid baseline argument")

class parbox(parbox_pt):

    def __init__(self, width, **kwargs):
        parbox_pt.__init__(self, unit.topt(width), **kwargs)


_textattrspreamble += "\\newbox\\PyXBoxVAlign%\n\\newdimen\PyXDimenVAlign%\n"

class valign(attr.sortbeforeexclusiveattr, textattr):

    def __init__(self):
        attr.sortbeforeexclusiveattr.__init__(self, valign, [parbox_pt, _localattr])

class _valigntop(valign):

    def apply(self, expr):
        return r"\setbox\PyXBoxVAlign=\hbox{{%s}}\lower\ht\PyXBoxVAlign\box\PyXBoxVAlign" % expr

class _valignmiddle(valign):

    def apply(self, expr):
        return r"\setbox\PyXBoxVAlign=\hbox{{%s}}\PyXDimenVAlign=0.5\ht\PyXBoxVAlign\advance\PyXDimenVAlign by -0.5\dp\PyXBoxVAlign\lower\PyXDimenVAlign\box\PyXBoxVAlign" % expr

class _valignbottom(valign):

    def apply(self, expr):
        return r"\setbox\PyXBoxVAlign=\hbox{{%s}}\raise\dp\PyXBoxVAlign\box\PyXBoxVAlign" % expr

valign.top = _valigntop()
valign.middle = _valignmiddle()
valign.bottom = _valignbottom()
valign.clear = attr.clearclass(valign)
valign.baseline = valign.clear


class _vshift(attr.sortbeforeattr, textattr):

    def __init__(self):
        attr.sortbeforeattr.__init__(self, [valign, parbox_pt, _localattr])

class vshift(_vshift):
    "vertical down shift by a fraction of a character height"

    def __init__(self, lowerratio, heightstr="0"):
        _vshift.__init__(self)
        self.lowerratio = lowerratio
        self.heightstr = heightstr

    def apply(self, expr):
        return r"\setbox0\hbox{{%s}}\lower%.5f\ht0\hbox{{%s}}" % (self.heightstr, self.lowerratio, expr)

class _vshiftmathaxis(_vshift):
    "vertical down shift by the height of the math axis"

    def apply(self, expr):
        return r"\setbox0\hbox{$\vcenter{\vrule width0pt}$}\lower\ht0\hbox{{%s}}" % expr


vshift.bottomzero = vshift(0)
vshift.middlezero = vshift(0.5)
vshift.topzero = vshift(1)
vshift.mathaxis = _vshiftmathaxis()


###############################################################################
# texrunner
###############################################################################


class _readpipe(threading.Thread):
    """threaded reader of TeX/LaTeX output
    - sets an event, when a specific string in the programs output is found
    - sets an event, when the terminal ends"""

    def __init__(self, pipe, expectqueue, gotevent, gotqueue, quitevent):
        """initialize the reader
        - pipe: file to be read from
        - expectqueue: keeps the next InputMarker to be wait for
        - gotevent: the "got InputMarker" event
        - gotqueue: a queue containing the lines recieved from TeX/LaTeX
        - quitevent: the "end of terminal" event"""
        threading.Thread.__init__(self)
        self.setDaemon(1) # don't care if the output might not be finished (nevertheless, it shouldn't happen)
        self.pipe = pipe
        self.expectqueue = expectqueue
        self.gotevent = gotevent
        self.gotqueue = gotqueue
        self.quitevent = quitevent
        self.expect = None
        self.start()

    def run(self):
        """thread routine"""
        read = self.pipe.readline() # read, what comes in
        try:
            self.expect = self.expectqueue.get_nowait() # read, what should be expected
        except Queue.Empty:
            pass
        while len(read):
            # universal EOL handling (convert everything into unix like EOLs)
            read.replace("\r", "")
            if not len(read) or read[-1] != "\n":
                read += "\n"
            self.gotqueue.put(read) # report, whats readed
            if self.expect is not None and read.find(self.expect) != -1:
                self.gotevent.set() # raise the got event, when the output was expected (XXX: within a single line)
            read = self.pipe.readline() # read again
            try:
                self.expect = self.expectqueue.get_nowait()
            except Queue.Empty:
                pass
        # EOF reached
        self.pipe.close()
        if self.expect is not None and self.expect.find("PyXInputMarker") != -1:
            raise RuntimeError("TeX/LaTeX finished unexpectedly")
        self.quitevent.set()


class textbox_pt(box.rect_pt, canvas._canvas):
    """basically a box.rect, but it contains a text created by the texrunner
    - texrunner._text and texrunner.text return such an object
    - _textbox instances can be inserted into a canvas
    - the output is contained in a page of the dvifile available thru the texrunner"""
    # TODO: shouldn't all boxes become canvases? how about inserts then?

    def __init__(self, x, y, left, right, height, depth, finishdvi, *attrs):
        """
        - finishdvi is a method to be called to get the dvicanvas
          (e.g. the finishdvi calls the setdvicanvas method)
        - attrs are fillstyles"""
        self.texttrafo = trafo._translate(x, y)
        box.rect_pt.__init__(self, x - left, y - depth,
                                 left + right, depth + height,
                                 abscenter = (left, depth))
        canvas._canvas.__init__(self)
        self.finishdvi = finishdvi
        self.dvicanvas = None
        for attr in attrs:
            self.set(attr)
        self.insertdvicanvas = 0

    def transform(self, *trafos):
        if self.insertdvicanvas:
            raise RuntimeError("can't apply transformation after dvicanvas was inserted")
        box.rect_pt.transform(self, *trafos)
        for trafo in trafos:
            self.texttrafo = trafo * self.texttrafo

    def setdvicanvas(self, dvicanvas):
        if self.dvicanvas is not None:
            raise RuntimeError("multiple call to setdvicanvas")
        self.dvicanvas = dvicanvas

    def ensuredvicanvas(self):
        if self.dvicanvas is None:
            self.finishdvi()
            assert self.dvicanvas is not None, "finishdvi is broken"
        if not self.insertdvicanvas:
            self.insert(self.dvicanvas, self.texttrafo)

    def marker(self, marker):
        self.ensuredvicanvas()
        return self.texttrafo.apply(*self.dvicanvas.markers[marker])

    def prolog(self):
        self.ensuredvicanvas()
        return canvas._canvas.prolog(self)

    def write(self, file):
        self.ensuredvicanvas()
        canvas._canvas.write(self, file)


class textbox(textbox_pt):

    def __init__(self, x, y, left, right, height, depth, texrunner, *attrs):
        textbox_pt.__init__(self, unit.topt(x), unit.topt(y), unit.topt(left), unit.topt(right),
                          unit.topt(height), unit.topt(depth), texrunner, *attrs)


def _cleantmp(texrunner):
    """get rid of temporary files
    - function to be registered by atexit
    - files contained in usefiles are kept"""
    if texrunner.texruns: # cleanup while TeX is still running?
        texrunner.texruns = 0
        texrunner.texdone = 1
        texrunner.expectqueue.put_nowait(None)              # do not expect any output anymore
        if texrunner.mode == "latex":                       # try to immediately quit from TeX or LaTeX
            texrunner.texinput.write("\n\\catcode`\\@11\\relax\\@@end\n")
        else:
            texrunner.texinput.write("\n\\end\n")
        texrunner.texinput.close()                          # close the input queue and
        if not texrunner.waitforevent(texrunner.quitevent): # wait for finish of the output
            return                                          # didn't got a quit from TeX -> we can't do much more
    for usefile in texrunner.usefiles:
        extpos = usefile.rfind(".")
        try:
            os.rename(texrunner.texfilename + usefile[extpos:], usefile)
        except OSError:
            pass
    for file in glob.glob("%s.*" % texrunner.texfilename):
        try:
            os.unlink(file)
        except OSError:
            pass
    if texrunner.texdebug is not None:
        try:
            texrunner.texdebug.close()
            texrunner.texdebug = None
        except IOError:
            pass


# texrunner state exceptions
class TexRunsError(Exception): pass
class TexDoneError(Exception): pass
class TexNotInPreambleModeError(Exception): pass


class texrunner:
    """TeX/LaTeX interface
    - runs TeX/LaTeX expressions instantly
    - checks TeX/LaTeX response
    - the instance variable texmessage stores the last TeX
      response as a string
    - the instance variable texmessageparsed stores a parsed
      version of texmessage; it should be empty after
      texmessage.check was called, otherwise a TexResultError
      is raised
    - the instance variable errordebug controls the verbose
      level of TexResultError"""

    def __init__(self, mode="tex",
                       lfs="10pt",
                       docclass="article",
                       docopt=None,
                       usefiles=None,
                       fontmaps=config.get("text", "fontmaps", "psfonts.map"),
                       waitfortex=config.getint("text", "waitfortex", 60),
                       showwaitfortex=config.getint("text", "showwaitfortex", 5),
                       texipc=config.getboolean("text", "texipc", 0),
                       texdebug=None,
                       dvidebug=0,
                       errordebug=1,
                       dvicopy=0,
                       pyxgraphics=1,
                       texmessagestart=texmessage.start,
                       texmessagedocclass=texmessage.load,
                       texmessagebegindoc=(texmessage.load, texmessage.noaux),
                       texmessageend=texmessage.texend,
                       texmessagedefaultpreamble=texmessage.load,
                       texmessagedefaultrun=texmessage.loadfd):
        mode = mode.lower()
        if mode != "tex" and mode != "latex":
            raise ValueError("mode \"TeX\" or \"LaTeX\" expected")
        self.mode = mode
        self.lfs = lfs
        self.docclass = docclass
        self.docopt = docopt
        self.usefiles = helper.ensurelist(usefiles)
        self.fontmap = dvifile.readfontmap(fontmaps.split())
        self.waitfortex = waitfortex
        self.showwaitfortex = showwaitfortex
        self.texipc = texipc
        if texdebug is not None:
            if texdebug[-4:] == ".tex":
                self.texdebug = open(texdebug, "w")
            else:
                self.texdebug = open("%s.tex" % texdebug, "w")
        else:
            self.texdebug = None
        self.dvidebug = dvidebug
        self.errordebug = errordebug
        self.dvicopy = dvicopy
        self.pyxgraphics = pyxgraphics
        texmessagestart = helper.ensuresequence(texmessagestart)
        helper.checkattr(texmessagestart, allowmulti=(texmessage,))
        self.texmessagestart = texmessagestart
        texmessagedocclass = helper.ensuresequence(texmessagedocclass)
        helper.checkattr(texmessagedocclass, allowmulti=(texmessage,))
        self.texmessagedocclass = texmessagedocclass
        texmessagebegindoc = helper.ensuresequence(texmessagebegindoc)
        helper.checkattr(texmessagebegindoc, allowmulti=(texmessage,))
        self.texmessagebegindoc = texmessagebegindoc
        texmessageend = helper.ensuresequence(texmessageend)
        helper.checkattr(texmessageend, allowmulti=(texmessage,))
        self.texmessageend = texmessageend
        texmessagedefaultpreamble = helper.ensuresequence(texmessagedefaultpreamble)
        helper.checkattr(texmessagedefaultpreamble, allowmulti=(texmessage,))
        self.texmessagedefaultpreamble = texmessagedefaultpreamble
        texmessagedefaultrun = helper.ensuresequence(texmessagedefaultrun)
        helper.checkattr(texmessagedefaultrun, allowmulti=(texmessage,))
        self.texmessagedefaultrun = texmessagedefaultrun

        self.texruns = 0
        self.texdone = 0
        self.preamblemode = 1
        self.executeid = 0
        self.page = 0
        self.preambles = []
        self.acttextboxes = [] # when texipc-mode off
        self.actdvifile = None # when texipc-mode on
        savetempdir = tempfile.tempdir
        tempfile.tempdir = os.curdir
        self.texfilename = os.path.basename(tempfile.mktemp())
        tempfile.tempdir = savetempdir

    def waitforevent(self, event):
        """waits verbosely with an timeout for an event
        - observes an event while periodly while printing messages
        - returns the status of the event (isSet)
        - does not clear the event"""
        if self.showwaitfortex:
            waited = 0
            hasevent = 0
            while waited < self.waitfortex and not hasevent:
                if self.waitfortex - waited > self.showwaitfortex:
                    event.wait(self.showwaitfortex)
                    waited += self.showwaitfortex
                else:
                    event.wait(self.waitfortex - waited)
                    waited += self.waitfortex - waited
                hasevent = event.isSet()
                if not hasevent:
                    if waited < self.waitfortex:
                        sys.stderr.write("*** PyX INFO: still waiting for %s after %i seconds...\n" % (self.mode, waited))
                    else:
                        sys.stderr.write("*** PyX ERROR: the timeout of %i seconds expired and %s did not respond.\n" % (waited, self.mode))
            return hasevent
        else:
            event.wait(self.waitfortex)
            return event.isSet()

    def execute(self, expr, *checks):
        """executes expr within TeX/LaTeX
        - if self.texruns is not yet set, TeX/LaTeX is initialized,
          self.texruns is set and self.preamblemode is set
        - the method must not be called, when self.texdone is already set
        - expr should be a string or None
        - when expr is None, TeX/LaTeX is stopped, self.texruns is unset and
          while self.texdone becomes set
        - when self.preamblemode is set, the expr is passed directly to TeX/LaTeX
        - when self.preamblemode is unset, the expr is passed to \ProcessPyXBox
        """
        if not self.texruns:
            if self.texdebug is not None:
                self.texdebug.write("%% PyX %s texdebug file\n" % version.version)
                self.texdebug.write("%% mode: %s\n" % self.mode)
                self.texdebug.write("%% date: %s\n" % time.asctime(time.localtime(time.time())))
            for usefile in self.usefiles:
                extpos = usefile.rfind(".")
                try:
                    os.rename(usefile, self.texfilename + usefile[extpos:])
                except OSError:
                    pass
            texfile = open("%s.tex" % self.texfilename, "w") # start with filename -> creates dvi file with that name
            texfile.write("\\relax%\n")
            texfile.close()
            if self.texipc:
                ipcflag = " --ipc"
            else:
                ipcflag = ""
            try:
                self.texinput, self.texoutput = os.popen4("%s%s %s" % (self.mode, ipcflag, self.texfilename), "t", 0)
            except ValueError:
                # XXX: workaround for MS Windows (bufsize = 0 makes trouble!?)
                self.texinput, self.texoutput = os.popen4("%s%s %s" % (self.mode, ipcflag, self.texfilename), "t")
            atexit.register(_cleantmp, self)
            self.expectqueue = Queue.Queue(1)  # allow for a single entry only -> keeps the next InputMarker to be wait for
            self.gotevent = threading.Event()  # keeps the got inputmarker event
            self.gotqueue = Queue.Queue(0)     # allow arbitrary number of entries
            self.quitevent = threading.Event() # keeps for end of terminal event
            self.readoutput = _readpipe(self.texoutput, self.expectqueue, self.gotevent, self.gotqueue, self.quitevent)
            self.texruns = 1
            oldpreamblemode = self.preamblemode
            self.preamblemode = 1
            self.execute("\\scrollmode\n\\raiseerror%\n" # switch to and check scrollmode
                         "\\def\\PyX{P\\kern-.3em\\lower.5ex\hbox{Y}\kern-.18em X}%\n" # just the PyX Logo
                         "\\gdef\\PyXHAlign{0}%\n" # global PyXHAlign (0.0-1.0) for the horizontal alignment, default to 0
                         "\\newbox\\PyXBox%\n" # PyXBox will contain the output
                         "\\newbox\\PyXBoxHAligned%\n" # PyXBox will contain the horizontal aligned output
                         "\\newdimen\\PyXDimenHAlignLT%\n" # PyXDimenHAlignLT/RT will contain the left/right extent
                         "\\newdimen\\PyXDimenHAlignRT%\n" +
                         _textattrspreamble + # insert preambles for textattrs macros
                         "\\long\\def\\ProcessPyXBox#1#2{%\n" # the ProcessPyXBox definition (#1 is expr, #2 is page number)
                         "\\setbox\\PyXBox=\\hbox{{#1}}%\n" # push expression into PyXBox
                         "\\PyXDimenHAlignLT=\\PyXHAlign\\wd\\PyXBox%\n" # calculate the left/right extent
                         "\\PyXDimenHAlignRT=\\wd\\PyXBox%\n"
                         "\\advance\\PyXDimenHAlignRT by -\\PyXDimenHAlignLT%\n"
                         "\\gdef\\PyXHAlign{0}%\n" # reset the PyXHAlign to the default 0
                         "\\immediate\\write16{PyXBox:page=#2," # write page and extents of this box to stdout
                                                     "lt=\\the\\PyXDimenHAlignLT,"
                                                     "rt=\\the\\PyXDimenHAlignRT,"
                                                     "ht=\\the\\ht\\PyXBox,"
                                                     "dp=\\the\\dp\\PyXBox:}%\n"
                         "\\setbox\\PyXBoxHAligned=\\hbox{\\kern-\\PyXDimenHAlignLT\\box\\PyXBox}%\n" # align horizontally
                         "\\ht\\PyXBoxHAligned0pt%\n" # baseline alignment (hight to zero)
                         "{\\count0=80\\count1=121\\count2=88\\count3=#2\\shipout\\box\\PyXBoxHAligned}}%\n" # shipout PyXBox to Page 80.121.88.<page number>
                         "\\def\\PyXInput#1{\\immediate\\write16{PyXInputMarker:executeid=#1:}}%\n" # write PyXInputMarker to stdout
                         "\\def\\PyXMarker#1{\\special{PyX:marker #1}}%\n", # write PyXMarker special into the dvi-file
                         *self.texmessagestart)
            os.remove("%s.tex" % self.texfilename)
            if self.mode == "tex":
                if len(self.lfs) > 4 and self.lfs[-4:] == ".lfs":
                    lfsname = self.lfs
                else:
                    lfsname = "%s.lfs" % self.lfs
                for fulllfsname in [lfsname,
                                    os.path.join(sys.prefix, "share", "pyx", lfsname),
                                    os.path.join(os.path.dirname(__file__), "lfs", lfsname)]:
                    try:
                        lfsfile = open(fulllfsname, "r")
                        lfsdef = lfsfile.read()
                        lfsfile.close()
                        break
                    except IOError:
                        pass
                else:
                    allfiles = (glob.glob("*.lfs") +
                                glob.glob(os.path.join(sys.prefix, "share", "pyx", "*.lfs")) +
                                glob.glob(os.path.join(os.path.dirname(__file__), "lfs", "*.lfs")))
                    lfsnames = []
                    for f in allfiles:
                        try:
                            open(f, "r").close()
                            lfsnames.append(os.path.basename(f)[:-4])
                        except IOError:
                            pass
                    lfsnames.sort()
                    if len(lfsnames):
                        raise IOError("file '%s' is not available or not readable. Available LaTeX font size files (*.lfs): %s" % (lfsname, lfsnames))
                    else:
                        raise IOError("file '%s' is not available or not readable. No LaTeX font size files (*.lfs) available. Check your installation." % lfsname)
                self.execute(lfsdef)
                self.execute("\\normalsize%\n")
                self.execute("\\newdimen\\linewidth%\n")
            elif self.mode == "latex":
                if self.pyxgraphics:
                    for pyxdef in ["pyx.def",
                                   os.path.join(sys.prefix, "share", "pyx", "pyx.def"),
                                   os.path.join(os.path.dirname(__file__), "..", "contrib", "pyx.def")]:
                        try:
                            open(pyxdef, "r").close()
                            break
                        except IOError:
                            pass
                    else:
                        IOError("file 'pyx.def' is not available or not readable. Check your installation or turn off the pyxgraphics option.")
                    pyxdef = os.path.abspath(pyxdef).replace(os.sep, "/")
                    self.execute("\\makeatletter%\n"
                                 "\\let\\saveProcessOptions=\\ProcessOptions%\n"
                                 "\\def\\ProcessOptions{%\n"
                                 "\\def\\Gin@driver{" + pyxdef + "}%\n"
                                 "\\def\\c@lor@namefile{dvipsnam.def}%\n"
                                 "\\saveProcessOptions}%\n"
                                 "\\makeatother")
                if self.docopt is not None:
                    self.execute("\\documentclass[%s]{%s}" % (self.docopt, self.docclass), *self.texmessagedocclass)
                else:
                    self.execute("\\documentclass{%s}" % self.docclass, *self.texmessagedocclass)
            self.preamblemode = oldpreamblemode
        self.executeid += 1
        if expr is not None: # TeX/LaTeX should process expr
            self.expectqueue.put_nowait("PyXInputMarker:executeid=%i:" % self.executeid)
            if self.preamblemode:
                self.expr = ("%s%%\n" % expr +
                             "\\PyXInput{%i}%%\n" % self.executeid)
            else:
                self.page += 1
                self.expr = ("\\ProcessPyXBox{%s%%\n}{%i}%%\n" % (expr, self.page) +
                             "\\PyXInput{%i}%%\n" % self.executeid)
        else: # TeX/LaTeX should be finished
            self.expectqueue.put_nowait("Transcript written on %s.log" % self.texfilename)
            if self.mode == "latex":
                self.expr = "\\end{document}%\n"
            else:
                self.expr = "\\end%\n"
        if self.texdebug is not None:
            self.texdebug.write(self.expr)
        self.texinput.write(self.expr)
        gotevent = self.waitforevent(self.gotevent)
        self.gotevent.clear()
        if expr is None and gotevent: # TeX/LaTeX should have finished
            self.texruns = 0
            self.texdone = 1
            self.texinput.close()                        # close the input queue and
            gotevent = self.waitforevent(self.quitevent) # wait for finish of the output
        try:
            self.texmessage = ""
            while 1:
                self.texmessage += self.gotqueue.get_nowait()
        except Queue.Empty:
            pass
        self.texmessageparsed = self.texmessage
        if gotevent:
            if expr is not None:
                texmessage.inputmarker.check(self)
                if not self.preamblemode:
                    texmessage.pyxbox.check(self)
                    texmessage.pyxpageout.check(self)
            for check in checks:
                try:
                    check.check(self)
                except TexResultWarning:
                    traceback.print_exc()
            texmessage.emptylines.check(self)
            if len(self.texmessageparsed):
                raise TexResultError("unhandled TeX response (might be an error)", self)
        else:
            raise TexResultError("TeX didn't respond as expected within the timeout period (%i seconds)." % self.waitfortex, self)

    def finishdvi(self):
        """finish TeX/LaTeX and read the dvifile
        - this method ensures that all textboxes can access their
          dvicanvas"""
        self.execute(None, *self.texmessageend)
        if self.dvicopy:
            os.system("dvicopy %(t)s.dvi %(t)s.dvicopy > %(t)s.dvicopyout 2> %(t)s.dvicopyerr" % {"t": self.texfilename})
            dvifilename = "%s.dvicopy" % self.texfilename
        else:
            dvifilename = "%s.dvi" % self.texfilename
        if not self.texipc:
            self.dvifile = dvifile.dvifile(dvifilename, self.fontmap, debug=self.dvidebug)
            for box in self.acttextboxes:
                box.setdvicanvas(self.dvifile.readpage())
        if self.dvifile.readpage() is not None:
            raise RuntimeError("end of dvifile expected")
        self.dvifile = None
        self.acttextboxes = []

    def reset(self, reinit=0):
        "resets the tex runner to its initial state (upto its record to old dvi file(s))"
        if self.texruns:
            self.finishdvi()
        if self.texdebug is not None:
            self.texdebug.write("%s\n%% preparing restart of %s\n" % ("%"*80, self.mode))
        self.executeid = 0
        self.page = 0
        self.texdone = 0
        if reinit:
            self.preamblemode = 1
            for expr, args in self.preambles:
                self.execute(expr, *args)
            if self.mode == "latex":
                self.execute("\\begin{document}", *self.texmessagebegindoc)
            self.preamblemode = 0
        else:
            self.preambles = []
            self.preamblemode = 1

    def set(self, mode=None,
                  lfs=None,
                  docclass=None,
                  docopt=None,
                  usefiles=None,
                  fontmaps=None,
                  waitfortex=None,
                  showwaitfortex=None,
                  texipc=None,
                  texdebug=None,
                  dvidebug=None,
                  errordebug=None,
                  dvicopy=None,
                  pyxgraphics=None,
                  texmessagestart=None,
                  texmessagedocclass=None,
                  texmessagebegindoc=None,
                  texmessageend=None,
                  texmessagedefaultpreamble=None,
                  texmessagedefaultrun=None):
        """provide a set command for TeX/LaTeX settings
        - TeX/LaTeX must not yet been started
        - especially needed for the defaultrunner, where no access to
          the constructor is available"""
        if self.texruns:
            raise TexRunsError
        if mode is not None:
            mode = mode.lower()
            if mode != "tex" and mode != "latex":
                raise ValueError("mode \"TeX\" or \"LaTeX\" expected")
            self.mode = mode
        if lfs is not None:
            self.lfs = lfs
        if docclass is not None:
            self.docclass = docclass
        if docopt is not None:
            self.docopt = docopt
        if usefiles is not None:
            self.usefiles = helper.ensurelist(usefiles)
        if fontmaps is not None:
            self.fontmap = dvifile.readfontmap(fontmaps.split())
        if waitfortex is not None:
            self.waitfortex = waitfortex
        if showwaitfortex is not None:
            self.showwaitfortex = showwaitfortex
        if texipc is not None:
            self.texipc = texipc
        if texdebug is not None:
            if self.texdebug is not None:
                self.texdebug.close()
            if texdebug[-4:] == ".tex":
                self.texdebug = open(texdebug, "w")
            else:
                self.texdebug = open("%s.tex" % texdebug, "w")
        if dvidebug is not None:
            self.dvidebug = dvidebug
        if errordebug is not None:
            self.errordebug = errordebug
        if dvicopy is not None:
            self.dvicopy = dvicopy
        if pyxgraphics is not None:
            self.pyxgraphics = pyxgraphics
        if errordebug is not None:
            self.errordebug = errordebug
        if texmessagestart is not None:
            texmessagestart = helper.ensuresequence(texmessagestart)
            helper.checkattr(texmessagestart, allowmulti=(texmessage,))
            self.texmessagestart = texmessagestart
        if texmessagedocclass is not None:
            texmessagedocclass = helper.ensuresequence(texmessagedocclass)
            helper.checkattr(texmessagedocclass, allowmulti=(texmessage,))
            self.texmessagedocclass = texmessagedocclass
        if texmessagebegindoc is not None:
            texmessagebegindoc = helper.ensuresequence(texmessagebegindoc)
            helper.checkattr(texmessagebegindoc, allowmulti=(texmessage,))
            self.texmessagebegindoc = texmessagebegindoc
        if texmessageend is not None:
            texmessageend = helper.ensuresequence(texmessageend)
            helper.checkattr(texmessageend, allowmulti=(texmessage,))
            self.texmessageend = texmessageend
        if texmessagedefaultpreamble is not None:
            texmessagedefaultpreamble = helper.ensuresequence(texmessagedefaultpreamble)
            helper.checkattr(texmessagedefaultpreamble, allowmulti=(texmessage,))
            self.texmessagedefaultpreamble = texmessagedefaultpreamble
        if texmessagedefaultrun is not None:
            texmessagedefaultrun = helper.ensuresequence(texmessagedefaultrun)
            helper.checkattr(texmessagedefaultrun, allowmulti=(texmessage,))
            self.texmessagedefaultrun = texmessagedefaultrun

    def preamble(self, expr, *args):
        r"""put something into the TeX/LaTeX preamble
        - in LaTeX, this is done before the \begin{document}
          (you might use \AtBeginDocument, when you're in need for)
        - it is not allowed to call preamble after calling the
          text method for the first time (for LaTeX this is needed
          due to \begin{document}; in TeX it is forced for compatibility
          (you should be able to switch from TeX to LaTeX, if you want,
          without breaking something
        - preamble expressions must not create any dvi output
        - args might contain texmessage instances"""
        if self.texdone or not self.preamblemode:
            raise TexNotInPreambleModeError
        helper.checkattr(args, allowmulti=(texmessage,))
        args = helper.getattrs(args, texmessage, default=self.texmessagedefaultpreamble)
        self.execute(expr, *args)
        self.preambles.append((expr, args))

    PyXBoxPattern = re.compile(r"PyXBox:page=(?P<page>\d+),lt=(?P<lt>-?\d*((\d\.?)|(\.?\d))\d*)pt,rt=(?P<rt>-?\d*((\d\.?)|(\.?\d))\d*)pt,ht=(?P<ht>-?\d*((\d\.?)|(\.?\d))\d*)pt,dp=(?P<dp>-?\d*((\d\.?)|(\.?\d))\d*)pt:")

    def text_pt(self, x, y, expr, *args):
        """create text by passing expr to TeX/LaTeX
        - returns a textbox containing the result from running expr thru TeX/LaTeX
        - the box center is set to x, y
        - *args may contain attr parameters, namely:
          - textattr instances
          - texmessage instances
          - trafo._trafo instances
          - style.fillstyle instances"""
        if expr is None:
            raise ValueError("None expression is invalid")
        if self.texdone:
            self.reset(reinit=1)
        first = 0
        if self.preamblemode:
            if self.mode == "latex":
                self.execute("\\begin{document}", *self.texmessagebegindoc)
            self.preamblemode = 0
            first = 1
            if self.texipc and self.dvicopy:
                raise RuntimeError("texipc and dvicopy can't be mixed up")
        helper.checkattr(args, allowmulti=(textattr, texmessage, trafo._trafo, style.fillstyle))
        textattrs = attr.getattrs(args, [textattr])
        textattrs = attr.mergeattrs(textattrs)
        lentextattrs = len(textattrs)
        for i in range(lentextattrs):
            expr = textattrs[lentextattrs-1-i].apply(expr)
        self.execute(expr, *helper.getattrs(args, texmessage, default=self.texmessagedefaultrun))
        if self.texipc:
            if first:
                self.dvifile = dvifile.dvifile("%s.dvi" % self.texfilename, self.fontmap, debug=self.dvidebug)
        match = self.PyXBoxPattern.search(self.texmessage)
        if not match or int(match.group("page")) != self.page:
            raise TexResultError("box extents not found", self)
        left, right, height, depth = map(lambda x: float(x) * 72.0 / 72.27, match.group("lt", "rt", "ht", "dp"))
        box = textbox_pt(x, y, left, right, height, depth, self.finishdvi,
                         *helper.getattrs(args, style.fillstyle, default=[]))
        for t in helper.getattrs(args, trafo._trafo, default=()):
            box.reltransform(t)
        if self.texipc:
            box.setdvicanvas(self.dvifile.readpage())
        self.acttextboxes.append(box)
        return box

    def text(self, x, y, expr, *args):
        return self.text_pt(unit.topt(x), unit.topt(y), expr, *args)


# the module provides an default texrunner and methods for direct access
defaulttexrunner = texrunner()
reset = defaulttexrunner.reset
set = defaulttexrunner.set
preamble = defaulttexrunner.preamble
text = defaulttexrunner.text
text_pt = defaulttexrunner.text_pt

