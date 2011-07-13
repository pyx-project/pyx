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

from math import atan2, radians
from pyx import path as pathmodule
from pyx import unit

from mp_path import mp_endpoint, mp_explicit, mp_given, mp_curl, mp_open, mp_end_cycle, mp_make_choices

################################################################################
# Path knots
################################################################################

class knot_pt:

    """Internal knot as used in MetaPost (mp.c)"""

    def __init__(self, x_pt, y_pt, ltype, lx_pt, ly_pt, rtype, rx_pt, ry_pt):
        self.x_pt = x_pt
        self.y_pt = y_pt
        self.ltype = ltype
        self.lx_pt = lx_pt
        self.ly_pt = ly_pt
        self.rtype = rtype
        self.rx_pt = rx_pt
        self.ry_pt = ry_pt
        # this is a linked list:
        self.next = self

    def set_left_tension(self, tens):
        self.ly_pt = tens
    def set_right_tension(self, tens):
        self.ry_pt = tens
    def set_left_curl(self, curl):
        self.lx_pt = curl
    def set_right_curl(self, curl):
        self.rx_pt = curl
    set_left_given = set_left_curl
    set_right_given = set_right_curl

    def left_tension(self):
        return self.ly_pt
    def right_tension(self):
        return self.ry_pt
    def left_curl(self):
        return self.lx_pt
    def right_curl(self):
        return self.rx_pt
    left_given = left_curl
    right_given = right_curl

    def linked_len(self):
        """returns the length of a circularly linked list of knots"""
        n = 1
        p = self.next
        while not p is self:
            n += 1
            p = p.next
        return n

    def __repr__(self):
        result = ""
        # left
        if self.ltype == mp_endpoint:
            pass
        elif self.ltype == mp_explicit:
            result += "{explicit %s %s}" % (self.lx_pt, self.ly_pt)
        elif self.ltype == mp_given:
            result += "{given %g tens %g}" % (self.lx_pt, self.ly_pt)
        elif self.ltype == mp_curl:
            result += "{curl %g tens %g}" % (self.lx_pt, self.ly_pt)
        elif self.ltype == mp_open:
            result += "{open tens %g}" % (self.ly_pt)
        elif self.ltype == mp_end_cycle:
            result += "{cycle tens %g}" % (self.ly_pt)
        result += "(%g %g)" % (self.x_pt, self.y_pt)
        # right
        if self.rtype == mp_endpoint:
            pass
        elif self.rtype == mp_explicit:
            result += "{explicit %g %g}" % (self.rx_pt, self.ry_pt)
        elif self.rtype == mp_given:
            result += "{given %g tens %g}" % (self.rx_pt, self.ry_pt)
        elif self.rtype == mp_curl:
            result += "{curl %g tens %g}" % (self.rx_pt, self.ry_pt)
        elif self.rtype == mp_open:
            result += "{open tens %g}" % (self.ry_pt)
        elif self.rtype == mp_end_cycle:
            result += "{cycle tens %g}" % (self.ry_pt)
        return result

class beginknot(knot_pt):

    """A knot which interrupts a path, or which allows to continue it with a straight line"""

    def __init__(self, x, y, curl=1, angle=None):
        if angle is None:
            type, value = mp_curl, curl
        else:
            type, value = mp_given, radians(angle)
        # tensions are modified by the adjacent curve, but default is 1
        knot_pt.__init__(self, unit.topt(x), unit.topt(y), mp_endpoint, None, None, type, value, 1)

startknot = beginknot

class endknot(knot_pt):

    """A knot which interrupts a path, or which allows to continue it with a straight line"""

    def __init__(self, x, y, curl=1, angle=None):
        if angle is None:
            type, value = mp_curl, curl
        else:
            type, value = mp_given, radians(angle)
        # tensions are modified by the adjacent curve, but default is 1
        knot_pt.__init__(self, unit.topt(x), unit.topt(y), type, value, 1, mp_endpoint, None, None)

class smoothknot(knot_pt):

    """A knot with continous tangent and "mock" curvature."""

    def __init__(self, x, y):
        # tensions are modified by the adjacent curve, but default is 1
        knot_pt.__init__(self, unit.topt(x), unit.topt(y), mp_open, None, 1, mp_open, None, 1)

knot = smoothknot

class roughknot(knot_pt):

    """A knot with noncontinous tangent."""

    def __init__(self, x, y, lcurl=1, rcurl=None, langle=None, rangle=None):
        """Specify either the relative curvatures, or tangent angles left (l)
        or right (r) of the point."""
        if langle is None:
            ltype, lvalue = mp_curl, lcurl
        else:
            ltype, lvalue = mp_given, radians(langle)
        if rcurl is not None:
            rtype, rvalue = mp_curl, rcurl
        elif rangle is not None:
            rtype, rvalue = mp_given, radians(rangle)
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
        left_knot.rtype = mp_endpoint
        right_knot.ltype = mp_endpoint
        left_knot.rx_pt, left_knot.ry_pt = None, None
        right_knot.lx_pt, right_knot.ly_pt = None, None
        if self.keepangles:
            angle = atan2(right_knot.y_pt-left_knot.y_pt, right_knot.x_pt-left_knot.x_pt)
            left_knot.ltype = mp_given
            left_knot.set_left_given(angle)
            right_knot.rtype = mp_given
            right_knot.set_right_given(angle)


class controlcurve_pt(link):

    """A cubic Bezier curve which has its control points explicity set"""

    def __init__(self, lcontrol_pt, rcontrol_pt):
        """The control points at the beginning (l) and the end (r) must be
        coordinate pairs"""
        self.lcontrol_pt = lcontrol_pt
        self.rcontrol_pt = rcontrol_pt

    def set_knots(self, left_knot, right_knot):
        left_knot.rtype = mp_explicit
        right_knot.ltype = mp_explicit
        left_knot.rx_pt, left_knot.ry_pt = self.lcontrol_pt
        right_knot.lx_pt, right_knot.ly_pt = self.rcontrol_pt


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
        if left_knot.rtype <= mp_explicit or right_knot.ltype <= mp_explicit:
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
                if elem.ltype is mp_endpoint or elem.rtype is mp_endpoint:
                    is_closed = False

        # link the knots among each other
        for i in range(len(knots)):
            knots[i-1].next = knots[i]

        # determine the control points
        mp_make_choices(knots[0])

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
                    self.append(pathmodule.moveto_pt(elem.x_pt, elem.y_pt))
                if do_lineto:
                    self.append(pathmodule.lineto_pt(elem.x_pt, elem.y_pt))
                elif do_curveto:
                    self.append(pathmodule.curveto_pt(prev.rx_pt, prev.ry_pt, elem.lx_pt, elem.ly_pt, elem.x_pt, elem.y_pt))
                do_moveto = True
                do_lineto = False
                do_curveto = False
                prev = elem

        # close the path if necessary
        if knots[0].ltype is mp_explicit:
            elem = knots[0]
            if do_lineto and is_closed:
                self.append(pathmodule.closepath())
            elif do_curveto:
                self.append(pathmodule.curveto_pt(prev.rx_pt, prev.ry_pt, elem.lx_pt, elem.ly_pt, elem.x_pt, elem.y_pt))
                if is_closed:
                    self.append(pathmodule.closepath())

