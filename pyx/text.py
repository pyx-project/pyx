# -*- encoding: utf-8 -*-
#
#
# Copyright (C) 2002-2013 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2003-2011 Michael Schindler <m-schindler@users.sourceforge.net>
# Copyright (C) 2002-2013 André Wobst <wobsta@users.sourceforge.net>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

import atexit, errno, functools, glob, inspect, io, logging, os, threading
import queue, re, shutil, sys, tempfile, time

from pyx import config, unit, box, canvas, trafo, version, attr, style, path
from pyx import bbox as bboxmodule
from pyx.dvi import dvifile

logger = logging.getLogger("pyx")

###############################################################################
# texmessages
# - please don't get confused:
#   - there is a texmessage (and a texmessageparsed) attribute within the
#     texrunner; it contains TeX/LaTeX response from the last command execution
#   - instances of classes derived from the class texmessage are used to
#     parse the TeX/LaTeX response as it is stored in the texmessageparsed
#     attribute of a texrunner instance
#   - the multiple usage of the name texmessage might be removed in the future
###############################################################################

def remove_string(p, s):
    """Removes a string from a string.

    The function removes the first occurrence of a string in another string.

    :param str p: string to be removed
    :param str s: string to be searched
    :returns: tuple of the result string and a success boolean (``True`` when
        the string was removed)
    :rtype: tuple of str and bool

    """
    r = s.replace(p, '', 1)
    return r, r != s


def remove_pattern(p, s, ignore_nl=True):
    """Removes a pattern from a string.

    The function removes the first occurence of the pattern from a string. It
    returns a tuple of the resulting string and the matching object (or
    ``None``, if the pattern did not match).

    :param re.regex p: pattern to be removed
    :param str s: string to be searched
    :param bool ignore_nl: When ``True``, newlines in the string are ignored
        during the pattern search. The returned string will still contain all
        newline characters outside of the matching part of the string, whereas
        the returned matching object will not contain the newline characters
        inside of the matching part of the string.
    :returns: the result string and the match object or ``None`` if
        search failed
    :rtype: tuple of str and (re.match or None)

    """
    if ignore_nl:
        r = s.replace('\n', '')
        has_nl = r != s
    else:
        r = s
        has_nl = False
    m = p.search(r)
    if m:
        s_start = r_start = m.start()
        s_end = r_end = m.end()
        if has_nl:
            j = 0
            for c in s:
                if c == '\n':
                    if j < r_end:
                        s_end += 1
                        if j <= r_start:
                            s_start += 1
                else:
                    j += 1
        return s[:s_start] + s[s_end:], m
    return s, None


class TexResultError(ValueError):
    """specialized texrunner exception class
    - it is raised by texmessage instances, when a texmessage indicates an error
    - it is raised by the texrunner itself, whenever there is a texmessage left
      after all parsing of this message (by texmessage instances)
    prints a detailed report about the problem
    - the verbose level is controlled by texrunner.errordebug"""

    def __init__(self, description, texrunner):
        if texrunner.errordebug >= 2:
            self.description = ("%s\n" % description +
                                #"The expression passed to TeX was:\n"
                                #"  %s\n" % texrunner.expr.replace("\n", "\n  ").rstrip() +
                                "The return message from TeX was:\n"
                                "  %s\n" % texrunner.texmessage.replace("\n", "\n  ").rstrip() +
                                "After parsing this message, the following was left:\n"
                                "  %s" % texrunner.texmessageparsed.replace("\n", "\n  ").rstrip())
        elif texrunner.errordebug == 1:
            firstlines = texrunner.texmessageparsed.split("\n")
            if len(firstlines) > 5:
                firstlines = firstlines[:5] + ["(cut after 5 lines, increase errordebug for more output)"]
            self.description = ("%s\n" % description +
                                #"The expression passed to TeX was:\n"
                                #"  %s\n" % texrunner.expr.replace("\n", "\n  ").rstrip() +
                                "After parsing the return message from TeX, the following was left:\n" +
                                functools.reduce(lambda x, y: "%s  %s\n" % (x,y), firstlines, "").rstrip())
        else:
            self.description = description

    def __str__(self):
        return self.description


class texmessage(attr.attr):

    def check(self, texrunner):
        """check a Tex/LaTeX response and respond appropriate
        - read the texrunners texmessageparsed attribute
        - if there is an problem found, raise TexResultError
        - remove any valid and identified TeX/LaTeX response
          from the texrunners texmessageparsed attribute
          -> finally, there should be nothing left in there,
             otherwise it is interpreted as an error"""
        raise NotImplementedError()


class _texmessagestart(texmessage):
    """validates TeX/LaTeX startup"""

    startpattern = re.compile(r"This is [-0-9a-zA-Z\s_]*TeX")

    def check(self, texrunner):
        # check for "This is e-TeX"
        m = self.startpattern.search(texrunner.texmessageparsed)
        if not m:
            raise TexResultError("TeX startup failed", texrunner)

        # check for \raiseerror -- just to be sure that communication works
        try:
            texrunner.texmessageparsed = texrunner.texmessageparsed.split("*! Undefined control sequence.\n<*> \\raiseerror\n               %\n", 1)[1]
        except (IndexError, ValueError):
            raise TexResultError("TeX batchmode check failed", texrunner)


class _texmessagenofile(texmessage):
    """allows for LaTeXs no-file warning"""

    def __init__(self, fileending):
        self.fileending = fileending

    def check(self, texrunner):
        try:
            s1, s2 = texrunner.texmessageparsed.split("No file texput.%s." % self.fileending, 1)
            texrunner.texmessageparsed = s1 + s2
        except (IndexError, ValueError):
            try:
                s1, s2 = texrunner.texmessageparsed.split("No file %s%stexput.%s." % (os.curdir,
                                                                                      os.sep,
                                                                                      self.fileending), 1)
                texrunner.texmessageparsed = s1 + s2
            except (IndexError, ValueError):
                pass


class _texmessageinputmarker(texmessage):
    """validates the PyXInputMarker"""

    def check(self, texrunner):
        texrunner.texmessageparsed, m = remove_string("PyXInputMarker:executeid=%s:" % texrunner.executeid, texrunner.texmessageparsed)
        if not m:
            raise TexResultError("PyXInputMarker expected", texrunner)


