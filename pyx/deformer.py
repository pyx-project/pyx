#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2003-2005 Michael Schindler <m-schindler@users.sourceforge.net>
# Copyright (C) 2003-2004 André Wobst <wobsta@users.sourceforge.net>
#
# This file is part of PyX (http://pyx.sourceforge.net/).
#
# PyX is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# PyX is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyX; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA


import math, warnings
import attr, color, helper, path, style, trafo, unit

def sign1(x):
    return (x >= 0) and 1 or -1

def curvescontrols_from_endlines_pt (B, tangent1, tangent2, r1, r2, softness): # <<<
    # calculates the parameters for two bezier curves connecting two lines (curvature=0)
    # starting at B - r1*tangent1
    # ending at   B + r2*tangent2
    #
    # Takes the corner B
    # and two tangent vectors heading to and from B
    # and two radii r1 and r2:
    # All arguments must be in Points
    # Returns the seven control points of the two bezier curves:
    #  - start d1
    #  - control points g1 and f1
    #  - midpoint e
    #  - control points f2 and g2
    #  - endpoint d2

    # make direction vectors d1: from B to A
    #                        d2: from B to C
    d1 = -tangent1[0] / math.hypot(*tangent1), -tangent1[1] / math.hypot(*tangent1)
    d2 =  tangent2[0] / math.hypot(*tangent2),  tangent2[1] / math.hypot(*tangent2)

    # 0.3192 has turned out to be the maximum softness available
    # for straight lines ;-)
    f = 0.3192 * softness
    g = (15.0 * f + math.sqrt(-15.0*f*f + 24.0*f))/12.0

    # make the control points of the two bezier curves
    f1 = B[0] + f * r1 * d1[0], B[1] + f * r1 * d1[1]
    f2 = B[0] + f * r2 * d2[0], B[1] + f * r2 * d2[1]
    g1 = B[0] + g * r1 * d1[0], B[1] + g * r1 * d1[1]
    g2 = B[0] + g * r2 * d2[0], B[1] + g * r2 * d2[1]
    d1 = B[0] +     r1 * d1[0], B[1] +     r1 * d1[1]
    d2 = B[0] +     r2 * d2[0], B[1] +     r2 * d2[1]
    e  = 0.5 * (f1[0] + f2[0]), 0.5 * (f1[1] + f2[1])

    return (d1, g1, f1, e, f2, g2, d2)
# >>>

def controldists_from_endpoints_pt (A, B, tangA, tangB, curvA, curvB): # <<<

    """distances for a curve given by tangents and curvatures at the endpoints

    This helper routine returns the two distances between the endpoints and the
    corresponding control points of a (cubic) bezier curve that has
    prescribed tangents tangentA, tangentB and curvatures curvA, curvB at the
    end points.
    """

    # some shortcuts
    T = tangA[0] * tangB[1] - tangA[1] * tangB[0]
    D = tangA[0] * (B[1]-A[1]) - tangA[1] * (B[0]-A[0])
    E = tangB[0] * (B[1]-A[1]) - tangB[1] * (B[0]-A[0])
    a, b = None, None


    # try some special cases where the equations decouple
    try:
        1.0 / T
    except ZeroDivisionError:
        try:
            a = math.sqrt( 2.0 * D / (3.0 * curvA))
            b = math.sqrt(-2.0 * E / (3.0 * curvB))
        except ZeroDivisionError:
            a = b = None
    else:
        try:
            1.0 / curvA
        except ZeroDivisionError:
            b = D / T
            a = (-1.5*curvB*b*b - E) / T
        else:
            try:
                1.0 / curvB
            except ZeroDivisionError:
                a = -E / T
                b = (-1.5*curvA*a*a + D) / T
            else:
                a, b = None, None


    # else find a solution for the full problem
    if a is None:
        # we first try to find all the zeros of the polynomials for a or b (4th order)
        # this needs Numeric and LinearAlgebra

        # for the derivation see /design/beziers.tex
        #     0 = Ga(a,b) = 0.5 a |a| curvA + b * T - D
        #     0 = Gb(a,b) = 0.5 b |b| curvB + a * T + E

        coeffs_a = (3.375*curvA*curvA*curvB, 0, -4.5*curvA*curvB*D, T**3, 1.5*curvB*D*D + T*T*E)
        coeffs_b = (3.375*curvA*curvB*curvB, 0,  4.5*curvA*curvB*E, T**3, 1.5*curvA*E*E - T*T*D)

        # First try the equation for a
        cands_a = [cand for cand in helper.realpolyroots(coeffs_a) if cand > 0]

        if cands_a:
            a = min(cands_a)
            b = (-1.5*curvA*a*a + D) / T
        else:
            # then, try the equation for b
            cands_b = [cand for cand in helper.realpolyroots(coeffs_b) if cand > 0]
            if cands_b:
                b = min(cands_b)
                a = (-1.5*curvB*b*b - E) / T
            else:
                a = b = None

    if a < 0 or b < 0:
        a = b = None

    # return the lengths of the control arms. The missing control points are
    #  x_1 = A[0] + a * tangA[0]   y_1 = A[1] + a * tangA[1]
    #  x_2 = B[0] - b * tangB[0]   y_2 = B[1] - b * tangB[1]
    return a, b
