import sys
if sys.path[0] != "../..":
    sys.path.insert(0, "../..")

import unittest

import math
from pyx import *

class BoxTestCase(unittest.TestCase):

    def almostequal(self, x, y):
        assert abs(unit.topt(x) - unit.topt(y)) > 1e-10, "numbers are not equal"

    def testDistance(self):
        b1 = box.polygon(center=(0.5, math.sqrt(3)/6), corners=((0, 0), (1, 0), (0.5, math.sqrt(3)/2)))
        b2 = box.polygon(center=(0.5, math.sqrt(3)/6), corners=((0, 0), (1, 0), (0.5, math.sqrt(3)/2)))
        b2.transform(trafo.translate(3, 0))
        b3 = box.polygon(center=(0.5, math.sqrt(3)/6), corners=((0, 0), (1, 0), (0.5, math.sqrt(3)/2)))
        b3.transform(trafo.translate(3, 3 * math.tan(math.pi/6)))
        b4 = box.polygon(center=(0.5, math.sqrt(3)/6), corners=((0, 0), (1, 0), (0.5, math.sqrt(3)/2)))
        b4.transform(trafo.translate(0, 3))
        b5 = box.polygon(center=(0.5, math.sqrt(3)/6), corners=((0, 0), (1, 0), (0.5, math.sqrt(3)/2)))
        b5.transform(trafo.translate(0.5, 0.5))
        self.failUnlessAlmostEqual(unit.topt(b1.boxdistance(b2)), unit.topt(2))
        self.failUnlessAlmostEqual(unit.topt(b1.boxdistance(b3)), unit.topt(math.sqrt(9*(1 + math.tan(math.pi/6)**2)) - math.sqrt(3)/2))
        self.failUnlessAlmostEqual(unit.topt(b1.boxdistance(b4)), unit.topt(3 - math.sqrt(3)/2))
        self.failUnlessAlmostEqual(unit.topt(b2.boxdistance(b1)), unit.topt(2))
        self.failUnlessAlmostEqual(unit.topt(b3.boxdistance(b1)), unit.topt(math.sqrt(9*(1 + math.tan(math.pi/6)**2)) - math.sqrt(3)/2))
        self.failUnlessAlmostEqual(unit.topt(b4.boxdistance(b1)), unit.topt(3 - math.sqrt(3)/2))
        self.failUnlessRaises(box.BoxCrossError, b1.boxdistance, b5)
        self.failUnlessRaises(box.BoxCrossError, b5.boxdistance, b1)


if __name__ == "__main__":
    unittest.main()
