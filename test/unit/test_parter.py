import unittest

from pyx import *
from pyx.graph import frac, tick, linparter, logparter


def PartEqual(part1, part2):
     assert len(part1) == len(part2), "partitions have different length"
     for tick1, tick2 in zip(part1, part2):
         assert tick1 == tick2, "position is different"
         assert tick1.ticklevel == tick2.ticklevel, "ticklevel is different"
         assert tick1.labellevel == tick2.labellevel, "labellevel is different"
         assert tick1.label == tick2.label, "label is different"


class LinParterTestCase(unittest.TestCase):

     def testAll(self):
         PartEqual(linparter(tickdist="1", labeldist=()).defaultpart(0, 1, 1, 1),
                   [tick((0, 1), 0, None), tick((1, 1), 0, None)])
         PartEqual(linparter(tickdist=("1", "0.5"), labeldist=()).defaultpart(0, 1, 1, 1),
                   [tick((0, 1), 0, None), tick((1, 2), 1, None), tick((1, 1), 0, None)])
         PartEqual(linparter(tickdist=("1", "0.5", "0.25"), labeldist=()).defaultpart(0, 1, 1, 1),
                   [tick((0, 1), 0, None), tick((1, 4), 2, None), tick((1, 2), 1, None), tick((3, 4), 2, None), tick((1, 1), 0, None)])
         PartEqual(linparter(tickdist=("1", "0.5"), labeldist=(), extendtick=None).defaultpart(0, 1.5, 1, 1),
                   [tick((0, 1), 0, None), tick((1, 2), 1, None), tick((1, 1), 0, None), tick((3, 2), 1, None)])
         PartEqual(linparter(tickdist=("1", "0.5"), labeldist=(), extendtick=1).defaultpart(0, 1.2, 1, 1),
                   [tick((0, 1), 0, None), tick((1, 2), 1, None), tick((1, 1), 0, None), tick((3, 2), 1, None)])
         PartEqual(linparter(tickdist=("1", "0.5"), labeldist=(), extendtick=0).defaultpart(0, 1.2, 1, 1),
                   [tick((0, 1), 0, None), tick((1, 2), 1, None), tick((1, 1), 0, None), tick((3, 2), 1, None), tick((2, 1), 0, None)])
         PartEqual(linparter(labeldist="1", tickdist=()).defaultpart(0, 1, 1, 1),
                   [tick((0, 1), None, 0), tick((1, 1), None, 0)])
         PartEqual(linparter(labeldist=("1", "0.5"), tickdist=()).defaultpart(0, 1, 1, 1),
                   [tick((0, 1), None, 0), tick((1, 2), None, 1), tick((1, 1), None, 0)])
         PartEqual(linparter(labeldist=("1", "0.5", "0.25"), tickdist=()).defaultpart(0, 1, 1, 1),
                   [tick((0, 1), None, 0), tick((1, 4), None, 2), tick((1, 2), None, 1), tick((3, 4), None, 2), tick((1, 1), None, 0)])
         PartEqual(linparter(labeldist=("1", "0.5"), tickdist=(), extendlabel=None).defaultpart(0, 1.5, 1, 1),
                   [tick((0, 1), None, 0), tick((1, 2), None, 1), tick((1, 1), None, 0), tick((3, 2), None, 1)])
         PartEqual(linparter(labeldist=("1", "0.5"), tickdist=(), extendlabel=1).defaultpart(0, 1.2, 1, 1),
                   [tick((0, 1), None, 0), tick((1, 2), None, 1), tick((1, 1), None, 0), tick((3, 2), None, 1)])
         PartEqual(linparter(labeldist=("1", "0.5"), tickdist=(), extendlabel=0).defaultpart(0, 1.2, 1, 1),
                   [tick((0, 1), None, 0), tick((1, 2), None, 1), tick((1, 1), None, 0), tick((3, 2), None, 1), tick((2, 1), None, 0)])
         PartEqual(linparter(tickdist="1").defaultpart(0, 1, 1, 1),
                   [tick((0, 1), 0, 0), tick((1, 1), 0, 0)])
         PartEqual(linparter(tickdist=("1", "0.5")).defaultpart(0, 1, 1, 1),
                   [tick((0, 1), 0, 0), tick((1, 2), 1, None), tick((1, 1), 0, 0)])
         PartEqual(linparter(tickdist=("1", "0.5", "0.25")).defaultpart(0, 1, 1, 1),
                   [tick((0, 1), 0, 0), tick((1, 4), 2, None), tick((1, 2), 1, None), tick((3, 4), 2, None), tick((1, 1), 0, 0)])
         PartEqual(linparter(tickdist=("1", "0.5"), extendtick=None).defaultpart(0, 1.5, 1, 1),
                   [tick((0, 1), 0, 0), tick((1, 2), 1, None), tick((1, 1), 0, 0), tick((3, 2), 1, None)])
         PartEqual(linparter(tickdist=("1", "0.5"), extendtick=1).defaultpart(0, 1.2, 1, 1),
                   [tick((0, 1), 0, 0), tick((1, 2), 1, None), tick((1, 1), 0, 0), tick((3, 2), 1, None)])
         PartEqual(linparter(tickdist=("1", "0.5"), extendtick=0).defaultpart(0, 1.2, 1, 1),
                   [tick((0, 1), 0, 0), tick((1, 2), 1, None), tick((1, 1), 0, 0), tick((3, 2), 1, None), tick((2, 1), 0, 0)])
         PartEqual(linparter(labeldist="1").defaultpart(0, 1, 1, 1),
                   [tick((0, 1), 0, 0), tick((1, 1), 0, 0)])
         PartEqual(linparter(labeldist=("1", "0.5")).defaultpart(0, 1, 1, 1),
                   [tick((0, 1), 0, 0), tick((1, 2), None, 1), tick((1, 1), 0, 0)])
         PartEqual(linparter(labeldist=("1", "0.5", "0.25")).defaultpart(0, 1, 1, 1),
                   [tick((0, 1), 0, 0), tick((1, 4), None, 2), tick((1, 2), None, 1), tick((3, 4), None, 2), tick((1, 1), 0, 0)])
         PartEqual(linparter(labeldist=("1", "0.5"), extendtick=None).defaultpart(0, 1.5, 1, 1),
                   [tick((0, 1), 0, 0), tick((1, 2), None, 1), tick((1, 1), 0, 0), tick((3, 2), None, 1)])
         PartEqual(linparter(labeldist=("1", "0.5"), extendtick=None, extendlabel=1).defaultpart(0, 1.2, 1, 1),
                   [tick((0, 1), 0, 0), tick((1, 2), None, 1), tick((1, 1), 0, 0), tick((3, 2), None, 1)])
         PartEqual(linparter(labeldist=("1", "0.5"), extendtick=None, extendlabel=0).defaultpart(0, 1.2, 1, 1),
                   [tick((0, 1), 0, 0), tick((1, 2), None, 1), tick((1, 1), 0, 0), tick((3, 2), None, 1), tick((2, 1), 0, 0)])
         PartEqual(linparter(labeldist="1", labels=("a", "b")).defaultpart(0, 1, 1, 1),
                   [tick((0, 1), 0, 0, "a"), tick((1, 1), 0, 0, "b")])
         PartEqual(linparter(labeldist=("1", "0.5"), labels=(("a", "c"), "b")).defaultpart(0, 1, 1, 1),
                   [tick((0, 1), 0, 0, "a"), tick((1, 2), None, 1, "b"), tick((1, 1), 0, 0, "c")])
         PartEqual(linparter(labeldist=("1", "0.5", "0.25"), labels=(("a", "e"), "c", ("b", "d"))).defaultpart(0, 1, 1, 1),
                   [tick((0, 1), 0, 0, "a"), tick((1, 4), None, 2, "b"), tick((1, 2), None, 1, "c"), tick((3, 4), None, 2, "d"), tick((1, 1), 0, 0, "e")])

