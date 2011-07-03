# -*- coding: ISO-8859-1 -*-
#
# Copyright (C) 2011 Michael Schindler <m-schindler@users.sourceforge.net>
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

from math import atan2, sin, cos, sqrt, pi, radians
import path as pathmodule
import unit

################################################################################
# Path knots
################################################################################

class knot_pt:

    """Internal knot as used in MetaPost (mp.c)"""

    def __init__(self, x, y, ltype, lx, ly, rtype, rx, ry):
        self.x = x
        self.y = y
        self.ltype = ltype
        self.lx = lx
        self.ly = ly
        self.rtype = rtype
        self.rx = rx
        self.ry = ry
        # this is a linked list:
        self.next = None

    def set_left_tension(self, tens):
        self.ly = tens
    def set_right_tension(self, tens):
        self.ry = tens
    def set_left_curl(self, curl):
        self.lx = curl
    def set_right_curl(self, curl):
        self.rx = curl
    set_left_given = set_left_curl
    set_right_given = set_right_curl

    def left_tension(self):
        return self.ly
    def right_tension(self):
        return self.ry
    def left_curl(self):
        return self.lx
    def right_curl(self):
        return self.rx
    left_given = left_curl
    right_given = right_curl

    def __repr__(self):
        result = ""
        # left
        if self.ltype == _mp_endpoint:
            pass
        elif self.ltype == _mp_explicit:
            result += "{explicit %s %s}" % (self.lx, self.ly)
        elif self.ltype == _mp_given:
            result += "{given %g tens %g}" % (self.lx, self.ly)
        elif self.ltype == _mp_curl:
            result += "{curl %g tens %g}" % (self.lx, self.ly)
        elif self.ltype == _mp_open:
            result += "{open tens %g}" % (self.ly)
        elif self.ltype == _mp_end_cycle:
            result += "{cycle tens %g}" % (self.ly)
        result += "(%g %g)" % (self.x, self.y)
        # right
        if self.rtype == _mp_endpoint:
            pass
        elif self.rtype == _mp_explicit:
            result += "{explicit %g %g}" % (self.rx, self.ry)
        elif self.rtype == _mp_given:
            result += "{given %g tens %g}" % (self.rx, self.ry)
        elif self.rtype == _mp_curl:
            result += "{curl %g tens %g}" % (self.rx, self.ry)
        elif self.rtype == _mp_open:
            result += "{open tens %g}" % (self.ry)
        elif self.rtype == _mp_end_cycle:
            result += "{cycle tens %g}" % (self.ry)
        return result

def _knot_len(knots):
    """returns the length of a circularly linked list of knots"""
    n = 1
    p = knots.next
    while not p is knots:
        n += 1
        p = p.next
    return n

class beginknot(knot_pt):

    """A knot which interrupts a path, or which allows to continue it with a straight line"""

    def __init__(self, x, y, curl=1, angle=None):
        if angle is None:
            type, value = _mp_curl, curl
        else:
            type, value = _mp_given, radians(angle)
        # tensions are modified by the adjacent curve, but default is 1
        knot_pt.__init__(self, unit.topt(x), unit.topt(y), _mp_endpoint, None, None, type, value, 1)

startknot = beginknot

class endknot(knot_pt):

    """A knot which interrupts a path, or which allows to continue it with a straight line"""

    def __init__(self, x, y, curl=1, angle=None):
        if angle is None:
            type, value = _mp_curl, curl
        else:
            type, value = _mp_given, radians(angle)
        # tensions are modified by the adjacent curve, but default is 1
        knot_pt.__init__(self, unit.topt(x), unit.topt(y), type, value, 1, _mp_endpoint, None, None)

class smoothknot(knot_pt):

    """A knot with continous tangent and "mock" curvature."""

    def __init__(self, x, y):
        # tensions are modified by the adjacent curve, but default is 1
        knot_pt.__init__(self, unit.topt(x), unit.topt(y), _mp_open, None, 1, _mp_open, None, 1)

knot = smoothknot

