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
    def __init__(self, uscale=1.0, vscale=1.0, wscale=1.0):
        self.scale        = { 't':1, 'u':uscale, 'v':vscale, 'w':wscale }
        
    def convert_to(self, l, dest_unit="m"):

        if type(l) is TupleType:
            return tuple(map(lambda x, self=self, dest_unit=dest_unit:self.convert_to(x,dest_unit), l))

        ll=length(l)                    # convert to length instance if necessary

        return ll.factor*self.scale[ll.unit_type]/m[dest_unit]

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
    """
    
    default_unit = "cm"

    def __init__(self, *args):
        if len(args)==1:
            l=args[0]
            if isinstance(l, length):
                self.factor    = l.factor
                self.unit_type = l.unit_type

            elif type(l) is StringType:
                unit_match=re.match(unit_pattern, l)
                if unit_match is None:
                    assert 0, "expecting number or string of the form 'number [u|v|w] unit'"
                else:
                    self.factor    = float(unit_match.group(1))
                    self.unit_type = unit_match.group(7) or "u"
                    self.unit_name = unit_match.group(9) or self.default_unit

                    self.factor    = self.factor * m[self.unit_name]

            elif type(l) in (IntType, LongType, FloatType):
                self.factor     = l * m[length.default_unit]
                self.unit_type  = "u"
            else:
                assert 0, "cannot convert given argument to length type"
        elif len(args)==3:
            self.factor    = args[0] * m[args[2]]
            self.unit_type = args[1]
        else: 
            assert 0, "expecting string or factor, unit_type, unit_name"

    def __mul__(self, factor):
        return length(self.factor * factor, self.unit_type, "m")

    __rmul__=__mul__

    def __add__(self, l):
        ll=length(l)                    # convert to length if necessary
        if ( self.unit_type!=ll.unit_type 
             and not (self.factor==0 or ll.factor==0) ):
            assert 0, "can only add units of same type"
        else:
            return length(self.factor+ll.factor, self.unit_type, "m")

    def __neg__(self):
        return length(-self.factor, self.unit_type, "m")

    __radd__=__add__

    def __str__(self):
        return "%f %s m" % (self.factor, self.unit_type)

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