class _texmessagepyxbox(texmessage):
    """validates the PyXBox output"""

    pattern = re.compile(r"PyXBox:page=(?P<page>\d+),lt=-?\d*((\d\.?)|(\.?\d))\d*pt,rt=-?\d*((\d\.?)|(\.?\d))\d*pt,ht=-?\d*((\d\.?)|(\.?\d))\d*pt,dp=-?\d*((\d\.?)|(\.?\d))\d*pt:")

    def check(self, texrunner):
        texrunner.texmessageparsed, m = remove_pattern(self.pattern, texrunner.texmessageparsed, ignore_nl=False)
        if not m:
            raise TexResultError("PyXBox expected", texrunner)
        if m.group("page") != str(texrunner.page):
            raise TexResultError("Wrong page number in PyXBox", texrunner)


class _texmessagepyxpageout(texmessage):
    """validates the dvi shipout message (writing a page to the dvi file)"""

    def check(self, texrunner):
        texrunner.texmessageparsed, m = remove_string("[80.121.88.%s]" % texrunner.page, texrunner.texmessageparsed)
        if not m:
            raise TexResultError("PyXPageOutMarker expected", texrunner)


class _texmessageend(texmessage):
    """validates TeX/LaTeX finish"""

    auxPattern = re.compile(r"\(([^()]+\.aux|\"[^\"]+\.aux\")\)")
    dviPattern = re.compile(r"Output written on .*texput\.dvi \((?P<page>\d+) pages?, \d+ bytes\)\.")
    logPattern = re.compile(r"Transcript written on .*texput\.log\.")

    def check(self, texrunner):
        texrunner.texmessageparsed, m = remove_pattern(self.auxPattern, texrunner.texmessageparsed, ignore_nl=False)
        texrunner.texmessageparsed, m = remove_string("(see the transcript file for additional information)", texrunner.texmessageparsed)

        # check for "Output written on ...dvi (1 page, 220 bytes)."
        if texrunner.page:
            texrunner.texmessageparsed, m = remove_pattern(self.dviPattern, texrunner.texmessageparsed)
            if not m:
                raise TexResultError("TeX dvifile messages expected", texrunner)
            if m.group("page") != str(texrunner.page):
                raise TexResultError("wrong number of pages reported", texrunner)
        else:
            texrunner.texmessageparsed, m = remove_string("No pages of output.", texrunner.texmessageparsed)
            if not m:
                raise TexResultError("no dvifile expected", texrunner)

        # check for "Transcript written on ...log."
        texrunner.texmessageparsed, m = remove_pattern(self.logPattern, texrunner.texmessageparsed)
        if not m:
            raise TexResultError("TeX logfile message expected", texrunner)


class _texmessageemptylines(texmessage):
    """validates "*-only" (TeX/LaTeX input marker in interactive mode) and empty lines
    also clear TeX interactive mode warning (Please type a command or say `\\end')
    """

    def check(self, texrunner):
        texrunner.texmessageparsed = (texrunner.texmessageparsed.replace(r"(Please type a command or say `\end')", "")
                                                                .replace(" ", "")
                                                                .replace("*\n", "")
                                                                .replace("\n", ""))


class _texmessageload(texmessage):
    """validates inclusion of arbitrary files
    - the matched pattern is "(<filename> <arbitrary other stuff>)", where
      <filename> is a readable file and other stuff can be anything
    - If the filename is enclosed in double quotes, it may contain blank space.
    - "(" and ")" must be used consistent (otherwise this validator just does nothing)
    - this is not always wanted, but we just assume that file inclusion is fine"""

    pattern = re.compile(r"\([\"]?(?P<filename>(?:(?<!\")[^()\s\n]+(?!\"))|[^\"\n]+)[\"]?(?P<additional>[^()]*)\)")

    def baselevels(self, s, maxlevel=1, brackets="()", quotes='""'):
        """strip parts of a string above a given bracket level
        - return a modified (some parts might be removed) version of the string s
          where all parts inside brackets with level higher than maxlevel are
          removed
        - if brackets do not match (number of left and right brackets is wrong
          or at some points there were more right brackets than left brackets)
          just return the unmodified string
        - a quoted string immediately followed after a bracket is left untouched
          even if it contains quotes itself"""
        level = 0
        highestlevel = 0
        inquote = 0
        res = ""
        for i, c in enumerate(s):
            if quotes and level <= maxlevel:
                if not inquote and c == quotes[0] and i and s[i-1] == brackets[0]:
                    inquote = True
                elif inquote and c == quotes[1]:
                    inquote = False
            if inquote:
                res += c
            else:
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
        search = self.baselevels(texrunner.texmessageparsed)
        res = []
        if search is not None:
            m = self.pattern.search(search)
            while m:
                filename = m.group("filename").replace("\n", "")
                try:
                    additional = m.group("additional")
                except IndexError:
                    additional = ""
                if (os.access(filename, os.R_OK) or
                    len(additional) and additional[0] == "\n" and os.access(filename+additional.split()[0], os.R_OK)):
                    res.append(search[:m.start()])
                else:
                    res.append(search[:m.end()])
                search = search[m.end():]
                m = self.pattern.search(search)
            else:
                res.append(search)
                texrunner.texmessageparsed = "".join(res)


class _texmessageloaddef(_texmessageload):
    """validates the inclusion of font description files (fd-files)
    - works like _texmessageload
    - filename must end with .def or .fd
    - further text is allowed"""

    pattern = re.compile(r"\([\"]?(?P<filename>(?:(?:(?<!\")[^\(\)\s\n\"]+)|(?:(?<=\")[^\(\)\"]+))(\.fd|\.def))[\"]?[\s\n]*(?P<additional>[\(]?[^\(\)]*[\)]?)[\s\n]*\)")

    def baselevels(self, s, **kwargs):
        return s


class _texmessagegraphicsload(_texmessageload):
    """validates the inclusion of files as the graphics packages writes it
    - works like _texmessageload, but using "<" and ">" as delimiters
    - filename must end with .eps and no further text is allowed"""

    pattern = re.compile(r"<(?P<filename>[^>]+.eps)>")

    def baselevels(self, s, **kwargs):
        return s


class _texmessageignore(_texmessageload):
    """validates any TeX/LaTeX response
    - this might be used, when the expression is ok, but no suitable texmessage
      parser is available
    - PLEASE: - consider writing suitable tex message parsers
              - share your ideas/problems/solutions with others (use the PyX mailing lists)"""

    def check(self, texrunner):
        texrunner.texmessageparsed = ""


