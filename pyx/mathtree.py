#!/usr/bin/env python
#
#
# Copyright (C) 2002 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2002 André Wobst <wobsta@users.sourceforge.net>
#
# This file is part of PyX (http://pyx.sourceforge.net/).
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


import string, re, math, types


class ParseStr:
    "parser based on a string"

    def __init__(self, StrToParse, Pos = 0):
        self.StrToParse = StrToParse
        self.Pos = Pos

    def __repr__(self):
        return "ParseStr('" + self.StrToParse + "', " + str(self.Pos) + ")"

    def __str__(self, Indent = ""):
        WhiteSpaces = ""
        for i in range(self.Pos):
            WhiteSpaces = WhiteSpaces + " "
        return Indent + self.StrToParse + "\n" + Indent + WhiteSpaces + "^"

    def NextNonWhiteSpace(self, i = None):
        if i == None:
            i = self.Pos
        while self.StrToParse[i] in string.whitespace:
            i = i + 1
        return i

    def MatchStr(self, Str):
        try:
            i = self.NextNonWhiteSpace()
            if self.StrToParse[i: i + len(Str)] == Str:
                self.Pos = i + len(Str)
                return Str
        except IndexError:
            pass

    def MatchStrParenthesis(self, Str):
        try:
            i = self.NextNonWhiteSpace()
            if self.StrToParse[i: i + len(Str)] == Str:
                i = i + len(Str)
                i = self.NextNonWhiteSpace(i)
                if self.StrToParse[i: i + 1] == "(":
                    self.Pos = i + 1
                    return Str
        except IndexError:
            pass

    def MatchPattern(self, Pat):
        try:
            i = self.NextNonWhiteSpace()
            Match = Pat.match(self.StrToParse[i:])
            if Match:
                self.Pos = i + Match.end()
                return Match.group()
        except IndexError:
            pass

    def AllDone(self):
        try:
            self.NextNonWhiteSpace()
        except IndexError:
            return 1
        return 0


class MathTree:

    def __init__(self, *args):
        self.ArgC = 0
        self.ArgV = list(args)

    def __repr__(self, depth = 0):
        assert len(self.ArgV) == self.ArgC, "wrong number of arguments"
        indent = ""
        SingleIndent = "    "
        for i in range(depth):
            indent = indent + SingleIndent
        result = indent + self.__class__.__name__ + "(\n"
        for SubTree in self.ArgV:
            if isinstance(SubTree, MathTree):
                result = result + SubTree.__repr__(depth + 1)
            else:
                result = result + indent + SingleIndent + repr(SubTree)
            
            if SubTree != self.ArgV[-1]:
                result = result + ",\n"
            else:
                result = result + ")"
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
            return MathTreeValConst(0.0)
        return self.CalcDerivative(arg)

    def VarList(self):
        list = [ ]
        for Arg in self.ArgV:
            newlist = Arg.VarList()
            for x in newlist:
                if x not in list:
                    list.append(x)
        return list


class MathTreeVal(MathTree):

    def __init__(self, *args):
        MathTree.__init__(self, *args)
        self.ArgC = 1

    def __str__(self):
        return str(self.ArgV[0])


ConstPattern = re.compile(r"-?\d*((\d\.?)|(\.?\d))\d*(E[+-]?\d+)?",
                          re.IGNORECASE)

class MathTreeValConst(MathTreeVal):

    def InitByParser(self, arg):
        Match = arg.MatchPattern(ConstPattern)
        if Match:
            self.AddArg(string.atof(Match))
            return 1

    def CalcDerivative(self, arg):
        assert 0, "expression doesn't depend on " + arg

    def Derivative(self, arg):
        return MathTreeValConst(0.0)

    def VarList(self):
        return [ ]

    def Calc(self, VarDict, Points):
        return self.ArgV[0]


VarPattern = re.compile(r"[a-z][a-z0-9_]*", re.IGNORECASE)
MathConst = { "pi": math.pi, "e": math.e }