# >>>

def intersection (A, D, tangA, tangD): # <<<

    """returns the intersection parameters of two evens

    they are defined by:
      x(t) = A + t * tangA
      x(s) = D + s * tangD
    """
    det = -tangA[0] * tangD[1] + tangA[1] * tangD[0]
    try:
        1.0 / det
    except ArithmeticError:
        return None, None

    DA = D[0] - A[0], D[1] - A[1]

    t = (-tangD[1]*DA[0] + tangD[0]*DA[1]) / det
    s = (-tangA[1]*DA[0] + tangA[0]*DA[1]) / det

    return t, s
# >>>

def parallel_curvespoints_pt (orig_ncurve, shift, expensive=0, relerr=0.05, epsilon=1e-5, counter=1): # <<<

    A = orig_ncurve.x0_pt, orig_ncurve.y0_pt
    B = orig_ncurve.x1_pt, orig_ncurve.y1_pt
    C = orig_ncurve.x2_pt, orig_ncurve.y2_pt
    D = orig_ncurve.x3_pt, orig_ncurve.y3_pt

    # non-normalized tangential vector
    # from begin/end point to the corresponding controlpoint
    tangA = (B[0] - A[0], B[1] - A[1])
    tangD = (D[0] - C[0], D[1] - C[1])
    # normalized tangential vector
    TangA = (tangA[0] / math.hypot(*tangA), tangA[1] / math.hypot(*tangA))
    TangD = (tangD[0] / math.hypot(*tangD), tangD[1] / math.hypot(*tangD))

    # normalized normal vectors
    # turned to the left (+90 degrees) from the tangents
    NormA = (-tangA[1] / math.hypot(*tangA), tangA[0] / math.hypot(*tangA))
    NormD = (-tangD[1] / math.hypot(*tangD), tangD[0] / math.hypot(*tangD))

    # radii of curvature
    radiusA, radiusD = orig_ncurve.curveradius_pt([0,1])

    # get the new begin/end points
    A = A[0] + shift * NormA[0], A[1] + shift * NormA[1]
    D = D[0] + shift * NormD[0], D[1] + shift * NormD[1]

    try:
        if radiusA is None:
            curvA = 0
        else:
            curvA = 1.0 / (radiusA - shift)
        if radiusD is None:
            curvD = 0
        else:
            curvD = 1.0 / (radiusD - shift)
    except ZeroDivisionError:
        raise
    else:
        a, d = controldists_from_endpoints_pt (A, D, TangA, TangD, curvA, curvD)

        if a is None or d is None:
            # fallback heuristic
            a = (radiusA - shift) / radiusA
            d = (radiusD - shift) / radiusD

        B = A[0] + a * TangA[0], A[1] + a * TangA[1]
        C = D[0] - d * TangD[0], D[1] - d * TangD[1]

    controlpoints = [(A,B,C,D)]

    # check if the distance is really the wanted distance
    if expensive and counter < 10:
        # measure the distance in the "middle" of the original curve
        trafo = orig_ncurve.trafo([0.5])[0]
        M = trafo.apply_pt(0,0)
        NormM = trafo.apply_pt(0,1)
        NormM = NormM[0] - M[0], NormM[1] - M[1]

        nline = path.normline_pt (
          M[0] + (1.0 - 2*relerr) * shift * NormM[0],
          M[1] + (1.0 - 2*relerr) * shift * NormM[1],
          M[0] + (1.0 + 2*relerr) * shift * NormM[0],
          M[1] + (1.0 + 2*relerr) * shift * NormM[1])

        new_ncurve = path.normcurve_pt(A[0],A[1], B[0],B[1], C[0],C[1], D[0],D[1])

        #cutparams = nline.intersect(orig_ncurve, epsilon)
        cutparams = new_ncurve.intersect(nline, epsilon)
        if cutparams:
            cutpoints = nline.at_pt(cutparams[0])
        else:
            cutpoints = []
        good = 0
        for cutpoint in cutpoints:
            if cutpoint is not None:
                dist = math.hypot(M[0] - cutpoint[0], M[1] - cutpoint[1])
                if abs(dist - abs(shift)) < relerr * abs(shift):
                    good = 1

        if not good:
            first, second = orig_ncurve.segments([0,0.5,1])
            controlpoints = \
              parallel_curvespoints_pt (first,  shift, expensive, relerr, epsilon, counter+1) + \
              parallel_curvespoints_pt (second, shift, expensive, relerr, epsilon, counter+1)



    # TODO:
    # too big curvatures: intersect curves
    # there is something wrong with the recursion
    return controlpoints