texmessage.start = _texmessagestart()
texmessage.noaux = _texmessagenofile("aux")
texmessage.nonav = _texmessagenofile("nav")
texmessage.end = _texmessageend()
texmessage.load = _texmessageload()
texmessage.loaddef = _texmessageloaddef()
texmessage.graphicsload = _texmessagegraphicsload()
texmessage.ignore = _texmessageignore()

# for internal use:
texmessage.inputmarker = _texmessageinputmarker()
texmessage.pyxbox = _texmessagepyxbox()
texmessage.pyxpageout = _texmessagepyxpageout()
texmessage.emptylines = _texmessageemptylines()


class _texmessageallwarning(texmessage):
    """validates a given pattern 'pattern' as a warning 'warning'"""

    def check(self, texrunner):
        if texrunner.texmessageparsed:
            logger.info("ignoring all warnings:\n%s" % texrunner.texmessageparsed)
        texrunner.texmessageparsed = ""

texmessage.allwarning = _texmessageallwarning()


class texmessagepattern(texmessage):
    """validates a given pattern"""

    def __init__(self, pattern, description=None):
        self.pattern = pattern
        self.description = description

    def check(self, texrunner):
        m = self.pattern.search(texrunner.texmessageparsed)
        while m:
            texrunner.texmessageparsed = texrunner.texmessageparsed[:m.start()] + texrunner.texmessageparsed[m.end():]
            if self.description:
                logger.warning("ignoring %s:\n%s" % (self.description, m.string[m.start(): m.end()].rstrip()))
            else:
                logger.info("ignoring matched pattern:\n%s" % (m.string[m.start(): m.end()].rstrip()))
            m = self.pattern.search(texrunner.texmessageparsed)

texmessage.fontwarning = texmessagepattern(re.compile(r"^LaTeX Font Warning: .*$(\n^\(Font\).*$)*", re.MULTILINE), "font warning")
texmessage.boxwarning = texmessagepattern(re.compile(r"^(Overfull|Underfull) \\[hv]box.*$(\n^..*$)*\n^$\n", re.MULTILINE), "overfull/underfull box warning")
texmessage.rerunwarning = texmessagepattern(re.compile(r"^(LaTeX Warning: Label\(s\) may have changed\. Rerun to get cross-references right\s*\.)$", re.MULTILINE), "rerun warning")
texmessage.packagewarning = texmessagepattern(re.compile(r"^package\s+(?P<packagename>\S+)\s+warning\s*:[^\n]+(?:\n\(?(?P=packagename)\)?[^\n]*)*", re.MULTILINE | re.IGNORECASE), "generic package warning")
texmessage.nobblwarning = texmessagepattern(re.compile(r"^[\s\*]*(No file .*\.bbl.)\s*", re.MULTILINE), "no-bbl warning")



###############################################################################
# textattrs
###############################################################################

_textattrspreamble = ""

class textattr:
    "a textattr defines a apply method, which modifies a (La)TeX expression"

class _localattr: pass

_textattrspreamble += r"""\gdef\PyXFlushHAlign{0}%
\def\PyXragged{%
\leftskip=0pt plus \PyXFlushHAlign fil%
\rightskip=0pt plus 1fil%
\advance\rightskip0pt plus -\PyXFlushHAlign fil%
\parfillskip=0pt%
\pretolerance=9999%
\tolerance=9999%
\parindent=0pt%
\hyphenpenalty=9999%
\exhyphenpenalty=9999}%
"""

class boxhalign(attr.exclusiveattr, textattr, _localattr):

    def __init__(self, aboxhalign):
        self.boxhalign = aboxhalign
        attr.exclusiveattr.__init__(self, boxhalign)

    def apply(self, expr):
        return r"\gdef\PyXBoxHAlign{%.5f}%s" % (self.boxhalign, expr)

boxhalign.left = boxhalign(0)
boxhalign.center = boxhalign(0.5)
boxhalign.right = boxhalign(1)
# boxhalign.clear = attr.clearclass(boxhalign) # we can't defined a clearclass for boxhalign since it can't clear a halign's boxhalign


class flushhalign(attr.exclusiveattr, textattr, _localattr):

    def __init__(self, aflushhalign):
        self.flushhalign = aflushhalign
        attr.exclusiveattr.__init__(self, flushhalign)

    def apply(self, expr):
        return r"\gdef\PyXFlushHAlign{%.5f}\PyXragged{}%s" % (self.flushhalign, expr)

flushhalign.left = flushhalign(0)
flushhalign.center = flushhalign(0.5)
flushhalign.right = flushhalign(1)
# flushhalign.clear = attr.clearclass(flushhalign) # we can't defined a clearclass for flushhalign since it couldn't clear a halign's flushhalign


class halign(boxhalign, flushhalign, _localattr):

    def __init__(self, aboxhalign, aflushhalign):
        self.boxhalign = aboxhalign
        self.flushhalign = aflushhalign
        attr.exclusiveattr.__init__(self, halign)

    def apply(self, expr):
        return r"\gdef\PyXBoxHAlign{%.5f}\gdef\PyXFlushHAlign{%.5f}\PyXragged{}%s" % (self.boxhalign, self.flushhalign, expr)

halign.left = halign(0, 0)
halign.center = halign(0.5, 0.5)
halign.right = halign(1, 1)
halign.clear = attr.clearclass(halign)
halign.boxleft = boxhalign.left
halign.boxcenter = boxhalign.center
halign.boxright = boxhalign.right
halign.flushleft = halign.raggedright = flushhalign.left
halign.flushcenter = halign.raggedcenter = flushhalign.center
halign.flushright = halign.raggedleft = flushhalign.right


class _mathmode(attr.attr, textattr, _localattr):
    "math mode"

    def apply(self, expr):
        return r"$\displaystyle{%s}$" % expr

mathmode = _mathmode()
clearmathmode = attr.clearclass(_mathmode)


class _phantom(attr.attr, textattr, _localattr):
    "phantom text"

    def apply(self, expr):
        return r"\phantom{%s}" % expr

phantom = _phantom()
clearphantom = attr.clearclass(_phantom)


_textattrspreamble += "\\newbox\\PyXBoxVBox%\n\\newdimen\\PyXDimenVBox%\n"