class roughknot(knot_pt):

    """A knot with noncontinous tangent."""

    def __init__(self, x, y, left_curl=1, right_curl=None, left_angle=None, right_angle=None):
        """Specify either the relative curvatures, or tangent angles at the
        beginning (left) point or the end (right) point."""
        if left_angle is None:
            ltype, lvalue = _mp_curl, left_curl
        else:
            ltype, lvalue = _mp_given, radians(left_angle)
        if right_curl is not None:
            rtype, rvalue = _mp_curl, right_curl
        elif right_angle is not None:
            rtype, rvalue = _mp_given, radians(right_angle)
        else:
            rtype, rvalue = ltype, lvalue
        # tensions are modified by the adjacent curve, but default is 1
        knot_pt.__init__(self, unit.topt(x), unit.topt(y), ltype, lvalue, 1, rtype, rvalue, 1)

################################################################################
# Path links
################################################################################

class link:
    def set_knots(self, left_knot, right_knot):
        """Sets the internal properties of the metapost knots"""
        pass

class line(link):

    """A straight line"""

    def __init__(self, keepangles=False):
        """The option keepangles will guarantee a continuous tangent. The
        curvature may become discontinuous, however"""
        self.keepangles = keepangles

    def set_knots(self, left_knot, right_knot):
        left_knot.rtype = _mp_endpoint
        right_knot.ltype = _mp_endpoint
        left_knot.rx, left_knot.ry = None, None
        right_knot.lx, right_knot.ly = None, None
        if self.keepangles:
            angle = atan2(right_knot.y-left_knot.y, right_knot.x-left_knot.x)
            if left_knot.ltype is _mp_open:
                left_knot.ltype = _mp_given
                left_knot.set_left_given(angle)
            if right_knot.ltype is _mp_open:
                right_knot.ltype = _mp_given
                right_knot.set_right_given(angle)


class controlcurve_pt(link):

    """A cubic Bezier curve which has its control points explicity set"""

    def __init__(self, lcontrol_pt, rcontrol_pt):
        """The control points at the beginning (l) and the end (r) must be
        coordinate pairs"""
        self.lcontrol_pt = lcontrol_pt
        self.rcontrol_pt = rcontrol_pt

    def set_knots(self, left_knot, right_knot):
        left_knot.rtype = _mp_explicit
        right_knot.ltype = _mp_explicit
        left_knot.rx, left_knot.ry = self.lcontrol_pt
        right_knot.lx, right_knot.ly = self.rcontrol_pt


class tensioncurve(link):

    """A yet unspecified cubic Bezier curve"""

    def __init__(self, ltension=1, latleast=False, rtension=None, ratleast=None):
        """The tension parameters indicate the tensions at the beginning (l)
        and the end (r) of the curve. Set the parameters (l/r)atleast to True
        if you want to avoid inflection points."""
        if rtension is None:
            rtension = ltension
        if ratleast is None:
            ratleast = latleast
        # make sure that tension >= 0.75 (p. 9 mpman.pdf)
        self.ltension = max(0.75, abs(ltension))
        self.rtension = max(0.75, abs(rtension))
        if latleast:
            self.ltension = -self.ltension
        if ratleast:
            self.rtension = -self.rtension

    def set_knots(self, left_knot, right_knot):
        if left_knot.rtype <= _mp_explicit or right_knot.ltype <= _mp_explicit:
            raise Exception("metapost curve with given tension cannot have explicit knots")
        left_knot.set_right_tension(self.ltension)
        right_knot.set_left_tension(self.rtension)

curve = tensioncurve


class controlcurve(controlcurve_pt):

    def __init__(self, lcontrol, rcontrol):
        controlcurve_pt.__init__(self, (unit.topt(lcontrol[0]), unit.topt(lcontrol[1])),
                                       (unit.topt(rcontrol[0]), unit.topt(rcontrol[1])))

################################################################################
# Path creation class
################################################################################

