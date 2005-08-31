import array, binascii
import sys; sys.path.insert(0, "../..")
from pyx import canvas, path, trafo

# XXX: we do not yet transform between font coordinates in its design size and postsript points

class T1context:

    def __init__(self, t1font):
        self.t1font = t1font

        self.path = None
        self.x = None
        self.y = None
        self.wx = None
        self.wy = None
        self.t1stack = []
        self.psstack = []
        self.valid = 1


# T1 commands

class _T1command:

    def __str__(self):
        "returns a string representation of the T1 command"
        raise NotImplementedError

    def __call__(self, context):
        "update path and stacks in context"
        raise NotImplementedError


class T1value(_T1command):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

    def __call__(self, context):
        context.t1stack.append(self.value)


# commands for starting and finishing

class _T1endchar(_T1command):

    def __str__(self):
        return "endchar"

    def __call__(self, context):
        pass

T1endchar = _T1endchar()


class _T1hsbw(_T1command):

    def __str__(self):
        return "hsbw"

    def __call__(self, context):
        assert context.path is None
        sbx = context.t1stack.pop(0)
        wx = context.t1stack.pop(0)
        assert not context.t1stack
        context.path = path.path(path.moveto(sbx, 0))
        context.x = sbx
        context.y = 0
        context.wx = wx
        context.wy = 0

T1hsbw = _T1hsbw()


class _T1seac(_T1command):

    # def __init__(self, asb, adx, ady, bchar, achar):

    def __str__(self):
        return "seac"

    def __call__(self, context):
        raise NotImplementedError("can't convert glyph containing a T1seac into a path")

T1seac = _T1seac()


class _T1sbw(_T1command):

    def __str__(self):
        return "sbw"

    def __call__(self, context):
        assert context.path is None
        sbx = context.t1stack.pop(0)
        sby = context.t1stack.pop(0)
        wx = context.t1stack.pop(0)
        wy = context.t1stack.pop(0)
        assert not context.t1stack
        context.path = path.path(path.moveto(sbx, sby))
        context.x = sbx
        context.y = sby
        context.wx = wx
        context.wy = wy

T1sbw = _T1sbw()


# path construction commands

class _T1closepath(_T1command):

    def __str__(self):
        return "closepath"

    def __call__(self, context):
        assert not context.t1stack
        context.path.append(path.closepath())
        # The closepath in T1 is different from PostScripts in that it does
        # *not* modify the current position; hence we need to add an additional
        # moveto here ...
        context.path.append(path.moveto(context.x, context.y))

T1closepath = _T1closepath()


class _T1hlineto(_T1command):

    def __str__(self):
        return "hlineto"

    def __call__(self, context):
        dx = context.t1stack.pop(0)
        assert not context.t1stack
        context.path.append(path.rlineto(dx, 0))
        context.x += dx

T1hlineto = _T1hlineto()


class _T1hmoveto(_T1command):

    def __str__(self):
        return "hmoveto"

    def __call__(self, context):
        dx = context.t1stack.pop(0)
        assert not context.t1stack
        context.path.append(path.rmoveto(dx, 0))
        context.x += dx

T1hmoveto = _T1hmoveto()


class _T1hvcurveto(_T1command):

    def __str__(self):
        return "hvcurveto"

    def __call__(self, context):
        dx1 = context.t1stack.pop(0)
        dx2 = context.t1stack.pop(0)
        dy2 = context.t1stack.pop(0)
        dy3 = context.t1stack.pop(0)
        assert not context.t1stack
        context.path.append(path.rcurveto(dx1,     0,
                                          dx1+dx2, dy2,
                                          dx1+dx2, dy2+dy3))
        context.x += dx1+dx2
        context.y += dy2+dy3

T1hvcurveto = _T1hvcurveto()


class _T1rlineto(_T1command):

    def __str__(self):
        return "rlineto"

    def __call__(self, context):
        dx = context.t1stack.pop(0)
        dy = context.t1stack.pop(0)
        assert not context.t1stack
        context.path.append(path.rlineto(dx, dy))
        context.x += dx
        context.y += dy

T1rlineto = _T1rlineto()


class _T1rmoveto(_T1command):

    def __str__(self):
        return "rmoveto"

    def __call__(self, context):
        dx = context.t1stack.pop(0)
        dy = context.t1stack.pop(0)
        assert not context.t1stack
        context.path.append(path.rmoveto(dx, dy))
        context.x += dx
        context.y += dy

T1rmoveto = _T1rmoveto()