class parbox_pt(attr.sortbeforeexclusiveattr, textattr):

    top = 1
    middle = 2
    bottom = 3

    def __init__(self, width, baseline=top):
        self.width = width * 72.27 / (unit.scale["x"] * 72)
        self.baseline = baseline
        attr.sortbeforeexclusiveattr.__init__(self, parbox_pt, [_localattr])

    def apply(self, expr):
        if self.baseline == self.top:
            return r"\linewidth=%.5ftruept\vtop{\hsize=\linewidth\textwidth=\linewidth{}%s}" % (self.width, expr)
        elif self.baseline == self.middle:
            return r"\linewidth=%.5ftruept\setbox\PyXBoxVBox=\hbox{{\vtop{\hsize=\linewidth\textwidth=\linewidth{}%s}}}\PyXDimenVBox=0.5\dp\PyXBoxVBox\setbox\PyXBoxVBox=\hbox{{\vbox{\hsize=\linewidth\textwidth=\linewidth{}%s}}}\advance\PyXDimenVBox by -0.5\dp\PyXBoxVBox\lower\PyXDimenVBox\box\PyXBoxVBox" % (self.width, expr, expr)
        elif self.baseline == self.bottom:
            return r"\linewidth=%.5ftruept\vbox{\hsize=\linewidth\textwidth=\linewidth{}%s}" % (self.width, expr)
        else:
            ValueError("invalid baseline argument")

parbox_pt.clear = attr.clearclass(parbox_pt)

class parbox(parbox_pt):

    def __init__(self, width, **kwargs):
        parbox_pt.__init__(self, unit.topt(width), **kwargs)

parbox.clear = parbox_pt.clear


_textattrspreamble += "\\newbox\\PyXBoxVAlign%\n\\newdimen\\PyXDimenVAlign%\n"

class valign(attr.sortbeforeexclusiveattr, textattr):

    def __init__(self, avalign):
        self.valign = avalign
        attr.sortbeforeexclusiveattr.__init__(self, valign, [parbox_pt, _localattr])

    def apply(self, expr):
        return r"\setbox\PyXBoxVAlign=\hbox{{%s}}\PyXDimenVAlign=%.5f\ht\PyXBoxVAlign\advance\PyXDimenVAlign by -%.5f\dp\PyXBoxVAlign\lower\PyXDimenVAlign\box\PyXBoxVAlign" % (expr, 1-self.valign, self.valign)

valign.top = valign(0)
valign.middle = valign(0.5)
valign.bottom = valign(1)
valign.clear = valign.baseline = attr.clearclass(valign)


_textattrspreamble += "\\newdimen\\PyXDimenVShift%\n"

class _vshift(attr.sortbeforeattr, textattr):

    def __init__(self):
        attr.sortbeforeattr.__init__(self, [valign, parbox_pt, _localattr])

    def apply(self, expr):
        return r"%s\setbox0\hbox{{%s}}\lower\PyXDimenVShift\box0" % (self.setheightexpr(), expr)

class vshift(_vshift):
    "vertical down shift by a fraction of a character height"

    def __init__(self, lowerratio, heightstr="0"):
        _vshift.__init__(self)
        self.lowerratio = lowerratio
        self.heightstr = heightstr

    def setheightexpr(self):
        return r"\setbox0\hbox{{%s}}\PyXDimenVShift=%.5f\ht0" % (self.heightstr, self.lowerratio)

class _vshiftmathaxis(_vshift):
    "vertical down shift by the height of the math axis"

    def setheightexpr(self):
        return r"\setbox0\hbox{$\vcenter{\vrule width0pt}$}\PyXDimenVShift=\ht0"


vshift.bottomzero = vshift(0)
vshift.middlezero = vshift(0.5)
vshift.topzero = vshift(1)
vshift.mathaxis = _vshiftmathaxis()
vshift.clear = attr.clearclass(_vshift)


defaultsizelist = ["normalsize", "large", "Large", "LARGE", "huge", "Huge",
None, "tiny", "scriptsize", "footnotesize", "small"]

class size(attr.sortbeforeattr, textattr):
    "font size"

    def __init__(self, sizeindex=None, sizename=None, sizelist=defaultsizelist):
        if (sizeindex is None and sizename is None) or (sizeindex is not None and sizename is not None):
            raise ValueError("either specify sizeindex or sizename")
        attr.sortbeforeattr.__init__(self, [_mathmode, _vshift])
        if sizeindex is not None:
            if sizeindex >= 0 and sizeindex < sizelist.index(None):
                self.size = sizelist[sizeindex]
            elif sizeindex < 0 and sizeindex + len(sizelist) > sizelist.index(None):
                self.size = sizelist[sizeindex]
            else:
                raise IndexError("index out of sizelist range")
        else:
            self.size = sizename

    def apply(self, expr):
        return r"\%s{}%s" % (self.size, expr)

size.tiny = size(-4)
size.scriptsize = size.script = size(-3)
size.footnotesize = size.footnote = size(-2)
size.small = size(-1)
size.normalsize = size.normal = size(0)
size.large = size(1)
size.Large = size(2)
size.LARGE = size(3)
size.huge = size(4)
size.Huge = size(5)
size.clear = attr.clearclass(size)


###############################################################################
# texrunner
###############################################################################