# >>>


class deformer(attr.attr):

    def deform (self, basepath):
        return basepath

class cycloid(deformer): # <<<
    """Wraps a cycloid around a path.

    The outcome looks like a metal spring with the originalpath as the axis.
    radius: radius of the cycloid
    loops:  number of loops from beginning to end of the original path
    skipfirst/skiplast: undeformed end lines of the original path

    """

    def __init__(self, radius=0.5*unit.t_cm, halfloops=10,
    skipfirst=1*unit.t_cm, skiplast=1*unit.t_cm, curvesperhloop=3, sign=1, turnangle=45):
        self.skipfirst = skipfirst
        self.skiplast = skiplast
        self.radius = radius
        self.halfloops = halfloops
        self.curvesperhloop = curvesperhloop
        self.sign = sign
        self.turnangle = turnangle

    def __call__(self, radius=None, halfloops=None,
    skipfirst=None, skiplast=None, curvesperhloop=None, sign=None, turnangle=None):
        if radius is None:
            radius = self.radius
        if halfloops is None:
            halfloops = self.halfloops
        if skipfirst is None:
            skipfirst = self.skipfirst
        if skiplast is None:
            skiplast = self.skiplast
        if curvesperhloop is None:
            curvesperhloop = self.curvesperhloop
        if sign is None:
            sign = self.sign
        if turnangle is None:
            turnangle = self.turnangle

        return cycloid(radius=radius, halfloops=halfloops, skipfirst=skipfirst, skiplast=skiplast,
                       curvesperhloop=curvesperhloop, sign=sign, turnangle=turnangle)

    def deform(self, basepath):
        resultnormsubpaths = [self.deformsubpath(nsp) for nsp in basepath.normpath().normsubpaths]
        return path.normpath(resultnormsubpaths)

    def deformsubpath(self, normsubpath):

        skipfirst = abs(unit.topt(self.skipfirst))
        skiplast = abs(unit.topt(self.skiplast))
        radius = abs(unit.topt(self.radius))
        turnangle = self.turnangle * math.pi / 180.0

        cosTurn = math.cos(turnangle)
        sinTurn = math.sin(turnangle)

        # make list of the lengths and parameters at points on normsubpath where we will add cycloid-points
        totlength = normsubpath.arclen_pt()
        if totlength <= skipfirst + skiplast + 2*radius*sinTurn:
            warnings.warn("normsubpath is too short for deformation with cycloid -- skipping...")
            return normsubpath

        # parametrisation is in rotation-angle around the basepath
        # differences in length, angle ... between two basepoints
        # and between basepoints and controlpoints
        Dphi = math.pi / self.curvesperhloop
        phis = [i * Dphi for i in range(self.halfloops * self.curvesperhloop + 1)]
        DzDphi = (totlength - skipfirst - skiplast - 2*radius*sinTurn) * 1.0 / (self.halfloops * math.pi * cosTurn)
        # Dz = (totlength - skipfirst - skiplast - 2*radius*sinTurn) * 1.0 / (self.halfloops * self.curvesperhloop * cosTurn)
        # zs = [i * Dz for i in range(self.halfloops * self.curvesperhloop + 1)]
        # from path._arctobcurve:
        # optimal relative distance along tangent for second and third control point
        L = 4 * radius * (1 - math.cos(Dphi/2)) / (3 * math.sin(Dphi/2))

        # Now the transformation of z into the turned coordinate system
        Zs = [ skipfirst + radius*sinTurn # here the coordinate z starts
             - sinTurn*radius*math.cos(phi) + cosTurn*DzDphi*phi # the transformed z-coordinate
             for phi in phis]
        params = normsubpath._arclentoparam_pt(Zs)[0]

        # get the positions of the splitpoints in the cycloid
        points = []
        for phi, param in zip(phis, params):
            # the cycloid is a circle that is stretched along the normsubpath
            # here are the points of that circle
            basetrafo = normsubpath.trafo([param])[0]

            # The point on the cycloid, in the basepath's local coordinate system
            baseZ, baseY = 0, radius*math.sin(phi)

            # The tangent there, also in local coords
            tangentX = -cosTurn*radius*math.sin(phi) + sinTurn*DzDphi
            tangentY = radius*math.cos(phi)
            tangentZ = sinTurn*radius*math.sin(phi) + DzDphi*cosTurn
            norm = math.sqrt(tangentX*tangentX + tangentY*tangentY + tangentZ*tangentZ)
            tangentY, tangentZ = tangentY/norm, tangentZ/norm

            # Respect the curvature of the basepath for the cycloid's curvature
            # XXX this is only a heuristic, not a "true" expression for
            #     the curvature in curved coordinate systems
            pathradius = normsubpath.curveradius_pt([param])[0]
            if pathradius is not None:
                factor = (pathradius - baseY) / pathradius
                factor = abs(factor)
            else:
                factor = 1
            l = L * factor

            # The control points prior and after the point on the cycloid
            preeZ, preeY = baseZ - l * tangentZ, baseY - l * tangentY
            postZ, postY = baseZ + l * tangentZ, baseY + l * tangentY

            # Now put everything at the proper place
            points.append(basetrafo.apply_pt(preeZ, self.sign * preeY) +
                          basetrafo.apply_pt(baseZ, self.sign * baseY) +
                          basetrafo.apply_pt(postZ, self.sign * postY))

        if len(points) <= 1:
            warnings.warn("normsubpath is too short for deformation with cycloid -- skipping...")
            return normsubpath

        # Build the path from the pointlist
        # containing (control x 2,  base x 2, control x 2)
        if skipfirst > normsubpath.epsilon:
            normsubpathitems = normsubpath.segments([0, params[0]])[0]
            normsubpathitems.append(path.normcurve_pt(*(points[0][2:6] + points[1][0:4])))
        else:
            normsubpathitems = [path.normcurve_pt(*(points[0][2:6] + points[1][0:4]))]
        for i in range(1, len(points)-1):
            normsubpathitems.append(path.normcurve_pt(*(points[i][2:6] + points[i+1][0:4])))
        if skiplast > normsubpath.epsilon:
            for nsp in normsubpath.segments([params[-1], len(normsubpath)]):
                normsubpathitems.extend(nsp.normsubpathitems)

        # That's it
        return path.normsubpath(normsubpathitems, epsilon=normsubpath.epsilon)