class MathTreeValVar(MathTreeVal):

    def InitByParser(self, arg):
        Match = arg.MatchPattern(VarPattern)
        if Match:
            self.AddArg(Match)
            return 1

    def CalcDerivative(self, arg):
        if arg != self.ArgV[0]:
            assert 0, "expression doesn't depend on " + arg
        return MathTreeValConst(1.0)

    def DependOn(self,arg):
        if arg == self.ArgV[0]:
            return 1
        return 0

    def VarList(self):
        if self.ArgV[0] in MathConst.keys():
            return [ ]
        return [self.ArgV[0], ]

    def Calc(self, VarDict, Points):
        if self.ArgV[0] in MathConst.keys():
            return MathConst[self.ArgV[0]]
        Values = VarDict[self.ArgV[0]]
        if type(Values) in (types.IntType, types.LongType, types.FloatType, ):
            return Values
        else:
            return Values[Points]


class MathTreeFunc(MathTree):

    def __init__(self, name, *args):
        MathTree.__init__(self, *args)
        self.name = name

    def InitByParser(self, arg):
        return arg.MatchStrParenthesis(self.name)

    def __str__(self):
        args = ""
        for SubTree in self.ArgV:
            args = args + str(SubTree)
            if SubTree != self.ArgV[-1]:
                args = args + ","
        return self.name + "(" + args + ")"

MathTreeFuncList = ( )


class MathTreeFunc1(MathTreeFunc):

    def __init__(self, name, *args):
        MathTreeFunc.__init__(self, name, *args)
        self.ArgC = 1


class MathTreeFunc1Neg(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "neg", *args)

    def CalcDerivative(self, arg):
        return MathTreeFunc1Neg(self.ArgV[0].CalcDerivative(arg))

    def Calc(self, VarDict, Points):
        return -self.ArgV[0].Calc(VarDict, Points)

MathTreeFuncList = MathTreeFuncList + (MathTreeFunc1Neg, )


class MathTreeFunc1Sgn(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "sgn", *args)

    def CalcDerivative(self, arg):
        return MathTreeValConst(0.0)

    def Calc(self, VarDict, Points):
        if self.ArgV[0].Calc(VarDict, Points) < 0:
            return -1.0
        return 1.0

MathTreeFuncList = MathTreeFuncList + (MathTreeFunc1Sgn, )


class MathTreeFunc1Sqrt(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "sqrt", *args)

    def CalcDerivative(self, arg):
        return MathTreeOpMul(
                   MathTreeOpDiv(
                       MathTreeValConst(0.5),
                       self),
                   self.ArgV[0].CalcDerivative(arg))

    def Calc(self, VarDict, Points):
        return math.sqrt(self.ArgV[0].Calc(VarDict, Points))

MathTreeFuncList = MathTreeFuncList + (MathTreeFunc1Sqrt, )


class MathTreeFunc1Exp(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "exp", *args)

    def CalcDerivative(self, arg):
        return MathTreeOpMul(self, self.ArgV[0].CalcDerivative(arg))

    def Calc(self, VarDict, Points):
        return math.exp(self.ArgV[0].Calc(VarDict, Points))

MathTreeFuncList = MathTreeFuncList + (MathTreeFunc1Exp, )


class MathTreeFunc1Log(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "log", *args)

    def CalcDerivative(self, arg):
        return MathTreeOpDiv(self.ArgV[0].CalcDerivative(arg), self.ArgV[0])

    def Calc(self, VarDict, Points):
        return math.log(self.ArgV[0].Calc(VarDict, Points))

MathTreeFuncList = MathTreeFuncList + (MathTreeFunc1Log, )


class MathTreeFunc1Sin(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "sin", *args)

    def CalcDerivative(self, arg):
        return MathTreeOpMul(
                   MathTreeFunc1Cos(self.ArgV[0]),
                   self.ArgV[0].CalcDerivative(arg))

    def Calc(self, VarDict, Points):
        return math.sin(self.ArgV[0].Calc(VarDict, Points))

MathTreeFuncList = MathTreeFuncList + (MathTreeFunc1Sin, )


