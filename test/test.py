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

import sys
sys.path.append("..")

import unittest
from pyx import *

def isEqual(trafo1, trafo2):
    return max(map(abs,[trafo1.matrix[0][0]-trafo2.matrix[0][0],
                        trafo1.matrix[0][1]-trafo2.matrix[0][1],
                        trafo1.matrix[1][0]-trafo2.matrix[1][0],
                        trafo1.matrix[1][1]-trafo2.matrix[1][1],
                        trafo1.vector[0]-trafo2.vector[0],
                        trafo1.vector[1]-trafo2.vector[1]]))<1e-7

def correctOnBasis(t, tesx, tesy):
    esx=unit.convert_to(t.apply(1,0), "cm")
#    esx=esx[0].convert_to("cm"), esx[1].convert_to("cm")
    
    esy=unit.convert_to(t.apply(0,1), "cm")
#    esy=esy[0].convert_to("cm"), esy[1].convert_to("cm")
    
#    print "  (1,0) => (%f, %f)" % (unit.tom(esx[0])*100, unit.tom(esx[1])*100)
#    print "  (0,1) => (%f, %f)" % (unit.tom(esy[0])*100, unit.tom(esy[1])*100)
    
    return max(map(abs,[esx[0]-tesx[0], esx[1]-tesx[1],
                        esy[0]-tesy[0], esy[1]-tesy[1]]))<1e-7


class TrafoTestCase(unittest.TestCase):

    def testInverse(self):
        "t*t.inverse()=1"
        from pyx.trafo import *
        t = translate(-1,-1)*rotate(72)*translate(1,1)
        assert isEqual(t*t.inverse(), trafo()), \
                "wrong inverse definition"

    def testTranslate(self):
        from pyx.trafo import *
        assert correctOnBasis(translate(1,0), (2,0), (1,1)), \
               "wrong definition of translate"
        assert correctOnBasis(translate(0,1), (1,1), (0,2)), \
               "wrong definition of translate"

    def testRotate(self):
        from pyx.trafo import *
        assert correctOnBasis(rotate(90), (0,1), (-1,0)), \
               "wrong definition of rotate"
        assert isEqual(rotate(360), trafo()), \
                "rotation by 360 deg is not 1"
        assert isEqual(rotate(40)*rotate(120)*rotate(90)*rotate(110),
                        trafo()), \
                "successive multiplication by 360 degrees does not yield 1"

    def testMirror(self):
        "mirroring two times must yield 1 and -mirror(phi)=mirror(phi+180)"
        from pyx.trafo import *
        assert isEqual(mirror(20)*mirror(20), trafo()), \
                "mirroring not idempotent"
        assert isEqual(mirror(20), mirror(180+20)), \
                "mirroring by 20 degrees unequal to mirroring by 180+20 degrees"

    def testScale(self):
        from pyx.trafo import *
        assert correctOnBasis(scale(0.5), (0.5,0), (0, 0.5)), \
               "wrong definition of scale"
        assert correctOnBasis(scale(0.5, 0.2), (0.5,0), (0, 0.2)), \
               "wrong definition of scale"
        assert isEqual(scale(2,3)*scale(1/2.0, 1/3.0), trafo()), \
                "scale definition wrong"

   
    def testMultVsMethods(self):
        "test multiplication vs trafo methods"
        from pyx.trafo import *
        assert isEqual(rotate(72).translate(1,2), translate(1,2)*rotate(72)), \
               "trafo.translate not consistent with multiplication result"
        assert isEqual(mirror(20)*mirror(20), mirror(20).mirror(20)), \
               "trafo.mirror not consistent with multiplication result"
        assert isEqual(translate(1,2).rotate(72).translate(-3,-1),
                       translate(-3,-1)*rotate(72)*translate(1,2)), \
                "trafo.translate/rotate not consistent with multiplication result"
   
    def testTranslateCombined(self):
        from pyx.trafo import *
        assert correctOnBasis(translate(1,0)*rotate(90), (1,1), (0,0)), \
               "wrong translate/rotate definition"
        assert correctOnBasis(rotate(90)*translate(1,0), (0,2), (-1,1)), \
               "wrong translate/rotate definition"
        assert isEqual(rotate(72,1,2),
                        translate(-1,-2).rotate(72).translate(1,2)), \
               "wrong translate/rotate definition"
        
        assert correctOnBasis(translate(1,0)*scale(0.5), (1.5, 0), (1.0,0.5)), \
               "wrong translate/scale definition"
        assert correctOnBasis(scale(0.5)*translate(1,0), (1, 0), (0.5,0.5)), \
               "wrong translate/scale definition"
                
        assert correctOnBasis(translate(1,0)*rotate(90)*scale(0.5), (1,0.5), (0.5,0)), \
               "wrong translate/rotate/scale definition"
        assert correctOnBasis(translate(1,0)*scale(0.5)*rotate(90), (1,0.5), (0.5,0)), \
               "wrong translate/rotate/scale definition"
        assert correctOnBasis(rotate(90)*scale(0.5)*translate(1,0), (0,1), (-0.5,0.5)), \
               "wrong translate/rotate/scale definition"

class UnitTestCase(unittest.TestCase):
    def testTrueUnits(self):
        from pyx.unit import *
        assert topt(t_pt(42)) == 42, "wrong unit definition"
        assert tom(t_m(42)) == 42, "wrong unit definition"

    def testUserUnits(self):
        from pyx.unit import *
        set(uscale=2)
        assert topt(pt(42)) == 84, "wrong unit definition"
        assert tom(m(42)) == 84, "wrong unit definition"
      

# construct the test suite automagically

suite = unittest.TestSuite((unittest.makeSuite(TrafoTestCase, 'test'),
                            unittest.makeSuite(UnitTestCase, 'test')))

if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite)
    