class MonitorOutput(threading.Thread):

    def __init__(self, name, output):
        """Deadlock-safe output stream reader and monitor.

        This method sets up a thread to continously read lines from a stream.
        By that a deadlock due to a full pipe is prevented. In addition, the
        stream content can be monitored for containing a certain string (see
        :meth:`expect` and :meth:`wait`) and return all the collected output
        (see :meth:`read`).

        :param string name: name to be used while logging in :meth:`wait` and
            :meth:`done`
        :param file output: output stream

        """
        self.output = output
        self._expect = queue.Queue(1)
        self._received = threading.Event()
        self._output = queue.Queue()
        threading.Thread.__init__(self, name=name, daemon=1)
        self.start()

    def expect(self, s):
        """Expect a string on a *single* line in the output.

        This method must be called *before* the output occurs, i.e. before
        the input is written to the TeX/LaTeX process.

        :param s: expected string or ``None`` if output is expected to become
            empty
        :type s: str or None

        """
        self._expect.put_nowait(s)

    def read(self):
        """Read all output collected since its previous call.

        The output reading should be synchronized by the :meth:`expect`
        and :meth:`wait` methods.

        :returns: collected output from the stream
        :rtype: str

        """
        l = []
        try:
            while True:
                l.append(self._output.get_nowait())
        except queue.Empty:
            pass
        return "".join(l).replace("\r\n", "\n").replace("\r", "\n")

    def _wait(self, waiter, checker):
        """Helper method to implement :meth:`wait` and :meth:`done`.

        Waits for an event using the *waiter* and *checker* functions while
        providing user feedback to the ``pyx``-logger using the warning level
        according to the ``wait`` and ``showwait`` from the ``text`` section of
        the pyx :mod:`config`.

        :param function waiter: callback to wait for (the function gets called
            with a timeout parameter)
        :param function checker: callback returing ``True`` if
            waiting was successful
        :returns: ``True`` when wait was successful
        :rtype: bool

        """
        wait = config.getint("text", "wait", 60)
        showwait = config.getint("text", "showwait", 5)
        if showwait:
            waited = 0
            hasevent = False
            while waited < wait and not hasevent:
                if wait - waited > showwait:
                    waiter(showwait)
                    waited += showwait
                else:
                    waiter(wait - waited)
                    waited += wait - waited
                hasevent = checker()
                if not hasevent:
                    if waited < wait:
                        logger.warning("Still waiting for {} "
                                       "after {} (of {}) seconds..."
                                       .format(self.name, waited, wait))
                    else:
                        logger.warning("The timeout of {} seconds expired "
                                       "and {} did not respond."
                                       .format(waited, self.name))
            return hasevent
        else:
            waiter(wait)
            return checker()

    def wait(self):
        """Wait for the expected output to happen.

        Waits either until a line containing the string set by the previous
        :meth:`expect` call is found, or a timeout occurs.

        :returns: ``True`` when the expected string was found
        :rtype: bool

        """
        r = self._wait(self._received.wait, self._received.isSet)
        if r:
            self._received.clear()
        return r

    def done(self):
        """Waits until the output becomes empty.

        Waits either until the output becomes empty, or a timeout occurs.
        The generated output can still be catched by :meth:`read` after
        :meth:`done` was successful.

        In the proper workflow :meth:`expect` should be called with ``None``
        before the output completes, as otherwise a ``ValueError`` is raised
        in the :meth:`run`.

        :returns: ``True`` when the output has become empty
        :rtype: bool

        """
        return self._wait(self.join, lambda self=self: not self.is_alive())

    def _readline(self):
        """Read a line from the output.

        To be used **inside** the thread routine only.

        :returns: one line of the output as a string
        :rtype: str

        """
        while True:
            try:
                return self.output.readline()
            except IOError as e:
                if e.errno != errno.EINTR:
                     raise

    def run(self):
        """Thread routine.

        **Not** to be called from outside.

        :raises ValueError: output becomes empty while some string is expected

        """
        expect = None
        while True:
            line = self._readline()
            if expect is None:
                try:
                    expect = self._expect.get_nowait()
                except queue.Empty:
                    pass
            if not line:
                break
            self._output.put(line)
            if expect is not None:
                found = line.find(expect)
                if found != -1:
                    self._received.set()
                    expect = None
        self.output.close()
        if expect is not None:
            raise ValueError("{} finished unexpectedly".format(self.name))


class textbox(box.rect, canvas.canvas):
    """basically a box.rect, but it contains a text created by the texrunner
    - texrunner._text and texrunner.text return such an object
    - _textbox instances can be inserted into a canvas
    - the output is contained in a page of the dvifile available thru the texrunner"""
    # TODO: shouldn't all boxes become canvases? how about inserts then?

    def __init__(self, x, y, left, right, height, depth, finishdvi, attrs):
        """
        - finishdvi is a method to be called to get the dvicanvas
          (e.g. the finishdvi calls the setdvicanvas method)
        - attrs are fillstyles"""
        self.left = left
        self.right = right
        self.width = left + right
        self.height = height
        self.depth = depth
        self.texttrafo = trafo.scale(unit.scale["x"]).translated(x, y)
        box.rect.__init__(self, x - left, y - depth, left + right, depth + height, abscenter = (left, depth))
        canvas.canvas.__init__(self, attrs)
        self.finishdvi = finishdvi
        self.dvicanvas = None
        self.insertdvicanvas = False

    def transform(self, *trafos):
        if self.insertdvicanvas:
            raise ValueError("can't apply transformation after dvicanvas was inserted")
        box.rect.transform(self, *trafos)
        for trafo in trafos:
            self.texttrafo = trafo * self.texttrafo

    def setdvicanvas(self, dvicanvas):
        if self.dvicanvas is not None:
            raise ValueError("multiple call to setdvicanvas")
        self.dvicanvas = dvicanvas

    def ensuredvicanvas(self):
        if self.dvicanvas is None:
            self.finishdvi()
            assert self.dvicanvas is not None, "finishdvi is broken"
        if not self.insertdvicanvas:
            self.insert(self.dvicanvas, [self.texttrafo])
            self.insertdvicanvas = True

    def marker(self, marker):
        self.ensuredvicanvas()
        return self.texttrafo.apply(*self.dvicanvas.markers[marker])

    def textpath(self):
        self.ensuredvicanvas()
        textpath = path.path()
        for item in self.dvicanvas.items:
            try:
                textpath += item.textpath()
            except AttributeError:
                # ignore color settings etc.
                pass
        return textpath.transformed(self.texttrafo)

    def processPS(self, file, writer, context, registry, bbox):
        self.ensuredvicanvas()
        abbox = bboxmodule.empty()
        canvas.canvas.processPS(self, file, writer, context, registry, abbox)
        bbox += box.rect.bbox(self)

    def processPDF(self, file, writer, context, registry, bbox):
        self.ensuredvicanvas()
        abbox = bboxmodule.empty()
        canvas.canvas.processPDF(self, file, writer, context, registry, abbox)
        bbox += box.rect.bbox(self)


class _marker:
    pass


class Tee(object):

    def __init__(self, *files):
        self.files = files

    def write(self, data):
        for file in self.files:
            file.write(data)

    def flush(self):
        for file in self.files:
            file.flush()

    def close(self):
        for file in self.files:
            file.close()

# The texrunner state represents the next (or current) execute state.
STATE_START, STATE_PREAMBLE, STATE_TYPESET, STATE_DONE = range(4)

