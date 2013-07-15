import sys
if sys.path[0] != "../..":
    sys.path.insert(0, "../..")

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

class A4(sortbeforeexclusiveattr): pass
class B4(sortbeforeexclusiveattr): pass
class C4(attr): pass


class AttrTestCase(unittest.TestCase):

    def testCheck(self):
        checkattrs([A1(), B1(), A1()], [A1, B1])
        self.failUnlessRaises(TypeError, checkattrs, [A1(), B1(), A1()], [A1, C1])

    def testMerge(self):
        a1 = A1()
        a2 = A1()
        b1 = B1()
        b2 = B1()
        c1 = C1()
        c2 = C1()
        self.failUnlessEqual(mergeattrs([a1, b2, b1, c2, a2, c1]), [a1, b2, b1, c2, a2, c1])

    def testExclusive(self):
        a1 = A2(A2)
        a2 = A2(A2)
        b1 = B2(B2)
        b2 = B2(B2)
        c1 = C2(C2)
        c2 = C2(C2)
        self.failUnlessEqual(mergeattrs([a1, b2, b1, c2, a2, c1]), [b1, a2, c1])

    def testSort(self):
        a1 = A3((B3, C3))
        a2 = A3((B3, C3))
        b1 = B3((C3,))
        b2 = B3((C3,))
        c1 = C3()
        c2 = C3()
        self.failUnlessEqual(mergeattrs([a1, b2, b1, c2, a2, c1]), [a1, a2, b2, b1, c2, c1])

    def testExclusiveSort(self):
        a1 = A4(A4, (B4, C4))
        a2 = A4(A4, (B4, C4))
        b1 = B4(B4, (C4,))
        b2 = B4(B4, (C4,))
        c1 = C4()
        c2 = C4()
        self.failUnlessEqual(mergeattrs([b2, a1, b1, c2, a2, c1]), [a2, b1, c2, c1])


if __name__ == "__main__":
    unittest.main()