class MathTreeFunc1Cos(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "cos", *args)

    def CalcDerivative(self, arg):
        return MathTreeOpMul(
                   MathTreeFunc1Neg(MathTreeFunc1Sin(self.ArgV[0])),
                   self.ArgV[0].CalcDerivative(arg))

    def Calc(self, VarDict, Points):
        return math.cos(self.ArgV[0].Calc(VarDict, Points))

MathTreeFuncList = MathTreeFuncList + (MathTreeFunc1Cos, )


class MathTreeFunc1Tan(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "tan", *args)

    def CalcDerivative(self, arg):
        return MathTreeOpDiv(
                   self.ArgV[0].CalcDerivative(arg),
                   MathTreeOpPow(
                       MathTreeFunc1Cos(self.ArgV[0]),
                       MathTreeValConst(2.0)))

    def Calc(self, VarDict, Points):
        return math.tan(self.ArgV[0].Calc(VarDict, Points))

MathTreeFuncList = MathTreeFuncList + (MathTreeFunc1Tan, )


class MathTreeFunc1ASin(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "asin", *args)

    def CalcDerivative(self, arg):
        return MathTreeOpDiv(
                   self.ArgV[0].CalcDerivative(arg),
                   MathTreeFunc1Sqrt(
                       MathTreeOpSub(
                           MathTreeValConst(1.0),
                           MathTreeOpPow(
                               self.ArgV[0],
                               MathTreeValConst(2.0)))))

    def Calc(self, VarDict, Points):
        return math.asin(self.ArgV[0].Calc(VarDict, Points))

MathTreeFuncList = MathTreeFuncList + (MathTreeFunc1ASin, )


class MathTreeFunc1ACos(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "acos", *args)

    def CalcDerivate(self, arg):
        return MathTreeOpDiv(
                   MathTreeFunc1Neg(self.ArgV[0].CalcDerivative(arg)),
                   MathTreeFunc1Sqrt(
                       MathTreeOpSub(
                           MathTreeValConst(1.0),
                           MathTreeOpPow(
                               self.ArgV[0],
                               MathTreeValConst(2.0)))))

    def Calc(self, VarDict, Points):
        return math.acos(self.ArgV[0].Calc(VarDict, Points))

MathTreeFuncList = MathTreeFuncList + (MathTreeFunc1ACos, )


class MathTreeFunc1ATan(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "atan", *args)

    def CalcDerivate(self, arg):
        return MathTreeOpDiv(
                   self.ArgV[0].CalcDerivative(arg),
                   MathTreeOpAdd(
                       MathTreeValConst(1.0),
                       MathTreeOpPow(
                           self.ArgV[0],
                           MathTreeValConst(2.0))))

    def Calc(self, VarDict, Points):
        return math.atan(self.ArgV[0].Calc(VarDict, Points))

MathTreeFuncList = MathTreeFuncList + (MathTreeFunc1ATan, )


class MathTreeFunc2(MathTreeFunc):

    def __init__(self, name, *args):
        MathTreeFunc.__init__(self, name, *args)
        self.ArgC = 2


class MathTreeFunc2Norm(MathTreeFunc2):

    def __init__(self, *args):
        MathTreeFunc2.__init__(self, "norm", *args)

    def CalcDerivative(self, arg):
        if self.ArgV[0].DependOn(arg):
            if self.ArgV[1].DependOn(arg):
                return MathTreeOpDiv(
                           MathTreeOpAdd(
                               MathTreeOpMul(
                                   self.ArgV[0],
                                   self.ArgV[0].CalcDerivative(arg)),
                               MathTreeOpMul(
                                   self.ArgV[1],
                                   self.ArgV[1].CalcDerivative(arg))),
                           self)
            else:
                return MathTreeOpDiv(
                           MathTreeOpMul(
                               self.ArgV[0],
                               self.ArgV[0].CalcDerivative(arg)),
                           self)
        else:
            if self.ArgV[1].DependOn(arg):
                return MathTreeOpDiv(
                           MathTreeOpMul(
                               self.ArgV[1],
                               self.ArgV[1].CalcDerivative(arg)),
                           self)

    def Calc(self, VarDict, Points):
        return math.sqrt(self.ArgV[0].Calc(VarDict, Points) ** 2 +
                         self.ArgV[1].Calc(VarDict, Points) ** 2)