class path(pathmodule.path):

    """A MetaPost-like path, which finds an optimal way through given points.

    At points, you can either specify a given tangent direction (angle in
    degrees) or a certain "curlyness" (relative to the curvature at the other
    end of a curve), or nothing. In the latter case, both the tangent and the
    "mock" curvature (an approximation to the real curvature, introduced by
    J.D. Hobby in MetaPost) will be continuous.

    The shape of the cubic Bezier curves between two points is controlled by
    its "tension", unless you choose to set the control points manually."""

    def __init__(self, *elems):
        """elems should contain metapost knots or links"""
        knots = []
        is_closed = True
        for i, elem in enumerate(elems):
            if isinstance(elem, link):
                elem.set_knots(elems[i-1], elems[(i+1)%len(elems)])
            elif isinstance(elem, knot_pt):
                knots.append(elem)
                if elem.ltype is _mp_endpoint or elem.rtype is _mp_endpoint:
                    is_closed = False

        # link the knots among each other
        for i in range(len(knots)):
            knots[i-1].next = knots[i]

        # determine the control points
        _mp_make_choices(knots[0])

        pathmodule.path.__init__(self)
        # build up the path
        do_moveto = True
        do_lineto = False
        do_curveto = False
        prev = None
        for i, elem in enumerate(elems):
            if isinstance(elem, link):
                do_moveto = False
                if isinstance(elem, line):
                    do_lineto, do_curveto = True, False
                else:
                    do_lineto, do_curveto = False, True
            elif isinstance(elem, knot_pt):
                if do_moveto:
                    self.append(pathmodule.moveto_pt(elem.x, elem.y))
                if do_lineto:
                    self.append(pathmodule.lineto_pt(elem.x, elem.y))
                elif do_curveto:
                    self.append(pathmodule.curveto_pt(prev.rx, prev.ry, elem.lx, elem.ly, elem.x, elem.y))
                do_moveto = True
                do_lineto = False
                do_curveto = False
                prev = elem

        # close the path if necessary
        if knots[0].ltype is _mp_explicit:
            elem = knots[0]
            if do_lineto and is_closed:
                self.append(pathmodule.closepath())
            elif do_curveto:
                self.append(pathmodule.curveto_pt(prev.rx, prev.ry, elem.lx, elem.ly, elem.x, elem.y))
                if is_closed:
                    self.append(pathmodule.closepath())


################################################################################
# Internal functions of MetaPost
#
# The remainder of this file re-implements some of the functionality of
# MetaPost (http://tug.org/metapost). MetaPost was developed by John D. Hobby
# and others.
#
# This file is based on the MetaPost version distributed by TeXLive:
# svn://tug.org/texlive/trunk/Build/source/texk/web2c/mplibdir
# revision 22737 (2011-05-31)
################################################################################

# from mplib.h:
_mp_endpoint = 0
_mp_explicit = 1
_mp_given = 2
_mp_curl = 3
_mp_open = 4
_mp_end_cycle = 5

# from mpmath.c:
_unity = 1.0
_two = 2.0
_fraction_half = 0.5
_fraction_one = 1.0
_fraction_three = 3.0
_one_eighty_deg = pi
_three_sixty_deg = 2*pi

