#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2005 Michael Schindler <m-schindler@users.sourceforge.net>
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


import sys; sys.path.insert(0, "../..")
import math
from pyx import *

#
# contains some nice curly braces
# This code is experimental because it is unclear
# how the brace fits into the concepts of PyX
#
# Some thoughts:
#
# - a brace needs to be decoratable with text
#   it needs stroking and filling attributes
#
# - the brace is not really a box:
#   it has two "anchor" points that are important for aligning it to other things
#   and one "anchor" point (plus direction) for aligning other things
#
# - a brace is not a deformer:
#   it does not look at anything else than begin/endpoint of a path
#
# - a brace might be a connector (which is to be dissolved into the box concept later?)
#

def unit_hypot(l1, l2):
    result = unit.length()
    l1 = unit.length(l1)
    l2 = unit.length(l2)
    result.t = math.hypot(l1.t, l2.t)
    result.u = math.hypot(l1.u, l2.u)
    result.v = math.hypot(l1.v, l2.v)
    result.w = math.hypot(l1.w, l2.w)
    result.x = math.hypot(l1.x, l2.x)
    return result


def straightbrace(x0, x1, y0, y1,
    totalheight=None,
    barthickness=None, innerstrokesthickness=None, outerstrokesthickness=None,
    innerstrokesangle=30, outerstrokesangle=30, slantstrokesangle=0,
    innerstrokessmoothness=1.0, outerstrokessmoothness=1.0,
    middlerelpos=0.5):

    """a straight curly brace (differs from the original brace only via its default parameters)"""

    return brace(x0, x1, y0, y1,
    totalheight=totalheight,
    barthickness=barthickness,
    innerstrokesthickness=innerstrokesthickness,
    outerstrokesthickness=outerstrokesthickness,
    innerstrokesrelheight=0.5, # this makes the brace straight
    outerstrokesrelheight=0.5, # this makes the brace straight
    innerstrokesangle=innerstrokesangle,
    outerstrokesangle=outerstrokesangle,
    slantstrokesangle=slantstrokesangle,
    innerstrokessmoothness=innerstrokessmoothness,
    outerstrokessmoothness=outerstrokessmoothness,
    middlerelpos=middlerelpos)


