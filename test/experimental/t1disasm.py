import array, binascii
import sys; sys.path.insert(0, "../..")
from pyx import canvas, path, trafo

StandardEncoding = { 32: "space",
                     33: "exclam",
                     34: "quotedbl",
                     35: "numbersign",
                     36: "dollar",
                     37: "percent",
                     38: "ampersand",
                     39: "quoteright",
                     40: "parenleft",
                     41: "parenright",
                     42: "asterisk",
                     43: "plus",
                     44: "comma",
                     45: "hyphen",
                     46: "period",
                     47: "slash",
                     48: "zero",
                     49: "one",
                     50: "two",
                     51: "three",
                     52: "four",
                     53: "five",
                     54: "six",
                     55: "seven",
                     56: "eight",
                     57: "nine",
                     58: "colon",
                     59: "semicolon",
                     60: "less",
                     61: "equal",
                     62: "greater",
                     63: "question",
                     64: "at",
                     65: "A",
                     66: "B",
                     67: "C",
                     68: "D",
                     69: "E",
                     70: "F",
                     71: "G",
                     72: "H",
                     73: "I",
                     74: "J",
                     75: "K",
                     76: "L",
                     77: "M",
                     78: "N",
                     79: "O",
                     80: "P",
                     81: "Q",
                     82: "R",
                     83: "S",
                     84: "T",
                     85: "U",
                     86: "V",
                     87: "W",
                     88: "X",
                     89: "Y",
                     90: "Z",
                     91: "bracketleft",
                     92: "backslash",
                     93: "bracketright",
                     94: "asciicircum",
                     95: "underscore",
                     96: "quoteleft",
                     97: "a",
                     98: "b",
                     99: "c",
                    100: "d",
                    101: "e",
                    102: "f",
                    103: "g",
                    104: "h",
                    105: "i",
                    106: "j",
                    107: "k",
                    108: "l",
                    109: "m",
                    110: "n",
                    111: "o",
                    112: "p",
                    113: "q",
                    114: "r",
                    115: "s",
                    116: "t",
                    117: "u",
                    118: "v",
                    119: "w",
                    120: "x",
                    121: "y",
                    122: "z",
                    123: "braceleft",
                    124: "bar",
                    125: "braceright",
                    126: "asciitilde",
                    161: "exclamdown",
                    162: "cent",
                    163: "sterling",
                    164: "fraction",
                    165: "yen",
                    166: "florin",
                    167: "section",
                    168: "currency",
                    169: "quotesingle",
                    170: "quotedblleft",
                    171: "guillemotleft",
                    172: "guilsinglleft",
                    173: "guilsinglright",
                    174: "fi",
                    175: "fl",
                    177: "endash",
                    178: "dagger",
                    179: "daggerdbl",
                    180: "periodcentered",
                    182: "paragraph",
                    183: "bullet",
                    184: "quotesinglbase",
                    185: "quotedblbase",
                    186: "quotedblright",
                    187: "guillemotright",
                    188: "ellipsis",
                    189: "perthousand",
                    191: "questiondown",
                    193: "grave",
                    194: "acute",
                    195: "circumflex",
                    196: "tilde",
                    197: "macron",
                    198: "breve",
                    199: "dotaccent",
                    200: "dieresis",
                    202: "ring",
                    203: "cedilla",
                    205: "hungarumlaut",
                    206: "ogonek",
                    207: "caron",
                    208: "emdash",
                    225: "AE",
                    227: "ordfeminine",
                    232: "Lslash",
                    233: "Oslash",
                    234: "OE",
                    235: "ordmasculine",
                    241: "ae",
                    245: "dotlessi",
                    248: "lslash",
                    249: "oslash",
                    250: "oe",
                    251: "germandbls"}


