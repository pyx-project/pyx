#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2002-2004 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2003-2004 Michael Schindler <m-schindler@users.sourceforge.net>
# Copyright (C) 2002-2004 André Wobst <wobsta@users.sourceforge.net>
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


import string, re, math, symbol, token
import parser as pythonparser


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

    def Calc(HIDDEN_self, **args):
        return HIDDEN_self.Args[0]


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

    def Calc(HIDDEN_self, **args):
        if HIDDEN_self.Args[0] in args.keys():
            return float(args[HIDDEN_self.Args[0]])
        return MathConst[HIDDEN_self.Args[0]]


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

    def Calc(HIDDEN_self, **args):
        return -HIDDEN_self.Args[0].Calc(**args)


class MathTreeFunc1Abs(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "abs", *args)

    def CalcDerivative(self, arg):
        return MathTreeOpMul(
                   MathTreeFunc1Sgn(self.Args[0]),
                   self.Args[0].CalcDerivative(arg))

    def Calc(HIDDEN_self, **args):
        return abs(HIDDEN_self.Args[0].Calc(**args))


class MathTreeFunc1Sgn(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "sgn", *args)

    def CalcDerivative(self, arg):
        return MathTreeValConst(0.0)

    def Calc(HIDDEN_self, **args):
        if HIDDEN_self.Args[0].Calc(**args) < 0:
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

    def Calc(HIDDEN_self, **args):
        return math.sqrt(HIDDEN_self.Args[0].Calc(**args))


class MathTreeFunc1Exp(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "exp", *args)

    def CalcDerivative(self, arg):
        return MathTreeOpMul(self, self.Args[0].CalcDerivative(arg))

    def Calc(HIDDEN_self, **args):
        return math.exp(HIDDEN_self.Args[0].Calc(**args))


class MathTreeFunc1Log(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "log", *args)

    def CalcDerivative(self, arg):
        return MathTreeOpDiv(self.Args[0].CalcDerivative(arg), self.Args[0])

    def Calc(HIDDEN_self, **args):
        return math.log(HIDDEN_self.Args[0].Calc(**args))


class MathTreeFunc1Sin(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "sin", *args)

    def CalcDerivative(self, arg):
        return MathTreeOpMul(
                   MathTreeFunc1Cos(self.Args[0]),
                   self.Args[0].CalcDerivative(arg))

    def Calc(HIDDEN_self, **args):
        return math.sin(HIDDEN_self.Args[0].Calc(**args))


class MathTreeFunc1Cos(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "cos", *args)

    def CalcDerivative(self, arg):
        return MathTreeOpMul(
                   MathTreeFunc1Neg(MathTreeFunc1Sin(self.Args[0])),
                   self.Args[0].CalcDerivative(arg))

    def Calc(HIDDEN_self, **args):
        return math.cos(HIDDEN_self.Args[0].Calc(**args))


class MathTreeFunc1Tan(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "tan", *args)

    def CalcDerivative(self, arg):
        return MathTreeOpDiv(
                   self.Args[0].CalcDerivative(arg),
                   MathTreeOpPow(
                       MathTreeFunc1Cos(self.Args[0]),
                       MathTreeValConst(2.0)))

    def Calc(HIDDEN_self, **args):
        return math.tan(HIDDEN_self.Args[0].Calc(**args))


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

    def Calc(HIDDEN_self, **args):
        return math.asin(HIDDEN_self.Args[0].Calc(**args))


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

    def Calc(HIDDEN_self, **args):
        return math.acos(HIDDEN_self.Args[0].Calc(**args))


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

    def Calc(HIDDEN_self, **args):
        return math.atan(HIDDEN_self.Args[0].Calc(**args))


class MathTreeFunc1SinD(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "sind", *args)

    def CalcDerivative(self, arg):
        return MathTreeOpMul(
                   MathTreeFunc1CosD(self.Args[0]),
                   MathTreeOpMul(
                       MathTreeValConst(math.pi/180.0),
                       self.Args[0].CalcDerivative(arg)))

    def Calc(HIDDEN_self, **args):
        return math.sin(math.pi/180.0*HIDDEN_self.Args[0].Calc(**args))


