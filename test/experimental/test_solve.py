import unittest, operator

from solve import scalar, vector, matrix, solver

class ScalarTestCase(unittest.TestCase):

    def testInit(self):
        self.failUnlessRaises(RuntimeError, scalar, "")
        self.failUnlessRaises(RuntimeError, scalar, 1j)
        self.failUnlessEqual(str(scalar()), "unnamed_scalar")
        self.failUnlessEqual(str(scalar(name="s")), "s")
        self.failUnlessEqual(str(scalar(1)), "unnamed_scalar{=1.0}")
        self.failUnlessEqual(str(scalar(-1, name="s")), "s{=-1.0}")

    def testMath(self):
        self.failUnlessEqual(str(-scalar(name="s")), "unnamed_scalar{=-1.0} * s")
        self.failUnlessEqual(str(scalar(name="s") + scalar(name="t")), "s  +  t")
        self.failUnlessEqual(str(scalar(name="s") + 1), "s  +  unnamed_scalar{=1.0}")
        self.failUnlessEqual(str(1 + scalar(name="s")), "s  +  unnamed_scalar{=1.0}")
        self.failUnlessEqual(str(scalar(name="s") - scalar(name="t")), "unnamed_scalar{=-1.0} * t  +  s")
        self.failUnlessEqual(str(1 - scalar(name="s")), "unnamed_scalar{=-1.0} * s  +  unnamed_scalar{=1.0}")
        self.failUnlessEqual(str(2 * scalar(name="s")), "s * unnamed_scalar{=2.0}")
        self.failUnlessEqual(str(scalar(name="s") * 2), "s * unnamed_scalar{=2.0}")
        self.failUnlessEqual(str(scalar(name="s") * scalar(name="t")), "s * t")
        self.failUnlessEqual(str((scalar(name="s") + scalar(name="t")) * 2), "s * unnamed_scalar{=2.0}  +  t * unnamed_scalar{=2.0}")
        self.failUnlessEqual(str(scalar(name="s") / 2.0), "unnamed_scalar{=0.5} * s")
        self.failUnlessEqual(str(scalar(name="s") / 2), "unnamed_scalar{=0.0} * s") # integer logic!
        self.failUnlessEqual(str((scalar(name="s") + scalar(name="t")) / 2.0), "unnamed_scalar{=0.5} * s  +  unnamed_scalar{=0.5} * t")
        self.failUnlessRaises(TypeError, lambda: 2 / scalar())
        self.failUnlessRaises(TypeError, lambda: scalar() / scalar())
        self.failUnlessRaises(TypeError, lambda: vector(1) / scalar())
        self.failUnlessRaises(TypeError, lambda: ((scalar() + scalar()) / scalar()))
        self.failUnlessRaises(TypeError, lambda: (vector(1) + vector(1)) / scalar())

    def testAccess(self):
        s = scalar()
        self.failUnlessEqual(s.is_set(), 0)
        self.failUnlessRaises(RuntimeError, s.get)
        self.failUnlessRaises(RuntimeError, float, s)
        s.set(2)
        self.failUnlessEqual(s.is_set(), 1)
        self.failUnlessAlmostEqual(s.get(), 2.0)
        self.failUnlessAlmostEqual(float(s), 2.0)
        self.failUnlessRaises(RuntimeError, s.set, 3)
        self.failUnlessEqual(s.is_set(), 1)
        self.failUnlessAlmostEqual(s.get(), 2.0)
        self.failUnlessAlmostEqual(float(s), 2.0)

        s = scalar(2)
        self.failUnlessEqual(scalar(2).is_set(), 1)
        self.failUnlessAlmostEqual(s.get(), 2.0)
        self.failUnlessAlmostEqual(float(s), 2.0)
        self.failUnlessRaises(RuntimeError, s.set, 3)
        self.failUnlessEqual(s.is_set(), 1)
        self.failUnlessAlmostEqual(s.get(), 2.0)
        self.failUnlessAlmostEqual(float(s), 2.0)


