import sys
if sys.path[0] != "../..":
    sys.path.insert(0, "../..")

import unittest

from pyx import *
from pyx.path import *
import math
set(epsilon=1e-7)

class NormpathTestCase(unittest.TestCase):

    def testparam(self):
        p = ( normpath([normsubpath([normline_pt(0, 0, 10, 0),
                                   normline_pt(10, 0, 10, 20),
                                   normline_pt(10, 20, 0, 20),
                                   normline_pt(0, 20, 0, 0)], closed=1)]) +
              circle_pt(0, 0, 10) +
              line_pt(0, 0, 2, 0))

        param = normpathparam(p, 0, 1.5)
        param = param + 0
        self.failUnlessEqual(param.normsubpathindex, 0)
        self.failUnlessAlmostEqual(param.normsubpathparam, 1.5)
        param = param + 15 * unit.t_pt
        self.failUnlessEqual(param.normsubpathindex, 0)
        self.failUnlessAlmostEqual(param.normsubpathparam, 2.5)
        param += 24.9 * unit.t_pt
        self.failUnlessEqual(param.normsubpathindex, 0)
        self.failUnlessAlmostEqual(param.normsubpathparam, 3.995)
        param = 0.1 * unit.t_pt + param
        self.failUnlessEqual(param.normsubpathindex, 1)
        self.failUnlessAlmostEqual(param.normsubpathparam, 0)
        param = param + 0.5*circle_pt(0, 0, 10).arclen()
        circlerange = len(p.normsubpaths[1])
        self.failUnlessEqual(param.normsubpathindex, 1)
        self.failUnlessAlmostEqual(param.normsubpathparam, 0.5*circlerange, 4)
        param = param + 0.5*circle_pt(0, 0, 10).arclen()
        param = param + 2 * unit.t_pt
        self.failUnlessEqual(param.normsubpathindex, 2)
        self.failUnlessAlmostEqual(param.normsubpathparam, 1, 4)
        param = param + 1 * unit.t_pt
        self.failUnlessEqual(param.normsubpathindex, 2)
        self.failUnlessAlmostEqual(param.normsubpathparam, 1.5, 4)

        param = normpathparam(p, 0, 1.5)
        param = param - 15 * unit.t_pt
        self.failUnlessEqual(param.normsubpathindex, 0)
        self.failUnlessAlmostEqual(param.normsubpathparam, 0.5)
        param -= 10 * unit.t_pt
        self.failUnlessEqual(param.normsubpathindex, 0)
        self.failUnlessAlmostEqual(param.normsubpathparam, -0.5)
        
        param = normpathparam(p, 0, 1.2)
        param2 = 2*param
        param += param
        self.failUnlessEqual(param.normsubpathindex, param2.normsubpathindex)
        self.failUnlessEqual(param.normsubpathparam, param2.normsubpathparam)

        param = normpathparam(p, 0, 1.2)
        self.failUnless(param < 15 * unit.t_pt)
        self.failUnless(15 * unit.t_pt > param)
        self.failUnless(param > 12 * unit.t_pt)
        self.failUnless(12 * unit.t_pt < param)
        self.failUnless(param < 1)
        self.failUnless(1 > param)

    def testat(self):
        p = normpath([normsubpath([normline_pt(0, 0, 10, 0),
                                   normline_pt(10, 0, 10, 20),
                                   normline_pt(10, 20, 0, 20),
                                   normline_pt(0, 20, 0, 0)], closed=1)])
        params = [-5, 0, 5, 10, 20, 30, 35, 40, 50, 60, 70]
        ats = (-5, 0), (0, 0), (5, 0), (10, 0), (10, 10), (10, 20), (5, 20), (0, 20), (0, 10), (0, 0), (0, -10)
        for param, (at_x, at_y) in zip(params, ats):
            self.failUnlessAlmostEqual(p.at_pt(param)[0], at_x)
            self.failUnlessAlmostEqual(p.at_pt(param)[1], at_y)
        for (at_x, at_y), (at2_x, at2_y) in zip(p.at_pt(params), ats):
            self.failUnlessAlmostEqual(at_x, at2_x)
            self.failUnlessAlmostEqual(at_y, at2_y)
        p = normpath([normsubpath([normline_pt(0, 0, 3, 0),
                                   normcurve_pt(3, 0, 3, 2, 3, 4, 3, 6),
                                   normcurve_pt(3, 6, 2, 6, 1, 6, 0, 6),
                                   normline_pt(0, 6, 0, 0)], closed=1)])
        self.failUnlessAlmostEqual(p.at_pt(6)[0], 3)
        self.failUnlessAlmostEqual(p.at_pt(6)[1], 3)
        self.failUnlessAlmostEqual(p.at_pt(4.5)[0], 3)
        self.failUnlessAlmostEqual(p.at_pt(4.5)[1], 1.5)

    def testarclentoparam(self):
        p = ( normpath([normsubpath([normline_pt(0, 0, 10, 0),
                                   normline_pt(10, 0, 10, 20),
                                   normline_pt(10, 20, 0, 20),
                                   normline_pt(0, 20, 0, 0)], closed=1)]) +
              circle_pt(0, 0, 10) +
              line_pt(0, 0, 2, 0))
        
        arclens_pt = [20, 30, -2, 61, 100, 200, -30, 1000]
        for arclen_pt, arclen2_pt in zip(arclens_pt, p.paramtoarclen_pt(p.arclentoparam_pt(arclens_pt))):
            self.failUnlessAlmostEqual(arclen_pt, arclen2_pt, 4)

        arclens = [x*unit.t_pt for x in [20, 30, -2, 61, 100, 200, -30, 1000]]
        for arclen, arclen2 in zip(arclens, p.paramtoarclen(p.arclentoparam(arclens))):
            self.failUnlessAlmostEqual(unit.tom(arclen), unit.tom(arclen2), 4)

    def testsplit(self):
        p = normsubpath([normline_pt(0, -1, 1, 0.1),
                         normline_pt(1, 0.1, 2, -1),
                         normline_pt(2, -1, 1, -1), 
                         normline_pt(1, -1, 1, 1)])

        self.failUnlessEqual(len(p.split([0.9, 1.1, 3.5])), 4)

    

    def testshortnormsubpath(self):
        sp = normsubpath(epsilon=1)
        sp.append(normline_pt(0, 0, 0.5, 0))
        sp.append(normline_pt(0.5, 0, 1.5, 0))

        sp.append(normline_pt(1.5, 0, 1.5, 0.3))
        sp.append(normline_pt(1.5, 0.3, 1.5, 0.6))
        sp.append(normline_pt(1.5, 0.6, 1.5, 0.9))
        sp.append(normline_pt(1.5, 0.9, 1.5, 1.2))

        sp.append(normline_pt(1.2, 1.5, 1.3, 1.6))
        sp.append(normcurve_pt(1.3, 1.6, 1.4, 1.7, 1.3, 1.7, 1.3, 1.8))
        sp.append(normcurve_pt(1.3, 1.8, 2.4, 2.7, 3.3, 3.7, 1.4, 1.8))

        self.failUnlessEqual(str(sp), "subpath(open, [normline_pt(0, 0, 1.5, 0), normline_pt(1.5, 0, 1.5, 1.2), normcurve_pt(1.2, 1.5, 2.4, 2.7, 3.3, 3.7, 1.4, 1.8)])")

    def testintersectnormsubpath(self):
        smallposy = 0.09
        smallnegy = -0.01
        p1 = normsubpath([normline_pt(-1, 0, 1, 0)])
        p2 = normsubpath([normline_pt(0, smallposy, 0, smallnegy),
                          normline_pt(0, smallnegy, 0, 1+smallnegy),
                          normline_pt(0, 1+smallnegy, 0, smallnegy),
                          normline_pt(0, smallnegy, 0, smallposy)], closed=0)
        p1.epsilon = p2.epsilon = 0.05
        intersect = p2.intersect(p1)
        self.failUnlessEqual(len(intersect[0]), 2)
        self.failUnlessAlmostEqual(intersect[0][0], 0.9)
        self.failUnlessAlmostEqual(intersect[0][1], 2.99)

        smallposy = 0.09
        smallnegy = -0.01
        p1 = normsubpath([normline_pt(-1, 0, 1, 0)])
        p2 = normsubpath([normline_pt(0, smallposy, 0, smallnegy),
                          normline_pt(0, smallnegy, 0, 1+smallnegy),
                          normline_pt(0, 1+smallnegy, 0, smallnegy),
                          normline_pt(0, smallnegy, 0, smallposy)], closed=1)
        p1.epsilon = p2.epsilon = 0.05
        intersect = p2.intersect(p1)
        self.failUnlessEqual(len(intersect[0]), 2)
        self.failUnlessAlmostEqual(intersect[0][0], 0.9)
        self.failUnlessAlmostEqual(intersect[0][1], 2.99)

        smallposy = 0.01
        smallnegy = -0.09
        p1 = normsubpath([normline_pt(-1, 0, 1, 0)])
        p2 = normsubpath([normline_pt(0, smallposy, 0, smallnegy),
                          normline_pt(0, smallnegy, 0, 1+smallnegy),
                          normline_pt(0, 1+smallnegy, 0, smallnegy),
                          normline_pt(0, smallnegy, 0, smallposy)], closed=0)
        p1.epsilon = p2.epsilon = 0.05
        intersect = p2.intersect(p1)
        self.failUnlessEqual(len(intersect[0]), 4)
        self.failUnlessAlmostEqual(intersect[0][0], 0.1)
        self.failUnlessAlmostEqual(intersect[0][1], 1.09)
        self.failUnlessAlmostEqual(intersect[0][2], 2.91)
        self.failUnlessAlmostEqual(intersect[0][3], 3.9)

        smallposy = 0.01
        smallnegy = -0.09
        p1 = normsubpath([normline_pt(-1, 0, 1, 0)])
        p2 = normsubpath([normline_pt(0, smallposy, 0, smallnegy),
                          normline_pt(0, smallnegy, 0, 1+smallnegy),
                          normline_pt(0, 1+smallnegy, 0, smallnegy),
                          normline_pt(0, smallnegy, 0, smallposy)], closed=1)
        p1.epsilon = p2.epsilon = 0.05
        intersect = p2.intersect(p1)
        self.failUnlessEqual(len(intersect[0]), 3)
        self.failUnlessAlmostEqual(intersect[0][0], 0.1)
        self.failUnlessAlmostEqual(intersect[0][1], 1.09)
        self.failUnlessAlmostEqual(intersect[0][2], 2.91)

        smallposy = 0.01
        smallnegy = -0.01
        p1 = normsubpath([normline_pt(-1, 0, 1, 0)])
        p2 = normsubpath([normline_pt(0, smallposy, 0, smallnegy),
                          normline_pt(0, smallnegy, 0, 1+smallnegy),
                          normline_pt(0, 1+smallnegy, 0, smallnegy),
                          normline_pt(0, smallnegy, 0, smallposy)], closed=0)
        p1.epsilon = p2.epsilon = 0.05
        intersect = p2.intersect(p1)
        self.failUnlessEqual(len(intersect[0]), 2)
        self.failUnlessAlmostEqual(intersect[0][0], 0.5)
        self.failUnlessAlmostEqual(intersect[0][1], 2.99)

        smallposy = 0.01
        smallnegy = -0.01
        p1 = normsubpath([normline_pt(-1, 0, 1, 0)])
        p2 = normsubpath([normline_pt(0, smallposy, 0, smallnegy),
                          normline_pt(0, smallnegy, 0, 1+smallnegy),
                          normline_pt(0, 1+smallnegy, 0, smallnegy),
                          normline_pt(0, smallnegy, 0, smallposy)], closed=1)
        p1.epsilon = p2.epsilon = 0.05
        intersect = p2.intersect(p1)
        self.failUnlessEqual(len(intersect[0]), 1)
        self.failUnlessAlmostEqual(intersect[0][0], 0.5)

        smallposy = 0.1
        smallnegy = -0.1
        p1 = normsubpath([normline_pt(-1, 0, 1, 0)])
        p2 = normsubpath([normline_pt(0, smallposy, 0, smallnegy),
                          normline_pt(0, smallnegy, 0, 1+smallnegy),
                          normline_pt(0, 1+smallnegy, 0, smallnegy),
                          normline_pt(0, smallnegy, 0, smallposy)], closed=0)
        p1.epsilon = p2.epsilon = 0.05
        intersect = p2.intersect(p1)
        self.failUnlessEqual(len(intersect[0]), 4)
        self.failUnlessAlmostEqual(intersect[0][0], 0.5)
        self.failUnlessAlmostEqual(intersect[0][1], 1.1)
        self.failUnlessAlmostEqual(intersect[0][2], 2.9)
        self.failUnlessAlmostEqual(intersect[0][3], 3.5)


if __name__ == "__main__":
    unittest.main()