class MathTreeFunc1CosD(MathTreeFunc1):

    def __init__(self, *args):
        MathTreeFunc1.__init__(self, "cosd", *args)

    def CalcDerivative(self, arg):
        return MathTreeOpMul(
                   MathTreeFunc1Neg(MathTreeFunc1Sin(self.Args[0])),
                   MathTreeOpMul(
                       MathTreeValConst(math.pi/180.0),
                       self.Args[0].CalcDerivative(arg)))

    def Calc(HIDDEN_self, **args):
        return math.cos(math.pi/180.0*HIDDEN_self.Args[0].Calc(**args))


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

    def Calc(HIDDEN_self, **args):
        return math.tan(math.pi/180.0*HIDDEN_self.Args[0].Calc(**args))


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

    def Calc(HIDDEN_self, **args):
        return 180.0/math.pi*math.asin(HIDDEN_self.Args[0].Calc(**args))


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

    def Calc(HIDDEN_self, **args):
        return 180.0/math.pi*math.acos(HIDDEN_self.Args[0].Calc(**args))


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

    def Calc(HIDDEN_self, **args):
        return 180.0/math.pi*math.atan(HIDDEN_self.Args[0].Calc(**args))


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

    def Calc(HIDDEN_self, **args):
        return math.sqrt(HIDDEN_self.Args[0].Calc(**args) ** 2 +
                         HIDDEN_self.Args[1].Calc(**args) ** 2)


FuncExternPattern = re.compile(r"([a-z_][a-z0-9_]*)\s*\(", re.IGNORECASE)

class MathTreeFuncExtern(MathTreeFunc):

    def __init__(self, *args):
        MathTreeFunc.__init__(self, None, -1, *args)

    def InitByParser(self, arg):
        Match = arg.MatchPattern(FuncExternPattern)
        if Match:
            self.name = Match[:-1].strip()
            return self.name

    def SetName(self, arg):
        self.name = arg.strip()
        return self

    def Calc(HIDDEN_self, **args):
        return args[HIDDEN_self.name](*[arg.Calc(**args) for arg in HIDDEN_self.Args])


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

    def Calc(HIDDEN_self, **args):
        return HIDDEN_self.Args[0].Calc(**args) + HIDDEN_self.Args[1].Calc(**args)


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

    def Calc(HIDDEN_self, **args):
        return HIDDEN_self.Args[0].Calc(**args) - HIDDEN_self.Args[1].Calc(**args)


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

    def Calc(HIDDEN_self, **args):
        return HIDDEN_self.Args[0].Calc(**args) * HIDDEN_self.Args[1].Calc(**args)


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

    def Calc(HIDDEN_self, **args):
        return HIDDEN_self.Args[0].Calc(**args) / HIDDEN_self.Args[1].Calc(**args)


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

    def Calc(HIDDEN_self, **args):
        return HIDDEN_self.Args[0].Calc(**args) ** HIDDEN_self.Args[1].Calc(**args)



DefaultMathTreeFuncs = [MathTreeFunc1Neg, MathTreeFunc1Abs, MathTreeFunc1Sgn, MathTreeFunc1Sqrt,
                        MathTreeFunc1Exp, MathTreeFunc1Log,
                        MathTreeFunc1Sin, MathTreeFunc1Cos, MathTreeFunc1Tan,
                        MathTreeFunc1ASin, MathTreeFunc1ACos, MathTreeFunc1ATan,
                        MathTreeFunc1SinD, MathTreeFunc1CosD, MathTreeFunc1TanD,
                        MathTreeFunc1ASinD, MathTreeFunc1ACosD, MathTreeFunc1ATanD,
                        MathTreeFunc2Norm]