class _T1rrcurveto(_T1command):

    def __str__(self):
        return "rrcurveto"

    def __call__(self, context):
        dx1 = context.t1stack.pop(0)
        dy1 = context.t1stack.pop(0)
        dx2 = context.t1stack.pop(0)
        dy2 = context.t1stack.pop(0)
        dx3 = context.t1stack.pop(0)
        dy3 = context.t1stack.pop(0)
        assert not context.t1stack
        context.path.append(path.rcurveto(dx1,         dy1,
                                          dx1+dx2,     dy1+dy2,
                                          dx1+dx2+dx3, dy1+dy2+dy3))
        context.x += dx1+dx2+dx3
        context.y += dy1+dy2+dy3

T1rrcurveto = _T1rrcurveto()


class _T1vlineto(_T1command):

    def __str__(self):
        return "vlineto"

    def __call__(self, context):
        dy = context.t1stack.pop(0)
        assert not context.t1stack
        context.path.append(path.rlineto(0, dy))
        context.y += dy

T1vlineto = _T1vlineto()


class _T1vmoveto(_T1command):

    def __str__(self):
        return "vmoveto"

    def __call__(self, context):
        dy = context.t1stack.pop(0)
        assert not context.t1stack
        context.path.append(path.rmoveto(0, dy))
        context.y += dy

T1vmoveto = _T1vmoveto()


class _T1vhcurveto(_T1command):

    def __str__(self):
        return "vhcurveto"

    def __call__(self, context):
        dy1 = context.t1stack.pop(0)
        dx2 = context.t1stack.pop(0)
        dy2 = context.t1stack.pop(0)
        dx3 = context.t1stack.pop(0)
        assert not context.t1stack
        context.path.append(path.rcurveto(0,       dy1,
                                          dx2,     dy1+dy2,
                                          dx2+dx3, dy1+dy2))
        context.x += dx2+dx3
        context.y += dy1+dy2

T1vhcurveto = _T1vhcurveto()


# hint commands

class _T1dotsection(_T1command):

    def __str__(self):
        return "dotsection"

    def __call__(self, context):
        assert not context.t1stack

T1dotsection = _T1dotsection()


class _T1hstem(_T1command):

    def __str__(self):
        return "hstem"

    def __call__(self, context):
        y = context.t1stack.pop(0)
        dy = context.t1stack.pop(0)
        assert not context.t1stack

T1hstem = _T1hstem()


class _T1hstem3(_T1command):

    def __str__(self):
        return "hstem3"

    def __call__(self, context):
        y0 = context.t1stack.pop(0)
        dy0 = context.t1stack.pop(0)
        y1 = context.t1stack.pop(0)
        dy1 = context.t1stack.pop(0)
        y2 = context.t1stack.pop(0)
        dy2 = context.t1stack.pop(0)
        assert not context.t1stack

T1hstem3 = _T1hstem3()


class _T1vstem(_T1command):

    def __str__(self):
        return "hstem"

    def __call__(self, context):
        x = context.t1stack.pop(0)
        dx = context.t1stack.pop(0)
        assert not context.t1stack

T1vstem = _T1vstem()


class _T1vstem3(_T1command):

    def __str__(self):
        return "hstem3(%s, %s, %s, %s, %s, %s)" % (self.x0, self, dx0, self.x1, self.dx1, self.x2, self.dx2)

    def __call__(self, context):
        self.x0 = context.t1stack.pop(0)
        self.dx0 = context.t1stack.pop(0)
        self.x1 = context.t1stack.pop(0)
        self.dx1 = context.t1stack.pop(0)
        self.x2 = context.t1stack.pop(0)
        self.dx2 = context.t1stack.pop(0)
        assert not context.t1stack

T1vstem3 = _T1vstem3()


# arithmetic command

