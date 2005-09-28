#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2003-2005 Michael Schindler <m-schindler@users.sourceforge.net>
# Copyright (C) 2003-2005 André Wobst <wobsta@users.sourceforge.net>
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
import attr, helper, path, normpath, unit, color
from path import degrees

# specific exception for an invalid parameterization point
# used in parallel
class InvalidParamException(Exception):

    def __init__(self, param):
        self.normsubpathitemparam = param

def curvescontrols_from_endlines_pt(B, tangent1, tangent2, r1, r2, softness): # <<<
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

def controldists_from_endgeometry_pt(A, B, tangA, tangB, curvA, curvB, epsilon): # <<<

    """For a curve with given tangents and curvatures at the endpoints this gives the distances between the controlpoints

    This helper routine returns a list of two distances between the endpoints and the
    corresponding control points of a (cubic) bezier curve that has
    prescribed tangents tangentA, tangentB and curvatures curvA, curvB at the
    end points.

    Note: The returned distances are not always positive.
          But only positive values are geometrically correct, so please check!
          The outcome is sorted so that the first entry is expected to be the
          most reasonable one
    """

    # these two thresholds are dimensionless, not lengths:
    fallback_threshold = 1.0e-3

    # some shortcuts
    T = tangA[0] * tangB[1] - tangA[1] * tangB[0]
    D = tangA[0] * (B[1]-A[1]) - tangA[1] * (B[0]-A[0])
    E = tangB[0] * (A[1]-B[1]) - tangB[1] * (A[0]-B[0])
    AB = math.hypot(A[0] - B[0], A[1] - B[1])

    # For curvatures zero we found no solutions (during testing)
    # Terefore, we need a fallback.
    # When the curvature is nearly zero or when T is nearly zero
    # we know the exact answer to the problem.

    # extreme case: all parameters are nearly zero
    a = b = 0.3 * AB
    if max([abs(1.5*a*a*curvA), abs(1.5*b*b*curvB), abs(a*T), abs(b*T), abs(D), abs(E)]) < epsilon:
        return [(a, b)]

    # extreme case: curvA geometrically too big
    if fallback_threshold * abs(curvA*AB) > 1:
        a = math.sqrt(abs(D / (1.5 * curvA))) * helper.sign(D*curvA)
        b = (D - 1.5*curvA*a*abs(a)) / T
        return [(a, b)]

    # extreme case: curvB geometrically too big
    if fallback_threshold * abs(curvB*AB) > 1:
        b = math.sqrt(abs(E / (1.5 * curvB))) * helper.sign(E*curvB)
        a = (E - 1.5*curvB*b*abs(b)) / T
        return [(a, b)]

    # extreme case: curvA much smaller than T
    try:
        b = D / T
        a = (E - 1.5*curvB*b*abs(b)) / T
    except ZeroDivisionError:
        pass
    else:
        if abs(1.5*a*a*curvA) < fallback_threshold * abs(b*T):
            return [(a, b)]

    # extreme case: curvB much smaller than T
    try:
        a = E / T
        b = (D - 1.5*curvA*a*abs(a)) / T
    except ZeroDivisionError:
        pass
    else:
        if abs(1.5*b*b*curvB) < fallback_threshold * abs(a*T):
            return [(a, b)]

    # extreme case: T much smaller than both curvatures
    try:
        a = math.sqrt(abs(D / (1.5 * curvA))) * helper.sign(D*curvA)
    except ZeroDivisionError:
        # we have tried the case with small curvA already
        # and we cannot divide by T
        pass
    else:
        try:
            b = math.sqrt(abs(E / (1.5 * curvB))) * helper.sign(E*curvB)
        except ZeroDivisionError:
            # we have tried the case with small curvB already
            # and we cannot divide by T
            pass
        else:
            if (abs(b*T) < fallback_threshold * abs(1.5*a*a*curvA) and
                abs(a*T) < fallback_threshold * abs(1.5*b*b*curvB) ):
                return [(a, b)]

    # Now the general case:
    # we try to find all the zeros of the decoupled 4th order problem
    # for the combined problem:
    # The control points of a cubic Bezier curve are given by a, b:
    #     A, A + a*tangA, B - b*tangB, B
    # for the derivation see /design/beziers.tex
    #     0 = 1.5 a |a| curvA + b * T - D
    #     0 = 1.5 b |b| curvB + a * T - E
    # because of the absolute values we get several possibilities for the signs
    # in the equation. We test all signs, also the invalid ones!
    candidates_a, candidates_b = [], []
    for sign_a in [+1, -1]:
        for sign_b in [+1, -1]:
            coeffs_a = (sign_b*1.5*curvB*D*D - T*T*E, T**3, -sign_b*sign_a*4.5*curvA*curvB*D, 0.0, sign_b*3.375*curvA*curvA*curvB)
            coeffs_b = (sign_a*1.5*curvA*E*E - T*T*D, T**3, -sign_a*sign_b*4.5*curvA*curvB*E, 0.0, sign_a*3.375*curvA*curvB*curvB)
            candidates_a += [root for root in helper.realpolyroots(coeffs_a) if sign_a*root >= 0]
            candidates_b += [root for root in helper.realpolyroots(coeffs_b) if sign_b*root >= 0]

    # check the combined equations
    # and find the candidate pairs
    solutions = []
    for a in candidates_a:
        for b in candidates_b:
            # check if the calculated radii of curvature do not differ from 1/curv
            # by more than epsilon. This uses epsilon like in all normpath
            # methods as a criterion for "length".
            # In mathematical language this is
            #   abs(1.5a|a|/(D-bT) - 1/curvA) < epsilon
            if ( abs(1.5*curvA*a*abs(a) + b*T - D) < epsilon * abs(curvA*(D - b*T)) and
                 abs(1.5*curvB*b*abs(b) + a*T - E) < epsilon * abs(curvB*(E - a*T)) ):
                solutions.append((a, b))

    # sort the solutions: the more reasonable values at the beginning
    def mycmp(x,y):
        # first the pairs that are purely positive, then all the pairs with some negative signs
        # inside the two sets: sort by magnitude
        sx = x[0] > 0 and x[1] > 0
        sy = y[0] > 0 and y[1] > 0
        if sx == sy:
            return cmp(x[0]**2 + x[1]**2, y[0]**2 + y[1]**2)
        else:
            return cmp(sy, sx)

    solutions.sort(mycmp)

    # XXX should the solutions's list also be unique'fied?

    # XXX we will stop here, if solutions is empty
    if not solutions:
        #print curvA, curvB, T, D, E
        raise ValueError, "no curve found. Try adjusting the fallback-parameters."

    return solutions