class brace:

    def __init__(self, x0, y0, x1, y1,
    totalheight=None,
    barthickness=None, innerstrokesthickness=None, outerstrokesthickness=None,
    innerstrokesrelheight=0.55, outerstrokesrelheight=0.60,
    innerstrokesangle=30, outerstrokesangle=25, slantstrokesangle=5,
    innerstrokessmoothness=2.0, outerstrokessmoothness=2.5,
    middlerelpos=0.5):

        r"""creates a curly brace

                  inner/\strokes
          ____________/  \__________
         /   bar            bar     \outer
        /                            \strokes
        parameters:
        x0, y0        starting point
        x1, y1        end point
        totalheight   distance from the jaws to the middle cap (default: 0.10 * totallength)
        barthickness  thickness of the main bars (default: 0.05 * totalheight)
        innerstrokesthickness thickness of the two ending strokes (default: 0.45 * barthickness)
        outerstrokesthickness thickness of the inner strokes at the middle cap (default: 0.45 * barthickness)
        innerstrokesrelheight | height of the inner/outer strokes, relative to the total height
        outerstrokesrelheight | this determines the angle of the main bars!
                                should be around 0.5
        Note: if innerstrokesrelheight + outerstrokesrelheight == 1 then the main bars
              will be aligned parallel to the connecting line between the endpoints
        outerstrokesangle  angle of the two ending strokes
        innerstrokesangle  angle between the inner strokes at the middle cap
        slantstrokesangle  extra slanting of the inner/outer strokes
        innerstrokessmoothness | smoothing parameter for the inner + outer strokes
        outerstrokessmoothness | should be around 1 (allowed: [0,infty))
        middlerelpos       position of the middle cap (0 == left, 1 == right)
        """

        # first all the pyx-length parameters:
        self.x0 = unit.length(x0)
        self.y0 = unit.length(y0)
        self.x1 = unit.length(x1)
        self.y1 = unit.length(y1)

        totallength = unit_hypot(x1 - x0, y1 - y0)

        self.leftlength = middlerelpos * totallength
        self.rightlength = (1 - middlerelpos) * totallength
        if totalheight is None:
            self.totalheight = 0.10 * totallength
        else:
            self.totalheight = unit.length(totalheight)

        # use thicknesses relative to the total height:
        if barthickness is None:
            self.barthickness = 0.05 * self.totalheight
        else:
            self.barthickness = unit.length(barthickness)
        if innerstrokesthickness is None:
            self.innerstrokesthickness = 0.45 * self.barthickness
        else:
            self.innerstrokesthickness = unit.length(innerstrokesthickness)
        if outerstrokesthickness is None:
            self.outerstrokesthickness = 0.45 * self.barthickness
        else:
            self.outerstrokesthickness = unit.length(outerstrokesthickness)

        # then angle parameters in degrees:
        self.innerstrokesangle = innerstrokesangle
        self.outerstrokesangle = outerstrokesangle
        self.slantstrokesangle = slantstrokesangle

        # and then simple number parameters:
        self.innerstrokesrelheight = innerstrokesrelheight
        self.outerstrokesrelheight = outerstrokesrelheight
        self.middlerelpos = middlerelpos

        self.innerstrokessmoothness = innerstrokessmoothness
        self.outerstrokessmoothness = outerstrokessmoothness


    def path(self):

        height_pt = unit.topt(self.totalheight)
        leftlength_pt = unit.topt(self.leftlength)
        rightlength_pt = unit.topt(self.rightlength)

        ithick_pt = unit.topt(self.innerstrokesthickness)
        othick_pt = unit.topt(self.outerstrokesthickness)
        bthick_pt = unit.topt(self.barthickness)

        # create the left halfbrace with positive slanting
        # because we will mirror this part
        cos_iangle = math.cos(math.radians(0.5*self.innerstrokesangle - self.slantstrokesangle))
        sin_iangle = math.sin(math.radians(0.5*self.innerstrokesangle - self.slantstrokesangle))
        cos_oangle = math.cos(math.radians(self.outerstrokesangle - self.slantstrokesangle))
        sin_oangle = math.sin(math.radians(self.outerstrokesangle - self.slantstrokesangle))
        cos_slangle = math.cos(math.radians(-self.slantstrokesangle))
        sin_slangle = math.sin(math.radians(-self.slantstrokesangle))
        ilength_pt = self.innerstrokesrelheight * height_pt / cos_iangle
        olength_pt = self.outerstrokesrelheight * height_pt / cos_oangle

        bracepath = self.halfbracepath_pt(leftlength_pt, height_pt,
        ilength_pt, olength_pt, ithick_pt, othick_pt, bthick_pt, cos_iangle,
        sin_iangle, cos_oangle, sin_oangle, cos_slangle,
        sin_slangle).reversed().transformed(trafo.mirror(90))

        # create the right halfbrace with negative slanting
        cos_iangle = math.cos(math.radians(0.5*self.innerstrokesangle + self.slantstrokesangle))
        sin_iangle = math.sin(math.radians(0.5*self.innerstrokesangle + self.slantstrokesangle))
        cos_oangle = math.cos(math.radians(self.outerstrokesangle + self.slantstrokesangle))
        sin_oangle = math.sin(math.radians(self.outerstrokesangle + self.slantstrokesangle))
        cos_slangle = math.cos(math.radians(-self.slantstrokesangle))
        sin_slangle = math.sin(math.radians(-self.slantstrokesangle))
        ilength_pt = self.innerstrokesrelheight * height_pt / cos_iangle
        olength_pt = self.outerstrokesrelheight * height_pt / cos_oangle

        bracepath = bracepath << self.halfbracepath_pt(rightlength_pt, height_pt,
        ilength_pt, olength_pt, ithick_pt, othick_pt, bthick_pt, cos_iangle,
        sin_iangle, cos_oangle, sin_oangle, cos_slangle,
        sin_slangle)

        x0_pt = unit.topt(self.x0)
        y0_pt = unit.topt(self.y0)
        x1_pt = unit.topt(self.x1)
        y1_pt = unit.topt(self.y1)
        return bracepath.transformed(
                 # two trafos for matching the given endpoints
                 trafo.translate_pt(x0_pt, y0_pt) *
                 trafo.rotate_pt(math.degrees(math.atan2(y1_pt-y0_pt, x1_pt-x0_pt))) *
                 # one trafo to move the brace's left outer stroke to zero
                 trafo.translate(self.leftlength, 0))

    def halfbracepath_pt(self, length_pt, height_pt, ilength_pt, olength_pt,
    ithick_pt, othick_pt, bthick_pt, cos_iangle, sin_iangle, cos_oangle,
    sin_oangle, cos_slangle, sin_slangle):

        ismooth = self.innerstrokessmoothness
        osmooth = self.outerstrokessmoothness

        # these two parameters are not important enough to be seen outside
        inner_cap_param = 1.5
        outer_cap_param = 2.5
        outerextracurved = 0.6 # in (0, 1]
        # 1.0 will lead to F=G, the outer strokes will not be curved at their ends.
        # The smaller, the more curvature

        # build an orientation path (three straight lines)
        #
        #      \q1
        #    /  \
        #   /    \
        # _/      \______________________________________q5
        #         q2         q3              q4           \
        #                                                  \
        #                                                   \
        #                                                    \q6
        #
        # get the points for that:
        q1 = (0, height_pt - inner_cap_param * ithick_pt + 0.5*ithick_pt/sin_iangle)
        q2 = (q1[0] + ilength_pt * sin_iangle,
              q1[1] - ilength_pt * cos_iangle)
        q6 = (length_pt, 0)
        q5 = (q6[0] - olength_pt * sin_oangle,
              q6[1] + olength_pt * cos_oangle)
        bardir = (q5[0] - q2[0], q5[1] - q2[1])
        bardirnorm = math.hypot(*bardir)
        bardir = (bardir[0]/bardirnorm, bardir[1]/bardirnorm)
        ismoothlength_pt = ilength_pt * ismooth
        osmoothlength_pt = olength_pt * osmooth
        if bardirnorm < ismoothlength_pt + osmoothlength_pt:
            ismoothlength_pt = bardirnorm * ismoothlength_pt / (ismoothlength_pt + osmoothlength_pt)
            osmoothlength_pt = bardirnorm * osmoothlength_pt / (ismoothlength_pt + osmoothlength_pt)
        q3 = (q2[0] + ismoothlength_pt * bardir[0],
              q2[1] + ismoothlength_pt * bardir[1])
        q4 = (q5[0] - osmoothlength_pt * bardir[0],
              q5[1] - osmoothlength_pt * bardir[1])

        #
        #    P _O
        #   / | \A2
        #  / A1\ \
        #   /   \ B2C2________D2___________E2_______F2___G2
        #        \______________________________________  \
        #       B1,C1         D1           E1      F1  G1  \
        #                                                \  \
        #                                                 \  \H2
        #                                                H1\_/I2
        #                                                  I1
        #
        # the halfbraces meet in P and A1:
        P = (0, height_pt)
        A1 = (0, height_pt - inner_cap_param * ithick_pt)
        # A2 is A1, shifted by the inner thickness
        A2 = (A1[0] + ithick_pt * cos_iangle,
              A1[1] + ithick_pt * sin_iangle)
        s, t = deformer.intersection(P, A2, (cos_slangle, sin_slangle), (sin_iangle, -cos_iangle))
        O = (P[0] + s * cos_slangle,
             P[1] + s * sin_slangle)

        # from D1 to E1 is the straight part of the brace
        # also back from E2 to D1
        D1 = (q3[0] + bthick_pt * bardir[1],
              q3[1] - bthick_pt * bardir[0])
        D2 = (q3[0] - bthick_pt * bardir[1],
              q3[1] + bthick_pt * bardir[0])
        E1 = (q4[0] + bthick_pt * bardir[1],
              q4[1] - bthick_pt * bardir[0])
        E2 = (q4[0] - bthick_pt * bardir[1],
              q4[1] + bthick_pt * bardir[0])
        # I1, I2 are the control points at the outer stroke
        I1 = (q6[0] - 0.5 * othick_pt * cos_oangle,
              q6[1] - 0.5 * othick_pt * sin_oangle)
        I2 = (q6[0] + 0.5 * othick_pt * cos_oangle,
              q6[1] + 0.5 * othick_pt * sin_oangle)
        # get the control points for the curved parts of the brace
        s, t = deformer.intersection(A1, D1, (sin_iangle, -cos_iangle), bardir)
        B1 = (D1[0] + t * bardir[0],
              D1[1] + t * bardir[1])
        s, t = deformer.intersection(A2, D2, (sin_iangle, -cos_iangle), bardir)
        B2 = (D2[0] + t * bardir[0],
              D2[1] + t * bardir[1])
        s, t = deformer.intersection(E1, I1, bardir, (-sin_oangle, cos_oangle))
        G1 = (E1[0] + s * bardir[0],
              E1[1] + s * bardir[1])
        s, t = deformer.intersection(E2, I2, bardir, (-sin_oangle, cos_oangle))
        G2 = (E2[0] + s * bardir[0],
              E2[1] + s * bardir[1])
        # at the inner strokes: use curvature zero at both ends
        C1 = B1
        C2 = B2
        # at the outer strokes: use curvature zero only at the connection to
        # the straight part
        F1 = (outerextracurved * G1[0] + (1 - outerextracurved) * E1[0],
              outerextracurved * G1[1] + (1 - outerextracurved) * E1[1])
        F2 = (outerextracurved * G2[0] + (1 - outerextracurved) * E2[0],
              outerextracurved * G2[1] + (1 - outerextracurved) * E2[1])
        # the tip of the outer stroke, endpoints of the bezier curve
        H1 = (I1[0] - outer_cap_param * othick_pt * sin_oangle,
              I1[1] + outer_cap_param * othick_pt * cos_oangle)
        H2 = (I2[0] - outer_cap_param * othick_pt * sin_oangle,
              I2[1] + outer_cap_param * othick_pt * cos_oangle)

        #for qq in [A1,B1,C1,D1,E1,F1,G1,H1,I1,
        #           A2,B2,C2,D2,E2,F2,G2,H2,I2,
        #           O,P
        #           ]:
        #    cc.fill(path.circle(qq[0], qq[1], 0.5), [color.rgb.green])

        # now build the right halfbrace
        bracepath = path.path(path.moveto_pt(*A1))
        bracepath.append(path.curveto_pt(B1[0], B1[1], C1[0], C1[1], D1[0], D1[1]))
        bracepath.append(path.lineto_pt(E1[0], E1[1]))
        bracepath.append(path.curveto_pt(F1[0], F1[1], G1[0], G1[1], H1[0], H1[1]))
        # the tip of the right halfbrace
        bracepath.append(path.curveto_pt(I1[0], I1[1], I2[0], I2[1], H2[0], H2[1]))
        # the rest of the right halfbrace
        bracepath.append(path.curveto_pt(G2[0], G2[1], F2[0], F2[1], E2[0], E2[1]))
        bracepath.append(path.lineto_pt(D2[0], D2[1]))
        bracepath.append(path.curveto_pt(C2[0], C2[1], B2[0], B2[1], A2[0], A2[1]))
        # the tip in the middle of the brace
        bracepath.append(path.curveto_pt(O[0], O[1], O[0], O[1], P[0], P[1]))

        return bracepath



A = (0,5)
B = (6,18)

b1 = straightbrace(A[0], A[1], B[0], B[1],
                   middlerelpos=0.8)
b2 = brace(B[0], B[1], A[0], A[1],
           middlerelpos=0.2,
           innerstrokesrelheight=0.6, outerstrokesrelheight=0.7,
           slantstrokesangle=10)

c = canvas.canvas()
c.fill(path.circle(A[0], A[1], 1), [color.rgb.red])
c.fill(path.circle(B[0], B[1], 1), [color.rgb.blue])
c.stroke(path.line(A[0], A[1], B[0], B[1]))
c.fill(b1.path())
c.fill(b2.path())

c.writetofile("brace.eps", paperformat=document.paperformat.A4, fittosize=1, rotated=0)

