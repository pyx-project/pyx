import array
import sys; sys.path.insert(0, "../..")
from pyx import canvas, path, trafo

# XXX: we do not yet transform between font coordinates in its design size and postsript points


# T1 commands

class _T1command:

    def __str__(self):
        "returns a string representation of the T1 command"
        raise NotImplementedError

    def pathitem(self, currentpoint):
        "return the pathitem represented by the T1 command and/or update the currentpoint"
        # by default do nothing
        return None

# commands for starting and finishing

class T1endchar(_T1command):

    def __str__(self):
        return "endchar"


class T1hsbw(_T1command):

    def __init__(self, sbx, wx):
        self.sbx = sbx
        self.wx = wx

    def __str__(self):
        return "hsbw(%s, %s)" % (self.sbx, self.wx)

    def pathitem(self, currentpoint):
        assert not currentpoint.valid()
        currentpoint.x_pt = self.sbx
        currentpoint.y_pt = 0
        return path.moveto(self.sbx, 0)


class T1seac(_T1command):

    def __init__(self, asb, adx, ady, bchar, achar):
        self.asb = asb
        self.adx = adx
        self.ady = ady
        self.bchar = bchar
        self.achar = achar

    def __str__(self):
        return "seac(%s, %s, %s, %s, %s)" % (self.asb, self.adx, self.ady, self.bchar, self.achar)

    def pathitem(self, currentpoint):
        raise NotImplementedError("can't convert glyph containing a T1seac into a path")


class T1sbw(_T1command):

    def __init__(self, sbx, sby, wx, wy):
        self.sbx = sbx
        self.sby = sby
        self.wx = wx
        self.wy = wy

    def __str__(self):
        return "sbw(%s, %s, %s, %s)" % (self.sbx, self.sby, self.wx, self.wy)

    def pathitem(self, currentpoint):
        assert not currentpoint.valid()
        currentpoint.x_pt = self.sbx
        currentpoint.y_pt = self.sby
        return path.moveto(self.sbx, self.sby)


# path construction commands

class T1closepath(_T1command):

    def __str__(self):
        return "closepath"

    def pathitem(self, currentpoint):
        # note: closepath does *not* invalidate the currentpoint!
        assert currentpoint.valid()
        return path.closepath()


class T1hlineto(_T1command):

    def __init__(self, dx):
        self.dx = dx

    def __str__(self):
        return "hlineto(%s)" % self.dx

    def pathitem(self, currentpoint):
        currentpoint.x_pt += self.dx
        return path.rlineto(self.dx, 0)


class T1hmoveto(_T1command):

    def __init__(self, dx):
        self.dx = dx

    def __str__(self):
        return "hmoveto(%s)" % self.dx

    def pathitem(self, currentpoint):
        currentpoint.x_pt += self.dx
        return path.rmoveto(self.dx, 0)


class T1hvcurveto(_T1command):

    def __init__(self, dx1, dx2, dy2, dy3):
        self.dx1 = dx1
        self.dx2 = dx2
        self.dy2 = dy2
        self.dy3 = dy3

    def __str__(self):
        return "hvcurveto(%s, %s, %s, %s)" % (self.dx1, self.dx2, self.dy2, self.dy3)

    def pathitem(self, currentpoint):
        currentpoint.x_pt += self.dx1 + self.dx2
        currentpoint.y_pt += self.dy2 + self.dy3
        return path.rcurveto(self.dx1,          0,
                             self.dx1+self.dx2, self.dy2,
                             self.dx1+self.dx2, self.dy2+self.dy3)


class T1rlineto(_T1command):

    def __init__(self, dx, dy):
        self.dx = dx
        self.dy = dy

    def __str__(self):
        return "rlineto(%s, %s)" % (self.dx, self.dy)

    def pathitem(self, currentpoint):
        currentpoint.x_pt += self.dx
        currentpoint.y_pt += self.dy
        return path.rlineto(self.dx, self.dy)


class T1rmoveto(_T1command):

    def __init__(self, dx, dy):
        self.dx = dx
        self.dy = dy

    def __str__(self):
        return "rmoveto(%s, %s)" % (self.dx, self.dy)

    def pathitem(self, currentpoint):
        currentpoint.x_pt += self.dx
        currentpoint.y_pt += self.dy
        return path.rmoveto(self.dx, self.dy)


