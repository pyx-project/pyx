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


class ArgCountError(Exception): pass
class DerivativeError(Exception): pass

class MathTree:

    def __init__(self, ArgCount, *Args):
        self.ArgCount = ArgCount
        self.Args = []
        for arg in Args:
            self.AddArg(arg)

    def __repr__(self, depth = 0):
        indent = ""
        SingleIndent = "    "
        for i in range(depth):
            indent = indent + SingleIndent
        result = indent + self.__class__.__name__ + "(\n"
        for SubTree in self.Args:
            if isinstance(SubTree, MathTree):
                result = result + SubTree.__repr__(depth + 1)
            else:
                result = result + indent + SingleIndent + repr(SubTree)

            if SubTree != self.Args[-1]:
                result = result + ",\n"
            else:
                result = result + ")"
        return result

    def AddArg(self, Arg, Last=0, NotLast=0):
        if len(self.Args) == self.ArgCount:
            raise ArgCountError
        self.Args.append(Arg)
        if NotLast and len(self.Args) == self.ArgCount:
            raise ArgCountError
        if Last and len(self.Args) != self.ArgCount:
            raise ArgCountError

    def DependOn(self, arg):
        for Arg in self.Args:
            if Arg.DependOn(arg):
                return 1
        return 0

    def Derivative(self, arg):
        if not self.DependOn(arg):
            return MathTreeValConst(0.0)
        return self.CalcDerivative(arg)

    def VarList(self):
        list = [ ]
        for Arg in self.Args:
            newlist = Arg.VarList()
            for x in newlist:
                if x not in list:
                    list.append(x)
        return list


class MathTreeVal(MathTree):

    def __init__(self, *args):
        MathTree.__init__(self, 1, *args)

    def __str__(self):
        return str(self.Args[0])


ConstPattern = re.compile(r"-?\d*((\d\.?)|(\.?\d))\d*(E[+-]?\d+)?",
                          re.IGNORECASE)

class MathTreeValConst(MathTreeVal):

    def InitByParser(self, arg):
        Match = arg.MatchPattern(ConstPattern)
        if Match:
            self.AddArg(string.atof(Match))
            return 1

    def CalcDerivative(self, arg):
        raise DerivativeError("expression doesn't depend on \"%s\"" % arg)

    def Derivative(self, arg):
        return MathTreeValConst(0.0)

    def DependOn(self, arg):
        return 0

    def VarList(self):
        return [ ]

    def Calc(self, **args):
        return self.Args[0]


VarPattern = re.compile(r"[a-z_][a-z0-9_]*", re.IGNORECASE)
MathConst = {"pi": math.pi, "e": math.e}

class MathTreeValVar(MathTreeVal):

    def InitByParser(self, arg):
        Match = arg.MatchPattern(VarPattern)
        if Match:
            self.AddArg(Match)
            return 1

    def CalcDerivative(self, arg):
        if arg != self.Args[0]:
            raise DerivativeError("expression doesn't depend on \"%s\"" % arg)
        return MathTreeValConst(1.0)

    def DependOn(self, arg):
        if arg == self.Args[0]:
            return 1
        return 0

    def VarList(self):
        if self.Args[0] in MathConst.keys():
            return []
        return [self.Args[0]]

    def Calc(self, **args):
        if self.Args[0] in args.keys():
            return float(args[self.Args[0]])
        return MathConst[self.Args[0]]


class MathTreeFunc(MathTree):

    def __init__(self, name, ArgCount, *args):
        self.name = name
        MathTree.__init__(self, ArgCount, *args)

    def InitByParser(self, arg):
        return arg.MatchStrParenthesis(self.name)

    def __str__(self):
        args = ""
        for SubTree in self.Args:
            args = args + str(SubTree)
            if SubTree != self.Args[-1]:
                args = args + ","
        return self.name + "(" + args + ")"


class MathTreeFunc1(MathTreeFunc):

    def __init__(self, name, *args):
        MathTreeFunc.__init__(self, name, 1, *args)


class MathTreeFunc1Neg(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "neg", *args)

    def CalcDerivative(self, arg):
        return MathTreeFunc1Neg(self.Args[0].CalcDerivative(arg))

    def Calc(self, **args):
        return -self.Args[0].Calc(**args)