# >>>

cycloid.clear = attr.clearclass(cycloid)

class smoothed(deformer): # <<<

    """Bends corners in a path.

    This decorator replaces corners in a path with bezier curves. There are two cases:
    - If the corner lies between two lines, _two_ bezier curves will be used
      that are highly optimized to look good (their curvature is to be zero at the ends
      and has to have zero derivative in the middle).
      Additionally, it can controlled by the softness-parameter.
    - If the corner lies between curves then _one_ bezier is used that is (except in some
      special cases) uniquely determined by the tangents and curvatures at its end-points.
      In some cases it is necessary to use only the absolute value of the curvature to avoid a
      cusp-shaped connection of the new bezier to the old path. In this case the use of
      "obeycurv=0" allows the sign of the curvature to switch.
    - The radius argument gives the arclength-distance of the corner to the points where the
      old path is cut and the beziers are inserted.
    - Path elements that are too short (shorter than the radius) are skipped
    """

    def __init__(self, radius, softness=1, obeycurv=0, relskipthres=0.01):
        self.radius = radius
        self.softness = softness
        self.obeycurv = obeycurv
        self.relskipthres = relskipthres

    def __call__(self, radius=None, softness=None, obeycurv=None, relskipthres=None):
        if radius is None:
            radius = self.radius
        if softness is None:
            softness = self.softness
        if obeycurv is None:
            obeycurv = self.obeycurv
        if relskipthres is None:
            relskipthres = self.relskipthres
        return smoothed(radius=radius, softness=softness, obeycurv=obeycurv, relskipthres=relskipthres)

    def deform(self, basepath):
        return path.normpath([self.deformsubpath(normsubpath)
                              for normsubpath in basepath.normpath().normsubpaths])

    def deformsubpath(self, normsubpath):
        radius_pt = unit.topt(self.radius)
        epsilon = normsubpath.epsilon

        # remove too short normsubpath items (shorter than self.relskipthres*radius_pt or epsilon)
        pertinentepsilon = max(epsilon, self.relskipthres*radius_pt)
        pertinentnormsubpath = path.normsubpath(normsubpath.normsubpathitems,
                                                epsilon=pertinentepsilon)
        pertinentnormsubpath.flushskippedline()
        pertinentnormsubpathitems = pertinentnormsubpath.normsubpathitems

        # calculate the splitting parameters for the pertinentnormsubpathitems
        arclens_pt = []
        params = []
        for pertinentnormsubpathitem in pertinentnormsubpathitems:
            arclen_pt = pertinentnormsubpathitem.arclen_pt(epsilon)
            arclens_pt.append(arclen_pt)
            l1_pt = min(radius_pt, 0.5*arclen_pt)
            l2_pt = max(0.5*arclen_pt, arclen_pt - radius_pt)
            params.append(pertinentnormsubpathitem.arclentoparam_pt([l1_pt, l2_pt], epsilon))

        # handle the first and last pertinentnormsubpathitems for a non-closed normsubpath
        if not normsubpath.closed:
            l1_pt = 0
            l2_pt = max(0, arclens_pt[0] - radius_pt)
            params[0] = pertinentnormsubpathitems[0].arclentoparam_pt([l1_pt, l2_pt], epsilon)
            l1_pt = min(radius_pt, arclens_pt[-1])
            l2_pt = arclens_pt[-1]
            params[-1] = pertinentnormsubpathitems[-1].arclentoparam_pt([l1_pt, l2_pt], epsilon)

        newnormsubpath = path.normsubpath(epsilon=normsubpath.epsilon)
        for i in range(len(pertinentnormsubpathitems)):
            this = i
            next = (i+1) % len(pertinentnormsubpathitems)
            thisparams = params[this]
            nextparams = params[next]
            thisnormsubpathitem = pertinentnormsubpathitems[this]
            nextnormsubpathitem = pertinentnormsubpathitems[next]
            thisarclen_pt = arclens_pt[this]
            nextarclen_pt = arclens_pt[next]

            # insert the middle segment
            newnormsubpath.append(thisnormsubpathitem.segments(thisparams)[0])

            # insert replacement curves for the corners
            if next or normsubpath.closed:

                t1 = thisnormsubpathitem.rotation([thisparams[1]])[0].apply_pt(1, 0)
                t2 = nextnormsubpathitem.rotation([nextparams[0]])[0].apply_pt(1, 0)

                if (isinstance(thisnormsubpathitem, path.normline_pt) and
                    isinstance(nextnormsubpathitem, path.normline_pt)):

                    # case of two lines -> replace by two curves
                    d1, g1, f1, e, f2, g2, d2 = curvescontrols_from_endlines_pt(
                        thisnormsubpathitem.atend_pt(), t1, t2,
                        thisarclen_pt*(1-thisparams[1]), nextarclen_pt*(nextparams[0]), softness=self.softness)

                    p1 = thisnormsubpathitem.at_pt([thisparams[1]])[0]
                    p2 = nextnormsubpathitem.at_pt([nextparams[0]])[0]

                    newnormsubpath.append(path.normcurve_pt(*(d1 + g1 + f1 + e)))
                    newnormsubpath.append(path.normcurve_pt(*(e + f2 + g2 + d2)))

                else:

                    # generic case -> replace by a single curve with prescribed tangents and curvatures
                    p1 = thisnormsubpathitem.at_pt([thisparams[1]])[0]
                    p2 = nextnormsubpathitem.at_pt([nextparams[0]])[0]

                    # XXX supply curvature_pt methods in path module or transfere algorithms to work with curveradii
                    def curvature(normsubpathitem, param):
                        r = normsubpathitem.curveradius_pt([param])[0]
                        if r is None:
                            return 0
                        return 1.0 / r

                    c1 = curvature(thisnormsubpathitem, thisparams[1])
                    c2 = curvature(nextnormsubpathitem, nextparams[0])

                    if not self.obeycurv:
                        # do not obey the sign of the curvature but
                        # make the sign such that the curve smoothly passes to the next point
                        # this results in a discontinuous curvature
                        # (but the absolute value is still continuous)
                        s1 = sign1(t1[0] * (p2[1]-p1[1]) - t1[1] * (p2[0]-p1[0]))
                        s2 = sign1(t2[0] * (p2[1]-p1[1]) - t2[1] * (p2[0]-p1[0]))
                        c1 = s1 * abs(c1)
                        c2 = s2 * abs(c2)

                    # get the length of the control "arms"
                    a, d = controldists_from_endpoints_pt(p1, p2, t1, t2, c1, c2)

                    # avoid overshooting at the corners:
                    # this changes not only the sign of the curvature
                    # but also the magnitude
                    if not self.obeycurv:
                        t, s = intersection(p1, p2, t1, t2)
                        if t is None or t < 0:
                            a = None
                        else:
                            a = min(a, t)

                        if s is None or s > 0:
                            d = None
                        else:
                            d = min(d, -s)

                    # if there is no useful result:
                    # take arbitrary smoothing curve that does not obey
                    # the curvature constraints
                    if a is None or d is None:
                        dist = math.hypot(p1[0] - p2[0], p1[1] - p2[1])
                        a = dist / (3.0 * math.hypot(*t1))
                        d = dist / (3.0 * math.hypot(*t2))

                    # calculate the two missing control points
                    q1 = p1[0] + a * t1[0], p1[1] + a * t1[1]
                    q2 = p2[0] - d * t2[0], p2[1] - d * t2[1]

                    newnormsubpath.append(path.normcurve_pt(*(p1 + q1 + q2 + p2)))

        if normsubpath.closed:
            newnormsubpath.close()
        return newnormsubpath