class _texrunner:
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

    defaulttexmessagesstart = [texmessage.start]
    defaulttexmessagesend = [texmessage.end, texmessage.fontwarning, texmessage.rerunwarning, texmessage.nobblwarning]
    defaulttexmessagesdefaultpreamble = [texmessage.load]
    defaulttexmessagesdefaultrun = [texmessage.loaddef, texmessage.graphicsload,
                                    texmessage.fontwarning, texmessage.boxwarning, texmessage.packagewarning]

    def __init__(self, executable,
                       texenc="ascii",
                       usefiles=[],
                       texipc=config.getboolean("text", "texipc", 0),
                       texdebug=None,
                       dvidebug=0,
                       errordebug=1,
                       texmessagesstart=[],
                       texmessagesend=[],
                       texmessagesdefaultpreamble=[],
                       texmessagesdefaultrun=[]):
        self.executable = executable
        self.texenc = texenc
        self.usefiles = usefiles
        self.texipc = texipc
        self.texdebug = texdebug
        self.dvidebug = dvidebug
        self.errordebug = errordebug
        self.texmessagesstart = texmessagesstart
        self.texmessagesend = texmessagesend
        self.texmessagesdefaultpreamble = texmessagesdefaultpreamble
        self.texmessagesdefaultrun = texmessagesdefaultrun

        self.state = STATE_START
        self.executeid = 0
        self.page = 0
        self.preambles = []
        self.needdvitextboxes = [] # when texipc-mode off
        self.dvifile = None
        self.textboxesincluded = 0

        self.tempdir = tempfile.mkdtemp()
        atexit.register(self.cleanup)

    def cleanup(self):
        """get rid of temporary files
        - function to be registered by atexit
        - files contained in usefiles are kept"""
        try:
            if self.state > STATE_START:
                if self.state < STATE_DONE:
                    self.finishdvi()
                    if self.state < STATE_DONE: # cleanup while TeX is still running?
                        self.texoutput.expect(None)
                        self.force_done()
                        self.texinput.close()
                        if self.texoutput.done():
                            logger.warn("Failed to force a quit of %s in clean-up function.".format(self.name))
                for usefile in self.usefiles:
                    extpos = usefile.rfind(".")
                    try:
                        os.rename(os.path.join(self.tempdir, "texput" + usefile[extpos:]), usefile)
                    except EnvironmentError:
                        logger.warn("Could not save '{}'.".format(usefile))
                        if os.path.isfile(usefile):
                            try:
                                os.unlink(usefile)
                            except EnvironmentError:
                                logger.warn("Failed to remove spurious file '{}'.".format(usefile))
        finally:
            shutil.rmtree(self.tempdir, ignore_errors=True)


    def execute(self, expr, texmessages, oldstate, newstate):
        """executes expr within TeX/LaTeX
        - when self.preamblemode is set, the expr is passed directly to TeX/LaTeX
        - when self.preamblemode is unset, the expr is passed to \ProcessPyXBox
        - texmessages is a list of texmessage instances"""
        assert STATE_PREAMBLE <= oldstate <= STATE_TYPESET
        assert oldstate == self.state
        assert newstate >= oldstate
        if newstate == STATE_DONE:
            self.texoutput.expect(None)
            self.texinput.write(expr)
        else:
            if oldstate == newstate == STATE_TYPESET:
                self.page += 1
                expr = "\\ProcessPyXBox{%s%%\n}{%i}" % (expr, self.page)
            self.executeid += 1
            self.texoutput.expect("PyXInputMarker:executeid=%i:" % self.executeid)
            self.texinput.write(expr + "%%\n\\PyXInput{%i}%%\n" % self.executeid)
        self.texinput.flush()
        self.state = newstate
        if newstate == STATE_DONE:
            wait_ok = self.texoutput.done()
        else:
            wait_ok = self.texoutput.wait()
        self.texmessage = self.texoutput.read()
        self.texmessageparsed = self.texmessage
        if wait_ok:
            if newstate != STATE_DONE:
                texmessage.inputmarker.check(self)
                if oldstate == newstate == STATE_TYPESET:
                    texmessage.pyxbox.check(self)
                    texmessage.pyxpageout.check(self)
            texmessages = attr.mergeattrs(texmessages)
            for t in texmessages:
                t.check(self)
            keeptexmessageparsed = self.texmessageparsed
            texmessage.emptylines.check(self)
            if len(self.texmessageparsed):
                self.texmessageparsed = keeptexmessageparsed
                raise TexResultError("unhandled TeX response (might be an error)", self)
        else:
            raise TexResultError("TeX didn't respond as expected within the timeout period.", self)

    def do_start(self):
        assert self.state == STATE_START
        self.state = STATE_PREAMBLE

        for usefile in self.usefiles:
            extpos = usefile.rfind(".")
            try:
                os.rename(usefile, os.path.join(self.tempdir, "texput" + usefile[extpos:]))
            except OSError:
                pass
        cmd = [self.executable, '--output-directory', self.tempdir]
        if self.texipc:
            cmd.append("--ipc")
        pipes = config.Popen(cmd, stdin=config.PIPE, stdout=config.PIPE, stderr=config.STDOUT, bufsize=0)
        self.texinput = io.TextIOWrapper(pipes.stdin, encoding=self.texenc)
        if self.texdebug:
            try:
                self.texdebug.write
            except AttributeError:
                self.texinput = Tee(open(self.texdebug, "w", encoding=self.texenc), self.texinput)
            else:
                self.texinput = Tee(self.texdebug, self.texinput)
        self.texoutput = MonitorOutput(self.name, io.TextIOWrapper(pipes.stdout, encoding=self.texenc))
        self.execute("\\scrollmode\n\\raiseerror%\n" # switch to and check scrollmode
                     "\\def\\PyX{P\\kern-.3em\\lower.5ex\hbox{Y}\kern-.18em X}%\n" # just the PyX Logo
                     "\\gdef\\PyXBoxHAlign{0}%\n" # global PyXBoxHAlign (0.0-1.0) for the horizontal alignment, default to 0
                     "\\newbox\\PyXBox%\n" # PyXBox will contain the output
                     "\\newbox\\PyXBoxHAligned%\n" # PyXBox will contain the horizontal aligned output
                     "\\newdimen\\PyXDimenHAlignLT%\n" # PyXDimenHAlignLT/RT will contain the left/right extent
                     "\\newdimen\\PyXDimenHAlignRT%\n" +
                     _textattrspreamble + # insert preambles for textattrs macros
                     "\\long\\def\\ProcessPyXBox#1#2{%\n" # the ProcessPyXBox definition (#1 is expr, #2 is page number)
                     "\\setbox\\PyXBox=\\hbox{{#1}}%\n" # push expression into PyXBox
                     "\\PyXDimenHAlignLT=\\PyXBoxHAlign\\wd\\PyXBox%\n" # calculate the left/right extent
                     "\\PyXDimenHAlignRT=\\wd\\PyXBox%\n"
                     "\\advance\\PyXDimenHAlignRT by -\\PyXDimenHAlignLT%\n"
                     "\\gdef\\PyXBoxHAlign{0}%\n" # reset the PyXBoxHAlign to the default 0
                     "\\immediate\\write16{PyXBox:page=#2," # write page and extents of this box to stdout
                                                 "lt=\\the\\PyXDimenHAlignLT,"
                                                 "rt=\\the\\PyXDimenHAlignRT,"
                                                 "ht=\\the\\ht\\PyXBox,"
                                                 "dp=\\the\\dp\\PyXBox:}%\n"
                     "\\setbox\\PyXBoxHAligned=\\hbox{\\kern-\\PyXDimenHAlignLT\\box\\PyXBox}%\n" # align horizontally
                     "\\ht\\PyXBoxHAligned0pt%\n" # baseline alignment (hight to zero)
                     "{\\count0=80\\count1=121\\count2=88\\count3=#2\\shipout\\box\\PyXBoxHAligned}}%\n" # shipout PyXBox to Page 80.121.88.<page number>
                     "\\def\\PyXInput#1{\\immediate\\write16{PyXInputMarker:executeid=#1:}}%\n" # write PyXInputMarker to stdout
                     "\\def\\PyXMarker#1{\\hskip0pt\\special{PyX:marker #1}}%", # write PyXMarker special into the dvi-file
                     self.defaulttexmessagesstart + self.texmessagesstart, STATE_PREAMBLE, STATE_PREAMBLE)

    def do_preamble(self, expr, texmessages):
        if self.state < STATE_PREAMBLE:
            self.do_start()
        self.execute(expr, texmessages, STATE_PREAMBLE, STATE_PREAMBLE)

    def do_typeset(self, expr, texmessages):
        if self.state < STATE_PREAMBLE:
            self.do_start()
        if self.state < STATE_TYPESET:
            self.go_typeset()
        self.execute(expr, texmessages, STATE_TYPESET, STATE_TYPESET)

    def do_finish(self):
        assert self.state < STATE_DONE
        self.go_finish()
        self.texinput.close()            # close the input queue and
        self.texoutput.done()            # wait for finish of the output

    def finishdvi(self):
        """finish TeX/LaTeX and read the dvifile
        - this method ensures that all textboxes can access their
          dvicanvas"""
        if self.state < STATE_TYPESET:
            self.go_typeset()
        self.do_finish()
        dvifilename = os.path.join(self.tempdir, "texput.dvi")
        if not self.texipc:
            self.dvifile = dvifile.DVIfile(dvifilename, debug=self.dvidebug)
            page = 1
            for box in self.needdvitextboxes:
                box.setdvicanvas(self.dvifile.readpage([ord("P"), ord("y"), ord("X"), page, 0, 0, 0, 0, 0, 0], fontmap=box.fontmap, singlecharmode=box.singlecharmode))
                page += 1
        if self.dvifile.readpage(None) is not None:
            raise ValueError("end of dvifile expected but further pages follow")
        self.dvifile = None
        self.needdvitextboxes = []

    def reset(self, reinit=0):
        "resets the tex runner to its initial state (upto its record to old dvi file(s))"
        if self.state < STATE_DONE:
            self.finishdvi()
        self.executeid = 0
        self.page = 0
        self.state = STATE_START
        if reinit:
            for expr, texmessages in self.preambles:
                self.do_preamble(expr, texmessages)
        else:
            self.preambles = []

    def preamble(self, expr, texmessages=[]):
        r"""put something into the TeX/LaTeX preamble
        - in LaTeX, this is done before the \begin{document}
          (you might use \AtBeginDocument, when you're in need for)
        - it is not allowed to call preamble after calling the
          text method for the first time (for LaTeX this is needed
          due to \begin{document}; in TeX it is forced for compatibility
          (you should be able to switch from TeX to LaTeX, if you want,
          without breaking something)
        - preamble expressions must not create any dvi output
        - args might contain texmessage instances"""
        if self.state > STATE_PREAMBLE:
            raise ValueError("preamble calls disabled due to previous text calls")
        texmessages = self.defaulttexmessagesdefaultpreamble + self.texmessagesdefaultpreamble + texmessages
        self.preambles.append((expr, texmessages))
        self.do_preamble(expr, texmessages)

    PyXBoxPattern = re.compile(r"PyXBox:page=(?P<page>\d+),lt=(?P<lt>-?\d*((\d\.?)|(\.?\d))\d*)pt,rt=(?P<rt>-?\d*((\d\.?)|(\.?\d))\d*)pt,ht=(?P<ht>-?\d*((\d\.?)|(\.?\d))\d*)pt,dp=(?P<dp>-?\d*((\d\.?)|(\.?\d))\d*)pt:")

    def text(self, x, y, expr, textattrs=[], texmessages=[], fontmap=None, singlecharmode=False):
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
        if self.state == STATE_DONE:
            self.reset(reinit=1)
        first = self.state < STATE_TYPESET
        textattrs = attr.mergeattrs(textattrs) # perform cleans
        attr.checkattrs(textattrs, [textattr, trafo.trafo_pt, style.fillstyle])
        trafos = attr.getattrs(textattrs, [trafo.trafo_pt])
        fillstyles = attr.getattrs(textattrs, [style.fillstyle])
        textattrs = attr.getattrs(textattrs, [textattr])
        for ta in textattrs[::-1]:
            expr = ta.apply(expr)
        try:
            self.do_typeset(expr, self.defaulttexmessagesdefaultrun + self.texmessagesdefaultrun + texmessages)
        except TexResultError as e:
            logger.warning("We try to finish the dvi due to an unhandled tex error")
            try:
                self.finishdvi()
            except TexResultError:
                pass
            raise e
        if self.texipc:
            if first:
                self.dvifile = dvifile.DVIfile(os.path.join(self.tempdir, "texput.dvi"), debug=self.dvidebug)
        match = self.PyXBoxPattern.search(self.texmessage)
        if not match or int(match.group("page")) != self.page:
            raise TexResultError("box extents not found", self)
        left, right, height, depth = [float(xxx)*72/72.27*unit.x_pt for xxx in match.group("lt", "rt", "ht", "dp")]
        box = textbox(x, y, left, right, height, depth, self.finishdvi, fillstyles)
        for t in trafos:
            box.reltransform(t) # TODO: should trafos really use reltransform???
                                #       this is quite different from what we do elsewhere!!!
                                #       see https://sourceforge.net/mailarchive/forum.php?thread_id=9137692&forum_id=23700
        if self.texipc:
            box.setdvicanvas(self.dvifile.readpage([ord("P"), ord("y"), ord("X"), self.page, 0, 0, 0, 0, 0, 0], fontmap=fontmap, singlecharmode=singlecharmode))
        else:
            box.fontmap = fontmap
            box.singlecharmode = singlecharmode
            self.needdvitextboxes.append(box)
        return box

    def text_pt(self, x, y, expr, *args, **kwargs):
        return self.text(x * unit.t_pt, y * unit.t_pt, expr, *args, **kwargs)


