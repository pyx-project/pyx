#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2003-2004 Michael Schindler <m-schindler@users.sourceforge.net>
# Copyright (C) 2002-2004 André Wobst <wobsta@users.sourceforge.net>
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


import math, warnings
import attr, color, helper, path, style, trafo, unit
try:
  import Numeric, LinearAlgebra
  have_la_packages = 1

  def realpolyroots(coeffs, epsilon=1e-5): # <<<

      """returns the roots of a polynom with given coefficients

      This helper routine uses the package Numeric to find the roots
      of the polynomial with coefficients given in coeffs:
        0 = \sum_{i=0}^N x^{N-i} coeffs[i]
      The solution is found via an equivalent eigenvalue problem
      """

      try:
          1.0 / coeffs[0]
      except:
          return realpolyroots(coeffs[1:], epsilon=epsilon)
      else:

          N = len(coeffs)
          # build the Matrix of the polynomial problem
          mat = Numeric.zeros((N, N), Numeric.Float)
          for i in range(N-1):
              mat[i+1][i] = 1
          for i in range(N-1):
              mat[0][i] = -coeffs[i+1]/coeffs[0]
          # find the eigenvalues of the matrix (== the zeros of the polynomial)
          zeros = [complex(zero) for zero in LinearAlgebra.eigenvalues(mat)]
          # take only the real zeros
          zeros = [zero.real for zero in zeros if -epsilon < zero.imag < epsilon]

          ## check if the zeros are really zeros!
          #for zero in zeros:
          #    p = 0
          #    for i in range(N):
          #        p += coeffs[i] * zero**(N-i)
          #    if abs(p) > epsilon:
          #        raise Exception("value %f instead of 0" % p)

      return zeros
  # >>>

except ImportError:
  have_la_packages = 0


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

def controldists_from_endpoints_pt (A, B, tangentA, tangentB, curvA, curvB, epsilon=1e-5): # <<<

    """distances for a curve given by tangents and curvatures at the endpoints

    This helper routine returns the two distances between the endpoints and the
    corresponding control points of a (cubic) bezier curve that has
    prescribed tangents tangentA, tangentB and curvatures curvA, curvB at the
    end points.
    """

    # normalise the tangent vectors
    normA = math.hypot(*tangentA)
    tangA = (tangentA[0] / normA, tangentA[1] / normA)
    normB = math.hypot(*tangentB)
    tangB = (tangentB[0] / normB, tangentB[1] / normB)
    # some shortcuts
    T = tangB[0] * tangA[1] - tangB[1] * tangA[0]
    D =   tangA[0] * (B[1]-A[1]) - tangA[1] * (B[0]-A[0])
    E = - tangB[0] * (B[1]-A[1]) + tangB[1] * (B[0]-A[0])
    # the variables: \dot X(0) = 3 * a * tangA
    #                \dot X(1) = 3 * b * tangB
    a, b = None, None


    # try some special cases where the equations decouple
    try:
        1.0 / T
    except ZeroDivisionError:
        try:
            a = math.sqrt(2.0 * D / (3.0 * curvA))
            b = math.sqrt(2.0 * E / (3.0 * curvB))
        except ZeroDivisionError:
            a = b = None
    else:
        try:
            1.0 / curvA
        except ZeroDivisionError:
            b = -D / T
            a = (1.5*curvB*b*b - E) / T
        else:
            try:
                1.0 / curvB
            except ZeroDivisionError:
                a = -E / T
                b = (1.5*curvA*a*a - D) / T
            else:
                a, b = None, None


    # else find a solution for the full problem
    if a is None:
        if have_la_packages:
            # we first try to find all the zeros of the polynomials for a or b (4th order)
            # this needs Numeric and LinearAlgebra

            coeffs_a = (3.375*curvA*curvA*curvB, 0, -4.5*curvA*curvB*D, -T**3,  1.5*curvB*D*D - T*T*E)
            coeffs_b = (3.375*curvA*curvB*curvB, 0, -4.5*curvA*curvB*E, -T**3,  1.5*curvA*E*E - T*T*D)

            # First try the equation for a
            cands_a = [cand for cand in realpolyroots(coeffs_a) if cand > 0]

            if cands_a:
                a = min(cands_a)
                b = (1.5*curvA*a*a - D) / T
            else:
                # then, try the equation for b
                cands_b = [cand for cand in realpolyroots(coeffs_b) if cand > 0]
                if cands_b:
                    b = min(cands_b)
                    a = (1.5*curvB*b*b - E) / T
                else:
                    a = b = None

        else:
            # if the Numeric modules are not available:
            # solve the coupled system by Newton iteration
            #     0 = Ga(a,b) = 0.5 a |a| curvA + b * T - D
            #     0 = Gb(a,b) = 0.5 b |b| curvB + a * T + E
            # this system is equivalent to the geometric contraints:
            #     the curvature and the normal tangent vectors
            #     at parameters 0 and 1 are to be continuous
            # the system is solved by 2-dim Newton-Iteration
            # (a,b)^{i+1} = (a,b)^i - (DG)^{-1} (Ga(a^i,b^i), Gb(a^i,b^i))
            a = 1.0 / abs(curvA)
            b = 1.0 / abs(curvB)
            eps = 1.0 # stepwith for the Newton iteration
            da = db = 2*epsilon
            counter = 0
            while max(abs(da),abs(db)) > epsilon and counter < 1000:

                Ga = eps * (1.5*curvA*a*a - T*b - D)
                Gb = eps * (1.5*curvB*b*b - T*a - E)

                detDG = 9.0*a*b*curvA*curvB - T*T
                invDG = ((3.0*curvB*b/detDG, T/detDG), (T/detDG, 3.0*curvA*a/detDG))

                da = invDG[0][0] * Ga + invDG[0][1] * Gb
                db = invDG[1][0] * Ga + invDG[1][1] * Gb

                a -= da
                b -= db

                counter += 1

    if a < 0 or b < 0:
        a = b = None

    if a is not None: a /= normA
    if b is not None: b /= normB

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


