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

unit_ps = 1.0

scale = { 't':1, 'u':1, 'v':1, 'w':1 }

_default_unit = "cm"

unit_pattern = re.compile(r"""^\s*([+-]?\d*((\d\.?)|(\.?\d))\d*(E[+-]?\d+)?)
                              (\s+([t-w]))?
                              (\s+(([a-z][a-z]+)|[^t-w]))?\s*$""",
                          re.IGNORECASE | re.VERBOSE)


_m = { 
      'm' :   1,
      'cm':   0.01,
      'mm':   0.001,
      'inch': 0.01*2.54,
      'pt':   0.01*2.54/72,
    }

def set(uscale=None, vscale=None, wscale=None, defaultunit=None):
    if uscale:
        scale['u'] = uscale
    if vscale:
        scale['v'] = vscale
    if wscale:
        scale['w'] = wscale
    if defaultunit:
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
             l.length['w']*scale['w'] ) / _m[dest_unit]

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
       -unit_type:  "t", "u", "v", or "w".
                    Optional, defaults to "u"
       -unit_name:  "m", "cm", "mm", "inch", "pt".
                    Optional, defaults to _default_unit

    Internally all length are stored in units of m as a quadruple of the four
    unit_types.

    """

    def __init__(self, l=1, default_type="u", dunit=None):
        self.length = { 't': 0 , 'u': 0, 'v': 0, 'v':0, 'w':0 }

        if isinstance(l, length):
            self.length = l.length
        elif helper.isnumber(l):
            self.length[default_type] = l*_m[dunit or _default_unit]
        elif helper.isstring(l):
            unit_match = re.match(unit_pattern, l)
            if unit_match is None:
                raise ValueError("expecting number or string of the form 'number [u|v|w] unit'")
            else:
                self.prefactor = float(unit_match.group(1))
                self.unit_type = unit_match.group(7) or default_type
                self.unit_name = unit_match.group(9) or dunit or _default_unit

                self.length[self.unit_type] = self.prefactor*_m[self.unit_name]
        else:
            raise ( NotImplementedError,
                    "cannot convert given argument to length type" )

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
        return "(%(t)f t + %(u)f u + %(v)f v + %(w)f w) m" % self.length


################################################################################
# class for more specialized lengths
################################################################################

# lengths with user units as default

class u_pt(length):
    def __init__(self, l=1, default_type="u"):
       length.__init__(self, l, default_type=default_type, dunit="pt")


class u_m(length):
    def __init__(self, l=1, default_type="u"):
       length.__init__(self, l, default_type=default_type, dunit="m")


class u_mm(length):
    def __init__(self, l=1, default_type="u"):
       length.__init__(self, l, default_type=default_type, dunit="mm")


class u_cm(length):
    def __init__(self, l=1, default_type="u"):
       length.__init__(self, l, default_type=default_type, dunit="cm")


class u_inch(length):
    def __init__(self, l=1, default_type="u"):
       length.__init__(self, l, default_type=default_type, dunit="inch")

# without further specification, length are user length. Hence we
# define the following aliases

pt = u_pt
m = u_m
cm = u_cm
mm = u_mm
inch = u_inch

# true lengths

class t_pt(length):
    def __init__(self, l=1):
       length.__init__(self, l, default_type="t", dunit="pt")


class t_m(length):
    def __init__(self, l=1):
       length.__init__(self, l, default_type="t", dunit="m")


class t_cm(length):
    def __init__(self, l=1):
       length.__init__(self, l, default_type="t", dunit="cm")


class t_mm(length):
    def __init__(self, l=1):
       length.__init__(self, l, default_type="t", dunit="mm")


class t_inch(length):
    def __init__(self, l=1):
       length.__init__(self, l, default_type="t", dunit="inch")

# visual lengths

class v_pt(length):
    def __init__(self, l=1):
       length.__init__(self, l, default_type="v", dunit="pt")


class v_m(length):
    def __init__(self, l=1):
       length.__init__(self, l, default_type="v", dunit="m")


class v_cm(length):
    def __init__(self, l=1):
       length.__init__(self, l, default_type="v", dunit="cm")


class v_mm(length):
    def __init__(self, l=1):
       length.__init__(self, l, default_type="v", dunit="mm")


class v_inch(length):
    def __init__(self, l=1):
       length.__init__(self, l, default_type="v", dunit="inch")

# width lengths

class w_pt(length):
    def __init__(self, l=1):
       length.__init__(self, l, default_type="w", dunit="pt")


class w_m(length):
    def __init__(self, l=1):
       length.__init__(self, l, default_type="w", dunit="m")


class w_cm(length):
    def __init__(self, l=1):
       length.__init__(self, l, default_type="w", dunit="cm")


class w_mm(length):
    def __init__(self, l=1):
       length.__init__(self, l, default_type="w", dunit="mm")


class w_inch(length):
    def __init__(self, l=1):
       length.__init__(self, l, default_type="w", dunit="inch")
