import sys
if sys.path[0] != "../..":
    sys.path.insert(0, "../..")

import unittest

from pyx import *
from pyx.graph.tick import frac


class FracTestCase(unittest.TestCase):

    def FracEqual(self, f1, f2):
        self.failUnlessEqual(f1.enum*f2.denom, f2.enum*f1.denom)

    def testFracInitSeq(self):
        self.FracEqual(frac((1, 1)), frac((2, 2)))
        self.FracEqual(frac([1, 1]), frac((2, 2)))

    def testFracInitString(self):
        self.FracEqual(frac((1, 1)), frac("1"))
        self.FracEqual(frac((11, 10)), frac("1.1"))
        self.FracEqual(frac((1, 1)), frac("1."))
        self.FracEqual(frac((1, 10)), frac(".1"))
        self.FracEqual(frac((1, 1)), frac("1e+0"))
        self.FracEqual(frac((11, 10)), frac("1.1e-0"))
        self.FracEqual(frac((10, 1)), frac("1.e+1"))
        self.FracEqual(frac((1, 100)), frac(".1e-1"))
        self.FracEqual(frac((-1, 1)), frac("-1"))
        self.FracEqual(frac((-11, 10)), frac("-1.1"))
        self.FracEqual(frac((-1, 1)), frac("-1."))
        self.FracEqual(frac((-1, 10)), frac("-.1"))
        self.FracEqual(frac((-1, 1)), frac("-1e0"))
        self.FracEqual(frac((-11, 10)), frac("-1.1e-0"))
        self.FracEqual(frac((-10, 1)), frac("-1.e+1"))
        self.FracEqual(frac((-1, 100)), frac("-.1e-1"))

    def testFracInitStringFrac(self):
        self.FracEqual(frac((1, 2)), frac("1/2"))
        self.FracEqual(frac((1, 2)), frac("1.1/2.2"))
        self.FracEqual(frac((1, 2)), frac("1./2."))
        self.FracEqual(frac((1, 2)), frac(".1/.2"))
        self.FracEqual(frac((1, 2)), frac("1e+0/2e+0"))
        self.FracEqual(frac((1, 2)), frac("1.1e-0/2.2e-0"))
        self.FracEqual(frac((1, 2)), frac("1.e+1/2.e+1"))
        self.FracEqual(frac((1, 2)), frac(".1e-1/.2e-1"))
        self.FracEqual(frac((1, 2)), frac("-1/-2"))
        self.FracEqual(frac((1, 2)), frac("-1.1/-2.2"))
        self.FracEqual(frac((1, 2)), frac("-1./-2."))
        self.FracEqual(frac((1, 2)), frac("-.1/-.2"))
        self.FracEqual(frac((1, 2)), frac("-1e0/-2e0"))
        self.FracEqual(frac((1, 2)), frac("-1.1e-0/-2.2e-0"))
        self.FracEqual(frac((1, 2)), frac("-1.e+1/-2.e+1"))
        self.FracEqual(frac((1, 2)), frac("-.1e-1/-.2e-1"))

    def testFracInitNumber(self):
        self.FracEqual(frac((1, 1)), frac(1))
        self.FracEqual(frac((11, 10)), frac(1.1))
        self.FracEqual(frac((1, 1)), frac(1.))
        self.FracEqual(frac((1, 10)), frac(.1))
        self.FracEqual(frac((1, 1)), frac(1e+0))
        self.FracEqual(frac((11, 10)), frac(1.1e-0))
        self.FracEqual(frac((10, 1)), frac(1.e+1))
        self.FracEqual(frac((1, 100)), frac(.1e-1))
        self.FracEqual(frac((-1, 1)), frac(-1))
        self.FracEqual(frac((-11, 10)), frac(-1.1))
        self.FracEqual(frac((-1, 1)), frac(-1.))
        self.FracEqual(frac((-1, 10)), frac(-.1))
        self.FracEqual(frac((-1, 1)), frac(-1e0))
        self.FracEqual(frac((-11, 10)), frac(-1.1e-0))
        self.FracEqual(frac((-10, 1)), frac(-1.e+1))
        self.FracEqual(frac((-1, 100)), frac(-.1e-1))


if __name__ == "__main__":
    unittest.main()
