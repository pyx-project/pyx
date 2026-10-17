import binascii, struct
from pyx import baseclasses, unit, pswriter, bbox
from pyx.font.font import _ReEncodeFont

latin1pos2name = {32: 'space', 33: 'exclam', 34: 'quotedbl', 35: 'numbersign',
                  36: 'dollar', 37: 'percent', 38: 'ampersand', 39:
                  'quoteright', 40: 'parenleft', 41: 'parenright', 42:
                  'asterisk', 43: 'plus', 44: 'comma', 45: 'minus', 46:
                  'period', 47: 'slash', 48: 'zero', 49: 'one', 50: 'two', 51:
                  'three', 52: 'four', 53: 'five', 54: 'six', 55: 'seven', 56:
                  'eight', 57: 'nine', 58: 'colon', 59: 'semicolon', 60:
                  'less', 61: 'equal', 62: 'greater', 63: 'question', 64: 'at',
                  65: 'A', 66: 'B', 67: 'C', 68: 'D', 69: 'E', 70: 'F', 71:
                  'G', 72: 'H', 73: 'I', 74: 'J', 75: 'K', 76: 'L', 77: 'M',
                  78: 'N', 79: 'O', 80: 'P', 81: 'Q', 82: 'R', 83: 'S', 84:
                  'T', 85: 'U', 86: 'V', 87: 'W', 88: 'X', 89: 'Y', 90: 'Z',
                  91: 'bracketleft', 92: 'backslash', 93: 'bracketright', 94:
                  'asciicircum', 95: 'underscore', 96: 'quoteleft', 97: 'a',
                  98: 'b', 99: 'c', 100: 'd', 101: 'e', 102: 'f', 103: 'g',
                  104: 'h', 105: 'i', 106: 'j', 107: 'k', 108: 'l', 109: 'm',
                  110: 'n', 111: 'o', 112: 'p', 113: 'q', 114: 'r', 115: 's',
                  116: 't', 117: 'u', 118: 'v', 119: 'w', 120: 'x', 121: 'y',
                  122: 'z', 123: 'braceleft', 124: 'bar', 125: 'braceright',
                  126: 'asciitilde', 144: 'dotlessi', 145: 'grave', 147:
                  'circumflex', 148: 'tilde', 150: 'breve', 151: 'dotaccent',
                  154: 'ring', 157: 'hungarumlaut', 158: 'ogonek', 159:
                  'caron', 161: 'exclamdown', 162: 'cent', 163: 'sterling',
                  164: 'currency', 165: 'yen', 166: 'brokenbar', 167:
                  'section', 168: 'dieresis', 169: 'copyright', 170:
                  'ordfeminine', 171: 'guillemotleft', 172: 'logicalnot', 173:
                  'hyphen', 174: 'registered', 175: 'macron', 176: 'degree',
                  177: 'plusminus', 178: 'twosuperior', 179: 'threesuperior',
                  180: 'acute', 181: 'mu', 182: 'paragraph', 183:
                  'periodcentered', 184: 'cedilla', 185: 'onesuperior', 186:
                  'ordmasculine', 187: 'guillemotright', 188: 'onequarter',
                  189: 'onehalf', 190: 'threequarters', 191: 'questiondown',
                  192: 'Agrave', 193: 'Aacute', 194: 'Acircumflex', 195:
                  'Atilde', 196: 'Adieresis', 197: 'Aring', 198: 'AE', 199:
                  'Ccedilla', 200: 'Egrave', 201: 'Eacute', 202: 'Ecircumflex',
                  203: 'Edieresis', 204: 'Igrave', 205: 'Iacute', 206:
                  'Icircumflex', 207: 'Idieresis', 208: 'Eth', 209: 'Ntilde',
                  210: 'Ograve', 211: 'Oacute', 212: 'Ocircumflex', 213:
                  'Otilde', 214: 'Odieresis', 215: 'multiply', 216: 'Oslash',
                  217: 'Ugrave', 218: 'Uacute', 219: 'Ucircumflex', 220:
                  'Udieresis', 221: 'Yacute', 222: 'Thorn', 223: 'germandbls',
                  224: 'agrave', 225: 'aacute', 226: 'acircumflex', 227:
                  'atilde', 228: 'adieresis', 229: 'aring', 230: 'ae', 231:
                  'ccedilla', 232: 'egrave', 233: 'eacute', 234: 'ecircumflex',
                  235: 'edieresis', 236: 'igrave', 237: 'iacute', 238:
                  'icircumflex', 239: 'idieresis', 240: 'eth', 241: 'ntilde',
                  242: 'ograve', 243: 'oacute', 244: 'ocircumflex', 245:
                  'otilde', 246: 'odieresis', 247: 'divide', 248: 'oslash',
                  249: 'ugrave', 250: 'uacute', 251: 'ucircumflex', 252:
                  'udieresis', 253: 'yacute', 254: 'thorn', 255: 'ydieresis'}

