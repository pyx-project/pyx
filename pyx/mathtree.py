import string
import re
import math


class ParseStr:

    def __init__(self, StrToParse, Pos = 0):
        self.StrToParse = StrToParse
        self.Pos = Pos

    def __repr__(self):
        return "ParseStr(\"" + self.StrToParse + "\", " + str(self.Pos) + ")"

    def __str__(self, Indent = ""):
        WhiteSpaces = ""
        for i in range(self.NextNonWhiteSpace()):
            WhiteSpaces = WhiteSpaces + " "
        return Indent + self.StrToParse + "\n" + Indent + WhiteSpaces + "^"

    def NextNonWhiteSpace(self, i = None):
        if i == None:
            i = self.Pos
        while (len(self.StrToParse) > i) and \
              (self.StrToParse[i] in string.whitespace):
            i = i + 1
        return i

    def MatchStr(self, Str):
        i = self.NextNonWhiteSpace()
        if (len(self.StrToParse) >= i + len(Str)) and \
           (self.StrToParse[i: i + len(Str)] == Str):
            self.Pos = i + len(Str)
            return Str
        return None

    def MatchStrBracket(self, Str):
        i = self.NextNonWhiteSpace()
        if (len(self.StrToParse) >= i + len(Str)) and \
           (self.StrToParse[i: i + len(Str)] == Str):
            i = i + len(Str)
            i = self.NextNonWhiteSpace(i)
            if (len(self.StrToParse) >= i + 1) and \
               (self.StrToParse[i: i + 1] == "("):
                return Str
        return None

    def MatchPattern(self, Pat):
        i = self.NextNonWhiteSpace()
        Match = Pat.match(self.StrToParse[i:])
        if Match:
            self.Pos = i + Match.end()
            return Match.group()
        return None

    def AllDone(self, i = None):
        if i == None:
            i = self.Pos
        while (len(self.StrToParse) > i) and \
              (self.StrToParse[i] in string.whitespace):
            i = i + 1
        return len(self.StrToParse) == i


# LeftParenthesis
# RightParenthesis

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
            newlist = Arg.VarList()
            for x in newlist:
                if x not in list:
                    list.append(x)
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
        Match = arg.MatchPattern(ConstPattern)
        if Match:
            self.Const =  string.atof(Match)
            return 1

    def CalcDerivative(self, arg):
        assert 0, "expression doesn't depend on " + arg

    def Calc(self, VarDict):
        return self.Const


VarPattern = re.compile(r"[a-z][a-z0-9_]*", re.IGNORECASE)
MathConst = { "pi": math.pi, "e": math.e }

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
        Match = arg.MatchPattern(VarPattern)
        if Match:
            self.Var = Match
            return 1

    def CalcDerivative(self, arg):
        if arg != self.Var:
            assert 0, "expression doesn't depend on " + arg
        return MTValConst().Init(1.0)

    def DependOn(self,arg):
        if arg == self.Var:
            return 1
        return 0

    def VarList(self):
        if self.Var in MathConst.keys():
            return [ ]
        return [self.Var, ]

    def Calc(self, VarDict):
        if self.Var in MathConst.keys():
            return MathConst[self.Var]
        return VarDict[self.Var]


class MTFunc(MT):

    pass


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
        return arg.MatchStrBracket("neg")

    def CalcDerivative(self, arg):
        return MTFunc1Neg().Init(self.ArgV[0].CalcDerivative(arg))

    def Calc(self, VarDict):
        return -self.ArgV[0].Calc(VarDict)


class MTFunc1Sgn(MTFunc1):

    def __str__(self):
        return "sgn(" + self.ArgV[0].__str__() + ")"

    def InitByMatch(self, arg):
        return self.InitByMatchStr(arg, "sgn")

    def CalcDerivative(self, arg):
        return MTValConst().Init(0.0)

    def Calc(self, VarDict):
        if self.ArgV[0].Calc(VarDict) < 0:
            return -1.0
        return 1.0


class MTFunc1Sqrt(MTFunc1):

    def __str__(self):
        return "sqrt(" + self.ArgV[0].__str__() + ")"

    def InitByMatch(self, arg):
        return arg.MatchStrBracket("sqrt")

    def CalcDerivative(self, arg):
        return MTOpMul().Init(
                   MTOpDiv().Init(
                       MTValConst().Init(0.5),
                       self),
                   self.ArgV[0].CalcDerivative(arg))

    def Calc(self, VarDict):
        return math.sqrt(self.ArgV[0].Calc(VarDict))


class MTFunc1Exp(MTFunc1):

    def __str__(self):
        return "exp(" + self.ArgV[0].__str__() + ")"

    def InitByMatch(self, arg):
        return arg.MatchStrBracket("exp")

    def CalcDerivative(self, arg):
        return MTOpMul().Init(self, self.ArgV[0].CalcDerivative(arg))

    def Calc(self, VarDict):
        return math.exp(self.ArgV[0].Calc(VarDict))