class VectorTestCase(unittest.TestCase):

    def testInit(self):
        self.failUnlessRaises(RuntimeError, vector, 0, 0)
        self.failUnlessEqual(str(vector(2)), "unnamed_vector{=(unnamed_vector[0], unnamed_vector[1])}")
        self.failUnlessEqual(str(vector([1, 2])), "unnamed_vector{=(unnamed_vector[0]{=1.0}, unnamed_vector[1]{=2.0})}")
        self.failUnlessEqual(str(vector(3, "a")), "a{=(a[0], a[1], a[2])}")
        self.failUnlessEqual(str(vector([3, 2, 1], "a")), "a{=(a[0]{=3.0}, a[1]{=2.0}, a[2]{=1.0})}")

    def testAccess(self):
        a = vector(2)
        self.failUnlessEqual(str(a), "unnamed_vector{=(unnamed_vector[0], unnamed_vector[1])}")
        self.failUnlessEqual(a[0].is_set(), 0)
        self.failUnlessEqual(a.x.is_set(), 0)
        self.failUnlessEqual(a[1].is_set(), 0)
        self.failUnlessEqual(a.y.is_set(), 0)
        self.failUnlessRaises(IndexError, operator.__getitem__, a, 2)
        self.failUnlessRaises(IndexError, getattr, a, "z")

        a[0].set(2)
        self.failUnlessEqual(str(a), "unnamed_vector{=(unnamed_vector[0]{=2.0}, unnamed_vector[1])}")
        self.failUnlessAlmostEqual(a[0].get(), 2.0)
        self.failUnlessAlmostEqual(float(a[0]), 2.0)
        self.failUnlessAlmostEqual(a.x.get(), 2.0)
        self.failUnlessAlmostEqual(float(a.x), 2.0)
        self.failUnlessRaises(RuntimeError, a[1].get)
        self.failUnlessRaises(RuntimeError, float, a[1])
        self.failUnlessRaises(RuntimeError, a.y.get)
        self.failUnlessRaises(RuntimeError, float, a.y)
        self.failUnlessEqual(a[0].is_set(), 1)
        self.failUnlessEqual(a.x.is_set(), 1)
        self.failUnlessEqual(a[1].is_set(), 0)
        self.failUnlessEqual(a.y.is_set(), 0)
        self.failUnlessRaises(RuntimeError, a[0].set, 3)
        self.failUnlessAlmostEqual(a[0].get(), 2.0)
        self.failUnlessAlmostEqual(float(a[0]), 2.0)
        self.failUnlessAlmostEqual(a.x.get(), 2.0)
        self.failUnlessAlmostEqual(float(a.x), 2.0)
        self.failUnlessRaises(RuntimeError, a[1].get)
        self.failUnlessRaises(RuntimeError, float, a[1])
        self.failUnlessRaises(RuntimeError, a.y.get)
        self.failUnlessRaises(RuntimeError, float, a.y)
        self.failUnlessEqual(a[0].is_set(), 1)
        self.failUnlessEqual(a.x.is_set(), 1)
        self.failUnlessEqual(a[1].is_set(), 0)
        self.failUnlessEqual(a.y.is_set(), 0)

        a[1].set(3)
        self.failUnlessEqual(str(a), "unnamed_vector{=(unnamed_vector[0]{=2.0}, unnamed_vector[1]{=3.0})}")
        self.failUnlessAlmostEqual(a[0].get(), 2.0)
        self.failUnlessAlmostEqual(float(a[0]), 2.0)
        self.failUnlessAlmostEqual(a.x.get(), 2.0)
        self.failUnlessAlmostEqual(float(a.x), 2.0)
        self.failUnlessAlmostEqual(a[1].get(), 3.0)
        self.failUnlessAlmostEqual(float(a[1]), 3.0)
        self.failUnlessAlmostEqual(a.y.get(), 3.0)
        self.failUnlessAlmostEqual(float(a.y), 3.0)
        self.failUnlessEqual(a[0].is_set(), 1)
        self.failUnlessEqual(a.x.is_set(), 1)
        self.failUnlessEqual(a[1].is_set(), 1)
        self.failUnlessEqual(a.y.is_set(), 1)
        self.failUnlessRaises(RuntimeError, a[0].set, 4)
        self.failUnlessAlmostEqual(a[0].get(), 2.0)
        self.failUnlessAlmostEqual(float(a[0]), 2.0)
        self.failUnlessAlmostEqual(a.x.get(), 2.0)
        self.failUnlessAlmostEqual(float(a.x), 2.0)
        self.failUnlessAlmostEqual(a[1].get(), 3.0)
        self.failUnlessAlmostEqual(float(a[1]), 3.0)
        self.failUnlessAlmostEqual(a.y.get(), 3.0)
        self.failUnlessAlmostEqual(float(a.y), 3.0)
        self.failUnlessEqual(a[0].is_set(), 1)
        self.failUnlessEqual(a.x.is_set(), 1)
        self.failUnlessEqual(a[1].is_set(), 1)
        self.failUnlessEqual(a.y.is_set(), 1)

        a = vector([1, 2, 3])
        self.failUnlessEqual(str(a.x), "unnamed_vector[0]{=1.0}")
        self.failUnlessEqual(str(a.y), "unnamed_vector[1]{=2.0}")
        self.failUnlessEqual(str(a.z), "unnamed_vector[2]{=3.0}")

    def testLen(self):
        for i in range(1, 10):
            a = vector(i)
            self.failUnlessEqual(len(a), i)
            self.failUnlessEqual(str(a), "unnamed_vector{=(" + ", ".join(["unnamed_vector[%i]" % j for j in range(i)]) + ")}")
        for i in range(1, 10):
            a = -vector(i)
            self.failUnlessEqual(len(a), i)
            self.failUnlessEqual(str(a), "unnamed_vector{=(" + ", ".join(["unnamed_scalar{=-1.0} * unnamed_vector[%i]" % j for j in range(i)]) + ")}")

    def testMath(self):
        self.failUnlessEqual(str(-vector(2, "a")), "unnamed_vector{=(unnamed_scalar{=-1.0} * a[0], unnamed_scalar{=-1.0} * a[1])}")
        self.failUnlessEqual(str(vector(2, "a") + vector(2, "b")), "unnamed_vector{=(a[0]  +  b[0], a[1]  +  b[1])}")
        self.failUnlessRaises(AttributeError, operator.__add__, vector(2), scalar())
        self.failUnlessRaises(RuntimeError, operator.__add__, vector(2), vector(3))
        self.failUnlessEqual(str(vector(2, "a") - vector(2, "b")), "unnamed_vector{=(unnamed_scalar{=-1.0} * b[0]  +  a[0], unnamed_scalar{=-1.0} * b[1]  +  a[1])}")
        self.failUnlessRaises(RuntimeError, operator.__sub__, vector(2), scalar())
        self.failUnlessRaises(RuntimeError, operator.__sub__, vector(2), vector(3))
        self.failUnlessEqual(str(2 * vector(2, "a")), "unnamed_vector{=(a[0] * unnamed_scalar{=2.0}, a[1] * unnamed_scalar{=2.0})}")
        self.failUnlessEqual(str(vector(2, "a") * 2), "unnamed_vector{=(a[0] * unnamed_scalar{=2.0}, a[1] * unnamed_scalar{=2.0})}")
        self.failUnlessEqual(str(scalar(name="s") * vector(2, "a")), "unnamed_vector{=(s * a[0], s * a[1])}")
        self.failUnlessEqual(str(scalar(name="s") * (vector(2, "a") + vector(2, "b"))), "unnamed_vector{=(s * a[0]  +  s * b[0], s * a[1]  +  s * b[1])}")
        self.failUnlessEqual(str((scalar(name="s") + scalar(name="t")) * vector(2, "a")), "unnamed_vector{=(s * a[0]  +  t * a[0], s * a[1]  +  t * a[1])}")
        self.failUnlessEqual(str((scalar(name="s") + scalar(name="t")) * (vector(2, "a") + vector(2, "b"))), "unnamed_vector{=(s * a[0]  +  s * b[0]  +  t * a[0]  +  t * b[0], s * a[1]  +  s * b[1]  +  t * a[1]  +  t * b[1])}")
        self.failUnlessEqual(str(vector(2, "a") * scalar(name="s")), "unnamed_vector{=(s * a[0], s * a[1])}")
        self.failUnlessEqual(str(vector(2, "a") * vector(2, "b")), "a[0] * b[0]  +  a[1] * b[1]")
        self.failUnlessRaises(RuntimeError, operator.__mul__, vector(2, "a"), vector(3))
        self.failUnlessEqual(str(vector(2, "a") / 2.0), "unnamed_vector{=(unnamed_scalar{=0.5} * a[0], unnamed_scalar{=0.5} * a[1])}")
        self.failUnlessEqual(str(vector(2, "a") / 2), "unnamed_vector{=(unnamed_scalar{=0.0} * a[0], unnamed_scalar{=0.0} * a[1])}") # integer logic!
        self.failUnlessRaises(TypeError, lambda: scalar() / vector(1))
        self.failUnlessRaises(TypeError, lambda: vector(1) / vector(1))
        self.failUnlessRaises(TypeError, lambda: (scalar() + scalar()) / vector(1))
        self.failUnlessRaises(TypeError, lambda: (vector(1) + vector(1)) / vector(1))