class T1context:

    def __init__(self, t1font, seacglyphs=None, subrs=None, othersubrs=None):
        """context for T1cmd evaluation

        subrs is the "called-subrs" dictionary; gathercalls will insert the
        subrnumber as key having the value 1, i.e. subrs.keys() will become the
        numbers of used subrs
        """
        self.t1font = t1font

        # state description
        self.x = None
        self.y = None
        self.wx = None
        self.wy = None
        self.t1stack = []
        self.psstack = []

        # result variables
        # for path creation:
        self.path = None
        # for gather calls:
        self.subrs = subrs
        self.seacglyphs = seacglyphs
        self.othersubrs = othersubrs


# T1 commands

class _T1cmd:

    def __str__(self):
        """returns a string representation of the T1 command"""
        raise NotImplementedError

    def buildpath(self, context):
        """update path in context"""
        raise NotImplementedError

    def gathercalls(self, context):
        """fill dependancy information in context

        This method might will not properly update all information in the
        context and will also skip various tests for performance reasons.
        For most T1 commands it just doesn't need to do anything.
        """
        pass


class T1value(_T1cmd):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

    def buildpath(self, context):
        context.t1stack.append(self.value)

    def gathercalls(self, context):
        context.t1stack.append(self.value)


# commands for starting and finishing

class _T1endchar(_T1cmd):

    def __str__(self):
        return "endchar"

    def buildpath(self, context):
        assert not context.t1stack

T1endchar = _T1endchar()


class _T1hsbw(_T1cmd):

    def __str__(self):
        return "hsbw"

    def buildpath(self, context):
        assert context.path is None
        sbx = context.t1stack.pop(0)
        wx = context.t1stack.pop(0)
        assert not context.t1stack
        context.path = path.path(path.moveto_pt(sbx, 0))
        context.x = sbx
        context.y = 0
        context.wx = wx
        context.wy = 0

T1hsbw = _T1hsbw()


class _T1seac(_T1cmd):

    def __str__(self):
        return "seac"

    def buildpath(self, context):
        sab = context.t1stack.pop(0)
        adx = context.t1stack.pop(0)
        ady = context.t1stack.pop(0)
        bchar = context.t1stack.pop(0)
        achar = context.t1stack.pop(0)
        apath = f.getglyphpath(StandardEncoding[bchar])
        bpath = f.getglyphpath(StandardEncoding[achar])
        bpath = bpath.transformed(trafo.translate_pt(adx-sab, ady))
        context.path = apath + bpath

    def gathercalls(self, context):
        achar = context.t1stack.pop()
        bchar = context.t1stack.pop()
        aname = StandardEncoding[achar]
        bname = StandardEncoding[bchar]
        context.seacglyphs[aname] = 1
        context.seacglyphs[bname] = 1
        f = context.t1font
        for cmd in f._cmds(f.glyphs[StandardEncoding[achar]]):
            cmd.gathercalls(context)
        for cmd in f._cmds(f.glyphs[StandardEncoding[bchar]]):
            cmd.gathercalls(context)

T1seac = _T1seac()


class _T1sbw(_T1cmd):

    def __str__(self):
        return "sbw"

    def buildpath(self, context):
        assert context.path is None
        sbx = context.t1stack.pop(0)
        sby = context.t1stack.pop(0)
        wx = context.t1stack.pop(0)
        wy = context.t1stack.pop(0)
        assert not context.t1stack
        context.path = path.path(path.moveto_pt(sbx, sby))
        context.x = sbx
        context.y = sby
        context.wx = wx
        context.wy = wy

T1sbw = _T1sbw()


# path construction commands

class _T1closepath(_T1cmd):

    def __str__(self):
        return "closepath"

    def buildpath(self, context):
        assert not context.t1stack
        context.path.append(path.closepath())
        # The closepath in T1 is different from PostScripts in that it does
        # *not* modify the current position; hence we need to add an additional
        # moveto here ...
        context.path.append(path.moveto_pt(context.x, context.y))

T1closepath = _T1closepath()