class _T1div(_T1command):

    def __str__(self):
        return "div"

    def __call__(self, context):
        num2 = context.t1stack.pop()
        num1 = context.t1stack.pop()
        context.t1stack.append(num1//num2)

T1div = _T1div()


# subroutine commands

class _T1callothersubr(_T1command):

    def __str__(self):
        return "callothersubr"

    def __call__(self, context):
        othersubrnumber = context.t1stack.pop()
        n = context.t1stack.pop()
        for i in range(n):
            context.psstack.append(context.t1stack.pop())

T1callothersubr = _T1callothersubr()


class _T1callsubr(_T1command):

    def __str__(self):
        return "callsubr"

    def __call__(self, context):
        subrnumber = context.t1stack.pop()
        f = context.t1font
        cmds = f._cmds(f.subrs[subrnumber])
        assert cmds[-1] == T1return
        for cmd in cmds:
            cmd(context)


T1callsubr = _T1callsubr()


class _T1pop(_T1command):

    def __str__(self):
        return "pop"

    def __call__(self, context):
        context.t1stack.append(context.psstack.pop())

T1pop = _T1pop()


class _T1return(_T1command):

    def __str__(self):
        return "return"

    def __call__(self, context):
        pass

T1return = _T1return()


class _T1setcurrentpoint(_T1command):

    def __str__(self):
        return "setcurrentpoint" % self.x, self.y

    def pathitem(self, context):
        x = context.t1stack.pop(0)
        y = context.t1stack.pop(0)
        assert not context.t1stack
        context.path.append(path.moveto(x, y))
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

    def __init__(self, data1, data2, data3):
        self.data1 = data1
        self.data2 = data2
        self.data3 = data3
        self.decoded = 0

    def _decoder(self, code, r, n=4):
        c1 = 52845
        c2 = 22719
        plain = array.array("B")
        for x in array.array("B", code):
            plain.append(x ^ (r >> 8))
            r = ((x + r) * c1 + c2) & 0xffff
        return plain.tostring()[n:]

    def _eexecdecode(self, code):
        return self._decoder(code, 55665)

    def _charstringdecode(self, code):
        # XXX: take into account lenIV
        return self._decoder(code, 4330)

    def _cmds(self, code):
        code = array.array("B", self._charstringdecode(code))
        cmds = []
        x = -1
        while x != 11 and x != 14:
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
        assert not code, "tailing commands"
        return cmds

    def _data2decode(self):
        if self.decoded:
            return
        self.decoded = 1

        self.data2 = self._decoder(self.data2, 55665)

        # extract Subrs
        c = cursor(self.data2, "/Subrs")
        arraycount = c.getint()
        token = c.gettoken(); assert token == "array"
        self.subrs = []
        for i in range(arraycount):
            token = c.gettoken(); assert token == "dup"
            token = c.getint(); assert token == i
            size = c.getint()
            if not i:
                self.subr_rd_token = c.gettoken()
            else:
                token = c.gettoken(); assert token == self.subr_rd_token
            self.subrs.append(c.getbytes(size))
            token = c.gettoken()
            if token == "noaccess":
                token = "%s %s" % (token, c.gettoken())
            if not i:
                self.subr_np_token = token
            else:
                assert token == self.subr_np_token

        # extract glyphs
        self.glyphs = {}
        c = cursor(self.data2, "/CharStrings")
        c.getint()
        token = c.gettoken(); assert token == "dict"
        token = c.gettoken(); assert token == "dup"
        token = c.gettoken(); assert token == "begin"
        while 1:
            chartoken = c.gettoken()
            if chartoken == "end":
                break
            assert chartoken[0] == "/"
            size = c.getint()
            c.gettoken()
            self.glyphs[chartoken[1:]] = c.getbytes(size)
            c.gettoken()

    def getstrippedfont(self, glyphs):

        def findsubrsincode(code):
            lastcmd = None
            for cmd in self._cmds(code):
                if cmd is T1callsubr:
                    assert isinstance(lastcmd, T1value), "can't decode callsubr without full execution (%r)" % lastcmd
                    if not subrs.has_key(lastcmd.value):
                        subrs[lastcmd.value] = 1
                        findsubrsincode(self.subrs[lastcmd.value])
                lastcmd = cmd

        self._data2decode()
        subrs = {}
        for glyph in glyphs:
            findsubrsincode(self.glyphs[glyph])
        return subrs.keys()

    def getsubrcmds(self, n):
        self._data2decode()
        return self._cmds(self.subrs[n])

    def getglyphcmds(self, glyphname):
        self._data2decode()
        return self._cmds(self.glyphs[glyphname])

    def getglyphpath(self, glyphname):
        self._data2decode()
        cmds = self._cmds(self.glyphs[glyphname])
        assert cmds[-1] == T1endchar
        context = T1context(self)
        for cmd in cmds:
            cmd(context)
        return context.path


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
# f = T1pfbfont("/Users/andre/texmf/fonts/type1/bitstrea/iowan/biwr8a.pfb")

c = canvas.canvas()
for i in range(26):
    c.stroke(f.getglyphpath(chr(97+i)), [trafo.scale(0.005), trafo.translate(5*i, 5)])
    c.stroke(f.getglyphpath(chr(65+i)), [trafo.scale(0.005), trafo.translate(5*i, 0)])
c.writeEPSfile("t1disasm")

# the following fails ... ;-(
# print f.getstrippedfont(["h", "e", "l", "o", "comma", "w", "r", "d", "exclam"])
