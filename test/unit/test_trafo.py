import sys
if sys.path[0] != "../..":
    sys.path.insert(0, "../..")

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
    esx = t.apply(1 * unit.t_cm, 0)
    esy = t.apply(0, 1 * unit.t_cm)

    esx = unit.tocm(esx[0]), unit.tocm(esx[1])
    esy = unit.tocm(esy[0]), unit.tocm(esy[1])

#    print "  (1,0) => (%f, %f)" % (esx[0], esx[1])
#    print "  (0,1) => (%f, %f)" % (esy[0], esy[1])

    return max(map(abs,[esx[0]-tesx[0], esx[1]-tesx[1],
                        esy[0]-tesy[0], esy[1]-tesy[1]]))<1e-7


class TrafoTestCase(unittest.TestCase):

    def testInverse(self):
        "t*t.inverse()=1"
        t = trafo.translate(-1,-1)*trafo.rotate(72)*trafo.translate(1,1)
        assert isEqual(t*t.inverse(), trafo.trafo()), \
                "wrong inverse definition"

    def testTranslate(self):
        assert correctOnBasis(trafo.translate(1,0),
                              (2,0), (1,1)), \
               "wrong definition of trafo.translation"
        assert correctOnBasis(trafo.translate(0,1),
                              (1,1), (0,2)), \
               "wrong definition of trafo.translation"

    def testRotate(self):
        assert correctOnBasis(trafo.rotate(90),
                              (0, 1), (-1, 0)), \
               "wrong definition of trafo.rotation"
        assert isEqual(trafo.rotate(360), trafo.trafo()), \
                "trafo.rotation by 360 deg is not 1"
        assert isEqual(trafo.rotate(40)*trafo.rotate(120)*
                       trafo.rotate(90)*trafo.rotate(110),
                        trafo.trafo()), \
                "successive multiplication by 360 degrees does not yield 1"

    def testMirror(self):
        "trafo.mirroring two times must yield 1 and -mirror(phi)=mirror(phi+180)"
        assert isEqual(trafo.mirror(20)*trafo.mirror(20),
                       trafo.trafo()), \
                "trafo.mirroring not idempotent"
        assert isEqual(trafo.mirror(20),
                       trafo.mirror(180+20)), \
                "trafo.mirroring by 20 degrees unequal to trafo.mirroring by 180+20 degrees"

    def testScale(self):
        assert correctOnBasis(trafo.scale(0.5),
                              (0.5,0), (0, 0.5)), \
               "wrong definition of trafo.scaling"
        assert correctOnBasis(trafo.scale(0.5, 0.2),
                              (0.5,0), (0, 0.2)), \
               "wrong definition of trafo.scaling"
        assert isEqual(trafo.scale(2,3)*trafo.scale(1/2.0, 1/3.0),
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
        assert isEqual(trafo.rotate(72).translated(1,2),
                       trafo.translate(1,2)*trafo.rotate(72)), \
               "trafo.translate not consistent with multiplication result"
        assert isEqual(trafo.mirror(20)*trafo.mirror(20),
                       trafo.mirror(20).mirrored(20)), \
               "trafo.mirror not consistent with multiplication result"
        assert isEqual(trafo.translate(1,2).rotated(72).translated(-3,-1),
                       trafo.translate(-3,-1)*
                       trafo.rotate(72)*
                       trafo.translate(1,2)), \
                "trafo.translate/rotate not consistent with multiplication result"

    def testTranslateCombined(self):
        assert correctOnBasis(trafo.translate(1,0)*trafo.rotate(90),
                              (1,1), (0,0)), \
               "wrong trafo.translation/trafo.rotation definition"
        assert correctOnBasis(trafo.rotate(90)*trafo.translate(1,0),
                              (0,2), (-1,1)), \
               "wrong trafo.translation/trafo.rotation definition"
        assert isEqual(trafo.rotate(72,1,2),
                       trafo.translate(-1,-2).rotated(72).translated(1,2)), \
               "wrong translate/rotate definition"

        assert correctOnBasis(trafo.translate(1,0)*
                              trafo.scale(0.5),
                              (1.5, 0), (1.0,0.5)), \
               "wrong trafo.translation/trafo.scaling definition"
        assert correctOnBasis(trafo.scale(0.5)*
                              trafo.translate(1,0),
                              (1, 0), (0.5,0.5)), \
               "wrong trafo.translation/trafo.scaling definition"

        assert correctOnBasis(trafo.translate(1,0)*
                              trafo.rotate(90)*
                              trafo.scale(0.5),
                              (1,0.5), (0.5,0)), \
               "wrong trafo.translation/trafo.rotation/trafo.scaling definition"
        assert correctOnBasis(trafo.translate(1,0)*
                              trafo.scale(0.5)*
                              trafo.rotate(90),
                              (1,0.5), (0.5,0)), \
               "wrong trafo.translation/trafo.rotation/trafo.scaling definition"
        assert correctOnBasis(trafo.rotate(90)*trafo.scale(0.5)*trafo.translate(1,0),
                              (0,1), (-0.5,0.5)), \
               "wrong trafo.translation/trafo.rotation/trafo.scaling definition"


if __name__ == "__main__":
    unittest.main()
