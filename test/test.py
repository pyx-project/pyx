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
sys.path[:0] = [".."]

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
        t = trafo.translation(-1,-1)*trafo.rotation(72)*trafo.translation(1,1)
        assert isEqual(t*t.inverse(), trafo.trafo()), \
                "wrong inverse definition"

    def testTranslate(self):
        assert correctOnBasis(trafo.translation(1,0),
                              (2,0), (1,1)), \
               "wrong definition of trafo.translation"
        assert correctOnBasis(trafo.translation(0,1),
                              (1,1), (0,2)), \
               "wrong definition of trafo.translation"

    def testRotate(self):
        assert correctOnBasis(trafo.rotation(90),
                              (0,1), (-1,0)), \
               "wrong definition of trafo.rotation"
        assert isEqual(trafo.rotation(360), trafo.trafo()), \
                "trafo.rotation by 360 deg is not 1"
        assert isEqual(trafo.rotation(40)*trafo.rotation(120)*
                       trafo.rotation(90)*trafo.rotation(110),
                        trafo.trafo()), \
                "successive multiplication by 360 degrees does not yield 1"

    def testMirror(self):
        "trafo.mirroring two times must yield 1 and -mirror(phi)=mirror(phi+180)"
        assert isEqual(trafo.mirroring(20)*trafo.mirroring(20),
                       trafo.trafo()), \
                "trafo.mirroring not idempotent"
        assert isEqual(trafo.mirroring(20),
                       trafo.mirroring(180+20)), \
                "trafo.mirroring by 20 degrees unequal to trafo.mirroring by 180+20 degrees"

    def testScale(self):
        assert correctOnBasis(trafo.scaling(0.5),
                              (0.5,0), (0, 0.5)), \
               "wrong definition of trafo.scaling"
        assert correctOnBasis(trafo.scaling(0.5, 0.2),
                              (0.5,0), (0, 0.2)), \
               "wrong definition of trafo.scaling"
        assert isEqual(trafo.scaling(2,3)*trafo.scaling(1/2.0, 1/3.0),
                       trafo.trafo()), \
                "trafo.scaling definition wrong"

    def testSlant(self):
        assert correctOnBasis(trafo.slant(0.5),
                              (1,0), (0.5, 1)), \
               "wrong definition of trafo.slant"
        assert isEqual(trafo.slant(2)*trafo.slant(-2),
                       trafo.trafo()), \
                "trafo.slant definition wrong"
   
    def testMultVsMethods(self):
        "test multiplication vs trafo methods"
        assert isEqual(trafo.rotation(72).translate(1,2),
                       trafo.translation(1,2)*trafo.rotation(72)), \
               "trafo.translate not consistent with multiplication result"
        assert isEqual(trafo.mirroring(20)*trafo.mirroring(20),
                       trafo.mirroring(20).mirror(20)), \
               "trafo.mirror not consistent with multiplication result"
        assert isEqual(trafo.translation(1,2).rotate(72).translate(-3,-1),
                       trafo.translation(-3,-1)*
                       trafo.rotation(72)*
                       trafo.translation(1,2)), \
                "trafo.translate/rotate not consistent with multiplication result"
   
    def testTranslateCombined(self):
        assert correctOnBasis(trafo.translation(1,0)*trafo.rotation(90),
                              (1,1), (0,0)), \
               "wrong trafo.translation/trafo.rotation definition"
        assert correctOnBasis(trafo.rotation(90)*trafo.translation(1,0),
                              (0,2), (-1,1)), \
               "wrong trafo.translation/trafo.rotation definition"
        assert isEqual(trafo.rotation(72,1,2),
                       trafo.translation(-1,-2).rotate(72).translate(1,2)), \
               "wrong translate/rotate definition"
        
        assert correctOnBasis(trafo.translation(1,0)*
                              trafo.scaling(0.5),
                              (1.5, 0), (1.0,0.5)), \
               "wrong trafo.translation/trafo.scaling definition"
        assert correctOnBasis(trafo.scaling(0.5)*
                              trafo.translation(1,0),
                              (1, 0), (0.5,0.5)), \
               "wrong trafo.translation/trafo.scaling definition"
                
        assert correctOnBasis(trafo.translation(1,0)*
                              trafo.rotation(90)*
                              trafo.scaling(0.5),
                              (1,0.5), (0.5,0)), \
               "wrong trafo.translation/trafo.rotation/trafo.scaling definition"
        assert correctOnBasis(trafo.translation(1,0)*
                              trafo.scaling(0.5)*
                              trafo.rotation(90),
                              (1,0.5), (0.5,0)), \
               "wrong trafo.translation/trafo.rotation/trafo.scaling definition"
        assert correctOnBasis(trafo.rotation(90)*trafo.scaling(0.5)*trafo.translation(1,0),
                              (0,1), (-0.5,0.5)), \
               "wrong trafo.translation/trafo.rotation/trafo.scaling definition"

class UnitTestCase(unittest.TestCase):
    def testTrueUnits(self):
        assert unit.topt(unit.t_pt(42)) == 42, "wrong unit definition"
        assert unit.tom(unit.t_m(42)) == 42, "wrong unit definition"

    def testUserUnits(self):
        unit.set(uscale=2)
        assert unit.topt(unit.pt(42)) == 84, "wrong unit definition"
        assert unit.tom(unit.m(42)) == 84, "wrong unit definition"
      

# construct the test suite automagically

suite = unittest.TestSuite((unittest.makeSuite(TrafoTestCase, 'test'),
                            unittest.makeSuite(UnitTestCase, 'test')))

if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite)
    



