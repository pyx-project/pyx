import sys; sys.path.insert(0, "../..")

import math
from pyx import *

c = canvas.canvas()

# I'm missing some basic functionality ...
def normpatheltrafo(normpathel, param):
    tx, ty = normpathel.at_pt(param)
    tdx, tdy = normpathel.tangentvector_pt(param)
    return trafo.translate_pt(tx, ty)*trafo.rotate(math.degrees(math.atan2(tdy, tdx)))

def normpathelbegintrafo(normpathel):
    if isinstance(normpathel, path.normcurve):
        tx, ty = normpathel.x0_pt, normpathel.y0_pt
        tdx, tdy = normpathel.x1_pt - normpathel.x0_pt, normpathel.y1_pt - normpathel.y0_pt
        return trafo.translate_pt(tx, ty)*trafo.rotate(math.degrees(math.atan2(tdy, tdx)))
    else:
        tx, ty = normpathel.x0_pt, normpathel.y0_pt
        tdx, tdy = normpathel.x1_pt - normpathel.x0_pt, normpathel.y1_pt - normpathel.y0_pt
        return trafo.translate_pt(tx, ty)*trafo.rotate(math.degrees(math.atan2(tdy, tdx)))

def normpathelendtrafo(normpathel):
    if isinstance(normpathel, path.normcurve):
        tx, ty = normpathel.x3_pt, normpathel.y3_pt
        tdx, tdy = normpathel.x3_pt - normpathel.x2_pt, normpathel.y3_pt - normpathel.y2_pt
        return trafo.translate_pt(tx, ty)*trafo.rotate(math.degrees(math.atan2(tdy, tdx)))
    else:
        tx, ty = normpathel.x1_pt, normpathel.y1_pt
        tdx, tdy = normpathel.x1_pt - normpathel.x0_pt, normpathel.y1_pt - normpathel.y0_pt
        return trafo.translate_pt(tx, ty)*trafo.rotate(math.degrees(math.atan2(tdy, tdx)))

def connect(normpathel1, normpathel2, round):
    "returns a list of normpathels connecting normpathel1 and normpathel2 either rounded or not"
    # this is for corners, i.e. when there are jumps in the tangent vector
    t1 = normpathelendtrafo(normpathel1)
    t2 = normpathelbegintrafo(normpathel2)
    xs, ys = t1._apply(0, 0) # TODO: _apply -> apply_pt
    xe, ye = t2._apply(0, 0)
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
            return [path.normline(xs, ys, xe, ye)]
        else:
            # since t1 is a translation + rotation, param is the radius
            # hence, param should be equal to enlargeby_pt
            # print param
            x, y = t1._apply(0, param)
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
            return [path.normline(xs, ys, xe, ye)]
        else:
            x, y = t1._apply(param, 0)
            return [path.normline(xs, ys, x, y), path.normline(x, y, xe, ye)]


