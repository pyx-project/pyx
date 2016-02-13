#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]
import warnings, math
from pyx import *
from pyx.deformer import *
from pyx import normpath

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


def testcornersmoothed(c):
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
    c.stroke(p, [cornersmoothed(radius=0.85, softness=1, obeycurv=1), style.linewidth.Thin])
    c.stroke(p, [cornersmoothed(radius=0.85, softness=1, obeycurv=0), color.rgb.red])
    c.stroke(p, [cornersmoothed(radius=0.20, softness=1, obeycurv=0), color.rgb.green])
    c.stroke(p, [cornersmoothed(radius=1.20, softness=1, obeycurv=0), color.rgb.blue])

    p = path.path(
      path.moveto(0,10),
      path.curveto(1,10, 4,12, 2,11),
      path.curveto(4,8, 4,12, 0,11)
    )
    c.stroke(p, [color.gray(0.8), style.linewidth.THICk])
    c.stroke(p.normpath(), [color.gray(0.8), style.linewidth.THICk])
    c.stroke(p, [cornersmoothed(radius=0.85, softness=1, obeycurv=1), style.linewidth.Thick])
    c.stroke(p, [cornersmoothed(radius=0.85, softness=1, obeycurv=0), color.rgb.red])
    c.stroke(p, [cornersmoothed(radius=0.20, softness=1, obeycurv=0), color.rgb.green])
    c.stroke(p, [cornersmoothed(radius=1.20, softness=1, obeycurv=0), color.rgb.blue])


def hard_test(c, pth, dist, pardef, move=(0, 0), label=None, dotests=[True]*4, checklens=[None]*4):
    print("hard test of parallel: ", label)
    tr = trafo.translate(*move)
    if label is not None:
        c.text(0.5*(pth.bbox().left() + pth.bbox().right()),
               0.5*(pth.bbox().bottom() + pth.bbox().top()), label, [tr])
    c.stroke(pth, [tr])
    pth_rev = pth.reversed()
    dists = [dist, -dist, -dist, dist]
    paths = [pth, pth_rev, pth, pth_rev]
    styles = [[color.rgb.red], [style.linestyle.dashed], [color.rgb.blue], [color.rgb.green, style.linestyle.dashed]]
    for i, d, p, dotest, assertlens, st in zip(range(4), dists, paths, dotests, checklens, styles):
        if dotest:
            pl = pardef(distance=d).deform(p)
            c.stroke(pl, st + [tr])#, deco.shownormpath()])
            if assertlens is None:
                print([len(nsp) for nsp in pl])
            else:
                if len(pl) != len(assertlens):
                    print("WARNING: wrong number of nsp (%d instead of expected %d) in test %d" % (len(pl), len(assertlens), i))
                for j, (n_nspitems, nsp) in enumerate(zip(assertlens, pl)):
                    if len(nsp) != n_nspitems:
                        print("WARNING: wrong number of nsp items (%d instead of expected %d) in test %d, nsp number %d" % (len(nsp), n_nspitems, i, j))