class _T1hlineto(_T1cmd):

    def __str__(self):
        return "hlineto"

    def buildpath(self, context):
        dx = context.t1stack.pop(0)
        assert not context.t1stack
        context.path.append(path.rlineto_pt(dx, 0))
        context.x += dx

T1hlineto = _T1hlineto()


class _T1hmoveto(_T1cmd):

    def __str__(self):
        return "hmoveto"

    def buildpath(self, context):
        dx = context.t1stack.pop(0)
        assert not context.t1stack
        context.path.append(path.rmoveto_pt(dx, 0))
        context.x += dx

T1hmoveto = _T1hmoveto()


class _T1hvcurveto(_T1cmd):

    def __str__(self):
        return "hvcurveto"

    def buildpath(self, context):
        dx1 = context.t1stack.pop(0)
        dx2 = context.t1stack.pop(0)
        dy2 = context.t1stack.pop(0)
        dy3 = context.t1stack.pop(0)
        assert not context.t1stack
        context.path.append(path.rcurveto_pt(dx1,     0,
                                             dx1+dx2, dy2,
                                             dx1+dx2, dy2+dy3))
        context.x += dx1+dx2
        context.y += dy2+dy3

T1hvcurveto = _T1hvcurveto()


class _T1rlineto(_T1cmd):

    def __str__(self):
        return "rlineto"

    def buildpath(self, context):
        dx = context.t1stack.pop(0)
        dy = context.t1stack.pop(0)
        assert not context.t1stack
        context.path.append(path.rlineto_pt(dx, dy))
        context.x += dx
        context.y += dy

T1rlineto = _T1rlineto()


class _T1rmoveto(_T1cmd):

    def __str__(self):
        return "rmoveto"

    def buildpath(self, context):
        dx = context.t1stack.pop(0)
        dy = context.t1stack.pop(0)
        assert not context.t1stack
        context.path.append(path.rmoveto_pt(dx, dy))
        context.x += dx
        context.y += dy

T1rmoveto = _T1rmoveto()


class _T1rrcurveto(_T1cmd):

    def __str__(self):
        return "rrcurveto"

    def buildpath(self, context):
        dx1 = context.t1stack.pop(0)
        dy1 = context.t1stack.pop(0)
        dx2 = context.t1stack.pop(0)
        dy2 = context.t1stack.pop(0)
        dx3 = context.t1stack.pop(0)
        dy3 = context.t1stack.pop(0)
        assert not context.t1stack
        context.path.append(path.rcurveto_pt(dx1,         dy1,
                                             dx1+dx2,     dy1+dy2,
                                             dx1+dx2+dx3, dy1+dy2+dy3))
        context.x += dx1+dx2+dx3
        context.y += dy1+dy2+dy3

T1rrcurveto = _T1rrcurveto()


class _T1vlineto(_T1cmd):

    def __str__(self):
        return "vlineto"

    def buildpath(self, context):
        dy = context.t1stack.pop(0)
        assert not context.t1stack
        context.path.append(path.rlineto_pt(0, dy))
        context.y += dy

T1vlineto = _T1vlineto()


class _T1vmoveto(_T1cmd):

    def __str__(self):
        return "vmoveto"

    def buildpath(self, context):
        dy = context.t1stack.pop(0)
        assert not context.t1stack
        context.path.append(path.rmoveto_pt(0, dy))
        context.y += dy

T1vmoveto = _T1vmoveto()


class _T1vhcurveto(_T1cmd):

    def __str__(self):
        return "vhcurveto"

    def buildpath(self, context):
        dy1 = context.t1stack.pop(0)
        dx2 = context.t1stack.pop(0)
        dy2 = context.t1stack.pop(0)
        dx3 = context.t1stack.pop(0)
        assert not context.t1stack
        context.path.append(path.rcurveto_pt(0,       dy1,
                                             dx2,     dy1+dy2,
                                             dx2+dx3, dy1+dy2))
        context.x += dx2+dx3
        context.y += dy1+dy2

