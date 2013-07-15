import sys; sys.path.insert(0, "../..")

import math
from pyx import *
from pyx import normpath

# make math.sqrt raising an exception for negativ values
try:
    math.sqrt(-1)
except:
    pass
else:
    math._sqrt = math.sqrt
    def mysqrt(x):
        if x < 0:
            raise ValueError("sqrt of negativ number")
        return math._sqrt(x)
    math.sqrt = mysqrt


c = canvas.canvas()

def connect(normpathitem1, normpathitem2, round):
    "returns a list of normsubpathitems connecting normpathitem1 and normpathitem2 either rounded or not"
    # this is for corners, i.e. when there are jumps in the tangent vector
    t1 = normpathitem1.trafo([1])[0]
    t2 = normpathitem2.trafo([0])[0]
    xs, ys = t1.apply_pt(0, 0)
    xe, ye = t2.apply_pt(0, 0)
    if (xs-xe)*(xs-xe) + (xs-xe)*(xs-xe) < 1e-5**2:
        return []
    if round:
        # calculate crossing point of normal
        try:
            param = ((t2.matrix[0][1]*(t1.vector[1]-t2.vector[1]) -
                      t2.matrix[1][1]*(t1.vector[0]-t2.vector[0])) /
                     (t2.matrix[1][1]*t1.matrix[0][1] -
                      t2.matrix[0][1]*t1.matrix[1][1]))
        except ArithmeticError:
            return [path.normline_pt(xs, ys, xe, ye)]
        else:
            # since t1 is a translation + rotation, param is the radius
            # hence, param should be equal to enlargeby_pt
            # print param
            x, y = t1.apply_pt(0, param)
            # c.fill(path.circle_pt(x, y, 1))
            angle1 = math.atan2(ys-y, xs-x)
            angle2 = math.atan2(ye-y, xe-x)
            while angle2 < angle1:
                angle1 -= 2*math.pi
            return [path._arctobcurve(x, y, param, angle1, angle2)]
    else:
        # calculate crossing point of tangents
        try:
            param = ((t2.matrix[0][0]*(t1.vector[1]-t2.vector[1]) -
                      t2.matrix[1][0]*(t1.vector[0]-t2.vector[0])) / 
                     (t2.matrix[1][0]*t1.matrix[0][0] -
                      t2.matrix[0][0]*t1.matrix[1][0]))
        except ArithmeticError:
            return [path.normline_pt(xs, ys, xe, ye)]
        else:
            x, y = t1.apply_pt(param, 0)
            return [path.normline_pt(xs, ys, x, y), path.normline_pt(x, y, xe, ye)]


def enlarged(anormpath, enlargeby_pt, round):
    newnormsubpaths = []
    for normsubpath in anormpath.normsubpaths:
        splitnormsubpathitems = normsubpath.normsubpathitems[:] # do splitting on a copy
        i = 0
        while i < len(splitnormsubpathitems):
            if isinstance(splitnormsubpathitems[i], normpath.normcurve_pt) and splitnormsubpathitems[i].arclen_pt(normsubpath.epsilon) > 100:
                splitnormsubpathitems[i:i+1] = splitnormsubpathitems[i]._midpointsplit(normsubpath.epsilon)
            else:
                i += 1
        newnormsubpathitems = []
        for normsubpathitem in splitnormsubpathitems:
            # get old and new start and end points
            ts, te = normsubpathitem.trafo([0, 1])
            xs, ys = ts.apply_pt(0, 0)
            nxs, nys = ts.apply_pt(0, -enlargeby_pt)
            xe, ye = te.apply_pt(0, 0)
            nxe, nye = te.apply_pt(0, -enlargeby_pt)

            if isinstance(normsubpathitem, normpath.normcurve_pt):
                # We should do not alter the sign. Could we do any better here?
                try:
                    cs = 1/(normsubpathitem.curveradius_pt([0])[0] + enlargeby_pt)
                except ArithmeticError:
                    cs = 0
                try:
                    ce = 1/(normsubpathitem.curveradius_pt([1])[0] + enlargeby_pt)
                except ArithmeticError:
                    ce = 0

                # this should be a function (in path?), not a method in a class
                # the parameter convention is quite different from other places ...
                bezierparams = deformer.normcurve_from_endgeometry_pt((nxs, nys), (nxe, nye),
                                                                      (ts.matrix[0][0], ts.matrix[1][0]),
                                                                      (te.matrix[0][0], te.matrix[1][0]),
                                                                      cs, ce)
                c.fill(path.circle_pt(bezierparams.x0_pt, bezierparams.y0_pt, 1), [color.rgb.blue])
                c.fill(path.circle_pt(bezierparams.x3_pt, bezierparams.y3_pt, 1), [color.rgb.blue])
                newnormpathitems = normpath.normcurve_pt(bezierparams.x0_pt, bezierparams.y0_pt,
                                               bezierparams.x1_pt, bezierparams.y1_pt,
                                               bezierparams.x2_pt, bezierparams.y2_pt,
                                               bezierparams.x3_pt, bezierparams.y3_pt)
                showtangent(newnormpathitems) # line alignment of bezier curves
                showcircle(newnormpathitems)  # circle alignment of bezier curves
            else:
                # line
                newnormpathitems = path.normline_pt(nxs, nys, nxe, nye)

            if len(newnormsubpathitems):
                newnormsubpathitems.extend(connect(newnormsubpathitems[-1], newnormpathitems, round=round))
            newnormsubpathitems.append(newnormpathitems)
        if normsubpath.closed:
            newnormsubpathitems.extend(connect(newnormsubpathitems[-1], newnormsubpathitems[0], round=round))
        newnormsubpaths.append(path.normsubpath(newnormsubpathitems, normsubpath.closed))
    return normpath.normpath(newnormsubpaths)