def testparallel_1(c):

    # HARD TESTS of elementary geometry:
    #
    # test for correct skipping of short ugly pieces:
    move = (-2, 0)
    p = path.path(path.moveto(0, 1), path.lineto(10, 0.3), path.lineto(12, 0), path.lineto(0, 0))
    p.append(path.closepath())
    hard_test(c, p, 0.1, parallel(0.0), move, "A", checklens=[[15],[15],[4],[4]])
    hard_test(c, p, 0.25, parallel(0.0, sharpoutercorners=True), move, "A", checklens=[[12],[12],[3],[3]])
    hard_test(c, p, 0.55, parallel(0.0), move, "A", checklens=[[15],[15],[],[]])

    # test non-intersecting/too short neighbouring pathels
    move = (0, 4)
    p = path.curve(0,0, 0,1, 1,2, 2,0)
    p.append(path.lineto(2.1, 0.1))
    p.append(path.lineto(1.6, -2))
    p.append(path.lineto(2.1, -2))
    p.append(path.lineto(-0.15, 0))
    p.append(path.closepath())
    hard_test(c, p, 0.02, parallel(0.0, sharpoutercorners=1), move, "B", checklens=[[3],[3],[11],[11]])
    hard_test(c, p, 0.06, parallel(0.0), move, "B", checklens=[[3],[3],[10],[9]]) # difference is due to rounding in path._arctobeziers
    hard_test(c, p, 0.3, parallel(0.0), move, "B", checklens=[[25],[25],[5],[5]])
    hard_test(c, p, 0.3, parallel(0.0, sharpoutercorners=1), move, "B", checklens=[[22],[22],[5],[5]])

    # test extreme precision:
    move = (3.5, 2)
    p = path.curve(0,0, 0,1, 1,1, 1,0)
    p.append(path.closepath())
    hard_test(c, p, 0.1, parallel(0.0), move, "C", checklens=[[8],[8],[2],[2]])
    hard_test(c, p, 0.1, parallel(0.0, relerr=1e-15, checkdistanceparams=[0.5]), move, "C", checklens=[[23],[23],[15],[15]])

    # test for numeric instabilities:
    move = (6, 2)
    p = path.curve(0,0, 1,1, 1,1, 2,0)
    p.append(path.closepath())
    hard_test(c, p, 0.1, parallel(0.0, relerr=0.15, checkdistanceparams=[0.5]), move, "D", checklens=[[11],[11],[3],[3]])
    hard_test(c, p, 0.3, parallel(0.0), move, "D", checklens=[[11],[11],[3],[3]])

    # test for an empty parallel path:
    move = (5, 5)
    p = path.circle(0, 0, 0.5).normpath()
    nspitems = [nspitem for nspitem in p[0] if isinstance(nspitem, normpath.normcurve_pt)]
    nspitems[-1] = nspitems[-1].modifiedend_pt(*nspitems[0].atbegin_pt())
    p = normpath.normpath([normpath.normsubpath(nspitems, closed=True)])
    hard_test(c, p, 0.55, parallel(0.0), move, "E", checklens=[[],[],[9],[9]])
    hard_test(c, p, 0.4999, parallel(0.0, relerr=1.0e-15), move, "E", checklens=[[1,14,8],[1,14],[17],[17]])

    # a degenerate path:
    move = (13, 3)
    p = path.curve(0,0, 0,-5, 0,1, 0,0.5)
    hard_test(c, p, 0.10, parallel(0.0, dointersection=False), move, "F", dotests=[True,True,False,False], checklens=[[13],[12],[13],[12]])
    hard_test(c, p, 0.13, parallel(0.0, dointersection=False), move, "F", dotests=[False,False,True,True], checklens=[[13],[12],[13],[12]])

    # test for too big curvatures in the middle:
    move = (9, 2.5)
    p = path.curve(0,0, 1,1, 1,1, 2,0)
    hard_test(c, p, 0.4, parallel(0.0, relerr=1.0e-2), move, "G", checklens=[[2],[2],[4],[4]])
    hard_test(c, p, 0.6, parallel(0.0, relerr=1.0e-2), move, "G", checklens=[[2],[2],[4],[4]])
    hard_test(c, p, 0.8, parallel(0.0, relerr=1.0e-2), move, "G", checklens=[[2],[2],[4],[4]])
    hard_test(c, p, 1.7, parallel(0.0, relerr=1.0e-2), move, "G", checklens=[[2],[2],[1,1],[1,1]])

    # deformation of the deformation:
    move = (11, 6)
    p = path.curve(-1,0, 0,1, 0,1, 1,0).normpath()
    c.stroke(p, [trafo.translate(*move), color.gray(0.8)])
    dist = unit.u_pt/p.curvature_pt([normpath.normpathparam(p,0,0.5)])[0]
    p = parallel(dist, relerr=1.0e-2, dointersection=0).deform(p)
    assert len(p) == 2
    assert len(p[0]) == len(p[1]) == 2
    c.stroke(p, [trafo.translate(*move), color.gray(0.8)])
    hard_test(c, p, -dist, parallel(0.0), move, "H", checklens=[[4],[4],[2],[2]])

    # test for infinite curvature in the middle:
    move = (11, 8.5)
    p = path.curve(0,0, 1,1, 0,1, 1,0).normpath()
    hard_test(c, p, 0.2, parallel(0.0), move, "I", checklens=[[1,1],[1,1],[2],[2]])
    hard_test(c, p, 1.5, parallel(0.0), move, "I", checklens=[[1,1],[1,1],[7],[7]])
    #ard_test(c, p, 5.0, parallel(0.0), move, "I", checklens=[[],[],[7],[7]])

    # test for infinite curvature at the end:
    move = (-2, 13)
    p = path.curve(0,0, 0.5,0.5, 0.75,0.5, 0.75,0.5)
    hard_test(c, p, 0.1, parallel(0.0, relerr=1.0e-4), move, "J", checklens=[[5],[5],[5],[5]])
    # test for infinite curvature when the path goes on
    # XXX this is not correctly detected if rlineto(1,0). Expect two nsp
    p.append(path.rlineto(0, 1))
    hard_test(c, p, 0.22, parallel(0.0, relerr=1.0e-4), move, "J", checklens=[[4],[4],[3,1],[1,3]])

    # test for too big curvature in the middle, the non-intersecting case
    move = (0, 8)
    p = path.curve(-1,-1, 4,4, -4,4, 1,-1).normpath()
    dist = unit.u_pt * (1.0/p.curvature_pt([normpath.normpathparam(p, 0, 0.5)])[0])
    hard_test(c, p, 1.5*dist, parallel(0.0, dointersection=False), move, "K", checklens=[[1,1],[1,1],[2],[2]])
    hard_test(c, p, dist+normpath._epsilon, parallel(0.0, dointersection=False, relerr=1.0e-5), move, "K", checklens=[[11,11],[11,11],[16],[16]])
    hard_test(c, p, dist+0*normpath._epsilon, parallel(0.0, dointersection=False, relerr=1.0e-5), move, "K", checklens=[[22],[22],[16],[16]])

    # what is to be done with the arcs running around corners?
    # for dist=1.1 they do not even intersect with the original path:
    # TODO
    move = (8, 14)
    p = path.rect(0, 0, 1, 1).normpath()
    hard_test(c, p, 1.1, parallel(0.0), move, "L", dotests=[True,True,False,False], checklens=[[20],[20],None,None])
    hard_test(c, p, 0.55, parallel(0.0), move, "L", dotests=[True,True,False,False], checklens=[[28],[28],None,None])

    # very small lines approximating a curve
    # make sure that there is no "dust" remaining from the many intersections
    move = (3, 9)
    N = 12
    angle = 0.5*math.pi / (N-1.0)
    p = path.path(path.moveto(0, 0))
    for n in range(N):
        p.append(path.lineto(2+math.sin(n*angle), 1-math.cos(n*angle)))
    p.append(path.rlineto(0, 1))
    p.append(path.rlineto(2, 0))
    p.append(path.rlineto(0, -2))
    p = p.transformed(trafo.translate(0, 0.05))
    p = p << p.transformed(trafo.scale(1, -1)).reversed()
    hard_test(c, p, 0.6, parallel(0.0), move, "M", checklens=[[43],[43],[29],[29]])

    # intersections where paths are parallel (in the middle of a nsp-item)
    move = (4, 15)
    c.text(move[0], move[1]+0.2, "N")
    tr = trafo.translate(*move)
    par = parallel(0.1)
    par.dist_pt = unit.topt(par.distance)
    c1 = path.curve(-2,-1, -2,1, 2,-1, 2,1).transformed(tr).normpath()
    c2 = path.curve(-2,-1, -2,1/3.0, 2,1/3.0, 2,-1).transformed(tr).normpath()
    l = path.line(-2,0, 2,0).transformed(tr).normpath()
    for p in [c1, c2, l]:
        c.stroke(p)
    p = (c1 + l).normpath()
    try:
        par._can_continue(mynormpathparam(p,0,0,0.5), mynormpathparam(p,1,0,0.5))
    except IntersectionError as e:
        assert str(e) == "Cannot determine whether curves intersect (parallel and equally curved)"
    p = c2 + l
    assert par._can_continue(mynormpathparam(p,0,0,0.5), mynormpathparam(p,1,0,0.5))
    p = c2 + l.reversed()
    assert par._can_continue(mynormpathparam(p,0,0,0.5), mynormpathparam(p,1,0,0.5))
    p = c2.reversed() + l
    assert not par._can_continue(mynormpathparam(p,0,0,0.5), mynormpathparam(p,1,0,0.5))
    p = c2.reversed() + l.reversed()
    assert not par._can_continue(mynormpathparam(p,0,0,0.5), mynormpathparam(p,1,0,0.5))
    p = c1 + c2
    assert not par._can_continue(mynormpathparam(p,0,0,0.5), mynormpathparam(p,1,0,0.5))
    p = c2 + c1
    assert par._can_continue(mynormpathparam(p,0,0,0.5), mynormpathparam(p,1,0,0.5))
    # intersections where paths are parallel (between nsp-items)
    c11, c12 = c1.split([normpath.normpathparam(c1, 0, 0.5)])
    c21, c22 = c2.split([normpath.normpathparam(c2, 0, 0.5)])
    l1, l2 = l.split([normpath.normpathparam(l, 0, 0.5)])
    p = (c21 << l2 + l1 << c22).normpath() # curve-line + line-curve
    assert par._can_continue(mynormpathparam(p,1,0,1), mynormpathparam(p,0,1,0)) # line -> line
    assert not par._can_continue(mynormpathparam(p,0,0,1), mynormpathparam(p,1,1,0)) # curve -> curve

    # intersections where paths are parallel (in the middle of a nsp-item)
    move = (12, 13)
    p1 = path.path(path.moveto(0,0), path.curveto(0,3, 1,5, 1,0)).normpath()
    params1, params2 = p1.intersect(path.line(0.5,-1, 0.5,5))
    p11, p12 = p1.split(params1)
    p11.append(path.rlineto(0,-2))
    p = p11 << p12
    p.append(path.closepath())
    hard_test(c, p, 0.55, parallel(0.0), move, "O", dotests=[True,True,False,False], checklens=[[10],[10],None,None])

    # jump to too large curvature between nspitems
    move = (-2, 17)
    p = path.path(path.moveto(0,0), path.arc(2,0.5,0.5,-90,90), path.lineto(0,1)).normpath()
    hard_test(c, p, 0.55, parallel(0.0), move, "P", dotests=[True,True,True,True], checklens=[[1,1],[1,1],[7],[7]])

