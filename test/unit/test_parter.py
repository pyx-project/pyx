import sys
if sys.path[0] != "../..":
    sys.path.insert(0, "../..")

import unittest

from pyx import *
from pyx.graph.tick import frac, tick
from pyx.graph.parter import linparter, logparter


class ParterTestCase(unittest.TestCase):

    def PartEqual(self, part1, part2):
        self.failUnlessEqual(len(part1), len(part2))
        for tick1, tick2 in zip(part1, part2):
            self.failUnlessEqual(tick1, tick2)
            self.failUnlessEqual(tick1.ticklevel, tick2.ticklevel)
            self.failUnlessEqual(tick1.labellevel, tick2.labellevel)
            self.failUnlessEqual(tick1.label, tick2.label)

    def testLinParter(self):
        self.PartEqual(linparter(tickdist="1", labeldist=()).defaultpart(0, 1, 1, 1),
                       [tick((0, 1), 0, None), tick((1, 1), 0, None)])
        self.PartEqual(linparter(tickdist=("1", "0.5"), labeldist=()).defaultpart(0, 1, 1, 1),
                       [tick((0, 1), 0, None), tick((1, 2), 1, None), tick((1, 1), 0, None)])
        self.PartEqual(linparter(tickdist=("1", "0.5", "0.25"), labeldist=()).defaultpart(0, 1, 1, 1),
                       [tick((0, 1), 0, None), tick((1, 4), 2, None), tick((1, 2), 1, None), tick((3, 4), 2, None), tick((1, 1), 0, None)])
        self.PartEqual(linparter(tickdist=("1", "0.5"), labeldist=(), extendtick=None).defaultpart(0, 1.5, 1, 1),
                       [tick((0, 1), 0, None), tick((1, 2), 1, None), tick((1, 1), 0, None), tick((3, 2), 1, None)])
        self.PartEqual(linparter(tickdist=("1", "0.5"), labeldist=(), extendtick=1).defaultpart(0, 1.2, 1, 1),
                       [tick((0, 1), 0, None), tick((1, 2), 1, None), tick((1, 1), 0, None), tick((3, 2), 1, None)])
        self.PartEqual(linparter(tickdist=("1", "0.5"), labeldist=(), extendtick=0).defaultpart(0, 1.2, 1, 1),
                       [tick((0, 1), 0, None), tick((1, 2), 1, None), tick((1, 1), 0, None), tick((3, 2), 1, None), tick((2, 1), 0, None)])
        self.PartEqual(linparter(labeldist="1", tickdist=()).defaultpart(0, 1, 1, 1),
                       [tick((0, 1), None, 0), tick((1, 1), None, 0)])
        self.PartEqual(linparter(labeldist=("1", "0.5"), tickdist=()).defaultpart(0, 1, 1, 1),
                       [tick((0, 1), None, 0), tick((1, 2), None, 1), tick((1, 1), None, 0)])
        self.PartEqual(linparter(labeldist=("1", "0.5", "0.25"), tickdist=()).defaultpart(0, 1, 1, 1),
                       [tick((0, 1), None, 0), tick((1, 4), None, 2), tick((1, 2), None, 1), tick((3, 4), None, 2), tick((1, 1), None, 0)])
        self.PartEqual(linparter(labeldist=("1", "0.5"), tickdist=(), extendlabel=None).defaultpart(0, 1.5, 1, 1),
                       [tick((0, 1), None, 0), tick((1, 2), None, 1), tick((1, 1), None, 0), tick((3, 2), None, 1)])
        self.PartEqual(linparter(labeldist=("1", "0.5"), tickdist=(), extendlabel=1).defaultpart(0, 1.2, 1, 1),
                       [tick((0, 1), None, 0), tick((1, 2), None, 1), tick((1, 1), None, 0), tick((3, 2), None, 1)])
        self.PartEqual(linparter(labeldist=("1", "0.5"), tickdist=(), extendlabel=0).defaultpart(0, 1.2, 1, 1),
                       [tick((0, 1), None, 0), tick((1, 2), None, 1), tick((1, 1), None, 0), tick((3, 2), None, 1), tick((2, 1), None, 0)])
        self.PartEqual(linparter(tickdist="1").defaultpart(0, 1, 1, 1),
                       [tick((0, 1), 0, 0), tick((1, 1), 0, 0)])
        self.PartEqual(linparter(tickdist=("1", "0.5")).defaultpart(0, 1, 1, 1),
                       [tick((0, 1), 0, 0), tick((1, 2), 1, None), tick((1, 1), 0, 0)])
        self.PartEqual(linparter(tickdist=("1", "0.5", "0.25")).defaultpart(0, 1, 1, 1),
                       [tick((0, 1), 0, 0), tick((1, 4), 2, None), tick((1, 2), 1, None), tick((3, 4), 2, None), tick((1, 1), 0, 0)])
        self.PartEqual(linparter(tickdist=("1", "0.5"), extendtick=None).defaultpart(0, 1.5, 1, 1),
                       [tick((0, 1), 0, 0), tick((1, 2), 1, None), tick((1, 1), 0, 0), tick((3, 2), 1, None)])
        self.PartEqual(linparter(tickdist=("1", "0.5"), extendtick=1).defaultpart(0, 1.2, 1, 1),
                       [tick((0, 1), 0, 0), tick((1, 2), 1, None), tick((1, 1), 0, 0), tick((3, 2), 1, None)])
        self.PartEqual(linparter(tickdist=("1", "0.5"), extendtick=0).defaultpart(0, 1.2, 1, 1),
                       [tick((0, 1), 0, 0), tick((1, 2), 1, None), tick((1, 1), 0, 0), tick((3, 2), 1, None), tick((2, 1), 0, 0)])
        self.PartEqual(linparter(labeldist="1").defaultpart(0, 1, 1, 1),
                       [tick((0, 1), 0, 0), tick((1, 1), 0, 0)])
        self.PartEqual(linparter(labeldist=("1", "0.5")).defaultpart(0, 1, 1, 1),
                       [tick((0, 1), 0, 0), tick((1, 2), None, 1), tick((1, 1), 0, 0)])
        self.PartEqual(linparter(labeldist=("1", "0.5", "0.25")).defaultpart(0, 1, 1, 1),
                       [tick((0, 1), 0, 0), tick((1, 4), None, 2), tick((1, 2), None, 1), tick((3, 4), None, 2), tick((1, 1), 0, 0)])
        self.PartEqual(linparter(labeldist=("1", "0.5"), extendtick=None).defaultpart(0, 1.5, 1, 1),
                       [tick((0, 1), 0, 0), tick((1, 2), None, 1), tick((1, 1), 0, 0), tick((3, 2), None, 1)])
        self.PartEqual(linparter(labeldist=("1", "0.5"), extendtick=None, extendlabel=1).defaultpart(0, 1.2, 1, 1),
                       [tick((0, 1), 0, 0), tick((1, 2), None, 1), tick((1, 1), 0, 0), tick((3, 2), None, 1)])
        self.PartEqual(linparter(labeldist=("1", "0.5"), extendtick=None, extendlabel=0).defaultpart(0, 1.2, 1, 1),
                       [tick((0, 1), 0, 0), tick((1, 2), None, 1), tick((1, 1), 0, 0), tick((3, 2), None, 1), tick((2, 1), 0, 0)])
        self.PartEqual(linparter(labeldist="1", labels=("a", "b")).defaultpart(0, 1, 1, 1),
                       [tick((0, 1), 0, 0, "a"), tick((1, 1), 0, 0, "b")])
        self.PartEqual(linparter(labeldist=("1", "0.5"), labels=(("a", "c"), "b")).defaultpart(0, 1, 1, 1),
                       [tick((0, 1), 0, 0, "a"), tick((1, 2), None, 1, "b"), tick((1, 1), 0, 0, "c")])
        self.PartEqual(linparter(labeldist=("1", "0.5", "0.25"), labels=(("a", "e"), "c", ("b", "d"))).defaultpart(0, 1, 1, 1),
                       [tick((0, 1), 0, 0, "a"), tick((1, 4), None, 2, "b"), tick((1, 2), None, 1, "c"), tick((3, 4), None, 2, "d"), tick((1, 1), 0, 0, "e")])

    def testLogParter(self):
        self.PartEqual(logparter(tickpos=logparter.pre1exp, labelpos=()).defaultpart(1, 10, 1, 1),
                       [tick((1, 1), 0, None), tick((10, 1), 0, None)])
        self.PartEqual(logparter(tickpos=logparter.pre1exp, labelpos=()).defaultpart(1, 100, 1, 1),
                       [tick((1, 1), 0, None), tick((10, 1), 0, None), tick((100, 1), 0, None)])
        self.PartEqual(logparter(tickpos=logparter.pre1exp2, labelpos=()).defaultpart(1, 100, 1, 1),
                       [tick((1, 1), 0, None), tick((100, 1), 0, None)])
        self.PartEqual(logparter(tickpos=logparter.pre1to9exp, labelpos=()).defaultpart(1, 10, 1, 1),
                       [tick((1, 1), 0, None), tick((2, 1), 0, None), tick((3, 1), 0, None), tick((4, 1), 0, None), tick((5, 1), 0, None), tick((6, 1), 0, None), tick((7, 1), 0, None), tick((8, 1), 0, None), tick((9, 1), 0, None), tick((10, 1), 0, None)])
        self.PartEqual(logparter(tickpos=(logparter.pre1exp, logparter.pre1to9exp), labelpos=()).defaultpart(1, 10, 1, 1),
                       [tick((1, 1), 0, None), tick((2, 1), 1, None), tick((3, 1), 1, None), tick((4, 1), 1, None), tick((5, 1), 1, None), tick((6, 1), 1, None), tick((7, 1), 1, None), tick((8, 1), 1, None), tick((9, 1), 1, None), tick((10, 1), 0, None)])
        self.PartEqual(logparter(tickpos=(logparter.pre1exp, logparter.pre1to9exp)).defaultpart(1, 10, 1, 1),
                       [tick((1, 1), 0, 0), tick((2, 1), 1, None), tick((3, 1), 1, None), tick((4, 1), 1, None), tick((5, 1), 1, None), tick((6, 1), 1, None), tick((7, 1), 1, None), tick((8, 1), 1, None), tick((9, 1), 1, None), tick((10, 1), 0, 0)])


if __name__ == "__main__":
    unittest.main()