class parser:

    def __init__(self, MathTreeFuncs=DefaultMathTreeFuncs):
        self.MathTreeFuncs = MathTreeFuncs

    def parse(self, expr):
        return self.astseq2mtree(pythonparser.expr(expr.strip()).totuple())

    def astseq2mtree(self, astseq, isfunc=0):
        # astseq has to be a sequence!
        tree = None

        if token.ISTERMINAL(astseq[0]):
            raise Exception("")

        if astseq[0] == symbol.arith_expr: # {{{
            try:
                # 1. arith_expr "PLUS" term
                if astseq[-2][0] == token.PLUS:
                    tree = MathTreeOpAdd(
                        self.astseq2mtree(astseq[:-2], isfunc=isfunc),
                        self.astseq2mtree(astseq[-1], isfunc=isfunc))
                # 2. arith_expr "MINUS" term
                elif astseq[-2][0] == token.MINUS:
                    tree = MathTreeOpSub(
                        self.astseq2mtree(astseq[:-2], isfunc=isfunc),
                        self.astseq2mtree(astseq[-1], isfunc=isfunc))
                else:
                    raise Exception("")
            except:
                # 3. term
                tree = self.astseq2mtree(astseq[1], isfunc=isfunc)
            return tree # }}}

        if astseq[0] == symbol.term: # {{{
            try:
                # 1. term "STAR" factor
                if astseq[-2][0] == token.STAR:
                    tree = MathTreeOpMul(
                        self.astseq2mtree(astseq[:-2], isfunc=isfunc),
                        self.astseq2mtree(astseq[-1], isfunc=isfunc))
                # 2. term "SLASH" factor
                elif astseq[-2][0] == token.SLASH:
                    tree = MathTreeOpDiv(
                        self.astseq2mtree(astseq[:-2], isfunc=isfunc),
                        self.astseq2mtree(astseq[-1], isfunc=isfunc))
                else:
                    raise Exception("")
            except:
                # 3. factor
                tree = self.astseq2mtree(astseq[1], isfunc=isfunc)
            return tree # }}}

        if astseq[0] == symbol.factor: # {{{
            if len(astseq) == 3:
                # 1. "PLUS" factor
                if astseq[1][0] == token.PLUS:
                    tree = self.astseq2mtree(astseq[2], isfunc=isfunc)
                # 2. "MINUS" factor
                elif astseq[1][0] == token.MINUS:
                    tree = MathTreeFunc1Neg(self.astseq2mtree(astseq[2], isfunc=isfunc))
                else:
                    raise Exception("unknown factor")
            elif len(astseq) == 2:
                # 3. power
                tree = self.astseq2mtree(astseq[1], isfunc=isfunc)
            else:
                raise Exception("wrong length of factor")
            return tree # }}}

        if astseq[0] == symbol.power: # {{{
            try:
                # 1. "DOUBLESTAR" factor
                if astseq[-2][0] == token.DOUBLESTAR:
                    tree = MathTreeOpPow(
                        self.astseq2mtree(astseq[:-2], isfunc=isfunc),
                        self.astseq2mtree(astseq[-1], isfunc=isfunc))
                else:
                    raise Exception("")
            except:
                # 2. atom + [trailer]
                if len(astseq) == 3:
                    # we have a function call atom + "LPAR" + argumentlist + "RPAR"
                    if astseq[2][0] == symbol.trailer and \
                       astseq[2][1][0] == token.LPAR and \
                       astseq[2][2][0] == symbol.arglist and \
                       astseq[2][3][0] == token.RPAR:
                        tree = self.astseq2mtree(astseq[1], isfunc=1)
                        for subtree in self.astseq2mtree(astseq[2][2], isfunc=0):
                            tree.AddArg(subtree)
                    elif astseq[2][0] == symbol.trailer and \
                       astseq[2][1][0] == token.LPAR and \
                       astseq[2][2][0] == token.RPAR:
                        tree = self.astseq2mtree(astseq[1], isfunc=1)
                    else:
                        raise Exception("wrong function call")
                else:
                    tree = self.astseq2mtree(astseq[1], isfunc=0)

            return tree # }}}

        if astseq[0] == symbol.atom: # {{{
            # only one nontrivial term:
            if len(astseq) == 2:
                if astseq[1][0] == token.NUMBER:
                # 1. a number
                # XXX: for evaluation of brackets we will need integers as well
                    tree = MathTreeValConst(string.atof(astseq[1][1]))
                elif astseq[1][0] == token.NAME:
                # 2. a function
                    if isfunc:
                        # a known function
                        for funcclass in self.MathTreeFuncs:
                            func = funcclass() # ist das guenstig, da jedesmal eine Instanz zu erzeugen?
                                               # doofe Frage, nein! <wobsta>
                            if func.name == astseq[1][1]:
                                return func
                        # an unknown function
                        tree = MathTreeFuncExtern()
                        tree.SetName(astseq[1][1])
                    else:
                # 3. a variable
                        return MathTreeValVar(astseq[1][1])
            elif len(astseq) == 4:
                # parentheses or brackets for structuring an atom
                if (astseq[1][0] == token.LPAR and astseq[3][0] == token.RPAR) or \
                   (astseq[1][0] == token.LSQB and astseq[3][0] == token.RSQB):
                    tree = self.astseq2mtree(astseq[2], isfunc=isfunc)
            else:
                raise Exception("symbol.atom with unknown number of arguments")
            return tree # }}}

        if astseq[0] == symbol.arglist: # {{{
            treelist = []
            for arg in astseq[1:]:
                if arg[0] == token.COMMA:
                    continue
                elif arg[0] == symbol.argument:
                    treelist.append(self.astseq2mtree(arg, isfunc=isfunc))
            return treelist # }}}

        if astseq[0] == symbol.testlist: # {{{
            treelist = []
            for arg in astseq[1:]:
                if arg[0] == token.COMMA:
                    continue
                elif arg[0] == symbol.test:
                    treelist.append(self.astseq2mtree(arg, isfunc=isfunc))
            if len(treelist) == 1: return treelist[0]
            else: return treelist # }}}

        if astseq[0] != symbol.eval_input and len(astseq) > 2:
            raise Exception("invalid expression structure (contains several parts)")
        return self.astseq2mtree(astseq[1], isfunc=isfunc)