def showtangent(normcurve_pt):
    dx = 2
    dy = 1

    cx =                                       3*normcurve_pt.x1_pt - 3*normcurve_pt.x0_pt
    bx =                   3*normcurve_pt.x2_pt - 6*normcurve_pt.x1_pt + 3*normcurve_pt.x0_pt
    ax = normcurve_pt.x3_pt - 3*normcurve_pt.x2_pt + 3*normcurve_pt.x1_pt -   normcurve_pt.x0_pt

    cy =                                       3*normcurve_pt.y1_pt - 3*normcurve_pt.y0_pt
    by =                   3*normcurve_pt.y2_pt - 6*normcurve_pt.y1_pt + 3*normcurve_pt.y0_pt
    ay = normcurve_pt.y3_pt - 3*normcurve_pt.y2_pt + 3*normcurve_pt.y1_pt -   normcurve_pt.y0_pt

    try:
        x = - (dy*bx-dx*by)/(3.0*dy*ax-3.0*dx*ay)
        s = math.sqrt(x*x-(dy*cx-dx*cy)/(3.0*dy*ax-3.0*dx*ay))
    except (ArithmeticError, ValueError):
        return
    t1 = x-s
    t2 = x+s
    ts = []
    if 0 < t1 < 1:
        ts.append(t1)
    if 0 < t2 < 1:
        ts.append(t2)
    for t in ts:
        trafo = normcurve_pt.trafo([t])[0]
        x, y = trafo.apply_pt(0, 0)
        c.fill(path.circle_pt(x, y, 1), [color.rgb.red])
        c.stroke(path.line_pt(*list(trafo.apply_pt(-100, 0))+list(trafo.apply_pt(100, 0))), [color.rgb.red])