class MathTreeFunc1Abs(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "abs", *args)

    def CalcDerivative(self, arg):
        return MathTreeOpMul(
                   MathTreeFunc1Sgn(self.Args[0]),
                   self.Args[0].CalcDerivative(arg))

    def Calc(self, **args):
        return abs(self.Args[0].Calc(**args))


class MathTreeFunc1Sgn(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "sgn", *args)

    def CalcDerivative(self, arg):
        return MathTreeValConst(0.0)

    def Calc(self, **args):
        if self.Args[0].Calc(**args) < 0:
            return -1.0
        return 1.0


class MathTreeFunc1Sqrt(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "sqrt", *args)

    def CalcDerivative(self, arg):
        return MathTreeOpMul(
                   MathTreeOpDiv(
                       MathTreeValConst(0.5),
                       self),
                   self.Args[0].CalcDerivative(arg))

    def Calc(self, **args):
        return math.sqrt(self.Args[0].Calc(**args))


class MathTreeFunc1Exp(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "exp", *args)

    def CalcDerivative(self, arg):
        return MathTreeOpMul(self, self.Args[0].CalcDerivative(arg))

    def Calc(self, **args):
        return math.exp(self.Args[0].Calc(**args))


class MathTreeFunc1Log(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "log", *args)

    def CalcDerivative(self, arg):
        return MathTreeOpDiv(self.Args[0].CalcDerivative(arg), self.Args[0])

    def Calc(self, **args):
        return math.log(self.Args[0].Calc(**args))


class MathTreeFunc1Sin(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "sin", *args)

    def CalcDerivative(self, arg):
        return MathTreeOpMul(
                   MathTreeFunc1Cos(self.Args[0]),
                   self.Args[0].CalcDerivative(arg))

    def Calc(self, **args):
        return math.sin(self.Args[0].Calc(**args))


class MathTreeFunc1Cos(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "cos", *args)

    def CalcDerivative(self, arg):
        return MathTreeOpMul(
                   MathTreeFunc1Neg(MathTreeFunc1Sin(self.Args[0])),
                   self.Args[0].CalcDerivative(arg))

    def Calc(self, **args):
        return math.cos(self.Args[0].Calc(**args))


class MathTreeFunc1Tan(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "tan", *args)

    def CalcDerivative(self, arg):
        return MathTreeOpDiv(
                   self.Args[0].CalcDerivative(arg),
                   MathTreeOpPow(
                       MathTreeFunc1Cos(self.Args[0]),
                       MathTreeValConst(2.0)))

    def Calc(self, **args):
        return math.tan(self.Args[0].Calc(**args))


class MathTreeFunc1ASin(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "asin", *args)

    def CalcDerivative(self, arg):
        return MathTreeOpDiv(
                   self.Args[0].CalcDerivative(arg),
                   MathTreeFunc1Sqrt(
                       MathTreeOpSub(
                           MathTreeValConst(1.0),
                           MathTreeOpPow(
                               self.Args[0],
                               MathTreeValConst(2.0)))))

    def Calc(self, **args):
        return math.asin(self.Args[0].Calc(**args))


class MathTreeFunc1ACos(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "acos", *args)

    def CalcDerivate(self, arg):
        return MathTreeOpDiv(
                   MathTreeFunc1Neg(self.Args[0].CalcDerivative(arg)),
                   MathTreeFunc1Sqrt(
                       MathTreeOpSub(
                           MathTreeValConst(1.0),
                           MathTreeOpPow(
                               self.Args[0],
                               MathTreeValConst(2.0)))))

    def Calc(self, **args):
        return math.acos(self.Args[0].Calc(**args))


class MathTreeFunc1ATan(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "atan", *args)

    def CalcDerivate(self, arg):
        return MathTreeOpDiv(
                   self.Args[0].CalcDerivative(arg),
                   MathTreeOpAdd(
                       MathTreeValConst(1.0),
                       MathTreeOpPow(
                           self.Args[0],
                           MathTreeValConst(2.0))))

    def Calc(self, **args):
        return math.atan(self.Args[0].Calc(**args))