MathTreeFuncList = MathTreeFuncList + (MathTreeFunc2Norm, )


class MathTreeOp(MathTree):

    def __init__(self, level, symbol, *args):
        MathTree.__init__(self, *args)
        self.ArgC = 2
        self.ParenthesisBarrier = 0
        self.level = level
        self.symbol = symbol

    def __str__(self):
        result = ""
        if isinstance(self.ArgV[0], MathTreeOp) and\
            self.level > self.ArgV[0].level:
            result = result + "(" + str(self.ArgV[0]) + ")"
        else:
            result = result + str(self.ArgV[0])
        result = result + self.symbol
        if isinstance(self.ArgV[1], MathTreeOp) and\
            self.level >= self.ArgV[1].level:
            result = result + "(" + str(self.ArgV[1]) + ")"
        else:
            result = result + str(self.ArgV[1])
        return result

    def InitByParser(self, arg):
        return arg.MatchStr(self.symbol)


class MathTreeOpAdd(MathTreeOp):

    def __init__(self, *args):
        MathTreeOp.__init__(self, 1, "+", *args)

    def CalcDerivative(self, arg):
        if self.ArgV[0].DependOn(arg):
            if self.ArgV[1].DependOn(arg):
                return MathTreeOpAdd(
                           self.ArgV[0].CalcDerivative(arg),
                           self.ArgV[1].CalcDerivative(arg))
            else:
                return self.ArgV[0].CalcDerivative(arg)
        else:
            if self.ArgV[1].DependOn(arg):
                return self.ArgV[1].CalcDerivative(arg)

    def Calc(self, VarDict, Points):
        return self.ArgV[0].Calc(VarDict, Points) + self.ArgV[1].Calc(VarDict, Points)


class MathTreeOpSub(MathTreeOp):

    def __init__(self, *args):
        MathTreeOp.__init__(self, 1, "-", *args)

    def CalcDerivative(self, arg):
        if self.ArgV[0].DependOn(arg):
            if self.ArgV[1].DependOn(arg):
                return MathTreeOpSub(
                           self.ArgV[0].CalcDerivative(arg),
                           self.ArgV[1].CalcDerivative(arg))
            else:
                return self.ArgV[0].CalcDerivative(arg)
        else:
            if self.ArgV[1].DependOn(arg):
                return MathTreeFunc1Neg(self.ArgV[1].CalcDerivative(arg))

    def Calc(self, VarDict, Points):
        return self.ArgV[0].Calc(VarDict, Points) - self.ArgV[1].Calc(VarDict, Points)


class MathTreeOpMul(MathTreeOp):

    def __init__(self, *args):
        MathTreeOp.__init__(self, 2, "*", *args)

    def CalcDerivative(self, arg):
        if self.ArgV[0].DependOn(arg):
            if self.ArgV[1].DependOn(arg):
                return MathTreeOpAdd(
                           MathTreeOpMul(
                               self.ArgV[0],
                               self.ArgV[1].CalcDerivative(arg)),
                           MathTreeOpMul(
                               self.ArgV[0].CalcDerivative(arg),
                               self.ArgV[1]))
            else:
                return MathTreeOpMul(
                           self.ArgV[0].CalcDerivative(arg),
                           self.ArgV[1])
        else:
            if self.ArgV[1].DependOn(arg):
                return MathTreeOpMul(
                           self.ArgV[0],
                           self.ArgV[1].CalcDerivative(arg))

    def Calc(self, VarDict, Points):
        return self.ArgV[0].Calc(VarDict, Points) * self.ArgV[1].Calc(VarDict, Points)