def _mp_make_choices(knots): # <<<
    """Implements mp_make_choices from metapost (mp.c)"""
    # 334: If consecutive knots are equal, join them explicitly
    p = knots
    while True:
        q = p.next
        # XXX float comparison: use epsilon
        if p.x == q.x and p.y == q.y and p.rtype > _mp_explicit:
            p.rtype = _mp_explicit
            if p.ltype == _mp_open:
                p.ltype = _mp_curl
                p.set_left_curl(_unity)
            q.ltype = _mp_explicit
            if q.rtype == _mp_open:
                q.rtype = _mp_curl
                q.set_right_curl(_unity)
            p.rx = p.x
            q.lx = p.x
            p.ry = p.y
            q.ly = p.y
        p = q
        if p is knots:
            break

    # 335:
    # If there are no breakpoints, it is necessary to compute the direction angles around an entire cycle.
    # In this case the mp left type of the first node is temporarily changed to end cycle.
    # Find the first breakpoint, h, on the path
    # insert an artificial breakpoint if the path is an unbroken cycle
    h = knots
    while True:
        if h.ltype != _mp_open or h.rtype != _mp_open:
            break
        h = h.next
        if h is knots:
            h.ltype = _mp_end_cycle
            break

    p = h
    while True:
        # 336:
        # Fill in the control points between p and the next breakpoint, then advance p to that breakpoint
        q = p.next
        if p.rtype >= _mp_given:
            while q.ltype == _mp_open and q.rtype == _mp_open:
                q = q.next

            # 346:
            # Calculate the turning angles psi_k and the distances d(k, k+1)
            # set n to the length of the path
            k = 0
            s = p
            n = _knot_len(knots)
            delta_x, delta_y, delta, psi = [], [], [], [None]
            while True:
                t = s.next
                assert len(delta_x) == k
                delta_x.append(t.x - s.x)
                delta_y.append(t.y - s.y)
                delta.append(_mp_pyth_add(delta_x[k], delta_y[k]))
                if k > 0:
                    sine = _mp_make_fraction(delta_y[k-1], delta[k-1])
                    cosine = _mp_make_fraction(delta_x[k-1], delta[k-1])
                    psi.append(_mp_n_arg(
                      _mp_take_fraction(delta_x[k], cosine) + _mp_take_fraction(delta_y[k], sine),
                      _mp_take_fraction(delta_y[k], cosine) - _mp_take_fraction(delta_x[k], sine)))
                k += 1
                s = t
                if s == q:
                    n = k
                if k >= n and s.ltype != _mp_end_cycle:
                    break
            if k == n:
                psi.append(0)
            else:
                # for closed paths:
                psi.append(psi[1])

            # 347: Remove open types at the breakpoints
            if q.ltype == _mp_open:
                delx = q.rx - q.x
                dely = q.ry - q.y
                if delx == 0 and dely == 0: # XXX float comparison
                    q.ltype = _mp_curl
                    q.set_left_curl(_unity)
                else:
                    q.ltype = _mp_given
                    q.set_left_given(_mp_n_arg(delx, dely))

            if p.rtype == _mp_open and p.ltype == _mp_explicit:
                delx = p.x - p.lx
                dely = p.y - p.ly
                if delx == 0 and dely == 0: # XXX float comparison
                    p.rtype = _mp_curl
                    p.set_right_curl(_unity)
                else:
                    p.rtype = _mp_given
                    p.set_right_given(_mp_n_arg(delx, dely))

            # call the internal solving routine
            _mp_solve_choices(p, q, n, delta_x, delta_y, delta, psi)

        elif p.rtype == _mp_endpoint:
            # 337: Give reasonable values for the unused control points between p and q
            p.rx = p.x
            p.ry = p.y
            q.lx = q.x
            q.ly = q.y

        p = q
        if p is h:
            break
