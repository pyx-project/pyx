import sys
if sys.path[0] != "../..":
    sys.path.insert(0, "../..")

import unittest

from pyx import *
from pyx.graph.axis.tick import rational


class RationalTestCase(unittest.TestCase):

    def RationalEqual(self, num, denom, r):
        self.failUnlessEqual(num*r.denom, r.num*denom)

    def testRationalInitSeq(self):
        self.RationalEqual(1, 1, rational((2, 2)))
        self.RationalEqual(1, 1, rational([2, 2]))

    def testRationalInitString(self):
        self.RationalEqual(1, 1, rational("1"))
        self.RationalEqual(11, 10, rational("1.1"))
        self.RationalEqual(12345, 1000, rational("12.345"))
        self.RationalEqual(1, 1, rational("1."))
        self.RationalEqual(1, 10, rational(".1"))
        self.RationalEqual(1, 1, rational("1e+0"))
        self.RationalEqual(11, 10, rational("1.1e-0"))
        self.RationalEqual(10, 1, rational("1.e+1"))
        self.RationalEqual(1, 100, rational(".1e-1"))
        self.RationalEqual(-1, 1, rational("-1"))
        self.RationalEqual(-11, 10, rational("-1.1"))
        self.RationalEqual(-1, 1, rational("-1."))
        self.RationalEqual(-1, 10, rational("-.1"))
        self.RationalEqual(-1, 1, rational("-1e0"))
        self.RationalEqual(-11, 10, rational("-1.1e-0"))
        self.RationalEqual(-10, 1, rational("-1.e+1"))
        self.RationalEqual(-1, 100, rational("-.1e-1"))
        self.RationalEqual(-100000000000000000000L, 1, rational("-1e+20"))
        self.RationalEqual(-1, 100000000000000000000L, rational("-1e-20"))

        self.RationalEqual(1234, 1, rational(" 1234"))
        self.failUnlessRaises(ValueError, rational, "12 34")
        self.failUnlessRaises(ValueError, rational, "1 2.34")
        self.failUnlessRaises(ValueError, rational, "12 .34")
        self.failUnlessRaises(ValueError, rational, "12. 34")
        self.failUnlessRaises(ValueError, rational, "12.3 4")
        self.RationalEqual(1234, 100, rational("12.34 "))
        self.RationalEqual(1234, 1, rational(" +1234"))
        self.RationalEqual(-1234, 1, rational(" -1234"))
        self.failUnlessRaises(ValueError, rational, " + 1234")
        self.failUnlessRaises(ValueError, rational, " - 1234")
        self.failUnlessRaises(ValueError, rational, "12.34 e0")
        self.failUnlessRaises(ValueError, rational, "12.34e 0")
        self.RationalEqual(1234, 10000, rational("12.34e-2"))
        self.RationalEqual(1234, 1000, rational("12.34E-1"))
        self.RationalEqual(1234, 100, rational("12.34e0 "))
        self.RationalEqual(1234, 10, rational("12.34E+1"))
        self.RationalEqual(1234, 1, rational("12.34e+2"))
        self.failUnlessRaises(ValueError, rational, "12.34e -0")
        self.failUnlessRaises(ValueError, rational, "12.34e+ 0")
        self.failUnlessRaises(ValueError, rational, "12.34e- 0")
        self.failUnlessRaises(ValueError, rational, "12.34e +0")
        self.failUnlessRaises(ValueError, rational, "12.34.56")
        self.failUnlessRaises(ValueError, rational, "12e34.56")

    def testRationalInitStrings(self):
        self.RationalEqual(1, 2, rational("1/2"))
        self.RationalEqual(1, 2, rational("1.1/2.2"))
        self.RationalEqual(1, 2, rational("1./2."))
        self.RationalEqual(1, 2, rational(".1/.2"))
        self.RationalEqual(1, 2, rational("1e+0/2e+0"))
        self.RationalEqual(1, 2, rational("1.1e-0/2.2e-0"))
        self.RationalEqual(1, 2, rational("1.e+1/2.e+1"))
        self.RationalEqual(1, 2, rational(".1e-1/.2e-1"))
        self.RationalEqual(1, 2, rational("-1/-2"))
        self.RationalEqual(1, 2, rational("-1.1/-2.2"))
        self.RationalEqual(1, 2, rational("-1./-2."))
        self.RationalEqual(1, 2, rational("-.1/-.2"))
        self.RationalEqual(1, 2, rational("-1e0/-2e0"))
        self.RationalEqual(1, 2, rational("-1.1e-0/-2.2e-0"))
        self.RationalEqual(1, 2, rational("-1.e+1/-2.e+1"))
        self.RationalEqual(1, 2, rational("-.1e-1/-.2e-1"))

    def testRationalInitNumber(self):
        self.RationalEqual(1, 1, rational(1))
        self.RationalEqual(11, 10, rational(1.1))
        self.RationalEqual(1, 1, rational(1.))
        self.RationalEqual(1, 10, rational(.1))
        self.RationalEqual(1, 1, rational(1e+0))
        self.RationalEqual(11, 10, rational(1.1e-0))
        self.RationalEqual(10, 1, rational(1.e+1))
        self.RationalEqual(1, 100, rational(.1e-1))
        self.RationalEqual(-1, 1, rational(-1))
        self.RationalEqual(-11, 10, rational(-1.1))
        self.RationalEqual(-1, 1, rational(-1.))
        self.RationalEqual(-1, 10, rational(-.1))
        self.RationalEqual(-1, 1, rational(-1e0))
        self.RationalEqual(-11, 10, rational(-1.1e-0))
        self.RationalEqual(-10, 1, rational(-1.e+1))
        self.RationalEqual(-1, 100, rational(-.1e-1))


if __name__ == "__main__":
    unittest.main()
