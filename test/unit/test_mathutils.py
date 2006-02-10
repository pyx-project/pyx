import sys
if sys.path[0] != "../..":
    sys.path.insert(0, "../..")

import unittest, random
# its certainly not a good practice to use random numbers, but its much better than nothing ...
# note that the checks might fail in very rare cases, but we've stabelized it quite a bit
# TODO: make a real testsuite (with known solutions)

from pyx import mathutils

class PolynomTestCase(unittest.TestCase):

    maxOrder = 4
    triesPerOrder = 100

    def polyValue(self, x, cs):
        if len(cs) == 0:
            return 0
        return x * self.polyValue(x, cs[:-1]) + cs[-1]

    def derivativeValue(self, x, cs):
        cs = [(len(cs)-i-1)*c for i, c in enumerate(cs[:-1])]
        # note that we do not really return the derivative
        # (we only use it to stablelize the root check)
        return max(abs(self.polyValue(x, cs)), 1)

    def testRandom(self):
        r = []
        for order in range(self.maxOrder+1):
            maxroot1 = maxroot2 = maxdist = 0
            for count in range(self.triesPerOrder):
                cs = [100*random.random()-50 for i in range(order+1)]
                if count < 10:
                    # check for proper handling of highest coefficient equals 0
                    cs[0] = 0
                roots1 = mathutils.realpolyroots(*cs)
                # different from PyX itself this test will also use
                # realpolyroot_eigenvalue, which needs the numeric package
                roots2 = mathutils.realpolyroots_eigenvalue(*cs)
                # check for roots being roots (such a test is in general very
                # problematic, but the division by the derivative makes it
                # reasonably stable)
                for root in roots1 + roots2:
                    self.failUnlessAlmostEqual(0, self.polyValue(root, cs)/self.derivativeValue(root, cs), 5)
                roots1.sort()
                roots2.sort()
                # compare the two ways of calculating roots
                # (for random numbers degenerate cases are unlikely;
                # however, they could generate problems in this simplistic check)
                self.failUnlessEqual(len(roots1), len(roots2))
                for root1, root2 in zip(roots1, roots2):
                    self.failUnlessAlmostEqual(root1, root2, 5)

if __name__ == "__main__":
    unittest.main()
