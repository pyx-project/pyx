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


import sys, math
import attr, base, canvas, color, helper, path, style, trafo, unit

### helpers

def sign0(x):
    return (x > 0) and 1 or (((x == 0) and 1 or 0) - 1)
def sign1(x):
    return (x >= 0) and 1 or -1

def realpolyroots(coeffs, epsilon=1e-5): # {{{
    # use Numeric to find the roots (via an equivalent eigenvalue problem)
    import Numeric, LinearAlgebra

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
# }}}

def curvescontrols_from_endlines_pt(B, tangent1, tangent2, r1, r2, softness): # {{{
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
# }}}

def curveparams_from_endpoints_pt(A, B, tangentA, tangentB, curvA, curvB, obeycurv=0, epsilon=1e-5): # {{{
    # connects points A and B with a bezier curve that has
    # prescribed tangents dirA, dirB and curvatures curA, curB at the end points.
    #
    # The sign of the tangent vectors is _always_ enforced. If the solution goes
    # into the opposite direction, None will be returned.
    #
    # If obeycurv, the sign of the curvature will be enforced which may cause a
    # strange solution to be found (or none at all).

    # normalise the tangent vectors
    # XXX we get numeric instabilities for ||dirA||==||dirB||==1
    #norm = math.hypot(*tangentA)
    #norm = 1
    #dirA = (tangentA[0] / norm, tangentA[1] / norm)
    #norm = math.hypot(*tangentB)
    #norm = 1
    #dirB = (tangentB[0] / norm, tangentB[1] / norm)
    dirA = tangentA
    dirB = tangentB
    # some shortcuts
    T = dirA[0] * dirB[1] - dirA[1] * dirB[0]
    D = 3 * (dirA[0] * (B[1]-A[1]) - dirA[1] * (B[0]-A[0]))
    E = 3 * (dirB[0] * (B[1]-A[1]) - dirB[1] * (B[0]-A[0]))
    # the variables: \dot X(0) = a * dirA
    #                \dot X(1) = b * dirB
    a, b = None, None

    # we may switch the sign of the curvatures if not obeycurv
    # XXX are these formulae correct ??
    # XXX improve the heuristic for choosing the sign of the curvature !!
    if not obeycurv:
        curvA = abs(curvA) * sign1(D)
        curvB = abs(curvB) * sign1(E)

    # ask for some special cases where the equations decouple
    if abs(T) < epsilon*epsilon:
        try:
            a = 2.0 * D / curvA
            a = math.sqrt(abs(a)) * sign1(a)
            b = -2.0 * E / curvB
            b = math.sqrt(abs(b)) * sign1(b)
        except ZeroDivisionError:
            sys.stderr.write("*** PyX Warning: The connecting bezier is not uniquely determined. "
                "The simple heuristic solution may not be optimal.\n")
            a = b = 1.5 * math.hypot(A[0] - B[0], A[1] - B[1])
    else:
        if abs(curvA) < epsilon:
            b = D / T
            a = - (E + b*abs(b)*curvB*0.5) / T
        elif abs(curvB) < epsilon:
            a = -E / T
            b = (D - a*abs(a)*curvA*0.5) / T
        else:
            a, b = None, None

    # else find a solution for the full problem
    if a is None:
        try:
            # we first try to find all the zeros of the polynomials for a or b (4th order)
            # this needs Numeric and LinearAlgebra
            # First try the equation for a
            coeffs = (0.125*curvA*curvA*curvB, 0, -0.5*D*curvA*curvB, T**3,  T*T*E + 0.5*curvB*D*D)
            cands = [cand for cand in realpolyroots(coeffs) if cand > 0]

            if cands:
                a = min(cands)
                b = (D - 0.5*curvA*a*a) / T
            else:
                # then, try the equation for b
                coeffs = (0.125*curvB*curvB*curvA, 0,  0.5*E*curvA*curvB, T**3, -T*T*D + 0.5*curvA*E*E)
                cands = [cand for cand in realpolyroots(coeffs) if cand > 0]
                if cands:
                    b = min(cands)
                    a = - (E + 0.5*curvB*b*b) / T
                else:
                    a = b = None

        except ImportError:
            # if the Numeric modules are not available:
            # solve the coupled system by Newton iteration
            #     0 = Ga(a,b) = 0.5 a |a| curvA + b * T - D
            #     0 = Gb(a,b) = 0.5 b |b| curvB + a * T + E
            # this system is equivalent to the geometric contraints:
            #     the curvature and the normal tangent vectors
            #     at parameters 0 and 1 are to be continuous
            # the system is solved by 2-dim Newton-Iteration
            # (a,b)^{i+1} = (a,b)^i - (DG)^{-1} (Ga(a^i,b^i), Gb(a^i,b^i))
            a = b = 0
            Ga = Gb = 1
            while max(abs(Ga),abs(Gb)) > epsilon:
                detDG = abs(a*b) * curvA*curvB - T*T
                invDG = [[curvB*abs(b)/detDG, -T/detDG], [-T/detDG, curvA*abs(a)/detDG]]

                Ga = a*abs(a)*curvA*0.5 + b*T - D
                Gb = b*abs(b)*curvB*0.5 + a*T + E

                a, b = a - 0.5*invDG[0][0]*Ga - 0.5*invDG[0][1]*Gb, b - 0.5*invDG[1][0]*Ga - 0.5*invDG[1][1]*Gb


    return (abs(a) / 3.0, abs(b) / 3.0)
