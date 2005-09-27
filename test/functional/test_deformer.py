#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]
import warnings
from pyx import *
from pyx.deformer import *

#####  helpers  ##############################################################

def bboxrect(cmd):
   return cmd.bbox().enlarged(5*unit.t_mm).rect()

def dotest(c, x, y, test):
   c2 = c.insert(canvas.canvas([trafo.translate(x, y)]))
   eval("%s(c2)" % test)
   c.stroke(bboxrect(c2))

def drawpathwbbox(c, p):
    c.stroke(p, [color.rgb.red])
    np = p.normpath()
    c.stroke(np, [color.rgb.green, style.linestyle.dashed])
    c.stroke(bboxrect(p))

#####  tests  ################################################################

def testcycloid(c):

    # dependence on turnangle
    p = path.line(0, 0, 3, 0)
    c.stroke(p, [style.linewidth.THIN])
    cyc = cycloid(halfloops=3, skipfirst=0.5, skiplast=0.5, curvesperhloop=2)
    c.stroke(p, [cyc(turnangle=00)])
    c.stroke(p, [cyc(turnangle=22), color.rgb.red])
    c.stroke(p, [cyc(turnangle=45), color.rgb.green])
    c.stroke(p, [cyc(turnangle=67), color.rgb.blue])
    c.stroke(p, [cyc(turnangle=90), color.cmyk.Cyan])

    # dependence on curvesperloop
    p = path.curve(5, 0, 8, 0, 6, 4, 9, 4)
    c.stroke(p)
    cyc = cycloid(halfloops=16, skipfirst=0, skiplast=0, curvesperhloop=1)
    c.stroke(p, [cyc(curvesperhloop=2)])
    c.stroke(p, [cyc(curvesperhloop=3), color.rgb.red])
    c.stroke(p, [cyc(curvesperhloop=4), color.rgb.green])
    c.stroke(p, [cyc(curvesperhloop=10), color.rgb.blue])

    # extremely curved path
    p = path.curve(0,2, 0.5,5, 1,6, 2,2)
    c.stroke(p)
    cyc = cycloid(radius=0.7, halfloops=7, skipfirst=0, skiplast=0, curvesperhloop=1)
    c.stroke(p, [cyc(curvesperhloop=2)])
    c.stroke(p, [cyc(curvesperhloop=3), color.rgb.red])
    c.stroke(p, [cyc(curvesperhloop=4), color.rgb.green])
    c.stroke(p, [cyc(curvesperhloop=50), color.rgb.blue])


def testsmoothed(c):
    p = path.path(
      path.moveto(0,0),
      path.lineto(3,0),
      path.lineto(5,7),
      path.curveto(0,10, -2,8, 0,6),
      path.lineto(0,4),
      # horrible overshooting with obeycurv=1
      #path.lineto(-4,4), path.curveto(-7,5, -4,2, -5,2),
      path.lineto(-4,3), path.curveto(-7,5, -4,2, -5,2),
      #path.arct(-6,4, -5,1, 1.5),
      #path.arc(-5, 3, 0.5, 0, 180),
      path.lineto(-5,1),
      path.lineto(-0.2,0.2),
      path.closepath()
    ) + path.circle(0,1,2)

    c.stroke(p, [color.gray(0.8), style.linewidth.THICk])
    c.stroke(p.normpath(), [color.gray(0.8), style.linewidth.THICk])
    c.stroke(p, [smoothed(radius=0.85, softness=1, obeycurv=1), style.linewidth.Thin])
    c.stroke(p, [smoothed(radius=0.85, softness=1, obeycurv=0), color.rgb.red])
    c.stroke(p, [smoothed(radius=0.20, softness=1, obeycurv=0), color.rgb.green])
    c.stroke(p, [smoothed(radius=1.20, softness=1, obeycurv=0), color.rgb.blue])

    p = path.path(
      path.moveto(0,10),
      path.curveto(1,10, 4,12, 2,11),
      path.curveto(4,8, 4,12, 0,11)
    )
    c.stroke(p, [color.gray(0.8), style.linewidth.THICk])
    c.stroke(p.normpath(), [color.gray(0.8), style.linewidth.THICk])
    c.stroke(p, [smoothed(radius=0.85, softness=1, obeycurv=1), style.linewidth.Thick])
    c.stroke(p, [smoothed(radius=0.85, softness=1, obeycurv=0), color.rgb.red])
    c.stroke(p, [smoothed(radius=0.20, softness=1, obeycurv=0), color.rgb.green])
    c.stroke(p, [smoothed(radius=1.20, softness=1, obeycurv=0), color.rgb.blue])