class deformer(attr.attr):

    def deform (self, basepath):
        return origpath

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

    def deform(self, abasepath):
        basepath = abasepath.normpath()

        for sp in basepath.normsubpaths:
            if sp == basepath.normsubpaths[0]:
                cycloidpath = self.deformsubpath(sp)
            else:
                cycloidpath.join(self.deformsubpath(sp))

        return cycloidpath

    def deformsubpath(self, subpath):

        skipfirst = abs(unit.topt(self.skipfirst))
        skiplast = abs(unit.topt(self.skiplast))
        radius = abs(unit.topt(self.radius))
        turnangle = self.turnangle * math.pi / 180.0

        cosTurn = math.cos(turnangle)
        sinTurn = math.sin(turnangle)

        # make list of the lengths and parameters at points on subpath where we will add cycloid-points
        totlength = subpath.arclen_pt()
        if totlength <= skipfirst + skiplast + 2*radius*sinTurn:
            warnings.warn("subpath is too short for deformation with cycloid -- skipping...")
            return path.normpath([subpath])

        # parametrisation is in rotation-angle around the basepath
        # differences in length, angle ... between two basepoints
        # and between basepoints and controlpoints
        Dphi = math.pi / self.curvesperhloop
        phis = [i * Dphi for i in range(self.halfloops * self.curvesperhloop + 1)]
        DzDphi = (totlength - skipfirst - skiplast - 2*radius*sinTurn) * 1.0 / (self.halfloops * math.pi * cosTurn)
        Dz = (totlength - skipfirst - skiplast - 2*radius*sinTurn) * 1.0 / (self.halfloops * self.curvesperhloop * cosTurn)
        zs = [i * Dz for i in range(self.halfloops * self.curvesperhloop + 1)]
        # from path._arctobcurve:
        # optimal relative distance along tangent for second and third control point
        L = 4 * radius * (1 - math.cos(Dphi/2)) / (3 * math.sin(Dphi/2))

        # Now the transformation of z into the turned coordinate system
        Zs = [ skipfirst + radius*sinTurn # here the coordinate z starts
             - sinTurn*radius*math.cos(phi) + cosTurn*DzDphi*phi # the transformed z-coordinate
             for phi in phis]
        params = subpath._arclentoparam_pt(Zs)[0]

        # get the positions of the splitpoints in the cycloid
        points = []
        for phi, param in zip(phis, params):
            # the cycloid is a circle that is stretched along the subpath
            # here are the points of that circle
            basetrafo = subpath.trafo([param])[0]

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
            pathradius = subpath.curveradius_pt([param])[0]
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
            points.append(basetrafo._apply(preeZ, self.sign * preeY) +
                          basetrafo._apply(baseZ, self.sign * baseY) +
                          basetrafo._apply(postZ, self.sign * postY))

        if len(points) <= 1:
            warnings.warn("subpath is too short for deformation with cycloid -- skipping...")
            return path.normpath([subpath])

        # Build the path from the pointlist
        # containing (control x 2,  base x 2, control x 2)
        if skipfirst > subpath.epsilon:
            newpath = subpath.segments([0, params[0]])[0]
            newpath.append(path.normcurve_pt(*(points[0][2:6] + points[1][0:4])))
            cycloidpath = path.normpath([newpath])
        else:
            cycloidpath = path.normpath([path.normsubpath([path.normcurve_pt(*(points[0][2:6] + points[1][0:4]))], 0)])
        for i in range(1, len(points)-1):
            cycloidpath.normsubpaths[-1].append(path.normcurve_pt(*(points[i][2:6] + points[i+1][0:4])))
        if skiplast > subpath.epsilon:
            cycloidpath.join(path.normpath(subpath.segments([params[-1], len(subpath)])))

        # That's it
        return cycloidpath
