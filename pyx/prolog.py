#!/usr/bin/env python
#
#
# Copyright (C) 2003 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2003 André Wobst <wobsta@users.sourceforge.net>
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

"""prolog module:

Snippets included in the prolog of a PostScript file, which can be
used as return values of PSOp instances.

"""

import pykpathsea, t1strip

#
# Abstract base class
# 

class prologitem:

    """Part of the PostScript prolog"""

    def merge(self, other):
        """ try to merge self with other prologitem

        If the merge succeeds, return None. Otherwise return other.
        Raise ValueError, if conflicts arise!"""

        pass

    def write(self, file):
        """ write self in file """
        pass

#
# Different variants of prolog items
#

class definition(prologitem):

    """ PostScript function definition included in the prolog """

    def __init__(self, id, body):
        self.id = id
        self.body = body

    def merge(self, other):
        if not isinstance(other, definition):
            return other
        if self.id==other.id:
            if self.body==other.body:
                return None
            raise ValueError("Conflicting function definitions!")
        else:
           return other

    def write(self, file):
        file.write("%%%%BeginRessource: %s\n" % self.id)
        file.write("%(body)s /%(id)s exch def\n" % self.__dict__)
        file.write("%%EndRessource\n")


class fontdefinition(prologitem):

    """ PostScript font definition included in the prolog """

    def __init__(self, font):
        self.basepsname = font.getbasepsname()
        self.fontfile = font.getfontfile()
        self.encfilename = font.getencodingfile()
        self.usedchars = font.usedchars

    def merge(self, other):
        if not isinstance(other, fontdefinition):
            return other
        if self.basepsname==other.basepsname and self.encfilename==other.encfilename:
            for i in range(len(self.usedchars)):
                self.usedchars[i] = self.usedchars[i] or other.usedchars[i]
            return None
        else:
            return other

    def write(self, file):
        if self.fontfile:
            file.write("%%%%BeginFont: %s\n" % self.basepsname)
            file.write("%Included char codes:")
            for i in range(len(self.usedchars)):
                if self.usedchars[i]:
                    file.write(" %d" % i)
            file.write("\n")
            pfbpath = pykpathsea.find_file(self.fontfile, pykpathsea.kpse_type1_format)
            if pfbpath is None:
                raise RuntimeError("cannot find type 1 font %s" % self.fontfile)
            if self.encfilename is not None:
                encpath = pykpathsea.find_file(self.encfilename, pykpathsea.kpse_tex_ps_header_format)
                if encpath is None:
                    raise RuntimeError("cannot find font encoding file %s" % self.encfilename)
                t1strip.t1strip(file, pfbpath, self.usedchars, encpath)
            else:
                t1strip.t1strip(file, pfbpath, self.usedchars)
            file.write("%%EndFont\n")


class fontencoding(prologitem):

    """ PostScript font re-encoding vector included in the prolog """

    def __init__(self, font):
        self.name = font.getencoding()
        self.filename = font.getencodingfile()

    def merge(self, other):
        if not isinstance(other, fontencoding):
            return other
        if self.name==other.name:
            if self.filename==other.filename:
                return None
            raise ValueError("Conflicting encodings!")
        else:
           return other

    def write(self, file):
        file.write("%%%%BeginProcSet: %s\n" % self.name)
        path = pykpathsea.find_file(self.filename, pykpathsea.kpse_tex_ps_header_format)
        encfile = open(path, "r")
        file.write(encfile.read())
        encfile.close()


class fontreencoding(prologitem):

    """ PostScript font re-encoding directive included in the prolog """

    def __init__(self, font):
        self.psname = font.getpsname()
        self.basepsname = font.getbasepsname()
        self.encoding = font.getencoding()

    def merge(self, other):
        if not isinstance(other, fontreencoding):
            return other
        if self.psname==other.psname:
            if self.basepsname==other.basepsname and self.encoding==other.encoding:
                return None
            raise ValueError("Conflicting font reencodings!")
        else:
            return other

    def write(self, file):
        file.write("%%%%BeginProcSet: %s\n" % self.psname)
        file.write("/%s /%s %s ReEncodeFont\n" % (self.basepsname, self.psname, self.encoding))
        file.write("%%EndProcSet\n")


