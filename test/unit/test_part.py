import unittest

from pyx import *
from pyx.graph import frac, tick, manualpart, linpart, logpart


def PartEqual(part1, part2):
     assert len(part1) == len(part2), "partitions have different length"
     for tick1, tick2 in zip(part1, part2):
         assert tick1 == tick2, "position is different"
         assert tick1.ticklevel == tick2.ticklevel, "ticklevel is different"
         assert tick1.labellevel == tick2.labellevel, "labellevel is different"
         assert tick1.label == tick2.label, "label is different"


class ManualPartTestCase(unittest.TestCase):

     def testFrac(self):
         PartEqual(manualpart(tickpos=frac((1, 1)), labelpos=()).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), 0, None)])
         PartEqual(manualpart(tickpos=frac((2, 2)), labelpos=()).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), 0, None)])
         PartEqual(manualpart(tickpos="1", labelpos=()).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), 0, None)])
         PartEqual(manualpart(tickpos="1/1", labelpos=()).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), 0, None)])
         PartEqual(manualpart(tickpos="2/2", labelpos=()).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), 0, None)])
         PartEqual(manualpart(tickpos="0.5/0.5", labelpos=()).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), 0, None)])

     def testTicks(self):
         PartEqual(manualpart(tickpos="1", labelpos=()).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), 0, None)])
         PartEqual(manualpart(tickpos=("1",), labelpos=()).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), 0, None)])
         PartEqual(manualpart(tickpos=("1", "2"), labelpos=()).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), 0, None), tick((2, 1), 0, None)])
         PartEqual(manualpart(tickpos=("2", "1"), labelpos=()).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), 0, None), tick((2, 1), 0, None)])
         try:
             manualpart(tickpos=("1", "1"), labelpos=()).defaultpart(0, 0, 1, 1)
             raise Exception("exception for duplicate entry expected")
         except ValueError, msg:
             assert msg != "duplicate entry found"
         try:
             manualpart(tickpos=("1", "2", "1"), labelpos=()).defaultpart(0, 0, 1, 1)
             raise Exception("exception for duplicate entry expected")
         except ValueError, msg:
             assert msg != "duplicate entry found"

     def testLabels(self):
         PartEqual(manualpart(labelpos="1", tickpos=()).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), None, 0)])
         PartEqual(manualpart(labelpos=("1",), tickpos=()).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), None, 0)])
         PartEqual(manualpart(labelpos=("1", "2"), tickpos=()).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), None, 0), tick((2, 1), None, 0)])
         PartEqual(manualpart(labelpos=("2", "1"), tickpos=()).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), None, 0), tick((2, 1), None, 0)])
         try:
             manualpart(labelpos=("1", "1"), tickpos=()).defaultpart(0, 0, 1, 1)
             raise Exception("exception for duplicate entry expected")
         except ValueError, msg:
             assert msg != "duplicate entry found"
         try:
             manualpart(labelpos=("1", "2", "1"), tickpos=()).defaultpart(0, 0, 1, 1)
             raise Exception("exception for duplicate entry expected")
         except ValueError, msg:
             assert msg != "duplicate entry found"

     def testSubTicks(self):
         PartEqual(manualpart(tickpos=((), "1"), labelpos=()).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), 1, None)])
         PartEqual(manualpart(tickpos=((), ("1",)), labelpos=()).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), 1, None)])
         PartEqual(manualpart(tickpos=((), ("1", "2")), labelpos=()).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), 1, None), tick((2, 1), 1, None)])
         PartEqual(manualpart(tickpos=((), ("2", "1")), labelpos=()).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), 1, None), tick((2, 1), 1, None)])
         try:
             manualpart(tickpos=((), ("1", "1")), labelpos=()).defaultpart(0, 0, 1, 1)
             raise Exception("exception for duplicate entry expected")
         except ValueError, msg:
             assert msg != "duplicate entry found"
         try:
             manualpart(tickpos=((), ("1", "2", "1")), labelpos=()).defaultpart(0, 0, 1, 1)
             raise Exception("exception for duplicate entry expected")
         except ValueError, msg:
             assert msg != "duplicate entry found"

     def testSubLabels(self):
         PartEqual(manualpart(labelpos=((), "1"), tickpos=()).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), None, 1)])
         PartEqual(manualpart(labelpos=((), ("1",)), tickpos=()).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), None, 1)])
         PartEqual(manualpart(labelpos=((), ("1", "2")), tickpos=()).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), None, 1), tick((2, 1), None, 1)])
         PartEqual(manualpart(labelpos=((), ("2", "1")), tickpos=()).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), None, 1), tick((2, 1), None, 1)])
         try:
             manualpart(labelpos=((), ("1", "1")), tickpos=()).defaultpart(0, 0, 1, 1)
             raise Exception("exception for duplicate entry expected")
         except ValueError, msg:
             assert msg != "duplicate entry found"
         try:
             manualpart(labelpos=((), ("1", "2", "1")), tickpos=()).defaultpart(0, 0, 1, 1)
             raise Exception("exception for duplicate entry expected")
         except ValueError, msg:
             assert msg != "duplicate entry found"

     def testTicksSubticks(self):
         PartEqual(manualpart(tickpos=(("1", "2"), ("1", "2")), labelpos=()).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), 0, None), tick((2, 1), 0, None)])
         PartEqual(manualpart(tickpos=(("1", "2"), ("3", "4")), labelpos=()).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), 0, None), tick((2, 1), 0, None), tick((3, 1), 1, None), tick((4, 1), 1, None)])
         PartEqual(manualpart(tickpos=(("1", "2"), ("3", "2")), labelpos=()).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), 0, None), tick((2, 1), 0, None), tick((3, 1), 1, None)])
         PartEqual(manualpart(tickpos=(("1", "3"), ("2", "4")), labelpos=()).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), 0, None), tick((2, 1), 1, None), tick((3, 1), 0, None), tick((4, 1), 1, None)])
         PartEqual(manualpart(tickpos=(("1", "3"), ("2", "4", "1", "3")), labelpos=()).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), 0, None), tick((2, 1), 1, None), tick((3, 1), 0, None), tick((4, 1), 1, None)])

     def testTicksSubsubticks(self):
         PartEqual(manualpart(tickpos=(("1", "2"), (), ("1", "2")), labelpos=()).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), 0, None), tick((2, 1), 0, None)])
         PartEqual(manualpart(tickpos=(("1", "2"), (), ("3", "4")), labelpos=()).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), 0, None), tick((2, 1), 0, None), tick((3, 1), 2, None), tick((4, 1), 2, None)])
         PartEqual(manualpart(tickpos=(("1", "2"), (), ("3", "2")), labelpos=()).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), 0, None), tick((2, 1), 0, None), tick((3, 1), 2, None)])
         PartEqual(manualpart(tickpos=(("1", "3"), (), ("2", "4")), labelpos=()).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), 0, None), tick((2, 1), 2, None), tick((3, 1), 0, None), tick((4, 1), 2, None)])
         PartEqual(manualpart(tickpos=(("1", "3"), (), ("2", "4", "1", "3")), labelpos=()).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), 0, None), tick((2, 1), 2, None), tick((3, 1), 0, None), tick((4, 1), 2, None)])
         PartEqual(manualpart(tickpos=(("1", "3"), "2", ("2", "4", "1", "3")), labelpos=()).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), 0, None), tick((2, 1), 1, None), tick((3, 1), 0, None), tick((4, 1), 2, None)])

     def testTickLabels(self):
         PartEqual(manualpart(tickpos="1").defaultpart(0, 0, 1, 1),
                   [tick((1, 1), 0, 0)])
         PartEqual(manualpart(tickpos=("1",)).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), 0, 0)])
         PartEqual(manualpart(tickpos=("1", "2")).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), 0, 0), tick((2, 1), 0, 0)])
         PartEqual(manualpart(tickpos=("2", "1")).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), 0, 0), tick((2, 1), 0, 0)])


     def testText(self):
         PartEqual(manualpart(labelpos="1", tickpos=(), labels="a").defaultpart(0, 0, 1, 1),
                   [tick((1, 1), None, 0, "a")])
         PartEqual(manualpart(labelpos="1", tickpos=(), labels=("a",)).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), None, 0, "a")])
         PartEqual(manualpart(labelpos=("1", "2"), tickpos=(), labels=("a", "b")).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), None, 0, "a"), tick((2, 1), None, 0, "b")])
         PartEqual(manualpart(labelpos=("2", "1"), tickpos=(), labels=("a", "b")).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), None, 0, "a"), tick((2, 1), None, 0, "b")])
         try:
             manualpart(labelpos=("1"), tickpos=(), labels=("a", "b")).defaultpart(0, 0, 1, 1)
             raise Exception("exception for wrong sequence length of labels expected")
         except IndexError, msg:
             assert msg != "wrong sequence length of labels"

     def testSubtextsAndSubLabelTicks(self):
         PartEqual(manualpart(labelpos=(("1", "2"), ("1", "2")), labels=("a", "b")).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), 0, 0, "a"), tick((2, 1), 0, 0, "b")])
         PartEqual(manualpart(labelpos=(("1", "2"), ("3", "4")), labels=("a", "b")).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), 0, 0, "a"), tick((2, 1), 0, 0, "b"), tick((3, 1), None, 1), tick((4, 1), None, 1)])
         PartEqual(manualpart(labelpos=(("1",), ("2", "3")), labels=(("a",), ("b", "c"))).defaultpart(0, 0, 1, 1),
                   [tick((1, 1), 0, 0, "a"), tick((2, 1), None, 1, "b"), tick((3, 1), None, 1, "c")])


