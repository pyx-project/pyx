import sys
if sys.path[0] != "../..":
    sys.path.insert(0, "../..")

import unittest

import parser
from pyx import *
from pyx import mathtree

class MathTreeTestCase(unittest.TestCase):

    def testStr(self):
        myparser = mathtree.parser()
        assert str(myparser.parse("a+b-c")) == "a+b-c"
        assert str(myparser.parse("(a+b)-c")) == "a+b-c"
        assert str(myparser.parse("a+(b-c)")) == "a+(b-c)" # XXX: needs no parenthesis
        assert str(myparser.parse("a-b+c")) == "a-b+c"
        assert str(myparser.parse("(a-b)+c")) == "a-b+c"
        assert str(myparser.parse("a-(b+c)")) == "a-(b+c)"
        assert str(myparser.parse("a+b-c*d/e**f")) == "a+b-c*d/e^f"
        assert str(myparser.parse("a**b/c*d-e+f")) == "a^b/c*d-e+f"
        assert str(myparser.parse("((a-(b+c))/(d*e))**f")) == "((a-(b+c))/(d*e))^f"
        assert str(myparser.parse("sin(pi/2)")) == "sin(pi/2.0)"
        assert str(myparser.parse("a+b*sin(c)**d")) == "a+b*sin(c)^d"
        assert str(myparser.parse("a+b*(c)")) == "a+b*c"
        assert str(myparser.parse("norm(a,b)")) == "norm(a,b)"

    def testRepr(self):
        myparser = mathtree.parser()
        assert repr(myparser.parse("a+b-c")) == """MathTreeOpSub(
    MathTreeOpAdd(
        MathTreeValVar(
            'a'),
        MathTreeValVar(
            'b')),
    MathTreeValVar(
        'c'))"""
        assert repr(myparser.parse("(a+b)-c")) == """MathTreeOpSub(
    MathTreeOpAdd(
        MathTreeValVar(
            'a'),
        MathTreeValVar(
            'b')),
    MathTreeValVar(
        'c'))"""
        assert repr(myparser.parse("a+(b-c)")) == """MathTreeOpAdd(
    MathTreeValVar(
        'a'),
    MathTreeOpSub(
        MathTreeValVar(
            'b'),
        MathTreeValVar(
            'c')))"""
        assert repr(myparser.parse("a-b+c")) == """MathTreeOpAdd(
    MathTreeOpSub(
        MathTreeValVar(
            'a'),
        MathTreeValVar(
            'b')),
    MathTreeValVar(
        'c'))"""
        assert repr(myparser.parse("(a-b)+c")) == """MathTreeOpAdd(
    MathTreeOpSub(
        MathTreeValVar(
            'a'),
        MathTreeValVar(
            'b')),
    MathTreeValVar(
        'c'))"""
        assert repr(myparser.parse("a-(b+c)")) == """MathTreeOpSub(
    MathTreeValVar(
        'a'),
    MathTreeOpAdd(
        MathTreeValVar(
            'b'),
        MathTreeValVar(
            'c')))"""
        assert repr(myparser.parse("a+b-c*d/e**f")) == """MathTreeOpSub(
    MathTreeOpAdd(
        MathTreeValVar(
            'a'),
        MathTreeValVar(
            'b')),
    MathTreeOpDiv(
        MathTreeOpMul(
            MathTreeValVar(
                'c'),
            MathTreeValVar(
                'd')),
        MathTreeOpPow(
            MathTreeValVar(
                'e'),
            MathTreeValVar(
                'f'))))"""
        assert repr(myparser.parse("a**b/c*d-e+f")) == """MathTreeOpAdd(
    MathTreeOpSub(
        MathTreeOpMul(
            MathTreeOpDiv(
                MathTreeOpPow(
                    MathTreeValVar(
                        'a'),
                    MathTreeValVar(
                        'b')),
                MathTreeValVar(
                    'c')),
            MathTreeValVar(
                'd')),
        MathTreeValVar(
            'e')),
    MathTreeValVar(
        'f'))"""
        assert repr(myparser.parse("((a-(b+c))/(d*e))**f")) == """MathTreeOpPow(
    MathTreeOpDiv(
        MathTreeOpSub(
            MathTreeValVar(
                'a'),
            MathTreeOpAdd(
                MathTreeValVar(
                    'b'),
                MathTreeValVar(
                    'c'))),
        MathTreeOpMul(
            MathTreeValVar(
                'd'),
            MathTreeValVar(
                'e'))),
    MathTreeValVar(
        'f'))"""
        assert repr(myparser.parse("sin(pi/2)")) == """MathTreeFunc1Sin(
    MathTreeOpDiv(
        MathTreeValVar(
            'pi'),
        MathTreeValConst(
            2.0)))"""
        assert repr(myparser.parse("a+b*sin(c)**d")) == """MathTreeOpAdd(
    MathTreeValVar(
        'a'),
    MathTreeOpMul(
        MathTreeValVar(
            'b'),
        MathTreeOpPow(
            MathTreeFunc1Sin(
                MathTreeValVar(
                    'c')),
            MathTreeValVar(
                'd'))))"""
        assert repr(myparser.parse("a+b*(c)")) == """MathTreeOpAdd(
    MathTreeValVar(
        'a'),
    MathTreeOpMul(
        MathTreeValVar(
            'b'),
        MathTreeValVar(
            'c')))"""
        assert repr(myparser.parse("norm(a,b)")) == """MathTreeFunc2Norm(
    MathTreeValVar(
        'a'),
    MathTreeValVar(
        'b'))"""

    def testCalc(self):
        myparser = mathtree.parser()
        abc = {"a": 1, "b": 2, "c": 3}
        abcdef = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "f": 6}
        assert abs(myparser.parse("a+b-c").Calc(**abc)) <= 1e-10
        assert abs(myparser.parse("(a+b)-c").Calc(**abc)) <= 1e-10
        assert abs(myparser.parse("a+(b-c)").Calc(**abc)) <= 1e-10
        assert abs(myparser.parse("a-b+c-2").Calc(**abc)) <= 1e-10
        assert abs(myparser.parse("(a-b)+c-2").Calc(**abc)) <= 1e-10
        assert abs(myparser.parse("a-(b+c)+4").Calc(**abc)) <= 1e-10
        assert abs(myparser.parse("a+b-c*d/e**f-2.999232").Calc(**abcdef)) <= 1e-10
        assert abs(myparser.parse("a**b/c*d-e+f-7/3").Calc(**abcdef)) <= 1e-10
        assert abs(myparser.parse("((a-(b+c))/(d*e))**f-6.4e-5").Calc(**abcdef)) <= 1e-10
        assert abs(myparser.parse("-a**2+1").Calc(**abc)) <= 1e-10
        assert abs(myparser.parse("-1**2+1").Calc(**abc)) <= 1e-10
        assert abs(myparser.parse("1-a**2").Calc(**abc)) <= 1e-10
        assert abs(myparser.parse("--1-a**2").Calc(**abc)) <= 1e-10
        assert abs(myparser.parse("1+-a**2").Calc(**abc)) <= 1e-10
        assert abs(myparser.parse("neg(1)+1").Calc()) <= 1e-10
        assert abs(myparser.parse("abs(2)-2").Calc()) <= 1e-10
        assert abs(myparser.parse("abs(-2)-2").Calc()) <= 1e-10
        assert abs(myparser.parse("sgn(1)-1").Calc()) <= 1e-10
        assert abs(myparser.parse("sgn(-1)+1").Calc()) <= 1e-10
        assert abs(myparser.parse("sqrt(4)-2").Calc()) <= 1e-10
        assert abs(myparser.parse("log(e)-1").Calc()) <= 1e-10
        assert abs(myparser.parse("exp(1)-e").Calc()) <= 1e-10
        assert abs(myparser.parse("sin(pi/2)-1").Calc()) <= 1e-10
        assert abs(myparser.parse("cos(pi)+1").Calc()) <= 1e-10
        assert abs(myparser.parse("tan(pi/4)-1").Calc()) <= 1e-10
        assert abs(myparser.parse("asin(1) - pi/2").Calc()) <= 1e-10
        assert abs(myparser.parse("acos(-1) - pi").Calc()) <= 1e-10
        assert abs(myparser.parse("atan(1) - pi/4").Calc()) <= 1e-10
        assert abs(myparser.parse("sind(90)-1").Calc()) <= 1e-10
        assert abs(myparser.parse("cosd(180)+1").Calc()) <= 1e-10
        assert abs(myparser.parse("tand(45)-1").Calc()) <= 1e-10
        assert abs(myparser.parse("asind(1) - 90").Calc()) <= 1e-10
        assert abs(myparser.parse("acosd(-1) - 180").Calc()) <= 1e-10
        assert abs(myparser.parse("atand(1) - 45").Calc()) <= 1e-10
        assert abs(myparser.parse("norm(3,4)").Calc() - 5) <= 1e-10

    def testExtern(self):
        myparser = mathtree.parser()
        assert abs(myparser.parse("a+b-c").Calc(a=1, b=2, c=3)) <= 1e-10
        assert abs(myparser.parse("f(2)-4").Calc(f=lambda x: x*x)) <= 1e-10

    def testException(self):
        myparser = mathtree.parser()
        self.failUnlessRaises(parser.ParserError, myparser.parse, "")
        self.failUnlessRaises(parser.ParserError, myparser.parse, "???")
        self.failUnlessRaises(Exception, myparser.parse, "sin()")
        self.failUnlessRaises(mathtree.ArgCountError, myparser.parse, "sin(x,y)")
        self.failUnlessRaises(KeyError, myparser.parse("sin(x)").Calc)
        self.failUnlessRaises(IndexError, myparser.parse("norm(x)").Calc, x=1)
        self.failUnlessRaises(parser.ParserError, myparser.parse, "xxx yyy")
        self.failUnlessRaises(parser.ParserError, myparser.parse, "(1+2")
        self.failUnlessRaises(parser.ParserError, myparser.parse, "1+2)")
        self.failUnlessEqual(len(myparser.parse("1,2")), 2)


if __name__ == "__main__":
    unittest.main()
