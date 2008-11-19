import re, warnings
from pyx import font, pykpathsea
from pyx.font import t1file, afmfile
from pyx.dvi import encfile

class UnsupportedFontFormat(Exception):
    pass

class UnsupportedPSFragment(Exception):
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
                raise RuntimeError("Cannot tokenize string '%s'" % s)

        for token in tokens:
            if token.startswith("<"):
                if token.startswith("<<"):
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
                else:
                    raise RuntimeError("Unknown token '%s'" % token)
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
                fontpath = pykpathsea.find_file(self.fontfilename, pykpathsea.kpse_type1_format)
                if not fontpath:
                    raise RuntimeError("cannot find type 1 font %s" % self.fontfilename)
                if fontpath.endswith(".pfb"):
                    t1font = t1file.PFBfile(fontpath)
                else:
                    t1font = t1file.PFAfile(fontpath)
                assert self.basepsname == t1font.name, "corrupt MAP file"
                metricpath = pykpathsea.find_file(self.fontfilename.replace(".pfb", ".afm"), pykpathsea.kpse_afm_format)
                if metricpath:
                    self._font = font.T1font(t1font, afmfile.AFMfile(metricpath))
                else:
                    self._font = font.T1font(t1font, None)
            else:
                afmfilename = "%s.afm" % self.basepsname
                metricpath = pykpathsea.find_file(afmfilename, pykpathsea.kpse_afm_format)
                if not metricpath:
                    raise RuntimeError("cannot find type 1 font metric %s" % afmfilename)
                self._font = font.T1builtinfont(self.basepsname, afmfile.AFMfile(metricpath))
        return self._font

    def getencoding(self):
        if self._encoding is _marker:
            if self.encodingfilename is not None:
                encodingpath = pykpathsea.find_file(self.encodingfilename, pykpathsea.kpse_tex_ps_header_format)
                if not encodingpath:
                    raise RuntimeError("cannot find font encoding file %s" % self.encodingfilename)
                ef = encfile.ENCfile(encodingpath)
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
        mappath = pykpathsea.find_file(filename, pykpathsea.kpse_fontmap_format)
        # try also the oft-used registration as dvips config file
        if not mappath:
            mappath = pykpathsea.find_file(filename, pykpathsea.kpse_dvips_config_format)
        if not mappath:
            raise RuntimeError("cannot find font mapping file '%s'" % filename)
        mapfile = open(mappath, "rU")
        lineno = 0
        for line in mapfile.readlines():
            lineno += 1
            line = line.rstrip()
            if not (line=="" or line[0] in (" ", "%", "*", ";" , "#")):
                try:
                    fm = MAPline(line)
                except (RuntimeError, UnsupportedPSFragment), e:
                    warnings.warn("Ignoring line %i in mapping file '%s': %s" % (lineno, mappath, e))
                except UnsupportedFontFormat, e:
                    pass
                else:
                    fontmap[fm.texname] = fm
        mapfile.close()
    return fontmap