macnames = [ ".notdef", ".null", "nonmarkingreturn", "space", "exclam",
             "quotedbl", "numbersign", "dollar", "percent", "ampersand",
             "quotesingle", "parenleft", "parenright", "asterisk", "plus",
             "comma", "hyphen", "period", "slash", "zero", "one", "two",
             "three", "four", "five", "six", "seven", "eight", "nine", "colon",
             "semicolon", "less", "equal", "greater", "question", "at", "A",
             "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N",
             "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z",
             "bracketleft", "backslash", "bracketright", "asciicircum",
             "underscore", "grave", "a", "b", "c", "d", "e", "f", "g", "h",
             "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u",
             "v", "w", "x", "y", "z", "braceleft", "bar", "braceright",
             "asciitilde", "Adieresis", "Aring", "Ccedilla", "Eacute",
             "Ntilde", "Odieresis", "Udieresis", "aacute", "agrave",
             "acircumflex", "adieresis", "atilde", "aring", "ccedilla",
             "eacute", "egrave", "ecircumflex", "edieresis", "iacute",
             "igrave", "icircumflex", "idieresis", "ntilde", "oacute",
             "ograve", "ocircumflex", "odieresis", "otilde", "uacute",
             "ugrave", "ucircumflex", "udieresis", "dagger", "degree", "cent",
             "sterling", "section", "bullet", "paragraph", "germandbls",
             "registered", "copyright", "trademark", "acute", "dieresis",
             "notequal", "AE", "Oslash", "infinity", "plusminus", "lessequal",
             "greaterequal", "yen", "mu", "partialdiff", "summation",
             "product", "pi", "integral", "ordfeminine", "ordmasculine",
             "Omega", "ae", "oslash", "questiondown", "exclamdown",
             "logicalnot", "radical", "florin", "approxequal", "Delta",
             "guillemotleft", "guillemotright", "ellipsis", "nonbreakingspace",
             "Agrave", "Atilde", "Otilde", "OE", "oe", "endash", "emdash",
             "quotedblleft", "quotedblright", "quoteleft", "quoteright",
             "divide", "lozenge", "ydieresis", "Ydieresis", "fraction",
             "currency", "guilsinglleft", "guilsinglright", "fi", "fl",
             "daggerdbl", "periodcentered", "quotesinglbase", "quotedblbase",
             "perthousand", "Acircumflex", "Ecircumflex", "Aacute",
             "Edieresis", "Egrave", "Iacute", "Icircumflex", "Idieresis",
             "Igrave", "Oacute", "Ocircumflex", "apple", "Ograve", "Uacute",
             "Ucircumflex", "Ugrave", "dotlessi", "circumflex", "tilde",
             "macron", "breve", "dotaccent", "ring", "cedilla", "hungarumlaut",
             "ogonek", "caron", "Lslash", "lslash", "Scaron", "scaron",
             "Zcaron", "zcaron", "brokenbar", "Eth", "eth", "Yacute", "yacute",
             "Thorn", "thorn", "minus", "multiply", "onesuperior",
             "twosuperior", "threesuperior", "onehalf", "onequarter",
             "threequarters", "franc", "Gbreve", "gbreve", "Idotaccent",
             "Scedilla", "scedilla", "Cacute", "cacute", "Ccaron", "ccaron",
             "dcroat"]