class MathTreeFunc1SinD(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "sind", *args)

    def CalcDerivative(self, arg):
        return MathTreeOpMul(
                   MathTreeFunc1CosD(self.Args[0]),
                   MathTreeOpMul(
                       MathTreeValConst(math.pi/180.0),
                       self.Args[0].CalcDerivative(arg)))

    def Calc(self, **args):
        return math.sin(math.pi/180.0*self.Args[0].Calc(**args))


class MathTreeFunc1CosD(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "cosd", *args)

    def CalcDerivative(self, arg):
        return MathTreeOpMul(
                   MathTreeFunc1Neg(MathTreeFunc1Sin(self.Args[0])),
                   MathTreeOpMul(
                       MathTreeValConst(math.pi/180.0),
                       self.Args[0].CalcDerivative(arg)))

    def Calc(self, **args):
        return math.cos(math.pi/180.0*self.Args[0].Calc(**args))


class MathTreeFunc1TanD(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "tand", *args)

    def CalcDerivative(self, arg):
        return MathTreeOpDiv(
                   MathTreeOpMul(
                       MathTreeValConst(math.pi/180.0),
                       self.Args[0].CalcDerivative(arg)),
                   MathTreeOpPow(
                       MathTreeFunc1Cos(self.Args[0]),
                       MathTreeValConst(2.0)))

    def Calc(self, **args):
        return math.tan(math.pi/180.0*self.Args[0].Calc(**args))


class MathTreeFunc1ASinD(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "asind", *args)

    def CalcDerivative(self, arg):
        return MathTreeOpDiv(
                   MathTreeOpMul(
                       MathTreeValConst(180.0/math.pi),
                       self.Args[0].CalcDerivative(arg)),
                   MathTreeFunc1Sqrt(
                       MathTreeOpSub(
                           MathTreeValConst(1.0),
                           MathTreeOpPow(
                               self.Args[0],
                               MathTreeValConst(2.0)))))

    def Calc(self, **args):
        return 180.0/math.pi*math.asin(self.Args[0].Calc(**args))


class MathTreeFunc1ACosD(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "acosd", *args)

    def CalcDerivate(self, arg):
        return MathTreeOpDiv(
                   MathTreeFunc1Neg(
                       MathTreeOpMul(
                           MathTreeValConst(180.0/math.pi),
                           self.Args[0].CalcDerivative(arg))),
                   MathTreeFunc1Sqrt(
                       MathTreeOpSub(
                           MathTreeValConst(1.0),
                           MathTreeOpPow(
                               self.Args[0],
                               MathTreeValConst(2.0)))))

    def Calc(self, **args):
        return 180.0/math.pi*math.acos(self.Args[0].Calc(**args))


class MathTreeFunc1ATanD(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "atand", *args)

    def CalcDerivate(self, arg):
        return MathTreeOpDiv(
                   MathTreeOpMul(
                       MathTreeValConst(180.0/math.pi),
                       self.Args[0].CalcDerivative(arg)),
                   MathTreeOpAdd(
                       MathTreeValConst(1.0),
                       MathTreeOpPow(
                           self.Args[0],
                           MathTreeValConst(2.0))))

    def Calc(self, **args):
        return 180.0/math.pi*math.atan(self.Args[0].Calc(**args))


class MathTreeFunc2(MathTreeFunc):

    def __init__(self, name, *args):
        MathTreeFunc.__init__(self, name, 2, *args)


class MathTreeFunc2Norm(MathTreeFunc2):

    def __init__(self, *args):
        MathTreeFunc2.__init__(self, "norm", *args)

    def CalcDerivative(self, arg):
        if self.Args[0].DependOn(arg):
            if self.Args[1].DependOn(arg):
                return MathTreeOpDiv(
                           MathTreeOpAdd(
                               MathTreeOpMul(
                                   self.Args[0],
                                   self.Args[0].CalcDerivative(arg)),
                               MathTreeOpMul(
                                   self.Args[1],
                                   self.Args[1].CalcDerivative(arg))),
                           self)
            else:
                return MathTreeOpDiv(
                           MathTreeOpMul(
                               self.Args[0],
                               self.Args[0].CalcDerivative(arg)),
                           self)
        else:
            if self.Args[1].DependOn(arg):
                return MathTreeOpDiv(
                           MathTreeOpMul(
                               self.Args[1],
                               self.Args[1].CalcDerivative(arg)),
                           self)

    def Calc(self, **args):
        return math.sqrt(self.Args[0].Calc(**args) ** 2 +
                         self.Args[1].Calc(**args) ** 2)