def hard_test(c, p, dist, pardef, move=(0, 0), label=""):
    print "hard test of parallel: ", label
    p = p.transformed(trafo.translate(*move))
    c.text(move[0], move[1], label)
    c.stroke(p)
    pps = []
    if 1:
        p1 = pardef(distance=+dist).deform(p)
        c.stroke(p1, [color.rgb.red])
        pps.append(p1)
    if 1:
        p2 = pardef(distance=-dist).deform(p)
        c.stroke(p2, [color.rgb.blue])
        pps.append(p2)
    return
    for pp in pps:
        for nsp in pp.normsubpaths:
            beg, end = nsp.at_pt([0, len(nsp)])
            begn, endn = nsp.rotation([0, len(nsp)])
            if begn is normpath.invalid:
                begn = (1, 0)
            else:
                begn = begn.apply_pt(0, 1)
            if endn is normpath.invalid:
                endn = (1, 0)
            else:
                endn = endn.apply_pt(0, 1)
            l = 0.1
            c.stroke(path.line_pt(beg[0]-l*begn[0], beg[1]-l*begn[1], beg[0]+l*begn[0], beg[1]+l*begn[1]), [color.rgb.green])
            c.stroke(path.line_pt(end[0]-l*endn[0], end[1]-l*endn[1], end[0]+l*endn[0], end[1]+l*endn[1]), [color.rgb.green])
            for nspitem in nsp.normsubpathitems:
                if isinstance(nspitem, normpath.normcurve_pt):
                    c.fill(path.circle(nspitem.x1_pt*unit.u_pt, nspitem.y1_pt*unit.u_pt, 0.025), [color.rgb.green])
                    c.fill(path.circle(nspitem.x2_pt*unit.u_pt, nspitem.y2_pt*unit.u_pt, 0.025), [color.rgb.green])
                c.fill(path.circle(nspitem.atbegin_pt()[0]*unit.u_pt, nspitem.atbegin_pt()[1]*unit.u_pt, 0.02))
                c.fill(path.circle(nspitem.atend_pt()[0]*unit.u_pt, nspitem.atend_pt()[1]*unit.u_pt, 0.02))

    for nsp in p.normpath().normsubpaths:
        for nspitem in nsp.normsubpathitems:
            c.fill(path.circle(nspitem.atbegin_pt()[0]*unit.u_pt, nspitem.atbegin_pt()[1]*unit.u_pt, 0.02), [color.rgb.red])
            c.fill(path.circle(nspitem.atend_pt()[0]*unit.u_pt, nspitem.atend_pt()[1]*unit.u_pt, 0.02), [color.rgb.red])


