import unittest

from pyx import *
from pyx.helper import *


class AttrTestCase(unittest.TestCase):

    def testAttrs(self):
        class a: pass
        class b: pass
        class c(b): pass
        class A: pass
        class B: pass
        class C(B): pass
        checkattr((a(), A(), A()), (a, b), (A, B))
        checkattr((c(), A(), A()), (a, b), (A, B))
        try:
            checkattr((a(), A(), A(), a()), (a, b), (A, B))
            assert 0, "checkattr failed"
        except AttrError: pass
        try:
            checkattr((c(), A(), A(), c()), (a, b), (A, B))
            assert 0, "checkattr failed"
        except AttrError: pass
        x1, x2 = a(), a()
        assert getattrs((x1, A(), A()), a) == [x1], "getattrs failed"
        assert getattrs((x1, A(), A(), x2), a) == [x1, x2], "getattrs failed"
        assert getattr((x1, A(), A()), a) == x1, "getattr failed"
        try:
            getattr((x1, A(), A(), x2), a)
            assert 0, "getattr failed"
        except AttrError: pass
        assert getfirstattr((x1, A(), A(), x2), a) == x1, "getfirstattr failed"
        assert getlastattr((x1, A(), A(), x2), a) == x2, "getlastattr failed"
        assert getattr((x1, A(), A()), a, x2) == x1, "getattr failed"
        assert getattr((A(), A()), a, x2) == x2, "getattr failed"


suite = unittest.TestSuite((unittest.makeSuite(AttrTestCase, 'test'),))

if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite)