# >>>

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

    def __init__(self, radius, softness=1, obeycurv=0):
        self.radius = radius
        self.softness = softness
        self.obeycurv = obeycurv

    def __call__(self, radius=None, softness=None, obeycurv=None):
        if radius is None:
            radius = self.radius
        if softness is None:
            softness = self.softness
        if obeycurv is None:
            obeycurv = self.obeycurv
        return smoothed(radius=radius, softness=softness, obeycurv=obeycurv)

    def deform(self, abasepath):
        basepath = abasepath.normpath()
        smoothpath = path.path()

        for sp in basepath.normsubpaths:
            smoothpath += self.deformsubpath(sp)

        return smoothpath

    def deformsubpath(self, normsubpath):

        radius = unit.topt(self.radius)
        epsilon = normsubpath.epsilon

        # 1. Build up a list of all relevant normsubpathitems
        #    and the lengths where they will be cut (length with respect to the normsubpath)
        all_npitems = normsubpath.normsubpathitems
        rel_npitems, arclengths = [], []
        for npitem in all_npitems:

            arclength = npitem.arclen_pt(epsilon)

            # items that should be totally skipped:
            # (we throw away the possible ending "closepath" piece)
            if (arclength > radius):
                rel_npitems.append(npitem)
                arclengths.append(arclength)
            else:
                warnings.warn("smoothed is skipping a too short normsubpathitem")

        # 2. Find the parameters, points,
        #    and calculate tangents and curvatures
        params, points, tangents, curvatures = [], [], [], []
        for npitem, arclength in zip(rel_npitems, arclengths):

            # find the parameter(s): either one or two
            # for short items we squeeze the radius
            if arclength > 2 * radius:
                cut_alengths = [radius, arclength - radius]
            else:
                cut_alengths = [0.5 * radius]

            # get the parameters
            pars = npitem._arclentoparam_pt(cut_alengths, epsilon)[0]

            # the endpoints of an open subpath must be handled specially
            if not normsubpath.closed:
                if npitem is rel_npitems[0]:
                    pars[0] = 0
                if npitem is rel_npitems[-1]:
                    pars[-1] = 1

            # find points, tangents and curvatures
            ts,cs,ps = [],[],[]
            for par in pars:
                thetrafo = npitem.trafo([par])[0]
                p = thetrafo._apply(0,0)
                t = thetrafo._apply(1,0)
                ps.append(p)
                ts.append((t[0]-p[0], t[1]-p[1]))
                r = npitem.curveradius_pt([par])[0]
                if r is None:
                    cs.append(0)
                else:
                    cs.append(1.0 / r)

            params.append(pars)
            points.append(ps)
            tangents.append(ts)
            curvatures.append(cs)


        # create an empty path to collect pathitems
        # this will be returned as normpath, later
        smoothpath = path.path()
        do_moveto = 1 # we do not know yet where to moveto

        ## 3. First part of extra handling of open paths
        #if not normsubpath.closed:

        #    if len(params[0]) == 1:
        #        beginpiece = npitems[npitemnumbers[0]].segments([0, params[0]])[0]
        #    else:
        #        beginpiece = npitems[npitemnumbers[0]].segments([0, params[0][0]])[0]

        #    if do_moveto:
        #        smoothpath.append(path.moveto_pt(*beginpiece.atbegin_pt()))
        #        do_moveto = 0

        #    if isinstance(beginpiece, path.normline_pt):
        #        smoothpath.append(path.lineto_pt(*beginpiece.atend_pt()))
        #    elif isinstance(beginpiece, path.normcurve_pt):
        #        smoothpath.append(path.curveto_pt(
        #           beginpiece.x1_pt, beginpiece.y1_pt,
        #           beginpiece.x2_pt, beginpiece.y2_pt,
        #           beginpiece.x3_pt, beginpiece.y3_pt))

        #    do_moveto = 0

        # 4. Do the splitting for the first to the last element,
        #    a closed path must be closed later
        #
        for i in range(len(rel_npitems)):

            this = i
            next = (i+1) % len(rel_npitems)
            thisnpitem = rel_npitems[this]
            nextnpitem = rel_npitems[next]

            # split thisnpitem apart and take the middle piece
            # We start the new path with the middle piece of the first path-elem
            if len(points[this]) == 2:

                middlepiece = thisnpitem.segments(params[this])[0]

                if do_moveto:
                    smoothpath.append(path.moveto_pt(*middlepiece.atbegin_pt()))
                    do_moveto = 0

                if isinstance(middlepiece, path.normline_pt):
                    smoothpath.append(path.lineto_pt(*middlepiece.atend_pt()))
                elif isinstance(middlepiece, path.normcurve_pt):
                    smoothpath.append(path.curveto_pt(
                      middlepiece.x1_pt, middlepiece.y1_pt,
                      middlepiece.x2_pt, middlepiece.y2_pt,
                      middlepiece.x3_pt, middlepiece.y3_pt))

            if (not normsubpath.closed) and (thisnpitem is rel_npitems[-1]):
                continue

            # add the curve(s) replacing the corner
            if isinstance(thisnpitem, path.normline_pt) and \
               isinstance(nextnpitem, path.normline_pt) and \
               epsilon > math.hypot(thisnpitem.atend_pt()[0] - nextnpitem.atbegin_pt()[0],
                                    thisnpitem.atend_pt()[0] - nextnpitem.atbegin_pt()[0]):

                d1,g1,f1,e,f2,g2,d2 = curvescontrols_from_endlines_pt(
                    thisnpitem.atend_pt(), tangents[this][-1], tangents[next][0],
                    math.hypot(points[this][-1][0] - thisnpitem.atend_pt()[0], points[this][-1][1] - thisnpitem.atend_pt()[1]),
                    math.hypot(points[next][0][0] - nextnpitem.atbegin_pt()[0], points[next][0][1] - nextnpitem.atbegin_pt()[1]),
                    softness=self.softness)

                if do_moveto:
                    smoothpath.append(path.moveto_pt(*d1))
                    do_moveto = 0

                smoothpath.append(path.curveto_pt(*(g1 + f1 + e)))
                smoothpath.append(path.curveto_pt(*(f2 + g2 + d2)))

            else:

                A, D = points[this][-1], points[next][0]
                tangA, tangD = tangents[this][-1], tangents[next][0]
                curvA, curvD = curvatures[this][-1], curvatures[next][0]
                if not self.obeycurv:
                    # do not obey the sign of the curvature but
                    # make the sign such that the curve smoothly passes to the next point
                    # this results in a discontinuous curvature
                    # (but the absolute value is still continuous)
                    sA = sign1(tangA[0] * (D[1]-A[1]) - tangA[1] * (D[0]-A[0]))
                    sD = sign1(tangD[0] * (D[1]-A[1]) - tangD[1] * (D[0]-A[0]))
                    curvA = sA * abs(curvA)
                    curvD = sD * abs(curvD)

                # get the length of the control "arms"
                a, d = controldists_from_endpoints_pt (
                    A, D, tangA, tangD, curvA, curvD,
                    epsilon=epsilon)

                # avoid overshooting at the corners:
                # this changes not only the sign of the curvature
                # but also the magnitude
                if not self.obeycurv:
                    t, s = intersection(A, D, tangA, tangD)
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
                    dist = math.hypot(A[0] - D[0], A[1] - D[1])
                    a = dist / (3.0 * math.hypot(*tangA))
                    d = dist / (3.0 * math.hypot(*tangD))
                    #warnings.warn("The connecting bezier cannot be found. Using a simple fallback.")

                # calculate the two missing control points
                B = A[0] + a * tangA[0], A[1] + a * tangA[1]
                C = D[0] - d * tangD[0], D[1] - d * tangD[1]

                if do_moveto:
                    smoothpath.append(path.moveto_pt(*A))
                    do_moveto = 0

                smoothpath.append(path.curveto_pt(*(B + C + D)))


        # 5. Second part of extra handling of closed paths
        if normsubpath.closed:
            if do_moveto:
                smoothpath.append(path.moveto_pt(*dp.strokepath.atbegin()))
                warnings.warn("The whole subpath has been smoothed away -- sorry")
            #smoothpath.append(path.closepath())

        #else:
        #    epart = npitems[npitemnumbers[-1]].segments([params[-1][0], 1])[0]
        #    if do_moveto:
        #        smoothpath.append(path.moveto_pt(*epart.atbegin_pt()))
        #        do_moveto = 0
        #    if isinstance(epart, path.normline_pt):
        #        smoothpath.append(path.lineto_pt(*epart.atend_pt()))
        #    elif isinstance(epart, path.normcurve_pt):
        #        smoothpath.append(path.curveto_pt(epart.x1_pt, epart.y1_pt, epart.x2_pt, epart.y2_pt, epart.x3_pt, epart.y3_pt))

        return smoothpath
# >>>

smoothed.clear = attr.clearclass(smoothed)

_base = unit.v_cm
smoothed.SHARP = smoothed(radius=_base/math.sqrt(64))
smoothed.SHARp = smoothed(radius=_base/math.sqrt(32))
smoothed.SHArp = smoothed(radius=_base/math.sqrt(16))
smoothed.SHarp = smoothed(radius=_base/math.sqrt(8))
smoothed.Sharp = smoothed(radius=_base/math.sqrt(4))
smoothed.sharp = smoothed(radius=_base/math.sqrt(2))
smoothed.normal = smoothed(radius=_base)
smoothed.round = smoothed(radius=_base*math.sqrt(2))
smoothed.Round = smoothed(radius=_base*math.sqrt(4))
smoothed.ROund = smoothed(radius=_base*math.sqrt(8))
smoothed.ROUnd = smoothed(radius=_base*math.sqrt(16))
smoothed.ROUNd = smoothed(radius=_base*math.sqrt(32))
smoothed.ROUND = smoothed(radius=_base*math.sqrt(64))

# vim:foldmethod=marker:foldmarker=<<<,>>>