T1vhcurveto = _T1vhcurveto()


# hint commands

class _T1dotsection(_T1cmd):

    def __str__(self):
        return "dotsection"

    def buildpath(self, context):
        assert not context.t1stack

T1dotsection = _T1dotsection()


class _T1hstem(_T1cmd):

    def __str__(self):
        return "hstem"

    def buildpath(self, context):
        y = context.t1stack.pop(0)
        dy = context.t1stack.pop(0)
        assert not context.t1stack

T1hstem = _T1hstem()


class _T1hstem3(_T1cmd):

    def __str__(self):
        return "hstem3"

    def buildpath(self, context):
        y0 = context.t1stack.pop(0)
        dy0 = context.t1stack.pop(0)
        y1 = context.t1stack.pop(0)
        dy1 = context.t1stack.pop(0)
        y2 = context.t1stack.pop(0)
        dy2 = context.t1stack.pop(0)
        assert not context.t1stack

T1hstem3 = _T1hstem3()


class _T1vstem(_T1cmd):

    def __str__(self):
        return "hstem"

    def buildpath(self, context):
        x = context.t1stack.pop(0)
        dx = context.t1stack.pop(0)
        assert not context.t1stack

T1vstem = _T1vstem()


class _T1vstem3(_T1cmd):

    def __str__(self):
        return "hstem3(%s, %s, %s, %s, %s, %s)" % (self.x0, self, dx0, self.x1, self.dx1, self.x2, self.dx2)

    def buildpath(self, context):
        self.x0 = context.t1stack.pop(0)
        self.dx0 = context.t1stack.pop(0)
        self.x1 = context.t1stack.pop(0)
        self.dx1 = context.t1stack.pop(0)
        self.x2 = context.t1stack.pop(0)
        self.dx2 = context.t1stack.pop(0)
        assert not context.t1stack

T1vstem3 = _T1vstem3()


# arithmetic command

