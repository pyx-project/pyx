#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2005 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2005 André Wobst <wobsta@users.sourceforge.net>
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

import math, re
import pykpathsea

_PFB_ASCII = "\200\1"
_PFB_BIN = "\200\2"
_PFB_DONE = "\200\3"
_PFA = "%!"

_StandardEncodingMatch = re.compile(r"\b/Encoding\s+StandardEncoding\s+def\b")
#_FontBBoxMatch = re.compile(r"\bFontBBox\s*\{\s*(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s*\}\s*readonly\s+def\b")
#_ItalicAngle = re.compile(r"\bItalicAngle\s+(-?\d+)\b")


def _pfblength(s):
    if len(s) != 4:
        raise ValueError("invalid string length")
    return (ord(s[0]) +
            ord(s[1])*256 +
            ord(s[2])*256*256 +
            ord(s[3])*256*256*256)

class type1font:

    def __init__(self, font):
        self.font = font
        # self.filename = pykpathsea.find_file("%s.%s" % (name, type), pykpathsea.kpse_type1_format)
        self.filename = self.font.getfontfile()

        fontfile = open(self.filename, "rb")
        self.fontdata = fontfile.read()
        fontfile.close()

        # split the font into its three main parts
        
        if self.fontdata[0:2] != _PFB_ASCII:
            raise RuntimeError("PFB_ASCII mark expected")
        self.length1 = _pfblength(self.fontdata[2:6])
        self.fontdata1 = self.fontdata[6:6+self.length1]
        
        if self.fontdata[6+self.length1:8+self.length1] != _PFB_BIN:
            raise RuntimeError("PFB_BIN mark expected")
        self.length2 = _pfblength(self.fontdata[8+self.length1:12+self.length1])
        self.fontdata2 = self.fontdata[12+self.length1:12+self.length1+self.length2]
        
        if self.fontdata[12+self.length1+self.length2:14+self.length1+self.length2] != _PFB_ASCII:
            raise RuntimeError("PFB_ASCII mark expected")
        self.length3 = _pfblength(self.fontdata[14+self.length1+self.length2:18+self.length1+self.length2])
        self.fontdata3 = self.fontdata[18+self.length1+self.length2:18+self.length1+self.length2+self.length3]
        
        if self.fontdata[18+self.length1+self.length2+self.length3:20+self.length1+self.length2+self.length3] != _PFB_DONE:
            raise RuntimeError("PFB_DONE mark expected")
        
        if len(self.fontdata) != 20 + self.length1 + self.length2 + self.length3:
            raise RuntimeError("end of pfb file expected")

        #         # we might be allowed to skip the third part ...
        #         if self.fontdata3.replace("\n", "").replace("\r", "").replace("\t", "").replace(" ", "") == "0"*512 + "cleartomark":
        #             self.length3 = 0
        #             self.fontdata3 = ""
        #         data = self.fontdata1 + self.fontdata2 + self.fontdata3


        # The following code is a very crude way to obtain the information
        # required for the PDF font descritor.
        # As a simple heuristics we assume non-symbolic fonts if and only
        # if the Adobe standard encoding is used. All other font flags are
        # not specified here.
        if _StandardEncodingMatch.search(self.fontdata1):
            self.flags = 32
        else:
            self.flags = 4
        # self.fontbbox = map(int, _FontBBoxMatch(self.fontdata1))
        # self.italicangle = int(_ItalicAngleMatch(self.fontdata1))
        # self.ascent = self.fontbbox[3]
        # self.descent = self.fontbbox[1]
        # self.capheight = self.fontbbox[3]
        # self.stemv = (self.fontbbox[2] - self.fontbbox[0]) / 23
        self.fontbbox = (0,
                         -self.font.getdepth_pt(ord("y"))*1000/self.font.getsize_pt(),
                         self.font.getwidth_pt(ord("W"))*1000/self.font.getsize_pt(),
                         self.font.getheight_pt(ord("H"))*1000/self.font.getsize_pt())
        self.italicangle = -180/math.pi*math.atan(self.font.tfmfile.param[0]/65536.0)
        self.ascent = self.fontbbox[3]
        self.descent = self.fontbbox[1]
        self.capheight = self.font.getheight_pt(ord("h"))*1000/self.font.getsize_pt()
        self.vstem = self.font.getwidth_pt(ord("."))*1000/self.font.getsize_pt()/3
