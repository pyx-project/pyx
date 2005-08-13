import array

class t1font:

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
        # XXX: stack might not be correct
        s = array.array("B", s)
        stack = []
        while 1:
            x = s.pop(0)
            if 0 <= x < 32:
                if x == 1:
                    print "hstem(%d, %d)" % (stack.pop(0), stack.pop(0))
                elif x == 3:
                    print "vstem(%d, %d)" % (stack.pop(0), stack.pop(0))
                elif x == 4:
                    print "vmoveto(%d)" % stack.pop(0)
                elif x == 5:
                    print "rlineto(%d, %d)" % (stack.pop(0), stack.pop(0))
                elif x == 6:
                    print "hlineto(%d)" % stack.pop(0)
                elif x == 7:
                    print "vlineto(%d)" % stack.pop(0)
                elif x == 8:
                    print "rrcurveto(%d, %d, %d, %d, %d, %d)" % (stack.pop(0), stack.pop(0), stack.pop(0), stack.pop(0), stack.pop(0), stack.pop(0))
                elif x == 9:
                    print "closepath"
                elif x == 10:
                    print "callsubr (not implemented)" % stack.pop()
                elif x == 11:
                    print "return"
                    # those asserts might be paranoid (and wrong for certain fonts ?!)
                    assert not len(s), "tailing commands: %s" % s
                    assert not len(stack), "stack is not empty: %s" % stack
                    break
                elif x == 12:
                    x = s.pop(0)
                    if x == 0:
                        print "dotsection"
                    elif x == 1:
                        print "vstem3(%d, %d, %d, %d, %d, %d)" % (stack.pop(0), stack.pop(0), stack.pop(0), stack.pop(0), stack.pop(0), stack.pop(0))
                    elif x == 2:
                        print "hstem3(%d, %d, %d, %d, %d, %d)" % (stack.pop(0), stack.pop(0), stack.pop(0), stack.pop(0), stack.pop(0), stack.pop(0))
                    elif x == 6:
                        print "seac(%d, %d, %d, %d, %d)" % (stack.pop(0), stack.pop(0), stack.pop(0), stack.pop(0), stack.pop(0))
                    elif x == 7:
                        print "sbw(%d, %d, %d, %d)" % (stack.pop(0), stack.pop(0), stack.pop(0), stack.pop(0))
                    elif x == 12:
                        print "div(%d, %d)" % (stack.pop(), stack.pop())
                    elif x == 16:
                        print "callothersubr (not implemented)"
                    elif x == 17:
                        print "pop"
                    elif x == 33:
                        print "setcurrentpoint(%d, %d)" % (stack.pop(0), stack.pop(0))
                    else:
                        raise ValueError("unknown escaped command %d" % x)
                elif x == 13:
                    print "hsbw(%d, %d)" % (stack.pop(0), stack.pop(0))
                elif x == 14:
                    print "endchar"
                    # those asserts might be paranoid (and wrong for certain fonts ?!)
                    assert not len(s), "tailing commands: %s" % s
                    assert not len(stack), "stack is not empty: %s" % stack
                    break
                elif x == 21:
                    print "rmoveto(%d, %d)" % (stack.pop(0), stack.pop(0))
                elif x == 22:
                    print "hmoveto(%d)" % stack.pop(0)
                elif x == 30:
                    print "vhcurveto(%d, %d, %d, %d)" % (stack.pop(0), stack.pop(0), stack.pop(0), stack.pop(0))
                elif x == 31:
                    print "hvcurveto(%d, %d, %d, %d)" % (stack.pop(0), stack.pop(0), stack.pop(0), stack.pop(0))
                else:
                    raise ValueError("unknown command %d" % x)
            elif 32 <= x <= 246:
                stack.append(x-139)
            elif 247 <= x <= 250:
                stack.append(((x - 247)*256) + s.pop(0) + 108)
            elif 251 <= x <= 254:
                stack.append(-((x - 251)*256) - s.pop(0) - 108)
            else:
                # check this
                x = ((s.pop(0)*256+s.pop(0))*256+s.pop(0))*256+s.pop(0)
                if x > (1l << 31):
                    stack.append(x - (1l << 32))
                else:
                    stack.append(x)

    def getsubr(self, n):
        return self.disasm(self.subrs[n])

    def getglyph(self, glyphname):
        return self.disasm(self.glyphs[glyphname])


f = t1font("cmr10.pfb")
f.getsubr(5)
f.getglyph("A")