def testparallel_1(c):

    d = c

    # HARD TESTS of elementary geometry:
    #
    # test for correct skipping of short ugly pieces:
    move = (0, 0)
    p = path.path(path.moveto(0, 1), path.lineto(10, 0.3), path.lineto(12, 0), path.lineto(0, 0))
    p.append(path.closepath())
    hard_test(c, p, -0.2, parallel(0.0), move, "A")

    # test non-intersecting/too short neighbouring pathels
    move = (0, 4)
    p = path.curve(0,0, 0,1, 1,2, 2,0)
    p.append(path.lineto(2.1, 0.1))
    p.append(path.lineto(1.6, -2))
    p.append(path.lineto(2.1, -2))
    p.append(path.lineto(-0.15, 0))
    p.append(path.closepath())
    hard_test(c, p, 0.3, parallel(0.0), move, "B")
    hard_test(c, p, 0.05, parallel(0.0), move, "B")

    # test extremely sensitively:
    move = (3.5, 2)
    p = path.curve(0,0, 0,1, 1,1, 1,0)
    p.append(path.closepath())
    hard_test(c, p, -0.1, parallel(0.0), move, "C")
    # takes quite long:
    hard_test(c, p, -0.1, parallel(0.0, relerr=1e-15, checkdistanceparams=[0.5]), move, "C")

    # test for numeric instabilities:
    move = (6, 2)
    p = path.curve(0,0, 1,1, 1,1, 2,0)
    p.append(path.closepath())
    hard_test(c, p, -0.1, parallel(0.0, relerr=0.15, checkdistanceparams=[0.5]), move, "D")
    hard_test(c, p, -0.3, parallel(0.0), move, "D")

    # test for an empty parallel path:
    move = (5, 5)
    p = path.circle(0, 0, 0.5)
    hard_test(c, p, 0.55, parallel(0.0), move, "E")
    hard_test(c, p, 0.499, parallel(0.0), move, "E")
    hard_test(c, p, 0.499999, parallel(0.0), move, "E")

    # a degenerate path:
    move = (12, 3)
    p = path.curve(0,0, 0,-5, 0,1, 0,0.5)
#   hard_test(c, p, 0.1, parallel(0.0), move, "F")

    # test for too big curvatures in the middle:
    move = (9, 2.5)
    p = path.curve(0,0, 1,1, 1,1, 2,0)
    hard_test(c, p, -0.4, parallel(0.0, relerr=1.0e-2), move, "G")
    hard_test(c, p, -0.6, parallel(0.0, relerr=1.0e-2), move, "G")
    hard_test(c, p, -0.8, parallel(0.0, relerr=1.0e-2), move, "G")
    hard_test(c, p, -1.2, parallel(0.0), move, "G")

    # deformation of the deformation:
    move = (9, 6)
    p = path.curve(0,0, 1,1, 1,1, 2,0)
    c.stroke(p, [trafo.translate(*move)])
    p = parallel(-0.4, relerr=1.0e-2).deform(p)
    hard_test(c, p, -0.39, parallel(0.0), move, "H")

    # test for infinite curvature in the middle:
    move = (9, 8)
    p = path.curve(0,0, 1,1, 0,1, 1,0)
    hard_test(c, p, -0.2, parallel(0.0), move, "I")

    # test for infinite curvature at the end:
    move = (5, 8)
    p = path.curve(0,0, 1,1, 1,0, 1,0)
    hard_test(c, p, -0.1, parallel(0.0), move, "J")
    # test for infinite curvature when the path goes on
    p.append(path.rlineto(1, 0))
    hard_test(c, p, -0.22, parallel(0.0), move, "J")


def testparallel_2(c):

    d = c

    # a path of two subpaths:
    move = (0, 0)
    p = path.circle(-6, 0, 2)
    p += path.path(path.moveto(0,0), path.curveto(0,16, -11,5, 5,5))
    p += path.path(path.lineto(5,4), path.lineto(7,4), path.lineto(7,6), path.lineto(4,6),
                   path.lineto(4,7), path.lineto(5,7), path.lineto(3,1), path.closepath())
    p = p.transformed(trafo.scale(0.5))
    hard_test(c, p, 0.05, parallel(0.0), move, "K")
    hard_test(c, p, 0.3, parallel(0.0), move, "K")
    hard_test(c, p, 0.6, parallel(0.0), move, "K")


c=canvas.canvas()
dotest(c, 13, 15, "testcycloid")
dotest(c, 20, 0, "testsmoothed")
dotest(c, 0, 0, "testparallel_1")
dotest(c, 6, 12, "testparallel_2")
c.writeEPSfile("test_deformer", paperformat=document.paperformat.A4, rotated=0, fittosize=1)
c.writePDFfile("test_deformer")

