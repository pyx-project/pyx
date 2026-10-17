# -*- encoding: utf-8 -*-
#
#
# Copyright (C) 2007-2026 André Wobst <wobsta@pyx-project.org>
#
# This file is part of PyX (https://pyx-project.org/).
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

import binascii, math, struct
try:
    import zlib
    haszlib = True
except ImportError:
    haszlib = False

from pyx import trafo
from pyx.path import path, moveto_pt, lineto_pt, curveto_pt, closepath
from . import afmfile, metric, t1file

macnames = [".notdef", ".null", "nonmarkingreturn", "space", "exclam",
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

cff_standard_strings = [
    ".notdef", "space", "exclam", "quotedbl", "numbersign", "dollar", "percent", "ampersand",
    "quoteright", "parenleft", "parenright", "asterisk", "plus", "comma", "hyphen", "period",
    "slash", "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "colon", "semicolon", "less", "equal", "greater", "question", "at", "A", "B", "C", "D",
    "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V",
    "W", "X", "Y", "Z", "bracketleft", "backslash", "bracketright", "asciicircum", "underscore",
    "quoteleft", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o",
    "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "braceleft", "bar", "braceright",
    "asciitilde", "exclamdown", "cent", "sterling", "fraction", "yen", "florin", "section",
    "currency", "quotesingle", "quotedblleft", "guillemotleft", "guilsinglleft", "guilsinglright",
    "fi", "fl", "endash", "dagger", "daggerdbl", "periodcentered", "paragraph", "bullet",
    "quotesinglbase", "quotedblbase", "quotedblright", "guillemotright", "ellipsis", "perthousand",
    "questiondown", "grave", "acute", "circumflex", "tilde", "macron", "breve", "dotaccent",
    "dieresis", "ring", "cedilla", "hungarumlaut", "ogonek", "caron", "emdash", "AE",
    "ordfeminine", "Lslash", "Oslash", "OE", "ordmasculine", "ae", "dotlessi", "lslash",
    "oslash", "oe", "germandbls", "onesuperior", "logicalnot", "mu", "trademark", "Eth",
    "onehalf", "plusminus", "Thorn", "onequarter", "divide", "brokenbar", "degree", "thorn",
    "threequarters", "twosuperior", "registered", "minus", "eth", "multiply", "threesuperior",
    "copyright", "Aacute", "Acircumflex", "Adieresis", "Agrave", "Aring", "Atilde", "Ccedilla",
    "Eacute", "Ecircumflex", "Edieresis", "Egrave", "Iacute", "Icircumflex", "Idieresis",
    "Igrave", "Ntilde", "Oacute", "Ocircumflex", "Odieresis", "Ograve", "Otilde", "Scaron",
    "Uacute", "Ucircumflex", "Udieresis", "Ugrave", "Yacute", "Ydieresis", "Zcaron", "aacute",
    "acircumflex", "adieresis", "agrave", "aring", "atilde", "ccedilla", "eacute", "ecircumflex",
    "edieresis", "egrave", "iacute", "icircumflex", "idieresis", "igrave", "ntilde", "oacute",
    "ocircumflex", "odieresis", "ograve", "otilde", "scaron", "uacute", "ucircumflex", "udieresis",
    "ugrave", "yacute", "ydieresis", "zcaron", "exclamsmall", "Hungarumlautsmall",
    "dollaroldstyle", "dollarsuperior", "ampersandsmall", "Acutesmall", "parenleftsuperior",
    "parenrightsuperior", "twodotenleader", "onedotenleader", "zerooldstyle", "oneoldstyle",
    "twooldstyle", "threeoldstyle", "fouroldstyle", "fiveoldstyle", "sixoldstyle",
    "sevenoldstyle", "eightoldstyle", "nineoldstyle", "commasuperior", "threequartersemdash",
    "periodsuperior", "questionsmall", "asuperior", "bsuperior", "centsuperior", "dsuperior",
    "esuperior", "isuperior", "lsuperior", "msuperior", "nsuperior", "osuperior", "rsuperior",
    "ssuperior", "tsuperior", "ff", "ffi", "ffl", "parenleftinferior", "parenrightinferior",
    "Circumflexsmall", "hyphensuperior", "Gravesmall", "Asmall", "Bsmall", "Csmall", "Dsmall",
    "Esmall", "Fsmall", "Gsmall", "Hsmall", "Ismall", "Jsmall", "Ksmall", "Lsmall", "Msmall",
    "Nsmall", "Osmall", "Psmall", "Qsmall", "Rsmall", "Ssmall", "Tsmall", "Usmall", "Vsmall",
    "Wsmall", "Xsmall", "Ysmall", "Zsmall", "colonmonetary", "onefitted", "rupiah", "Tildesmall",
    "exclamdownsmall", "centoldstyle", "Lslashsmall", "Scaronsmall", "Zcaronsmall",
    "Dieresissmall", "Brevesmall", "Caronsmall", "Dotaccentsmall", "Macronsmall", "figuredash",
    "hypheninferior", "Ogoneksmall", "Ringsmall", "Cedillasmall", "questiondownsmall",
    "oneeighth", "threeeighths", "fiveeighths", "seveneighths", "onethird", "twothirds",
    "zerosuperior", "foursuperior", "fivesuperior", "sixsuperior", "sevensuperior",
    "eightsuperior", "ninesuperior", "zeroinferior", "oneinferior", "twoinferior",
    "threeinferior", "fourinferior", "fiveinferior", "sixinferior", "seveninferior",
    "eightinferior", "nineinferior", "centinferior", "dollarinferior", "periodinferior",
    "commainferior", "Agravesmall", "Aacutesmall", "Acircumflexsmall", "Atildesmall",
    "Adieresissmall", "Aringsmall", "AEsmall", "Ccedillasmall", "Egravesmall", "Eacutesmall",
    "Ecircumflexsmall", "Edieresissmall", "Igravesmall", "Iacutesmall", "Icircumflexsmall",
    "Idieresissmall", "Ethsmall", "Ntildesmall", "Ogravesmall", "Oacutesmall",
    "Ocircumflexsmall", "Otildesmall", "Odieresissmall", "OEsmall", "Oslashsmall",
    "Ugravesmall", "Uacutesmall", "Ucircumflexsmall", "Udieresissmall", "Yacutesmall",
    "Thornsmall", "Ydieresissmall", "001.000", "001.001", "001.002", "001.003", "Black",
    "Bold", "Book", "Light", "Medium", "Regular", "Roman", "Semibold"
]
cff_standard_string_to_sid = {name: sid for sid, name in enumerate(cff_standard_strings)}

codepoint2glyphname = {ord(ch): name for ch, name in afmfile.unicodestring.items() if len(ch) == 1}


def checksum(data):
    pad = (4 - len(data) % 4) % 4
    if pad:
        data = data + b"\x00" * pad
    return sum(struct.unpack(">%dL" % (len(data) // 4), data)) & 0xffffffff


def _read_coverage(buf, pos):
    fmt, = struct.unpack(">H", buf[pos:pos+2])
    if fmt == 1:
        count, = struct.unpack(">H", buf[pos+2:pos+4])
        return list(struct.unpack(">%dH" % count, buf[pos+4:pos+4+2*count]))
    elif fmt == 2:
        range_count, = struct.unpack(">H", buf[pos+2:pos+4])
        glyphs = []
        for i in range(range_count):
            start_gid, end_gid, start_cov = struct.unpack(">HHH", buf[pos+4+6*i:pos+10+6*i])
            glyphs.extend(range(start_gid, end_gid + 1))
        return glyphs
    return []


def _read_classdef(buf, pos):
    fmt, = struct.unpack(">H", buf[pos:pos+2])
    classes = {}
    if fmt == 1:
        start_gid, count = struct.unpack(">HH", buf[pos+2:pos+6])
        vals = struct.unpack(">%dH" % count, buf[pos+6:pos+6+2*count])
        for i, v in enumerate(vals):
            if v:
                classes[start_gid + i] = v
    elif fmt == 2:
        range_count, = struct.unpack(">H", buf[pos+2:pos+4])
        for i in range(range_count):
            start_gid, end_gid, cls = struct.unpack(">HHH", buf[pos+4+6*i:pos+10+6*i])
            if cls:
                for gid in range(start_gid, end_gid + 1):
                    classes[gid] = cls
    return classes


def _read_cff_index(buf, pos):
    count, = struct.unpack(">H", buf[pos:pos+2])
    if count == 0:
        return [], pos + 2
    off_size = buf[pos+2]
    pos += 3
    offsets = [int.from_bytes(buf[pos+i*off_size:pos+(i+1)*off_size], "big") for i in range(count + 1)]
    data_start = pos + (count + 1) * off_size - 1
    items = [buf[data_start+offsets[i]:data_start+offsets[i+1]] for i in range(count)]
    return items, data_start + offsets[-1]


def _make_cff_index(items):
    if not items:
        return b"\x00\x00"
    offsets = [1]
    for item in items:
        offsets.append(offsets[-1] + len(item))
    max_off = offsets[-1]
    if max_off < 256:
        off_size = 1
    elif max_off < 65536:
        off_size = 2
    elif max_off < 16777216:
        off_size = 3
    else:
        off_size = 4
    res = bytearray(struct.pack(">HB", len(items), off_size))
    for off in offsets:
        res.extend(off.to_bytes(off_size, "big"))
    for item in items:
        res.extend(item)
    return bytes(res)


def _parse_cff_dict(buf):
    pos = 0
    stack = []
    res = {}
    while pos < len(buf):
        b0 = buf[pos]
        pos += 1
        if b0 <= 21:
            if b0 == 12:
                op = (12, buf[pos])
                pos += 1
            else:
                op = b0
            res[op] = stack
            stack = []
        elif b0 == 28:
            stack.append(struct.unpack(">h", buf[pos:pos+2])[0])
            pos += 2
        elif b0 == 29:
            stack.append(struct.unpack(">i", buf[pos:pos+4])[0])
            pos += 4
        elif b0 == 30:
            nibbles = []
            while True:
                b = buf[pos]
                pos += 1
                for nib in (b >> 4, b & 0x0f):
                    if nib == 15:
                        break
                    nibbles.append({10: ".", 11: "E", 12: "E-", 14: "-"}.get(nib, str(nib)))
                else:
                    continue
                break
            stack.append(float("".join(nibbles)))
        elif 32 <= b0 <= 246:
            stack.append(b0 - 139)
        elif 247 <= b0 <= 250:
            stack.append((b0 - 247) * 256 + buf[pos] + 108)
            pos += 1
        elif 251 <= b0 <= 254:
            stack.append(-(b0 - 251) * 256 - buf[pos] - 108)
            pos += 1
    return res


def _encode_cff_int(val):
    val = int(round(val))
    if -107 <= val <= 107:
        return bytes([val + 139])
    elif 108 <= val <= 1131:
        val -= 108
        return bytes([(val >> 8) + 247, val & 0xff])
    elif -1131 <= val <= -108:
        val = -val - 108
        return bytes([(val >> 8) + 251, val & 0xff])
    elif -32768 <= val <= 32767:
        return b"\x1c" + struct.pack(">h", val)
    else:
        return b"\x1d" + struct.pack(">i", val)


def _encode_cff_fixed_int(val):
    return b"\x1d" + struct.pack(">i", int(val))


def _encode_cff_float(val):
    if int(val) == val:
        return _encode_cff_int(int(val))
    s = ("%g" % val).upper().replace("E-", "c").replace("E+", "b").replace("E", "b")
    nibbles = []
    for ch in s:
        if "0" <= ch <= "9":
            nibbles.append(ord(ch) - ord("0"))
        elif ch == ".":
            nibbles.append(10)
        elif ch == "b":
            nibbles.append(11)
        elif ch == "c":
            nibbles.append(12)
        elif ch == "-":
            nibbles.append(14)
    nibbles.append(15)
    if len(nibbles) % 2:
        nibbles.append(15)
    out = bytearray([30])
    for i in range(0, len(nibbles), 2):
        out.append((nibbles[i] << 4) | nibbles[i + 1])
    return bytes(out)


def _cff_subr_bias(n):
    if n < 1240:
        return 107
    elif n < 33900:
        return 1131
    return 32768


class OTFfile(metric.metric):

    def __init__(self, otffile):
        if isinstance(otffile, (bytes, bytearray)):
            self.otfdata = bytes(otffile)
        elif hasattr(otffile, "read"):
            self.otfdata = otffile.read()
        else:
            with open(otffile, "rb") as f:
                self.otfdata = f.read()

        sfntVersion, numTables = struct.unpack(">4sHHHH", self.otfdata[:12])[:2]
        if sfntVersion not in (b"\x00\x01\x00\x00", b"OTTO", b"true", b"typ1"):
            raise RuntimeError("invalid font file (sfnt version error)")
        self.sfntVersion = sfntVersion
        self.otfsplit = []
        self.tables = tables = {}
        self.glyfoffset = None
        self.glyflength = None
        self.locaoffset = None
        for numTable in range(numTables):
            tag, checkSum, offset, length = struct.unpack(">4sLLL", self.otfdata[12+16*numTable:28+16*numTable])
            tables[tag] = self.otfdata[offset:offset+length]
            if tag == b"glyf":
                self.glyfoffset = offset
                self.glyflength = length
            elif tag == b"loca":
                self.locaoffset = offset
            self.otfsplit.append(offset)

        self.is_cff = b"CFF " in tables
        self.unitsPerEm, = struct.unpack(">H", tables[b"head"][18:20])
        self.factor = factor = 1000.0 / self.unitsPerEm
        self.raw_xMin, self.raw_yMin, self.raw_xMax, self.raw_yMax = struct.unpack(">4h", tables[b"head"][36:44])
        self.xMin, self.yMin, self.xMax, self.yMax = [int(round(factor * value)) for value in (self.raw_xMin, self.raw_yMin, self.raw_xMax, self.raw_yMax)]
        self.indexToLocFormat, = struct.unpack(">h", tables[b"head"][50:52])
        if self.is_cff:
            self.fontmatrix = trafo.scale_pt(1.0 / self.unitsPerEm, 1.0 / self.unitsPerEm)
        else:
            self.fontmatrix = trafo.scale_pt(1.0, 1.0)

        self.numGlyphs = numGlyphs = struct.unpack(">H", tables[b"maxp"][4:6])[0]

        if b"hhea" in tables:
            hhea_ascent, hhea_descent, hhea_linegap = struct.unpack(">hhh", tables[b"hhea"][4:10])
            numHMetrics, = struct.unpack(">H", tables[b"hhea"][34:36])
            self.ascent = int(round(factor * hhea_ascent))
            self.descent = int(round(factor * hhea_descent))
        else:
            numHMetrics = numGlyphs
            self.ascent = self.yMax
            self.descent = self.yMin

        self.raw_widths = []
        self.widths = []
        last_aw = 0
        hmtx = tables[b"hmtx"]
        for i in range(numGlyphs):
            if i < numHMetrics and 4 * i + 2 <= len(hmtx):
                last_aw, = struct.unpack(">H", hmtx[4*i:4*i+2])
            self.raw_widths.append(last_aw)
            self.widths.append(factor * last_aw)

        if b"OS/2" in tables and len(tables[b"OS/2"]) >= 72:
            self.weightClass, = struct.unpack(">H", tables[b"OS/2"][4:6])
            typo_asc, typo_desc = struct.unpack(">hh", tables[b"OS/2"][68:72])
            if typo_asc:
                self.ascent = int(round(factor * typo_asc))
            if typo_desc:
                self.descent = int(round(factor * typo_desc))
            if len(tables[b"OS/2"]) >= 90:
                cap_h, = struct.unpack(">h", tables[b"OS/2"][88:90])
                self.capHeight = int(round(factor * cap_h)) if cap_h else self.ascent
            else:
                self.capHeight = self.ascent
        else:
            self.weightClass = 400
            self.capHeight = self.ascent

        if b"name" not in tables:
            raise RuntimeError("invalid font file (name table missing error)")
        fmt, count, stringOffset = struct.unpack(">HHH", tables[b"name"][:6])
        self.fontname = ""
        self.displayname = "unknown"
        self.displaystyle = "unknown"
        for i in range(count):
            platformID, encodingID, languageID, nameID, length, offset = struct.unpack(">HHHHHH", tables[b"name"][6+12*i:18+12*i])
            raw_str = tables[b"name"][stringOffset+offset:stringOffset+offset+length]
            if platformID == 1:
                val = raw_str.decode("mac_roman", errors="replace")
                if nameID == 1 and self.displayname == "unknown":
                    self.displayname = val
                elif nameID == 2 and self.displaystyle == "unknown":
                    self.displaystyle = val
                elif nameID == 6 and not self.fontname:
                    self.fontname = val
            elif platformID in (0, 3) and (platformID == 0 or (encodingID in (1, 10) and languageID == 1033)):
                val = raw_str.decode("utf-16be", errors="replace")
                if nameID == 1:
                    self.displayname = val
                elif nameID == 2:
                    self.displaystyle = val
                elif nameID == 6:
                    self.fontname = val
        if not self.fontname:
            raise RuntimeError("invalid font file (nameID missing error)")
        self.name = self.fontname

        if b"post" not in tables:
            raise RuntimeError("invalid font file (post (== PostScript) table missing)")
        self.italicAngle = struct.unpack(">i", tables[b"post"][4:8])[0] / 65536.0
        self.isFixedPitch, = struct.unpack(">L", tables[b"post"][12:16])

        self.charstrings = [None] * numGlyphs
        self.name2pos = {}
        post_ver = tables[b"post"][:4]
        if post_ver == b"\x00\x01\x00\x00":
            for i in range(min(numGlyphs, len(macnames))):
                name = macnames[i]
                self.charstrings[i] = name
                self.name2pos[name] = i
        elif post_ver == b"\x00\x02\x00\x00":
            count, = struct.unpack(">H", tables[b"post"][32:34])
            indices = struct.unpack(">%dH" % count, tables[b"post"][34:34+2*count])
            pos = 34 + 2 * count
            names = []
            while pos < len(tables[b"post"]):
                nlen = tables[b"post"][pos]
                names.append(tables[b"post"][pos+1:pos+1+nlen].decode("ascii", errors="replace"))
                pos += nlen + 1
            for i, index in enumerate(indices):
                if i >= numGlyphs:
                    break
                if 0 <= index < 258:
                    name = macnames[index]
                elif index - 258 < len(names):
                    name = names[index - 258]
                else:
                    name = ".notdef"
                if name in self.name2pos:
                    self.charstrings[i] = None
                else:
                    self.charstrings[i] = name
                    self.name2pos[name] = i
        elif post_ver == b"\x00\x02\x00\x05":
            count, = struct.unpack(">H", tables[b"post"][32:34])
            indices = struct.unpack(">%db" % count, tables[b"post"][34:34+count])
            for i, index in enumerate(indices):
                if i < numGlyphs:
                    name = macnames[i + index]
                    self.charstrings[i] = name
                    self.name2pos[name] = i
        elif post_ver == b"\x00\x03\x00\x00":
            self.charstrings[0] = ".notdef"
            self.name2pos[".notdef"] = 0
        elif post_ver == b"\x00\x04\x00\x00":
            raise RuntimeError("post table format 4 for Japanese, Chinese or Korean is not implemented")
        else:
            raise RuntimeError("invalid post table format")

        if self.is_cff:
            self._init_cff(tables[b"CFF "])
        else:
            self._init_glyf(tables[b"loca"], tables[b"glyf"])

        self.cmap = {}
        if b"cmap" in tables:
            self._init_cmap(tables[b"cmap"])

        self.encoding = [self.charstrings[i] if i < len(self.charstrings) else None for i in range(256)]

        self.kerning = {}
        if b"kern" in tables:
            self._init_kern(tables[b"kern"])
        if b"GPOS" in tables:
            self._init_gpos(tables[b"GPOS"])

        self.ligatures = {}
        if b"GSUB" in tables:
            self._init_gsub(tables[b"GSUB"])

    def _init_glyf(self, loca_data, glyf_data):
        if not self.indexToLocFormat:
            self.glyphLocations = [2 * location for location in struct.unpack(">%dH" % (self.numGlyphs + 1), loca_data[:2*(self.numGlyphs+1)])]
        else:
            self.glyphLocations = list(struct.unpack(">%dL" % (self.numGlyphs + 1), loca_data[:4*(self.numGlyphs+1)]))

        self.depth = []
        self.height = []
        for i in range(self.numGlyphs):
            loc1 = self.glyphLocations[i]
            loc2 = self.glyphLocations[i + 1]
            if loc1 < loc2 and loc1 + 10 <= len(glyf_data):
                yMin, xMax, yMax = struct.unpack(">hhh", glyf_data[loc1+4:loc1+10])
                self.depth.append(self.factor * yMin)
                self.height.append(self.factor * yMax)
            else:
                self.depth.append(0.0)
                self.height.append(0.0)

    def _init_cff(self, cff_data):
        self.cff_data = cff_data
        hdr_size = cff_data[2]
        names, pos = _read_cff_index(cff_data, hdr_size)
        top_dicts, pos = _read_cff_index(cff_data, pos)
        strings, pos = _read_cff_index(cff_data, pos)
        self.cff_gsubrs, pos = _read_cff_index(cff_data, pos)
        self.cff_strings = [s.decode("ascii", errors="replace") for s in strings]
        self.cff_top_dict = td = _parse_cff_dict(top_dicts[0])

        cs_offset = td[17][0]
        self.cff_charstrings, _ = _read_cff_index(cff_data, cs_offset)

        self.cff_is_cid = (12, 30) in td
        self.cff_subrs = []
        self.cff_default_width = 0
        self.cff_nominal_width = 0
        self.cff_fdarray = None
        self.cff_fdselect = None

        if self.cff_is_cid and (12, 36) in td:
            fd_items, _ = _read_cff_index(cff_data, td[(12, 36)][0])
            self.cff_fdarray = []
            for fd_bytes in fd_items:
                fdict = _parse_cff_dict(fd_bytes)
                subrs = []
                def_w = 0
                nom_w = 0
                if 18 in fdict:
                    psize, poff = fdict[18]
                    pdict = _parse_cff_dict(cff_data[poff:poff+psize])
                    def_w = pdict.get(20, [0])[0]
                    nom_w = pdict.get(21, [0])[0]
                    if 19 in pdict:
                        subrs, _ = _read_cff_index(cff_data, poff + pdict[19][0])
                self.cff_fdarray.append((subrs, def_w, nom_w))
            if self.cff_fdarray:
                self.cff_subrs, self.cff_default_width, self.cff_nominal_width = self.cff_fdarray[0]
            if (12, 37) in td:
                fds_pos = td[(12, 37)][0]
                fds_fmt = cff_data[fds_pos]
                if fds_fmt == 0:
                    self.cff_fdselect = list(cff_data[fds_pos+1:fds_pos+1+len(self.cff_charstrings)])
                elif fds_fmt == 3:
                    n_ranges, = struct.unpack(">H", cff_data[fds_pos+1:fds_pos+3])
                    self.cff_fdselect = [0] * len(self.cff_charstrings)
                    for r in range(n_ranges):
                        first_gid, fd_idx = struct.unpack(">HB", cff_data[fds_pos+3+3*r:fds_pos+6+3*r])
                        next_gid, = struct.unpack(">H", cff_data[fds_pos+6+3*r:fds_pos+8+3*r])
                        for g in range(first_gid, min(next_gid, len(self.cff_charstrings))):
                            self.cff_fdselect[g] = fd_idx
        elif 18 in td:
            psize, poff = td[18]
            pdict = _parse_cff_dict(cff_data[poff:poff+psize])
            self.cff_default_width = pdict.get(20, [0])[0]
            self.cff_nominal_width = pdict.get(21, [0])[0]
            if 19 in pdict:
                self.cff_subrs, _ = _read_cff_index(cff_data, poff + pdict[19][0])

        if not self.cff_is_cid:
            charset_off = td.get(15, [0])[0]
            sids = [0]
            if charset_off == 0:
                sids.extend(range(1, min(self.numGlyphs, 229)))
            elif charset_off > 2:
                cfmt = cff_data[charset_off]
                cpos = charset_off + 1
                if cfmt == 0:
                    while len(sids) < self.numGlyphs and cpos + 2 <= len(cff_data):
                        sid, = struct.unpack(">H", cff_data[cpos:cpos+2])
                        sids.append(sid)
                        cpos += 2
                elif cfmt in (1, 2):
                    step = 3 if cfmt == 1 else 4
                    unpack_fmt = ">HB" if cfmt == 1 else ">HH"
                    while len(sids) < self.numGlyphs and cpos + step <= len(cff_data):
                        first_sid, n_left = struct.unpack(unpack_fmt, cff_data[cpos:cpos+step])
                        sids.extend(range(first_sid, first_sid + n_left + 1))
                        cpos += step
            for gid, sid in enumerate(sids[:self.numGlyphs]):
                name = self._cff_sid_to_string(sid)
                if name and self.charstrings[gid] in (None, ".notdef"):
                    self.charstrings[gid] = name
                if name and name not in self.name2pos:
                    self.name2pos[name] = gid

        self.depth = [None] * self.numGlyphs
        self.height = [None] * self.numGlyphs

    def _cff_sid_to_string(self, sid):
        if sid < len(cff_standard_strings):
            return cff_standard_strings[sid]
        idx = sid - len(cff_standard_strings)
        if idx < len(self.cff_strings):
            return self.cff_strings[idx]
        return None

    def _ensure_cff_glyph_metrics(self, gid):
        if self.depth[gid] is None:
            p = path()
            self._run_cff_charstring(gid, p, trafo.scale_pt(self.factor, self.factor))
            b = p.bbox()
            if b:
                self.depth[gid] = b.lly_pt
                self.height[gid] = b.ury_pt
            else:
                self.depth[gid] = 0.0
                self.height[gid] = 0.0

    def _init_cmap(self, cmap_data):
        version, numTables = struct.unpack(">HH", cmap_data[:4])
        subtables = []
        for i in range(numTables):
            platformID, encodingID, offset = struct.unpack(">HHL", cmap_data[4+8*i:12+8*i])
            fmt, = struct.unpack(">H", cmap_data[offset:offset+2])
            if (platformID == 3 and encodingID in (1, 10)) or platformID == 0:
                priority = 0 if fmt == 12 else 1
                subtables.append((priority, fmt, offset))
        subtables.sort()

        for _, fmt, offset in subtables:
            if fmt == 4 and not self.cmap:
                length, language, segCount2 = struct.unpack(">HHH", cmap_data[offset+2:offset+8])
                segCount = segCount2 // 2
                endCounts = struct.unpack(">%dH" % segCount, cmap_data[offset+14:offset+14+segCount2])
                startCounts = struct.unpack(">%dH" % segCount, cmap_data[offset+16+segCount2:offset+16+2*segCount2])
                idDeltas = struct.unpack(">%dh" % segCount, cmap_data[offset+16+2*segCount2:offset+16+3*segCount2])
                idRangePos = offset + 16 + 3 * segCount2
                idRangeOffsets = struct.unpack(">%dH" % segCount, cmap_data[idRangePos:idRangePos+segCount2])
                for n, (endCount, startCount, idDelta, idRangeOffset) in enumerate(zip(endCounts, startCounts, idDeltas, idRangeOffsets)):
                    if startCount == 0xffff:
                        continue
                    if idRangeOffset:
                        glyph_pos = idRangePos + 2 * n + idRangeOffset
                        count_seg = endCount - startCount + 1
                        gids = struct.unpack(">%dH" % count_seg, cmap_data[glyph_pos:glyph_pos+2*count_seg])
                        for idx_c, gid in enumerate(gids):
                            if gid != 0:
                                gid = (gid + idDelta) & 0xffff
                                if 0 < gid < self.numGlyphs:
                                    self.cmap.setdefault(startCount + idx_c, gid)
                    else:
                        for code in range(startCount, endCount + 1):
                            gid = (code + idDelta) & 0xffff
                            if 0 < gid < self.numGlyphs:
                                self.cmap.setdefault(code, gid)
            elif fmt == 12:
                nGroups, = struct.unpack(">L", cmap_data[offset+12:offset+16])
                for n in range(nGroups):
                    startCode, endCode, startGID = struct.unpack(">LLL", cmap_data[offset+16+12*n:offset+28+12*n])
                    for code in range(startCode, min(endCode + 1, 0x10000)):
                        gid = startGID + (code - startCode)
                        if 0 < gid < self.numGlyphs and code not in self.cmap:
                            self.cmap[code] = gid

        assigned_agl = set()
        assigned_gids = set()
        for code, gid in sorted(self.cmap.items()):
            name = codepoint2glyphname.get(code)
            if name is not None and name not in assigned_agl:
                assigned_agl.add(name)
                self.name2pos[name] = gid
                if gid not in assigned_gids:
                    assigned_gids.add(gid)
                    self.charstrings[gid] = name
        for gid in range(1, self.numGlyphs):
            if self.charstrings[gid] is None:
                gname = "glyph%d" % gid
                self.charstrings[gid] = gname
                if gname not in self.name2pos:
                    self.name2pos[gname] = gid
            else:
                self.name2pos.setdefault(self.charstrings[gid], gid)
        self.unicodestring = dict(afmfile.unicodestring)
        for code, gid in self.cmap.items():
            if self.charstrings[gid]:
                self.unicodestring[chr(code)] = self.charstrings[gid]

    def _init_kern(self, kern_data):
        if len(kern_data) < 4:
            return
        version, nTables = struct.unpack(">HH", kern_data[:4])
        if version != 0:
            return
        pos = 4
        for _ in range(nTables):
            if pos + 6 > len(kern_data):
                break
            sub_ver, length, coverage = struct.unpack(">HHH", kern_data[pos:pos+6])
            if coverage & 0x0003 == 1 and coverage & 0xff00 == 0x0000:
                nPairs, = struct.unpack(">H", kern_data[pos+6:pos+8])
                for nPair in range(nPairs):
                    ppos = pos + 14 + 6 * nPair
                    if ppos + 6 <= len(kern_data):
                        left, right, value = struct.unpack(">HHh", kern_data[ppos:ppos+6])
                        self.kerning.setdefault(left, {})[right] = self.factor * value
            pos += length

    def _init_gpos(self, gpos_data):
        if len(gpos_data) < 10:
            return
        _, f_off, l_off = struct.unpack(">HHH", gpos_data[4:10])
        f_count, = struct.unpack(">H", gpos_data[f_off:f_off+2])
        use_lookup = set()
        for i in range(f_count):
            ftag, off = struct.unpack(">4sH", gpos_data[f_off+2+6*i:f_off+8+6*i])
            if ftag == b"kern":
                _, lcount = struct.unpack(">HH", gpos_data[f_off+off:f_off+off+4])
                use_lookup.update(struct.unpack(">%dH" % lcount, gpos_data[f_off+off+4:f_off+off+4+2*lcount]))
        if not use_lookup:
            return
        l_count, = struct.unpack(">H", gpos_data[l_off:l_off+2])
        for idx in sorted(use_lookup):
            if idx >= l_count:
                continue
            off, = struct.unpack(">H", gpos_data[l_off+2+2*idx:l_off+4+2*idx])
            lpos = l_off + off
            ltype, lflag, scount = struct.unpack(">HHH", gpos_data[lpos:lpos+6])
            for s in range(scount):
                soff, = struct.unpack(">H", gpos_data[lpos+6+2*s:lpos+8+2*s])
                sub_pos = lpos + soff
                actual_type = ltype
                if ltype == 9:
                    _, actual_type, ext_off = struct.unpack(">HHL", gpos_data[sub_pos:sub_pos+8])
                    sub_pos += ext_off
                if actual_type != 2:
                    continue
                pos_fmt, cov_off, vf1, vf2 = struct.unpack(">HHHH", gpos_data[sub_pos:sub_pos+8])
                if vf1 != 4 or vf2 != 0:
                    continue
                cov_glyphs = _read_coverage(gpos_data, sub_pos + cov_off)
                if pos_fmt == 1:
                    pair_set_count, = struct.unpack(">H", gpos_data[sub_pos+8:sub_pos+10])
                    pair_set_offs = struct.unpack(">%dH" % pair_set_count, gpos_data[sub_pos+10:sub_pos+10+2*pair_set_count])
                    for left_gid, ps_off in zip(cov_glyphs, pair_set_offs):
                        ps_pos = sub_pos + ps_off
                        pv_count, = struct.unpack(">H", gpos_data[ps_pos:ps_pos+2])
                        for p in range(pv_count):
                            right_gid, val = struct.unpack(">Hh", gpos_data[ps_pos+2+4*p:ps_pos+6+4*p])
                            if val:
                                self.kerning.setdefault(left_gid, {}).setdefault(right_gid, self.factor * val)
                elif pos_fmt == 2:
                    cd1_off, cd2_off, c1_count, c2_count = struct.unpack(">HHHH", gpos_data[sub_pos+8:sub_pos+16])
                    cd1 = _read_classdef(gpos_data, sub_pos + cd1_off)
                    cd2 = _read_classdef(gpos_data, sub_pos + cd2_off)
                    c1_map = {}
                    for gid in cov_glyphs:
                        c1_map.setdefault(cd1.get(gid, 0), []).append(gid)
                    c2_map = {}
                    for gid, c2 in cd2.items():
                        c2_map.setdefault(c2, []).append(gid)
                    rec_pos = sub_pos + 16
                    for c1 in range(c1_count):
                        left_gids = c1_map.get(c1)
                        for c2 in range(c2_count):
                            val, = struct.unpack(">h", gpos_data[rec_pos:rec_pos+2])
                            rec_pos += 2
                            if val and left_gids and c2 in c2_map:
                                scaled_val = self.factor * val
                                for lg in left_gids:
                                    kdict = self.kerning.setdefault(lg, {})
                                    for rg in c2_map[c2]:
                                        kdict.setdefault(rg, scaled_val)

    def _init_gsub(self, gsub_data):
        if len(gsub_data) < 10:
            return
        ScriptList, FeatureList, LookupList = struct.unpack(">HHH", gsub_data[4:10])
        useLookup = set()
        FeatureCount, = struct.unpack(">H", gsub_data[FeatureList:FeatureList+2])
        for i in range(FeatureCount):
            FeatureTag, offset = struct.unpack(">4sH", gsub_data[FeatureList+2+6*i:FeatureList+8+6*i])
            if FeatureTag in (b"liga", b"rlig"):
                FeatureParams, LookupCount = struct.unpack(">HH", gsub_data[FeatureList+offset:FeatureList+offset+4])
                for idx in struct.unpack(">%dH" % LookupCount, gsub_data[FeatureList+offset+4:FeatureList+offset+4+2*LookupCount]):
                    useLookup.add(idx)
        LookupCount, = struct.unpack(">H", gsub_data[LookupList:LookupList+2])
        for index, offset in enumerate(struct.unpack(">%dH" % LookupCount, gsub_data[LookupList+2:LookupList+2+2*LookupCount])):
            if index not in useLookup:
                continue
            lpos = LookupList + offset
            LookupType, LookupFlag, SubTableCount = struct.unpack(">HHH", gsub_data[lpos:lpos+6])
            for offset2 in struct.unpack(">%dH" % SubTableCount, gsub_data[lpos+6:lpos+6+2*SubTableCount]):
                sub_pos = lpos + offset2
                actual_type = LookupType
                if LookupType == 7:
                    _, actual_type, ext_off = struct.unpack(">HHL", gsub_data[sub_pos:sub_pos+8])
                    sub_pos += ext_off
                if actual_type == 4:
                    SubstFormat, Coverage, LigSetCount = struct.unpack(">HHH", gsub_data[sub_pos:sub_pos+6])
                    glyph0s = _read_coverage(gsub_data, sub_pos + Coverage)
                    for glyph0, offset3 in zip(glyph0s, struct.unpack(">%dH" % LigSetCount, gsub_data[sub_pos+6:sub_pos+6+2*LigSetCount])):
                        ls_pos = sub_pos + offset3
                        LigatureCount, = struct.unpack(">H", gsub_data[ls_pos:ls_pos+2])
                        for offset4 in struct.unpack(">%dH" % LigatureCount, gsub_data[ls_pos+2:ls_pos+2+2*LigatureCount]):
                            lig_pos = ls_pos + offset4
                            LigGlyph, CompCount = struct.unpack(">HH", gsub_data[lig_pos:lig_pos+4])
                            glyphs = struct.unpack(">%dH" % (CompCount - 1), gsub_data[lig_pos+4:lig_pos+4+2*(CompCount-1)])
                            if glyph0 < self.numGlyphs and LigGlyph < self.numGlyphs:
                                g0_name = self.charstrings[glyph0]
                                lig_name = self.charstrings[LigGlyph]
                                comp_names = [self.charstrings[g] for g in glyphs if g < self.numGlyphs]
                                if g0_name and lig_name and len(comp_names) == CompCount - 1 and all(comp_names):
                                    self.ligatures.setdefault(g0_name, []).append((comp_names, lig_name))

    def width_ds(self, glyphname):
        return int(round(self.widths[self.name2pos[glyphname]]))

    def width_pt(self, glyphnames, size_pt):
        return sum(self.widths[self.name2pos[glyphname]] for glyphname in glyphnames) * size_pt / 1000.0

    def height_pt(self, glyphnames, size_pt):
        if not glyphnames:
            return 0.0
        if self.is_cff:
            for glyphname in glyphnames:
                self._ensure_cff_glyph_metrics(self.name2pos[glyphname])
        return max(self.height[self.name2pos[glyphname]] for glyphname in glyphnames) * size_pt / 1000.0

    def depth_pt(self, glyphnames, size_pt):
        if not glyphnames:
            return 0.0
        if self.is_cff:
            for glyphname in glyphnames:
                self._ensure_cff_glyph_metrics(self.name2pos[glyphname])
        return min(self.depth[self.name2pos[glyphname]] for glyphname in glyphnames) * size_pt / 1000.0

    def resolveligatures(self, glyphnames):
        glyphnames = list(glyphnames)
        i = 0
        while i < len(glyphnames):
            for nextnames, ligature in self.ligatures.get(glyphnames[i], []):
                if i + len(nextnames) < len(glyphnames) and nextnames == glyphnames[i+1:i+1+len(nextnames)]:
                    glyphnames[i] = ligature
                    del glyphnames[i+1:i+1+len(nextnames)]
                    break
            else:
                i += 1
        return glyphnames

    def resolvekernings(self, glyphnames, size_pt=None):
        result = [None] * (2 * len(glyphnames) - 1)
        for i, glyphname in enumerate(glyphnames):
            result[2 * i] = glyphname
            if i:
                pos1 = self.name2pos[glyphnames[i - 1]]
                pos2 = self.name2pos[glyphname]
                amount = self.kerning.get(pos1, {}).get(pos2)
                if amount:
                    if size_pt is not None:
                        result[2 * i - 1] = amount * size_pt / 1000.0
                    else:
                        result[2 * i - 1] = amount
        return result

    def writePDFfontinfo(self, file, seriffont=False, symbolfont=False):
        flags = 0
        if self.isFixedPitch:
            flags |= 1 << 0
        if seriffont:
            flags |= 1 << 1
        if symbolfont:
            flags |= 1 << 2
        else:
            flags |= 1 << 5
        if self.italicAngle:
            flags |= 1 << 6
        file.write("/Flags %d\n" % flags)
        file.write("/ItalicAngle %d\n" % int(round(self.italicAngle)))
        file.write("/Ascent %d\n" % self.ascent)
        file.write("/Descent %d\n" % self.descent)
        file.write("/FontBBox [%d %d %d %d]\n" % (self.xMin, self.yMin, self.xMax, self.yMax))
        file.write("/CapHeight %d\n" % self.capHeight)
        stemv = 120 if self.weightClass >= 600 else 70
        file.write("/StemV %d\n" % stemv)

    def _update_glyf_path(self, gid, p, atrafo):
        if gid < 0 or gid >= self.numGlyphs:
            return
        loc1 = self.glyphLocations[gid]
        loc2 = self.glyphLocations[gid + 1]
        if loc1 >= loc2:
            return
        glyf = self.tables[b"glyf"]
        numberOfContours, = struct.unpack(">h", glyf[loc1:loc1+2])
        if numberOfContours == 0:
            return
        if numberOfContours > 0:
            endPts = struct.unpack(">%dH" % numberOfContours, glyf[loc1+10:loc1+10+2*numberOfContours])
            numPoints = endPts[-1] + 1
            pos = loc1 + 10 + 2 * numberOfContours
            instrLen, = struct.unpack(">H", glyf[pos:pos+2])
            pos += 2 + instrLen
            flags = []
            while len(flags) < numPoints:
                f = glyf[pos]
                pos += 1
                flags.append(f)
                if f & 0x08:
                    repeat = glyf[pos]
                    pos += 1
                    flags.extend([f] * repeat)
            xs = []
            x = 0
            for f in flags:
                if f & 0x02:
                    dx = glyf[pos]
                    pos += 1
                    x += dx if (f & 0x10) else -dx
                elif not (f & 0x10):
                    dx, = struct.unpack(">h", glyf[pos:pos+2])
                    pos += 2
                    x += dx
                xs.append(x)
            ys = []
            y = 0
            for f in flags:
                if f & 0x04:
                    dy = glyf[pos]
                    pos += 1
                    y += dy if (f & 0x20) else -dy
                elif not (f & 0x20):
                    dy, = struct.unpack(">h", glyf[pos:pos+2])
                    pos += 2
                    y += dy
                ys.append(y)
            start = 0
            for end in endPts:
                pts = [(xs[idx], ys[idx], bool(flags[idx] & 0x01)) for idx in range(start, end + 1)]
                start = end + 1
                if not pts:
                    continue
                expanded = []
                n = len(pts)
                for idx in range(n):
                    x0, y0, on0 = pts[idx]
                    x1, y1, on1 = pts[(idx + 1) % n]
                    expanded.append((x0, y0, on0))
                    if not on0 and not on1:
                        expanded.append((0.5 * (x0 + x1), 0.5 * (y0 + y1), True))
                if not expanded[0][2]:
                    expanded = [expanded[-1]] + expanded[:-1]
                sx, sy, _ = expanded[0]
                p.append(moveto_pt(*atrafo.apply_pt(sx, sy)))
                cx, cy = sx, sy
                m = len(expanded)
                idx = 1
                while idx <= m:
                    px, py, on = expanded[idx % m]
                    if on:
                        p.append(lineto_pt(*atrafo.apply_pt(px, py)))
                        cx, cy = px, py
                        idx += 1
                    else:
                        nx, ny, _ = expanded[(idx + 1) % m]
                        c1x = cx + (2.0 / 3.0) * (px - cx)
                        c1y = cy + (2.0 / 3.0) * (py - cy)
                        c2x = nx + (2.0 / 3.0) * (px - nx)
                        c2y = ny + (2.0 / 3.0) * (py - ny)
                        p.append(curveto_pt(*(atrafo.apply_pt(c1x, c1y) + atrafo.apply_pt(c2x, c2y) + atrafo.apply_pt(nx, ny))))
                        cx, cy = nx, ny
                        idx += 2
                p.append(closepath())
        else:
            pos = loc1 + 10
            while True:
                flags, comp_gid = struct.unpack(">HH", glyf[pos:pos+4])
                pos += 4
                if flags & 0x0001:
                    if flags & 0x0002:
                        dx, dy = struct.unpack(">hh", glyf[pos:pos+4])
                    else:
                        dx, dy = 0, 0
                    pos += 4
                else:
                    if flags & 0x0002:
                        dx, dy = struct.unpack(">bb", glyf[pos:pos+2])
                    else:
                        dx, dy = 0, 0
                    pos += 2
                a, b, c, d = 1.0, 0.0, 0.0, 1.0
                if flags & 0x0008:
                    s, = struct.unpack(">h", glyf[pos:pos+2])
                    a = d = s / 16384.0
                    pos += 2
                elif flags & 0x0040:
                    sx, sy = struct.unpack(">hh", glyf[pos:pos+4])
                    a, d = sx / 16384.0, sy / 16384.0
                    pos += 4
                elif flags & 0x0080:
                    s0, s1, s2, s3 = struct.unpack(">hhhh", glyf[pos:pos+8])
                    a, b, c, d = s0 / 16384.0, s1 / 16384.0, s2 / 16384.0, s3 / 16384.0
                    pos += 8
                comp_trafo = atrafo * trafo.trafo_pt(matrix=((a, c), (b, d)), vector=(dx, dy))
                self._update_glyf_path(comp_gid, p, comp_trafo)
                if not (flags & 0x0020):
                    break

    def _run_cff_charstring(self, gid, p, atrafo):
        if gid < 0 or gid >= len(self.cff_charstrings):
            return
        if self.cff_fdarray and self.cff_fdselect:
            subrs, _, _ = self.cff_fdarray[self.cff_fdselect[gid]]
        else:
            subrs = self.cff_subrs
        gsubrs = self.cff_gsubrs
        local_bias = _cff_subr_bias(len(subrs))
        global_bias = _cff_subr_bias(len(gsubrs))

        state = {"x": 0.0, "y": 0.0, "open": False, "stems": 0, "has_width": False}
        stack = []

        def close_current():
            if state["open"]:
                p.append(closepath())
                state["open"] = False

        def check_width(even_args=True):
            if not state["has_width"]:
                if (len(stack) % 2 == 1) if even_args else (len(stack) > 1):
                    stack.pop(0)
                state["has_width"] = True

        def execute(code):
            pos = 0
            n = len(code)
            while pos < n:
                b0 = code[pos]
                pos += 1
                if b0 == 28:
                    stack.append(struct.unpack(">h", code[pos:pos+2])[0])
                    pos += 2
                elif 32 <= b0 <= 246:
                    stack.append(b0 - 139)
                elif 247 <= b0 <= 250:
                    stack.append((b0 - 247) * 256 + code[pos] + 108)
                    pos += 1
                elif 251 <= b0 <= 254:
                    stack.append(-(b0 - 251) * 256 - code[pos] - 108)
                    pos += 1
                elif b0 == 255:
                    stack.append(struct.unpack(">i", code[pos:pos+4])[0] / 65536.0)
                    pos += 4
                elif b0 in (1, 3, 18, 23):
                    check_width(True)
                    state["stems"] += len(stack) // 2
                    stack.clear()
                elif b0 in (19, 20):
                    check_width(True)
                    state["stems"] += len(stack) // 2
                    stack.clear()
                    pos += (state["stems"] + 7) // 8
                elif b0 == 21:
                    if not state["has_width"]:
                        if len(stack) > 2:
                            stack.pop(0)
                        state["has_width"] = True
                    close_current()
                    dy = stack.pop()
                    dx = stack.pop()
                    stack.clear()
                    state["x"] += dx
                    state["y"] += dy
                    p.append(moveto_pt(*atrafo.apply_pt(state["x"], state["y"])))
                    state["open"] = True
                elif b0 == 22:
                    check_width(False)
                    close_current()
                    dx = stack.pop()
                    stack.clear()
                    state["x"] += dx
                    p.append(moveto_pt(*atrafo.apply_pt(state["x"], state["y"])))
                    state["open"] = True
                elif b0 == 4:
                    check_width(False)
                    close_current()
                    dy = stack.pop()
                    stack.clear()
                    state["y"] += dy
                    p.append(moveto_pt(*atrafo.apply_pt(state["x"], state["y"])))
                    state["open"] = True
                elif b0 == 5:
                    while len(stack) >= 2:
                        dx = stack.pop(0)
                        dy = stack.pop(0)
                        state["x"] += dx
                        state["y"] += dy
                        p.append(lineto_pt(*atrafo.apply_pt(state["x"], state["y"])))
                    stack.clear()
                elif b0 in (6, 7):
                    horiz = (b0 == 6)
                    while stack:
                        d = stack.pop(0)
                        if horiz:
                            state["x"] += d
                        else:
                            state["y"] += d
                        p.append(lineto_pt(*atrafo.apply_pt(state["x"], state["y"])))
                        horiz = not horiz
                elif b0 == 8:
                    while len(stack) >= 6:
                        dx1, dy1, dx2, dy2, dx3, dy3 = stack[:6]
                        del stack[:6]
                        x1, y1 = state["x"] + dx1, state["y"] + dy1
                        x2, y2 = x1 + dx2, y1 + dy2
                        x3, y3 = x2 + dx3, y2 + dy3
                        state["x"], state["y"] = x3, y3
                        p.append(curveto_pt(*(atrafo.apply_pt(x1, y1) + atrafo.apply_pt(x2, y2) + atrafo.apply_pt(x3, y3))))
                    stack.clear()
                elif b0 == 24:
                    while len(stack) >= 8:
                        dx1, dy1, dx2, dy2, dx3, dy3 = stack[:6]
                        del stack[:6]
                        x1, y1 = state["x"] + dx1, state["y"] + dy1
                        x2, y2 = x1 + dx2, y1 + dy2
                        x3, y3 = x2 + dx3, y2 + dy3
                        state["x"], state["y"] = x3, y3
                        p.append(curveto_pt(*(atrafo.apply_pt(x1, y1) + atrafo.apply_pt(x2, y2) + atrafo.apply_pt(x3, y3))))
                    if len(stack) >= 2:
                        state["x"] += stack[0]
                        state["y"] += stack[1]
                        p.append(lineto_pt(*atrafo.apply_pt(state["x"], state["y"])))
                    stack.clear()
                elif b0 == 25:
                    while len(stack) >= 8:
                        dx, dy = stack[:2]
                        del stack[:2]
                        state["x"] += dx
                        state["y"] += dy
                        p.append(lineto_pt(*atrafo.apply_pt(state["x"], state["y"])))
                    if len(stack) >= 6:
                        dx1, dy1, dx2, dy2, dx3, dy3 = stack[:6]
                        x1, y1 = state["x"] + dx1, state["y"] + dy1
                        x2, y2 = x1 + dx2, y1 + dy2
                        x3, y3 = x2 + dx3, y2 + dy3
                        state["x"], state["y"] = x3, y3
                        p.append(curveto_pt(*(atrafo.apply_pt(x1, y1) + atrafo.apply_pt(x2, y2) + atrafo.apply_pt(x3, y3))))
                    stack.clear()
                elif b0 == 26:
                    dx1 = stack.pop(0) if len(stack) % 4 == 1 else 0
                    while len(stack) >= 4:
                        dy1, dx2, dy2, dy3 = stack[:4]
                        del stack[:4]
                        x1, y1 = state["x"] + dx1, state["y"] + dy1
                        x2, y2 = x1 + dx2, y1 + dy2
                        x3, y3 = x2, y2 + dy3
                        state["x"], state["y"] = x3, y3
                        p.append(curveto_pt(*(atrafo.apply_pt(x1, y1) + atrafo.apply_pt(x2, y2) + atrafo.apply_pt(x3, y3))))
                        dx1 = 0
                    stack.clear()
                elif b0 == 27:
                    dy1 = stack.pop(0) if len(stack) % 4 == 1 else 0
                    while len(stack) >= 4:
                        dx1, dx2, dy2, dx3 = stack[:4]
                        del stack[:4]
                        x1, y1 = state["x"] + dx1, state["y"] + dy1
                        x2, y2 = x1 + dx2, y1 + dy2
                        x3, y3 = x2 + dx3, y2
                        state["x"], state["y"] = x3, y3
                        p.append(curveto_pt(*(atrafo.apply_pt(x1, y1) + atrafo.apply_pt(x2, y2) + atrafo.apply_pt(x3, y3))))
                        dy1 = 0
                    stack.clear()
                elif b0 in (30, 31):
                    horiz = (b0 == 31)
                    while len(stack) >= 4:
                        d1, d2, d3, d4 = stack[:4]
                        del stack[:4]
                        d5 = stack.pop(0) if len(stack) == 1 else 0
                        if horiz:
                            x1, y1 = state["x"] + d1, state["y"]
                            x2, y2 = x1 + d2, y1 + d3
                            x3, y3 = x2 + d5, y2 + d4
                        else:
                            x1, y1 = state["x"], state["y"] + d1
                            x2, y2 = x1 + d2, y1 + d3
                            x3, y3 = x2 + d4, y2 + d5
                        state["x"], state["y"] = x3, y3
                        p.append(curveto_pt(*(atrafo.apply_pt(x1, y1) + atrafo.apply_pt(x2, y2) + atrafo.apply_pt(x3, y3))))
                        horiz = not horiz
                    stack.clear()
                elif b0 == 10:
                    subr_idx = int(stack.pop()) + local_bias
                    execute(subrs[subr_idx])
                elif b0 == 29:
                    gsubr_idx = int(stack.pop()) + global_bias
                    execute(gsubrs[gsubr_idx])
                elif b0 == 11:
                    return
                elif b0 == 14:
                    if not state["has_width"]:
                        if len(stack) in (1, 5):
                            stack.pop(0)
                        state["has_width"] = True
                    close_current()
                    if len(stack) == 4:
                        adx, ady, bchar, achar = stack
                        stack.clear()
                        bglyph = t1file.adobestandardencoding[int(bchar)]
                        aglyph = t1file.adobestandardencoding[int(achar)]
                        if bglyph in self.name2pos:
                            self._run_cff_charstring(self.name2pos[bglyph], p, atrafo)
                        if aglyph in self.name2pos:
                            self._run_cff_charstring(self.name2pos[aglyph], p, atrafo * trafo.translate_pt(adx, ady))
                    return
                elif b0 == 12:
                    b1 = code[pos]
                    pos += 1
                    if b1 == 34 and len(stack) >= 7:
                        dx1, dx2, dy2, dx3, dx4, dx5, dx6 = stack[:7]
                        stack.clear()
                        x1, y1 = state["x"] + dx1, state["y"]
                        x2, y2 = x1 + dx2, y1 + dy2
                        x3, y3 = x2 + dx3, y2
                        x4, y4 = x3 + dx4, y3
                        x5, y5 = x4 + dx5, y4 - dy2
                        x6, y6 = x5 + dx6, y5
                        state["x"], state["y"] = x6, y6
                        p.append(curveto_pt(*(atrafo.apply_pt(x1, y1) + atrafo.apply_pt(x2, y2) + atrafo.apply_pt(x3, y3))))
                        p.append(curveto_pt(*(atrafo.apply_pt(x4, y4) + atrafo.apply_pt(x5, y5) + atrafo.apply_pt(x6, y6))))
                    elif b1 == 35 and len(stack) >= 12:
                        dx1, dy1, dx2, dy2, dx3, dy3, dx4, dy4, dx5, dy5, dx6, dy6 = stack[:12]
                        stack.clear()
                        x1, y1 = state["x"] + dx1, state["y"] + dy1
                        x2, y2 = x1 + dx2, y1 + dy2
                        x3, y3 = x2 + dx3, y2 + dy3
                        x4, y4 = x3 + dx4, y3 + dy4
                        x5, y5 = x4 + dx5, y4 + dy5
                        x6, y6 = x5 + dx6, y5 + dy6
                        state["x"], state["y"] = x6, y6
                        p.append(curveto_pt(*(atrafo.apply_pt(x1, y1) + atrafo.apply_pt(x2, y2) + atrafo.apply_pt(x3, y3))))
                        p.append(curveto_pt(*(atrafo.apply_pt(x4, y4) + atrafo.apply_pt(x5, y5) + atrafo.apply_pt(x6, y6))))
                    elif b1 == 36 and len(stack) >= 9:
                        dx1, dy1, dx2, dy2, dx3, dx4, dx5, dy5, dx6 = stack[:9]
                        stack.clear()
                        x1, y1 = state["x"] + dx1, state["y"] + dy1
                        x2, y2 = x1 + dx2, y1 + dy2
                        x3, y3 = x2 + dx3, y2
                        x4, y4 = x3 + dx4, y3
                        x5, y5 = x4 + dx5, y4 + dy5
                        x6, y6 = x5 + dx6, state["y"]
                        state["x"], state["y"] = x6, y6
                        p.append(curveto_pt(*(atrafo.apply_pt(x1, y1) + atrafo.apply_pt(x2, y2) + atrafo.apply_pt(x3, y3))))
                        p.append(curveto_pt(*(atrafo.apply_pt(x4, y4) + atrafo.apply_pt(x5, y5) + atrafo.apply_pt(x6, y6))))
                    elif b1 == 37 and len(stack) >= 11:
                        dx1, dy1, dx2, dy2, dx3, dy3, dx4, dy4, dx5, dy5, d6 = stack[:11]
                        stack.clear()
                        x1, y1 = state["x"] + dx1, state["y"] + dy1
                        x2, y2 = x1 + dx2, y1 + dy2
                        x3, y3 = x2 + dx3, y2 + dy3
                        x4, y4 = x3 + dx4, y3 + dy4
                        x5, y5 = x4 + dx5, y4 + dy5
                        if abs(x5 - state["x"]) > abs(y5 - state["y"]):
                            x6, y6 = x5 + d6, state["y"]
                        else:
                            x6, y6 = state["x"], y5 + d6
                        state["x"], state["y"] = x6, y6
                        p.append(curveto_pt(*(atrafo.apply_pt(x1, y1) + atrafo.apply_pt(x2, y2) + atrafo.apply_pt(x3, y3))))
                        p.append(curveto_pt(*(atrafo.apply_pt(x4, y4) + atrafo.apply_pt(x5, y5) + atrafo.apply_pt(x6, y6))))
                    else:
                        stack.clear()

        execute(self.cff_charstrings[gid])
        close_current()

    def getglyphpath_pt(self, x_pt, y_pt, glyph, size_pt, convertcharcode=False):
        if convertcharcode:
            gid = glyph if isinstance(glyph, int) else self.name2pos[glyph]
        else:
            gid = self.name2pos[glyph]
        scale = float(size_pt) / self.unitsPerEm
        t = trafo.scale_pt(scale, scale)
        tpath = t.translated_pt(x_pt, y_pt)
        p = path()
        if self.is_cff:
            self._run_cff_charstring(gid, p, tpath)
        else:
            self._update_glyf_path(gid, p, tpath)
        wx_pt = self.widths[gid] * size_pt / 1000.0

        class glyphpath:
            def __init__(self, p, wx_pt, wy_pt):
                self.path = p
                self.wx_pt = wx_pt
                self.wy_pt = wy_pt

        return glyphpath(p, wx_pt, 0.0)

    def getglyphinfo(self, glyph):
        gid = self.name2pos[glyph]
        if self.is_cff:
            self._ensure_cff_glyph_metrics(gid)
        return self.widths[gid], 0, 0, self.depth[gid], self.widths[gid], self.height[gid]

    def _build_post_v2_table(self):
        orig_post = self.tables[b"post"]
        header = b"\x00\x02\x00\x00" + orig_post[4:32]
        indices = []
        extra_names = []
        mac_to_idx = {name: i for i, name in enumerate(macnames)}
        for i in range(self.numGlyphs):
            name = self.charstrings[i] or ".notdef"
            if name in mac_to_idx:
                indices.append(mac_to_idx[name])
            else:
                nb = name.encode("ascii", errors="replace")[:255]
                indices.append(258 + len(extra_names))
                extra_names.append(bytes([len(nb)]) + nb)
        return header + struct.pack(">H%dH" % self.numGlyphs, self.numGlyphs, *indices) + b"".join(extra_names)

    def _build_cff_bytes(self, glyphnames=None):
        if glyphnames is None:
            selected = [(0, ".notdef")] + [(gid, self.charstrings[gid] or ("glyph%d" % gid)) for gid in range(1, self.numGlyphs)]
        else:
            seen = {0}
            selected = [(0, ".notdef")]
            for gname in sorted(glyphnames):
                if gname in self.name2pos:
                    gid = self.name2pos[gname]
                    if gid not in seen:
                        seen.add(gid)
                        selected.append((gid, gname))

        strings = []
        str_to_sid = dict(cff_standard_string_to_sid)
        sids = []
        for gid, gname in selected[1:]:
            if gname not in str_to_sid:
                str_to_sid[gname] = len(cff_standard_strings) + len(strings)
                strings.append(gname.encode("ascii", errors="replace"))
            sids.append(str_to_sid[gname])

        charset = b"\x00" + struct.pack(">%dH" % len(sids), *sids) if sids else b"\x00"
        cs_items = [self.cff_charstrings[gid] for gid, _ in selected]
        charstrings_idx = _make_cff_index(cs_items)

        priv_base = (
            _encode_cff_int(self.cff_default_width) + bytes([20]) +
            _encode_cff_int(self.cff_nominal_width) + bytes([21])
        )
        if self.cff_subrs:
            subrs_idx = _make_cff_index(self.cff_subrs)
            priv_dict = priv_base + _encode_cff_fixed_int(len(priv_base) + 6) + bytes([19])
            priv_block = priv_dict + subrs_idx
        else:
            priv_dict = priv_base
            priv_block = priv_dict

        hdr = b"\x01\x00\x04\x04"
        name_idx = _make_cff_index([self.name.encode("ascii", errors="replace")])
        string_idx = _make_cff_index(strings)
        gsubr_idx = _make_cff_index(self.cff_gsubrs)

        scale_fm = 1.0 / self.unitsPerEm
        fm_bytes = (
            _encode_cff_float(scale_fm) + _encode_cff_int(0) + _encode_cff_int(0) +
            _encode_cff_float(scale_fm) + _encode_cff_int(0) + _encode_cff_int(0) + bytes([12, 7])
        )
        bbox_bytes = (
            _encode_cff_int(self.raw_xMin) + _encode_cff_int(self.raw_yMin) +
            _encode_cff_int(self.raw_xMax) + _encode_cff_int(self.raw_yMax) + bytes([5])
        )

        def make_td(charset_off, cs_off, priv_size, priv_off):
            return (
                fm_bytes + bbox_bytes +
                _encode_cff_fixed_int(charset_off) + bytes([15]) +
                _encode_cff_fixed_int(cs_off) + bytes([17]) +
                _encode_cff_fixed_int(priv_size) + _encode_cff_fixed_int(priv_off) + bytes([18])
            )

        dummy_td_idx = _make_cff_index([make_td(0, 0, len(priv_dict), 0)])
        base_off = len(hdr) + len(name_idx) + len(dummy_td_idx) + len(string_idx) + len(gsubr_idx)
        charset_off = base_off
        cs_off = charset_off + len(charset)
        priv_off = cs_off + len(charstrings_idx)
        top_dict_idx = _make_cff_index([make_td(charset_off, cs_off, len(priv_dict), priv_off)])

        return hdr + name_idx + top_dict_idx + string_idx + gsubr_idx + charset + charstrings_idx + priv_block

    def _build_stripped_ttf_bytes(self, glyphs, charcodes):
        used_names = set(glyphs)
        for charcode in charcodes:
            if 0 <= charcode < len(self.encoding) and self.encoding[charcode]:
                used_names.add(self.encoding[charcode])

        usedglyphs = {0}
        glyf = self.tables[b"glyf"]
        queue = []
        for gname in used_names:
            if gname in self.name2pos:
                gid = self.name2pos[gname]
                usedglyphs.add(gid)
                queue.append(gid)
        while queue:
            gid = queue.pop()
            offset1 = self.glyphLocations[gid]
            offset2 = self.glyphLocations[gid + 1]
            if offset1 >= offset2:
                continue
            numberOfContours, = struct.unpack(">h", glyf[offset1:offset1+2])
            if numberOfContours < 0:
                offset = offset1 + 10
                while True:
                    flags, glyphIndex = struct.unpack(">HH", glyf[offset:offset+4])
                    if glyphIndex not in usedglyphs:
                        usedglyphs.add(glyphIndex)
                        queue.append(glyphIndex)
                    offset += 4
                    offset += 4 if (flags & 0x0001) else 2
                    if flags & 0x0008:
                        offset += 2
                    elif flags & 0x0040:
                        offset += 4
                    elif flags & 0x0080:
                        offset += 8
                    if not (flags & 0x0020):
                        break

        glyph_blobs = []
        new_locations = []
        cur_offset = 0
        for i in range(self.numGlyphs):
            new_locations.append(cur_offset)
            if i in usedglyphs:
                offset1 = self.glyphLocations[i]
                offset2 = self.glyphLocations[i + 1]
                blob = glyf[offset1:offset2]
                if not self.indexToLocFormat and (len(blob) % 2):
                    blob = blob + b"\x00"
                glyph_blobs.append(blob)
                cur_offset += len(blob)
            else:
                glyph_blobs.append(b"")
        new_locations.append(cur_offset)

        new_glyf = b"".join(glyph_blobs)
        if not self.indexToLocFormat and cur_offset // 2 <= 0xffff:
            new_loca = struct.pack(">%dH" % len(new_locations), *[loc // 2 for loc in new_locations])
        else:
            new_loca = struct.pack(">%dL" % len(new_locations), *new_locations)

        new_tables = dict(self.tables)
        new_tables[b"glyf"] = new_glyf
        new_tables[b"loca"] = new_loca
        new_tables[b"post"] = self._build_post_v2_table()
        if not self.indexToLocFormat and cur_offset // 2 > 0xffff:
            head = bytearray(new_tables[b"head"])
            struct.pack_into(">h", head, 50, 1)
            new_tables[b"head"] = bytes(head)

        sfnt_bytes, split_offsets = self._assemble_sfnt(new_tables, new_locations)
        return sfnt_bytes, used_names, split_offsets

    def _assemble_sfnt(self, tables_dict, glyph_locations=None):
        head = bytearray(tables_dict[b"head"])
        struct.pack_into(">L", head, 8, 0)
        tables_dict = dict(tables_dict)
        tables_dict[b"head"] = bytes(head)

        tags = sorted(tables_dict.keys())
        num_tables = len(tags)
        max_pow2 = 1
        entry_selector = 0
        while max_pow2 * 2 <= num_tables:
            max_pow2 *= 2
            entry_selector += 1
        search_range = max_pow2 * 16
        range_shift = num_tables * 16 - search_range

        dir_offset = 12 + 16 * num_tables
        directory = bytearray(struct.pack(">4sHHHH", self.sfntVersion, num_tables, search_range, entry_selector, range_shift))
        body = bytearray()
        head_body_offset = None
        glyf_body_offset = None
        split_offsets = []
        for tag in tags:
            tdata = tables_dict[tag]
            cs = checksum(tdata)
            offset = dir_offset + len(body)
            split_offsets.append(offset)
            if tag == b"head":
                head_body_offset = offset
            elif tag == b"glyf":
                glyf_body_offset = offset
            length = len(tdata)
            directory.extend(struct.pack(">4sLLL", tag, cs, offset, length))
            body.extend(tdata)
            pad = (4 - length % 4) % 4
            if pad:
                body.extend(b"\x00" * pad)

        if glyf_body_offset is not None and glyph_locations is not None:
            split_offsets.extend([glyf_body_offset + loc for loc in glyph_locations])

        full = directory + body
        if head_body_offset is not None:
            adj = (0xB1B0AFBA - checksum(bytes(full))) & 0xffffffff
            struct.pack_into(">L", full, head_body_offset + 8, adj)
        return bytes(full), split_offsets

    def getstrippedfont(self, glyphs, charcodes):
        used_names = set(glyphs)
        for charcode in charcodes:
            if 0 <= charcode < len(self.encoding) and self.encoding[charcode]:
                used_names.add(self.encoding[charcode])
        if self.is_cff:
            return _StrippedOTFfile(self, used_names, None, None)
        else:
            ttf_bytes, used_names, split_offsets = self._build_stripped_ttf_bytes(glyphs, charcodes)
            return _StrippedOTFfile(self, used_names, ttf_bytes, split_offsets)

    def outputPS(self, file, writer, used_names=None, sfnt_bytes=None, split_offsets=None):
        if self.is_cff:
            cff_bytes = self._build_cff_bytes(used_names)
            cmd = b"/FontSetInit /ProcSet findresource begin /%s %d StartData " % (
                self.name.encode("ascii"), len(cff_bytes)
            ) + cff_bytes
            hex_str = binascii.b2a_hex(cmd).decode("ascii").upper()
            file.write("currentfile /ASCIIHexDecode filter cvx exec\n")
            for i in range(0, len(hex_str), 72):
                file.write("%s\n" % hex_str[i:i+72])
            file.write(">\n")
            return

        otfdata = sfnt_bytes if sfnt_bytes is not None else self.otfdata
        if used_names is not None:
            cs_entries = [(0, ".notdef")]
            seen_names = {".notdef"}
            for name in sorted(used_names):
                if name not in seen_names and name in self.name2pos:
                    seen_names.add(name)
                    cs_entries.append((self.name2pos[name], name))
        else:
            cs_entries = [(i, name) for i, name in enumerate(self.charstrings) if name is not None]

        file.write("11 dict begin\n")
        file.write("/FontName /%s def\n" % self.fontname)
        file.write("/FontType 42 def\n")
        file.write("/FontMatrix [1 0 0 1 0 0] def\n")
        file.write("/FontBBox [%d %d %d %d] def\n" % (self.xMin, self.yMin, self.xMax, self.yMax))
        file.write("/PaintType 0 def\n")
        file.write("/Encoding StandardEncoding def\n")
        file.write("/CharStrings %d dict dup begin\n" % len(cs_entries))
        for i, name in cs_entries:
            file.write("/%s %d def\n" % (name, i))
        file.write("end readonly def\n")

        if split_offsets is not None:
            otfsplit = split_offsets[:]
        else:
            otfsplit = self.otfsplit[:]
            otfsplit.extend([self.glyfoffset + location for location in self.glyphLocations])

        otfsplit.sort()
        otfsplit.append(len(otfdata))

        i = 0
        while i < len(otfsplit) - 1:
            if otfsplit[i + 1] - otfsplit[i] > 65000:
                otfsplit.insert(i + 1, otfsplit[i] + 65000)
            else:
                i += 1

        lastsplit = 0
        i = 0
        while i < len(otfsplit) - 1:
            if otfsplit[i + 1] - lastsplit < 65000:
                del otfsplit[i]
            else:
                lastsplit = otfsplit[i]
                i += 1
        del otfsplit[-1]

        file.write("/sfnts[<\n")
        for p1, p2 in zip([0] + otfsplit, otfsplit + [len(otfdata)]):
            chunk = binascii.b2a_hex(otfdata[p1:p2]).decode("ascii").upper()
            if p1:
                file.write("00><\n")
            for i in range(0, len(chunk), 72):
                file.write("%s\n" % chunk[i:i+72])
        file.write("00>]def\n")
        file.write("FontName currentdict end definefont pop\n")

    def outputPDF(self, file, writer, used_names=None, sfnt_bytes=None):
        if self.is_cff:
            raw_data = self._build_cff_bytes(used_names)
            data = zlib.compress(raw_data) if (writer.compress and haszlib) else raw_data
            file.write("<<\n"
                       "/Length %d\n"
                       "/Subtype /Type1C\n" % len(data))
            if writer.compress and haszlib:
                file.write("/Filter /FlateDecode\n")
            file.write(">>\n"
                       "stream\n")
            file.write_bytes(data)
            file.write("\n"
                       "endstream\n")
            return

        if sfnt_bytes is not None:
            raw_data = sfnt_bytes
        else:
            new_tables = dict(self.tables)
            new_tables[b"post"] = self._build_post_v2_table()
            raw_data, _ = self._assemble_sfnt(new_tables, self.glyphLocations)

        data = zlib.compress(raw_data) if (writer.compress and haszlib) else raw_data
        file.write("<<\n"
                   "/Length %d\n"
                   "/Length1 %d\n" % (len(data), len(raw_data)))
        if writer.compress and haszlib:
            file.write("/Filter /FlateDecode\n")
        file.write(">>\n"
                   "stream\n")
        file.write_bytes(data)
        file.write("\n"
                   "endstream\n")


class _StrippedOTFfile:

    def __init__(self, otffile, used_names, sfnt_bytes, split_offsets=None):
        self.otffile = otffile
        self.used_names = used_names
        self.sfnt_bytes = sfnt_bytes
        self.split_offsets = split_offsets

    def outputPS(self, file, writer):
        self.otffile.outputPS(file, writer, used_names=self.used_names, sfnt_bytes=self.sfnt_bytes, split_offsets=self.split_offsets)

    def outputPDF(self, file, writer):
        self.otffile.outputPDF(file, writer, used_names=self.used_names, sfnt_bytes=self.sfnt_bytes)