class _T1div(_T1cmd):

    def __str__(self):
        return "div"

    def buildpath(self, context):
        num2 = context.t1stack.pop()
        num1 = context.t1stack.pop()
        context.t1stack.append(num1//num2)

    gathercalls = buildpath

T1div = _T1div()


# subroutine commands

class _T1callothersubr(_T1cmd):

    def __str__(self):
        return "callothersubr"

    def buildpath(self, context):
        othersubrnumber = context.t1stack.pop()
        n = context.t1stack.pop()
        for i in range(n):
            context.psstack.append(context.t1stack.pop())

    def gathercalls(self, context):
        othersubrnumber = context.t1stack.pop()
        context.othersubrs[othersubrnumber] = 1
        n = context.t1stack.pop()
        for i in range(n):
            context.psstack.append(context.t1stack.pop())

T1callothersubr = _T1callothersubr()


class _T1callsubr(_T1cmd):

    def __str__(self):
        return "callsubr"

    def buildpath(self, context):
        subrnumber = context.t1stack.pop()
        f = context.t1font
        for cmd in f._cmds(f.subrs[subrnumber]):
            cmd.buildpath(context)

    def gathercalls(self, context):
        subrnumber = context.t1stack.pop()
        context.subrs[subrnumber] = 1
        f = context.t1font
        for cmd in f._cmds(f.subrs[subrnumber]):
            cmd.gathercalls(context)

T1callsubr = _T1callsubr()


class _T1pop(_T1cmd):

    def __str__(self):
        return "pop"

    def buildpath(self, context):
        context.t1stack.append(context.psstack.pop())

    gathercalls = buildpath

T1pop = _T1pop()


class _T1return(_T1cmd):

    def __str__(self):
        return "return"

    def buildpath(self, context):
        pass

T1return = _T1return()


class _T1setcurrentpoint(_T1cmd):

    def __str__(self):
        return "setcurrentpoint" % self.x, self.y

    def pathitem(self, context):
        x = context.t1stack.pop(0)
        y = context.t1stack.pop(0)
        assert not context.t1stack
        context.path.append(path.moveto_pt(x, y))
        context.x = x
        context.y = y

T1setcurrentpoint = _T1setcurrentpoint()


##########################

class cursor:

    def __init__(self, data, startstring, tokenseps=" \t\r\n"):
        self.data = data
        self.pos = data.index(startstring) + len(startstring)
        self.tokenseps = tokenseps

    def gettoken(self):
        while self.data[self.pos] in self.tokenseps:
            self.pos += 1
        startpos = self.pos
        while self.data[self.pos] not in self.tokenseps:
            self.pos += 1
        self.pos += 1 # consume a single tokensep
        return self.data[startpos: self.pos-1]

    def getint(self):
        return int(self.gettoken())

    def getbytes(self, count):
        startpos = self.pos
        self.pos += count
        return self.data[startpos: self.pos]


class T1font:

    c1 = 52845
    c2 = 22719
    eexecr = 55665
    charstringr = 4330

    def __init__(self, data1, data2eexec, data3):
        self.data1 = data1
        self.data2eexec = data2eexec
        self.data3 = data3
        self.decoded = 0

    def _decoder(self, code, r, n=4):
        plain = array.array("B")
        for x in array.array("B", code):
            plain.append(x ^ (r >> 8))
            r = ((x + r) * self.c1 + self.c2) & 0xffff
        return plain.tostring()[n:]

    def _encoder(self, data, r, random="PyX!"):
        code = array.array("B")
        for x in array.array("B", random+data):
            code.append(x ^ (r>>8))
            r = ((code[-1] + r) * self.c1 + self.c2) & 0xffff;
        return code.tostring()

    def _eexecdecode(self, code):
        return self._decoder(code, self.eexecr)

    def _charstringdecode(self, code):
        # XXX: take into account lenIV
        return self._decoder(code, self.charstringr)

    def _eexecencode(self, code):
        return self._encoder(code, self.eexecr)

    def _charstringencode(self, code):
        return self._encoder(code, self.charstringr)

    def _cmds(self, code):
        code = array.array("B", self._charstringdecode(code))
        cmds = []
        while code:
            x = code.pop(0)
            if 0 <= x < 32:
                try:
                    cmds.append({1: T1hstem,
                                 3: T1vstem,
                                 4: T1vmoveto,
                                 5: T1rlineto,
                                 6: T1hlineto,
                                 7: T1vlineto,
                                 8: T1rrcurveto,
                                 9: T1closepath,
                                 10: T1callsubr,
                                 11: T1return,
                                 13: T1hsbw,
                                 14: T1endchar,
                                 21: T1rmoveto,
                                 22: T1hmoveto,
                                 30: T1vhcurveto,
                                 31: T1hvcurveto}[x])
                except KeyError:
                    if x == 12:
                        x = code.pop(0)
                        try:
                            cmds.append({0: T1dotsection,
                                         1: T1vstem3,
                                         2: T1hstem3,
                                         6: T1seac,
                                         7: T1sbw,
                                         12: T1div,
                                         16: T1callothersubr,
                                         17: T1pop,
                                         33: T1setcurrentpoint}[x])
                        except KeyError:
                            raise ValueError("unknown escaped command %d" % x)
                    else:
                        raise ValueError("unknown command %d" % x)
            elif 32 <= x <= 246:
                cmds.append(T1value(x-139))
            elif 247 <= x <= 250:
                cmds.append(T1value(((x - 247)*256) + code.pop(0) + 108))
            elif 251 <= x <= 254:
                cmds.append(T1value(-((x - 251)*256) - code.pop(0) - 108))
            else:
                y = ((code.pop(0)*256+code.pop(0))*256+code.pop(0))*256+code.pop(0)
                if y > (1l << 31):
                    cmds.append(T1value(y - (1l << 32)))
                else:
                    cmds.append(T1value(y))
        return cmds

    def _data2decode(self):
        if self.decoded:
            return
        self.decoded = 1

        self.data2 = self._decoder(self.data2eexec, 55665)

        # extract Subrs
        c = cursor(self.data2, "/Subrs")
        self.subrsstart = c.pos
        arraycount = c.getint()
        token = c.gettoken(); assert token == "array"
        self.subrs = []
        for i in range(arraycount):
            token = c.gettoken(); assert token == "dup"
            token = c.getint(); assert token == i
            size = c.getint()
            if not i:
                self.subrrdtoken = c.gettoken()
            else:
                token = c.gettoken(); assert token == self.subrrdtoken
            self.subrs.append(c.getbytes(size))
            token = c.gettoken()
            if token == "noaccess":
                token = "%s %s" % (token, c.gettoken())
            if not i:
                self.subrnptoken = token
            else:
                assert token == self.subrnptoken
        self.subrsend = c.pos

        # extract glyphs
        self.glyphs = {}
        self.glyphnames = [] # we want to keep the order of the glyph names
        c = cursor(self.data2, "/CharStrings")
        self.charstingsstart = c.pos
        c.getint()
        token = c.gettoken(); assert token == "dict"
        token = c.gettoken(); assert token == "dup"
        token = c.gettoken(); assert token == "begin"
        first = 1
        while 1:
            chartoken = c.gettoken()
            if chartoken == "end":
                break
            assert chartoken[0] == "/"
            size = c.getint()
            if first:
                self.glyphrdtoken = c.gettoken()
            else:
                token = c.gettoken(); assert token == self.glyphrdtoken
            self.glyphnames.append(chartoken[1:])
            self.glyphs[chartoken[1:]] = c.getbytes(size)
            if first:
                self.glyphndtoken = c.gettoken()
            else:
                token = c.gettoken(); assert token == self.glyphndtoken
            first = 0
        self.charstingsend = c.pos
        assert self.subrrdtoken == self.glyphrdtoken

    def getstrippedfont(self, glyphs):
        self._data2decode()
        seacglyphs = {}
        subrs = {}
        othersubrs = {}

        for glyph in glyphs:
            context = T1context(self, seacglyphs, subrs, othersubrs)
            for cmd in self._cmds(self.glyphs[glyph]):
                cmd.gathercalls(context)
        for glyph in seacglyphs.keys():
            if glyph not in glyphs:
                glyphs.append(glyph)
        if ".notdef" not in glyphs:
            glyphs.append(".notdef")

        subrs = subrs.keys()
        subrs.sort()
        if subrs and subrs[-1] > 3:
            count = subrs[-1]+1
        else:
            count = 4
        strippedsubrs = [" %d array\n" % count]
        for subr in range(count):
            if subr < 4 or subr in subrs:
                code = self.subrs[subr]
            else:
                code = self.subrs[3]
            strippedsubrs.append("dup %d %d %s %s %s\n" % (subr, len(code), self.subrrdtoken, code, self.subrnptoken))
        strippedsubrs = "".join(strippedsubrs)

        strippedcharstrings = [" %d dict dup begin\n" % len(glyphs)]
        for glyph in self.glyphnames:
            if glyph in glyphs:
                strippedcharstrings.append("/%s %d %s %s %s\n" % (glyph, len(self.glyphs[glyph]), self.glyphrdtoken, self.glyphs[glyph], self.glyphndtoken))
        strippedcharstrings.append("end\n")
        strippedcharstrings = "".join(strippedcharstrings)

        data2 = self.data2
        if self.subrsstart < self.charstingsstart:
            data2 = data2[:self.charstingsstart] + strippedcharstrings + data2[self.charstingsend:]
            data2 = data2[:self.subrsstart] + strippedsubrs + data2[self.subrsend:]
        else:
            data2 = data2[:self.subrsstart] + strippedsubrs + data2[self.subrsend:]
            data2 = data2[:self.charstingsstart] + strippedcharstrings + data2[self.charstingsend:]

        import re
        data1 = re.subn("\s*[\r\n]\s*", "\n", self.data1)[0]
        for glyph in self.glyphnames:
            if glyph not in glyphs:
                data1 = re.subn("dup \d+ /%s put\s*" % glyph, "", data1)[0]
        data3 = re.subn("\s*[\r\n]\s*", "\n", self.data3)[0]
        return T1font(data1, self._eexecencode(data2), data3.rstrip())

    def getsubrcmds(self, n):
        self._data2decode()
        return self._cmds(self.subrs[n])

    def getglyphcmds(self, glyphname):
        self._data2decode()
        return self._cmds(self.glyphs[glyphname])

    def getglyphpath(self, glyphname):
        # XXX: we do not yet transform between font coordinates in its design size and postsript points
        self._data2decode()
        context = T1context(self)
        for cmd in self._cmds(self.glyphs[glyphname]):
            cmd.buildpath(context)
        return context.path

    def outputPS(self, file):
        file.write(self.data1)
        data2eexechex = binascii.b2a_hex(self.data2eexec)
        linelength = 64
        for i in range((len(data2eexechex)-1)/linelength + 1):
            file.write(data2eexechex[i*linelength: i*linelength+linelength])
            file.write("\n")
        file.write(self.data3)


class T1pfafont(T1font):

    def __init__(self, filename):
        d = open(filename, "rb").read()
        # hey, that's quick'n'dirty
        m1 = d.index("eexec") + 6
        m2 = d.index("0"*40)
        data1 = d[:m1]
        data2 = binascii.a2b_hex(d[m1: m2].replace(" ", "").replace("\r", "").replace("\n", ""))
        data3 = d[m2:]
        T1font.__init__(self, data1, data2, data3)


class T1pfbfont(T1font):

    def __init__(self, filename):
        def pfblength(s):
            if len(s) != 4:
                raise ValueError("invalid string length")
            return (ord(s[0]) +
                    ord(s[1])*256 +
                    ord(s[2])*256*256 +
                    ord(s[3])*256*256*256)
        f = open(filename, "rb")
        assert f.read(2) != "7F01"
        data1 = f.read(pfblength(f.read(4)))
        assert f.read(2) != "7F02"
        data2 = f.read(pfblength(f.read(4)))
        assert f.read(2) != "7F01"
        data3 = f.read(pfblength(f.read(4)))
        assert f.read(2) != "7F03"
        assert not f.read(1)
        T1font.__init__(self, data1, data2, data3)


f = T1pfbfont("cmr10.pfb")
# f = T1pfafont("cmr10.pfa")

c = canvas.canvas()
for i in range(26):
    c.stroke(f.getglyphpath(chr(97+i)), [trafo.scale(0.1), trafo.translate(5*i, 5)])
    c.stroke(f.getglyphpath(chr(65+i)), [trafo.scale(0.1), trafo.translate(5*i, 0)])
c.writeEPSfile("t1disasm")

head = """%!PS-Adobe-3.0 EPSF-3.0
%%BoundingBox: -1 -3 58 8
%%HiResBoundingBox: -1 -2.93718 57.6929 7.9185
%%Creator: PyX 0.8+
%%Title: hello.eps
%%CreationDate: Thu Sep  1 20:19:40 2005
%%EndComments
%%BeginProlog
%%BeginFont: CMR10
%Included char codes: 33 44 72 100 101 108 111 114 119
"""
foot = """
%%EndFont
%%BeginRessource: ReEncodeFont
{
  5 dict
  begin
    /newencoding exch def
    /newfontname exch def
    /basefontname exch def
    /basefontdict basefontname findfont def
    /newfontdict basefontdict maxlength dict def
    basefontdict {
      exch dup dup /FID ne exch /Encoding ne and
      { exch newfontdict 3 1 roll put }
      { pop pop }
      ifelse
    } forall
    newfontdict /FontName newfontname put
    newfontdict /Encoding newencoding put
    newfontname newfontdict definefont pop
  end
} /ReEncodeFont exch def
%%EndRessource
%%BeginProcSet: TeXf7b6d320Encoding
/TeXf7b6d320Encoding
[ /Gamma /Delta /Theta /Lambda /Xi /Pi /Sigma /Upsilon
/Phi /Psi /Omega /ff /fi /fl /ffi /ffl
/dotlessi /dotlessj /grave /acute /caron /breve /macron /ring
/cedilla /germandbls /ae /oe /oslash /AE /OE /Oslash
/suppress /exclam /quotedblright /numbersign /dollar /percent /ampersand /quoteright
/parenleft /parenright /asterisk /plus /comma /hyphen /period /slash
/zero /one /two /three /four /five /six /seven
/eight /nine /colon /semicolon /exclamdown /equal /questiondown /question
/at /A /B /C /D /E /F /G
/H /I /J /K /L /M /N /O
/P /Q /R /S /T /U /V /W
/X /Y /Z /bracketleft /quotedblleft /bracketright /circumflex /dotaccent
/quoteleft /a /b /c /d /e /f /g
/h /i /j /k /l /m /n /o
/p /q /r /s /t /u /v /w
/x /y /z /endash /emdash /hungarumlaut /tilde /dieresis
/suppress /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef
/.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef
/.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef
/.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef
/space /Gamma /Delta /Theta /Lambda /Xi /Pi /Sigma
/Upsilon /Phi /Psi /.notdef /.notdef /Omega /ff /fi
/fl /ffi /ffl /dotlessi /dotlessj /grave /acute /caron
/breve /macron /ring /cedilla /germandbls /ae /oe /oslash
/AE /OE /Oslash /suppress /dieresis /.notdef /.notdef /.notdef
/.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef
/.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef
/.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef
/.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef
/.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef
/.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef
/.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef ] def
%%EndProcSet
%%BeginProcSet: CMR10-TeXf7b6d320Encoding
/CMR10 /CMR10-TeXf7b6d320Encoding TeXf7b6d320Encoding ReEncodeFont
%%EndProcSet
%%EndProlog
0.566929 setlinewidth
gsave
gsave
gsave
[1.000000 0.000000 0.000000 1.000000 0.000000 0.000000] concat
gsave
/CMR10-TeXf7b6d320Encoding 9.962640 selectfont
0 0 moveto (Hello,) show
28.5043 0 moveto (w) show
35.4228 0 moveto (orld!) show
grestore
grestore
grestore
newpath
0 0 moveto
56.6929 0 lineto
stroke
grestore
showpage
%%Trailer
%%EOF
"""
fstripped = f.getstrippedfont(["H", "e", "l", "o", "comma", "w", "r", "d", "exclam"])
out = open("t1strip.eps", "w")
out.write(head)
fstripped.outputPS(out)
out.write(foot)

# f = T1pfbfont("/Users/andre/texmf/fonts/type1/bitstrea/iowan/biwr8a.pfb")
# 
# c = canvas.canvas()
# c.stroke(f.getglyphpath("Aacute"), [trafo.scale(0.1)])
# c.writeEPSfile("t1seac")
# 
# print f.getstrippedfont(["Adieresis"])
# 
# # funny:
# f = T1pfbfont("/sw/share/texmf/fonts/type1/bluesky/cm/cmr10.pfb")
# f._data2decode()
# for code in f.subrs:
#     sys.stdout.write(f._decoder(code, 4330, n=0)[:4])
# for glyph in f.glyphnames:
#     sys.stdout.write(f._decoder(f.glyphs[glyph], 4330, n=0)[:4])
# 
