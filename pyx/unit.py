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

import types
import re
import helper

scale = { 't':1, 'u':1, 'v':1, 'w':1, 'x':1 }

_default_unit = "cm"

unit_pattern = re.compile(r"""^\s*([+-]?\d*((\d\.?)|(\.?\d))\d*(E[+-]?\d+)?)
                              (\s+([t-x]))?
                              (\s+(([a-z][a-z]+)|[^t-x]))?\s*$""",
                          re.IGNORECASE | re.VERBOSE)


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
        return l*_m[_default_unit]*scale['u']/_m[dest_unit]
    elif not isinstance(l, length): 
        l=length(l)       # convert to length instance if necessary

    return ( l.length['t']            +
             l.length['u']*scale['u'] +
             l.length['v']*scale['v'] +
             l.length['w']*scale['w'] +
             l.length['x']*scale['x'] ) / _m[dest_unit]

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

    Lengths can either be a initialized with a number or a string:

     - a length specified as a number corresponds to the default values of
       unit_type and unit_name
     - a string has to consist of a maximum of three parts:
       -quantifier: integer/float value
       -unit_type:  "t", "u", "v", "w", or "x".
                    Optional, defaults to "u"
       -unit_name:  "m", "cm", "mm", "inch", "pt".
                    Optional, defaults to _default_unit

    Internally all length are stored in units of m as a quadruple of the four
    unit_types.

    """

    def __init__(self, l=1, default_type="u", dunit=None):
        self.length = { 't': 0 , 'u': 0, 'v': 0, 'w': 0, 'x': 0 }

        if isinstance(l, length):
            self.length = l.length
        elif helper.isnumber(l):
            self.length[default_type] = l*_m[dunit or _default_unit]
        elif helper.isstring(l):
            unit_match = re.match(unit_pattern, l)
            if unit_match is None:
                raise ValueError("expecting number or string of the form 'number [u|v|w|x] unit'")
            else:
                self.prefactor = float(unit_match.group(1))
                self.unit_type = unit_match.group(7) or default_type
                self.unit_name = unit_match.group(9) or dunit or _default_unit

                self.length[self.unit_type] = self.prefactor*_m[self.unit_name]
        else:
            raise NotImplementedError("cannot convert given argument to length type")

    def __cmp__(self, other):
        return cmp(tom(self), tom(other))

    def __mul__(self, factor):
        newlength = self.__class__()
        for unit_type in newlength.length.keys():
           newlength.length[unit_type] = self.length[unit_type]*factor
        return newlength

    __rmul__=__mul__

    def __div__(self, factor):
        newlength = self.__class__()
        for unit_type in newlength.length.keys():
           newlength.length[unit_type] = self.length[unit_type]/factor
        return newlength

    def __add__(self, l):
        # convert to length if necessary
        ll = length(l)
        newlength = self.__class__()
        for unit_type in newlength.length.keys():
           newlength.length[unit_type] = self.length[unit_type] + ll.length[unit_type]
        return newlength

    __radd__=__add__

    def __sub__(self, l):
        # convert to length if necessary
        ll = length(l)
        newlength = self.__class__()
        for unit_type in newlength.length.keys():
           newlength.length[unit_type] = self.length[unit_type] - ll.length[unit_type]
        return newlength

    def __rsub__(self, l):
        # convert to length if necessary
        ll = length(l)
        newlength = self.__class__()
        for unit_type in newlength.length.keys():
           newlength.length[unit_type] = ll.length[unit_type] - self.length[unit_type]
        return newlength

    def __neg__(self):
        newlength = self.__class__()
        for unit_type in newlength.length.keys():
           newlength.length[unit_type] = -self.length[unit_type]
        return newlength

    def __str__(self):
        return "(%(t)f t + %(u)f u + %(v)f v + %(w)f w + %(x)f x) m" % self.length


################################################################################
# predefined instances which can be used as length units
################################################################################

# user lengths and unqualified length which are also user length
u_pt = pt = length("1 u pt")
u_m = m = length("1 u m")
u_mm = mm = length("1 u mm")
u_cm = cm = length("1 u cm")
u_inch = inch = length("1 u inch")

# true lengths
t_pt = length("1 t pt")
t_m = length("1 t m")
t_mm = length("1 t mm")
t_cm = length("1 t cm")
t_inch = length("1 t inch")

# visual lengths
v_pt = length("1 v pt")
v_m = length("1 v m")
v_mm = length("1 v mm")
v_cm = length("1 v cm")
v_inch = length("1 v inch")


# width lengths
w_pt = length("1 w pt")
w_m = length("1 w m")
w_mm = length("1 w mm")
w_cm = length("1 w cm")
w_inch = length("1 w inch")

# TeX lengths
x_pt = length("1 x pt")
x_m = length("1 x m")
x_mm = length("1 x mm")
x_cm = length("1 x cm")
x_inch = length("1 x inch")