# >>>
def _mp_solve_choices(p, q, n, delta_x, delta_y, delta, psi): # <<<
    """Implements mp_solve_choices form metapost (mp.c)"""
    uu = [None]*(len(delta)+1)
    vv = [None]*len(uu) # angles
    ww = [None]*len(uu)
    theta = [None]*len(uu)
    # k current knot number
    # r, s, t registers for list traversal
    k = 0
    s = p
    r = 0
    while True:
        t = s.next
        if k == 0: # <<<
            # 354:
            # Get the linear equations started
            # or return with the control points in place, if linear equations needn't be solved

            if s.rtype == _mp_given: # <<<
                if t.ltype == _mp_given:
                    # 372: Reduce to simple case of two givens and return
                    aa = _mp_n_arg(delta_x[0], delta_y[0])
                    ct, st = _mp_n_sin_cos(p.right_given() - aa)
                    cf, sf = _mp_n_sin_cos(q.left_given() - aa)
                    _mp_set_controls(p, q, delta_x[0], delta_y[0], st, ct, -sf, cf)
                    return
                else:
                    # 362:
                    vv[0] = s.right_given() - _mp_n_arg(delta_x[0], delta_y[0])
                    vv[0] = _reduce_angle(vv[0])
                    uu[0] = 0
                    ww[0] = 0
            # >>>
            elif s.rtype == _mp_curl: # <<<
                if t.ltype == _mp_curl:
                    # 373: (mp.pdf) Reduce to simple case of straight line and return
                    p.rtype = _mp_explicit
                    q.ltype = _mp_explicit
                    lt = abs(q.left_tension())
                    rt = abs(p.right_tension())
                    if rt == _unity:
                        if delta_x[0] >= 0:
                            p.rx = p.x + delta_x[0]/3.0
                        else:
                            p.rx = p.x + delta_x[0]/3.0
                        if delta_y[0] >= 0:
                            p.ry = p.y + delta_y[0]/3.0
                        else:
                            p.ry = p.y + delta_y[0]/3.0
                    else:
                        ff = _mp_make_fraction(_unity, 3.0*rt)
                        p.rx = p.x + _mp_take_fraction(delta_x[0], ff)
                        p.ry = p.y + _mp_take_fraction(delta_y[0], ff)

                    if lt == _unity:
                        if delta_x[0] >= 0:
                            q.lx = q.x - delta_x[0]/3.0
                        else:
                            q.lx = q.x - delta_x[0]/3.0
                        if delta_y[0] >= 0:
                            q.ly = q.y - delta_y[0]/3.0
                        else:
                            q.ly = q.y - delta_y[0]/3.0
                    else:
                        ff = _mp_make_fraction(_unity, 3.0*lt)
                        q.lx = q.x - _mp_take_fraction(delta_x[0], ff)
                        q.ly = q.y - _mp_take_fraction(delta_y[0], ff)
                    return

                else: # t.ltype != _mp_curl
                    # 363:
                    cc = s.right_curl()
                    lt = abs(t.left_tension())
                    rt = abs(s.right_tension())
                    if rt == _unity and lt == _unity: # XXX float comparison
                        uu[0] = _mp_make_fraction(cc + cc + _unity, cc + _two)
                    else:
                        uu[0] = _mp_curl_ratio(cc, rt, lt)
                    vv[0] = -_mp_take_fraction(psi[1], uu[0])
                    ww[0] = 0
            # >>>
            elif s.rtype == _mp_open: # <<<
                uu[0] = 0
                vv[0] = 0
                ww[0] = _fraction_one
            # >>>
        # end of 354 >>>
        else: # k > 0 <<<

            if s.ltype == _mp_end_cycle or s.ltype == _mp_open: # <<<
                # 356: Set up equation to match mock curvatures at z_k;
                #      then finish loop with theta_n adjusted to equal theta_0, if a
                #      cycle has ended

                # 357: Calculate the values
                #      aa = Ak/Bk, bb = Dk/Ck, dd = (3-alpha_{k-1})d(k,k+1),
                #      ee = (3-beta_{k+1})d(k-1,k), cc=(Bk-uk-Ak)/Bk
                if abs(r.right_tension()) == _unity: # XXX float comparison
                    aa = _fraction_half
                    dd = 2*delta[k]
                else:
                    aa = _mp_make_fraction(_unity, 3*abs(r.right_tension()) - _unity)
                    dd = _mp_take_fraction(delta[k],
                                          _fraction_three - _mp_make_fraction(_unity, abs(r.right_tension())))
                if abs(t.left_tension()) == _unity: # XXX float comparison
                    bb = _fraction_half
                    ee = 2*delta[k-1]
                else:
                    bb = _mp_make_fraction(_unity, 3*abs(t.left_tension()) - _unity)
                    ee = _mp_take_fraction(delta[k-1],
                                          _fraction_three - _mp_make_fraction(_unity, abs(t.left_tension())))
                cc = _fraction_one - _mp_take_fraction(uu[k-1], aa)

                # 358: Calculate the ratio ff = Ck/(Ck + Bk - uk-1Ak)
                dd = _mp_take_fraction(dd, cc)
                lt = abs(s.left_tension())
                rt = abs(s.right_tension())
                if lt != rt:
                    if lt < rt:
                        ff = _mp_make_fraction(lt, rt)
                        ff = _mp_take_fraction(ff, ff)
                        dd = _mp_take_fraction(dd, ff)
                    else:
                        ff = _mp_make_fraction(rt, lt)
                        ff = _mp_take_fraction(ff, ff)
                        ee = _mp_take_fraction(ee, ff)
                ff = _mp_make_fraction(ee, ee + dd)

                uu[k] = _mp_take_fraction(ff, bb)

                # 359: Calculate the values of vk and wk
                acc = -_mp_take_fraction(psi[k+1], uu[k])
                if r.rtype == _mp_curl:
                    ww[k] = 0
                    vv[k] = acc - _mp_take_fraction(psi[1], _fraction_one - ff)
                else:
                    ff = _mp_make_fraction(_fraction_one - ff, cc)
                    acc = acc - _mp_take_fraction(psi[k], ff)
                    ff = _mp_take_fraction(ff, aa)
                    vv[k] = acc - _mp_take_fraction(vv[k-1], ff)
                    if ww[k-1] == 0:
                        ww[k] = 0
                    else:
                        ww[k] = -_mp_take_fraction(ww[k-1], ff)

                if s.ltype == _mp_end_cycle:
                    # 360: Adjust theta_n to equal theta_0 and finish loop

                    aa = 0
                    bb = _fraction_one
                    while True:
                        k -= 1
                        if k == 0:
                            k = n
                        aa = vv[k] - _mp_take_fraction(aa, uu[k])
                        bb = ww[k] - _mp_take_fraction(bb, uu[k])
                        if k == n:
                            break
                    aa = _mp_make_fraction(aa, _fraction_one - bb)
                    theta[n] = aa
                    vv[0] = aa
                    for k in range(1, n):
                        vv[k] = vv[k] + _mp_take_fraction(aa, ww[k])
                    break
            # >>>
            elif s.ltype == _mp_curl: # <<<
                # 364:
                cc = s.left_curl()
                lt = abs(s.left_tension())
                rt = abs(r.right_tension())
                if rt == _unity and lt == _unity:
                    ff = _mp_make_fraction(cc + cc + _unity, cc + _two)
                else:
                    ff = _mp_curl_ratio(cc, lt, rt)
                theta[n] = -_mp_make_fraction(_mp_take_fraction(vv[n-1], ff),
                                             _fraction_one - _mp_take_fraction(ff, uu[n-1]))
                break
            # >>>
            elif s.ltype == _mp_given: # <<<
                # 361:
                theta[n] = s.left_given() - _mp_n_arg(delta_x[n-1], delta_y[n-1])
                theta[n] = _reduce_angle(theta[n])
                break
            # >>>

        # end of k == 0, k != 0 >>>

        r = s
        s = t
        k += 1

    # 367:
    # Finish choosing angles and assigning control points
    for k in range(n-1, -1, -1):
        theta[k] = vv[k] - _mp_take_fraction(theta[k+1], uu[k])
    s = p
    k = 0
    while True:
        t = s.next
        ct, st = _mp_n_sin_cos(theta[k])
        cf, sf = _mp_n_sin_cos(-psi[k+1]-theta[k+1])
        _mp_set_controls(s, t, delta_x[k], delta_y[k], st, ct, sf, cf)
        k += 1
        s = t
        if k == n:
            break