FuncExternPattern = re.compile(r"([a-z_][a-z0-9_]*)\s*\(", re.IGNORECASE)

class MathTreeFuncExtern(MathTreeFunc):

    def __init__(self, *args):
        MathTreeFunc.__init__(self, None, -1, *args)

    def InitByParser(self, arg):
        Match = arg.MatchPattern(FuncExternPattern)
        if Match:
            self.name = Match[:-1].strip()
            return self.name

    def Calc(self, **args):
        return args[self.name](*[arg.Calc(**args) for arg in self.Args])


class MathTreeOp(MathTree):

    def __init__(self, level, symbol, *args):
        self.ParenthesisBarrier = 0
        self.level = level
        self.symbol = symbol
        MathTree.__init__(self, 2, *args)

    def __str__(self):
        result = ""
        if isinstance(self.Args[0], MathTreeOp) and\
            self.level > self.Args[0].level:
            result = result + "(" + str(self.Args[0]) + ")"
        else:
            result = result + str(self.Args[0])
        result = result + self.symbol
        if isinstance(self.Args[1], MathTreeOp) and\
            self.level >= self.Args[1].level:
            result = result + "(" + str(self.Args[1]) + ")"
        else:
            result = result + str(self.Args[1])
        return result

    def InitByParser(self, arg):
        return arg.MatchStr(self.symbol)


class MathTreeOpAdd(MathTreeOp):

    def __init__(self, *args):
        MathTreeOp.__init__(self, 1, "+", *args)

    def CalcDerivative(self, arg):
        if self.Args[0].DependOn(arg):
            if self.Args[1].DependOn(arg):
                return MathTreeOpAdd(
                           self.Args[0].CalcDerivative(arg),
                           self.Args[1].CalcDerivative(arg))
            else:
                return self.Args[0].CalcDerivative(arg)
        else:
            if self.Args[1].DependOn(arg):
                return self.Args[1].CalcDerivative(arg)

    def Calc(self, **args):
        return self.Args[0].Calc(**args) + self.Args[1].Calc(**args)


class MathTreeOpSub(MathTreeOp):

    def __init__(self, *args):
        MathTreeOp.__init__(self, 1, "-", *args)

    def CalcDerivative(self, arg):
        if self.Args[0].DependOn(arg):
            if self.Args[1].DependOn(arg):
                return MathTreeOpSub(
                           self.Args[0].CalcDerivative(arg),
                           self.Args[1].CalcDerivative(arg))
            else:
                return self.Args[0].CalcDerivative(arg)
        else:
            if self.Args[1].DependOn(arg):
                return MathTreeFunc1Neg(self.Args[1].CalcDerivative(arg))

    def Calc(self, **args):
        return self.Args[0].Calc(**args) - self.Args[1].Calc(**args)


class MathTreeOpMul(MathTreeOp):

    def __init__(self, *args):
        MathTreeOp.__init__(self, 2, "*", *args)

    def CalcDerivative(self, arg):
        if self.Args[0].DependOn(arg):
            if self.Args[1].DependOn(arg):
                return MathTreeOpAdd(
                           MathTreeOpMul(
                               self.Args[0],
                               self.Args[1].CalcDerivative(arg)),
                           MathTreeOpMul(
                               self.Args[0].CalcDerivative(arg),
                               self.Args[1]))
            else:
                return MathTreeOpMul(
                           self.Args[0].CalcDerivative(arg),
                           self.Args[1])
        else:
            if self.Args[1].DependOn(arg):
                return MathTreeOpMul(
                           self.Args[0],
                           self.Args[1].CalcDerivative(arg))

    def Calc(self, **args):
        return self.Args[0].Calc(**args) * self.Args[1].Calc(**args)


