#!/usr/bin/env python
#
#
# Copyright (C) 2002 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2002 André Wobst <wobsta@users.sourceforge.net>
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

from types import *
import re

unit_ps = 1.0

scale = { 't':1, 'u':1, 'v':1, 'w':1 }

default_unit = "cm"

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
      'tpt':  0.01*2.54/72.27,
    }

def set(uscale=None, vscale=None, wscale=None):
    if uscale:
        scale['u'] = uscale
    if vscale:
        scale['v'] = vscale
    if wscale:
        scale['w'] = wscale
    
            
def convert_to(l, dest_unit="m"):

    if type(l) is TupleType:
        return tuple(map(lambda x, self=self, dest_unit=dest_unit:
                         self.convert_to(x,dest_unit), l))

    if type(l) in (IntType, LongType, FloatType):
        return l*_m[default_unit]*scale['u']/_m[dest_unit]
    elif not isinstance(l,length): 
        l=length(l)       # convert to length instance if necessary

    return ( l.length['t']            +
	     l.length['u']*scale['u'] +
	     l.length['v']*scale['v'] +
	     l.length['w']*scale['w'] ) / _m[dest_unit]



def tom(l):
    return convert_to(l, "m")
        
def topt(l):
    return convert_to(l, "pt")
        
def totpt(l):
    return convert_to(l, "tpt")

################################################################################
# class for generic length
################################################################################

class length:
    """ general lengths
    
    Lengths can either be a initialized with a number or a string:
     - a length specified as a number corresponds to the default values of unit_type
       and unit_name
     - a string has to consist of a maximum of three parts:
       -quantifier: integer/float value
       -unit_type:  "t", "u", "v", or "w". Optional, defaults to "u"
       -unit_name:  "m", "cm", "mm", "inch", "pt", "tpt". Optional, defaults to default_unit

    Internally all length are stored in units of m as a quadruple for the four unit_types
    """

    def __init__(self, l=None, default_type="u", dunit=None, glength=None):
        self.length = { 't': 0 , 'u': 0, 'v': 0, 'v':0, 'w':0 }
        
        if l:
            if isinstance(l,length):
               self.length=l.length
            elif type(l) is StringType:
                unit_match=re.match(unit_pattern, l)
                if unit_match is None:
                    assert 0, "expecting number or string of the form 'number [u|v|w] unit'"
                else:
                    self.prefactor = float(unit_match.group(1))
                    self.unit_type = unit_match.group(7) or default_type
                    self.unit_name = unit_match.group(9) or dunit or default_unit

                    self.length[self.unit_type] = self.prefactor*_m[self.unit_name]

            elif type(l) in (IntType, LongType, FloatType):
                self.length[default_type] = l*_m[dunit or default_unit]
            else:
                raise ( NotImplementedError,
			"cannot convert given argument to length type" )
        if glength:
            self.length=glength

    def __mul__(self, factor):
        newlength = self.length.copy()
        for unit_type in newlength.keys():
           newlength[unit_type] = newlength[unit_type]*factor
        return length(glength=newlength)

    __rmul__=__mul__

    def __add__(self, l):
        ll=length(l)                    # convert to length if necessary
        newlength = self.length.copy()
        for unit_type in newlength.keys():
           newlength[unit_type] = newlength[unit_type] + ll.length[unit_type]
        return length(glength=newlength)

    __radd__=__add__

    def __sub__(self, l):
        ll=length(l)                    # convert to length if necessary
        newlength = self.length.copy()
        for unit_type in newlength.keys():
           newlength[unit_type] = newlength[unit_type] - ll.length[unit_type]
        return length(glength=newlength)

    def __rsub__(self, l):
        ll=length(l)                    # convert to length if necessary
        newlength = self.length.copy()
        for unit_type in newlength.keys():
           newlength[unit_type] = ll.length[unit_type] - newlength[unit_type]
        return length(glength=newlength)

    def __neg__(self):
        newlength = self.length.copy()
        for unit_type in newlength.keys():
           newlength[unit_type] = -newlength[unit_type]
        return length(glength=newlength)

    def __str__(self):
        return "(%(t)f t + %(u)f u + %(v)f v + %(w)f w) m" % self.length

################################################################################
# class for more specialized lengths
################################################################################

# lengths in user units as default

class pt(length):
    def __init__(self, l=None, default_type="u"):
       length.__init__(self, l, default_type=default_type, dunit="pt")


class tpt(length):
    def __init__(self, l=None, default_type="u"):
       length.__init__(self, l, default_type=default_type, dunit="tpt")


class m(length):
    def __init__(self, l=None, default_type="u"):
       length.__init__(self, l, default_type=default_type, dunit="m")


# true lengths 

class t_pt(length):
    def __init__(self, l=None):
       length.__init__(self, l, default_type="t", dunit="pt")
       

class t_tpt(length):
    def __init__(self, l=None):
       length.__init__(self, l, default_type="t", dunit="tpt")


class t_m(length):
    def __init__(self, l=None):
       length.__init__(self, l, default_type="t", dunit="m")
