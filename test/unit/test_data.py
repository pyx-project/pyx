import sys
if sys.path[0] != "../..":
    sys.path.insert(0, "../..")

import unittest

import StringIO, ConfigParser, types
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

#        a = "nothing"
#        two = 2
#        f = lambda x: x*x
#        mydata = data.data([[1], [2]], ["a"])
#        mydata.addcolumn("b=two*a", context=locals())
#        mydata.addcolumn("two*$(-1)*a", context=locals())
#        mydata.addcolumn("two*$(-1)*a", context=locals())
#        mydata.addcolumn("f($(-1))", context=locals())
#        self.failUnlessEqual(mydata.titles, ["a", "b", None, None, None])
#        self.failUnlessEqual(mydata.data, [[1, 2.0, 4.0, 8.0, 64.0], [2, 4.0, 16.0, 64.0, 4096.0]])
#
#    def testFile(self):
#        teststr = """#a
#0
#1 eins
#2 "2"
#3 x"x
#"""
#        mydata = data.datafile(StringIO.StringIO(teststr))
#        self.failUnlessEqual(mydata.titles, [None, "a", None])
#        self.failUnlessEqual(len(mydata.data), 4)
#        self.failUnlessEqual(mydata.data[0], [1, 0.0, None])
#        self.failUnlessEqual(mydata.data[1], [2, 1.0, "eins"])
#        self.failUnlessEqual(mydata.data[2], [3, 2.0, "2"])
#        self.failUnlessEqual(mydata.data[3], [4, 3.0, "x\"x"])

#    def testSec(self):
#        teststr = """[sec1]
#opt1=bla1
#opt2=bla2
#val=1
#val=2
#
#[sec2]
#opt1=bla1
#opt2=bla2
#val=2
#val=1
#
#[sec1]
#opt3=bla3"""
#
#        mydata = data.sectionfile(StringIO.StringIO(teststr))
#
#        configfile = ConfigParser.ConfigParser()
#        configfile.optionxform = str
#        configfile.readfp(StringIO.StringIO(teststr))
#
#        sec1 = list(mydata.getcolumn("section"))
#        sec1.sort()
#        sec2 = list(configfile.sections())
#        sec2.sort()
#        self.failUnlessEqual(sec1, sec2)
#
#        for line in mydata.data:
#            sec = line[0]
#            for i in range(1, len(mydata.titles)):
#                opt = mydata.titles[i]
#                if type(line[i]) == types.FloatType:
#                    self.failUnlessEqual(configfile.getfloat(sec, opt), line[i])
#                elif type(line[i]) == types.StringType:
#                    self.failUnlessEqual(configfile.get(sec, opt), line[i])
#                else:
#                    self.failIf(configfile.has_option(sec, opt))


if __name__ == "__main__":
    unittest.main()
