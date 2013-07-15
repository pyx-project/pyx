import sys
if sys.path[0] != "../..":
    sys.path.insert(0, "../..")

import unittest

from pyx import *
from pyx.deco import *

class DecoTestCase(unittest.TestCase):

    def testExcluderange(self):
        d = decoratedpath(path.line(0, 0, 1, 0))
        d.ensurenormpath()
        d.excluderange(0.1, 0.2)
        d.excluderange(0.5, 0.6)
        d.excluderange(0.3, 0.4)
        self.failUnlessEqual(len(d.nostrokeranges), 3)
        self.failUnlessAlmostEqual(d.nostrokeranges[0][0], 0.1)
        self.failUnlessAlmostEqual(d.nostrokeranges[0][1], 0.2)
        self.failUnlessAlmostEqual(d.nostrokeranges[1][0], 0.3)
        self.failUnlessAlmostEqual(d.nostrokeranges[1][1], 0.4)
        self.failUnlessAlmostEqual(d.nostrokeranges[2][0], 0.5)
        self.failUnlessAlmostEqual(d.nostrokeranges[2][1], 0.6)

        d.excluderange(0.52, 0.58)
        self.failUnlessEqual(len(d.nostrokeranges), 3)
        self.failUnlessAlmostEqual(d.nostrokeranges[0][0], 0.1)
        self.failUnlessAlmostEqual(d.nostrokeranges[0][1], 0.2)
        self.failUnlessAlmostEqual(d.nostrokeranges[1][0], 0.3)
        self.failUnlessAlmostEqual(d.nostrokeranges[1][1], 0.4)
        self.failUnlessAlmostEqual(d.nostrokeranges[2][0], 0.5)
        self.failUnlessAlmostEqual(d.nostrokeranges[2][1], 0.6)

        d.excluderange(0.45, 0.55)
        self.failUnlessEqual(len(d.nostrokeranges), 3)
        self.failUnlessAlmostEqual(d.nostrokeranges[0][0], 0.1)
        self.failUnlessAlmostEqual(d.nostrokeranges[0][1], 0.2)
        self.failUnlessAlmostEqual(d.nostrokeranges[1][0], 0.3)
        self.failUnlessAlmostEqual(d.nostrokeranges[1][1], 0.4)
        self.failUnlessAlmostEqual(d.nostrokeranges[2][0], 0.45)
        self.failUnlessAlmostEqual(d.nostrokeranges[2][1], 0.6)

        d.excluderange(0.15, 0.25)
        self.failUnlessEqual(len(d.nostrokeranges), 3)
        self.failUnlessAlmostEqual(d.nostrokeranges[0][0], 0.1)
        self.failUnlessAlmostEqual(d.nostrokeranges[0][1], 0.25)
        self.failUnlessAlmostEqual(d.nostrokeranges[1][0], 0.3)
        self.failUnlessAlmostEqual(d.nostrokeranges[1][1], 0.4)
        self.failUnlessAlmostEqual(d.nostrokeranges[2][0], 0.45)
        self.failUnlessAlmostEqual(d.nostrokeranges[2][1], 0.6)

        d.excluderange(0.05, 0.15)
        self.failUnlessEqual(len(d.nostrokeranges), 3)
        self.failUnlessAlmostEqual(d.nostrokeranges[0][0], 0.05)
        self.failUnlessAlmostEqual(d.nostrokeranges[0][1], 0.25)
        self.failUnlessAlmostEqual(d.nostrokeranges[1][0], 0.3)
        self.failUnlessAlmostEqual(d.nostrokeranges[1][1], 0.4)
        self.failUnlessAlmostEqual(d.nostrokeranges[2][0], 0.45)
        self.failUnlessAlmostEqual(d.nostrokeranges[2][1], 0.6)

        d.excluderange(0.2, 0.35)
        self.failUnlessEqual(len(d.nostrokeranges), 2)
        self.failUnlessAlmostEqual(d.nostrokeranges[0][0], 0.05)
        self.failUnlessAlmostEqual(d.nostrokeranges[0][1], 0.4)
        self.failUnlessAlmostEqual(d.nostrokeranges[1][0], 0.45)
        self.failUnlessAlmostEqual(d.nostrokeranges[1][1], 0.6)

        d.excluderange(0.35, 0.65)
        self.failUnlessEqual(len(d.nostrokeranges), 1)
        self.failUnlessAlmostEqual(d.nostrokeranges[0][0], 0.05)
        self.failUnlessAlmostEqual(d.nostrokeranges[0][1], 0.65)


if __name__ == "__main__":
    unittest.main()