class MathTreeOpDiv(MathTreeOp):

    def __init__(self, *args):
        MathTreeOp.__init__(self, 2, "/", *args)

    def CalcDerivative(self, arg):
        if self.Args[0].DependOn(arg):
            if self.Args[1].DependOn(arg):
                return MathTreeOpMul(
                           MathTreeOpSub(
                               MathTreeOpMul(
                                   self.Args[0].CalcDerivative(arg),
                                   self.Args[1]),
                               MathTreeOpMul(
                                   self.Args[0],
                                   self.Args[1].CalcDerivative(arg))),
                           MathTreeOpPow(
                               self.Args[1],
                               MathTreeValConst(-2.0)))
            else:
                return MathTreeOpDiv(
                           self.Args[0].CalcDerivative(arg),
                           self.Args[1])
        else:
            if self.Args[1].DependOn(arg):
                return MathTreeOpMul(
                           MathTreeOpMul(
                               MathTreeFunc1Neg(self.Args[0]),
                               MathTreeOpPow(
                                   self.Args[1],
                                   MathTreeValConst(-2.0))),
                           self.Args[1].CalcDerivative(arg))

    def Calc(self, **args):
        return self.Args[0].Calc(**args) / self.Args[1].Calc(**args)


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
        if self.Args[0].DependOn(arg):
            if self.Args[1].DependOn(arg):
                return MathTreeOpMul(
                           MathTreeOpPow(
                               self.Args[0],
                               self.Args[1]),
                           MathTreeOpAdd(
                               MathTreeOpMul(
                                   MathTreeFunc1Log(self.Args[0]),
                                   self.Args[1].CalcDerivative(arg)),
                               MathTreeOpMul(
                                   self.Args[1],
                                   MathTreeOpDiv(
                                       self.Args[0].CalcDerivative(arg),
                                       self.Args[0]))))
            else:
                return MathTreeOpMul(
                           self.Args[1],
                           MathTreeOpMul(
                               MathTreeOpPow(
                                   self.Args[0],
                                   MathTreeOpSub(
                                       self.Args[1],
                                       MathTreeValConst(1.0))),
                               self.Args[0].CalcDerivative(arg)))
        else:
            if self.Args[1].DependOn(arg):
                return MathTreeOpMul(
                           MathTreeOpMul(
                               MathTreeOpPow(
                                   self.Args[0],
                                   self.Args[1]),
                               MathTreeFunc1Log(self.Args[0])),
                           self.Args[1].CalcDerivative(arg))

    def Calc(self, **args):
        return self.Args[0].Calc(**args) ** self.Args[1].Calc(**args)



class UndefinedMathTreeParseError(Exception):

    def __init__(self, ParseStr, MathTree):
        self.ParseStr = ParseStr
        self.MathTree = MathTree

    def __str__(self):
        return "\n" + str(self.ParseStr)


class RightParenthesisExpectedMathTreeParseError(UndefinedMathTreeParseError): pass
class RightParenthesisFoundMathTreeParseError(UndefinedMathTreeParseError): pass
class CommaExpectedMathTreeParseError(UndefinedMathTreeParseError): pass
class CommaFoundMathTreeParseError(UndefinedMathTreeParseError): pass
class OperatorExpectedMathTreeParseError(UndefinedMathTreeParseError): pass
class OperandExpectedMathTreeParseError(UndefinedMathTreeParseError): pass


DefaultMathTreeOps = (MathTreeOpPow, MathTreeOpDiv, MathTreeOpMul, MathTreeOpSub, MathTreeOpAdd)
DefaultMathTreeFuncs = (MathTreeFunc1Neg, MathTreeFunc1Abs, MathTreeFunc1Sgn, MathTreeFunc1Sqrt,
                        MathTreeFunc1Exp, MathTreeFunc1Log,
                        MathTreeFunc1Sin, MathTreeFunc1Cos, MathTreeFunc1Tan,
                        MathTreeFunc1ASin, MathTreeFunc1ACos, MathTreeFunc1ATan,
                        MathTreeFunc1SinD, MathTreeFunc1CosD, MathTreeFunc1TanD,
                        MathTreeFunc1ASinD, MathTreeFunc1ACosD, MathTreeFunc1ATanD,
                        MathTreeFunc2Norm)