class OpenTypeFont:

    def __init__(self, otffile):

        self.usedchars = {}

        try:
            self.otfdata = open(otffile, "rb")
        except:
            pass
        self.otfdata = otffile.read()
        sfntVersion, numTables = struct.unpack(">4sHHHH", self.otfdata[:12])[:2]
        if self.otfdata[:4] not in [b"\000\001\000\000", b"OTTO", b"true", b"typ1"]:
            raise RuntimeError("invalid font file (sfnt version error)")
        self.otfsplit = []
        tables = {}
        for numTable in range(numTables):
            tag, checkSum, offset, length = struct.unpack(">4slll", self.otfdata[12+16*numTable:28+16*numTable])
            tables[tag] = self.otfdata[offset: offset+length]
            if tag == "glyf":
                self.glyfoffset = offset
                self.glyflength = length
            elif tag == "loca":
                self.locaoffset = offset
            self.otfsplit.append(offset)

        unitsPerEm, = struct.unpack(">H", tables[b"head"][18:20])
        factor = 1000.0/unitsPerEm
        self.xMin, self.yMin, self.xMax, self.yMax = [int(factor*value) for value in struct.unpack(">4h", tables[b"head"][36:44])]
        self.indexToLocFormat, = struct.unpack(">h", tables[b"head"][50:52])

        numGlyphs, = struct.unpack(">H", tables[b"maxp"][4:6])

        self.widths = []
        for i in range(numGlyphs):
            try:
                self.widths.append(factor*struct.unpack(">H", tables[b"hmtx"][i*4:2+i*4])[0])
            except:
                self.widths.append(0)

        if not self.indexToLocFormat:
            self.glyphLocations = [2*location for location in struct.unpack(">%dH" % (numGlyphs+1), tables[b"loca"])]
        else:
            self.glyphLocations = struct.unpack(">%dL" % (numGlyphs+1), tables[b"loca"])

        self.depth = []
        self.height = []
        for location in self.glyphLocations[:-1]:
            if location < len(tables[b"glyf"]):
                depth, dummy, height = struct.unpack(">hhh", tables[b"glyf"][location+4:location+10])
                self.depth.append(factor*depth)
                self.height.append(factor*height)
            else:
                self.depth.append(0)
                self.height.append(0)

        if b"name" not in tables:
            raise RuntimeError("invalid font file (name table missing error)")
        format, count, stringOffset = struct.unpack(">HHH", tables[b"name"][:6])
        self.fontname = ""
        self.displayname = "unknown"
        self.displaystyle = "unknown"
        for i in range(count):
            platformID, encodingID, languageID, nameID, length, offset = struct.unpack(">HHHHHH", tables[b"name"][6+12*i:18+12*i])
            if platformID == 1:
                if nameID == 1:
                    self.displayname = tables[b"name"][offset+6+12*count:offset+length+6+12*count]
                elif nameID == 2:
                    self.displaystyle = tables[b"name"][offset+6+12*count:offset+length+6+12*count]
                elif nameID == 6:
                    self.fontname = tables[b"name"][offset+6+12*count:offset+length+6+12*count]
            elif platformID == 3 and encodingID == 1 and languageID == 1033:
                if nameID == 1:
                    self.displayname = tables[b"name"][offset+6+12*count:offset+length+6+12*count].decode("utf-16be")
                elif nameID == 2:
                    self.displaystyle = tables[b"name"][offset+6+12*count:offset+length+6+12*count].decode("utf-16be")
                elif nameID == 6:
                    self.fontname = tables[b"name"][offset+6+12*count:offset+length+6+12*count].decode("utf-16be")
        if not self.fontname:
            raise RuntimeError("invalid font file (nameID missing error)")

        if b"post" not in tables:
            raise RuntimeError("invalid font file (post (== PostScript) table missing)")
        if tables[b"post"][:4] == b"\000\001\000\000":
            # XXX untested
            self.charstrings = macnames
            for i, name in enumerate(self.charstrings):
                 self.name2pos[name] = i
        elif tables[b"post"][:4] == b"\000\002\000\000":
            count, = struct.unpack(">H", tables[b"post"][32:34])
            indizes = struct.unpack(">%iH" % count, tables[b"post"][34:34+2*count])
            pos = 34+2*count
            names = []
            while pos < len(tables[b"post"]):
                 names.append(tables[b"post"][pos+1:pos+1+tables[b"post"][pos]])
                 pos += tables[b"post"][pos]+1
            self.charstrings = []
            for i, index in enumerate(indizes):
                 if 0 <= index < 258:
                     self.charstrings.append(macnames[index])
                 else:
                     self.charstrings.append(names[index-258])
            self.name2pos = {}
            for i, name in enumerate(self.charstrings):
                if name in self.name2pos:
                    self.charstrings[i] = None # remove dublicates
                else:
                    self.name2pos[name] = i
        elif tables[b"post"][:4] == b"\000\002\000\005":
            # XXX untested
            count, = struct.unpack(">H", tables[b"post"][32:34])
            indizes = struct.unpack(">%ib" % count, tables[b"post"][34:34+count])
            self.charstrings = [macnames[i+index] for i, index in enumerate(indizes)]
            for i, name in enumerate(self.charstrings):
                 self.name2pos[name] = i
        elif tables[b"post"][:4] == b"\000\003\000\000":
            # according to the specs "printing behavior is unspecified", but we try to decode it from cmap
            self.charstrings = [".notdef"]*max(256, numGlyphs)
            self.name2pos = {}
            if b"cmap" in tables:
                version, numTables = struct.unpack(">HH", tables[b"cmap"][:4])
                for i in range(numTables):
                    platformID, encodingID, offset = struct.unpack(">HHL", tables[b"cmap"][4+8*i:12+8*i])
                    if platformID == 3 and encodingID == 1:
                        format, length, language = struct.unpack(">HHH", tables[b"cmap"][offset:6+offset])
                        if format == 4: # other formats not yet supported
                            segCount2, searchRange, entrySelector, rangeShift = struct.unpack(">HHHH", tables[b"cmap"][6+offset:14+offset])
                            segCount = segCount2/2
                            endCounts = struct.unpack(">%dH" % segCount, tables[b"cmap"][14+offset:14+offset+segCount2])
                            # assert (0,) == struct.unpack(">H", tables[b"cmap"][14+offset+segCount2:16+offset+segCount2])
                            startCounts = struct.unpack(">%dH" % segCount, tables[b"cmap"][16+offset+segCount2:16+offset+2*segCount2])
                            idDeltas = struct.unpack(">%dh" % segCount, tables[b"cmap"][16+offset+2*segCount2:16+offset+3*segCount2])
                            idRangeOffsets = struct.unpack(">%dH" % segCount, tables[b"cmap"][16+offset+3*segCount2:16+offset+4*segCount2])
                            n = 0
                            for endCount, startCount, idDelta, idRangeOffset in zip(endCounts, startCounts, idDeltas, idRangeOffsets):
                                if startCount < 256:
                                    for i, name in latin1pos2name.items():
                                        if startCount <= i <= endCount:
                                            if idRangeOffset:
                                                i, = struct.unpack(">H", tables[b"cmap"][16+offset+3*segCount2+2*n+idRangeOffset+2*(i-startCount):18+offset+3*segCount2+2*n+idRangeOffset+2*(i-startCount)])
                                            else:
                                                i = (i + idDelta) % (1 << 16)
                                            self.charstrings[i] = name
                                            self.name2pos[name] = i
                                n += 1
        elif tables[b"post"][:4] == b"\000\004\000\000":
            raise RuntimeError("post table format 4 for Japanese, Chinese or Korean is not implemented")
        else:
            raise RuntimeError("invalid post table format")

        self.kerning = {}
        if b"kern" in tables:
            nTables, = struct.unpack(">H", tables[b"kern"][2:4])
            pos = 4
            for nTable in range(nTables):
                version, length, coverage = struct.unpack(">HHH", tables[b"kern"][pos:pos+6])
                if coverage & 0x0003 == 1:
                    if coverage & 0xff00 == 0x0000:
                        nPairs, = struct.unpack(">H", tables[b"kern"][pos+6:pos+8])
                        for nPair in range(nPairs):
                            left, right, value = struct.unpack(">HHh", tables[b"kern"][pos+6*nPair+14:pos+6*nPair+20])
                            self.kerning.setdefault(left, {})[right] = factor*value
                    elif coverage & 0xff00 == 0x0200:
                        raise RuntimeError("can't handle class based kerning")
                pos += length

        self.ligatures = {}
        if b"GSUB" in tables:
            ScriptList, FeatureList, LookupList = struct.unpack(">HHH", tables[b"GSUB"][4:10])
            ScriptCount, = struct.unpack(">H", tables[b"GSUB"][ScriptList:ScriptList+2])
            for ScriptTag, offset in [struct.unpack(">4sH", tables[b"GSUB"][ScriptList+2+6*i:ScriptList+8+6*i]) for i in range(ScriptCount)]:
                if ScriptTag == "latn":
                    DefaultLangSys, LangSysCount = struct.unpack(">HH", tables[b"GSUB"][ScriptList+offset:ScriptList+4+offset])
                    # the lookup for a specific language would be:
                    # for LangSysTag, offset2 in [struct.unpack(">4sH", tables[b"GSUB"][ScriptList+offset+4+6*i:ScriptList+offset+10+6*i]) for i in range(LangSysCount)]:
                    #     print LangSysTag, offset2
                    if DefaultLangSys:
                        LookupOrder, ReqFeatureIndex, FeatureCount = struct.unpack(">HHH", tables[b"GSUB"][ScriptList+offset+DefaultLangSys:ScriptList+offset+DefaultLangSys+6])
                        useFeatures = dict([(index, True)
                                            for index in struct.unpack(">%dH" % FeatureCount, tables[b"GSUB"][ScriptList+offset+DefaultLangSys+6:ScriptList+offset+DefaultLangSys+6+2*FeatureCount])])
                        if ReqFeatureIndex != (1 << 16) - 1:
                             useFeatures[ReqFeatureIndex] = True
            useLookup = {}
            FeatureCount, = struct.unpack(">H", tables[b"GSUB"][FeatureList:FeatureList+2])
            for index, (FeatureTag, offset) in [(i, struct.unpack(">4sH", tables[b"GSUB"][FeatureList+2+6*i:FeatureList+8+6*i]))
                                                for i in range(FeatureCount)]:
                if FeatureTag in ["liga", "rlig"]:
                    FeatureParams, LookupCount = struct.unpack(">HH", tables[b"GSUB"][FeatureList+offset: FeatureList+offset+4])
                    for index in struct.unpack(">%dH" % LookupCount, tables[b"GSUB"][FeatureList+offset+4: FeatureList+offset+4+2*LookupCount]):
                        useLookup[index] = True
            LookupCount, = struct.unpack(">H", tables[b"GSUB"][LookupList:LookupList+2])
            for index, offset in enumerate(struct.unpack(">%dH" % LookupCount, tables[b"GSUB"][LookupList+2:LookupList+2+2*LookupCount])):
                LookupType, LookupFlag, SubTableCount = struct.unpack(">HHH", tables[b"GSUB"][LookupList+offset:LookupList+offset+6])
                if LookupType == 4 and index in useLookup:
                    for offset2 in struct.unpack(">%dH" % SubTableCount, tables[b"GSUB"][LookupList+offset+6:LookupList+offset+6+2*SubTableCount]):
                        SubstFormat, Coverage, LigSetCount = struct.unpack(">HHH", tables[b"GSUB"][LookupList+offset+offset2:LookupList+offset+offset2+6])
                        LigatureCount, = struct.unpack(">H", tables[b"GSUB"][LookupList+offset+offset2+2+Coverage:LookupList+offset+offset2+4+Coverage])
                        glyph0s = struct.unpack(">%dH" % LigatureCount, tables[b"GSUB"][LookupList+offset+offset2+4+Coverage:LookupList+offset+offset2+4+Coverage+2*LigatureCount])
                        for glyph0, offset3 in zip(glyph0s, struct.unpack(">%dH" % LigSetCount, tables[b"GSUB"][LookupList+offset+offset2+6:LookupList+offset+offset2+6+2*LigSetCount])):
                            LigatureCount, = struct.unpack(">H", tables[b"GSUB"][LookupList+offset+offset2+offset3:LookupList+offset+offset2+offset3+2])
                            for offset4 in struct.unpack(">%dH" % LigatureCount, tables[b"GSUB"][LookupList+offset+offset2+offset3+2:LookupList+offset+offset2+offset3+2+2*LigatureCount]):
                                LigGlyph, CompCount = struct.unpack(">HH", tables[b"GSUB"][LookupList+offset+offset2+offset3+offset4:LookupList+offset+offset2+offset3+offset4+4])
                                glyphs = struct.unpack(">%dH" % (CompCount-1), tables[b"GSUB"][LookupList+offset+offset2+offset3+offset4+4:LookupList+offset+offset2+offset3+offset4+4+2*(CompCount-1)])
                                #if self.charstrings[LigGlyph] in self.name2pos: # was already deactivated in pyx_meyer
                                if 1:
                                    self.ligatures.setdefault(self.charstrings[glyph0], []).append(([self.charstrings[glyph] for glyph in glyphs], self.charstrings[LigGlyph]))


    def text_pt(self, x_pt, y_pt, size, text):
        return otftext_pt(self, x_pt, y_pt, size, text)