# }}}

def curvecontrols_from_endpoints_pt(A, B, tangentA, tangentB, curvA, curvB, obeycurv=0, epsilon=1e-5): # {{{
    a, b = curveparams_from_endpoints_pt(A, B, tangentA, tangentB, curvA, curvB, obeycurv=obeycurv, epsilon=epsilon)
    # XXX respect the normalization from curveparams_from_endpoints_pt
    return A, (A[0] + a * tangentA[0], A[1] + a * tangentA[1]), (B[0] - b * tangentB[0], B[1] - b * tangentB[1]), B
# }}}


class deformer:

    def deform (self, basepath):
        return origpath

class cycloid(deformer): # {{{
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
        basepath = path.normpath(abasepath)

        for sp in basepath.subpaths:
            if sp == basepath.subpaths[0]:
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
            sys.stderr.write("*** PyX Warning: subpath is too short for deformation with cycloid -- skipping...\n")
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
            basetrafo = subpath.trafo(param)

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
            pathradius = subpath.curvradius_pt(param)
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
            sys.stderr.write("*** PyX Warning: subpath is too short for deformation with cycloid -- skipping...\n")
            return path.normpath([subpath])

        # Build the path from the pointlist
        # containing (control x 2,  base x 2, control x 2)
        if skipfirst > subpath.epsilon:
            cycloidpath = path.normpath([subpath.split([params[0]])[0]])
            cycloidpath.append(path.curveto_pt(*(points[0][4:6] + points[1][0:4])))
        else:
            cycloidpath = path.normpath([path.normsubpath([path.normcurve(*(points[0][2:6] + points[1][0:4]))], 0)])
        for i in range(1, len(points)-1):
            cycloidpath.append(path.curveto_pt(*(points[i][4:6] + points[i+1][0:4])))
        if skiplast > subpath.epsilon:
            cycloidpath.join(path.normpath([subpath.split([params[-1]])[-1]]))

        # That's it
        return cycloidpath
# }}}

