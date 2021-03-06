import sys
if sys.path[0] != "../..":
    sys.path.insert(0, "../..")

import unittest

import io
from pyx.graph import data

class DataTestCase(unittest.TestCase):

    def testPoints(self):
        mydata = data.points([[1, 2, 3], [4, 5, 6]], a=1, b=2)
        self.assertEqual(mydata.columndata[0], [1, 2])
        self.assertEqual(mydata.columns["a"], [1, 4])
        self.assertEqual(mydata.columndata[2], [2, 5])
        self.assertEqual("c" in list(mydata.columns.keys()), 0)

    def testValues(self):
        mydata = data.values(a=[1, 4])
        self.assertEqual(mydata.columns["a"], [1, 4])
        self.assertEqual("c" in list(mydata.columns.keys()), 0)

    def testData(self):
        mydata = data.points([[1], [2]], a=1)
        mydata2 = data.data(mydata, a="2*a", b="2*$1*a", c="4*$(i)*a*$(-1)", context={"i":1})
        self.assertEqual(mydata.columns["a"], [1, 2])
        self.assertAlmostEqual(mydata2.columns["a"][0], 2.0)
        self.assertAlmostEqual(mydata2.columns["a"][1], 4.0)
        self.assertAlmostEqual(mydata2.columns["b"][0], 2.0)
        self.assertAlmostEqual(mydata2.columns["b"][1], 8.0)
        self.assertAlmostEqual(mydata2.columns["c"][0], 4.0)
        self.assertAlmostEqual(mydata2.columns["c"][1], 32.0)
        mydata3 = data.data(mydata2, a="b", b="2*c")
        self.assertEqual(mydata3.columns["a"], mydata2.columns["b"])
        self.assertAlmostEqual(mydata3.columns["b"][0], 2*mydata2.columns["c"][0])
        self.assertAlmostEqual(mydata3.columns["b"][1], 2*mydata2.columns["c"][1])

        a = "nothing"
        two = 2
        f = lambda x: x*x
        mydata = data.points([[1], [2]], a=1)
        mydata2 = data.data(mydata, b="two*a", c="two*$1*a", d="f($1)", context=locals())
        self.assertEqual(mydata.columndata[0], [1, 2])
        self.assertAlmostEqual(mydata2.columns["b"][0], 2.0)
        self.assertAlmostEqual(mydata2.columns["b"][1], 4.0)
        self.assertAlmostEqual(mydata2.columns["c"][0], 2.0)
        self.assertAlmostEqual(mydata2.columns["c"][1], 8.0)
        self.assertAlmostEqual(mydata2.columns["d"][0], 1.0)
        self.assertAlmostEqual(mydata2.columns["d"][1], 4.0)

    def testFile(self):
        testfile = io.StringIO("""#a
0
1 eins
2 "2"
3 x"x""")
        mydata = data.file(testfile, row=0, a="a", b=2)
        self.assertEqual(mydata.columns["row"], [1, 2, 3, 4])
        self.assertAlmostEqual(mydata.columns["a"][0], 0.0)
        self.assertAlmostEqual(mydata.columns["a"][1], 1.0)
        self.assertAlmostEqual(mydata.columns["a"][2], 2.0)
        self.assertAlmostEqual(mydata.columns["a"][3], 3.0)
        self.assertEqual(mydata.columns["b"][0], None)
        self.assertEqual(mydata.columns["b"][1], "eins")
        self.assertEqual(mydata.columns["b"][2], "2")
        self.assertEqual(mydata.columns["b"][3], "x\"x")
        testfile = io.StringIO("""#a
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
        self.assertEqual(mydata.columns["row"], [4, 6, 8])
        self.assertEqual(mydata.title, "title")

    def testSec(self):
        testfile = io.StringIO("""[sec1]
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
        self.assertEqual(mydata.columns["sec"], ["sec1", "sec2"])
        self.assertEqual(mydata.columns["a"], ["a1", "a4"])
        self.assertEqual(mydata.columns["b"], ["a2", "a5"])
        self.assertEqual(mydata.columns["c"], ["a3", None])
        self.assertAlmostEqual(mydata.columns["d"][0], 2.0)
        self.assertAlmostEqual(mydata.columns["d"][1], 1.0)

    def testParamfunction(self):
        mydata = data.paramfunction("k", 0, 9, "x, y = k, -k", points=10)
        for i in range(10):
            self.assertEqual(mydata.columns["x"][i], i)
            self.assertEqual(mydata.columns["y"][i], -i)


if __name__ == "__main__":
    unittest.main()
