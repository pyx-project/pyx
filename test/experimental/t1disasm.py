import array
import sys; sys.path.insert(0, "../..")
from pyx import canvas, path, trafo

# XXX: we do not yet transform between font coordinates in its design size and postsript points

class T1context:

    def __init__(self, callsubr):
        self.callsubr = callsubr

        self.path = None
        self.wx = None
        self.wy = None
        self.t1stack = []
        self.psstack = []
        self.valid = 1

    def invalidate(self):
        assert self.valid
        self.valid = 0


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
        context.invalidate()

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

T1closepath = _T1closepath()


class _T1hlineto(_T1command):

    def __str__(self):
        return "hlineto"

    def __call__(self, context):
        dx = context.t1stack.pop(0)
        assert not context.t1stack
        context.path.append(path.rlineto(dx, 0))

T1hlineto = _T1hlineto()


class _T1hmoveto(_T1command):

    def __str__(self):
        return "hmoveto"

    def __call__(self, context):
        dx = context.t1stack.pop(0)
        assert not context.t1stack
        context.path.append(path.rmoveto(dx, 0))

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

T1hvcurveto = _T1hvcurveto()


class _T1rlineto(_T1command):

    def __str__(self):
        return "rlineto"

    def __call__(self, context):
        dx = context.t1stack.pop(0)
        dy = context.t1stack.pop(0)
        assert not context.t1stack
        context.path.append(path.rlineto(dx, dy))

T1rlineto = _T1rlineto()


class _T1rmoveto(_T1command):

    def __str__(self):
        return "rmoveto"

    def __call__(self, context):
        dx = context.t1stack.pop(0)
        dy = context.t1stack.pop(0)
        assert not context.t1stack
        context.path.append(path.rmoveto(dx, dy))

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

T1rrcurveto = _T1rrcurveto()


class _T1vlineto(_T1command):

    def __str__(self):
        return "vlineto"

    def __call__(self, context):
        dy = context.t1stack.pop(0)
        assert not context.t1stack
        context.path.append(path.rlineto(0, dy))

T1vlineto = _T1vlineto()


class _T1vmoveto(_T1command):

    def __str__(self):
        return "vmoveto"

    def __call__(self, context):
        dy = context.t1stack.pop(0)
        assert not context.t1stack
        context.path.append(path.rmoveto(0, dy))

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
        context.callsubr(subrnumber, context)

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
        # check to be at the end of a subroutine
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

T1setcurrentpoint = _T1setcurrentpoint()


##########################

