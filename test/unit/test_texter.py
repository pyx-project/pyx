import sys
if sys.path[0] != "../..":
    sys.path.insert(0, "../..")

import unittest

from pyx import *
from pyx.graph.axis.tick import tick
from pyx.graph.axis.texter import rational, decimal, exponential, mixed


class TexterTestCase(unittest.TestCase):

    def testFrac(self):
        ticks = [tick((1, 4), labellevel=0), tick((2, 4), labellevel=0)]
        rational(numsuffix=r"\pi").labels(ticks)
        self.failUnlessEqual([t.label for t in ticks], [r"{{\pi}\over{4}}", r"{{\pi}\over{2}}"])
        ticks = [tick((0, 3), labellevel=0), tick((3, 3), labellevel=0), tick((6, 3), labellevel=0)]
        rational(numsuffix=r"\pi").labels(ticks)
        self.failUnlessEqual([t.label for t in ticks], ["0", r"\pi", r"2\pi"])
        ticks = [tick((2, 3), labellevel=0), tick((4, 5), labellevel=0)]
        rational(numsuffix=r"\pi", equaldenom=1).labels(ticks)
        self.failUnlessEqual([t.label for t in ticks], [r"{{10\pi}\over{15}}", r"{{12\pi}\over{15}}"])

    def testDec(self):
        ticks = [tick((1, 4), labellevel=0), tick((2, 4), labellevel=0)]
        decimal().labels(ticks)
        self.failUnlessEqual([t.label for t in ticks], ["0.25", "0.5"])
        ticks = [tick((1, 4), labellevel=0), tick((2, 4), labellevel=0)]
        decimal(equalprecision=1).labels(ticks)
        self.failUnlessEqual([t.label for t in ticks], ["0.25", "0.50"])
        ticks = [tick((1, 17), labellevel=0), tick((17, 17), labellevel=0)]
        decimal().labels(ticks)
        self.failUnlessEqual([t.label for t in ticks], [r"0.\overline{0588235294117647}", "1"])
        ticks = [tick((1, 10000000), labellevel=0), tick((1, 100000000), labellevel=0), tick((1, 1000000000), labellevel=0)]
        decimal(thousandthpartsep=",").labels(ticks)
        self.failUnlessEqual([t.label for t in ticks], ["0.000,000,1", "0.000,000,01", "0.000,000,001"])
        ticks = [tick((1000000, 1), labellevel=0), tick((10000000, 1), labellevel=0), tick((100000000, 1), labellevel=0)]
        decimal(thousandsep=",").labels(ticks)
        self.failUnlessEqual([t.label for t in ticks], ["1,000,000", "10,000,000", "100,000,000"])

    def testExp(self):
        ticks = [tick((-1, 10), labellevel=0), tick((1, 1), labellevel=0), tick((10, 1), labellevel=0)]
        exponential().labels(ticks)
        self.failUnlessEqual([t.label for t in ticks], [r"{-10^{-1}}", r"{10^{0}}", r"{10^{1}}"])
        ticks = [tick((0, 1), labellevel=0), tick((1, -10), labellevel=0), tick((15, 100), labellevel=0)]
        exponential(mantissatexter=decimal(equalprecision=1)).labels(ticks)
        self.failUnlessEqual([t.label for t in ticks], [r"{0.0}", r"{{-1.0}\cdot10^{-1}}", r"{{1.5}\cdot10^{-1}}"])

    def testDefault(self):
        ticks = [tick((0, 10), labellevel=0), tick((1, 10), labellevel=0), tick((1, 1), labellevel=0), tick((10, 1), labellevel=0)]
        mixed().labels(ticks)
        self.failUnlessEqual([t.label for t in ticks], ["0", "0.1", "1", "10"])
        ticks = [tick((0, 10), labellevel=0), tick((1, 10), labellevel=0), tick((1, 1), labellevel=0), tick((10000, 1), labellevel=0)]
        mixed().labels(ticks)
        self.failUnlessEqual([t.label for t in ticks], [r"{0}", r"{{1}\cdot10^{-1}}", r"{1}", r"{{1}\cdot10^{4}}"])
        ticks = [tick((0, 10), labellevel=0), tick((1, 10), labellevel=0), tick((1, 1), labellevel=0), tick((10000, 1), labellevel=0)]
        mixed(equaldecision=0).labels(ticks)
        self.failUnlessEqual([t.label for t in ticks], ["0", "0.1", "1", r"{10^{4}}"])


if __name__ == "__main__":
    unittest.main()