class smoothed(deformer): # {{{

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
        basepath = path.normpath(abasepath)
        smoothpath = path.path()

        for sp in basepath.subpaths:
            smoothpath += self.deformsubpath(sp)

        return smoothpath

    def deformsubpath(self, normsubpath):

        radius = unit.topt(self.radius)

        npitems = normsubpath.normpathitems
        arclens = [npitem.arclen_pt() for npitem in npitems]

        # 1. Build up a list of all relevant normpathitems
        #    and the lengths where they will be cut (length with respect to the normsubpath)
        npitemnumbers = []
        cumalen = 0
        for no in range(len(arclens)):
            alen = arclens[no]
            # a first selection criterion for skipping too short normpathitems
            # the rest will queeze the radius
            if alen > radius:
                npitemnumbers.append(no)
            else:
                sys.stderr.write("*** PyX Warning: smoothed is skipping a normpathitem that is too short\n")
            cumalen += alen
        # XXX: what happens, if 0 or -1 is skipped and path not closed?

        # 2. Find the parameters, points,
        #    and calculate tangents and curvatures
        params, tangents, curvatures, points = [], [], [], []
        for no in npitemnumbers:
            npitem = npitems[no]
            alen = arclens[no]

            # find the parameter(s): either one or two
            if no is npitemnumbers[0] and not normsubpath.closed:
                pars = npitem._arclentoparam_pt([max(0, alen - radius)])[0]
            elif alen > 2 * radius:
                pars = npitem._arclentoparam_pt([radius, alen - radius])[0]
            else:
                pars = npitem._arclentoparam_pt([0.5 * alen])[0]

            # find points, tangents and curvatures
            ts,cs,ps = [],[],[]
            for par in pars:
                # XXX: there is no trafo method for normpathitems?
                thetrafo = normsubpath.trafo(par + no)
                p = thetrafo._apply(0,0)
                # XXX thetrafo._apply(1,0) causes numeric instabilities in
                # bezier_by_endpoints
                t = thetrafo._apply(100,0)
                ps.append(p)
                ts.append((t[0]-p[0], t[1]-p[1]))
                c = npitem.curvradius_pt(par)
                if c is None: cs.append(0)
                else: cs.append(1.0/c)

            params.append(pars)
            points.append(ps)
            tangents.append(ts)
            curvatures.append(cs)

        # create empty path to collect pathitems
        # this will be returned as normpath, later
        smoothpath = path.path()
        do_moveto = 1 # we do not know yet where to moveto
        # 3. First part of extra handling of closed paths
        if not normsubpath.closed:
            bpart = npitems[npitemnumbers[0]].split(params[0])[0]
            if do_moveto:
                smoothpath.append(path.moveto_pt(*bpart.begin_pt()))
                do_moveto = 0
            if isinstance(bpart, path.normline):
                smoothpath.append(path.lineto_pt(*bpart.end_pt()))
            elif isinstance(bpart, path.normcurve):
                smoothpath.append(path.curveto_pt(bpart.x1_pt, bpart.y1_pt, bpart.x2_pt, bpart.y2_pt, bpart.x3_pt, bpart.y3_pt))
            do_moveto = 0

        # 4. Do the splitting for the first to the last element,
        #    a closed path must be closed later
        for i in range(len(npitemnumbers)-1+(normsubpath.closed==1)):
            this = npitemnumbers[i]
            next = npitemnumbers[(i+1) % len(npitemnumbers)]
            thisnpitem, nextnpitem = npitems[this], npitems[next]

            # split thisnpitem apart and take the middle peace
            if len(points[this]) == 2:
                mpart = thisnpitem.split(params[this])[1]
                if do_moveto:
                    smoothpath.append(path.moveto_pt(*mpart.begin_pt()))
                    do_moveto = 0
                if isinstance(mpart, path.normline):
                    smoothpath.append(path.lineto_pt(*mpart.end_pt()))
                elif isinstance(mpart, path.normcurve):
                    smoothpath.append(path.curveto_pt(mpart.x1_pt, mpart.y1_pt, mpart.x2_pt, mpart.y2_pt, mpart.x3_pt, mpart.y3_pt))

            # add the curve(s) replacing the corner
            if isinstance(thisnpitem, path.normline) and isinstance(nextnpitem, path.normline) \
               and (next-this == 1 or (this==0 and next==len(npitems)-1)):
                d1,g1,f1,e,f2,g2,d2 = curvescontrols_from_endlines_pt(
                    thisnpitem.end_pt(), tangents[this][-1], tangents[next][0],
                    math.hypot(points[this][-1][0] - thisnpitem.end_pt()[0], points[this][-1][1] - thisnpitem.end_pt()[1]),
                    math.hypot(points[next][0][0] - nextnpitem.begin_pt()[0], points[next][0][1] - nextnpitem.begin_pt()[1]),
                    softness=self.softness)
                if do_moveto:
                    smoothpath.append(path.moveto_pt(*d1))
                    do_moveto = 0
                smoothpath.append(path.curveto_pt(*(g1 + f1 + e)))
                smoothpath.append(path.curveto_pt(*(f2 + g2 + d2)))
                #for X in [d1,g1,f1,e,f2,g2,d2]:
                #    dp.subcanvas.fill(path.circle_pt(X[0], X[1], 1.0))
            else:
                A,B,C,D = curvecontrols_from_endpoints_pt(
                    points[this][-1], points[next][0],
                    tangents[this][-1], tangents[next][0],
                    curvatures[this][-1], curvatures[next][0],
                    obeycurv=self.obeycurv, epsilon=normsubpath.epsilon)
                if do_moveto:
                    smoothpath.append(path.moveto_pt(*A))
                    do_moveto = 0
                smoothpath.append(path.curveto_pt(*(B + C + D)))
                #for X in [A,B,C,D]:
                #    dp.subcanvas.fill(path.circle_pt(X[0], X[1], 1.0))

        # 5. Second part of extra handling of closed paths
        if normsubpath.closed:
            if do_moveto:
                smoothpath.append(path.moveto_pt(*dp.strokepath.begin()))
                sys.stderr.write("*** PyXWarning: The whole subpath has been smoothed away -- sorry\n")
            smoothpath.append(path.closepath())
        else:
            epart = npitems[npitemnumbers[-1]].split([params[-1][0]])[-1]
            if do_moveto:
                smoothpath.append(path.moveto_pt(*epart.begin_pt()))
                do_moveto = 0
            if isinstance(epart, path.normline):
                smoothpath.append(path.lineto_pt(*epart.end_pt()))
            elif isinstance(epart, path.normcurve):
                smoothpath.append(path.curveto_pt(epart.x1_pt, epart.y1_pt, epart.x2_pt, epart.y2_pt, epart.x3_pt, epart.y3_pt))

        return smoothpath
# }}}

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


