import sys
if sys.path[0] != "../..":
    sys.path.insert(0, "../..")

import unittest

import StringIO
from pyx.graph import data

class DataTestCase(unittest.TestCase):

    def testList(self):
        mydata = data.list([[1, 2, 3], [4, 5, 6]], a=1, b=2)
        self.failUnlessEqual(mydata.getcolumn(0), [1, 2])
        self.failUnlessEqual(mydata.getcolumn("a"), [1, 4])
        self.failUnlessEqual(mydata.getcolumn(2), [2, 5])
        self.failUnlessRaises(ValueError, mydata.getcolumn, "c")

    def testData(self):
        mydata = data.list([[1], [2]], a=1)
        mydata2 = data.data(mydata, a="2*a", b="2*$1*a", c="4*$(i)*a*$(-1)", context={"i":1})
        self.failUnlessEqual(mydata.getcolumn("a"), [1, 2])
        self.failUnlessAlmostEqual(mydata2.getcolumn("a")[0], 2.0)
        self.failUnlessAlmostEqual(mydata2.getcolumn("a")[1], 4.0)
        self.failUnlessAlmostEqual(mydata2.getcolumn("b")[0], 2.0)
        self.failUnlessAlmostEqual(mydata2.getcolumn("b")[1], 8.0)
        self.failUnlessAlmostEqual(mydata2.getcolumn("c")[0], 4.0)
        self.failUnlessAlmostEqual(mydata2.getcolumn("c")[1], 32.0)
        mydata3 = data.data(mydata2, a="b", b="2*c")
        self.failUnlessEqual(mydata3.getcolumn("a"), mydata2.getcolumn("b"))
        self.failUnlessAlmostEqual(mydata3.getcolumn("b")[0], 2*mydata2.getcolumn("c")[0])
        self.failUnlessAlmostEqual(mydata3.getcolumn("b")[1], 2*mydata2.getcolumn("c")[1])

        a = "nothing"
        two = 2
        f = lambda x: x*x
        mydata = data.list([[1], [2]], a=1)
        mydata2 = data.data(mydata, b="two*a", c="two*$1*a", d="f($1)", context=locals())
        self.failUnlessEqual(mydata.getcolumn(0), [1, 2])
        self.failUnlessAlmostEqual(mydata2.getcolumn("b")[0], 2.0)
        self.failUnlessAlmostEqual(mydata2.getcolumn("b")[1], 4.0)
        self.failUnlessAlmostEqual(mydata2.getcolumn("c")[0], 2.0)
        self.failUnlessAlmostEqual(mydata2.getcolumn("c")[1], 8.0)
        self.failUnlessAlmostEqual(mydata2.getcolumn("d")[0], 1.0)
        self.failUnlessAlmostEqual(mydata2.getcolumn("d")[1], 4.0)

    def testFile(self):
        testfile = StringIO.StringIO("""#a
0
1 eins
2 "2"
3 x"x""")
        mydata = data.file(testfile, row=0, a="a", b=2)
        self.failUnlessEqual(mydata.getcolumn("row"), [1, 2, 3, 4])
        self.failUnlessAlmostEqual(mydata.getcolumn("a")[0], 0.0)
        self.failUnlessAlmostEqual(mydata.getcolumn("a")[1], 1.0)
        self.failUnlessAlmostEqual(mydata.getcolumn("a")[2], 2.0)
        self.failUnlessAlmostEqual(mydata.getcolumn("a")[3], 3.0)
        self.failUnlessEqual(mydata.getcolumn("b")[0], None)
        self.failUnlessEqual(mydata.getcolumn("b")[1], "eins")
        self.failUnlessEqual(mydata.getcolumn("b")[2], "2")
        self.failUnlessEqual(mydata.getcolumn("b")[3], "x\"x")
        testfile = StringIO.StringIO("""#a
0
1
2
3
4
5
6
7
8
9""")
        mydata = data.file(testfile, title="title", skiphead=3, skiptail=2, every=2, row=0)
        self.failUnlessEqual(mydata.getcolumn("row"), [4, 6, 8])
        self.failUnlessEqual(mydata.gettitle(), "title")

    def testSec(self):
        testfile = StringIO.StringIO("""[sec1]
opt1=a1
opt2=a2
val=1
val=2

[sec2]
opt1=a4
opt2=a5
val=2
val=1

[sec1]
opt3=a3""")
        mydata = data.conffile(testfile, sec=0, a="opt1", b="opt2", c="opt3", d="val")
        self.failUnlessEqual(mydata.getcolumn("sec"), ["sec1", "sec2"])
        self.failUnlessEqual(mydata.getcolumn("a"), ["a1", "a4"])
        self.failUnlessEqual(mydata.getcolumn("b"), ["a2", "a5"])
        self.failUnlessEqual(mydata.getcolumn("c"), ["a3", None])
        self.failUnlessAlmostEqual(mydata.getcolumn("d")[0], 2.0)
        self.failUnlessAlmostEqual(mydata.getcolumn("d")[1], 1.0)

    def testParamfunction(self):
        mydata = data.paramfunction("k", 0, 9, "x, y = k, -k", points=10)
        for i in range(10):
            self.failUnlessEqual(mydata.getcolumn("x")[i], i)
            self.failUnlessEqual(mydata.getcolumn("y")[i], -i)


if __name__ == "__main__":
    unittest.main()
