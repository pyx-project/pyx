#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2002-2004 Jörg Lehmann <joergl@users.sourceforge.net>
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

import copy
import types
import helper

scale = { 't':1, 'u':1, 'v':1, 'w':1, 'x':1 }

_default_unit = "cm"

_m = { 
      'm' :   1,
      'cm':   0.01,
      'mm':   0.001,
      'inch': 0.01*2.54,
      'pt':   0.01*2.54/72,
    }

def set(uscale=None, vscale=None, wscale=None, xscale=None, defaultunit=None):
    if uscale is not None:
        scale['u'] = uscale
    if vscale is not None:
        scale['v'] = vscale
    if wscale is not None:
        scale['w'] = wscale
    if xscale is not None:
        scale['x'] = xscale
    if defaultunit is not None:
        global _default_unit
        _default_unit = defaultunit


def _convert_to(l, dest_unit="m"):
    if type(l) in (types.IntType, types.LongType, types.FloatType):
        return l * _m[_default_unit] * scale['u'] / _m[dest_unit]
    elif not isinstance(l, length): 
        l = length(l)       # convert to length instance if necessary

    return (l.t + l.u*scale['u'] + l.v*scale['v'] + l.w*scale['w'] + l.x*scale['x']) / _m[dest_unit]

def tom(l):
    return _convert_to(l, "m")

def tocm(l):
    return _convert_to(l, "cm")

def tomm(l):
    return _convert_to(l, "mm")

def toinch(l):
    return _convert_to(l, "inch")

def topt(l):
    return _convert_to(l, "pt")

################################################################################
# class for generic length
################################################################################

class length:
    """ general lengths

    XXX write me

    """

    def __init__(self, f, type="u", unit=None):
        self.t = self.u = self.v = self.w = self.x = 0
        l = f * _m[unit or _default_unit]
        if type == "t":
            self.t = l
        elif type == "u":
            self.u = l
        elif type == "v":
            self.v = l
        elif type == "w":
            self.w = l
        elif type == "x":
            self.x = l

    def __cmp__(self, other):
        return cmp(tom(self), tom(other))

    def __mul__(self, factor):
        result = copy.copy(self)
        result.t *= factor
        result.u *= factor
        result.v *= factor
        result.w *= factor
        result.x *= factor
        return result

    __rmul__=__mul__

    def __div__(self, factor):
        result = copy.copy(self)
        result.t /= factor
        result.u /= factor
        result.v /= factor
        result.w /= factor
        result.x /= factor
        return result

    def __add__(self, other):
        # convert to length if necessary
        if not isinstance(other, length):
            other = length(other)
        result = copy.copy(self)
        result.t += other.t
        result.u += other.u
        result.v += other.v
        result.w += other.w
        result.x += other.x
        return result

    __radd__=__add__

    def __sub__(self, other):
        # convert to length if necessary
        if not isinstance(other, length):
            other = length(other)
        result = copy.copy(self)
        result.t -= other.t
        result.u -= other.u
        result.v -= other.v
        result.w -= other.w
        result.x -= other.x
        return result

    def __rsub__(self, other):
        # convert to length if necessary
        if not isinstance(other, length):
            other = length(other)
        result = copy.copy(self)
        result.t = other.t - self.t
        result.u = other.u - self.u
        result.v = other.v - self.v
        result.w = other.w - self.w
        result.x = other.x - self.x
        return result

    def __neg__(self):
        result = copy.copy(self)
        result.t *= -1
        result.u *= -1
        result.v *= -1
        result.w *= -1
        result.x *= -1
        return result

    def __str__(self):
        return "(%(t)f t + %(u)f u + %(v)f v + %(w)f w + %(x)f x) m" % self.length.__dict__


################################################################################
# predefined instances which can be used as length units
################################################################################

# user lengths and unqualified length which are also user length
u_pt   = pt   = length(1, type="u", unit="pt")
u_m    = m    = length(1, type="u", unit="m")
u_mm   = mm   = length(1, type="u", unit="mm")
u_cm   = cm   = length(1, type="u", unit="cm")
u_inch = inch = length(1, type="u", unit="inch")

# true lengths
t_pt   = length(1, type="t", unit="pt")
t_m    = length(1, type="t", unit="m")
t_mm   = length(1, type="t", unit="mm")
t_cm   = length(1, type="t", unit="cm")
t_inch = length(1, type="t", unit="inch")

# visual lengths
v_pt   = length(1, type="v", unit="pt")
v_m    = length(1, type="v", unit="m")
v_mm   = length(1, type="v", unit="mm")
v_cm   = length(1, type="v", unit="cm")
v_inch = length(1, type="v", unit="inch")

# width lengths
w_pt   = length(1, type="w", unit="pt")
w_m    = length(1, type="w", unit="m")
w_mm   = length(1, type="w", unit="mm")
w_cm   = length(1, type="w", unit="cm")
w_inch = length(1, type="w", unit="inch")

# TeX lengths
x_pt   = length(1, type="x", unit="pt")
x_m    = length(1, type="x", unit="m")
x_mm   = length(1, type="x", unit="mm")
x_cm   = length(1, type="x", unit="cm")
x_inch = length(1, type="x", unit="inch")
