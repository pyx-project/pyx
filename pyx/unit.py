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
    def __init__(self, default_unit="cm", uscale=1.0, vscale=1.0, wscale=1.0):
        self.default_unit = default_unit
        self.scale        = { 'u':uscale, 'v':vscale, 'w':wscale }
        
    def convert_to(self, length, dest_unit="m"):
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

        if type(length) is TupleType:
            return tuple(map(lambda x, self=self, dest_unit=dest_unit:self.convert_to(x,dest_unit), length))
            
        if type(length) is StringType:
            unit_match=re.match(unit_pattern, length)
            if unit_match is None:
                assert 0, "expecting string of the form 'number [u|v|w] unit'"
            else:
                quantifier = float(unit_match.group(1))
                unit_type  = unit_match.group(7) or "u"
                unit_name  = unit_match.group(9) or self.default_unit
        elif type(length) in (IntType, LongType, FloatType):
            quantifier = length
            unit_type  = "u"
            unit_name  = self.default_unit

        return quantifier*self.scale[unit_type]*m[unit_name]/m[dest_unit]

    def m(self, length):
        return self.convert_to(length, "m")
        
    def pt(self, length):
        return self.convert_to(length, "pt")
        
    def tpt(self, length):
        return self.convert_to(length, "tpt")


if __name__ == "__main__":
     print unit(default_unit="inch").m(1)
     print unit().m("1.e-3 v cm")
     print unit().pt("1.e-3 v")
     print unit().tpt("1.e-3")
     print unit().pt("1.e-3 inch")

