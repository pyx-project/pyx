import unittest

from pyx import *
from pyx.graph import frac


def FracEqual(f1, f2):
     assert f1.enum * f2.denom == f2.enum * f1.denom, "fracs are different"


class FracTestCase(unittest.TestCase):

     def testFracInit(self):
         FracEqual(frac((1, 1)), frac((2, 2)))
         FracEqual(frac((1, 1)), frac("1"))
         FracEqual(frac((11, 10)), frac("1.1"))
         FracEqual(frac((1, 1)), frac("1."))
         FracEqual(frac((1, 10)), frac(".1"))
         FracEqual(frac((1, 1)), frac("1e+0"))
         FracEqual(frac((11, 10)), frac("1.1e-0"))
         FracEqual(frac((10, 1)), frac("1.e+1"))
         FracEqual(frac((1, 100)), frac(".1e-1"))
         FracEqual(frac((-1, 1)), frac("-1"))
         FracEqual(frac((-11, 10)), frac("-1.1"))
         FracEqual(frac((-1, 1)), frac("-1."))
         FracEqual(frac((-1, 10)), frac("-.1"))
         FracEqual(frac((-1, 1)), frac("-1e0"))
         FracEqual(frac((-11, 10)), frac("-1.1e-0"))
         FracEqual(frac((-10, 1)), frac("-1.e+1"))
         FracEqual(frac((-1, 100)), frac("-.1e-1"))
         FracEqual(frac((1, 1)), frac(1))
         FracEqual(frac((11, 10)), frac(1.1))
         FracEqual(frac((1, 1)), frac(1.))
         FracEqual(frac((1, 10)), frac(.1))
         FracEqual(frac((1, 1)), frac(1e+0))
         FracEqual(frac((11, 10)), frac(1.1e-0))
         FracEqual(frac((10, 1)), frac(1.e+1))
         FracEqual(frac((1, 100)), frac(.1e-1))
         FracEqual(frac((-1, 1)), frac(-1))
         FracEqual(frac((-11, 10)), frac(-1.1))
         FracEqual(frac((-1, 1)), frac(-1.))
         FracEqual(frac((-1, 10)), frac(-.1))
         FracEqual(frac((-1, 1)), frac(-1e0))
         FracEqual(frac((-11, 10)), frac(-1.1e-0))
         FracEqual(frac((-10, 1)), frac(-1.e+1))
         FracEqual(frac((-1, 100)), frac(-.1e-1))

suite = unittest.TestSuite((unittest.makeSuite(FracTestCase, 'test'),))

if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite)