class LinPartTestCase(unittest.TestCase):

     def testAll(self):
         PartEqual(linpart(tickdist="1", labeldist=()).defaultpart(0, 1, 1, 1),
                   [tick((0, 1), 0, None), tick((1, 1), 0, None)])
         PartEqual(linpart(tickdist=("1", "0.5"), labeldist=()).defaultpart(0, 1, 1, 1),
                   [tick((0, 1), 0, None), tick((1, 2), 1, None), tick((1, 1), 0, None)])
         PartEqual(linpart(tickdist=("1", "0.5", "0.25"), labeldist=()).defaultpart(0, 1, 1, 1),
                   [tick((0, 1), 0, None), tick((1, 4), 2, None), tick((1, 2), 1, None), tick((3, 4), 2, None), tick((1, 1), 0, None)])
         PartEqual(linpart(tickdist=("1", "0.5"), labeldist=(), extendtick=None).defaultpart(0, 1.5, 1, 1),
                   [tick((0, 1), 0, None), tick((1, 2), 1, None), tick((1, 1), 0, None), tick((3, 2), 1, None)])
         PartEqual(linpart(tickdist=("1", "0.5"), labeldist=(), extendtick=1).defaultpart(0, 1.2, 1, 1),
                   [tick((0, 1), 0, None), tick((1, 2), 1, None), tick((1, 1), 0, None), tick((3, 2), 1, None)])
         PartEqual(linpart(tickdist=("1", "0.5"), labeldist=(), extendtick=0).defaultpart(0, 1.2, 1, 1),
                   [tick((0, 1), 0, None), tick((1, 2), 1, None), tick((1, 1), 0, None), tick((3, 2), 1, None), tick((2, 1), 0, None)])
         PartEqual(linpart(labeldist="1", tickdist=()).defaultpart(0, 1, 1, 1),
                   [tick((0, 1), None, 0), tick((1, 1), None, 0)])
         PartEqual(linpart(labeldist=("1", "0.5"), tickdist=()).defaultpart(0, 1, 1, 1),
                   [tick((0, 1), None, 0), tick((1, 2), None, 1), tick((1, 1), None, 0)])
         PartEqual(linpart(labeldist=("1", "0.5", "0.25"), tickdist=()).defaultpart(0, 1, 1, 1),
                   [tick((0, 1), None, 0), tick((1, 4), None, 2), tick((1, 2), None, 1), tick((3, 4), None, 2), tick((1, 1), None, 0)])
         PartEqual(linpart(labeldist=("1", "0.5"), tickdist=(), extendlabel=None).defaultpart(0, 1.5, 1, 1),
                   [tick((0, 1), None, 0), tick((1, 2), None, 1), tick((1, 1), None, 0), tick((3, 2), None, 1)])
         PartEqual(linpart(labeldist=("1", "0.5"), tickdist=(), extendlabel=1).defaultpart(0, 1.2, 1, 1),
                   [tick((0, 1), None, 0), tick((1, 2), None, 1), tick((1, 1), None, 0), tick((3, 2), None, 1)])
         PartEqual(linpart(labeldist=("1", "0.5"), tickdist=(), extendlabel=0).defaultpart(0, 1.2, 1, 1),
                   [tick((0, 1), None, 0), tick((1, 2), None, 1), tick((1, 1), None, 0), tick((3, 2), None, 1), tick((2, 1), None, 0)])
         PartEqual(linpart(tickdist="1").defaultpart(0, 1, 1, 1),
                   [tick((0, 1), 0, 0), tick((1, 1), 0, 0)])
         PartEqual(linpart(tickdist=("1", "0.5")).defaultpart(0, 1, 1, 1),
                   [tick((0, 1), 0, 0), tick((1, 2), 1, None), tick((1, 1), 0, 0)])
         PartEqual(linpart(tickdist=("1", "0.5", "0.25")).defaultpart(0, 1, 1, 1),
                   [tick((0, 1), 0, 0), tick((1, 4), 2, None), tick((1, 2), 1, None), tick((3, 4), 2, None), tick((1, 1), 0, 0)])
         PartEqual(linpart(tickdist=("1", "0.5"), extendtick=None).defaultpart(0, 1.5, 1, 1),
                   [tick((0, 1), 0, 0), tick((1, 2), 1, None), tick((1, 1), 0, 0), tick((3, 2), 1, None)])
         PartEqual(linpart(tickdist=("1", "0.5"), extendtick=1).defaultpart(0, 1.2, 1, 1),
                   [tick((0, 1), 0, 0), tick((1, 2), 1, None), tick((1, 1), 0, 0), tick((3, 2), 1, None)])
         PartEqual(linpart(tickdist=("1", "0.5"), extendtick=0).defaultpart(0, 1.2, 1, 1),
                   [tick((0, 1), 0, 0), tick((1, 2), 1, None), tick((1, 1), 0, 0), tick((3, 2), 1, None), tick((2, 1), 0, 0)])
         PartEqual(linpart(labeldist="1").defaultpart(0, 1, 1, 1),
                   [tick((0, 1), 0, 0), tick((1, 1), 0, 0)])
         PartEqual(linpart(labeldist=("1", "0.5")).defaultpart(0, 1, 1, 1),
                   [tick((0, 1), 0, 0), tick((1, 2), None, 1), tick((1, 1), 0, 0)])
         PartEqual(linpart(labeldist=("1", "0.5", "0.25")).defaultpart(0, 1, 1, 1),
                   [tick((0, 1), 0, 0), tick((1, 4), None, 2), tick((1, 2), None, 1), tick((3, 4), None, 2), tick((1, 1), 0, 0)])
         PartEqual(linpart(labeldist=("1", "0.5"), extendtick=None).defaultpart(0, 1.5, 1, 1),
                   [tick((0, 1), 0, 0), tick((1, 2), None, 1), tick((1, 1), 0, 0), tick((3, 2), None, 1)])
         PartEqual(linpart(labeldist=("1", "0.5"), extendtick=None, extendlabel=1).defaultpart(0, 1.2, 1, 1),
                   [tick((0, 1), 0, 0), tick((1, 2), None, 1), tick((1, 1), 0, 0), tick((3, 2), None, 1)])
         PartEqual(linpart(labeldist=("1", "0.5"), extendtick=None, extendlabel=0).defaultpart(0, 1.2, 1, 1),
                   [tick((0, 1), 0, 0), tick((1, 2), None, 1), tick((1, 1), 0, 0), tick((3, 2), None, 1), tick((2, 1), 0, 0)])
         PartEqual(linpart(labeldist="1", labels=("a", "b")).defaultpart(0, 1, 1, 1),
                   [tick((0, 1), 0, 0, "a"), tick((1, 1), 0, 0, "b")])
         PartEqual(linpart(labeldist=("1", "0.5"), labels=(("a", "c"), "b")).defaultpart(0, 1, 1, 1),
                   [tick((0, 1), 0, 0, "a"), tick((1, 2), None, 1, "b"), tick((1, 1), 0, 0, "c")])
         PartEqual(linpart(labeldist=("1", "0.5", "0.25"), labels=(("a", "e"), "c", ("b", "d"))).defaultpart(0, 1, 1, 1),
                   [tick((0, 1), 0, 0, "a"), tick((1, 4), None, 2, "b"), tick((1, 2), None, 1, "c"), tick((3, 4), None, 2, "d"), tick((1, 1), 0, 0, "e")])

