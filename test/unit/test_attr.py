import unittest

import pyx
from pyx.attr import *

class A1(attr): pass
class B1(attr): pass
class C1(attr): pass

class A2(exclusiveattr): pass
class B2(exclusiveattr): pass
class C2(exclusiveattr): pass

class A3(sortbeforeattr): pass
class B3(sortbeforeattr): pass
class C3(attr): pass


class AttrTestCase(unittest.TestCase):

    def testCheck(self):
        checkattrs([A1(), B1(), A1()], [A1, B1])
        try:
            checkattrs([A1(), B1(), A1()], [A1, C1])
            assert 0, "should have failed"
        except TypeError:
            pass

    def testMerge(self):
        a1 = A1()
        a2 = A1()
        b1 = B1()
        b2 = B1()
        c1 = C1()
        c2 = C1()
        assert mergeattrs([a1, b2, b1, c2, a2, c1]) == [a1, b2, b1, c2, a2, c1]

    def testExclusive(self):
        a1 = A2(A2)
        a2 = A2(A2)
        b1 = B2(B2)
        b2 = B2(B2)
        c1 = C2(C2)
        c2 = C2(C2)
        assert mergeattrs([a1, b2, b1, c2, a2, c1]) == [b1, a2, c1]

    def testSort(self):
        a1 = A3((B3, C3))
        a2 = A3((B3, C3))
        b1 = B3((C3))
        b2 = B3((C3))
        c1 = C3()
        c2 = C3()
        assert mergeattrs([a1, b2, b1, c2, a2, c1]) == [a1, a2, b2, b1, c2, c1]


suite = unittest.TestSuite((unittest.makeSuite(AttrTestCase, 'test'), ))

if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite)

