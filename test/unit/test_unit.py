import sys
if sys.path[0] != "../..":
    sys.path.insert(0, "../..")

import unittest

import types
from pyx import *

class UnitTestCase(unittest.TestCase):

    def testTrueUnits(self):
        self.failUnlessAlmostEqual(unit.tom(unit.t_m*42), 42)
        self.failUnlessAlmostEqual(unit.tocm(unit.t_cm*42), 42)
        self.failUnlessAlmostEqual(unit.tomm(unit.t_mm*42), 42)
        self.failUnlessAlmostEqual(unit.toinch(unit.t_inch*42), 42)
        self.failUnlessAlmostEqual(unit.topt(unit.t_pt*42), 42)

    def testUserUnits(self):
        unit.set(uscale=2)
        self.failUnlessAlmostEqual(unit.tom(unit.m*42), 84)
        self.failUnlessAlmostEqual(unit.tocm(unit.cm*42), 84)
        self.failUnlessAlmostEqual(unit.tomm(unit.mm*42), 84)
        self.failUnlessAlmostEqual(unit.toinch(unit.inch*42), 84)
        self.failUnlessAlmostEqual(unit.topt(unit.pt*42), 84)
        unit.set(uscale=1)

    def testVisualUnits(self):
        unit.set(vscale=3)
        self.failUnlessAlmostEqual(unit.tom(unit.v_m*42), 126)
        self.failUnlessAlmostEqual(unit.tocm(unit.v_cm*42), 126)
        self.failUnlessAlmostEqual(unit.tomm(unit.v_mm*42), 126)
        self.failUnlessAlmostEqual(unit.toinch(unit.v_inch*42), 126)
        self.failUnlessAlmostEqual(unit.topt(unit.v_pt*42), 126)
        unit.set(vscale=1)

    def testWidthUnits(self):
        unit.set(wscale=4)
        self.failUnlessAlmostEqual(unit.tom(unit.w_m*42), 168)
        self.failUnlessAlmostEqual(unit.tocm(unit.w_cm*42), 168)
        self.failUnlessAlmostEqual(unit.tomm(unit.w_mm*42), 168)
        self.failUnlessAlmostEqual(unit.toinch(unit.w_inch*42), 168)
        self.failUnlessAlmostEqual(unit.topt(unit.w_pt*42), 168)
        unit.set(wscale=1)

    def testTeXUnits(self):
        unit.set(xscale=5)
        self.failUnlessAlmostEqual(unit.tom(unit.x_m*42), 210)
        self.failUnlessAlmostEqual(unit.tocm(unit.x_cm*42), 210)
        self.failUnlessAlmostEqual(unit.tomm(unit.x_mm*42), 210)
        self.failUnlessAlmostEqual(unit.toinch(unit.x_inch*42), 210)
        self.failUnlessAlmostEqual(unit.topt(unit.x_pt*42), 210)
        unit.set(xscale=1)

    def testMixedUnits(self):
        unit.set(uscale=2, vscale=3, wscale=4, xscale=5)
        self.failUnlessAlmostEqual(unit.tom(42*unit.t_m + 42*unit.m + 42*unit.v_m + 42*unit.w_m + 42*unit.x_m), 630)
        self.failUnlessAlmostEqual(unit.tocm(42*unit.t_cm + 42*unit.cm + 42*unit.v_cm + 42*unit.w_cm + 42*unit.x_cm), 630)
        self.failUnlessAlmostEqual(unit.toinch(42*unit.t_inch + 42*unit.inch + 42*unit.v_inch + 42*unit.w_inch + 42*unit.x_inch), 630)
        self.failUnlessAlmostEqual(unit.topt(42*unit.t_pt + 42*unit.pt + 42*unit.v_pt + 42*unit.w_pt + 42*unit.x_pt), 630)
        unit.set(uscale=1, vscale=1, wscale=1, xscale=1)

    def testCompareUnits(self):
        assert unit.cm*41 < unit.cm*42, "comparision error"
        assert unit.cm*42 == unit.cm*42, "numbers should be equal (might be unstable)"
        assert unit.cm*43 > unit.cm*42, "comparision error"
        assert unit.cm*41 < 42, "comparision error"
        assert unit.cm*42 == 42, "numbers should be equal (might be unstable)"
        assert unit.cm*43 > 42, "comparision error"
        assert 42 > unit.cm*41, "comparision error"
        assert 42 == unit.cm*42, "numbers should be equal (might be unstable)"
        assert 42 < unit.cm*43, "comparision error"


if __name__ == "__main__":
    unittest.main()
