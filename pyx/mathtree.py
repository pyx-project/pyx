import string
import re


def HeadWhiteSpace(arg):
    i = 0
    while (len(arg) > i) and (arg[i] in string.whitespace):
        i = i + 1
    return i


def MatchStr(arg, MatchStr):
    pos = HeadWhiteSpace(arg)
    if (len(arg) >= pos + len(MatchStr)) and \
       (arg[pos: pos+len(MatchStr)] == MatchStr):
        return pos + len(MatchStr)


class MT:

    def __init__(self):
        self.ArgC = 0
        self.ArgV = [ ]

    def __repr__(self, depth = 0):
        assert len(self.ArgV) == self.ArgC, "wrong number of arguments"
        result = ""
        for i in range(depth):
           result = result + "    "
        result = result + str(self.__class__) + "().Init(\n"
        for SubTree in self.ArgV:
            if SubTree != self.ArgV[-1]:
                result = result + SubTree.__repr__(depth + 1) + ",\n"
            else:
                result = result + SubTree.__repr__(depth + 1) + ")"
        return result

    def AddArg(self, Arg):
        assert self.ArgC > 0, "can't add an argument"
        if len(self.ArgV) < self.ArgC:
            self.ArgV = self.ArgV + [ Arg, ]
        else:
            self.ArgV[-1].AddArg(Arg)

    def DependOn(self, arg):
        for Arg in self.ArgV:
            if Arg.DependOn(arg):
                return 1
        return 0

    def Derivative(self, arg):
        if not self.DependOn(arg):
            return MTValConst().Init(0.0)
        return self.CalcDerivative(arg)

    def VarList(self):
        list = [ ]
        for Arg in self.ArgV:
            list = list + Arg.VarList()
        return list


class MTVal(MT):

    pass


ConstPattern = re.compile(r"-?\d*((\d\.?)|(\.?\d))\d*(E[+-]?\d+)?",
                          re.IGNORECASE)

class MTValConst(MTVal):

    def __str__(self):
        return str(self.Const)

    def __repr__(self, depth = 0):
        assert len(self.ArgV) == self.ArgC, "wrong number of arguments"
        result = ""
        for i in range(depth):
           result = result + "    "
        result = result + str(self.__class__) + "().Init(" + str(self) + ")"
        return result

    def Init(self, value):
        self.Const = value
        return self

    def InitByMatch(self, arg):
        pos = HeadWhiteSpace(arg)
        Match = ConstPattern.match(arg[pos:])
        if Match:
            self.Const =  string.atof(Match.group())
            return pos + Match.end()

    def CalcDerivative(self, arg):
        assert 0, "expression doesn't depend on " + arg


VarPattern = re.compile(r"[a-z][a-z0-9_]*", re.IGNORECASE)

class MTValVar(MTVal):

    def __str__(self):
        return str(self.Var)

    def __repr__(self, depth = 0):
        assert len(self.ArgV) == self.ArgC, "wrong number of arguments"
        result = ""
        for i in range(depth):
           result = result + "    "
        result = result + str(self.__class__) + "().Init(\"" + str(self) + "\")"
        return result

    def Init(self, value):
        self.Var = value
        return self

    def InitByMatch(self, arg):
        pos = HeadWhiteSpace(arg)
        Match = VarPattern.match(arg[pos:])
        if Match:
            self.Var = Match.group()
            return pos + Match.end()

    def CalcDerivative(self, arg):
        if arg != self.Var:
            assert 0, "expression doesn't depend on " + arg
        return MTValConst().Init(1.0)

    def DependOn(self,arg):
        if arg == self.Var:
            return 1
        return 0

    def VarList(self):
        return [self.Var, ]


class MTFunc(MT):

    def InitByMatchStr(self, arg, matchstr):
        pos = MatchStr(arg, matchstr)
        if pos:
            pos2 = MatchStr(arg[pos:], "(")
            if pos2:
                return pos + pos2


class MTFunc1(MTFunc):

    def __init__(self):
        MTFunc.__init__(self)
        self.ArgC = 1

    def Init(self, Arg):
        self.ArgV = [Arg, ]
        return self