class MathTreeOpDiv(MathTreeOp):

    def __init__(self, *args):
        MathTreeOp.__init__(self, 2, "/", *args)

    def CalcDerivative(self, arg):
        if self.ArgV[0].DependOn(arg):
            if self.ArgV[1].DependOn(arg):
                return MathTreeOpMul(
                           MathTreeOpSub(
                               MathTreeOpMul(
                                   self.ArgV[0].CalcDerivative(arg),
                                   self.ArgV[1]),
                               MathTreeOpMul(
                                   self.ArgV[0],
                                   self.ArgV[1].CalcDerivative(arg))),
                           MathTreeOpPow(
                               self.ArgV[1],
                               MathTreeValConst(-2.0)))
            else:
                return MathTreeOpDiv(
                           self.ArgV[0].CalcDerivative(arg),
                           self.ArgV[1])
        else:
            if self.ArgV[1].DependOn(arg):
                return MathTreeOpMul(
                           MathTreeOpMul(
                               MathTreeFunc1Neg(self.ArgV[0]),
                               MathTreeOpPow(
                                   self.ArgV[1],
                                   MathTreeValConst(-2.0))),
                           self.ArgV[1].CalcDerivative(arg))

    def Calc(self, VarDict, Points):
        return self.ArgV[0].Calc(VarDict, Points) / self.ArgV[1].Calc(VarDict, Points)


class MathTreeOpPow(MathTreeOp):

    def __init__(self, *args):
        MathTreeOp.__init__(self, 3, "^", *args)

    def InitByParser(self, arg):
        pos = arg.MatchStr("^")
        if pos:
            return 1
        else:
            return arg.MatchStr("**")

    def CalcDerivative(self, arg):
        if self.ArgV[0].DependOn(arg):
            if self.ArgV[1].DependOn(arg):
                return MathTreeOpMul(
                           MathTreeOpPow(
                               self.ArgV[0],
                               self.ArgV[1]),
                           MathTreeOpAdd(
                               MathTreeOpMul(
                                   MathTreeFunc1Log(self.ArgV[0]),
                                   self.ArgV[1].CalcDerivative(arg)),
                               MathTreeOpMul(
                                   self.ArgV[1],
                                   MathTreeOpDiv(
                                       self.ArgV[0].CalcDerivative(arg),
                                       self.ArgV[0]))))
            else:
                return MathTreeOpMul(
                           self.ArgV[1],
                           MathTreeOpMul(
                               MathTreeOpPow(
                                   self.ArgV[0],
                                   MathTreeOpSub(
                                       self.ArgV[1],
                                       MathTreeValConst(1.0))),
                               self.ArgV[0].CalcDerivative(arg)))
        else:
            if self.ArgV[1].DependOn(arg):
                return MathTreeOpMul(
                           MathTreeOpMul(
                               MathTreeOpPow(
                                   self.ArgV[0],
                                   self.ArgV[1]),
                               MathTreeFunc1Log(self.ArgV[0])),
                           self.ArgV[1].CalcDerivative(arg))

    def Calc(self, VarDict, Points):
        return self.ArgV[0].Calc(VarDict, Points) ** self.ArgV[1].Calc(VarDict, Points)

MathTreeOpList = (MathTreeOpPow, MathTreeOpDiv, MathTreeOpMul, MathTreeOpSub, MathTreeOpAdd)


class UndefinedMathTreeParseError(Exception):
    
    def __init__(self, ParseStr, MathTree):
        self.ParseStr = ParseStr
        self.MathTree = MathTree
    def __str__(self):
        return "\n" + str(self.ParseStr)

class RightParenthesisExpectedMathTreeParseError(UndefinedMathTreeParseError):
    pass

class RightParenthesisFoundMathTreeParseError(UndefinedMathTreeParseError):
    pass

class CommaExpectedMathTreeParseError(UndefinedMathTreeParseError):
    pass

class CommaFoundMathTreeParseError(UndefinedMathTreeParseError):
    pass

class OperatorExpectedMathTreeParseError(UndefinedMathTreeParseError):
    pass

class OperandExpectedMathTreeParseError(UndefinedMathTreeParseError):
    pass


NegPattern = re.compile(r"\s*-(?![0-9\.])")