class LogParterTestCase(unittest.TestCase):

     def testAll(self):
         PartEqual(logparter(tickpos=logparter.pre1exp, labelpos=()).defaultpart(1, 10, 1, 1),
                   [tick((1, 1), 0, None), tick((10, 1), 0, None)])
         PartEqual(logparter(tickpos=logparter.pre1exp, labelpos=()).defaultpart(1, 100, 1, 1),
                   [tick((1, 1), 0, None), tick((10, 1), 0, None), tick((100, 1), 0, None)])
         PartEqual(logparter(tickpos=logparter.pre1exp2, labelpos=()).defaultpart(1, 100, 1, 1),
                   [tick((1, 1), 0, None), tick((100, 1), 0, None)])
         PartEqual(logparter(tickpos=logparter.pre1to9exp, labelpos=()).defaultpart(1, 10, 1, 1),
                   [tick((1, 1), 0, None), tick((2, 1), 0, None), tick((3, 1), 0, None), tick((4, 1), 0, None), tick((5, 1), 0, None), tick((6, 1), 0, None), tick((7, 1), 0, None), tick((8, 1), 0, None), tick((9, 1), 0, None), tick((10, 1), 0, None)])
         PartEqual(logparter(tickpos=(logparter.pre1exp, logparter.pre1to9exp), labelpos=()).defaultpart(1, 10, 1, 1),
                   [tick((1, 1), 0, None), tick((2, 1), 1, None), tick((3, 1), 1, None), tick((4, 1), 1, None), tick((5, 1), 1, None), tick((6, 1), 1, None), tick((7, 1), 1, None), tick((8, 1), 1, None), tick((9, 1), 1, None), tick((10, 1), 0, None)])
         PartEqual(logparter(tickpos=(logparter.pre1exp, logparter.pre1to9exp)).defaultpart(1, 10, 1, 1),
                   [tick((1, 1), 0, 0), tick((2, 1), 1, None), tick((3, 1), 1, None), tick((4, 1), 1, None), tick((5, 1), 1, None), tick((6, 1), 1, None), tick((7, 1), 1, None), tick((8, 1), 1, None), tick((9, 1), 1, None), tick((10, 1), 0, 0)])


suite = unittest.TestSuite((unittest.makeSuite(LinParterTestCase, 'test'),
                            unittest.makeSuite(LogParterTestCase, 'test')))

if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite)

