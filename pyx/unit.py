#!/usr/bin/env python

from types import *
import re

unit_ps = 1.0

unit_pattern = re.compile(r"""^\s*([+-]?\d*((\d\.?)|(\.?\d))\d*(E[+-]?\d+)?)
                              (\s+([t-w]))?
                              (\s+(([a-z][a-z]+)|[^t-w]))?\s*$""",
                          re.IGNORECASE | re.VERBOSE)


m = { 
      'm' :   1,
      'cm':   0.01,
      'mm':   0.001,
      'inch': 0.01*2.54,
      'pt':   0.01*2.54/72,
      'tpt':  0.01*2.54/72.27,
    }

class unit:
    def __init__(self, scale=None, uscale=None, vscale=None, wscale=None):
        self.scale = { 't':1, 'u':1, 'v':1, 'w':1 }
        if scale: 
            self.scale = scale
        if uscale:
            self.scale[uscale] = uscale
        if vscale:
            self.scale[vscale] = vscale
        if wscale:
            self.scale[wscale] = wscale

    def copy(self):
        return unit(scale=self.scale.copy())
        
    def convert_to(self, l, dest_unit="m"):

#        if type(l) is TupleType:
#            return tuple(map(lambda x, self=self, dest_unit=dest_unit:self.convert_to(x,dest_unit), l))

        if type(l) in (IntType, LongType, FloatType):
            return  l*m[length.default_unit]*self.scale['u']/m[dest_unit]
        elif not isinstance(l,length): l=length(l)                    # convert to length instance if necessary

        return ( l.length['t']                 +
                 l.length['u']*self.scale['u'] +
                 l.length['v']*self.scale['v'] +
                 l.length['w']*self.scale['w'] ) / m[dest_unit]

        result = 0 

#        for unit_type in self.scale.keys():
#            result = result + l.length[unit_type]*self.scale[unit_type]


        return result/m[dest_unit]

    def m(self, l):
        return self.convert_to(l, "m")
        
    def pt(self, l):
        return self.convert_to(l, "pt")
        
    def tpt(self, l):
        return self.convert_to(l, "tpt")

class length:
    """ 
    This value can either be a number or a string.
    The string has to consist of a maximum of three parts:
       -quantifier: integer/float value
       -unit_type:  "t", "u", "v", or "w". Optional, defaults to "u"
       -unit_name:  "m", "cm", "mm", "inch", "pt", "tpt". Optional, defaults to default_unit
    A length specified as a number corresponds to the default values of unit_type
    and unit_name

    Internally all length are stored in units of m as a quadruple for the four unit_types
    """
    
    default_unit = "cm"

    def __init__(self, l=None, default_type="u", glength=None):
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
                    self.unit_name = unit_match.group(9) or self.default_unit

                    self.length[self.unit_type]  = self.prefactor * m[self.unit_name]

            elif type(l) in (IntType, LongType, FloatType):
                self.length['u'] = l * m[length.default_unit]
            else:
                assert 0, "cannot convert given argument to length type"
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

    def __neg__(self):
        newlength = self.length.copy()
        for unit_type in newlength.keys():
           newlength[unit_type] = -newlength[unit_type]
        return length(glength=newlength)

    __radd__=__add__

    def __str__(self):
        return "(%(t)f t + %(u)f u + %(v)f v + %(w)f w) m" % self.length

if __name__ == "__main__":
     length.default_unit="cm"
     print unit().m(1)
     print unit().m("1.e-3 v cm")
     print unit().m("1.e-3 v mm")
     print unit().pt("1.e-3 v")
     print unit().tpt("1.e-3")
     print unit().pt("1.e-3 inch")

     length.default_unit="inch"
     print unit().m(1)
     print unit().m("1.e-3 v cm")
     print unit().m(length("1.e-3 v mm")*5)
     print unit().m(length("1.e-3 v mm")+length("2e-3 v mm"))
     print unit().pt("1.e-3 v")
     print unit().tpt("1.e-3")
     print unit().pt("1.e-3 inch")
     
     length.default_unit="cm"
     print length("1 t") + length("2 u") + length("3 v") + length("4 w")
     
