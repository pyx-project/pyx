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
import bbox, path, unit, trafo, helper


class BoxCrossError(Exception): pass

class _polygon:

    def __init__(self, corners=None, center=None):
        self.corners = corners
        self.center = center

    def path(self, centerradius=None, bezierradius=None, beziersoftness=1):
        pathels = []
        if centerradius is not None and self.center is not None:
            r = unit.topt(unit.length(centerradius, default_type="v"))
            pathels.append(path._arc(self.center[0], self.center[1], r, 0, 360))
            pathels.append(path.closepath())
        if bezierradius is None:
            pathels.append(path._moveto(self.corners[0][0], self.corners[0][1]))
            for x, y in self.corners[1:]:
                pathels.append(path._lineto(x, y))
            pathels.append(path.closepath())
        else:
            # curved box plotting by Michael Schindler
            l = len(self.corners)
            x = beziersoftness
            r = unit.topt(bezierradius)
            for i in range(l):
                c = self.corners[i]
                def normed(*v):
                    n = math.sqrt(v[0] * v[0] + v[1] * v[1])
                    return v[0] / n, v[1] / n
                d1 = normed(self.corners[(i - 1 + l) % l][0] - c[0],
                            self.corners[(i - 1 + l) % l][1] - c[1])
                d2 = normed(self.corners[(i + 1 + l) % l][0] - c[0],
                            self.corners[(i + 1 + l) % l][1] - c[1])
                dc = normed(d1[0] + d2[0], d1[1] + d2[1])
                f = 0.375 * x * r
                g = 1.25 * f + math.sqrt(1.5625 * f * f + f * r / 6.0)
                e = f * math.sqrt(0.5 + 0.5 * (d1[0] * d2[0] + d1[1] * d2[1]))
                e = c[0] + e * dc[0], c[1] + e * dc[1]
                f1 = c[0] + f * d1[0], c[1] + f * d1[1]
                f2 = c[0] + f * d2[0], c[1] + f * d2[1]
                g1 = c[0] + g * d1[0], c[1] + g * d1[1]
                g2 = c[0] + g * d2[0], c[1] + g * d2[1]
                d1 = c[0] + r * d1[0], c[1] + r * d1[1]
                d2 = c[0] + r * d2[0], c[1] + r * d2[1]
                if i:
                    pathels.append(path._lineto(*d1))
                else:
                    pathels.append(path._moveto(*d1))
                pathels.append(path._curveto(*(g1 + f1 + e)))
                pathels.append(path._curveto(*(f2 + g2 + d2)))
            pathels.append(path.closepath())
        return path.path(*pathels)

    def transform(self, *trafos):
        for trafo in trafos:
            if self.center is not None:
                self.center = trafo._apply(*self.center)
            self.corners = [trafo._apply(*point) for point in self.corners]

    def reltransform(self, *trafos):
        if self.center is not None:
            trafos = ([trafo._translate(-self.center[0], -self.center[1])] +
                      list(trafos) +
                      [trafo._translate(self.center[0], self.center[1])])
        self.transform(*trafos)

    def successivepointnumbers(self):
        return [i and (i - 1, i) or (len(self.corners) - 1, 0) for i in range(len(self.corners))]

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
                return beta*dx, beta*dy # valid solution -> return align tuple
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
            return beta*dx, beta*dy # valid solution -> return align tuple
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
        return alpha*dx, alpha*dy

    def _linealignpointvector(self, a, dx, dy, px, py):
        cx, cy = self.center
        beta = (a*dx+cx-px)*dy - (a*dy+cy-py)*dx
        return a*dx - beta*dy - px + cx, a*dy + beta*dx - py + cy

    def _alignvector(self, a, dx, dy, alignlinevector, alignpointvector):
        n = math.sqrt(dx * dx + dy * dy)
        dx, dy = dx / n, dy / n
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
        n = math.sqrt(dx * dx + dy * dy)
        dx, dy = dx / n, dy / n
        oldcenter = self.center
        if self.center is None:
            self.center = 0, 0
        x1, y1 = self._linealignvector(0, dx, dy)
        x2, y2 = self._linealignvector(0, -dx, -dy)
        self.center = oldcenter
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

    def _boxdistance(self, other, epsilon=1e-10):
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

    def bbox(self):
        return bbox.bbox(min([x[0] for x in self.corners]),
                         min([x[1] for x in self.corners]),
                         max([x[0] for x in self.corners]),
                         max([x[1] for x in self.corners]))


def _genericalignequal(method, polygons, a, dx, dy):
    vec = None
    for p in polygons:
        v = method(p, a, dx, dy)
        if vec is None or vec[0] * dx + vec[1] * dy < v[0] * dx + v[1] * dy:
            vec = v
    for p in polygons:
        p.transform(trafo._translate(*vec))


def _circlealignequal(polygons, *args):
    _genericalignequal(_polygon._circlealignvector, polygons, *args)

def _linealignequal(polygons, *args):
    _genericalignequal(_polygon._linealignvector, polygons, *args)

def circlealignequal(polygons, *args):
    _genericalignequal(_polygon.circlealignvector, polygons, *args)

def linealignequal(polygons, *args):
    _genericalignequal(_polygon.linealignvector, polygons, *args)


def _tile(polygons, a, dx, dy):
    d = maxextent = polygons[0]._extent(dx, dy)
    for p in polygons[1:]:
        extent = p._extent(dx, dy)
        if extent > maxextent:
            maxextent = extent
    for p in polygons:
        p.transform(trafo._translate(d*dx, d*dy))
        d += maxextent + a


def tile(polygons, a, dx, dy):
    _tile(polygons, unit.topt(a), dx, dy)

def _htile(polygons, a):
    _tile(polygons, a, 1, 0)

def htile(polygons, a):
    tile(polygons, a, 1, 0)

def _vtile(polygons, a):
    _tile(polygons, a, 0, 1)

def vtile(polygons, a):
    tile(polygons, a, 0, 1)


class polygon(_polygon):

    def __init__(self, corners=None, center=None, **args):
        corners = [[unit.topt(x) for x in corner] for corner in corners]
        if center is not None:
            center = map(unit.topt, center)
        _polygon.__init__(self, corners=corners, center=center, **args)


class _rect(_polygon):

    def __init__(self, x, y, width, height, relcenter=(0, 0), abscenter=(0, 0),
                       corners=helper.nodefault, center=helper.nodefault, **args):
        if corners != helper.nodefault or center != helper.nodefault:
            raise ValueError
        _polygon.__init__(self, corners=((x, y),
                                      (x + width, y),
                                      (x + width, y + height),
                                      (x, y + height)),
                             center=(x + relcenter[0] * width + abscenter[0],
                                     y + relcenter[1] * height + abscenter[1]),
                             **args)


class rect(_rect):

    def __init__(self, x, y, width, height, relcenter=(0, 0), abscenter=(0, 0), **args):
        _rect.__init__(self, unit.topt(x), unit.topt(y), unit.topt(width), unit.topt(height),
                             relcenter=relcenter, abscenter=(unit.topt(center[0]), unit.topt(center[1])), **args)