# >>>
def _mp_n_arg(x, y): # <<<
    return atan2(y, x)
# >>>
def _mp_n_sin_cos(z): # <<<
    """Given an integer z that is 2**20 times an angle theta in degrees, the
    purpose of n sin cos(z) is to set x = r cos theta and y = r sin theta
    (approximately), for some rather large number r. The maximum of x and y
    will be between 2**28 and 2**30, so that there will be hardly any loss of
    accuracy. Then x and y are divided by r."""
    # 67: mpmath.pdf
    return cos(z), sin(z)
# >>>
def _mp_set_controls(p, q, delta_x, delta_y, st, ct, sf, cf): # <<<
    """The set controls routine actually puts the control points into a pair of
    consecutive nodes p and q. Global variables are used to record the values
    of sin(theta), cos(theta), sin(phi), and cos(phi) needed in this
    calculation.

    See mp.pdf, item 370"""
    lt = abs(q.left_tension())
    rt = abs(p.right_tension())
    rr = _mp_velocity(st, ct, sf, cf, rt)
    ss = _mp_velocity(sf, cf, st, ct, lt)
    if p.right_tension() < 0 or q.left_tension() < 0:
        # 371: Decrease the velocities, if necessary, to stay inside the bounding triangle
        # this is the only place where the sign of the tension counts
        if (st >= 0 and sf >= 0) or (st <= 0 and sf <= 0):
            sine = _mp_take_fraction(abs(st), cf) + _mp_take_fraction(abs(sf), ct) # sin(theta+phi)
            if sine > 0:
                #sine = _mp_take_fraction(sine, _fraction_one + _unity) # safety factor
                sine *= 1.00024414062 # safety factor
                if p.right_tension() < 0:
                    if _mp_ab_vs_cd(abs(sf), _fraction_one, rr, sine) < 0:
                        rr = _mp_make_fraction(abs(sf), sine)
                if q.left_tension() < 0:
                    if _mp_ab_vs_cd(abs(st), _fraction_one, ss, sine) < 0:
                        ss = _mp_make_fraction(abs(st), sine)

    p.rx = p.x + _mp_take_fraction(_mp_take_fraction(delta_x, ct) - _mp_take_fraction(delta_y, st), rr)
    p.ry = p.y + _mp_take_fraction(_mp_take_fraction(delta_y, ct) + _mp_take_fraction(delta_x, st), rr)
    q.lx = q.x - _mp_take_fraction(_mp_take_fraction(delta_x, cf) + _mp_take_fraction(delta_y, sf), ss)
    q.ly = q.y - _mp_take_fraction(_mp_take_fraction(delta_y, cf) - _mp_take_fraction(delta_x, sf), ss)
    p.rtype = _mp_explicit
    q.ltype = _mp_explicit