class T1font:

    def __init__(self, pfbfile):
        def pfblength(s):
            if len(s) != 4:
                raise ValueError("invalid string length")
            return (ord(s[0]) +
                    ord(s[1])*256 +
                    ord(s[2])*256*256 +
                    ord(s[3])*256*256*256)
        f = open(pfbfile, "rb")
        assert f.read(2) != "7F01"
        self.data1 = f.read(pfblength(f.read(4)))
        assert f.read(2) != "7F02"
        self.data2 = f.read(pfblength(f.read(4)))
        assert f.read(2) != "7F01"
        self.data3 = f.read(pfblength(f.read(4)))
        assert f.read(2) != "7F03"
        assert not f.read(1)

        # decode data2
        self.data2 = self.decode(self.data2, 55665)

        # the following is a quick'n'dirty parser
        # we need a real tokenizer (line end handling) etc.
        # see chapter 10 in the T1 spec. (ATM compatibility)

        # extract Subrs
        self.subrs = {}
        pos = self.data2.find("Subrs")
        pos = self.data2.find("array", pos) + 7 # \r\n
        while self.data2[pos: pos+4] == "dup ":
            pos += 4
            newpos = self.data2.find(" ", pos)
            n = int(self.data2[pos: newpos])
            pos = newpos + 1
            newpos = self.data2.find(" ", pos)
            l = int(self.data2[pos: newpos])
            pos = newpos
            assert self.data2[pos: pos+4] == " RD "
            pos += 4
            # decoding correct???
            self.subrs[n] = self.decode(self.data2[pos: pos+l], 4330) # implement lenIV
            pos += l
            assert self.data2[pos: pos+3] == " NP"
            pos += 5 # \r\n

        # extract glyphs
        self.glyphs = {}
        pos = self.data2.find("CharStrings")
        pos = self.data2.find("begin", pos) + 7 # \r\n
        while self.data2[pos] == "/":
            newpos = self.data2.find(" ", pos)
            glyphname = self.data2[pos+1: newpos]
            pos = newpos + 1
            newpos = self.data2.find(" ", pos)
            l = int(self.data2[pos: newpos])
            pos = newpos
            assert self.data2[pos: pos+4] == " RD "
            pos += 4
            self.glyphs[glyphname] = self.decode(self.data2[pos: pos+l], 4330) # implement lenIV
            pos += l
            assert self.data2[pos: pos+3] == " ND"
            pos += 5 # \r\n

        # note: when lenIV is zero, no charstring decoding is necessary

    def decode(self, code, r, n=4):
        c1 = 52845
        c2 = 22719
        plain = array.array("B")
        for x in array.array("B", code):
            plain.append(x ^ (r >> 8))
            r = ((x + r) * c1 + c2) & 0xffff
        return plain.tostring()[n: ]

    def commands(self, s):
        s = array.array("B", s)
        cmds = []
        while 1:
            x = s.pop(0)
            if 0 <= x < 32:
                if x == 1:
                    cmds.append(T1hstem)
                elif x == 3:
                    cmds.append(T1vstem)
                elif x == 4:
                    cmds.append(T1vmoveto)
                elif x == 5:
                    cmds.append(T1rlineto)
                elif x == 6:
                    cmds.append(T1hlineto)
                elif x == 7:
                    cmds.append(T1vlineto)
                elif x == 8:
                    cmds.append(T1rrcurveto)
                elif x == 9:
                    cmds.append(T1closepath)
                elif x == 10:
                    cmds.append(T1callsubr)
                elif x == 11:
                    cmds.append(T1return)
                    break
                elif x == 12:
                    x = s.pop(0)
                    if x == 0:
                        cmds.append(T1dotsection)
                    elif x == 1:
                        cmds.append(T1vstem3)
                    elif x == 2:
                        cmds.append(T1hstem3)
                    elif x == 6:
                        cmds.append(T1seac)
                    elif x == 7:
                        cmds.append(T1sbw)
                    elif x == 12:
                        cmds.append(T1div)
                    elif x == 16:
                        cmds.append(T1callothersubr)
                    elif x == 17:
                        cmds.append(T1pop)
                    elif x == 33:
                        cmds.append(T1setcurrentpoint)
                    else:
                        raise ValueError("unknown escaped command %d" % x)
                elif x == 13:
                    cmds.append(T1hsbw)
                elif x == 14:
                    cmds.append(T1endchar)
                    break
                elif x == 21:
                    cmds.append(T1rmoveto)
                elif x == 22:
                    cmds.append(T1hmoveto)
                elif x == 30:
                    cmds.append(T1vhcurveto)
                elif x == 31:
                    cmds.append(T1hvcurveto)
                else:
                    raise ValueError("unknown command %d" % x)
            elif 32 <= x <= 246:
                cmds.append(T1value(x-139))
            elif 247 <= x <= 250:
                cmds.append(T1value(((x - 247)*256) + s.pop(0) + 108))
            elif 251 <= x <= 254:
                cmds.append(T1value(-((x - 251)*256) - s.pop(0) - 108))
            else:
                x = ((s.pop(0)*256+s.pop(0))*256+s.pop(0))*256+s.pop(0)
                if x > (1l << 31):
                    cmds.append(T1value(x - (1l << 32)))
                else:
                    cmds.append(T1value(x))
        assert not s, "tailing commands"
        return cmds

    def getsubrcmds(self, n):
        return self.commands(self.subrs[n])

    def getglyphcmds(self, glyphname):
        return self.commands(self.glyphs[glyphname])

    def callsubr(self, n, context):
        for cmd in self.getsubrcmds(n):
            cmd(context)

    def getglyphpath(self, glyphname):
        context = T1context(self.callsubr)
        for cmd in self.getglyphcmds(glyphname):
            cmd(context)
        assert not context.valid
        return context.path


def printcommands(commands):
    print "\n".join([str(command) for command in commands])

def getpath(commands):
    context = T1context
    pathitems = []
    for command in commands:
        pathitem = command.pathitem(currentpoint)
        if pathitem:
            pathitems.append(pathitem)
    return path.path(*pathitems)

f = T1font("cmr10.pfb")
#printcommands(f.getsubr(5))
#printcommands(f.getsubrcmds(4))
#printcommands(f.getglyphcmds("d"))

c = canvas.canvas()
c.stroke(f.getglyphpath("d"), [trafo.scale(0.005)])
c.writeEPSfile("t1disasm")