class MTFunc1Log(MTFunc1):

    def __str__(self):
        return "log(" + self.ArgV[0].__str__() + ")"

    def InitByMatch(self, arg):
        return arg.MatchStrBracket("log")

    def CalcDerivative(self, arg):
        return MTOpDiv().Init(self.ArgV[0].CalcDerivative(arg), self.ArgV[0])

    def Calc(self, VarDict):
        return math.log(self.ArgV[0].Calc(VarDict))


class MTFunc1Sin(MTFunc1):

    def __str__(self):
        return "sin(" + self.ArgV[0].__str__() + ")"

    def InitByMatch(self, arg):
        return arg.MatchStrBracket("sin")

    def CalcDerivative(self, arg):
        return MTOpMul().Init(
                   MTFunc1Cos().Init(self.ArgV[0]),
                   self.ArgV[0].CalcDerivative(arg))

    def Calc(self, VarDict):
        return math.sin(self.ArgV[0].Calc(VarDict))


class MTFunc1Cos(MTFunc1):

    def __str__(self):
        return "cos(" + self.ArgV[0].__str__() + ")"

    def InitByMatch(self, arg):
        return arg.MatchStrBracket("cos")

    def CalcDerivative(self, arg):
        return MTOpMul().Init(
                   MTFunc1Neg().Init(MTFunc1Sin().Init(self.ArgV[0])),
                   self.ArgV[0].CalcDerivative(arg))

    def Calc(self, VarDict):
        return math.cos(self.ArgV[0].Calc(VarDict))


class MTFunc1Tan(MTFunc1):

    def __str__(self):
        return "tan(" + self.ArgV[0].__str__() + ")"

    def InitByMatch(self, arg):
        return arg.MatchStrBracket("tan")

    def CalcDerivative(self, arg):
        return MTOpDiv().Init(
                   self.ArgV[0].CalcDerivative(arg),
                   MTOpPow().Init(
                       MTFunc1Cos().Init(self.ArgV[0]),
                       MTValConst().Init(2.0)))

    def Calc(self, VarDict):
        return math.tan(self.ArgV[0].Calc(VarDict))


class MTFunc1ASin(MTFunc1):

    def __str__(self):
        return "asin(" + self.ArgV[0].__str__() + ")"

    def InitByMatch(self, arg):
        return arg.MatchStrBracket("asin")

    def CalcDerivative(self, arg):
        return MTOpDiv().Init(
                   self.ArgV[0].CalcDerivative(arg),
                   MTFunc1Sqrt().Init(
                       MTOpSub().Init(
                           MTValConst().Init(1.0),
                           MTOpPow().Init(
                               self.ArgV[0],
                               MTValConst().Init(2.0)))))

    def Calc(self, VarDict):
        return math.asin(self.ArgV[0].Calc(VarDict))


class MTFunc1ACos(MTFunc1):

    def __str__(self):
        return "acos(" + self.ArgV[0].__str__() + ")"

    def InitByMatch(self, arg):
        return arg.MatchStrBracket("acos")

    def CalcDerivate(self, arg):
        return MTOpDiv().Init(
                   MTFunc1Neg().Init(self.ArgV[0].CalcDerivative(arg)),
                   MTFunc1Sqrt().Init(
                       MTOpSub().Init(
                           MTValConst().Init(1.0),
                           MTOpPow().Init(
                               self.ArgV[0],
                               MTValConst().Init(2.0)))))

    def Calc(self, VarDict):
        return math.acos(self.ArgV[0].Calc(VarDict))


class MTFunc1ATan(MTFunc1):

    def __str__(self):
        return "atan(" + self.ArgV[0].__str__() + ")"

    def InitByMatch(self, arg):
        return arg.MatchStrBracket("atan")

    def CalcDerivate(self, arg):
        return MTOpDiv().Init(
                   self.ArgV[0].CalcDerivative(arg),
                   MTOpAdd().Init(
                       MTValConst().Init(1.0),
                       MTOpPow().Init(
                           self.ArgV[0],
                           MTValConst().Init(2.0))))

    def Calc(self, VarDict):
        return math.atan(self.ArgV[0].Calc(VarDict))


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
        return arg.MatchStrBracket("norm")

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

    def Calc(self, VarDict):
        return math.sqrt(self.ArgV[0].Calc(VarDict) ** 2 +
                         self.ArgV[1].Calc(VarDict) ** 2)


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


class MTOpAdd(MTOp):

    def __init__(self):
        MTOp.__init__(self, 1)

    def __str__(self):
        return MTOp.__str__(self, "+")

    def InitByMatch(self, arg):
        return arg.MatchStr("+")

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

    def Calc(self, VarDict):
        return self.ArgV[0].Calc(VarDict) + self.ArgV[1].Calc(VarDict)


