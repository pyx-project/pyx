#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2004 André Wobst <wobsta@users.sourceforge.net>
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

_PFB_ASCII = "\200\1"
_PFB_BIN = "\200\2"
_PFB_DONE = "\200\3"
_PFA = "%!"

def pfblength(string):
    if len(string) != 4:
        raise ValueError("invalid string length")
    return (ord(string[0]) +
            ord(string[1])*256 +
            ord(string[2])*256*256 +
            ord(string[3])*256*256*256)

def fullfont(file, filename):
    """inserts full pfa or pfb fonts
    - file is a file instance where the pfa output is written to
    - pfbfilename is the full filename of the pfa or pfb input file
    - the input type pfa or pfb is autodetected"""

    infile = open(filename, "rb")
    blockid = infile.read(2)
    if blockid == _PFA:
        file.write(blockid)
        file.write(infile.read().replace("\r\n", "\n").replace("\r", "\n"))
    else:
        while 1:
            if len(blockid) != 2:
                raise RuntimeError("EOF reached while reading blockid")
            if blockid == _PFB_DONE:
                if infile.read() != "":
                    raise RuntimeError("trailing characters in pfb file")
                else:
                    return
            if blockid != _PFB_ASCII and blockid != _PFB_BIN:
                raise RuntimeError("invalid blockid")
            length = pfblength(infile.read(4))
            block = infile.read(length)
            if blockid == _PFB_ASCII:
                file.write(block.replace("\r\n", "\n").replace("\r", "\n"))
            else:
                block = [ord(c) for c in block]
                while len(block) > 32:
                    file.write("%02x"*32 % tuple(block[:32]) + "\n")
                    del block[:32]
                if len(block):
                    file.write("%02x"*len(block) % tuple(block) + "\n")
            blockid = infile.read(2)