# def checksum(data):
#     l = len(data)
#     return sum(struct.unpack(">%dL" % ((l+3)/4), data+"\000"*((4-l%4)%4))) % (1l << 32)

class otffontresource(pswriter.PSresource):

    def __init__(self, otffont):
        self.type = "t1file"
        self.id = otffont.fontname
        self.otffont = otffont
        self.otffont.encoding = {}

    def merge(self, other):
        if not isinstance(other, otffontresource):
            return other
        if self.otffont.fontname == other.otffont.fontname:
            self.otffont.usedchars.update(other.otffont.usedchars)
            other.otffont.encoding = self.otffont.encoding
            return None
        else:
            return other

    def outputPS(self, file):
        encvector = self.otffont.usedchars.keys()
        self.otffont.encoding.update(dict([(char, i) for i, char in enumerate(encvector)]))

        file.write("%%%%BeginFont: %s\n" % self.otffont.fontname)
        file.write("11 dict begin\n")
        file.write("/FontName /%s def\n" % self.otffont.fontname)
        file.write("/FontType 42 def\n")
        file.write("/FontMatrix [1 0 0 1 0 0] def\n")
        file.write("/FontBBox [%d %d %d %d] def\n" % (self.otffont.xMin, self.otffont.yMin, self.otffont.xMax, self.otffont.yMax))
        file.write("/PaintType 0 def\n")
        file.write("/Encoding StandardEncoding def\n")
        file.write("/CharStrings %i dict dup begin\n" % len(self.otffont.charstrings))
        for i, name in enumerate(self.otffont.charstrings):
            if name is not None:
#               if not self.otffont.strip or self.otffont.usedchars.has_key(name):
                    file.write("/%s %d def\n" % (name, i))
        file.write("end readonly def\n")

        otfsplit = self.otffont.otfsplit[:]
        glyphLocations = self.otffont.glyphLocations
        otfdata = self.otffont.otfdata

#         if self.otffont.strip:
#             usedglyphs = {}
#             for i in range(len(glyphLocations)-1):
#                 if self.otffont.usedchars.has_key(self.otffont.charstrings[i]):
#                     usedglyphs[i] = True
#                     offset1 = glyphLocations[i]
#                     numberOfContours, = struct.unpack(">h", otfdata[self.otffont.glyfoffset+offset1:self.otffont.glyfoffset+offset1+2])
#                     if numberOfContours == -1:
#                         offset = offset1+10
#                         while 1:
#                             flags, glyphIndex = struct.unpack(">HH", otfdata[self.otffont.glyfoffset+offset: self.otffont.glyfoffset+offset+4])
#                             usedglyphs[glyphIndex] = True
#                             offset += 6
#                             if flags & 0x0001:
#                                 offset += 2
#                             if flags & 0x0008:
#                                 offset += 2
#                             if not flags & 0x0020:
#                                 break
#                             if flags & 0x0040:
#                                 offset += 2
#                             if flags & 0x0080:
#                                 offset += 4
#             glyphs = []
#             for i in range(len(glyphLocations)-1):
#                 if usedglyphs.has_key(i):
#                     offset1 = glyphLocations[i]
#                     offset2 = glyphLocations[i+1]
#                     glyphs.append(otfdata[self.otffont.glyfoffset+offset1:self.otffont.glyfoffset+offset2])
#                 else:
#                     glyphs.append("")
# 
#             offset = 0
#             glyphLocations = []
#             for glyph in glyphs:
#                 glyphLocations.append(offset)
#                 offset += len(glyph)
#             glyphLocations.append(offset)
# 
#             if self.otffont.strip:
#                 if not self.otffont.indexToLocFormat:
#                     otfdata = otfdata[:self.otffont.locaoffset] + struct.pack(">%dH" % len(glyphLocations), *[location/2 for location in glyphLocations]) + otfdata[self.otffont.locaoffset+2*len(glyphLocations):]
#                 else:
#                     otfdata = otfdata[:self.otffont.locaoffset] + struct.pack(">%dL" % len(glyphLocations), *glyphLocations) + otfdata[self.otffont.locaoffset+4*len(glyphLocations):]
#             glyphs = "".join([glyph for glyph in glyphs])
#             otfdata = otfdata[:self.otffont.glyfoffset] + glyphs + otfdata[self.otffont.glyfoffset+self.otffont.glyflength:]
# 
#             sfntVersion, numTables = struct.unpack(">4sHHHH", otfdata[:12])[:2]
#             for numTable in range(numTables):
#                 tag, checkSum, offset, length = struct.unpack(">4sLll", otfdata[12+16*numTable:28+16*numTable])
#                 if tag == "glyf":
#                     length = len(glyphs)
#                 elif offset > self.otffont.glyfoffset:
#                     offset += len(glyphs) - self.otffont.glyflength
#                 if tag in ["glyf", "loca"]:
#                     checkSum = checksum(otfdata[offset: offset+length])
#                 elif tag == "head":
#                     otfdata = otfdata[:offset+8] + "\000"*4 + otfdata[offset+12:]
#                     checkSum = 2981146554L - checksum(otfdata)
#                     if checkSum < 0:
#                         checkSum += 1l << 32
#                 otfdata = otfdata[:12+16*numTable] + struct.pack(">4sLll", tag, checkSum, offset, length) + otfdata[28+16*numTable:]

        otfsplit.extend([self.otffont.glyfoffset + location for location in glyphLocations])

        otfsplit.sort()
        otfsplit.append(len(otfdata))

        # add further split positions (at arbitrary placed, which should *not* be done according to the specs, but otherwise the strings can't be expressed in PostScript at all and fail for sure)
        i = 0
        while i < len(otfsplit)-1:
            if otfsplit[i+1] - otfsplit[i] > 65000:
                otfsplit.insert(i+1, otfsplit[i]+65000)
            else:
                i += 1

        lastsplit = 0
        i = 0
        while i < len(otfsplit)-1:
            if otfsplit[i+1] - lastsplit < 65000:
                del otfsplit[i]
            else:
                lastsplit = otfsplit[i]
                i += 1
        del otfsplit[-1]

        file.write("/sfnts[<\n")
        for p1, p2 in zip([0]+otfsplit, otfsplit+[len(otfdata)]):
            chunk = otfdata[p1:p2]
            chunk = binascii.b2a_hex(chunk)
            if p1:
                file.write("00><\n")
            i = 0
            while i < len(chunk):
                file.write("%s\n" % (chunk[i:i+72].upper()))
                i += 72
        file.write("00>]def\n")
        file.write("FontName currentdict end definefont pop\n")
        file.write("%%EndFont\n")
        file.write("%%%%BeginRessource: %s-PyXencoded\n" % self.otffont.fontname)
        file.write("/%s /%s-PyXencoded [ %s ] ReEncodeFont\n" % (self.otffont.fontname, self.otffont.fontname, " ".join(["/%s" % glyphname for glyphname in encvector])))
        file.write("%%EndRessource\n")