class texrunner(_texrunner):

    def __init__(self, executable=config.get("text", "tex", "tex"), lfs="10pt", **kwargs):
        super().__init__(executable=executable, **kwargs)
        self.lfs = lfs
        self.name = "TeX"

    def go_typeset(self):
        assert self.state == STATE_PREAMBLE
        self.state = STATE_TYPESET

    def go_finish(self):
        self.execute("\\end%\n", self.defaulttexmessagesend + self.texmessagesend, STATE_TYPESET, STATE_DONE)

    def force_done(self):
        self.texinput.write("\n\\end\n")

    def do_start(self):
        super().do_start()
        if self.lfs:
            if not self.lfs.endswith(".lfs"):
                self.lfs = "%s.lfs" % self.lfs
            with config.open(self.lfs, []) as lfsfile:
                lfsdef = lfsfile.read().decode("ascii")
            self.execute(lfsdef, [], STATE_PREAMBLE, STATE_PREAMBLE)
            self.execute("\\normalsize%\n", [], STATE_PREAMBLE, STATE_PREAMBLE)
        self.execute("\\newdimen\\linewidth\\newdimen\\textwidth%\n", [], STATE_PREAMBLE, STATE_PREAMBLE)


class latexrunner(_texrunner):

    defaulttexmessagesdocclass = [texmessage.load]
    defaulttexmessagesbegindoc = [texmessage.load, texmessage.noaux]

    def __init__(self, executable=config.get("text", "latex", "latex"),
                       docclass="article", docopt=None, pyxgraphics=True,
                       texmessagesdocclass=[], texmessagesbegindoc=[], **kwargs):
        super().__init__(executable=executable, **kwargs)
        self.docclass = docclass
        self.docopt = docopt
        self.pyxgraphics = pyxgraphics
        self.texmessagesdocclass = texmessagesdocclass
        self.texmessagesbegindoc = texmessagesbegindoc
        self.name = "LaTeX"

    def go_typeset(self):
        self.execute("\\begin{document}", self.defaulttexmessagesbegindoc + self.texmessagesbegindoc, STATE_PREAMBLE, STATE_TYPESET)

    def go_finish(self):
        self.execute("\\end{document}%\n", self.defaulttexmessagesend + self.texmessagesend, STATE_TYPESET, STATE_DONE)

    def force_done(self):
        self.texinput.write("\n\\catcode`\\@11\\relax\\@@end\n")

    def do_start(self):
        super().do_start()
        if self.pyxgraphics:
            with config.open("pyx.def", []) as source, open(os.path.join(self.tempdir, "pyx.def"), "wb") as dest:
                dest.write(source.read())
            self.execute("\\makeatletter%\n"
                         "\\let\\saveProcessOptions=\\ProcessOptions%\n"
                         "\\def\\ProcessOptions{%\n"
                         "\\def\\Gin@driver{" + self.tempdir.replace(os.sep, "/") + "/pyx.def}%\n"
                         "\\def\\c@lor@namefile{dvipsnam.def}%\n"
                         "\\saveProcessOptions}%\n"
                         "\\makeatother",
                         [], STATE_PREAMBLE, STATE_PREAMBLE)
        if self.docopt is not None:
            self.execute("\\documentclass[%s]{%s}" % (self.docopt, self.docclass),
                         self.defaulttexmessagesdocclass + self.texmessagesdocclass, STATE_PREAMBLE, STATE_PREAMBLE)
        else:
            self.execute("\\documentclass{%s}" % self.docclass,
                         self.defaulttexmessagesdocclass + self.texmessagesdocclass, STATE_PREAMBLE, STATE_PREAMBLE)


