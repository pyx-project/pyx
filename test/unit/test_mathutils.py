import sys
if sys.path[0] != "../..":
    sys.path.insert(0, "../..")

import unittest

from pyx import mathutils

class PolynomTestCase(unittest.TestCase):

    def makePolyRoots(self, *rs):
        # creates a polynom with zeros rs
        if len(rs) == 1:
            return [1, -rs[0]]
        cs = self.makePolyRoots(*rs[1:])
        return [cim1-rs[0]*ci for cim1, ci in zip(cs+[0], [0]+cs)]

    def makePolyNonroots(self, cs, a, b):
        # adds a factor ((x-a)**2 + b) to the polynom with coefficients cs
        # which can be used (for b > 0) to construct polynoms with complex roots
        return [cim2-2*a*cim1+(a*a+b)*ci for cim2, cim1, ci in zip(cs+[0, 0], [0]+cs+[0], [0, 0]+cs)]

    def compareRoots(self, found, should):
        found.sort()
        # we remove degeneracies in found, since we do *not* claim to properly handle degeneracies
        i = 1
        while len(found) > i:
            if found[i] - found[i-1] < 1e-7:
                del found[i]
            else:
                i += 1
        self.assertEqual(len(found), len(should))
        for r1, r2 in zip(found, should):
            self.assertAlmostEqual(r1, r2)

    def testConstant(self):
        self.compareRoots(mathutils.realpolyroots(1), [])
        self.compareRoots(mathutils.realpolyroots(0), [0])

    def testLinear(self):
        self.compareRoots(mathutils.realpolyroots(0, 1), [])
        self.compareRoots(mathutils.realpolyroots(0, 0), [0])
        self.compareRoots(mathutils.realpolyroots(1, 1), [-1])
        self.compareRoots(mathutils.realpolyroots(2, 0), [0])
        self.compareRoots(mathutils.realpolyroots(4, -1), [0.25])
        self.compareRoots(mathutils.realpolyroots(*self.makePolyRoots(1.7)), [1.7])
        self.compareRoots(mathutils.realpolyroots(*self.makePolyRoots(-42)), [-42])

    def testQuadratic(self):
        self.compareRoots(mathutils.realpolyroots(0, 1, 1), [-1])
        self.compareRoots(mathutils.realpolyroots(1, -4, 3), [1, 3])
        self.compareRoots(mathutils.realpolyroots(*self.makePolyRoots(1.7, 2.3)), [1.7, 2.3])
        self.compareRoots(mathutils.realpolyroots(*self.makePolyRoots(2.3, 1.7)), [1.7, 2.3])
        self.compareRoots(mathutils.realpolyroots(*self.makePolyRoots(1.7, -2.3)), [-2.3, 1.7])
        self.compareRoots(mathutils.realpolyroots(*self.makePolyRoots(-2.3, 1.7)), [-2.3, 1.7])
        self.compareRoots(mathutils.realpolyroots(*self.makePolyRoots(1.7, 1.7)), [1.7])
        self.compareRoots(mathutils.realpolyroots(*self.makePolyNonroots([1], 1.7, 1)), [])
        self.compareRoots(mathutils.realpolyroots(*self.makePolyNonroots([1], 1.7, -1)), [0.7, 2.7])
        self.compareRoots(mathutils.realpolyroots(*self.makePolyNonroots([1], 1.7, -4)), [-0.3, 3.7])

    def testCubic(self):
        self.compareRoots(mathutils.realpolyroots(0, 0, 0, 1), [])
        self.compareRoots(mathutils.realpolyroots(0, 0, 1, 1), [-1])
        self.compareRoots(mathutils.realpolyroots(0, 1, -4, 3), [1, 3])
        self.compareRoots(mathutils.realpolyroots(1, -9, 23, -15), [1, 3, 5])
        self.compareRoots(mathutils.realpolyroots(*self.makePolyRoots(1.7, 2.3, 4.2)), [1.7, 2.3, 4.2])
        self.compareRoots(mathutils.realpolyroots(*self.makePolyRoots(1.7, -2.3, 4.2)), [-2.3, 1.7, 4.2])
        self.compareRoots(mathutils.realpolyroots(*self.makePolyRoots(1.7, -2.3, -4.2)), [-4.2, -2.3, 1.7])
        self.compareRoots(mathutils.realpolyroots(*self.makePolyNonroots(self.makePolyRoots(1.7), 2.3, 1)), [1.7])
        self.compareRoots(mathutils.realpolyroots(*self.makePolyNonroots(self.makePolyRoots(1.7), 2.3, -1)), [1.3, 1.7, 3.3])
        self.compareRoots(mathutils.realpolyroots(*self.makePolyNonroots(self.makePolyRoots(1.7), 2.3, -4)), [0.3, 1.7, 4.3])

    def testQuartic(self):
        self.compareRoots(mathutils.realpolyroots(0, 0, 0, 0, 1), [])
        self.compareRoots(mathutils.realpolyroots(0, 0, 0, 1, 1), [-1])
        self.compareRoots(mathutils.realpolyroots(0, 1, -9, 23, -15), [1, 3, 5])
        self.compareRoots(mathutils.realpolyroots(1, -16, 86, -176, 105), [1, 3, 5, 7])
        self.compareRoots(mathutils.realpolyroots(*self.makePolyRoots(1.7, 2.3, 4.2, 13)), [1.7, 2.3, 4.2, 13])
        self.compareRoots(mathutils.realpolyroots(*self.makePolyRoots(1.7, -2.3, 4.2, 13)), [-2.3, 1.7, 4.2, 13])
        self.compareRoots(mathutils.realpolyroots(*self.makePolyRoots(1.7, -2.3, -4.2, 13)), [-4.2, -2.3, 1.7, 13])
        self.compareRoots(mathutils.realpolyroots(*self.makePolyNonroots(self.makePolyRoots(1.7, 2.3), 4.2, 1)), [1.7, 2.3])
        self.compareRoots(mathutils.realpolyroots(*self.makePolyNonroots(self.makePolyRoots(1.7, 2.3), 4.2, -1)), [1.7, 2.3, 3.2, 5.2])
        self.compareRoots(mathutils.realpolyroots(*self.makePolyNonroots(self.makePolyRoots(1.7, 2.3), 4.2, -4)), [1.7, 2.2, 2.3, 6.2])
        self.compareRoots(mathutils.realpolyroots(*self.makePolyNonroots(self.makePolyRoots(1.7, -2.3), 4.2, -1)), [-2.3, 1.7, 3.2, 5.2])
        self.compareRoots(mathutils.realpolyroots(*self.makePolyNonroots(self.makePolyRoots(1.7, -2.3), 4.2, -4)), [-2.3, 1.7, 2.2, 6.2])
        self.compareRoots(mathutils.realpolyroots(*self.makePolyNonroots(self.makePolyNonroots([1], 1.7, 1), 2.3, 1)), [])
        self.compareRoots(mathutils.realpolyroots(*self.makePolyNonroots(self.makePolyNonroots([1], 1.7, 1), 2.3, -1)), [1.3, 3.3])


if __name__ == "__main__":
    unittest.main()