class otftext_pt(baseclasses.canvasitem):

    def __init__(self, otffont, x_pt, y_pt, text, size):
        self.otffont = otffont
        self.x_pt = x_pt
        self.y_pt = y_pt
        self.size = size
        self.text = text

        try:
            self.names = [latin1pos2name[ord(c)] for c in self.text]
        except KeyError as e:
            raise RuntimeError("missing glyph %s in font %s" % (c, self.otffont.fontname))

        i = 0
        while i < len(self.names):
            for nextnames, ligature in self.otffont.ligatures.get(self.names[i], []):
                 if i + len(nextnames) < len(self.names) and nextnames == self.names[i+1:i+1+len(nextnames)]:
                     self.names[i] = ligature
                     del self.names[i+1:i+1+len(nextnames)]
                     break
            i += 1

        for name in self.names:
            if name not in self.otffont.name2pos:
                raise RuntimeError("missing glyph named %s in font %s" % (name, self.otffont.fontname))
            self.otffont.usedchars[name] = True

        factor = size/1000.0
        depth = None
        height = None
        width = 0
        for name in self.names:
            pos = self.otffont.name2pos[name]
            if depth is None or -self.otffont.depth[pos] > depth:
                depth = -self.otffont.depth[pos]
            if height is None or self.otffont.height[pos] > height:
                height = self.otffont.height[pos]
            width += self.otffont.widths[pos]
        for name1, name2 in zip(self.names[:-1], self.names[1:]):
            pos1 = self.otffont.name2pos[name1]
            pos2 = self.otffont.name2pos[name2]
            width += self.otffont.kerning.get(pos1, {}).get(pos2, 0)
        self.width_pt = factor*width
        self.height_pt = factor*height
        self.depth_pt = factor*depth
        self.width = self.width_pt * unit.t_pt
        self.height = self.height_pt * unit.t_pt
        self.depth = self.depth_pt * unit.t_pt

    def bbox(self):
        return bbox.bbox_pt(self.x_pt,
                            self.y_pt-self.depth_pt,
                            self.x_pt+self.width_pt,
                            self.y_pt+self.height_pt)

    def processPS(self, file, writer, context, registry, bbox):
        bbox += self.bbox()
        registry.add(_ReEncodeFont)
        registry.add(otffontresource(self.otffont))
        file.write("/%s-PyXencoded %g selectfont\n" % (self.otffont.fontname, self.size))
        file.write("%f %f moveto (" % (self.x_pt, self.y_pt))
        for i, name in enumerate(self.names):
            if i:
                kern = self.otffont.kerning.get(self.otffont.name2pos[self.names[i-1]], {}).get(self.otffont.name2pos[name], 0)
                if kern:
                    file.write(") show\n%f 0 rmoveto (" % (kern*self.size/1000.0))
            file.write("\\%03o" % self.otffont.encoding[name])
        file.write(") show\n")