def showcircle(normcurve_pt):
    gx = 350
    gy = 200
    hx = -1
    hy = 2
    cos = hx/math.sqrt(hx*hx+hy*hy)
    sin = hy/math.sqrt(hx*hx+hy*hy)

    r = 16

    dx =                                                             normcurve_pt.x0_pt
    cx =                                       3*normcurve_pt.x1_pt - 3*normcurve_pt.x0_pt
    bx =                   3*normcurve_pt.x2_pt - 6*normcurve_pt.x1_pt + 3*normcurve_pt.x0_pt
    ax = normcurve_pt.x3_pt - 3*normcurve_pt.x2_pt + 3*normcurve_pt.x1_pt -   normcurve_pt.x0_pt

    dy =                                                             normcurve_pt.y0_pt
    cy =                                       3*normcurve_pt.y1_pt - 3*normcurve_pt.y0_pt
    by =                   3*normcurve_pt.y2_pt - 6*normcurve_pt.y1_pt + 3*normcurve_pt.y0_pt
    ay = normcurve_pt.y3_pt - 3*normcurve_pt.y2_pt + 3*normcurve_pt.y1_pt -   normcurve_pt.y0_pt

    def x(t, gx=gx):
        return ax*t*t*t+bx*t*t+cx*t+normcurve_pt.x0_pt
    def y(t, gy=gy):
        return ay*t*t*t+by*t*t+cy*t+normcurve_pt.y0_pt
    def xdot(t):
        return 3*ax*t*t+2*bx*t+cx
    def ydot(t):
        return 3*ay*t*t+2*by*t+cy

    # we need to find roots of the following polynom:
    # (xdot(t)**2+ydot(t)**2)*((x(t)-gx)*hy-(y(t)-gy)*hx)**2-r*r*(xdot(t)*hx+ydot(t)*hy)**2 == 0

    # the polynom is of order 10. its coefficients are:

    coeffs = [9*(ax**2+ay**2)*(hy*ax-ay*hx)**2, # * t**10,

              -6*(hy*ax-ay*hx)*(-5*ax**2*bx*hy+3*ax**2*hx*by-2*ax*by*ay*hy+
              2*ax*hx*bx*ay-3*ay**2*bx*hy+5*hx*ay**2*by), # * t**9, etc.

              -30*hy*hx*ay*ax**2*cx-32*hy*hx*ay*bx**2*ax-42*hy*hx*bx*ax**2*by-18*hy*hx*ax**3*cy+
              24*hy**2*ax**3*cx+37*hy**2*bx**2*ax**2+24*hx**2*ay**3*cy+37*hx**2*by**2*ay**2-
              30*hy*hx*ay**2*ax*cy-32*hy*hx*ay*ax*by**2-42*hy*hx*by*ay**2*bx-18*hy*hx*ay**3*cx+
              6*hy**2*ax**2*cy*ay+4*hy**2*ax**2*by**2+24*hy**2*bx*ax*by*ay+18*hy**2*ay**2*cx*ax+
              9*hy**2*ay**2*bx**2+6*hx**2*ay**2*cx*ax+4*hx**2*ay**2*bx**2+24*hx**2*bx*ax*by*ay+
              18*hx**2*ax**2*cy*ay+9*hx**2*ax**2*by**2,

              20*hx**2*by**3*ay+8*hx**2*by*ay*bx**2+4*hx**2*cx*bx*ay**2-18*hx**2*ax**2*ay*gy+
              18*hx**2*ax**2*ay*dy+20*hy**2*bx**3*ax+18*hy**2*ax**3*dx+12*hx**2*by*ay*cx*ax+18*
              hx**2*cy*by*ax**2+12*hx**2*bx*ax*by**2+8*hy**2*bx*ax*by**2+4*hy**2*cy*by*ax**2-
              18*hy**2*ay**2*ax*gx+18*hy**2*ay**2*ax*dx+18*hy**2*cx*bx*ay**2+12*hy**2*by*ay*bx**2
              +58*hy**2*cx*bx*ax**2-8*hy*hx*ay*bx**3+18*hy*hx*ax**3*gy-18*hy*hx*ax**3*dy-
              18*hy*hx*ay**3*dx-8*hy*hx*ax*by**3+58*hx**2*cy*by*ay**2+24*hx**2*bx*ax*cy*ay+
              12*hy**2*bx*ax*cy*ay+24*hy**2*by*ay*cx*ax-18*hy**2*ax**3*gx-44*hy*hx*ay*cx*bx*ax+
              18*hy*hx*ay*ax**2*gx-18*hy*hx*ay*ax**2*dx-30*hy*hx*by*ax**2*cx-32*hy*hx*by*bx**2*ax-
              42*hy*hx*bx*ax**2*cy+18*hy*hx*ay**3*gx-44*hy*hx*ay*cy*by*ax-30*hy*hx*bx*cy*ay**2-
              32*hy*hx*ay*bx*by**2-42*hy*hx*by*ay**2*cx+18*hy*hx*ay**2*ax*gy-
              18*hy*hx*ay**2*ax*dy-18*hx**2*ay**3*gy+18*hx**2*ay**3*dy,

              hx**2*cx**2*ay**2+46*hy**2*cx*bx**2*ax-42*hy**2*bx*ax**2*gx+42*hy**2*bx*ax**2*dx+
              46*hx**2*cy*by**2*ay-42*hx**2*by*ay**2*gy+42*hx**2*by*ay**2*dy-8*hy*hx*bx*by**3+
              6*hy**2*cy*ay*bx**2+8*hy**2*by**2*cx*ax-18*hy**2*ay**2*bx*gx+18*hy**2*ay**2*bx*dx+
              6*hx**2*by**2*cx*ax+8*hx**2*cy*ay*bx**2-18*hx**2*ax**2*by*gy+18*hx**2*ax**2*by*dy-
              8*hy*hx*by*bx**3+4*hy**2*bx**4+22*hy**2*cx**2*ax**2+22*hx**2*cy**2*ay**2+hy**2*cy**2*ax**2+
              4*hy**2*by**2*bx**2+9*hy**2*cx**2*ay**2+4*hx**2*by**2*bx**2+9*hx**2*cy**2*ax**2+
              4*hx**2*by**4-14*hy*hx*ay*cy**2*ax-44*hy*hx*ay*cy*by*bx-30*hy*hx*cx*cy*ay**2-
              32*hy*hx*ay*cx*by**2+42*hy*hx*by*ay**2*gx-42*hy*hx*by*ay**2*dx-16*hy*hx*cy*by**2*ax+
              24*hy*hx*by*ay*ax*gy-24*hy*hx*by*ay*ax*dy+18*hy*hx*ay**2*bx*gy-18*hy*hx*ay**2*bx*dy+
              8*hy**2*cy*by*bx*ax+12*hy**2*cy*ay*cx*ax-24*hy**2*by*ay*ax*gx+24*hy**2*by*ay*ax*dx+
              24*hy**2*cx*bx*by*ay+8*hx**2*cx*bx*by*ay+12*hx**2*cy*ay*cx*ax-24*hx**2*bx*ax*ay*gy+
              24*hx**2*bx*ax*ay*dy+24*hx**2*cy*by*bx*ax-14*hy*hx*ay*cx**2*ax-16*hy*hx*ay*cx*bx**2+
              24*hy*hx*ay*bx*ax*gx-24*hy*hx*ay*bx*ax*dx-44*hy*hx*by*cx*bx*ax+18*hy*hx*by*ax**2*gx-
              18*hy*hx*by*ax**2*dx-30*hy*hx*cy*ax**2*cx-32*hy*hx*cy*bx**2*ax+42*hy*hx*bx*ax**2*gy-
              42*hy*hx*bx*ax**2*dy,

              12*hx**2*cy*by**3+12*hy**2*cx*bx**3+34*hx**2*cy**2*by*ay-30*hx**2*cy*ay**2*gy+
              30*hx**2*cy*ay**2*dy-32*hx**2*by**2*ay*gy+32*hx**2*by**2*ay*dy+2*hx**2*cx**2*by*ay+
              4*hx**2*cx*bx*by**2-8*hx**2*bx**2*ay*gy+8*hx**2*bx**2*ay*dy+8*hx**2*bx**2*cy*by+
              12*hx**2*cy**2*bx*ax-18*hx**2*ax**2*cy*gy+8*hx**2*cx*bx*cy*ay-12*hx**2*cx*ax*ay*gy+
              12*hx**2*cx*ax*ay*dy+12*hx**2*cx*ax*cy*by-24*hx**2*bx*ax*by*gy+24*hx**2*bx*ax*by*dy+
              18*hx**2*ax**2*cy*dy-8*hy*hx*cy*bx**3-8*hy*hx*cx*by**3+34*hy**2*cx**2*bx*ax-
              30*hy**2*cx*ax**2*gx+30*hy**2*cx*ax**2*dx-32*hy**2*bx**2*ax*gx+32*hy**2*bx**2*ax*dx+
              2*hy**2*cy**2*bx*ax+4*hy**2*bx**2*cy*by-8*hy**2*by**2*ax*gx+8*hy**2*by**2*ax*dx+
              8*hy**2*cx*bx*by**2+12*hy**2*cx**2*by*ay-18*hy**2*ay**2*cx*gx+18*hy**2*ay**2*cx*dx-
              10*hy*hx*ay*cx**2*bx+12*hy*hx*ay*cx*ax*gx-12*hy*hx*ay*cx*ax*dx+
              8*hy*hx*ay*bx**2*gx-8*hy*hx*ay*bx**2*dx-14*hy*hx*by*cx**2*ax-16*hy*hx*by*cx*bx**2+
              24*hy*hx*by*bx*ax*gx-24*hy*hx*by*bx*ax*dx-44*hy*hx*cy*cx*bx*ax+18*hy*hx*cy*ax**2*gx-
              18*hy*hx*cy*ax**2*dx+30*hy*hx*ax**2*cx*gy-30*hy*hx*ax**2*cx*dy+32*hy*hx*bx**2*ax*gy-
              32*hy*hx*bx**2*ax*dy-32*hy*hx*ay*by**2*dx-16*hy*hx*cy*by**2*bx+8*hy*hx*ax*by**2*gy+
              32*hy*hx*ay*by**2*gx-44*hy*hx*ay*cy*by*cx+12*hy*hx*ax*cy*ay*gy-12*hy*hx*ax*cy*ay*dy+
              24*hy*hx*by*ay*bx*gy-24*hy*hx*by*ay*bx*dy+30*hy*hx*cy*ay**2*gx-30*hy*hx*cy*ay**2*dx-
              14*hy*hx*ay*cy**2*bx-10*hy*hx*by*cy**2*ax-8*hy*hx*ax*by**2*dy+18*hy*hx*ay**2*cx*gy-
              18*hy*hx*ay**2*cx*dy+8*hy**2*cx*ax*cy*by-12*hy**2*cy*ay*ax*gx+12*hy**2*cy*ay*ax*dx+
              12*hy**2*cx*bx*cy*ay-24*hy**2*by*ay*bx*gx+24*hy**2*by*ay*bx*dx,

              hy**2*bx**2*cy**2+13*hy**2*cx**2*bx**2+9*hx**2*ax**2*gy**2-9*r**2*ax**2*hx**2-
              9*r**2*ay**2*hy**2+9*hx**2*ax**2*dy**2+hx**2*cx**2*by**2+4*hx**2*bx**2*cy**2+8*hy**2*cx**3*ax+
              8*hx**2*cy**3*ay+13*hx**2*cy**2*by**2-8*hx**2*by**3*gy+8*hx**2*by**3*dy+9*hx**2*ay**2*gy**2+
              9*hx**2*ay**2*dy**2+4*hy**2*cx**2*by**2+9*hy**2*ay**2*gx**2+9*hy**2*ay**2*dx**2-8*hy**2*bx**3*gx+
              8*hy**2*bx**3*dx+9*hy**2*ax**2*gx**2+9*hy**2*ax**2*dx**2-18*hx**2*ay**2*gy*dy+2*hx**2*cx**2*cy*ay+
              6*hx**2*cx*ax*cy**2-8*hx**2*bx**2*by*gy+8*hx**2*bx**2*by*dy-18*hx**2*ax**2*gy*dy+8*hy*hx*by**3*gx-
              8*hy*hx*by**3*dx-2*hy*hx*cy**3*ax+2*hy**2*cx*ax*cy**2+6*hy**2*cx**2*cy*ay-8*hy**2*by**2*bx*gx+
              8*hy**2*by**2*bx*dx-18*hy**2*ay**2*gx*dx-18*hy**2*ax**2*gx*dx-18*r**2*ax*ay*hx*hy-
              44*hx**2*cy*by*ay*gy+44*hx**2*cy*by*ay*dy-8*hx**2*cx*bx*ay*gy+8*hx**2*cx*bx*ay*dy+
              8*hx**2*cx*bx*cy*by-12*hx**2*cx*ax*by*gy+12*hx**2*cx*ax*by*dy-24*hx**2*bx*ax*cy*gy+
              24*hx**2*bx*ax*cy*dy+8*hy*hx*bx*by**2*gy-8*hy*hx*bx*by**2*dy+18*hy*hx*ay**2*dx*gy-
              14*hy*hx*ay*cy**2*cx-18*hy*hx*ay**2*gx*gy-18*hy*hx*ay**2*dx*dy-16*hy*hx*cy*by**2*cx+
              18*hy*hx*ay**2*gx*dy-10*hy*hx*by*cy**2*bx+44*hy*hx*ay*cy*by*gx-44*hy*hx*ay*cy*by*dx+
              8*hy*hx*cy*by*ax*gy-8*hy*hx*cy*by*ax*dy+12*hy*hx*bx*cy*ay*gy-12*hy*hx*bx*cy*ay*dy+
              24*hy*hx*by*ay*cx*gy-24*hy*hx*by*ay*cx*dy-8*hy**2*cy*by*ax*gx+8*hy**2*cy*by*ax*dx+
              8*hy**2*cx*bx*cy*by-12*hy**2*cy*ay*bx*gx+12*hy**2*cy*ay*bx*dx-24*hy**2*by*ay*cx*gx+
              24*hy**2*by*ay*cx*dx-44*hy**2*cx*bx*ax*gx+44*hy**2*cx*bx*ax*dx-2*hy*hx*ay*cx**3+
              8*hy*hx*bx**3*gy-8*hy*hx*bx**3*dy+8*hy*hx*ay*cx*bx*gx-8*hy*hx*ay*cx*bx*dx-
              10*hy*hx*by*cx**2*bx+12*hy*hx*by*cx*ax*gx-12*hy*hx*by*cx*ax*dx+8*hy*hx*by*bx**2*gx-
              8*hy*hx*by*bx**2*dx-14*hy*hx*cy*cx**2*ax-16*hy*hx*cy*cx*bx**2+24*hy*hx*cy*bx*ax*gx-
              24*hy*hx*cy*bx*ax*dx+44*hy*hx*cx*bx*ax*gy-44*hy*hx*cx*bx*ax*dy-18*hy*hx*ax**2*gx*gy+
              18*hy*hx*ax**2*gx*dy+18*hy*hx*ax**2*dx*gy-18*hy*hx*ax**2*dx*dy,

              6*hx**2*cy**3*by-24*hx**2*by*ay*gy*dy-8*hy**2*cy*by*bx*gx-14*hy**2*cx**2*ax*gx-
              12*hy*hx*r**2*bx*ay+2*hy*hx*cx**2*ay*gx-12*r**2*bx*ax*hx**2-12*r**2*by*ay*hy**2+
              16*hy**2*cx*bx**2*dx+6*hy**2*cx**3*bx-16*hy**2*cx*bx**2*gx+14*hy**2*cx**2*ax*dx+
              12*hy**2*bx*ax*gx**2+12*hy**2*bx*ax*dx**2-2*hy*hx*by*cx**3+4*hx**2*cx*bx*cy**2-
              2*hx**2*cx**2*ay*gy+2*hx**2*cx**2*ay*dy+2*hx**2*cx**2*cy*by+12*hx**2*bx*ax*gy**2+
              12*hx**2*bx*ax*dy**2-8*hx**2*cy*bx**2*gy+8*hx**2*cy*bx**2*dy+16*hx**2*cy*by**2*dy-
              14*hx**2*cy**2*ay*gy+14*hx**2*cy**2*ay*dy+12*hx**2*by*ay*gy**2+12*hx**2*by*ay*dy**2+
              4*hy**2*cx**2*cy*by-2*hy**2*cy**2*ax*gx+2*hy**2*cy**2*ax*dx+2*hy**2*cx*bx*cy**2+
              12*hy**2*by*ay*gx**2+12*hy**2*by*ay*dx**2-8*hy**2*cx*by**2*gx+8*hy**2*cx*by**2*dx-
              24*hy**2*bx*ax*gx*dx-2*hy*hx*cx**2*ay*dx+8*hy*hx*by*cx*bx*gx-8*hy*hx*by*cx*bx*dx-
              10*hy*hx*cy*cx**2*bx+12*hy*hx*cy*cx*ax*gx-12*hy*hx*cy*cx*ax*dx+8*hy*hx*cy*bx**2*gx-
              8*hy*hx*cy*bx**2*dx+14*hy*hx*cx**2*ax*gy-14*hy*hx*cx**2*ax*dy+16*hy*hx*cx*bx**2*gy-
              16*hy*hx*cx*bx**2*dy-24*hy*hx*bx*ax*gx*gy+24*hy*hx*bx*ax*gx*dy+24*hy*hx*bx*ax*dx*gy-
              24*hy*hx*bx*ax*dx*dy-2*hy*hx*cy**3*bx+14*hy*hx*cy**2*ay*gx-14*hy*hx*cy**2*ay*dx-
              10*hy*hx*by*cy**2*cx+16*hy*hx*cy*by**2*gx-16*hy*hx*cy*by**2*dx+2*hy*hx*cy**2*ax*gy-
              2*hy*hx*cy**2*ax*dy+8*hy*hx*cy*by*bx*gy-8*hy*hx*cy*by*bx*dy+12*hy*hx*cx*cy*ay*gy-
              12*hy*hx*cx*cy*ay*dy+8*hy*hx*cx*by**2*gy-8*hy*hx*cx*by**2*dy-24*hy*hx*by*ay*gx*gy+
              24*hy*hx*by*ay*gx*dy+24*hy*hx*by*ay*dx*gy-24*hy*hx*by*ay*dx*dy-8*hx**2*cx*bx*by*gy+
              8*hx**2*cx*bx*by*dy-24*hx**2*bx*ax*gy*dy-12*hx**2*cy*cx*ax*gy+12*hx**2*cy*cx*ax*dy-
              16*hx**2*cy*by**2*gy+8*hy**2*cy*by*bx*dx-24*hy**2*by*ay*gx*dx-12*hy**2*cx*cy*ay*gx+
              12*hy**2*cx*cy*ay*dx-12*hy*hx*r**2*ax*by,

              hy**2*cy**2*cx**2-4*r**2*hy**2*by**2+4*hx**2*bx**2*dy**2+4*hx**2*by**2*gy**2-
              4*r**2*hx**2*bx**2+4*hy**2*by**2*dx**2+4*hy**2*by**2*gx**2+4*hx**2*by**2*dy**2+
              hx**2*cy**2*cx**2+4*hy**2*bx**2*dx**2+8*hy**2*cy*by*cx*dx+4*hx**2*bx**2*gy**2+
              2*hy*hx*cy**2*bx*gy+4*hy**2*bx**2*gx**2-2*hy*hx*cy**2*bx*dy-10*hy*hx*cy**2*by*dx-
              8*hy**2*cy*by*cx*gx+10*hy*hx*cy**2*by*gx-6*hy*hx*r**2*cx*ay-10*hx**2*cy**2*by*gy+
              10*hx**2*cy**2*by*dy+6*hx**2*cy*ay*gy**2+6*hx**2*cy*ay*dy**2-8*hx**2*by**2*gy*dy-
              10*hy**2*cx**2*bx*gx+10*hy**2*cx**2*bx*dx+6*hy**2*cx*ax*gx**2+6*hy**2*cx*ax*dx**2-
              8*hy**2*bx**2*gx*dx-6*r**2*hx**2*cx*ax-2*hy**2*cy**2*bx*gx+2*hy**2*cy**2*bx*dx+
              6*hy**2*cy*ay*gx**2+6*hy**2*cy*ay*dx**2-8*hy**2*by**2*gx*dx-2*hy*hx*cy**3*cx-
              6*r**2*hy**2*cy*ay-2*hy*hx*cy*cx**3-2*hx**2*cx**2*by*gy+2*hx**2*cx**2*by*dy+
              6*hx**2*cx*ax*gy**2+6*hx**2*cx*ax*dy**2-8*hx**2*bx**2*gy*dy+hx**2*cy**4+
              hy**2*cx**4-12*hx**2*cy*ay*gy*dy-12*hy**2*cx*ax*gx*dx-8*hy*hx*r**2*bx*by-
              6*hy*hx*r**2*ax*cy-12*hy**2*cy*ay*gx*dx+8*hy*hx*cy*by*cx*gy-8*hy*hx*cy*by*cx*dy-
              12*hy*hx*cy*ay*gx*gy+12*hy*hx*cy*ay*gx*dy+12*hy*hx*cy*ay*dx*gy-
              12*hy*hx*cy*ay*dx*dy-8*hy*hx*by**2*gx*gy+8*hy*hx*by**2*gx*dy+8*hy*hx*by**2*dx*gy-
              8*hy*hx*by**2*dx*dy+2*hy*hx*cx**2*by*gx-2*hy*hx*cx**2*by*dx+8*hy*hx*cy*cx*bx*gx-
              8*hy*hx*cy*cx*bx*dx+10*hy*hx*cx**2*bx*gy-10*hy*hx*cx**2*bx*dy-12*hy*hx*cx*ax*gx*gy+
              12*hy*hx*cx*ax*gx*dy+12*hy*hx*cx*ax*dx*gy-12*hy*hx*cx*ax*dx*dy-8*hy*hx*bx**2*gx*gy+
              8*hy*hx*bx**2*gx*dy+8*hy*hx*bx**2*dx*gy-8*hy*hx*bx**2*dx*dy-8*hx**2*cx*bx*cy*gy+
              8*hx**2*cx*bx*cy*dy-12*hx**2*cx*ax*gy*dy,

              -2*hx**2*cy**3*gy-2*hy**2*cx**3*gx+2*hy**2*cx**3*dx-4*hy*hx*r**2*cx*by+
              2*hy*hx*cy*cx**2*gx+2*hx**2*cy**3*dy-4*r**2*cx*bx*hx**2-4*r**2*cy*by*hy**2-
              2*hy**2*cy**2*cx*gx+2*hy**2*cy**2*cx*dx+4*hy**2*cy*by*gx**2+4*hy**2*cy*by*dx**2+
              4*hx**2*cy*by*gy**2+4*hx**2*cy*by*dy**2+2*hy*hx*cx**3*gy-2*hy*hx*cx**3*dy+
              4*hy**2*cx*bx*gx**2+4*hy**2*cx*bx*dx**2-2*hx**2*cy*cx**2*gy+2*hx**2*cy*cx**2*dy+
              4*hx**2*cx*bx*gy**2+4*hx**2*cx*bx*dy**2+2*hy*hx*cy**3*gx-2*hy*hx*cy**3*dx-
              8*hy**2*cy*by*gx*dx-4*hy*hx*r**2*bx*cy-8*hx**2*cy*by*gy*dy-2*hy*hx*cy*cx**2*dx-
              8*hy*hx*cx*bx*gx*gy+8*hy*hx*cx*bx*gx*dy+8*hy*hx*cx*bx*dx*gy-
              8*hy*hx*cx*bx*dx*dy-8*hy**2*cx*bx*gx*dx-8*hx**2*cx*bx*gy*dy+2*hy*hx*cy**2*cx*gy-
              2*hy*hx*cy**2*cx*dy-8*hy*hx*cy*by*gx*gy+8*hy*hx*cy*by*gx*dy+
              8*hy*hx*cy*by*dx*gy-8*hy*hx*cy*by*dx*dy,

              cx**2*hy**2*gx**2-2*cx**2*hy**2*gx*dx+cx**2*hy**2*dx**2-2*r**2*hx*hy*cx*cy+
              cy**2*hx**2*gy**2-2*cy**2*hx**2*gy*dy+cy**2*hx**2*dy**2+cy**2*hy**2*gx**2-
              2*cy**2*hy**2*gx*dx+cy**2*hy**2*dx**2-2*cy**2*hx*hy*gy*gx+2*cy**2*hx*hy*dy*gx+
              2*cy**2*hx*hy*gy*dx-2*cy**2*hx*hy*dy*dx+cx**2*hx**2*gy**2-2*cx**2*hx**2*gy*dy+
              cx**2*hx**2*dy**2-r**2*hy**2*cy**2-2*cx**2*hx*hy*gy*gx+2*cx**2*hx*hy*dy*gx+
              2*cx**2*hx*hy*gy*dx-2*cx**2*hx*hy*dy*dx-r**2*hx**2*cx**2]

    # def z(t):
    #     res = 0
    #     for x in coeffs:
    #         res = res*t + x
    #     return res

    # def zdot(t):
    #     res = 0
    #     i = len(coeffs)
    #     for x in coeffs[:-1]:
    #         res = res*t + (i-1)*x
    #         i -= 1
    #     return res

    # def newton(t):
    #     # newton iteration to find the zero of z with t being the starting value for t
    #     if t < 0: t = 0
    #     if t > 1: t = 1
    #     slow = 1
    #     try:
    #         isz=z(t)
    #     except (ValueError, ArithmeticError):
    #         return
    #     loop = 0
    #     while abs(isz) > 1e-6:
    #         try:
    #             nt = t - slow * isz/zdot(t)
    #             newisz = z(nt)
    #         except (ValueError, ArithmeticError):
    #             slow *= 0.5 # we might have slow down the newton iteration
    #         else:
    #             t = nt
    #             isz = newisz
    #             if slow <= 0.5:
    #                 slow *= 2
    #         if loop > 100:
    #             break
    #         loop += 1
    #     else:
    #         return t

    # def ts():
    #     epsilon = 1e-5
    #     res = []
    #     count = 100
    #     for x in range(count+1):
    #        t = newton(x/float(count))
    #        if t is not None and 0-0.5*epsilon < t < 1+0.5*epsilon:
    #            res.append(t)
    #     res.sort()
    #     i = 1
    #     while len(res) > i:
    #         if res[i] > res[i-1] + epsilon:
    #             i += 1
    #         else:
    #             del res[i]
    #     return res

    # use Numeric to find the roots (via an equivalent eigenvalue problem)
    import Numeric, LinearAlgebra
    mat = Numeric.zeros((10, 10), Numeric.Float)
    for i in range(9):
        mat[i+1][i] = 1
    for i in range(10):
        mat[0][i] = -coeffs[i+1]/coeffs[0]
    ists = [zero.real for zero in LinearAlgebra.eigenvalues(mat) if -1e-10 < zero.imag < 1e-10 and 0 <= zero.real <= 1]

    for t in ists:
        isl = (xdot(t)*(x(t)-gx)+ydot(t)*(y(t)-gy))/(xdot(t)*cos+ydot(t)*sin)
        c.fill(path.circle_pt(x(t), y(t), 1), [color.rgb.green])
        c.stroke(path.circle_pt(gx+isl*cos, gy+isl*sin, r), [color.rgb.green])


# parameters for the enlargement:
enlargeby_pt = 10
round = 0 # a boolean to turn round corners on and off

# some examples:
for anormpath in [path.rect(0, 0, 5, 5).normpath(),
                 path.circle(10, 3, 3).normpath(),
                 path.path(path.moveto(0, 8),
                           path.curveto(1, 8, 1, 9, 2, 11),
                           path.curveto(1, 12, 1, 12, 0, 11),
                           path.lineto(0, 8),
                           path.closepath()).normpath(),
                 path.path(path.moveto(5, 8),
                           path.curveto(20, 8, 6, 9, 7, 11),
                           path.curveto(6, 12, 6, 12, 5, 11),
                           path.lineto(5, 8),
                           path.closepath()).normpath(),
                 path.path(path.moveto(16, 0),
                           path.curveto(18, 0, 18, 4, 20, 4),
                           path.lineto(20, 12),
                           path.curveto(12, 12, 20, 8, 16, 8),
                           path.closepath()).normpath()]:
    c.stroke(anormpath)
    c.stroke(enlarged(anormpath, enlargeby_pt, round), [color.rgb.blue])

c.writeEPSfile("newbox")