def testparallel_2(c):

    # a case with several dangers:
    #  - double intersection pairs
    #  - intersections with angle 0
    #  - inner intersections that have to be cut away by _between_paths
    move = (10, 2)
    nsp = normpath.normsubpath([# <<<
    #ormpath.normline_pt(-87.5005, 184.037, -86.2747, 184.198),
    #ormpath.normline_pt(-86.2747, 184.198, -85.0394, 184.252),
    #ormpath.normline_pt(-85.0394, 184.252, -83.8041, 184.198),
    #ormpath.normline_pt(-83.8041, 184.198, -82.5782, 184.037),
    #ormpath.normline_pt(-82.5782, 184.037, -81.3711, 183.769),
    #ormpath.normline_pt(-81.3711, 183.769, -80.1918, 183.397),
    #ormpath.normline_pt(-80.1918, 183.397, -79.0495, 182.924),
    #ormpath.normline_pt(-79.0495, 182.924, -77.9528, 182.353),
    #ormpath.normline_pt(-77.9528, 182.353, -76.9099, 181.689),
    #ormpath.normline_pt(-76.9099, 181.689, -75.929, 180.936),
    #ormpath.normline_pt(-75.929, 180.936, -75.0174, 180.101),
    #ormpath.normline_pt(-75.0174, 180.101, -74.1821, 179.189),
    #ormpath.normline_pt(-74.1821, 179.189, -73.4293, 178.208),
    #ormpath.normline_pt(-73.4293, 178.208, -72.765, 177.165),
    #ormpath.normline_pt(-72.765, 177.165, -72.1941, 176.069),
    #ormpath.normline_pt(-72.1941, 176.069, -71.7209, 174.926),
    #ormpath.normline_pt(-71.7209, 174.926, -71.3491, 173.747),
    #ormpath.normline_pt(-71.3491, 173.747, -71.0815, 172.54),
    #ormpath.normline_pt(-71.0815, 172.54, -70.9201, 171.314),
    #ormpath.normline_pt(-70.9201, 171.314, -70.8661, 170.079),
    #ormpath.normline_pt(-70.8661, 170.079, -70.9201, 168.843),
    #ormpath.normline_pt(-70.9201, 168.843, -71.0815, 167.618),
    #ormpath.normline_pt(-71.0815, 167.618, -71.3491, 166.41),
    #ormpath.normline_pt(-71.3491, 166.41, -71.7209, 165.231),
    #ormpath.normline_pt(-71.7209, 165.231, -72.1941, 164.089),
    #ormpath.normline_pt(-72.1941, 164.089, -72.765, 162.992),
    #ormpath.normline_pt(-72.765, 162.992, -73.4293, 161.949),
    #ormpath.normline_pt(-73.4293, 161.949, -74.1821, 160.968),
    #ormpath.normline_pt(-74.1821, 160.968, -75.0174, 160.057),
    #ormpath.normline_pt(-75.0174, 160.057, -75.929, 159.221),
    #ormpath.normline_pt(-75.929, 159.221, -76.9099, 158.469),
    #ormpath.normline_pt(-76.9099, 158.469, -77.9528, 157.804),
    #ormpath.normline_pt(-77.9528, 157.804, -77.9528, -28.3465),
    #ormpath.normline_pt(-77.9528, -28.3465, -77.9797, -28.9641),
    #ormpath.normline_pt(-77.9797, -28.9641, -78.0604, -29.577),
    #ormpath.normline_pt(-78.0604, -29.577, -78.1942, -30.1806),
    #ormpath.normline_pt(-78.1942, -30.1806, -78.3801, -30.7702),
    #ormpath.normline_pt(-78.3801, -30.7702, -78.6167, -31.3414),
    #ormpath.normline_pt(-78.6167, -31.3414, -78.9022, -31.8897),
    #ormpath.normline_pt(-78.9022, -31.8897, -79.2344, -32.4111),
    #ormpath.normline_pt(-79.2344, -32.4111, -79.6107, -32.9016),
    #ormpath.normline_pt(-79.6107, -32.9016, -80.0284, -33.3574),
    #ormpath.normline_pt(-80.0284, -33.3574, -80.4842, -33.7751),
    #ormpath.normline_pt(-80.4842, -33.7751, -80.9747, -34.1514),
    #ormpath.normline_pt(-80.9747, -34.1514, -81.4961, -34.4836),
    #ormpath.normline_pt(-81.4961, -34.4836, -82.0444, -34.7691),
    #ormpath.normline_pt(-82.0444, -34.7691, -82.6156, -35.0057),
    #ormpath.normline_pt(-82.6156, -35.0057, -83.2052, -35.1916),
    #ormpath.normline_pt(-83.2052, -35.1916, -83.8088, -35.3254),
    #ormpath.normline_pt(-83.8088, -35.3254, -84.3307, -35.3941),
    #ormpath.normline_pt(-84.3307, -35.3941, -84.3307, -169.37),
    #ormpath.normline_pt(-84.3307, -169.37, -28.423, -169.37),
    #ormpath.normline_pt(-28.423, -169.37, 0, -156.252),
    #ormpath.normline_pt(0, -156.252, 0, -157.813),
    #ormpath.normline_pt(0, -157.813, -28.1117, -170.787),
    #ormpath.normline_pt(-28.1117, -170.787, -150, -170.787),
    normpath.normline_pt(-150, -170.787, -361.417, -170.787), # start
    normpath.normline_pt(-361.417, -170.787, -361.417, -169.37),
    normpath.normline_pt(-361.417, -169.37, -299.055, -169.37),
    normpath.normline_pt(-299.055, -169.37, -299.055, -141.732),
    normpath.normline_pt(-299.055, -141.732, -297.638, -141.732),
    normpath.normline_pt(-297.638, -141.732, -297.638, -143.15),
    normpath.normline_pt(-297.638, -143.15, -297.638, -169.37),
    normpath.normline_pt(-297.638, -169.37, -270.709, -169.37),
    normpath.normline_pt(-270.709, -169.37, -270.709, -143.15),
    normpath.normline_pt(-270.709, -143.15, -297.638, -143.15),
    normpath.normline_pt(-297.638, -143.15, -297.638, -141.732),
    normpath.normline_pt(-297.638, -141.732, -284.882, -141.732),
    normpath.normline_pt(-284.882, -141.732, -284.882, -113.386),
    normpath.normline_pt(-284.882, -113.386, -283.465, -113.386),
    normpath.normline_pt(-283.465, -113.386, -283.465, -114.803),
    normpath.normline_pt(-283.465, -114.803, -283.465, -141.732),
    normpath.normline_pt(-283.465, -141.732, -269.291, -141.732),
    normpath.normline_pt(-269.291, -141.732, -269.291, -169.37),
    normpath.normline_pt(-269.291, -169.37, -242.362, -169.37),
    normpath.normline_pt(-242.362, -169.37, -242.362, -141.732),
    normpath.normline_pt(-242.362, -141.732, -240.945, -141.732),
    normpath.normline_pt(-240.945, -141.732, -240.945, -143.15),
    normpath.normline_pt(-240.945, -143.15, -240.945, -169.37),
    normpath.normline_pt(-240.945, -169.37, -214.016, -169.37),
    normpath.normline_pt(-214.016, -169.37, -214.016, -143.15),
    normpath.normline_pt(-214.016, -143.15, -240.945, -143.15),
    normpath.normline_pt(-240.945, -143.15, -240.945, -141.732),
    normpath.normline_pt(-240.945, -141.732, -228.189, -141.732),
    normpath.normline_pt(-228.189, -141.732, -228.189, -114.803),
    normpath.normline_pt(-228.189, -114.803, -283.465, -114.803),
    normpath.normline_pt(-283.465, -114.803, -283.465, -113.386),
    normpath.normline_pt(-283.465, -113.386, -226.772, -113.386),
    normpath.normline_pt(-226.772, -113.386, -226.772, -141.732),
    normpath.normline_pt(-226.772, -141.732, -212.598, -141.732),
    normpath.normline_pt(-212.598, -141.732, -212.598, -169.37),
    normpath.normline_pt(-212.598, -169.37, -150, -169.37), # end
    #ormpath.normline_pt(-150, -169.37, -85.748, -169.37),
    #ormpath.normline_pt(-85.748, -169.37, -85.748, -35.3941),
    #ormpath.normline_pt(-85.748, -35.3941, -86.2699, -35.3254),
    #ormpath.normline_pt(-86.2699, -35.3254, -86.8735, -35.1916),
    #ormpath.normline_pt(-86.8735, -35.1916, -87.4631, -35.0057),
    #ormpath.normline_pt(-87.4631, -35.0057, -88.0343, -34.7691),
    #ormpath.normline_pt(-88.0343, -34.7691, -88.5827, -34.4836),
    #ormpath.normline_pt(-88.5827, -34.4836, -89.1041, -34.1514),
    #ormpath.normline_pt(-89.1041, -34.1514, -89.5946, -33.7751),
    #ormpath.normline_pt(-89.5946, -33.7751, -90.0504, -33.3574),
    #ormpath.normline_pt(-90.0504, -33.3574, -90.468, -32.9016),
    #ormpath.normline_pt(-90.468, -32.9016, -90.8444, -32.4111),
    #ormpath.normline_pt(-90.8444, -32.4111, -91.1765, -31.8897),
    #ormpath.normline_pt(-91.1765, -31.8897, -91.462, -31.3414),
    #ormpath.normline_pt(-91.462, -31.3414, -91.6986, -30.7702),
    #ormpath.normline_pt(-91.6986, -30.7702, -91.8845, -30.1806),
    #ormpath.normline_pt(-91.8845, -30.1806, -92.0183, -29.577),
    #ormpath.normline_pt(-92.0183, -29.577, -92.099, -28.9641),
    #ormpath.normline_pt(-92.099, -28.9641, -92.126, -28.3465),
    #ormpath.normline_pt(-92.126, -28.3465, -92.126, 157.804),
    #ormpath.normline_pt(-92.126, 157.804, -93.1688, 158.469),
    #ormpath.normline_pt(-93.1688, 158.469, -94.1498, 159.221),
    #ormpath.normline_pt(-94.1498, 159.221, -95.0613, 160.057),
    #ormpath.normline_pt(-95.0613, 160.057, -95.8967, 160.968),
    #ormpath.normline_pt(-95.8967, 160.968, -96.6494, 161.949),
    #ormpath.normline_pt(-96.6494, 161.949, -97.3138, 162.992),
    #ormpath.normline_pt(-97.3138, 162.992, -97.8847, 164.089),
    #ormpath.normline_pt(-97.8847, 164.089, -98.3578, 165.231),
    #ormpath.normline_pt(-98.3578, 165.231, -98.7297, 166.41),
    #ormpath.normline_pt(-98.7297, 166.41, -98.9973, 167.618),
    #ormpath.normline_pt(-98.9973, 167.618, -99.1587, 168.843),
    #ormpath.normline_pt(-99.1587, 168.843, -99.2126, 170.079),
    #ormpath.normline_pt(-99.2126, 170.079, -99.1587, 171.314),
    #ormpath.normline_pt(-99.1587, 171.314, -98.9973, 172.54),
    #ormpath.normline_pt(-98.9973, 172.54, -98.7297, 173.747),
    #ormpath.normline_pt(-98.7297, 173.747, -98.3578, 174.926),
    #ormpath.normline_pt(-98.3578, 174.926, -97.8847, 176.069),
    #ormpath.normline_pt(-97.8847, 176.069, -97.3138, 177.165),
    #ormpath.normline_pt(-97.3138, 177.165, -96.6494, 178.208),
    #ormpath.normline_pt(-96.6494, 178.208, -95.8967, 179.189),
    #ormpath.normline_pt(-95.8967, 179.189, -95.0613, 180.101),
    #ormpath.normline_pt(-95.0613, 180.101, -94.1498, 180.936),
    #ormpath.normline_pt(-94.1498, 180.936, -93.1688, 181.689),
    #ormpath.normline_pt(-93.1688, 181.689, -92.126, 182.353),
    #ormpath.normline_pt(-92.126, 182.353, -91.0292, 182.924),
    #ormpath.normline_pt(-91.0292, 182.924, -89.8869, 183.397),
    #ormpath.normline_pt(-89.8869, 183.397, -88.7077, 183.769),
    #ormpath.normline_pt(-88.7077, 183.769, -87.5005, 184.037),
    ], closed=1) # >>>
    p = normpath.normpath([nsp])
    c.stroke(p, [trafo.translate(*move)])
    hard_test(c, p, 0.47504345 - 5*normpath._epsilon, parallel(0.0), move, "Y", checklens=[[37,14],[37,14],[7,7],[7,7]])
    hard_test(c, p, 0.47504345 + 5*normpath._epsilon, parallel(0.0), move, "Y", checklens=[[37,7],[37,7],[7,7,7],[7,7,7]])
    hard_test(c, p, 0.5, parallel(0.0), move, "Y", checklens=[[36,7],[36,7],[6,5,6,3,7,3],[6,3,7,3,5,6]])
    hard_test(c, p, 0.6125, parallel(0.0), move, "Y", checklens=[[35],[35],[3],[3]])
    hard_test(c, p, 0.6130, parallel(0.0), move, "Y", checklens=[[35],[35],[],[]])

    # a path of two subpaths:
    # and with inner intersections to be cut away by _between_paths
    move = (0, 0)
    p = path.circle(-6, 0, 2)
    p += path.path(path.moveto(0,0), path.curveto(0,16, -11,5, 5,5))
    p += path.path(path.lineto(5,4), path.lineto(7,4), path.lineto(7,6), path.lineto(4,6),
                   path.lineto(4,7), path.lineto(5,7), path.lineto(3,1), path.closepath())
    p = p.transformed(trafo.scale(0.5)).normpath()
    hard_test(c, p, 0.05, parallel(0.0), move, "Z", checklens=[[10,2,8],[9,2,10],[13,4,4],[13,4,4]])
    hard_test(c, p, 0.3, parallel(0.0), move, "Z", checklens=[[10,4,5],[4,6,10],[13,4],[13,4]])
    hard_test(c, p, 0.6, parallel(0.0), move, "Z", checklens=[[],[],[13,4],[13,4]])


def testlinesmoothed(c):

    # dependence on turnangle
    p = path.path(path.moveto(0, 0), path.lineto(1, 0), path.lineto(2, 1), path.lineto(4, -1),
                  path.lineto(5, 0), path.lineto(6, 0))
    c.stroke(p)
    d = linesmoothed()
    c.stroke(p, [d])
    c.stroke(p, [d(atleast=True), color.rgb.red])
    c.stroke(p, [d(lcurl=None), color.rgb.green])
    c.stroke(p, [d(rcurl=None), color.rgb.blue])

    p.append(path.lineto(3, 3))
    p.append(path.closepath())

    c.stroke(p, [d, color.cmyk.Orange])

c=canvas.canvas()
dotest(c, 0, -12, "testparallel_1")
dotest(c, 6, 13, "testparallel_2")
dotest(c, 16, 12, "testlinesmoothed")
dotest(c, 16, 4, "testcycloid")
dotest(c, 20, -10, "testcornersmoothed")
c.writeEPSfile("test_deformer", page_paperformat=document.paperformat.A4, page_rotated=0, page_fittosize=1)
c.writePDFfile("test_deformer")
c.writeSVGfile("test_deformer")

# vim:foldmethod=marker:foldmarker=<<<,>>>