class LogPartTestCase(unittest.TestCase):

     def testAll(self):
         PartEqual(logpart(tickpos=logpart.pre1exp, labelpos=()).defaultpart(1, 10, 1, 1),
                   [tick((1, 1), 0, None), tick((10, 1), 0, None)])
         PartEqual(logpart(tickpos=logpart.pre1exp, labelpos=()).defaultpart(1, 100, 1, 1),
                   [tick((1, 1), 0, None), tick((10, 1), 0, None), tick((100, 1), 0, None)])
         PartEqual(logpart(tickpos=logpart.pre1exp2, labelpos=()).defaultpart(1, 100, 1, 1),
                   [tick((1, 1), 0, None), tick((100, 1), 0, None)])
         PartEqual(logpart(tickpos=logpart.pre1to9exp, labelpos=()).defaultpart(1, 10, 1, 1),
                   [tick((1, 1), 0, None), tick((2, 1), 0, None), tick((3, 1), 0, None), tick((4, 1), 0, None), tick((5, 1), 0, None), tick((6, 1), 0, None), tick((7, 1), 0, None), tick((8, 1), 0, None), tick((9, 1), 0, None), tick((10, 1), 0, None)])
         PartEqual(logpart(tickpos=(logpart.pre1exp, logpart.pre1to9exp), labelpos=()).defaultpart(1, 10, 1, 1),
                   [tick((1, 1), 0, None), tick((2, 1), 1, None), tick((3, 1), 1, None), tick((4, 1), 1, None), tick((5, 1), 1, None), tick((6, 1), 1, None), tick((7, 1), 1, None), tick((8, 1), 1, None), tick((9, 1), 1, None), tick((10, 1), 0, None)])
         PartEqual(logpart(tickpos=(logpart.pre1exp, logpart.pre1to9exp)).defaultpart(1, 10, 1, 1),
                   [tick((1, 1), 0, 0), tick((2, 1), 1, None), tick((3, 1), 1, None), tick((4, 1), 1, None), tick((5, 1), 1, None), tick((6, 1), 1, None), tick((7, 1), 1, None), tick((8, 1), 1, None), tick((9, 1), 1, None), tick((10, 1), 0, 0)])


suite = unittest.TestSuite((unittest.makeSuite(ManualPartTestCase, 'test'),
                            unittest.makeSuite(LinPartTestCase, 'test'),
                            unittest.makeSuite(LogPartTestCase, 'test')))

if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite)