class MTOpSub(MTOp):

    def __init__(self):
        MTOp.__init__(self, 1)

    def __str__(self):
        return MTOp.__str__(self, "-")
        
    def InitByMatch(self, arg):
        return arg.MatchStr("-")

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

    def Calc(self, VarDict):
        return self.ArgV[0].Calc(VarDict) - self.ArgV[1].Calc(VarDict)


class MTOpMul(MTOp):

    def __init__(self):
        MTOp.__init__(self, 2)

    def __str__(self):
        return MTOp.__str__(self, "*")

    def InitByMatch(self, arg):
        return arg.MatchStr("*")

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

    def Calc(self, VarDict):
        return self.ArgV[0].Calc(VarDict) * self.ArgV[1].Calc(VarDict)


class MTOpDiv(MTOp):

    def __init__(self):
        MTOp.__init__(self, 2)

    def __str__(self):
        return MTOp.__str__(self, "/")

    def InitByMatch(self, arg):
        return arg.MatchStr("/")

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

    def Calc(self, VarDict):
        return self.ArgV[0].Calc(VarDict) / self.ArgV[1].Calc(VarDict)


class MTOpPow(MTOp):

    def __init__(self):
        MTOp.__init__(self, 3)

    def __str__(self):
        return MTOp.__str__(self, "^")

    def InitByMatch(self, arg):
        pos = arg.MatchStr("^")
        if pos:
            return 1
        else:
            return arg.MatchStr("**")

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

    def Calc(self, VarDict):
        return self.ArgV[0].Calc(VarDict) ** self.ArgV[1].Calc(VarDict)


NegPattern = re.compile(r"\s*-(?![0-9\.])")

def MathTree(arg):
    Tree = None
    Match = arg.MatchPattern(NegPattern)
    if Match:
        Tree = MTFunc1Neg()
    while 1:
        i = arg.MatchStr("(")
        if i:
            try:
                MathTree(arg)
                raise "Braket expected"
            except "Braket", SubTree:
                if isinstance(SubTree, MTOp):
                    SubTree.BraketBarrier = 1
                if Tree:
                    Tree.AddArg(SubTree)
                else:
                    Tree = SubTree
        else:
            for Func in (MTFunc1Neg(), MTFunc1Sqrt(), MTFunc1Exp(),\
                         MTFunc1Log(), MTFunc1Sin(), MTFunc1Cos(),\
                         MTFunc1Tan(), MTFunc1ASin(), MTFunc1ACos(),\
                         MTFunc1ATan(), MTFunc2Norm()):
                i = Func.InitByMatch(arg)
                if i:
                    if Tree:
                        Tree.AddArg(Func)
                    else:
                        Tree = Func
                    for i in range(Func.ArgC - 1):
                        try:
                            MathTree(arg)
                            raise "Komma expected"
                        except "Komma", (i, SubTree):
                            Func.AddArg(SubTree)
                    try:
                        MathTree(arg)
                        raise "Braket expected"
                    except "Braket", (i, SubTree):
                        Func.AddArg(SubTree)
                    break
            else:
                for Val in (MTValConst(), MTValVar()):
                    i = Val.InitByMatch(arg)
                    if i:
                        if Tree:
                            Tree.AddArg(Val)
                        else:
                            Tree = Val
                        break
                else:
                    raise "operand expected"
        if arg.AllDone():
            return Tree
        i = arg.MatchStr(")")
        if i:
            raise "Braket", Tree
        i = arg.MatchStr(",")
        if i:
            raise "Komma", Tree
        for Op in (MTOpPow(), MTOpDiv(), MTOpMul(), MTOpSub(), MTOpAdd()):
            i = Op.InitByMatch(arg)
            if i:
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
    print "fit.py test program"
    choise = "6"
    while choise != "7":
        if choise == "6":
            expression = raw_input("\nexpression? ")
            mytree=MathTree(ParseStr(expression))
        choise = "0"
        while choise not in map(lambda x: chr(x + ord("1")), range(7)):
            choise = raw_input("\n1) view expression\
                                \n2) view math tree\
                                \n3) view list of variables\
                                \n4) calculate expression\
                                \n5) calculate derivative\
                                \n6) enter new expression\
                                \n7) quit\
                                \nyour choise? ")
        if choise == "1":
            print "\n", mytree
        if choise == "2":
            print "\n", repr(mytree)
        if choise == "3":
            print "\n", mytree.VarList()
        if choise == "4":
            print
            VarDict = { }
            for key in mytree.VarList():
                VarDict[key] = float(raw_input("value for \"" + key + "\"? "))
            print "\nthe result is ",mytree.Calc(VarDict)
        if choise == "5":
            varname = raw_input("\nwhich variable? ")
            if varname != "":
                mytree = mytree.Derivative(varname)
                print "\nexpression replaced by the calculated derivative"
            else:
                print "\nstring was empty, go back to main menu"