def enlarged(normpath, enlargeby_pt, round):
    newnormsubpaths = []
    for subpath in normpath.subpaths:
        splitnormpathels = subpath.normpathels[:] # do splitting on a copy
        i = 0
        while i < len(splitnormpathels):
            if isinstance(splitnormpathels[i], path.normcurve) and splitnormpathels[i].arclen_pt() > 50:
                splitnormpathels[i:i+1] = splitnormpathels[i].midpointsplit()
            else:
                i += 1
        newnormpathels = []
        for normpathel in splitnormpathels:
            # get old and new start and end points
            ts = normpathelbegintrafo(normpathel)
            xs, ys = ts._apply(0, 0)
            nxs, nys = ts._apply(0, -enlargeby_pt)
            te = normpathelendtrafo(normpathel)
            xe, ye = te._apply(0, 0)
            nxe, nye = te._apply(0, -enlargeby_pt)

            if isinstance(normpathel, path.normcurve):
                # We should do not alter the sign. Could we do any better here?
                try:
                    cs = 1/(normpathel.curvradius_pt(0) + enlargeby_pt)
                except ArithmeticError:
                    cs = 0
                try:
                    ce = 1/(normpathel.curvradius_pt(1) + enlargeby_pt)
                except ArithmeticError:
                    ce = 0

                # this should be a function (in path?), not a method in a class
                # the parameter convention is quite different from other places ...
                bezierparams = deco.smoothed.normal._onebezierbetweentwopathels((nxs, nys), (nxe, nye),
                                                                                (ts.matrix[0][0], ts.matrix[1][0]),
                                                                                (te.matrix[0][0], te.matrix[1][0]),
                                                                                cs, ce, strict=1)
                c.fill(path.circle_pt(bezierparams[0][0], bezierparams[0][1], 1), [color.rgb.red])
                c.fill(path.circle_pt(bezierparams[3][0], bezierparams[3][1], 1), [color.rgb.green])
                newnormpathel = path.normcurve(bezierparams[0][0], bezierparams[0][1],
                                               bezierparams[1][0], bezierparams[1][1],
                                               bezierparams[2][0], bezierparams[2][1],
                                               bezierparams[3][0], bezierparams[3][1])
                showtangent(newnormpathel)
            else:
                # line
                newnormpathel = path.normline(nxs, nys, nxe, nye)

            if len(newnormpathels):
                newnormpathels.extend(connect(newnormpathels[-1], newnormpathel, round=round))
            newnormpathels.append(newnormpathel)
        if subpath.closed:
            newnormpathels.extend(connect(newnormpathels[-1], newnormpathels[0], round=round))
        newnormsubpaths.append(path.normsubpath(newnormpathels, subpath.closed))
    return path.normpath(newnormsubpaths)


def showtangent(normcurve):
    dx = 2
    dy = 1

    cx =                                       3*normcurve.x1_pt - 3*normcurve.x0_pt
    bx =                   3*normcurve.x2_pt - 6*normcurve.x1_pt + 3*normcurve.x0_pt
    ax = normcurve.x3_pt - 3*normcurve.x2_pt + 3*normcurve.x1_pt -   normcurve.x0_pt

    cy =                                       3*normcurve.y1_pt - 3*normcurve.y0_pt
    by =                   3*normcurve.y2_pt - 6*normcurve.y1_pt + 3*normcurve.y0_pt
    ay = normcurve.y3_pt - 3*normcurve.y2_pt + 3*normcurve.y1_pt -   normcurve.y0_pt

    x = - (dy*bx-dx*by)/(3.0*dy*ax-3.0*dx*ay)
    s = math.sqrt(x*x-(dy*cx-dx*cy)/(3.0*dy*ax-3.0*dx*ay))
    t1 = x-s
    t2 = x+s
    ts = []
    if 0 < t1 < 1:
        ts.append(t1)
    if 0 < t2 < 1:
        ts.append(t2)
    for t in ts:
        trafo = normpatheltrafo(normcurve, t)
        c.stroke(path.line_pt(*list(trafo._apply(-100, 0))+list(trafo._apply(100, 0))), [color.rgb.red])


# parameters for the enlargement:
enlargeby_pt = 10
round = 0 # a boolean to turn round corners on and off

# some examples:
for normpath in [path.normpath(path.rect(0, 0, 5, 5)),
                 path.normpath(path.circle(10, 3, 3)),
                 path.normpath(path.path(path.moveto(0, 8),
                                         path.curveto(1, 8, 1, 9, 2, 11),
                                         path.curveto(1, 12, 1, 12, 0, 11),
                                         path.lineto(0, 8),
                                         path.closepath())),
                 path.normpath(path.path(path.moveto(5, 8),
                                         path.curveto(20, 8, 6, 9, 7, 11),
                                         path.curveto(6, 12, 6, 12, 5, 11),
                                         path.lineto(5, 8),
                                         path.closepath())),
                 path.normpath(path.path(path.moveto(16, 0),
                                         path.curveto(18, 0, 18, 4, 20, 4),
                                         path.lineto(20, 12),
                                         path.curveto(12, 12, 20, 8, 16, 8),
                                         path.closepath()))]:
    c.stroke(normpath)
    c.stroke(enlarged(normpath, enlargeby_pt, round), [color.rgb.blue])

c.writeEPSfile("newbox")