DefaultMathTreeVals = (MathTreeValConst, MathTreeValVar)

class parser:

    def __init__(self, MathTreeOps=DefaultMathTreeOps,
                       MathTreeFuncs=DefaultMathTreeFuncs,
                       MathTreeVals=DefaultMathTreeVals):
        self.MathTreeOps = MathTreeOps
        self.MathTreeFuncs = MathTreeFuncs
        self.MathTreeVals = MathTreeVals

    def parse(self, str, externfunction=0):
        return self.ParseMathTree(ParseStr(str), externfunction=externfunction)

    def ParseMathTree(self, arg, externfunction=0):
        Tree = None
        Match = arg.MatchPattern(re.compile(r"\s*-(?![0-9\.])"))
        if Match:
            Tree = MathTreeFunc1Neg()
        while 1:
            i = arg.MatchStr("(")
            if i:
                try:
                    self.ParseMathTree(arg)
                    raise RightParenthesisExpectedMathTreeParseError(arg, Tree)
                except RightParenthesisFoundMathTreeParseError, e:
                    if isinstance(e.MathTree, MathTreeOp):
                        e.MathTree.ParenthesisBarrier = 1
                    if Tree is not None:
                        Tree.AddArg(e.MathTree)
                    else:
                        Tree = e.MathTree
            else:
                for FuncClass in self.MathTreeFuncs:
                    Func = FuncClass()
                    if Func.InitByParser(arg):
                        if Tree is not None:
                            SubTree = Tree # XXX 1: four lines code dublication (see 2)
                            while isinstance(SubTree, MathTreeOp) and len(SubTree.Args) == 2:
                                SubTree = SubTree.Args[1]
                            SubTree.AddArg(Func)
                        else:
                            Tree = Func
                        while 1:
                            try:
                                self.ParseMathTree(arg)
                                raise RightParenthesisExpectedMathTreeParseError(arg, Tree)
                            except CommaFoundMathTreeParseError, e:
                                try:
                                    Func.AddArg(e.MathTree, NotLast=1)
                                except ArgCountError:
                                    raise RightParenthesisExpectedMathTreeParseError(arg, Tree)
                                continue
                            except RightParenthesisFoundMathTreeParseError, e:
                                try:
                                    Func.AddArg(e.MathTree, Last=1)
                                except ArgCountError:
                                    raise CommaExpectedMathTreeParseError(arg, Tree)
                                break
                        break
                else:
                    FuncExtern = MathTreeFuncExtern()
                    if externfunction and FuncExtern.InitByParser(arg):
                        if Tree is not None:
                            Tree.AddArg(FuncExtern)
                        else:
                            Tree = FuncExtern
                        while 1:
                            try:
                                self.ParseMathTree(arg)
                                raise RightParenthesisExpectedMathTreeParseError(arg, Tree)
                            except CommaFoundMathTreeParseError, e:
                                FuncExtern.AddArg(e.MathTree)
                                continue
                            except RightParenthesisFoundMathTreeParseError, e:
                                FuncExtern.AddArg(e.MathTree)
                                break
                    else:
                        for ValClass in self.MathTreeVals:
                            Val = ValClass()
                            if Val.InitByParser(arg):
                                if Tree is not None:
                                    SubTree = Tree # XXX 2: four lines code dublication (see 1)
                                    while isinstance(SubTree, MathTreeOp) and len(SubTree.Args) == 2:
                                        SubTree = SubTree.Args[1]
                                    SubTree.AddArg(Val)
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
            for OpClass in self.MathTreeOps:
                Op = OpClass()
                if Op.InitByParser(arg):
                    SubTree = Tree
                    SubTreeRoot = None
                    while isinstance(SubTree, MathTreeOp) and\
                          Op.level > SubTree.level and\
                          not SubTree.ParenthesisBarrier:
                        SubTreeRoot = SubTree
                        SubTree = SubTree.Args[1]
                    if SubTreeRoot:
                        Op.AddArg(SubTree)
                        SubTreeRoot.Args[1] = Op
                    else:
                        Op.AddArg(Tree)
                        Tree = Op
                    break
            else:
                raise OperatorExpectedMathTreeParseError(arg, Tree)