# >>>
def _mp_make_fraction(p, q): # <<<
    # 17: mpmath.pdf
    """The make fraction routine produces the fraction equivalent of p/q, given
    integers p and q; it computes the integer f = floor(2**28 p/q + 1/2), when
    p and q are positive.

    In machine language this would simply be (2**28*p)div q"""
    return p/q
# >>>
def _mp_take_fraction(q, f): # <<<
    # 20: mpmath.pdf
    """The dual of make fraction is take fraction, which multiplies a given
    integer q by a fraction f. When the operands are positive, it computes
    p = floor(q*f/2**28 + 1/2), a symmetric function of q and f."""
    return q*f
# >>>
def _mp_pyth_add(a, b): # <<<
    # 44: mpmath.pdf
    """Pythagorean addition sqrt(a**2 + b**2) is implemented by an elegant
    iterative scheme due to Cleve Moler and Donald Morrison [IBM Journal of
    Research and Development 27 (1983), 577-581]. It modifies a and b in such a
    way that their Pythagorean sum remains invariant, while the smaller
    argument decreases."""
    return sqrt(a*a + b*b)
# >>>
def _mp_curl_ratio(gamma, a_tension, b_tension): # <<<
    """The curl ratio subroutine has three arguments, which our previous
    notation encourages us to call gamma, 1/alpha, and 1/beta. It is a somewhat
    tedious program to calculate
      [(3-alpha)alpha^2 gamma + beta^3] / [alpha^3 gamma + (3-beta)beta^2],
    with the result reduced to 4 if it exceeds 4. (This reduction of curl is
    necessary only if the curl and tension are both large.) The values of alpha
    and beta will be at most 4/3.

    See mp.pdf (items 365, 366)."""
    alpha = 1.0/a_tension
    beta = 1.0/b_tension
    return min(4.0, ((3.0-alpha)*alpha**2*gamma + beta**3) /
                    (alpha**3*gamma + (3.0-beta)*beta**2))
# >>>
def _mp_ab_vs_cd(a, b, c, d): # <<<
    """Tests rigorously if ab is greater than, equal to, or less than cd, given
    integers (a, b, c, d). In most cases a quick decision is reached. The
    result is +1, 0, or -1 in the three respective cases.
    See mpmath.pdf (item 33)."""
    if a*b == c*d:
        return 0
    if a*b > c*d:
        return 1
    return -1
# >>>
def _mp_velocity(st, ct, sf, cf, t): # <<<
    """Metapost's standard velocity subroutine for cubic Bezier curves.
    See mpmath.pdf (item 30) and mp.pdf (item 339)."""
    return min(4.0, (2.0 + sqrt(2)*(st-sf/16.0)*(sf-st/16.0)*(ct-cf)) /
                    (1.5*t*(2+(sqrt(5)-1)*ct + (3-sqrt(5))*cf)))
# >>>
def _reduce_angle(A): # <<<
    """A macro in mp.c"""
    if abs(A) > _one_eighty_deg:
        if A > 0:
            A -= _three_sixty_deg
        else:
            A += _three_sixty_deg
    return A
# >>>

# vim:foldmethod=marker:foldmarker=<<<,>>>