class MTFunc1Neg(MTFunc1):

    def __str__(self):
        return "neg(" + self.ArgV[0].__str__() + ")"

    def InitByMatch(self, arg):
        return self.InitByMatchStr(arg, "neg")

    def CalcDerivative(self, arg):
        return MTFunc1Neg().Init(self.ArgV[0].CalcDerivative(arg))


class MTFunc1Sgn(MTFunc1):

    def __str__(self):
        return "sgn(" + self.ArgV[0].__str__() + ")"

    def InitByMatch(self, arg):
        return self.InitByMatchStr(arg, "sgn")

    def CalcDerivative(self, arg):
        return MTValConst().Init(0.0)


class MTFunc1Sqrt(MTFunc1):

    def __str__(self):
        return "sqrt(" + self.ArgV[0].__str__() + ")"

    def InitByMatch(self, arg):
        return self.InitByMatchStr(arg, "sqrt")

    def CalcDerivative(self, arg):
        return MTOpMul().Init(
                   MTOpDiv().Init(
                       MTValConst().Init(0.5),
                       self),
                   self.ArgV[0].CalcDerivative(arg))


class MTFunc1Exp(MTFunc1):

    def __str__(self):
        return "exp(" + self.ArgV[0].__str__() + ")"

    def InitByMatch(self, arg):
        return self.InitByMatchStr(arg, "exp")

    def CalcDerivative(self, arg):
        return MTOpMul().Init(self, self.ArgV[0].CalcDerivative(arg))


class MTFunc1Log(MTFunc1):

    def __str__(self):
        return "log(" + self.ArgV[0].__str__() + ")"

    def InitByMatch(self, arg):
        return self.InitByMatchStr(arg, "log")

    def CalcDerivative(self, arg):
        return MTOpDiv().Init(self.ArgV[0].CalcDerivative(arg), self.ArgV[0])


class MTFunc1Sin(MTFunc1):

    def __str__(self):
        return "sin(" + self.ArgV[0].__str__() + ")"

    def InitByMatch(self, arg):
        return self.InitByMatchStr(arg, "sin")

    def CalcDerivative(self, arg):
        return MTOpMul().Init(
                   MTFunc1Cos().Init(self.ArgV[0]),
                   self.ArgV[0].CalcDerivative(arg))

class MTFunc1Cos(MTFunc1):

    def __str__(self):
        return "cos(" + self.ArgV[0].__str__() + ")"

    def InitByMatch(self, arg):
        return self.InitByMatchStr(arg, "cos")

    def CalcDerivative(self, arg):
        return MTOpMul().Init(
                   MTFunc1Neg().Init(MTFunc1Sin().Init(self.ArgV[0])),
                   self.ArgV[0].CalcDerivative(arg))


class MTFunc1Tan(MTFunc1):

    def __str__(self):
        return "tan(" + self.ArgV[0].__str__() + ")"

    def InitByMatch(self, arg):
        return self.InitByMatchStr(arg, "tan")

    def CalcDerivative(self, arg):
        return MTOpDiv().Init(
                   self.ArgV[0].CalcDerivative(arg),
                   MTOpPow().Init(
                       MTFunc1Cos().Init(self.ArgV[0]),
                       MTValConst().Init(2.0)))


class MTFunc1ArcSin(MTFunc1):

    def __str__(self):
        return "arcsin(" + self.ArgV[0].__str__() + ")"

    def InitByMatch(self, arg):
        return self.InitByMatchStr(arg, "arcsin")

    def CalcDerivative(self, arg):
        return MTOpDiv().Init(
                   self.ArgV[0].CalcDerivative(arg),
                   MTFunc1Sqrt().Init(
                       MTOpSub().Init(
                           MTValConst().Init(1.0),
                           MTOpPow().Init(
                               self.ArgV[0],
                               MTValConst().Init(2.0)))))


class MTFunc1ArcCos(MTFunc1):

    def __str__(self):
        return "arccos(" + self.ArgV[0].__str__() + ")"

    def InitByMatch(self, arg):
        return self.InitByMatchStr(arg, "arccos")

    def deriavte(self, arg):
        return MTOpDiv().Init(
                   MTFunc1Neg().Init(self.ArgV[0].CalcDerivative(arg)),
                   MTFunc1Sqrt().Init(
                       MTOpSub().Init(
                           MTValConst().Init(1.0),
                           MTOpPow().Init(
                               self.ArgV[0],
                               MTValConst().Init(2.0)))))


