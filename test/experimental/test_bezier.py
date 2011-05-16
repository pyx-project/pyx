#!/usr/bin/env python
import sys; sys.path.insert(0, "../..")

import math
from random import Random

from pyx import *
from pyx import normpath
from pyx.deformer import controldists_from_endgeometry_pt
from pyx.normpath import _epsilon

def test_reproductions(seed, n_tests, xmax, ymax, accuracy): # <<<
    # insert xmax, ymax, accuracy in pt!

    r = Random(seed)
    n_testpoints = 20
    testparams = [i / (n_testpoints - 1.0) for i in range(n_testpoints)]

    # a canvas for drawing
    can = canvas.canvas()
    xpos = 0
    ypos = 0

    # loop over many different cases
    n_failures = 0
    n_successes = 0
    for cnt in range(n_tests):

        # the original curve
        a = r.uniform(0,xmax), r.uniform(0,ymax)
        b = r.uniform(0,xmax), r.uniform(0,ymax)
        c = r.uniform(0,xmax), r.uniform(0,ymax)
        d = r.uniform(0,xmax), r.uniform(0,ymax)
        origcurve = normpath.normcurve_pt(a[0], a[1], b[0], b[1], c[0], c[1], d[0], d[1])
        tbeg, tend = origcurve.rotation([0, 1])
        cbeg, cend = origcurve.curvature_pt([0, 1])
        # raise an error if one of the params is invalid:
        tbeg, tend, cbeg, cend
        tbeg, tend = tbeg.apply_pt(1, 0), tend.apply_pt(1, 0)

        # the reproduced curve
        controldistpairs = controldists_from_endgeometry_pt(a, d, tbeg, tend, cbeg, cend, _epsilon)
        reprocurves = []
        for controldistpair in controldistpairs:
            alpha, beta = controldistpair
            reprocurves.append(normpath.normcurve_pt(
              a[0], a[1],
              a[0] + alpha * tbeg[0], a[1] + alpha * tbeg[1],
              d[0] - beta * tend[0], d[1] - beta * tend[1],
              d[0], d[1]))

        # analyse the quality of the reproduction
        minmaxdist = float("inf")
        minindex = -1
        maxdists = []
        for i, reprocurve in enumerate(reprocurves):
            maxdist = max([math.hypot(p[0]-q[0], p[1]-q[1])
              for p,q in zip(origcurve.at_pt(testparams), reprocurve.at_pt(testparams))])
            if maxdist < minmaxdist:
                minmaxdist = maxdist
                minindex = i
            maxdists.append(maxdist)

        # print complaints for too bad reproductions
        if minindex != 0 or minmaxdist > accuracy:
            n_failures += 1

            if minmaxdist > accuracy:
                print "%4d Smallest distance is %f" % (cnt, minmaxdist)

            if minindex == -1:
                print "%4d Failure: no solution found" % (cnt)

            if minindex > 0:
                print "%4d Wrong sorting: entry %d is the smallest" % (cnt, minindex)

            if minindex >=0 and not (controldistpairs[minindex][0] >= 0 and controldistpairs[minindex][1] >= 0):
                print "%4d Failure: signs are wrong" % (cnt)

            # selectively draw the curves:
            #if minindex == -1:
            #if minindex > 0:
            if minmaxdist > accuracy:
                # draw the failure curves
                can.stroke(path.rect_pt(0,0,xmax,ymax), [trafo.translate_pt(xpos, ypos)])
                can.draw(normpath.normpath([normpath.normsubpath([origcurve])]),  [trafo.translate_pt(xpos, ypos), deco.stroked([style.linewidth.THIck]), deco.shownormpath()])
                if minindex != -1:
                    can.stroke(normpath.normpath([normpath.normsubpath([reprocurves[minindex]])]), [trafo.translate_pt(xpos, ypos), color.rgb.red])
                can.text(0, 0, r"(%d)" % (cnt), [trafo.translate_pt(xpos+0.5*xmax, ypos), text.halign.center, text.vshift(2.0)])
                xpos += 1.1*xmax
                if xpos > 11*xmax:
                    xpos = 0
                    ypos -= 1.1*ymax
                    ypos -= 15
        else:
            n_successes += 1

    print "failures, successes = ", n_failures, ", ", n_successes
    can.writeEPSfile("test_bezier")
# >>>

test_reproductions(43, 10000, 100, 100, 1.0e-2)


# vim:foldmethod=marker:foldmarker=<<<,>>>