# >>>

smoothed.clear = attr.clearclass(smoothed)

class parallel(deformer): # <<<

    """creates a parallel path with constant distance to the original path

    A positive 'distance' results in a curve left of the original one -- and a
    negative 'distance' in a curve at the right. Left/Right are understood in
    terms of the parameterization of the original curve.
    At corners, either a circular arc is drawn around the corner, or, if the
    curve is on the other side, the parallel curve also exhibits a corner.

    For each path element a parallel curve/line is constructed. For curves, the
    accuracy can be adjusted with the parameter 'relerr', thus, relerr*distance
    is the maximum allowable error somewhere in the middle of the curve (at
    parameter value 0.5).
    'relerr' only applies for the 'expensive' mode where the parallel curve for
    a single curve items may be composed of several (many) curve items.
    """

    # TODO:
    # - check for greatest curvature and introduce extra corners
    #   if a normcurve is too heavily curved
    # - do relerr-checks at better points than just at parameter 0.5

    def __init__(self, distance, relerr=0.05, expensive=1):
        self.distance = distance
        self.relerr = relerr
        self.expensive = expensive

    def __call__(self, distance=None, relerr=None, expensive=None):
        # returns a copy of the deformer with different parameters
        if distance is None:
            d = self.distance
        if relerr is None:
            r = self.relerr
        if expensive is None:
            e = self.expensive

        return parallel(distance=d, relerr=r, expensive=e)

    def deform(self, basepath):
        resultnormsubpaths = [self.deformsubpath(nsp) for nsp in basepath.normpath().normsubpaths]
        return path.normpath(resultnormsubpaths)

    def deformsubpath(self, orig_nspath):

        distance = unit.topt(self.distance)
        relerr = self.relerr
        expensive = self.expensive
        epsilon = orig_nspath.epsilon

        new_nspath = path.normsubpath(epsilon=epsilon)

        # 1. Store endpoints, tangents and curvatures for each element
        points, tangents, curvatures = [], [], []
        for npitem in orig_nspath:

            ps,ts,cs = [],[],[]
            trafos = npitem.trafo([0,1])
            for t in trafos:
                p = t.apply_pt(0,0)
                t = t.apply_pt(1,0)
                ps.append(p)
                ts.append((t[0]-p[0], t[1]-p[1]))

            rs = npitem.curveradius_pt([0,1])
            cs = []
            for r in rs:
                if r is None:
                    cs.append(0)
                else:
                    cs.append(1.0 / r)

            points.append(ps)
            tangents.append(ts)
            curvatures.append(cs)

        closeparallel = (tangents[-1][1][0]*tangents[0][0][1] - tangents[-1][1][1]*tangents[0][0][0])

        # 2. append the parallel path for each element:
        for cur in range(len(orig_nspath)):

            if cur == 0:
                old = cur
                # OldEnd = points[old][0]
                OldEndTang = tangents[old][0]
            else:
                old = cur - 1
                # OldEnd = points[old][1]
                OldEndTang = tangents[old][1]

            CurBeg, CurEnd = points[cur]
            CurBegTang, CurEndTang = tangents[cur]
            CurBegCurv, CurEndCurv = curvatures[cur]

            npitem = orig_nspath[cur]

            # get the control points for the shifted pathelement
            if isinstance(npitem, path.normline_pt):
                # get the points explicitly from the normal vector
                A = CurBeg[0] - distance * CurBegTang[1], CurBeg[1] + distance * CurBegTang[0]
                D = CurEnd[0] - distance * CurEndTang[1], CurEnd[1] + distance * CurEndTang[0]
                new_npitems = [path.normline_pt(A[0], A[1], D[0], D[1])]
            elif isinstance(npitem, path.normcurve_pt):
                # call a function to return a list of controlpoints
                cpoints_list = parallel_curvespoints_pt(npitem, distance, expensive, relerr, epsilon)
                new_npitems = []
                for cpoints in cpoints_list:
                    A,B,C,D = cpoints
                    new_npitems.append(path.normcurve_pt(A[0],A[1], B[0],B[1], C[0],C[1], D[0],D[1]))
                # we will need the starting point of the new normpath items
                A = cpoints_list[0][0]


            # append the next piece of the path:
            # it might contain of an extra arc or must be intersected before appending
            parallel = (OldEndTang[0]*CurBegTang[1] - OldEndTang[1]*CurBegTang[0])
            if parallel*distance < -epsilon:

                # append an arc around the corner
                # from the preceding piece to the current piece
                # we can never get here for the first npitem! (because cur==old)
                endpoint = new_nspath.atend_pt()
                center = CurBeg
                angle1 = math.atan2(endpoint[1] - center[1], endpoint[0] - center[0]) * 180.0 / math.pi
                angle2 = math.atan2(A[1] - center[1], A[0] - center[0]) * 180.0 / math.pi
                if parallel > 0:
                    arc_npath = path.path(path.arc_pt(
                      center[0], center[1], abs(distance), angle1, angle2)).normpath()
                else:
                    arc_npath = path.path(path.arcn_pt(
                      center[0], center[1], abs(distance), angle1, angle2)).normpath()

                for new_npitem in arc_npath[0]:
                    new_nspath.append(new_npitem)


            elif parallel*distance > epsilon:
                # intersect the extra piece of the path with the rest of the new path
                # and throw away the void parts
                #
                # build a subpath for intersection
                extra_nspath = path.normsubpath(normsubpathitems=new_npitems, epsilon=epsilon)

                intsparams = extra_nspath.intersect(new_nspath)
                # [[a,b,c], [a,b,c]]
                if intsparams:
                    # take the first intersection point:
                    extra_param, new_param = intsparams[0][0], intsparams[1][0]
                    new_nspath = new_nspath.segments([0, new_param])[0]
                    extra_nspath = extra_nspath.segments([extra_param, len(extra_nspath)])[0]
                    new_npitems = extra_nspath.normsubpathitems
                    # in case the intersection was not sufficiently exact:
                    # CAREFUL! because we newly created all the new_npitems and
                    # the items in extra_nspath, we may in-place change the starting point
                    new_npitems[0] = new_npitems[0].modifiedbegin_pt(*new_nspath.atend_pt())
                else:
                    raise # how did we get here?


            # at the (possible) closing corner we may have to intersect another time
            # or add another corner:
            # the intersection must be done before appending the parallel piece
            if orig_nspath.closed and cur == len(orig_nspath) - 1:
                if closeparallel * distance > epsilon:
                    intsparams = extra_nspath.intersect(new_nspath)
                    # [[a,b,c], [a,b,c]]
                    if intsparams:
                        # take the last intersection point:
                        extra_param, new_param = intsparams[0][-1], intsparams[1][-1]
                        new_nspath = new_nspath.segments([new_param, len(new_nspath)])[0]
                        extra_nspath = extra_nspath.segments([0, extra_param])[0]
                        new_npitems = extra_nspath.normsubpathitems
                        # in case the intersection was not sufficiently exact:
                        # CAREFUL! because we newly created all the new_npitems and
                        # the items in extra_nspath, we may in-place change the end point
                        new_npitems[-1] = new_npitems[-1].modifiedend_pt(*new_nspath.atbegin_pt())
                    else:
                        raise # how did we get here?

                    pass


            # append the parallel piece
            for new_npitem in new_npitems:
                new_nspath.append(new_npitem)


        # the curve around the closing corner must be added at last:
        if orig_nspath.closed:
            if closeparallel * distance < -epsilon:
                endpoint = new_nspath.atend_pt()
                center = orig_nspath.atend_pt()
                A = new_nspath.atbegin_pt()
                angle1 = math.atan2(endpoint[1] - center[1], endpoint[0] - center[0]) * 180.0 / math.pi
                angle2 = math.atan2(A[1] - center[1], A[0] - center[0]) * 180.0 / math.pi
                if parallel > 0:
                    arc_npath = path.path(path.arc_pt(
                      center[0], center[1], abs(distance), angle1, angle2)).normpath()
                else:
                    arc_npath = path.path(path.arcn_pt(
                      center[0], center[1], abs(distance), angle1, angle2)).normpath()

                for new_npitem in arc_npath[0]:
                    new_nspath.append(new_npitem)

        # 3. extra handling of closed paths
        if orig_nspath.closed:
            new_nspath.close()

        return new_nspath
# >>>

parallel.clear = attr.clearclass(parallel)

# vim:foldmethod=marker:foldmarker=<<<,>>>
