#!/usr/bin/env python

unit_ps         = 1.0
 
unit_u2p        = 28.346456693*unit_ps
unit_v2p        = 28.346456693*unit_ps
unit_w2p        = 28.346456693*unit_ps

class unit:
    def u2p(self, lengths):
        if isnumber(lengths):
            return lengths*unit_u2p
        else:
            return tuple(map(lambda x:x*unit_u2p, lengths))
 
    def v2p(self, lengths):
        if isnumber(lengths):
            return lengths*unit_v2p
        else:
            return tuple(map(lambda x:x*unit_v2p, lengths))
 
    def w2p(self, lengths):
        if type(lengths)==type(0.0):
            return lengths*unit_w2p
        else:
            return tuple(map(lambda x:x*unit_w2p, lengths))
