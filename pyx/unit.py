#!/usr/bin/env python

from types import *
import re

unit_ps         = 1.0

class unit:
 
    unit_u2p        = 28.346456693*unit_ps
    unit_v2p        = 28.346456693*unit_ps
    unit_w2p        = 28.346456693*unit_ps

    def __init__(self):
        pass
        
    def point(self, length):
        if type(length) in (IntType, FloatType, LongType):
            return length*self.unit_u2p
        else:
           if type(length) is StringType:
               pass
           else: 
               if type(length) is TupleType:
                   return tuple(map(lambda x, self=self:self.point(x), length))

