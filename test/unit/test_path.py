import sys
if sys.path[0] != "../..":
    sys.path.insert(0, "../..")

import unittest

from pyx import *
from pyx.path import *

epsilon = 1e-5
def isEqual(l1, l2):
    return abs(unit.topt(l1-l2))<epsilon


class NormpathTestCase(unittest.TestCase):
    def testsplit(self):
        p = normsubpath([normline(0, -1, 1, 0.1),
                         normline(1, 0.1, 2, -1),
                         normline(2, -1, 1, -1), 
                         normline(1, -1, 1, 1)])

        self.failUnlessEqual(len(p.split([0.9, 1.1, 3.5])), 4)


#        p = path(moveto(0,0), lineto(1,0), moveto(2,0), lineto(3,0))
#        np = normpath(p)
#
#        # one split parameter
#        sp = np.split([0])
#        assert len(sp)==2 and sp[0] is None and isEqual(sp[1].arclen(), 2)
#        
#        sp = np.split([0.5])
#        assert len(sp)==2 and isEqual(sp[0].arclen(), 0.5) and isEqual(sp[1].arclen(), 1.5)
#        
#        sp = np.split([1])
#        assert len(sp)==2 and isEqual(sp[0].arclen(), 1) and isEqual(sp[1].arclen(), 1)
#        
#        sp = np.split([1.5])
#        assert len(sp)==2 and isEqual(sp[0].arclen(), 1.5) and isEqual(sp[1].arclen(), 0.5)
#        
#        sp = np.split([2])
#        assert len(sp)==2 and isEqual(sp[0].arclen(), 2) and sp[1] is None
#
#        # two split parameters
#        sp = np.split([0, 0.5])
#        assert len(sp)==3 and sp[0] is None and isEqual(sp[1].arclen(), 0.5) and isEqual(sp[2].arclen(), 1.5)
#        
#        sp = np.split([0, 1])
#        assert len(sp)==3 and sp[0] is None and isEqual(sp[1].arclen(), 1) and isEqual(sp[2].arclen(), 1)
#
#        sp = np.split([0, 1.5])
#        assert len(sp)==3 and sp[0] is None and isEqual(sp[1].arclen(), 1.5) and isEqual(sp[2].arclen(), 0.5)
#        
#        sp = np.split([0, 2])
#        assert len(sp)==3 and sp[0] is None and isEqual(sp[1].arclen(), 2) and sp[2] is None
#
#        sp = np.split([0.5, 1])
#        assert len(sp)==3 and isEqual(sp[0].arclen(), 0.5) and isEqual(sp[1].arclen(), 0.5) and isEqual(sp[2].arclen(), 1)
#
#        sp = np.split([0.5, 1.5])
#        assert len(sp)==3 and isEqual(sp[0].arclen(), 0.5) and isEqual(sp[1].arclen(), 1) and isEqual(sp[2].arclen(), 0.5)
#
#        sp = np.split([0.5, 2])
#        assert len(sp)==3 and isEqual(sp[0].arclen(), 0.5) and isEqual(sp[1].arclen(), 1.5) and sp[2] is None
#
#        sp = np.split([1, 1.5])
#        assert len(sp)==3 and isEqual(sp[0].arclen(), 1) and isEqual(sp[1].arclen(), 0.5) and isEqual(sp[2].arclen(), 0.5)
#
#        sp = np.split([1, 2])
#        assert len(sp)==3 and isEqual(sp[0].arclen(), 1) and isEqual(sp[1].arclen(), 1) and sp[2] is None
#
#        sp = np.split([1.5, 2])
#        assert len(sp)==3 and isEqual(sp[0].arclen(), 1.5) and isEqual(sp[1].arclen(), 0.5) and sp[2] is None
#        
#        # three split parameters
#        sp = np.split([0, 0.5, 1])
#        assert len(sp)==4 and sp[0] is None and isEqual(sp[1].arclen(), 0.5) and isEqual(sp[2].arclen(), 0.5) and isEqual(sp[3].arclen(), 1)
#
#        sp = np.split([0, 0.5, 1.5])
#        assert len(sp)==4 and sp[0] is None and isEqual(sp[1].arclen(), 0.5) and isEqual(sp[2].arclen(), 1) and isEqual(sp[3].arclen(), 0.5)
#
#        sp = np.split([0, 0.5, 2])
#        assert len(sp)==4 and sp[0] is None and isEqual(sp[1].arclen(), 0.5) and isEqual(sp[2].arclen(), 1.5) and sp[3] is None
#
#        sp = np.split([0, 1, 1.5])
#        assert len(sp)==4 and sp[0] is None and isEqual(sp[1].arclen(), 1) and isEqual(sp[2].arclen(), 0.5) and isEqual(sp[3].arclen(), 0.5)
#
#        sp = np.split([0, 1, 2])
#        assert len(sp)==4 and sp[0] is None and isEqual(sp[1].arclen(), 1) and isEqual(sp[2].arclen(), 1) and sp[3] is None
#        
#
#        sp = np.split([0, 1.5, 2])
#        assert len(sp)==4 and sp[0] is None and isEqual(sp[1].arclen(), 1.5) and isEqual(sp[2].arclen(), 0.5) and sp[3] is None
#
#        sp = np.split([0.5, 1, 1.5])
#        assert len(sp)==4 and isEqual(sp[0].arclen(), 0.5) and isEqual(sp[1].arclen(), 0.5) and isEqual(sp[2].arclen(), 0.5) and isEqual(sp[3].arclen(), 0.5)
#
#        sp = np.split([0.5, 1.5, 2])
#        assert len(sp)==4 and isEqual(sp[0].arclen(), 0.5) and isEqual(sp[1].arclen(), 1) and isEqual(sp[2].arclen(), 0.5) and sp[3] is None
#
#        sp = np.split([1, 1.5, 2])
#        assert len(sp)==4 and isEqual(sp[0].arclen(), 1) and isEqual(sp[1].arclen(), 0.5) and isEqual(sp[2].arclen(), 0.5) and sp[3] is None
#
#
#        # four split parameters
#        sp = np.split([0, 0.5, 1, 1.5])
#        assert len(sp)==5 and sp[0] is None and isEqual(sp[1].arclen(), 0.5) and isEqual(sp[2].arclen(), 0.5) and isEqual(sp[3].arclen(), 0.5) and isEqual(sp[4].arclen(), 0.5)
#
#        sp = np.split([0, 0.5, 1, 2])
#        assert len(sp)==5 and sp[0] is None and isEqual(sp[1].arclen(), 0.5) and isEqual(sp[2].arclen(), 0.5) and isEqual(sp[3].arclen(), 1) and sp[4] is None
#
#        sp = np.split([0, 0.5, 1.5, 2])
#        assert len(sp)==5 and sp[0] is None and isEqual(sp[1].arclen(), 0.5) and isEqual(sp[2].arclen(), 1) and isEqual(sp[3].arclen(), 0.5) and sp[4] is None
#
#        sp = np.split([0, 1, 1.5, 2])
#        assert len(sp)==5 and sp[0] is None and isEqual(sp[1].arclen(), 1) and isEqual(sp[2].arclen(), 0.5) and isEqual(sp[3].arclen(), 0.5) and sp[4] is None
#
#        sp = np.split([0.5, 1, 1.5, 2])
#        assert len(sp)==5 and isEqual(sp[0].arclen(), 0.5) and isEqual(sp[1].arclen(), 0.5) and isEqual(sp[2].arclen(), 0.5) and isEqual(sp[3].arclen(), 0.5) and sp[4] is None
#
#        
#        # five split parameters
#        sp = np.split([0, 0.5, 1, 1.5, 2])
#        assert len(sp)==6 and sp[0] is None and isEqual(sp[1].arclen(), 0.5) and isEqual(sp[2].arclen(), 0.5) and isEqual(sp[3].arclen(), 0.5) and isEqual(sp[4].arclen(), 0.5) and sp[5] is None

    def testshortnormsubpath(self):
        sp = normsubpath(epsilon=1)
        sp.append(normline(0, 0, 0.5, 0))
        sp.append(normline(0.5, 0, 1.5, 0))

        sp.append(normline(1.5, 0, 1.5, 0.3))
        sp.append(normline(1.5, 0.3, 1.5, 0.6))
        sp.append(normline(1.5, 0.6, 1.5, 0.9))
        sp.append(normline(1.5, 0.9, 1.5, 1.2))

        sp.append(normline(1.2, 1.5, 1.3, 1.6))
        sp.append(normcurve(1.3, 1.6, 1.4, 1.7, 1.3, 1.7, 1.3, 1.8))
        sp.append(normcurve(1.3, 1.8, 2.4, 2.7, 3.3, 3.7, 1.4, 1.8))

        self.failUnlessEqual(str(sp), "subpath(open, [normline(0, 0, 1.5, 0), normline(1.5, 0, 1.5, 1.2), normcurve(1.2, 1.5, 2.4, 2.7, 3.3, 3.7, 1.4, 1.8)])")

    def testintersectnormsubpath(self):
        smallposy = 0.09
        smallnegy = -0.01
        p1 = normsubpath([normline(-1, 0, 1, 0)])
        p2 = normsubpath([normline(0, smallposy, 0, smallnegy),
                          normline(0, smallnegy, 0, 1+smallnegy),
                          normline(0, 1+smallnegy, 0, smallnegy),
                          normline(0, smallnegy, 0, smallposy)], closed=0)
        p1.epsilon = p2.epsilon = 0.05
        intersect = p2.intersect(p1)
        self.failUnlessEqual(len(intersect[0]), 2)
        self.failUnlessAlmostEqual(intersect[0][0], 0.9)
        self.failUnlessAlmostEqual(intersect[0][1], 2.99)

        smallposy = 0.09
        smallnegy = -0.01
        p1 = normsubpath([normline(-1, 0, 1, 0)])
        p2 = normsubpath([normline(0, smallposy, 0, smallnegy),
                          normline(0, smallnegy, 0, 1+smallnegy),
                          normline(0, 1+smallnegy, 0, smallnegy),
                          normline(0, smallnegy, 0, smallposy)], closed=1)
        p1.epsilon = p2.epsilon = 0.05
        intersect = p2.intersect(p1)
        self.failUnlessEqual(len(intersect[0]), 2)
        self.failUnlessAlmostEqual(intersect[0][0], 0.9)
        self.failUnlessAlmostEqual(intersect[0][1], 2.99)

        smallposy = 0.01
        smallnegy = -0.09
        p1 = normsubpath([normline(-1, 0, 1, 0)])
        p2 = normsubpath([normline(0, smallposy, 0, smallnegy),
                          normline(0, smallnegy, 0, 1+smallnegy),
                          normline(0, 1+smallnegy, 0, smallnegy),
                          normline(0, smallnegy, 0, smallposy)], closed=0)
        p1.epsilon = p2.epsilon = 0.05
        intersect = p2.intersect(p1)
        self.failUnlessEqual(len(intersect[0]), 4)
        self.failUnlessAlmostEqual(intersect[0][0], 0.1)
        self.failUnlessAlmostEqual(intersect[0][1], 1.09)
        self.failUnlessAlmostEqual(intersect[0][2], 2.91)
        self.failUnlessAlmostEqual(intersect[0][3], 3.9)

        smallposy = 0.01
        smallnegy = -0.09
        p1 = normsubpath([normline(-1, 0, 1, 0)])
        p2 = normsubpath([normline(0, smallposy, 0, smallnegy),
                          normline(0, smallnegy, 0, 1+smallnegy),
                          normline(0, 1+smallnegy, 0, smallnegy),
                          normline(0, smallnegy, 0, smallposy)], closed=1)
        p1.epsilon = p2.epsilon = 0.05
        intersect = p2.intersect(p1)
        self.failUnlessEqual(len(intersect[0]), 3)
        self.failUnlessAlmostEqual(intersect[0][0], 0.1)
        self.failUnlessAlmostEqual(intersect[0][1], 1.09)
        self.failUnlessAlmostEqual(intersect[0][2], 2.91)

        smallposy = 0.01
        smallnegy = -0.01
        p1 = normsubpath([normline(-1, 0, 1, 0)])
        p2 = normsubpath([normline(0, smallposy, 0, smallnegy),
                          normline(0, smallnegy, 0, 1+smallnegy),
                          normline(0, 1+smallnegy, 0, smallnegy),
                          normline(0, smallnegy, 0, smallposy)], closed=0)
        p1.epsilon = p2.epsilon = 0.05
        intersect = p2.intersect(p1)
        self.failUnlessEqual(len(intersect[0]), 2)
        self.failUnlessAlmostEqual(intersect[0][0], 0.5)
        self.failUnlessAlmostEqual(intersect[0][1], 2.99)

        smallposy = 0.01
        smallnegy = -0.01
        p1 = normsubpath([normline(-1, 0, 1, 0)])
        p2 = normsubpath([normline(0, smallposy, 0, smallnegy),
                          normline(0, smallnegy, 0, 1+smallnegy),
                          normline(0, 1+smallnegy, 0, smallnegy),
                          normline(0, smallnegy, 0, smallposy)], closed=1)
        p1.epsilon = p2.epsilon = 0.05
        intersect = p2.intersect(p1)
        self.failUnlessEqual(len(intersect[0]), 1)
        self.failUnlessAlmostEqual(intersect[0][0], 0.5)

        smallposy = 0.1
        smallnegy = -0.1
        p1 = normsubpath([normline(-1, 0, 1, 0)])
        p2 = normsubpath([normline(0, smallposy, 0, smallnegy),
                          normline(0, smallnegy, 0, 1+smallnegy),
                          normline(0, 1+smallnegy, 0, smallnegy),
                          normline(0, smallnegy, 0, smallposy)], closed=0)
        p1.epsilon = p2.epsilon = 0.05
        intersect = p2.intersect(p1)
        self.failUnlessEqual(len(intersect[0]), 4)
        self.failUnlessAlmostEqual(intersect[0][0], 0.5)
        self.failUnlessAlmostEqual(intersect[0][1], 1.1)
        self.failUnlessAlmostEqual(intersect[0][2], 2.9)
        self.failUnlessAlmostEqual(intersect[0][3], 3.5)


if __name__ == "__main__":
    unittest.main()