class MTFunc1ArcTan(MTFunc1):

    def __str__(self):
        return "arctan(" + self.ArgV[0].__str__() + ")"

    def InitByMatch(self, arg):
        return self.InitByMatchStr(arg, "arctan")

    def deriavte(self, arg):
        return MTOpDiv().Init(
                   self.ArgV[0].CalcDerivative(arg),
                   MTOpAdd().Init(
                       MTValConst().Init(1.0),
                       MTOpPow().Init(
                           self.ArgV[0],
                           MTValConst().Init(2.0))))


class MTFunc2(MTFunc):

    def __init__(self):
        MTFunc.__init__(self)
        self.ArgC = 2

    def Init(self, Arg1, Arg2):
        self.ArgV = [Arg1, Arg2, ]
        return self


class MTFunc2Norm(MTFunc2):

    def __str__(self):
        return "norm(" + self.ArgV[0].__str__() + "," + \
                         self.ArgV[1].__str__() + ")"

    def InitByMatch(self, arg):
        return self.InitByMatchStr(arg, "norm")

    def CalcDerivative(self, arg):
        if self.ArgV[0].DependOn(arg):
            if self.ArgV[1].DependOn(arg):
                return MTOpDiv().Init(
                           MTOpAdd().Init(
                               MTOpMul().Init(
                                   self.ArgV[0],
                                   self.ArgV[0].CalcDerivative(arg)),
                               MTOpMul().Init(
                                   self.ArgV[1],
                                   self.ArgV[1].CalcDerivative(arg))),
                           self)
            else:
                return MTOpDiv().Init(
                           MTOpMul().Init(
                               self.ArgV[0],
                               self.ArgV[0].CalcDerivative(arg)),
                           self)
        else:
            if self.ArgV[1].DependOn(arg):
                return MTOpDiv().Init(
                           MTOpMul().Init(
                               self.ArgV[1],
                               self.ArgV[1].CalcDerivative(arg)),
                           self)


class MTOp(MT):

    def __init__(self, Level):
        MT.__init__(self)
        self.ArgC = 2
        self.BraketBarrier = 0
        self.Level = Level

    def __str__(self, symbol = "?"):
        result = ""
        if isinstance(self.ArgV[0], MTOp) and\
           self.Level > self.ArgV[0].Level:
           result = result + "(" + self.ArgV[0].__str__() + ")"
        else:
           result = result + self.ArgV[0].__str__()
        result = result + symbol
        if isinstance(self.ArgV[1], MTOp) and\
           self.Level >= self.ArgV[1].Level:
           result = result + "(" + self.ArgV[1].__str__() + ")"
        else:
           result = result + self.ArgV[1].__str__()
        return result

    def Init(self, Arg1, Arg2):
        self.ArgV = [Arg1, Arg2, ]
        return self

    def InitByMatchStr(self, arg, MatchStr):
        pos = HeadWhiteSpace(arg)
        if arg[pos: pos+len(MatchStr)] == MatchStr:
            return pos + len(MatchStr)


class MTOpAdd(MTOp):

    def __init__(self):
        MTOp.__init__(self, 1)

    def __str__(self):
        return MTOp.__str__(self, "+")

    def InitByMatch(self, arg):
        return self.InitByMatchStr(arg, "+")

    def CalcDerivative(self, arg):
        if self.ArgV[0].DependOn(arg):
            if self.ArgV[1].DependOn(arg):
                return MTOpAdd().Init(
                           self.ArgV[0].CalcDerivative(arg),
                           self.ArgV[1].CalcDerivative(arg))
            else:
                return self.ArgV[0].CalcDerivative(arg)
        else:
            if self.ArgV[1].DependOn(arg):
                return self.ArgV[1].CalcDerivative(arg)