# >>>

def normcurve_from_endgeometry_pt(A, B, tangA, tangB, curvA, curvB): # <<<
    a, b = controldists_from_endgeometry_pt(A, B, tangA, tangB, curvA, curvB, epsilon=epsilon)[0]
    return normpath.normcurve_pt(A[0], A[1],
        A[0] + a * tangA[0], A[1] + a * tangA[1],
        B[0] - b * tangB[0], B[1] - b * tangB[1], B[0], B[1])
    # >>>

def intersection(A, D, tangA, tangD): # <<<

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

class deformer(attr.attr):

    def deform (self, basepath):
        return basepath

class cycloid(deformer): # <<<
    """Wraps a cycloid around a path.

    The outcome looks like a spring with the originalpath as the axis.
    radius: radius of the cycloid
    halfloops:  number of halfloops
    skipfirst/skiplast: undeformed end lines of the original path
    curvesperhloop:
    sign: start left (1) or right (-1) with the first halfloop
    turnangle: angle of perspective on a (3D) spring
               turnangle=0 will produce a sinus-like cycloid,
               turnangle=90 will procude a row of connected circles

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
        return normpath.normpath(resultnormsubpaths)

    def deformsubpath(self, normsubpath):

        skipfirst = abs(unit.topt(self.skipfirst))
        skiplast = abs(unit.topt(self.skiplast))
        radius = abs(unit.topt(self.radius))
        turnangle = degrees(self.turnangle)
        sign = helper.sign(self.sign)

        cosTurn = math.cos(turnangle)
        sinTurn = math.sin(turnangle)

        # make list of the lengths and parameters at points on normsubpath
        # where we will add cycloid-points
        totlength = normsubpath.arclen_pt()
        if totlength <= skipfirst + skiplast + 2*radius*sinTurn:
            warnings.warn("normsubpath is too short for deformation with cycloid -- skipping...")
            return normsubpath

        # parameterization is in rotation-angle around the basepath
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
            if pathradius is not normpath.invalid:
                factor = (pathradius - baseY) / pathradius
                factor = abs(factor)
            else:
                factor = 1
            l = L * factor

            # The control points prior and after the point on the cycloid
            preeZ, preeY = baseZ - l * tangentZ, baseY - l * tangentY
            postZ, postY = baseZ + l * tangentZ, baseY + l * tangentY

            # Now put everything at the proper place
            points.append(basetrafo.apply_pt(preeZ, sign * preeY) +
                          basetrafo.apply_pt(baseZ, sign * baseY) +
                          basetrafo.apply_pt(postZ, sign * postY))

        if len(points) <= 1:
            warnings.warn("normsubpath is too short for deformation with cycloid -- skipping...")
            return normsubpath

        # Build the path from the pointlist
        # containing (control x 2,  base x 2, control x 2)
        if skipfirst > normsubpath.epsilon:
            normsubpathitems = normsubpath.segments([0, params[0]])[0]
            normsubpathitems.append(normpath.normcurve_pt(*(points[0][2:6] + points[1][0:4])))
        else:
            normsubpathitems = [normpath.normcurve_pt(*(points[0][2:6] + points[1][0:4]))]
        for i in range(1, len(points)-1):
            normsubpathitems.append(normpath.normcurve_pt(*(points[i][2:6] + points[i+1][0:4])))
        if skiplast > normsubpath.epsilon:
            for nsp in normsubpath.segments([params[-1], len(normsubpath)]):
                normsubpathitems.extend(nsp.normsubpathitems)

        # That's it
        return normpath.normsubpath(normsubpathitems, epsilon=normsubpath.epsilon)
# >>>

cycloid.clear = attr.clearclass(cycloid)

class smoothed(deformer): # <<<

    """Bends corners in a normpath.

    This decorator replaces corners in a normpath with bezier curves. There are two cases:
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
        return normpath.normpath([self.deformsubpath(normsubpath)
                              for normsubpath in basepath.normpath().normsubpaths])

    def deformsubpath(self, normsubpath):
        radius_pt = unit.topt(self.radius)
        epsilon = normsubpath.epsilon

        # remove too short normsubpath items (shorter than self.relskipthres*radius_pt or epsilon)
        pertinentepsilon = max(epsilon, self.relskipthres*radius_pt)
        pertinentnormsubpath = normpath.normsubpath(normsubpath.normsubpathitems,
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

        newnormsubpath = normpath.normsubpath(epsilon=normsubpath.epsilon)
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
                # TODO: normpath.invalid

                if (isinstance(thisnormsubpathitem, normpath.normline_pt) and
                    isinstance(nextnormsubpathitem, normpath.normline_pt)):

                    # case of two lines -> replace by two curves
                    d1, g1, f1, e, f2, g2, d2 = curvescontrols_from_endlines_pt(
                        thisnormsubpathitem.atend_pt(), t1, t2,
                        thisarclen_pt*(1-thisparams[1]), nextarclen_pt*(nextparams[0]), softness=self.softness)

                    p1 = thisnormsubpathitem.at_pt([thisparams[1]])[0]
                    p2 = nextnormsubpathitem.at_pt([nextparams[0]])[0]

                    newnormsubpath.append(normpath.normcurve_pt(*(d1 + g1 + f1 + e)))
                    newnormsubpath.append(normpath.normcurve_pt(*(e + f2 + g2 + d2)))

                else:

                    # generic case -> replace by a single curve with prescribed tangents and curvatures
                    p1 = thisnormsubpathitem.at_pt([thisparams[1]])[0]
                    p2 = nextnormsubpathitem.at_pt([nextparams[0]])[0]
                    c1 = thisnormsubpathitem.curvature_pt([thisparams[1]])[0]
                    c2 = nextnormsubpathitem.curvature_pt([nextparams[0]])[0]
                    # TODO: normpath.invalid

                    # TODO: more intelligent fallbacks:
                    #   circle -> line
                    #   circle -> circle

                    if not self.obeycurv:
                        # do not obey the sign of the curvature but
                        # make the sign such that the curve smoothly passes to the next point
                        # this results in a discontinuous curvature
                        # (but the absolute value is still continuous)
                        s1 = helper.sign(t1[0] * (p2[1]-p1[1]) - t1[1] * (p2[0]-p1[0]))
                        s2 = helper.sign(t2[0] * (p2[1]-p1[1]) - t2[1] * (p2[0]-p1[0]))
                        c1 = s1 * abs(c1)
                        c2 = s2 * abs(c2)

                    # get the length of the control "arms"
                    a, d = controldists_from_endgeometry_pt(p1, p2, t1, t2, c1, c2, epsilon=epsilon)[0]

                    if a >= 0 and d >= 0:
                        # avoid curves with invalid parameterization
                        a = max(a, epsilon)
                        d = max(d, epsilon)

                        # avoid overshooting at the corners:
                        # this changes not only the sign of the curvature
                        # but also the magnitude
                        if not self.obeycurv:
                            t, s = intersection(p1, p2, t1, t2)
                            if (t is not None and s is not None and
                                t > 0 and s < 0):
                                a = min(a, abs(t))
                                d = min(d, abs(s))

                    else:
                        t, s = intersection(p1, p2, t1, t2)
                        if t is not None and s is not None:
                            a = abs(t)
                            d = abs(s)
                        else:
                            # if there is no useful result:
                            # take an arbitrary smoothing curve that does not obey
                            # the curvature constraints
                            dist = math.hypot(p1[0] - p2[0], p1[1] - p2[1])
                            a = dist / (3.0 * math.hypot(*t1))
                            d = dist / (3.0 * math.hypot(*t2))

                    # calculate the two missing control points
                    q1 = p1[0] + a * t1[0], p1[1] + a * t1[1]
                    q2 = p2[0] - d * t2[0], p2[1] - d * t2[1]

                    newnormsubpath.append(normpath.normcurve_pt(*(p1 + q1 + q2 + p2)))

        if normsubpath.closed:
            newnormsubpath.close()
        return newnormsubpath

# >>>

smoothed.clear = attr.clearclass(smoothed)

class parallel(deformer): # <<<

    """creates a parallel normpath with constant distance to the original normpath

    A positive 'distance' results in a curve left of the original one -- and a
    negative 'distance' in a curve at the right. Left/Right are understood in
    terms of the parameterization of the original curve. For each path element
    a parallel curve/line is constructed. At corners, either a circular arc is
    drawn around the corner, or, if possible, the parallel curve is cut in
    order to also exhibit a corner.

    distance:            the distance of the parallel normpath
    relerr:              distance*relerr is the maximal allowed error in the parallel distance
    checkdistanceparams: a list of parameter values in the interval (0,1) where the
                         parallel distance is checked on each normpathitem
    lookforcurvatures:   number of points per normpathitem where is looked for
                         a critical value of the curvature
    dointersection:      boolean for doing the intersection step (default: 1).
                         Set this value to 0 if you want the whole parallel path
    """

    # TODO:
    # * more testing of controldists_from_endgeometry_pt
    # * do testing for curv=0, T=0, D=0, E=0 cases
    # * do testing for several random curves
    #   -- does the recursive deformnicecurve converge?
    #
    # TODO for the test cases:
    # * improve the intersection of nearly degenerate paths


    def __init__(self, distance, relerr=0.05, sharpoutercorners=0, checkdistanceparams=[0.5],
                       lookforcurvatures=11, dointersection=1, debug=None):
        self.distance = distance
        self.relerr = relerr
        self.sharpoutercorners = sharpoutercorners
        self.checkdistanceparams = checkdistanceparams
        self.lookforcurvatures = lookforcurvatures
        self.dointersection = dointersection
        self.debug = debug

    def __call__(self, distance=None, relerr=None, sharpoutercorners=None, checkdistanceparams=None,
                       lookforcurvatures=None, dointersection=None, debug=None):
        # returns a copy of the deformer with different parameters
        if distance is None:
            distance = self.distance
        if relerr is None:
            relerr = self.relerr
        if sharpoutercorners is None:
            sharpoutercorners = self.sharpoutercorners
        if checkdistanceparams is None:
            checkdistanceparams = self.checkdistanceparams
        if lookforcurvatures is None:
            lookforcurvatures = self.lookforcurvatures
        if dointersection is None:
            dointersection = self.dointersection
        if debug is None:
            debug = self.debug

        return parallel(distance=distance, relerr=relerr, sharpoutercorners=sharpoutercorners,
                        checkdistanceparams=checkdistanceparams,
                        lookforcurvatures=lookforcurvatures, dointersection=dointersection,
                        debug=debug)

    def deform(self, basepath):
        self.dist_pt = unit.topt(self.distance)
        resultnormsubpaths = []
        for nsp in basepath.normpath().normsubpaths:
            parallel_normpath = self.deformsubpath(nsp)
            resultnormsubpaths += parallel_normpath.normsubpaths
        result = normpath.normpath(resultnormsubpaths)
        return result

    def deformsubpath(self, orig_nsp): # <<<

        """returns a list of normsubpaths building the parallel curve"""

        dist = self.dist_pt
        epsilon = orig_nsp.epsilon

        # avoid too small dists: we would run into instabilities
        if abs(dist) < abs(epsilon):
            return orig_nsp

        result = normpath.normpath()

        # iterate over the normsubpath in the following manner:
        # * for each item first append the additional arc / intersect
        #   and then add the next parallel piece
        # * for the first item only add the parallel piece
        #   (because this is done for next_orig_nspitem, we need to start with next=0)
        for i in range(len(orig_nsp.normsubpathitems)):
            prev = i-1
            next = i
            prev_orig_nspitem = orig_nsp.normsubpathitems[prev]
            next_orig_nspitem = orig_nsp.normsubpathitems[next]

            stepsize = 0.01
            prev_param, prev_rotation = self.valid_near_rotation(prev_orig_nspitem, 1, 0, stepsize, 0.5*epsilon)
            next_param, next_rotation = self.valid_near_rotation(next_orig_nspitem, 0, 1, stepsize, 0.5*epsilon)
            # TODO: eventually shorten next_orig_nspitem

            prev_tangent = prev_rotation.apply_pt(1, 0)
            next_tangent = next_rotation.apply_pt(1, 0)

            # get the next parallel piece for the normpath
            try:
                next_parallel_normpath = self.deformsubpathitem(next_orig_nspitem, epsilon)
            except InvalidParamException, e:
                invalid_nspitem_param = e.normsubpathitemparam
                # split the nspitem apart and continue with pieces that do not contain
                # the invalid point anymore. At the end, simply take one piece, otherwise two.
                stepsize = 0.01
                if self.length_pt(next_orig_nspitem, invalid_nspitem_param, 0) > epsilon:
                    if self.length_pt(next_orig_nspitem, invalid_nspitem_param, 1) > epsilon:
                        p1, foo = self.valid_near_rotation(next_orig_nspitem, invalid_nspitem_param, 0, stepsize, 0.5*epsilon)
                        p2, foo = self.valid_near_rotation(next_orig_nspitem, invalid_nspitem_param, 1, stepsize, 0.5*epsilon)
                        segments = next_orig_nspitem.segments([0, p1, p2, 1])[0:3:2]
                        segments[1] = segments[1].modifiedbegin_pt(*(segments[0].atend_pt()))
                    else:
                        p1, foo = self.valid_near_rotation(next_orig_nspitem, invalid_nspitem_param, 0, stepsize, 0.5*epsilon)
                        segments = next_orig_nspitem.segments([0, p1])
                else:
                    p2, foo = self.valid_near_rotation(next_orig_nspitem, invalid_nspitem_param, 1, stepsize, 0.5*epsilon)
                    segments = next_orig_nspitem.segments([p2, 1])

                next_parallel_normpath = self.deformsubpath(normpath.normsubpath(segments, epsilon=epsilon))

            if not (next_parallel_normpath.normsubpaths and next_parallel_normpath[0].normsubpathitems):
                continue

            # this starts the whole normpath
            if not result.normsubpaths:
                result = next_parallel_normpath
                continue

            # sinus of the angle between the tangents
            # sinangle > 0 for a left-turning nexttangent
            # sinangle < 0 for a right-turning nexttangent
            sinangle = prev_tangent[0]*next_tangent[1] - prev_tangent[1]*next_tangent[0]
            cosangle = prev_tangent[0]*next_tangent[0] + prev_tangent[1]*next_tangent[1]
            if cosangle < 0 or abs(dist*math.asin(sinangle)) >= epsilon:
                if self.sharpoutercorners and dist*sinangle < 0:
                    A1, A2 = result.atend_pt(), next_parallel_normpath.atbegin_pt()
                    t1, t2 = intersection(A1, A2, prev_tangent, next_tangent)
                    B = A1[0] + t1 * prev_tangent[0], A1[1] + t1 * prev_tangent[1]
                    arc_normpath = normpath.normpath([normpath.normsubpath([
                        normpath.normline_pt(A1[0], A1[1], B[0], B[1]),
                        normpath.normline_pt(B[0], B[1], A2[0], A2[1])
                        ])])
                else:
                    # We must append an arc around the corner
                    arccenter = next_orig_nspitem.atbegin_pt()
                    arcbeg = result.atend_pt()
                    arcend = next_parallel_normpath.atbegin_pt()
                    angle1 = math.atan2(arcbeg[1] - arccenter[1], arcbeg[0] - arccenter[0])
                    angle2 = math.atan2(arcend[1] - arccenter[1], arcend[0] - arccenter[0])

                    # depending on the direction we have to use arc or arcn
                    if dist > 0:
                        arcclass = path.arcn_pt
                    else:
                        arcclass = path.arc_pt
                    arc_normpath = path.path(arcclass(
                      arccenter[0], arccenter[1], abs(dist),
                      degrees(angle1), degrees(angle2))).normpath(epsilon=epsilon)

                # append the arc to the parallel path
                result.join(arc_normpath)
                # append the next parallel piece to the path
                result.join(next_parallel_normpath)
            else:
                # The path is quite straight between prev and next item:
                # normpath.normpath.join adds a straight line if necessary
                result.join(next_parallel_normpath)


        # end here if nothing has been found so far
        if not (result.normsubpaths and result[-1].normsubpathitems):
            return result

        # the curve around the closing corner may still be missing
        if orig_nsp.closed:
            # TODO: normpath.invalid
            stepsize = 0.01
            prev_param, prev_rotation = self.valid_near_rotation(result[-1][-1], 1, 0, stepsize, 0.5*epsilon)
            next_param, next_rotation = self.valid_near_rotation(result[0][0], 0, 1, stepsize, 0.5*epsilon)
            # TODO: eventually shorten next_orig_nspitem

            prev_tangent = prev_rotation.apply_pt(1, 0)
            next_tangent = next_rotation.apply_pt(1, 0)
            sinangle = prev_tangent[0]*next_tangent[1] - prev_tangent[1]*next_tangent[0]
            cosangle = prev_tangent[0]*next_tangent[0] + prev_tangent[1]*next_tangent[1]

            if cosangle < 0 or abs(dist*math.asin(sinangle)) >= epsilon:
                # We must append an arc around the corner
                # TODO: avoid the code dublication
                if self.sharpoutercorners and dist*sinangle < 0:
                    A1, A2 = result.atend_pt(), result.atbegin_pt()
                    t1, t2 = intersection(A1, A2, prev_tangent, next_tangent)
                    B = A1[0] + t1 * prev_tangent[0], A1[1] + t1 * prev_tangent[1]
                    arc_normpath = normpath.normpath([normpath.normsubpath([
                        normpath.normline_pt(A1[0], A1[1], B[0], B[1]),
                        normpath.normline_pt(B[0], B[1], A2[0], A2[1])
                        ])])
                else:
                    arccenter = orig_nsp.atend_pt()
                    arcbeg = result.atend_pt()
                    arcend = result.atbegin_pt()
                    angle1 = math.atan2(arcbeg[1] - arccenter[1], arcbeg[0] - arccenter[0])
                    angle2 = math.atan2(arcend[1] - arccenter[1], arcend[0] - arccenter[0])

                    # depending on the direction we have to use arc or arcn
                    if dist > 0:
                        arcclass = path.arcn_pt
                    else:
                        arcclass = path.arc_pt
                    arc_normpath = path.path(arcclass(
                        arccenter[0], arccenter[1], abs(dist),
                        degrees(angle1), degrees(angle2))).normpath(epsilon=epsilon)

                # append the arc to the parallel path
                if (result.normsubpaths and result[-1].normsubpathitems and
                    arc_normpath.normsubpaths and arc_normpath[-1].normsubpathitems):
                    result.join(arc_normpath)

            if len(result) == 1:
                result[0].close()
            else:
                # if the parallel normpath is split into several subpaths anyway,
                # then use the natural beginning and ending
                # closing is not possible anymore
                for nspitem in result[0]:
                    result[-1].append(nspitem)
                result.normsubpaths = result.normsubpaths[1:]

        if self.dointersection:
            result = self.rebuild_intersected_normpath(result, normpath.normpath([orig_nsp]), epsilon)

        return result
        # >>>
    def deformsubpathitem(self, nspitem, epsilon): # <<<

        """Returns a parallel normpath for a single normsubpathitem

        Analyzes the curvature of a normsubpathitem and returns a normpath with
        the appropriate number of normsubpaths. This must be a normpath because
        a normcurve can be strongly curved, such that the parallel path must
        contain a hole"""

        dist = self.dist_pt

        # for a simple line we return immediately
        if isinstance(nspitem, normpath.normline_pt):
            normal = nspitem.rotation([0])[0].apply_pt(0, 1)
            start = nspitem.atbegin_pt()
            end = nspitem.atend_pt()
            return path.line_pt(
                start[0] + dist * normal[0], start[1] + dist * normal[1],
                end[0] + dist * normal[0], end[1] + dist * normal[1]).normpath(epsilon=epsilon)

        # for a curve we have to check if the curvatures
        # cross the singular value 1/dist
        crossings = self.distcrossingparameters(nspitem, epsilon)

        # depending on the number of crossings we must consider
        # three different cases:
        if crossings:
            # The curvature crosses the borderline 1/dist
            # the parallel curve contains points with infinite curvature!
            result = normpath.normpath()

            # we need the endpoints of the nspitem
            if self.length_pt(nspitem, crossings[0], 0) > epsilon:
                crossings.insert(0, 0)
            if self.length_pt(nspitem, crossings[-1], 1) > epsilon:
                crossings.append(1)

            for i in range(len(crossings) - 1):
                middleparam = 0.5*(crossings[i] + crossings[i+1])
                middlecurv = nspitem.curvature_pt([middleparam])[0]
                if middlecurv is normpath.invalid:
                    raise InvalidParamException(middleparam)
                # the radius is good if
                #  - middlecurv and dist have opposite signs or
                #  - middlecurv is "smaller" than 1/dist
                if middlecurv*dist < 0 or abs(dist*middlecurv) < 1:
                    parallel_nsp = self.deformnicecurve(nspitem.segments(crossings[i:i+2])[0], epsilon)
                    # never append empty normsubpaths
                    if parallel_nsp.normsubpathitems:
                        result.append(parallel_nsp)

            return result

        else:
            # the curvature is either bigger or smaller than 1/dist
            middlecurv = nspitem.curvature_pt([0.5])[0]
            if dist*middlecurv < 0 or abs(dist*middlecurv) < 1:
                # The curve is everywhere less curved than 1/dist
                # We can proceed finding the parallel curve for the whole piece
                parallel_nsp = self.deformnicecurve(nspitem, epsilon)
                # never append empty normsubpaths
                if parallel_nsp.normsubpathitems:
                    return normpath.normpath([parallel_nsp])
                else:
                    return normpath.normpath()
            else:
                # the curve is everywhere stronger curved than 1/dist
                # There is nothing to be returned.
                return normpath.normpath()

        # >>>
    def deformnicecurve(self, normcurve, epsilon, startparam=0.0, endparam=1.0): # <<<

        """Returns a parallel normsubpath for the normcurve.

        This routine assumes that the normcurve is everywhere
        'less' curved than 1/dist and contains no point with an
        invalid parameterization
        """
        dist = self.dist_pt
        T_threshold = 1.0e-5

        # normalized tangent directions
        tangA, tangD = normcurve.rotation([startparam, endparam])
        # if we find an unexpected normpath.invalid we have to
        # parallelise this normcurve on the level of split normsubpaths
        if tangA is normpath.invalid:
            raise InvalidParamException(startparam)
        if tangD is normpath.invalid:
            raise InvalidParamException(endparam)
        tangA = tangA.apply_pt(1, 0)
        tangD = tangD.apply_pt(1, 0)

        # the new starting points
        orig_A, orig_D = normcurve.at_pt([startparam, endparam])
        A = orig_A[0] - dist * tangA[1], orig_A[1] + dist * tangA[0]
        D = orig_D[0] - dist * tangD[1], orig_D[1] + dist * tangD[0]

        # we need to end this _before_ we will run into epsilon-problems
        # when creating curves we do not want to calculate the length of
        # or even split it for recursive calls
        if (math.hypot(A[0] - D[0], A[1] - D[1]) < epsilon and
            math.hypot(tangA[0] - tangD[0], tangA[1] - tangD[1]) < T_threshold):
            return normpath.normsubpath([normpath.normline_pt(A[0], A[1], D[0], D[1])], epsilon=epsilon)

        result = normpath.normsubpath(epsilon=epsilon)
        # is there enough space on the normals before they intersect?
        a, d = intersection(orig_A, orig_D, (-tangA[1], tangA[0]), (-tangD[1], tangD[0]))
        # a,d are the lengths to the intersection points:
        # for a (and equally for b) we can proceed in one of the following cases:
        #   a is None (means parallel normals)
        #   a and dist have opposite signs (and the same for b)
        #   a has the same sign but is bigger
        if ( (a is None or a*dist < 0 or abs(a) > abs(dist) + epsilon) or
             (d is None or d*dist < 0 or abs(d) > abs(dist) + epsilon) ):
            # the original path is long enough to draw a parallel piece
            # this is the generic case. Get the parallel curves
            orig_curvA, orig_curvD = normcurve.curvature_pt([startparam, endparam])
            # normpath.invalid may not appear here because we have asked
            # for this already at the tangents
            assert orig_curvA is not normpath.invalid
            assert orig_curvD is not normpath.invalid
            curvA = orig_curvA / (1.0 - dist*orig_curvA)
            curvD = orig_curvD / (1.0 - dist*orig_curvD)

            # first try to approximate the normcurve with a single item
            # TODO: is it good enough to get the first entry here?
            # TODO: we rely on getting a result!
            a, d = controldists_from_endgeometry_pt(A, D, tangA, tangD, curvA, curvD, epsilon=epsilon)[0]
            if a >= 0 and d >= 0:
                if a < epsilon and d < epsilon:
                    result = normpath.normsubpath([normpath.normline_pt(A[0], A[1], D[0], D[1])], epsilon=epsilon)
                else:
                    # we avoid curves with invalid parameterization
                    a = max(a, epsilon)
                    d = max(d, epsilon)
                    result = normpath.normsubpath([normpath.normcurve_pt(
                        A[0], A[1],
                        A[0] + a * tangA[0], A[1] + a * tangA[1],
                        D[0] - d * tangD[0], D[1] - d * tangD[1],
                        D[0], D[1])], epsilon=epsilon)

            # then try with two items, recursive call
            if ((not result.normsubpathitems) or
                (self.checkdistanceparams and result.normsubpathitems
                 and not self.distchecked(normcurve, result, epsilon, startparam, endparam))):
                # TODO: does this ever converge?
                # TODO: what if this hits epsilon?
                firstnsp = self.deformnicecurve(normcurve, epsilon, startparam, 0.5*(startparam+endparam))
                secondnsp = self.deformnicecurve(normcurve, epsilon, 0.5*(startparam+endparam), endparam)
                if not (firstnsp.normsubpathitems and secondnsp.normsubpathitems):
                    result = normpath.normsubpath(
                        [normpath.normline_pt(A[0], A[1], D[0], D[1])], epsilon=epsilon)
                else:
                    # we will get problems if the curves are too short:
                    result = firstnsp.joined(secondnsp)

        return result
        # >>>

    def distchecked(self, orig_normcurve, parallel_normsubpath, epsilon, tstart, tend): # <<<

        """Checks the distances between orig_normcurve and parallel_normsubpath

        The checking is done at parameters self.checkdistanceparams of orig_normcurve."""

        dist = self.dist_pt
        # do not look closer than epsilon:
        dist_relerr = helper.sign(dist) * max(abs(self.relerr*dist), epsilon)

        checkdistanceparams = [tstart + (tend-tstart)*t for t in self.checkdistanceparams]

        for param, P, rotation in zip(checkdistanceparams,
                                      orig_normcurve.at_pt(checkdistanceparams),
                                      orig_normcurve.rotation(checkdistanceparams)):
            # check if the distance is really the wanted distance
            # measure the distance in the "middle" of the original curve
            if rotation is normpath.invalid:
                raise InvalidParamException(param)

            normal = rotation.apply_pt(0, 1)

            # create a short cutline for intersection only:
            cutline = normpath.normsubpath([normpath.normline_pt (
              P[0] + (dist - 2*dist_relerr) * normal[0],
              P[1] + (dist - 2*dist_relerr) * normal[1],
              P[0] + (dist + 2*dist_relerr) * normal[0],
              P[1] + (dist + 2*dist_relerr) * normal[1])], epsilon=epsilon)

            cutparams = parallel_normsubpath.intersect(cutline)
            distances = [math.hypot(P[0] - cutpoint[0], P[1] - cutpoint[1])
                         for cutpoint in cutline.at_pt(cutparams[1])]

            if (not distances) or (abs(min(distances) - abs(dist)) > abs(dist_relerr)):
                return 0

        return 1
    # >>>
    def distcrossingparameters(self, normcurve, epsilon, tstart=0, tend=1): # <<<

        """Returns a list of parameters where the curvature is 1/distance"""

        dist = self.dist_pt

        # we _need_ to do this with the curvature, not with the radius
        # because the curvature is continuous at the straight line and the radius is not:
        # when passing from one slightly curved curve to the other with opposite curvature sign,
        # via the straight line, then the curvature changes its sign at curv=0, while the
        # radius changes its sign at +/-infinity
        # this causes instabilities for nearly straight curves

        # include tstart and tend
        params = [tstart + i * (tend - tstart) * 1.0 / (self.lookforcurvatures - 1)
                  for i in range(self.lookforcurvatures)]
        curvs = normcurve.curvature_pt(params)

        # break everything at invalid curvatures
        for param, curv in zip(params, curvs):
            if curv is normpath.invalid:
                raise InvalidParamException(param)

        parampairs = zip(params[:-1], params[1:])
        curvpairs = zip(curvs[:-1], curvs[1:])

        crossingparams = []
        for parampair, curvpair in zip(parampairs, curvpairs):
            begparam, endparam = parampair
            begcurv, endcurv = curvpair
            if (endcurv*dist - 1)*(begcurv*dist - 1) < 0:
                # the curvature crosses the value 1/dist
                # get the parmeter value by linear interpolation:
                middleparam = (
                  (begparam * abs(begcurv*dist - 1) + endparam * abs(endcurv*dist - 1)) /
                  (abs(begcurv*dist - 1) + abs(endcurv*dist - 1)))
                middleradius = normcurve.curveradius_pt([middleparam])[0]

                if middleradius is normpath.invalid:
                    raise InvalidParamException(middleparam)

                if abs(middleradius - dist) < epsilon:
                    # get the parmeter value by linear interpolation:
                    crossingparams.append(middleparam)
                else:
                    # call recursively:
                    cps = self.distcrossingparameters(normcurve, epsilon, tstart=begparam, tend=endparam)
                    crossingparams += cps

        return crossingparams
        # >>>
    def valid_near_rotation(self, nspitem, param, otherparam, stepsize, epsilon): # <<<
        p = param
        rot = nspitem.rotation([p])[0]
        # run towards otherparam searching for a valid rotation
        while rot is normpath.invalid:
            p = (1-stepsize)*p + stepsize*otherparam
            rot = nspitem.rotation([p])[0]
        # walk back to param until near enough
        # but do not go further if an invalid point is hit
        end, new = nspitem.at_pt([param, p])
        far = math.hypot(end[0]-new[0], end[1]-new[1])
        pnew = p
        while far > epsilon:
            pnew = (1-stepsize)*pnew + stepsize*param
            end, new = nspitem.at_pt([param, pnew])
            far = math.hypot(end[0]-new[0], end[1]-new[1])
            if nspitem.rotation([pnew])[0] is normpath.invalid:
                break
            else:
                p = pnew
        return p, nspitem.rotation([p])[0]
    # >>>
    def length_pt(self, path, param1, param2): # <<<
        point1, point2 = path.at_pt([param1, param2])
        return math.hypot(point1[0] - point2[0], point1[1] - point2[1])
    # >>>

    def normpath_selfintersections(self, np, epsilon): # <<<

        """return all self-intersection points of normpath np.

        This does not include the intersections of a single normcurve with itself,
        but all intersections of one normpathitem with a different one in the path"""

        n = len(np)
        linearparams = []
        parampairs = []
        paramsriap = {}
        for nsp_i in range(n):
            for nsp_j in range(nsp_i, n):
                for nspitem_i in range(len(np[nsp_i])):
                    if nsp_j == nsp_i:
                        nspitem_j_range = range(nspitem_i+1, len(np[nsp_j]))
                    else:
                        nspitem_j_range = range(len(np[nsp_j]))
                    for nspitem_j in nspitem_j_range:
                        #print "intersecting (%d,%d) with (%d,%d)" %(nsp_i, nspitem_i, nsp_j, nspitem_j)
                        intsparams = np[nsp_i][nspitem_i].intersect(np[nsp_j][nspitem_j], epsilon)
                        #if 1:#intsparams:
                        #    print np[nsp_i][nspitem_i]
                        #    print np[nsp_j][nspitem_j]
                        #    print intsparams
                        if intsparams:
                            for intsparam_i, intsparam_j in intsparams:
                                if ( (abs(intsparam_i) < epsilon and abs(1-intsparam_j) < epsilon) or 
                                     (abs(intsparam_j) < epsilon and abs(1-intsparam_i) < epsilon) ):
                                     continue
                                npp_i = normpath.normpathparam(np, nsp_i, float(nspitem_i)+intsparam_i)
                                npp_j = normpath.normpathparam(np, nsp_j, float(nspitem_j)+intsparam_j)
                                linearparams.append(npp_i)
                                linearparams.append(npp_j)
                                paramsriap[npp_i] = len(parampairs)
                                paramsriap[npp_j] = len(parampairs)
                                parampairs.append((npp_i, npp_j))
        linearparams.sort()
        return linearparams, parampairs, paramsriap

    # >>>
    def can_continue(self, par_np, param1, param2): # <<<
        dist = self.dist_pt

        rot1, rot2 = par_np.rotation([param1, param2])
        if rot1 is normpath.invalid or rot2 is normpath.invalid:
            return 0
        curv1, curv2 = par_np.curvature_pt([param1, param2])
        tang2 = rot2.apply_pt(1, 0)
        norm1 = rot1.apply_pt(0, -1)
        norm1 = (dist*norm1[0], dist*norm1[1])

        # the self-intersection is valid if the tangents
        # point into the correct direction or, for parallel tangents,
        # if the curvature is such that the on-going path does not
        # enter the region defined by dist
        mult12 = norm1[0]*tang2[0] + norm1[1]*tang2[1]
        eps = 1.0e-6
        if abs(mult12) > eps:
            return (mult12 < 0)
        else:
            # tang1 and tang2 are parallel
            if curv2 is normpath.invalid or curv1 is normpath.invalid:
                return 0
            if dist > 0:
                return (curv2 <= curv1)
            else:
                return (curv2 >= curv1)
    # >>>
    def rebuild_intersected_normpath(self, par_np, orig_np, epsilon): # <<<

        dist = self.dist_pt

        # calculate the self-intersections of the par_np
        selfintparams, selfintpairs, selfintsriap = self.normpath_selfintersections(par_np, epsilon)
        # calculate the intersections of the par_np with the original path
        origintparams = par_np.intersect(orig_np)[0]

        # visualize the intersection points: # <<<
        if self.debug is not None:
            for param1, param2 in selfintpairs:
                point1, point2 = par_np.at([param1, param2])
                self.debug.fill(path.circle(point1[0], point1[1], 0.05), [color.rgb.red])
                self.debug.fill(path.circle(point2[0], point2[1], 0.03), [color.rgb.black])
            for param in origintparams:
                point = par_np.at([param])[0]
                self.debug.fill(path.circle(point[0], point[1], 0.05), [color.rgb.green])
        # >>>

        result = normpath.normpath()
        if not selfintparams:
            if origintparams:
                return result
            else:
                return par_np

        beginparams = []
        endparams = []
        for i in range(len(par_np)):
            beginparams.append(normpath.normpathparam(par_np, i, 0))
            endparams.append(normpath.normpathparam(par_np, i, len(par_np[i])))

        allparams = selfintparams + origintparams + beginparams + endparams
        allparams.sort()
        allparamindices = {}
        for i, param in enumerate(allparams):
            allparamindices[param] = i

        done = {}
        for param in allparams:
            done[param] = 0

        def otherparam(p): # <<<
            pair = selfintpairs[selfintsriap[p]]
            if (p is pair[0]):
                return pair[1]
            else:
                return pair[0]
        # >>>
        def trial_parampairs(startp): # <<<
            tried = {}
            for param in allparams:
                tried[param] = done[param]

            lastp = startp
            currentp = allparams[allparamindices[startp] + 1]
            result = []

            while 1:
                if currentp is startp:
                    result.append((lastp, currentp))
                    return result
                if currentp in selfintparams and otherparam(currentp) is startp:
                    result.append((lastp, currentp))
                    return result
                if currentp in endparams:
                    result.append((lastp, currentp))
                    return result
                if tried[currentp]:
                    return []
                if currentp in origintparams:
                    return []
                # follow the crossings on valid startpairs until
                # the normsubpath is closed or the end is reached
                if (currentp in selfintparams and
                    self.can_continue(par_np, currentp, otherparam(currentp))):
                    # go to the next pair on the curve, seen from currentpair[1]
                    result.append((lastp, currentp))
                    lastp = otherparam(currentp)
                    tried[currentp] = 1
                    tried[otherparam(currentp)] = 1
                    currentp = allparams[allparamindices[otherparam(currentp)] + 1]
                else:
                    # go to the next pair on the curve, seen from currentpair[0]
                    tried[currentp] = 1
                    tried[otherparam(currentp)] = 1
                    currentp = allparams[allparamindices[currentp] + 1]
            assert 0
        # >>>

        # first the paths that start at the beginning of a subnormpath:
        for startp in beginparams + selfintparams:
            if done[startp]:
                continue

            parampairs = trial_parampairs(startp)
            if not parampairs:
                continue

            # collect all the pieces between parampairs
            add_nsp = normpath.normsubpath(epsilon=epsilon)
            for begin, end in parampairs:
                # check that trial_parampairs works correctly
                assert begin is not end
                # we do not cross the border of a normsubpath here
                assert begin.normsubpathindex is end.normsubpathindex
                for item in par_np[begin.normsubpathindex].segments(
                    [begin.normsubpathparam, end.normsubpathparam])[0].normsubpathitems:
                    # TODO: this should be obsolete with an improved intersecion algorithm
                    # guaranteeing epsilon
                    if add_nsp.normsubpathitems:
                        item = item.modifiedbegin_pt(*(add_nsp.atend_pt()))
                    add_nsp.append(item)

                if begin in selfintparams:
                    done[begin] = 1
                    #done[otherparam(begin)] = 1
                if end in selfintparams:
                    done[end] = 1
                    #done[otherparam(end)] = 1

            # eventually close the path
            if (parampairs[0][0] is parampairs[-1][-1] or
                (parampairs[0][0] in selfintparams and otherparam(parampairs[0][0]) is parampairs[-1][-1])):
                add_nsp.normsubpathitems[-1] = add_nsp.normsubpathitems[-1].modifiedend_pt(*add_nsp.atbegin_pt())
                add_nsp.close()

            result.extend([add_nsp])

        return result

    # >>>

# >>>

parallel.clear = attr.clearclass(parallel)

# vim:foldmethod=marker:foldmarker=<<<,>>>
