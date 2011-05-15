# -*- encoding: utf-8 -*-
#
#
# Copyright (C) 2007-2011 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2007-2011 André Wobst <wobsta@users.sourceforge.net>
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

import os.path, re, warnings
from pyx import font, filelocator
from pyx.font import t1file, afmfile
from pyx.dvi import encfile

class UnsupportedFontFormat(Exception):
    pass

class UnsupportedPSFragment(Exception):
    pass

class ParseError(Exception):
    pass

_marker = object()

class MAPline:

    tokenpattern = re.compile(r'"(.*?)("\s+|"$|$)|(.*?)(\s+|$)')

    def __init__(self, s):
        """ construct font mapping from line s of font mapping file """
        self.texname = self.basepsname = self.fontfilename = None

        # standard encoding
        self.encodingfilename = None

        # supported postscript fragments occuring in psfonts.map
        # XXX extendfont not yet implemented
        self.reencodefont = self.extendfont = self.slant = None

        # cache for openend font and encoding
        self._font = None
        self._encoding = _marker

        tokens = []
        while len(s):
            match = self.tokenpattern.match(s)
            if match:
                if match.groups()[0] is not None:
                    tokens.append('"%s"' % match.groups()[0])
                else:
                    tokens.append(match.groups()[2])
                s = s[match.end():]
            else:
                raise ParseError("Cannot tokenize string '%s'" % s)

        next_token_is_encfile = False
        for token in tokens:
            if next_token_is_encfile:
                self.encodingfilename = token
                next_token_is_encfile = False
            elif token.startswith("<"):
                if token == "<":
                    next_token_is_encfile = True
                elif token.startswith("<<"):
                    # XXX: support non-partial download here
                    self.fontfilename = token[2:]
                elif token.startswith("<["):
                    self.encodingfilename = token[2:]
                elif token.endswith(".pfa") or token.endswith(".pfb"):
                    self.fontfilename = token[1:]
                elif token.endswith(".enc"):
                    self.encodingfilename = token[1:]
                elif token.endswith(".ttf"):
                    raise UnsupportedFontFormat("TrueType font")
                elif token.endswith(".t42"):
                    raise UnsupportedFontFormat("Type 42 font")
                else:
                    raise ParseError("Unknown token '%s'" % token)
            elif token.startswith('"'):
                pscode = token[1:-1].split()
                # parse standard postscript code fragments
                while pscode:
                    try:
                        arg, cmd = pscode[:2]
                    except:
                        raise UnsupportedPSFragment("Unsupported Postscript fragment '%s'" % pscode)
                    pscode = pscode[2:]
                    if cmd == "ReEncodeFont":
                        self.reencodefont = arg
                    elif cmd == "ExtendFont":
                        self.extendfont = arg
                    elif cmd == "SlantFont":
                        self.slant = float(arg)
                    else:
                        raise UnsupportedPSFragment("Unsupported Postscript fragment '%s %s'" % (arg, cmd))
            else:
                if self.texname is None:
                    self.texname = token
                else:
                    self.basepsname = token
        if self.basepsname is None:
            self.basepsname = self.texname

    def getfontname(self):
        return self.basepsname

    def getfont(self):
        if self._font is None:
            if self.fontfilename is not None:
                fontfile = filelocator.open(self.fontfilename, [filelocator.format.type1], "rb")
                t1font = t1file.from_PF_bytes(fontfile.read())
                fontfile.close()
                assert self.basepsname == t1font.name, "corrupt MAP file"
                try:
                    metricfile = filelocator.open(os.path.splitext(self.fontfilename)[0], [filelocator.format.afm])
                except IOError:
                    self._font = font.T1font(t1font, None)
                else:
                    self._font = font.T1font(t1font, afmfile.AFMfile(metricfile))
                    metricfile.close()
            else:
                metricfile = filelocator.open(self.basepsname, [filelocator.format.afm])
                self._font = font.T1builtinfont(self.basepsname, afmfile.AFMfile(metricfile))
                metricfile.close()
        return self._font

    def getencoding(self):
        if self._encoding is _marker:
            if self.encodingfilename is not None:
                encodingfile = filelocator.open(self.encodingfilename, [filelocator.format.tex_ps_header], "rb")
                ef = encfile.ENCfile(encodingfile.read())
                encodingfile.close()
                assert ef.name == "/%s" % self.reencodefont
                self._encoding = ef.vector

            else:
                self._encoding = None
        return self._encoding

    def __str__(self):
        return ("'%s' is '%s' read from '%s' encoded as '%s'" %
                (self.texname, self.basepsname, self.fontfile, repr(self.encodingfile)))

# generate fontmap

def readfontmap(filenames):
    """ read font map from filename (without path) """
    fontmap = {}
    for filename in filenames:
        mapfile = filelocator.open(filename, [filelocator.format.fontmap, filelocator.format.dvips_config], mode="rU")
        lineno = 0
        for line in mapfile.readlines():
            lineno += 1
            line = line.rstrip()
            if not (line=="" or line[0] in (" ", "%", "*", ";" , "#")):
                try:
                    fm = MAPline(line)
                except (ParseError, UnsupportedPSFragment), e:
                    warnings.warn("Ignoring line %i in mapping file '%s': %s" % (lineno, filename, e))
                except UnsupportedFontFormat, e:
                    pass
                else:
                    fontmap[fm.texname] = fm
        mapfile.close()
    return fontmap
