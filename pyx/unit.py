#!/usr/bin/env python

from types import *
import re

unit_ps = 1.0

unit_pattern = re.compile(r"""^\s*([+-]?\d*((\d\.?)|(\.?\d))\d*(E[+-]?\d+)?)
                              (\s+([u-w]))?
                              (\s+(([a-z][a-z]+)|[^uvw]))?\s*$""",
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
    def __init__(self, uscale=1.0, vscale=1.0, wscale=1.0):
        self.scale        = { 'u':uscale, 'v':vscale, 'w':wscale }
        
    def convert_to(self, l, dest_unit="m"):
        """ converts length to given destination unit.

            length can either be a tuple of length which are then separately converted
            or a single value. This value can either be a number or a string.
            The string has to consist of a maximum of three parts:
               -quantifier: integer/float value
               -unit_type:  "u", "v", or "w". Optional, defaults to "u"
               -unit_name:  Optional, defaults to self.default_unit
            length specified as a number corresponds to the default values of unit_type
            and unit_name
        """

        if type(l) is TupleType:
            return tuple(map(lambda x, self=self, dest_unit=dest_unit:self.convert_to(x,dest_unit), l))

        ll=length(l)                    # convert to length instance if necessary

        return ll.factor*self.scale[ll.unit_type]*m[ll.unit_name]/m[dest_unit]

    def m(self, l):
        return self.convert_to(l, "m")
        
    def pt(self, l):
        return self.convert_to(l, "pt")
        
    def tpt(self, l):
        return self.convert_to(l, "tpt")

class length:
    default_unit = "cm"

    def __init__(self, l):
        if isinstance(l, length):
            self.factor    = l.factor
            self.unit_type = l.unit_type
            self.unit_name = l.unit_name
        elif type(l) is StringType:
            unit_match=re.match(unit_pattern, l)
            if unit_match is None:
                assert 0, "expecting number or string of the form 'number [u|v|w] unit'"
            else:
                self.factor    = float(unit_match.group(1))
                self.unit_type = unit_match.group(7) or "u"
                self.unit_name = unit_match.group(9) or self.default_unit

        elif type(l) in (IntType, LongType, FloatType):
            self.factor     = l
            self.unit_type  = "u"
            self.unit_name  = self.default_unit
        else:
            assert 0, "cannot convert given argument to length type"

    def __mul__(self, factor):
        return length("%f %s %s" % (self.factor * factor, self.unit_type, self.unit_name))

    __rmul__=__mul__

    def __add__(self, l):
        ll=length(l)                    # convert to length if necessary
        if ( (self.unit_type!=ll.unit_type or self.unit_name!=ll.unit_name) 
             and not (self.factor==0 or ll.factor==0) ):
            assert 0, "can only add units of same type"
        else:
            return length("%f %s %s" % (self.factor+ll.factor, self.unit_type, self.unit_name))

    __radd__=__add__

if __name__ == "__main__":
     length.default_unit="cm"
     print unit().m(1)
     print unit().m("1.e-3 v cm")
     print unit().pt("1.e-3 v")
     print unit().tpt("1.e-3")
     print unit().pt("1.e-3 inch")

     length.default_unit="inch"
     print unit().m(1)
     print unit().m("1.e-3 v cm")
     print unit().pt("1.e-3 v")
     print unit().tpt("1.e-3")
     print unit().pt("1.e-3 inch")