class MTOpSub(MTOp):

    def __init__(self):
        MTOp.__init__(self, 2)

    def __str__(self):
        return MTOp.__str__(self, "-")
        
    def InitByMatch(self, arg):
        return self.InitByMatchStr(arg, "-")

    def CalcDerivative(self, arg):
        if self.ArgV[0].DependOn(arg):
            if self.ArgV[1].DependOn(arg):
                return MTOpSub().Init(
                           self.ArgV[0].CalcDerivative(arg),
                           self.ArgV[1].CalcDerivative(arg))
            else:
                return self.ArgV[0].CalcDerivative(arg)
        else:
            if self.ArgV[1].DependOn(arg):
                return MTFunc1Neg().Init(self.ArgV[1].CalcDerivative(arg))


class MTOpMul(MTOp):

    def __init__(self):
        MTOp.__init__(self, 3)

    def __str__(self):
        return MTOp.__str__(self, "*")

    def InitByMatch(self, arg):
        return self.InitByMatchStr(arg, "*")

    def CalcDerivative(self, arg):
        if self.ArgV[0].DependOn(arg):
            if self.ArgV[1].DependOn(arg):
                return MTOpAdd().Init(
                           MTOpMul().Init(
                               self.ArgV[0],
                               self.ArgV[1].CalcDerivative(arg)),
                           MTOpMul().Init(
                               self.ArgV[0].CalcDerivative(arg),
                               self.ArgV[1]))
            else:
                return MTOpMul().Init(
                           self.ArgV[0].CalcDerivative(arg),
                           self.ArgV[1])
        else:
            if self.ArgV[1].DependOn(arg):
                return MTOpMul().Init(
                           self.ArgV[0],
                           self.ArgV[1].CalcDerivative(arg))


class MTOpDiv(MTOp):

    def __init__(self):
        MTOp.__init__(self, 4)

    def __str__(self):
        return MTOp.__str__(self, "/")

    def InitByMatch(self, arg):
        return self.InitByMatchStr(arg, "/")

    def CalcDerivative(self, arg):
        if self.ArgV[0].DependOn(arg):
            if self.ArgV[1].DependOn(arg):
                return MTOpMul().Init(
                           MTOpSub().Init(
                               MTOpMul().Init(
                                   self.ArgV[0].CalcDerivative(arg),
                                   self.ArgV[1]),
                               MTOpMul().Init(
                                   self.ArgV[0],
                                   self.ArgV[1].CalcDerivative(arg))),
                           MTOpPow().Init(
                               self.ArgV[1],
                               MTValConst().Init(-2.0)))
            else:
                return MTOpDiv().Init(
                           self.ArgV[0].CalcDerivative(arg),
                           self.ArgV[1])
        else:
            if self.ArgV[1].DependOn(arg):
                return MTOpMul().Init(
                           MTOpMul().Init(
                               MTFunc1Neg().Init(self.ArgV[0]),
                               MTOpPow().Init(
                                   self.ArgV[1],
                                   MTValConst().Init(-2.0))),
                           self.ArgV[1].CalcDerivative(arg))


class MTOpPow(MTOp):

    def __init__(self):
        MTOp.__init__(self, 5)

    def __str__(self):
        return MTOp.__str__(self, "^")

    def InitByMatch(self, arg):
        pos = self.InitByMatchStr(arg, "^")
        if pos:
            return pos
        else:
            return self.InitByMatchStr(arg, "**")

    def CalcDerivative(self, arg):
        if self.ArgV[0].DependOn(arg):
            if self.ArgV[1].DependOn(arg):
                return MTOpMul().Init(
                           MTOpPow().Init(
                               self.ArgV[0],
                               self.ArgV[1]),
                           MTOpAdd().Init(
                               MTOpMul().Init(
                                   MTFunc1Log().Init(self.ArgV[0]),
                                   self.ArgV[1].CalcDerivative(arg)),
                               MTOpMul().Init(
                                   self.ArgV[1],
                                   MTOpDiv().Init(
                                       self.ArgV[0].CalcDerivative(arg),
                                       self.ArgV[0]))))
            else:
                return MTOpMul().Init(
                           self.ArgV[1],
                           MTOpMul().Init(
                               MTOpPow().Init(
                                   self.ArgV[0],
                                   MTOpSub().Init(
                                       self.ArgV[1],
                                       MTValConst().Init(1.0))),
                               self.ArgV[0].CalcDerivative(arg)))
        else:
            if self.ArgV[1].DependOn(arg):
                return MTOpMul().Init(
                           MTOpMul().Init(
                               MTOpPow().Init(
                                   self.ArgV[0],
                                   self.ArgV[1]),
                               MTFunc1Log().Init(self.ArgV[0])),
                           self.ArgV[1].CalcDerivative(arg))