class T1rrcurveto(_T1command):

    def __init__(self, dx1, dy1, dx2, dy2, dx3, dy3):
        self.dx1 = dx1
        self.dy1 = dy1
        self.dx2 = dx2
        self.dy2 = dy2
        self.dx3 = dx3
        self.dy3 = dy3

    def __str__(self):
        return "rrcurveto(%s, %s, %s, %s, %s, %s)" % (self.dx1, self.dy1, self.dx2, self.dy2, self.dx3, self.dy3)

    def pathitem(self, currentpoint):
        currentpoint.x_pt += self.dx1 + self.dx2 + self.dx3
        currentpoint.y_pt += self.dy1 + self.dy2 + self.dy3
        return path.rcurveto(self.dx1,                   self.dy1,
                             self.dx1+self.dx2,          self.dy1+self.dy2,
                             self.dx1+self.dx2+self.dx3, self.dy1+self.dy2+self.dy3)


class T1vlineto(_T1command):

    def __init__(self, dy):
        self.dy = dy

    def __str__(self):
        return "vlineto(%s)" % self.dy

    def pathitem(self, currentpoint):
        currentpoint.y_pt += self.dy
        return path.rlineto(0, self.dy)


class T1vmoveto(_T1command):

    def __init__(self, dy):
        self.dy = dy

    def __str__(self):
        return "vmoveto(%s)" % self.dy

    def pathitem(self, currentpoint):
        currentpoint.y_pt += self.dy
        return path.rmoveto(0, self.dy)


class T1vhcurveto(_T1command):

    def __init__(self, dy1, dx2, dy2, dx3):
        self.dy1 = dy1
        self.dx2 = dx2
        self.dy2 = dy2
        self.dx3 = dx3

    def __str__(self):
        return "vhcurveto(%s, %s, %s, %s)" % (self.dy1, self.dx2, self.dy2, self.dx3)

    def pathitem(self, currentpoint):
        currentpoint.x_pt += self.dx2 + self.dx3
        currentpoint.y_pt += self.dy1 + self.dy2
        return path.rcurveto(0,                 self.dy1,
                             self.dx2,          self.dy1+self.dy2,
                             self.dx2+self.dx3, self.dy1+self.dy2)


# hint commands

class T1dotsection(_T1command):

    def __str__(self):
        return "dotsection"


class T1hstem(_T1command):

    def __init__(self, y, dy):
        self.y = y
        self.dy = dy

    def __str__(self):
        return "hstem(%s, %s)" % (self.y, self.dy)


class T1hstem3(_T1command):

    def __init__(self, y0, dy0, y1, dy1, x2, dy2):
        self.y0 = y0
        self.dy0 = dy0
        self.y1 = y1
        self.dy1 = dy1
        self.y2 = y2
        self.dy2 = dy2

    def __str__(self):
        return "hstem3(%s, %s, %s, %s, %s, %s)" % (self.y0, self, dy0, self.y1, self.dy1, self.y2, self.dy2)


class T1vstem(_T1command):

    def __init__(self, x, dx):
        self.x = x
        self.dx = dx

    def __str__(self):
        return "hstem(%s, %s)" % (self.x, self.dx)


class T1vstem3(_T1command):

    def __init__(self, x0, dx0, x1, dx1, x2, dx2):
        self.x0 = x0
        self.dx0 = dx0
        self.x1 = x1
        self.dx1 = dx1
        self.x2 = x2
        self.dx2 = dx2

    def __str__(self):
        return "hstem3(%s, %s, %s, %s, %s, %s)" % (self.x0, self, dx0, self.x1, self.dx1, self.x2, self.dx2)


# arithmetic command

class T1div(_T1command):

    def __init__(self, num1, num2):
        self.num1 = num1
        self.num2 = num2

    def __str__(self):
        return "div(%s, %s)" % (self.num1, self.num2)

    def __float__(self):
        return self.num1/self.num2


# subroutine commands

class T1callothersubr(_T1command):

    def __init__(self, othersubrnumber, *args):
        self.othersubrnumber = othersubrnumber
        self.args = args

    def __str__(self):
        return "callothersubr(%s, %s, %s)" % (", ".join(self.args), len(self.args), self.othersubrnumber)

    def pathitem(self, currentpoint):
        raise NotImplementedError("can't convert glyph containing a T1callothersubr into a path")


class T1callsubr(_T1command):

    def __init__(self, subrnumber):
        self.subrnumber = subrnumber

    def __str__(self):
        return "callsubr(%s)" % self.subrnumber

    def pathitem(self, currentpoint):
        raise NotImplementedError("can't yet convert glyph containing a T1callsubr into a path")


class T1pop(_T1command):

    def __str__(self):
        return "pop"

    def pathitem(self, currentpoint):
        raise NotImplementedError("can't convert glyph containing a T1pop command into a path")


class T1return(_T1command):

    def __str__(self):
        return "return"


