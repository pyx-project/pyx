import sys
if sys.path[0] != "../..":
    sys.path.insert(0, "../..")

import unittest

import os
from pyx.graph import data

class DataTestCase(unittest.TestCase):

    def testList(self):
        mydata = data.list([[1, 2, 3], [4, 5, 6]], a=1, b=2)
        self.failUnlessEqual(mydata.getcolumnnumber("a"), 1)
        self.failUnlessEqual(mydata.getcolumnnumber(2), 2)
        self.failUnlessRaises(KeyError, mydata.getcolumnnumber, "c")
        self.failUnlessEqual(mydata.getcolumn("a"), [1, 4])
        self.failUnlessEqual(mydata.getcolumn(2), [2, 5])

    def testData(self):
        mydata = data.list([[1], [2]], a=1)
        mydata2 = data.data(mydata, a="2*a", b="2*$1*a", c="4*$(i)*a*$(-1)", context={"i":1})
        self.failUnlessEqual(mydata.points[0][0], 1)
        self.failUnlessEqual(mydata.points[1][0], 2)
        self.failUnlessAlmostEqual(mydata2.points[0][mydata2.columns["a"]], 2.0)
        self.failUnlessAlmostEqual(mydata2.points[1][mydata2.columns["a"]], 4.0)
        self.failUnlessAlmostEqual(mydata2.points[0][mydata2.columns["b"]], 2.0)
        self.failUnlessAlmostEqual(mydata2.points[1][mydata2.columns["b"]], 8.0)
        self.failUnlessAlmostEqual(mydata2.points[0][mydata2.columns["c"]], 4.0)
        self.failUnlessAlmostEqual(mydata2.points[1][mydata2.columns["c"]], 32.0)
        mydata3 = data.data(mydata2, a=2, b=3)
        self.failUnlessEqual(mydata3.points, mydata2.points)

        a = "nothing"
        two = 2
        f = lambda x: x*x
        mydata = data.list([[1], [2]], a=1)
        mydata2 = data.data(mydata, b="two*a", c="two*$1*a", d="f($1)", context=locals())
        self.failUnlessEqual(mydata.points[0][0], 1)
        self.failUnlessEqual(mydata.points[1][0], 2)
        self.failUnlessAlmostEqual(mydata2.points[0][mydata2.columns["b"]], 2.0)
        self.failUnlessAlmostEqual(mydata2.points[1][mydata2.columns["b"]], 4.0)
        self.failUnlessAlmostEqual(mydata2.points[0][mydata2.columns["c"]], 2.0)
        self.failUnlessAlmostEqual(mydata2.points[1][mydata2.columns["c"]], 8.0)
        self.failUnlessAlmostEqual(mydata2.points[0][mydata2.columns["d"]], 1.0)
        self.failUnlessAlmostEqual(mydata2.points[1][mydata2.columns["d"]], 4.0)

    def testFile(self):
        testfile = open("test_data.dat", "w")
        testfile.write("""#a
0
1 eins
2 "2"
3 x"x""")
        testfile.close()
        mydata = data.file("test_data.dat", a="a", b=2)
        self.failUnlessEqual(len(mydata.columns.keys()), 2)
        self.failUnlessEqual(len(mydata.points), 4)
        self.failUnlessEqual(mydata.points[0][0], 1)
        self.failUnlessEqual(mydata.points[1][0], 2)
        self.failUnlessEqual(mydata.points[2][0], 3)
        self.failUnlessEqual(mydata.points[3][0], 4)
        self.failUnlessAlmostEqual(mydata.points[0][mydata.columns["a"]], 0.0)
        self.failUnlessAlmostEqual(mydata.points[1][mydata.columns["a"]], 1.0)
        self.failUnlessAlmostEqual(mydata.points[2][mydata.columns["a"]], 2.0)
        self.failUnlessAlmostEqual(mydata.points[3][mydata.columns["a"]], 3.0)
        self.failUnlessEqual(mydata.points[0][mydata.columns["b"]], None)
        self.failUnlessEqual(mydata.points[1][mydata.columns["b"]], "eins")
        self.failUnlessEqual(mydata.points[2][mydata.columns["b"]], "2")
        self.failUnlessEqual(mydata.points[3][mydata.columns["b"]], "x\"x")
        os.unlink("test_data.dat")

    def testSec(self):
        testfile = open("test_data.dat", "w")
        testfile.write("""[sec1]
opt1=bla1
opt2=bla2
val=1
val=2

[sec2]
opt1=bla1
opt2=bla2
val=2
val=1

[sec1]
opt3=bla3""")
        testfile.close()
        mydata = data.conffile("test_data.dat", a="opt1", b="opt2", c="opt3", d="val")
        self.failUnlessEqual(len(mydata.columns.keys()), 4)
        self.failUnlessEqual(len(mydata.points), 2)
        self.failUnlessEqual(mydata.points[0][0], "sec1")
        self.failUnlessEqual(mydata.points[1][0], "sec2")
        self.failUnlessEqual(mydata.points[0][mydata.columns["a"]], "bla1")
        self.failUnlessEqual(mydata.points[0][mydata.columns["b"]], "bla2")
        self.failUnlessEqual(mydata.points[0][mydata.columns["c"]], "bla3")
        self.failUnlessAlmostEqual(mydata.points[0][mydata.columns["d"]], 2.0)
        self.failUnlessEqual(mydata.points[1][mydata.columns["a"]], "bla1")
        self.failUnlessEqual(mydata.points[1][mydata.columns["b"]], "bla2")
        self.failUnlessEqual(mydata.points[1][mydata.columns["c"]], None)
        self.failUnlessAlmostEqual(mydata.points[1][mydata.columns["d"]], 1.0)
        os.unlink("test_data.dat")


if __name__ == "__main__":
    unittest.main()