NegPattern = re.compile(r"\s*-(?![0-9\.])")

def MathTree(arg, pos = 0):
    Tree = None
    Match = NegPattern.match(arg[pos:])
    if Match:
        Tree = MTFunc1Neg()
        pos = pos + Match.end()
    while 1:
        i = MatchStr(arg[pos:],"(")
        if i:
            pos = pos + i
            try:
                MathTree(arg, pos)
                raise "Braket expected"
            except "Braket", (i, SubTree):
                pos = i
                if isinstance(SubTree, MTOp):
                    SubTree.BraketBarrier = 1
                if Tree:
                    Tree.AddArg(SubTree)
                else:
                    Tree = SubTree
        else:
            for Func in (MTFunc1Neg(), MTFunc1Sqrt(), MTFunc1Exp(),\
                         MTFunc1Log(), MTFunc1Sin(), MTFunc1Cos(),\
                         MTFunc1Tan(), MTFunc1ArcSin(), MTFunc1ArcCos(),\
                         MTFunc1ArcTan(), MTFunc2Norm()):
                i = Func.InitByMatch(arg[pos:])
                if i:
                    if Tree:
                        Tree.AddArg(Func)
                    else:
                        Tree = Func
                    pos = pos + i
                    for i in range(Func.ArgC - 1):
                        try:
                            MathTree(arg, pos)
                            raise "Komma expected"
                        except "Komma", (i, SubTree):
                            pos = i
                            Func.AddArg(SubTree)
                    try:
                        MathTree(arg, pos)
                        raise "Braket expected"
                    except "Braket", (i, SubTree):
                        pos = i
                        Func.AddArg(SubTree)
                    break
            else:
                for Val in (MTValConst(), MTValVar()):
                    i = Val.InitByMatch(arg[pos:])
                    if i:
                        pos = pos + i
                        if Tree:
                            Tree.AddArg(Val)
                        else:
                            Tree = Val
                        break
                else:
                    raise "operand expected"
        if pos + HeadWhiteSpace(arg[pos:]) == len(arg):
            return Tree
        i = MatchStr(arg[pos:], ")")
        if i:
            raise "Braket", (pos + i, Tree)
        i = MatchStr(arg[pos:], ",")
        if i:
            raise "Komma", (pos + i, Tree)
        for Op in (MTOpPow(), MTOpDiv(), MTOpMul(), MTOpSub(), MTOpAdd()):
            i = Op.InitByMatch(arg[pos:])
            if i:
                pos = pos + i
                SubTree = Tree
                SubTreeRoot = None
                while isinstance(SubTree, MTOp) and\
                      Op.Level > SubTree.Level and\
                      not SubTree.BraketBarrier:
                    SubTreeRoot = SubTree
                    SubTree = SubTree.ArgV[1]
                if SubTreeRoot:
                    Op.AddArg(SubTree)
                    SubTreeRoot.ArgV[1] = Op
                else:
                    Op.AddArg(Tree)
                    Tree = Op
                break
        else:
            raise "operator expected"


if __name__=="__main__":
    print "fit.py 0.0.1 test program"
    choise = "5"
    while choise != "6":
        if choise == "5":
            expression = raw_input("\nexpression? ")
            mytree=MathTree(expression)
        choise = "0"
        while choise not in map(lambda x: chr(x + ord("1")), range(6)):
            choise = raw_input("\n1) view expression\
                                \n2) view math tree\
                                \n3) view list of variables\
                                \n4) calulate derivative\
                                \n5) enter new expression\
                                \n6) quit\
                                \nyour choise? ")
        if choise == "1":
            print "\n", mytree
        if choise == "2":
            print "\n", repr(mytree)
        if choise == "3":
            print "\n",mytree.VarList()
        if choise == "4":
            varname = raw_input("\nwhich variable? ")
            if varname != "":
                mytree = mytree.Derivative(varname)
                print "\nexpression replaced by the calculated derivative"
            else:
                print "\nstring was empty, go back to main menu"
