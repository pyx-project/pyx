#!/usr/bin/env python
#
#
# Copyright (C) 2002-2003 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2002-2003 André Wobst <wobsta@users.sourceforge.net>
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


import types, re, math, string, sys
import bbox, path, unit, trafo


class BoxCrossError(Exception): pass

class _poly:

    def __init__(self, corners=None, center=None, trafo=None):
        self.corners = corners
        self.center = center
        if trafo is not None:
            self.transform(trafo)

    def path(self, centerradius=None):
        # TODO: - supply curved box plotting (Michael Schindler)
        pathels = []
        if centerradius is not None and self.center is not None:
            r = unit.topt(unit.length(centerradius, default_type="v"))
            pathels.append(path._arc(self.center[0], self.center[1], r, 0, 360))
            pathels.append(path.closepath())
        pathels.append(path._moveto(self.corners[0][0], self.corners[0][1]))
        for x, y in self.corners[1:]:
            pathels.append(path._lineto(x, y))
        pathels.append(path.closepath())
        return path.path(*pathels)

    def transform(self, trafo):
        if self.center is not None:
            self.center = trafo._apply(*self.center)
        self.corners = [trafo._apply(*point) for point in self.corners]
        return self

    def successivepointnumbers(self):
        return map(lambda i, self=self: i and (i - 1, i) or (len(self.corners) - 1, 0), range(len(self.corners)))

    def successivepoints(self):
        return [(self.corners[i], self.corners[j]) for i, j in self.successivepointnumbers()]

    def _circlealignlinevector(self, a, dx, dy, ex, ey, fx, fy, epsilon=1e-10):
        cx, cy = self.center
        gx, gy = ex - fx, ey - fy # direction vector
        if gx*gx + gy*gy < epsilon: # zero line length
            return None             # no solution -> return None
        rsplit = (dx*gx + dy*gy) * 1.0 / (gx*gx + gy*gy)
        bx, by = dx - gx * rsplit, dy - gy * rsplit
        if bx*bx + by*by < epsilon: # zero projection
            return None             # no solution -> return None
        if bx*gy - by*gx < 0: # half space
            return None       # no solution -> return None
        sfactor = math.sqrt((dx*dx + dy*dy) / (bx*bx + by*by))
        bx, by = a * bx * sfactor, a * by * sfactor
        alpha = ((bx+cx-ex)*dy - (by+cy-ey)*dx) * 1.0 / (gy*dx - gx*dy)
        if alpha > 0 - epsilon and alpha < 1 + epsilon:
                beta = ((ex-bx-cx)*gy - (ey-by-cy)*gx) * 1.0 / (gx*dy - gy*dx)
                return beta*dx - cx, beta*dy - cy # valid solution -> return align tuple
        # crossing point at the line, but outside a valid range
        if alpha < 0:
            return 0 # crossing point outside e
        return 1 # crossing point outside f

    def _linealignlinevector(self, a, dx, dy, ex, ey, fx, fy, epsilon=1e-10):
        cx, cy = self.center
        gx, gy = ex - fx, ey - fy # direction vector
        if gx*gx + gy*gy < epsilon: # zero line length
            return None             # no solution -> return None
        if gy*dx - gx*dy < -epsilon: # half space
            return None              # no solution -> return None
        if dx*gx + dy*gy > epsilon or dx*gx + dy*gy < -epsilon:
            if dx*gx + dy*gy < 0: # angle bigger 90 degree
                return 0 # use point e
            return 1 # use point f
        # a and g are othorgonal
        alpha = ((a*dx+cx-ex)*dy - (a*dy+cy-ey)*dx) * 1.0 / (gy*dx - gx*dy)
        if alpha > 0 - epsilon and alpha < 1 + epsilon:
            beta = ((ex-a*dx-cx)*gy - (ey-a*dy-cy)*gx) * 1.0 / (gx*dy - gy*dx)
            return beta*dx - cx, beta*dy - cy # valid solution -> return align tuple
        # crossing point at the line, but outside a valid range
        if alpha < 0:
            return 0 # crossing point outside e
        return 1 # crossing point outside f

    def _circlealignpointvector(self, a, dx, dy, px, py, epsilon=1e-10):
        if a*a < epsilon:
            return None
        cx, cy = self.center
        p = 2 * ((px-cx)*dx + (py-cy)*dy)
        q = ((px-cx)*(px-cx) + (py-cy)*(py-cy) - a*a)
        if p*p/4 - q < 0:
            return None
        if a > 0:
            alpha = - p / 2 + math.sqrt(p*p/4 - q)
        else:
            alpha = - p / 2 - math.sqrt(p*p/4 - q)
        return alpha*dx - cx, alpha*dy - cy

    def _linealignpointvector(self, a, dx, dy, px, py):
        cx, cy = self.center
        beta = (a*dx+cx-px)*dy - (a*dy+cy-py)*dx
        return a*dx - beta*dy - px, a*dy + beta*dx - py

    def _alignvector(self, a, dx, dy, alignlinevector, alignpointvector):
        linevectors = map(lambda (p1, p2), self=self, a=a, dx=dx, dy=dy, alignlinevector=alignlinevector:
                                alignlinevector(a, dx, dy, *(p1 + p2)), self.successivepoints())
        for linevector in linevectors:
            if type(linevector) is types.TupleType:
                return linevector
        for i, j in self.successivepointnumbers():
            l1, l2 = linevectors[i], linevectors[j]
            if (l1 is not None or l2 is not None) and (l1 == 1 or l1 is None) and (l2 == 0 or l2 is None):
                return alignpointvector(a, dx, dy, *self.successivepoints()[j][0])
        return a*dx, a*dy

    def _circlealignvector(self, a, dx, dy):
        return self._alignvector(a, dx, dy, self._circlealignlinevector, self._circlealignpointvector)

    def _linealignvector(self, a, dx, dy):
        return self._alignvector(a, dx, dy, self._linealignlinevector, self._linealignpointvector)

    def circlealignvector(self, a, dx, dy):
        return map(unit.t_pt, self._circlealignvector(unit.topt(a), dx, dy))

    def linealignvector(self, a, dx, dy):
        return map(unit.t_pt, self._linealignvector(unit.topt(a), dx, dy))

    def _circlealign(self, *args):
        self.transform(trafo._translate(*self._circlealignvector(*args)))
        return self

    def _linealign(self, *args):
        self.transform(trafo._translate(*self._linealignvector(*args)))
        return self

    def circlealign(self, *args):
        self.transform(trafo.translate(*self.circlealignvector(*args)))
        return self

    def linealign(self, *args):
        self.transform(trafo.translate(*self.linealignvector(*args)))
        return self

    def _extent(self, dx, dy):
        x1, y1 = self._linealignvector(0, dx, dy)
        x2, y2 = self._linealignvector(0, -dx, -dy)
        return (x1-x2)*dx + (y1-y2)*dy

    def extent(self, dx, dy):
        return unit.t_pt(self._extent(dx, dy))

    def _pointdistance(self, x, y):
        result = None
        for p1, p2 in self.successivepoints():
            gx, gy = p2[0] - p1[0], p2[1] - p1[1]
            if gx * gx + gy * gy < 1e-10:
                dx, dy = p1[0] - x, p1[1] - y
            else:
                a = (gx * (x - p1[0]) + gy * (y - p1[1])) / (gx * gx + gy * gy)
                if a < 0:
                    dx, dy = p1[0] - x, p1[1] - y
                elif a > 1:
                    dx, dy = p2[0] - x, p2[1] - y
                else:
                    dx, dy = x - p1[0] - a * gx, y - p1[1] - a * gy
            new = math.sqrt(dx * dx + dy * dy)
            if result is None or new < result:
                result = new
        return result

    def pointdistance(self, x, y):
        return unit.t_pt(self._pointdistance(unit.topt(x), unit.topt(y)))

    def _boxdistance(self, other, epsilon = 1e-10):
        # XXX: boxes crossing and distance calculation is O(N^2)
        for p1, p2 in self.successivepoints():
            for p3, p4 in other.successivepoints():
                a = (p4[1] - p3[1]) * (p3[0] - p1[0]) - (p4[0] - p3[0]) * (p3[1] - p1[1])
                b = (p2[1] - p1[1]) * (p3[0] - p1[0]) - (p2[0] - p1[0]) * (p3[1] - p1[1])
                c = (p2[0] - p1[0]) * (p4[1] - p3[1]) - (p2[1] - p1[1]) * (p4[0] - p3[0])
                if (abs(c) > 1e-10 and
                    a / c > -epsilon and a / c < 1 + epsilon and
                    b / c > -epsilon and b / c < 1 + epsilon):
                    raise BoxCrossError
        result = None
        for x, y in other.corners:
            new = self._pointdistance(x, y)
            if result is None or new < result:
                result = new
        for x, y in self.corners:
            new = other._pointdistance(x, y)
            if result is None or new < result:
                result = new
        return result

    def boxdistance(self, other):
        return unit.t_pt(self._boxdistance(other))


class poly(_poly):

    def __init__(self, corners=None, center=None, **args):
        corners = [[unit.topt(x) for x in corner] for corner in corners]
        if center is not None:
            center = map(unit.topt, center)
        _poly.__init__(self, corners=corners, center=center, **args)


class _rect(_poly):

    def __init__(self, x, y, width, height, relcenter=(0, 0), abscenter=(0, 0), **args):
        self._bbox = bbox.bbox(x, y, x + width, y + height)
        _poly.__init__(self, corners=((x, y),
                                      (x + width, y),
                                      (x + width, y + height),
                                      (x, y + height)),
                             center=(x + relcenter[0] * width + abscenter[0], y + relcenter[1] * height + abscenter[1]), **args)

    def transform(self, trafo):
        _poly.transform(self, trafo)
        self._bbox = self._bbox.transform(trafo)

    def bbox(self):
        return self._bbox


class rect(_rect):

    def __init__(self, x, y, width, height, relcenter=(0, 0), abscenter=(0, 0), **args):
        _rect.__init__(self, unit.topt(x), unit.topt(y), unit.topt(width), unit.topt(height),
                             relcenter=relcenter, abscenter=(unit.topt(center[0]), unit.topt(center[1])), **args)