def set(mode="tex", **kwargs):
    global defaulttexrunner, reset, preamble, text, text_pt
    mode = mode.lower()
    if mode == "tex":
        defaulttexrunner = texrunner(**kwargs)
    elif mode == "latex":
        defaulttexrunner = latexrunner(**kwargs)
    else:
        raise ValueError("mode \"TeX\" or \"LaTeX\" expected")
    reset = defaulttexrunner.reset
    preamble = defaulttexrunner.preamble
    text = defaulttexrunner.text
    text_pt = defaulttexrunner.text_pt

set()

def escapestring(s, replace={" ": "~",
                             "$": "\\$",
                             "&": "\\&",
                             "#": "\\#",
                             "_": "\\_",
                             "%": "\\%",
                             "^": "\\string^",
                             "~": "\\string~",
                             "<": "{$<$}",
                             ">": "{$>$}",
                             "{": "{$\{$}",
                             "}": "{$\}$}",
                             "\\": "{$\setminus$}",
                             "|": "{$\mid$}"}):
    "escape all ascii characters such that they are printable by TeX/LaTeX"
    i = 0
    while i < len(s):
        if not 32 <= ord(s[i]) < 127:
            raise ValueError("escapestring function handles ascii strings only")
        c = s[i]
        try:
            r = replace[c]
        except KeyError:
            i += 1
        else:
            s = s[:i] + r + s[i+1:]
            i += len(r)
    return s