def ParseMathTree(arg):
    Tree = None
    Match = arg.MatchPattern(NegPattern)
    if Match:
        Tree = MathTreeFunc1Neg()
    while 1:
        i = arg.MatchStr("(")
        if i:
            try:
                ParseMathTree(arg)
                raise RightParenthesisExpectedMathTreeParseError(arg, Tree)
            except RightParenthesisFoundMathTreeParseError, e:
                if isinstance(e.MathTree, MathTreeOp):
                    e.MathTree.ParenthesisBarrier = 1
                if Tree:
                    Tree.AddArg(e.MathTree)
                else:
                    Tree = e.MathTree
        else:
            for FuncClass in MathTreeFuncList:
                Func = FuncClass()
                if Func.InitByParser(arg):
                    if Tree:
                        Tree.AddArg(Func)
                    else:
                        Tree = Func
                    for i in range(Func.ArgC - 1):
                        try:
                            ParseMathTree(arg)
                            raise CommaExpectedMathTreeParseError(arg, Tree)
                        except CommaFoundMathTreeParseError, e:
                            Func.AddArg(e.MathTree)
                    try:
                        ParseMathTree(arg)
                        raise RightParenthesisExpectedMathTreeParseError(arg, Tree)
                    except RightParenthesisFoundMathTreeParseError, e:
                        Func.AddArg(e.MathTree)
                    break
            else:
                for Val in (MathTreeValConst(), MathTreeValVar()):
                    i = Val.InitByParser(arg)
                    if i:
                        if Tree:
                            Tree.AddArg(Val)
                        else:
                            Tree = Val
                        break
                else:
                    raise OperandExpectedMathTreeParseError(arg, Tree)
        if arg.AllDone():
            return Tree
        i = arg.MatchStr(")")
        if i:
            raise RightParenthesisFoundMathTreeParseError(arg, Tree)
        i = arg.MatchStr(",")
        if i:
            raise CommaFoundMathTreeParseError(arg, Tree)
        for OpClass in MathTreeOpList:
            Op = OpClass()
            if Op.InitByParser(arg):
                SubTree = Tree
                SubTreeRoot = None
                while isinstance(SubTree, MathTreeOp) and\
                      Op.level > SubTree.level and\
                      not SubTree.ParenthesisBarrier:
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
            raise OperatorExpectedMathTreeParseError(arg, Tree)


if __name__=="__main__":
    print ParseMathTree(ParseStr("a+b-c*d/e**f"))
    print ParseMathTree(ParseStr("a**b/c*d-e+f"))
    print ParseMathTree(ParseStr("a+b-c"))
    print ParseMathTree(ParseStr("(a+b)-c"))
    print ParseMathTree(ParseStr("a+(b-c)")), " <= this is somehow wrong (needs no parenthesis)"
    print ParseMathTree(ParseStr("a-b+c"))
    print ParseMathTree(ParseStr("(a-b)+c"))
    print ParseMathTree(ParseStr("a-(b+c)"))
    print ParseMathTree(ParseStr("((a-(b+c))/(d*e))**f"))
    print repr(ParseMathTree(ParseStr("((a-(b+c))/(d*e))**f")))
    print ParseMathTree(ParseStr("sin(pi/2)"))
    print repr(ParseMathTree(ParseStr("sin(pi/2)")))
    x = MathTreeFunc1Sin(
            MathTreeOpDiv(
                MathTreeValVar(
                    'pi'),
                MathTreeValConst(
                    2.0)))
    print x
    print ParseMathTree(ParseStr("norm(a,b)"))

    choise = "n"
    while choise not in ["y","n"]:
        choise = raw_input("\nrun interactive test program [y/n]? ")
    if choise == "n":
        assert 0
    choise = "6"
    while choise != "7":
        if choise == "6":
            expression = raw_input("\nexpression? ")
            MyTree=ParseMathTree(ParseStr(expression))
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
            print "\n", MyTree
        if choise == "2":
            print "\n", repr(MyTree)
        if choise == "3":
            print "\n", MyTree.VarList()
        if choise == "4":
            print
            VarDict = { }
            for key in MyTree.VarList():
                VarDict[key] = float(raw_input("value for '" + key + "'? "))
            print "\nthe result is:",MyTree.Calc(VarDict)
        if choise == "5":
            VarName = raw_input("\nwhich variable? ")
            if VarName != "":
                MyTree = MyTree.Derivative(VarName)
                print "\nexpression replaced by the calculated derivative"
            else:
                print "\nstring was empty, go back to main menu"
