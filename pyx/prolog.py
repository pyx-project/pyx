#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2003-2004 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2003-2004 André Wobst <wobsta@users.sourceforge.net>
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

    def outputPS(self, file):
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

    def outputPS(self, file):
        file.write("%%%%BeginRessource: %s\n" % self.id)
        file.write("%(body)s /%(id)s exch def\n" % self.__dict__)
        file.write("%%EndRessource\n")


class fontdefinition(prologitem):

    """ PostScript font definition included in the prolog """

    def __init__(self, font, fontname, filename, encfilename, usedchars):
        """ include type 1 font defined by the following parameters

        - fontname:    PostScript FontName of font
        - filename:    name (without path) of file containing the font definition
        - encfilename: name (without path) of file containing used encoding of font
                       or None (if no encoding file used)
        - usechars:    list with 256 elements containing used charcodes of font

        """

        # Note that here we only need the encoding for selecting the used glyphs!

        # XXX rewrite

        self.font = font
        self.fontname = fontname
        self.filename = filename
        self.encfilename = encfilename
        self.usedchars = usedchars

    def merge(self, other):
        if not isinstance(other, fontdefinition):
            return other
        if self.fontname==other.fontname and self.encfilename==other.encfilename:
            for i in range(len(self.usedchars)):
                self.usedchars[i] = self.usedchars[i] or other.usedchars[i]
            return None
        else:
            return other

    def outputPS(self, file):
        if self.filename:
            file.write("%%%%BeginFont: %s\n" % self.fontname)
            file.write("%Included char codes:")
            for i in range(len(self.usedchars)):
                if self.usedchars[i]:
                    file.write(" %d" % i)
            file.write("\n")
            pfbpath = pykpathsea.find_file(self.filename, pykpathsea.kpse_type1_format)
            if not pfbpath:
                raise RuntimeError("cannot find type 1 font %s" % self.filename)
            if self.encfilename is not None:
                encpath = pykpathsea.find_file(self.encfilename, pykpathsea.kpse_tex_ps_header_format)
                if not encpath:
                    raise RuntimeError("cannot find font encoding file %s" % self.encfilename)
                t1strip.t1strip(file, pfbpath, self.usedchars, encpath)
            else:
                t1strip.t1strip(file, pfbpath, self.usedchars)
            file.write("%%EndFont\n")


class fontencoding(prologitem):

    """ PostScript font encoding vector included in the prolog """

    def __init__(self, name, filename):
        """ include font encoding vector specified by

        - name:        name of the encoding
        - filename:    name (without path) of file containing the font encoding

        """

        self.name = name
        self.filename = filename

    def merge(self, other):
        if not isinstance(other, fontencoding):
            return other
        if self.name==other.name:
            if self.filename==other.filename:
                return None
            raise ValueError("Conflicting encodings!")
        else:
           return other

    def outputPS(self, file):
        file.write("%%%%BeginProcSet: %s\n" % self.name)
        path = pykpathsea.find_file(self.filename, pykpathsea.kpse_tex_ps_header_format)
        encfile = open(path, "r")
        file.write(encfile.read())
        encfile.close()
        file.write("%%EndProcSet\n")


class fontreencoding(prologitem):

    """ PostScript font re-encoding directive included in the prolog """

    def __init__(self, fontname, basefontname, encname):
        """ include font re-encoding directive specified by

        - fontname:     PostScript FontName of the new reencoded font
        - basefontname: PostScript FontName of the original font
        - encname:      name of the encoding
        - font:         a reference to the font instance (temporarily added for pdf support)

        Before being able to reencode a font, you have to include the
        encoding via a fontencoding prolog item with name=encname

        """

        self.fontname = fontname
        self.basefontname = basefontname
        self.encname = encname

    def merge(self, other):
        if not isinstance(other, fontreencoding):
            return other
        if self.fontname==other.fontname:
            if self.basefontname==other.basefontname and self.encname==other.encname:
                return None
            raise ValueError("Conflicting font reencodings!")
        else:
            return other

    def outputPS(self, file):
        file.write("%%%%BeginProcSet: %s\n" % self.fontname)
        file.write("/%s /%s %s ReEncodeFont\n" % (self.basefontname, self.fontname, self.encname))
        file.write("%%EndProcSet\n")
