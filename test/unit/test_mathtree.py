import unittest

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
        assert repr(myparser.parse("norm(a,b)")) == """MathTreeFunc2Norm(
    MathTreeValVar(
        'a'),
    MathTreeValVar(
        'b'))"""

    def testCalc(self):
        myparser = mathtree.parser()
        abc = {"a": 1, "b": 2, "c": 3}
        abcdef = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "f": 6}
        assert abs(myparser.parse("a+b-c").Calc(abc)) <= 1e-10
        assert abs(myparser.parse("(a+b)-c").Calc(abc)) <= 1e-10
        assert abs(myparser.parse("a+(b-c)").Calc(abc)) <= 1e-10
        assert abs(myparser.parse("a-b+c-2").Calc(abc)) <= 1e-10
        assert abs(myparser.parse("(a-b)+c-2").Calc(abc)) <= 1e-10
        assert abs(myparser.parse("a-(b+c)+4").Calc(abc)) <= 1e-10
        assert abs(myparser.parse("a+b-c*d/e**f-2.999232").Calc(abcdef)) <= 1e-10
        assert abs(myparser.parse("a**b/c*d-e+f-7/3").Calc(abcdef)) <= 1e-10
        assert abs(myparser.parse("((a-(b+c))/(d*e))**f-6.4e-5").Calc(abcdef)) <= 1e-10
        assert abs(myparser.parse("neg(1)+1").Calc({})) <= 1e-10
        assert abs(myparser.parse("sgn(1)-1").Calc({})) <= 1e-10
        assert abs(myparser.parse("sgn(-1)+1").Calc({})) <= 1e-10
        assert abs(myparser.parse("sqrt(4)-2").Calc({})) <= 1e-10
        assert abs(myparser.parse("log(e)-1").Calc({})) <= 1e-10
        assert abs(myparser.parse("exp(1)-e").Calc({})) <= 1e-10
        assert abs(myparser.parse("sin(pi/2)-1").Calc({})) <= 1e-10
        assert abs(myparser.parse("cos(pi)+1").Calc({})) <= 1e-10
        assert abs(myparser.parse("tan(pi/4)-1").Calc({})) <= 1e-10
        assert abs(myparser.parse("asin(1) - pi/2").Calc({})) <= 1e-10
        assert abs(myparser.parse("acos(-1) - pi").Calc({})) <= 1e-10
        assert abs(myparser.parse("atan(1) - pi/4").Calc({})) <= 1e-10
        assert abs(myparser.parse("sind(90)-1").Calc({})) <= 1e-10
        assert abs(myparser.parse("cosd(180)+1").Calc({})) <= 1e-10
        assert abs(myparser.parse("tand(45)-1").Calc({})) <= 1e-10
        assert abs(myparser.parse("asind(1) - 90").Calc({})) <= 1e-10
        assert abs(myparser.parse("acosd(-1) - 180").Calc({})) <= 1e-10
        assert abs(myparser.parse("atand(1) - 45").Calc({})) <= 1e-10
        assert abs(myparser.parse("norm(3,4)").Calc({}) - 5) <= 1e-10

    def testExtern(self):
        myparser = mathtree.parser()
        a = 1
        b = 2
        c = 3
        f = lambda x: x*x
        assert abs(myparser.parse("a+b-c").Calc(locals())) <= 1e-10
        assert abs(myparser.parse("f(2)-4", extern=locals()).Calc()) <= 1e-10

    def testException(self):
        myparser = mathtree.parser()
        try:
            myparser.parse("")
            assert 0, "OperandExpectedMathTreeParseError expected"
        except mathtree.OperandExpectedMathTreeParseError: pass
        try:
            myparser.parse("???")
            assert 0, "OperandExpectedMathTreeParseError expected"
        except mathtree.OperandExpectedMathTreeParseError: pass
        try:
            myparser.parse("sin()")
            assert 0, "OperandExpectedMathTreeParseError expected"
        except mathtree.OperandExpectedMathTreeParseError: pass
        try:
            myparser.parse("sin(x,y)")
            assert 0, "RightParenthesisExpectedMathTreeParseError expected"
        except mathtree.RightParenthesisExpectedMathTreeParseError: pass
        try:
            myparser.parse("norm(x)")
            assert 0, "CommaExpectedMathTreeParseError expected"
        except mathtree.CommaExpectedMathTreeParseError: pass
        try:
            myparser.parse("xxx(y)")
            assert 0, "OperatorExpectedMathTreeParseError expected"
        except mathtree.OperatorExpectedMathTreeParseError: pass
        try:
            myparser.parse("(1+2")
            assert 0, "RightParenthesisExpectedMathTreeParseError expected"
        except mathtree.RightParenthesisExpectedMathTreeParseError: pass
        try:
            myparser.parse("1+2)")
            assert 0, "RightParenthesisFoundExpectedMathTreeParseError expected"
        except mathtree.RightParenthesisFoundMathTreeParseError: pass
        try:
            myparser.parse("1,2")
            assert 0, "CommaFoundExpectedMathTreeParseError expected"
        except mathtree.CommaFoundMathTreeParseError: pass

suite = unittest.TestSuite((unittest.makeSuite(MathTreeTestCase, 'test'), ))

if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite)