class MatrixTestCase(unittest.TestCase):

    def testInit(self):
        self.failUnlessEqual(str(matrix([2, 3])), "unnamed_matrix{=((unnamed_matrix[0, 0], unnamed_matrix[0, 1], unnamed_matrix[0, 2]), (unnamed_matrix[1, 0], unnamed_matrix[1, 1], unnamed_matrix[1, 2]))}")
        self.failUnlessEqual(str(matrix([[1, 2, 3], [4, 5, 6]])), "unnamed_matrix{=((unnamed_matrix[0, 0]{=1.0}, unnamed_matrix[0, 1]{=2.0}, unnamed_matrix[0, 2]{=3.0}), (unnamed_matrix[1, 0]{=4.0}, unnamed_matrix[1, 1]{=5.0}, unnamed_matrix[1, 2]{=6.0}))}")
        self.failUnlessEqual(str(matrix([2, 3], "a")), "a{=((a[0, 0], a[0, 1], a[0, 2]), (a[1, 0], a[1, 1], a[1, 2]))}")
        self.failUnlessEqual(str(matrix([[1, 2, 3], [4, 5, 6]], "a")), "a{=((a[0, 0]{=1.0}, a[0, 1]{=2.0}, a[0, 2]{=3.0}), (a[1, 0]{=4.0}, a[1, 1]{=5.0}, a[1, 2]{=6.0}))}")

    def testMath(self):
        self.failUnlessEqual(str(-matrix([2, 2], "A")), "unnamed_matrix{=((unnamed_scalar{=-1.0} * A[0, 0], unnamed_scalar{=-1.0} * A[0, 1]), (unnamed_scalar{=-1.0} * A[1, 0], unnamed_scalar{=-1.0} * A[1, 1]))}")
        self.failUnlessEqual(str(matrix([2, 3], "A") + matrix([2, 3], "B")), "unnamed_matrix{=((A[0, 0]  +  B[0, 0], A[0, 1]  +  B[0, 1], A[0, 2]  +  B[0, 2]), (A[1, 0]  +  B[1, 0], A[1, 1]  +  B[1, 1], A[1, 2]  +  B[1, 2]))}")
        self.failUnlessEqual(str(matrix([2, 3], "A") * matrix([3, 2], "B")), "unnamed_matrix{=((A[0, 0] * B[0, 0]  +  A[0, 1] * B[1, 0]  +  A[0, 2] * B[2, 0], A[0, 0] * B[0, 1]  +  A[0, 1] * B[1, 1]  +  A[0, 2] * B[2, 1]), (A[1, 0] * B[0, 0]  +  A[1, 1] * B[1, 0]  +  A[1, 2] * B[2, 0], A[1, 0] * B[0, 1]  +  A[1, 1] * B[1, 1]  +  A[1, 2] * B[2, 1]))}")
        self.failUnlessEqual(str(matrix([2, 3], "A") * vector(3, "a")), "unnamed_vector{=(A[0, 0] * a[0]  +  A[0, 1] * a[1]  +  A[0, 2] * a[2], A[1, 0] * a[0]  +  A[1, 1] * a[1]  +  A[1, 2] * a[2])}")


if __name__ == "__main__":
    unittest.main()