class T1setcurrentpoint(_T1command):

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return "setcurrentpoint(%s, %s)" % self.x, self.y

    def pathitem(self, currentpoint):
        currentpoint.x_pt = self.x
        currentpoint.y_pt = self.y
        return path.moveto(self.x, self.y)


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

    def disasm(self, s):
        s = array.array("B", s)
        commands = []
        stack = []
        while 1:
            x = s.pop(0)
            if 0 <= x < 32:
                if x == 1:
                    commands.append(T1hstem(*stack))
                    stack = []
                elif x == 3:
                    commands.append(T1vstem(*stack))
                    stack = []
                elif x == 4:
                    commands.append(T1vmoveto(*stack))
                    stack = []
                elif x == 5:
                    commands.append(T1rlineto(*stack))
                    stack = []
                elif x == 6:
                    commands.append(T1hlineto(*stack))
                    stack = []
                elif x == 7:
                    commands.append(T1vlineto(*stack))
                    stack = []
                elif x == 8:
                    commands.append(T1rrcurveto(*stack))
                    stack = []
                elif x == 9:
                    commands.append(T1closepath())
                    stack = []
                elif x == 10:
                    commands.append(T1callsubr(stack.pop()))
                elif x == 11:
                    commands.append(T1return())
                    # those asserts might be paranoid (and wrong for certain fonts ?!)
                    assert not len(s), "tailing commands: %s" % s
                    assert not len(stack), "stack is not empty: %s" % stack
                    break
                elif x == 12:
                    x = s.pop(0)
                    if x == 0:
                        commands.append(T1dotsection())
                        stack = []
                    elif x == 1:
                        commands.append(T1vstem3(*stack))
                        stack = []
                    elif x == 2:
                        commands.append(T1hstem3(*stack))
                        stack = []
                    elif x == 6:
                        commands.append(T1seac(*stack))
                        stack = []
                    elif x == 7:
                        commands.append(T1sbw(*stack))
                        stack = []
                    elif x == 12:
                        num2 = stack.pop()
                        num1 = stack.pop()
                        stack.append(T1div(num1, num2))
                    elif x == 16:
                        othersubrnumber = stack.pop()
                        args = []
                        for i in range(stack.pop()):
                            args.insert(0, stack.pop())
                        commands.append(T1callothersubr(othersubrnumber, *args))
                    elif x == 17:
                        stack.append(T1pop())
                    elif x == 33:
                        commands.append(T1setcurrentpoint(*stack))
                        stack = []
                    else:
                        raise ValueError("unknown escaped command %d" % x)
                elif x == 13:
                    commands.append(T1hsbw(*stack))
                    stack = []
                elif x == 14:
                    commands.append(T1endchar())
                    # those asserts might be paranoid (and wrong for certain fonts ?!)
                    assert not len(s), "tailing commands: %s" % s
                    assert not len(stack), "stack is not empty: %s" % stack
                    break
                elif x == 21:
                    commands.append(T1rmoveto(*stack))
                    stack = []
                elif x == 22:
                    commands.append(T1hmoveto(*stack))
                    stack = []
                elif x == 30:
                    commands.append(T1vhcurveto(*stack))
                    stack = []
                elif x == 31:
                    commands.append(T1hvcurveto(*stack))
                    stack = []
                else:
                    raise ValueError("unknown command %d" % x)
            elif 32 <= x <= 246:
                stack.append(x-139)
            elif 247 <= x <= 250:
                stack.append(((x - 247)*256) + s.pop(0) + 108)
            elif 251 <= x <= 254:
                stack.append(-((x - 251)*256) - s.pop(0) - 108)
            else:
                x = ((s.pop(0)*256+s.pop(0))*256+s.pop(0))*256+s.pop(0)
                if x > (1l << 31):
                    stack.append(x - (1l << 32))
                else:
                    stack.append(x)
        return commands

    def getsubr(self, n):
        return self.disasm(self.subrs[n])

    def getglyph(self, glyphname):
        return self.disasm(self.glyphs[glyphname])


def printcommands(commands):
    print "\n".join([str(command) for command in commands])

def getpath(commands):
    currentpoint = path._currentpoint()
    pathitems = []
    for command in commands:
        pathitem = command.pathitem(currentpoint)
        if pathitem:
            pathitems.append(pathitem)
    return path.path(*pathitems)

f = T1font("cmr10.pfb")
#printcommands(f.getsubr(5))
#printcommands(f.getglyph("A"))

c = canvas.canvas()
c.stroke(getpath(f.getglyph("A")), [trafo.scale(0.005)])
c.writeEPSfile("t1disasm")
