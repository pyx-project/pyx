import sys
if sys.path[0] != "../..":
    sys.path.insert(0, "../..")

import unittest

import StringIO, ConfigParser, types
from pyx import *

class DataTestCase(unittest.TestCase):

    def testAccess(self):
        mydata = data.data([[1, 2, 3], [4, 5, 6]], ["a", "b", "b"])
        self.failUnlessEqual(mydata.getcolumnno("a"), 0)
        self.failUnlessEqual(mydata.getcolumnno(1), 1)
        self.failUnlessRaises(data.ColumnError, mydata.getcolumnno, 3)
        self.failUnlessRaises(data.ColumnError, mydata.getcolumnno, "b")
        self.failUnlessRaises(data.ColumnError, mydata.getcolumnno, "c")
        self.failUnlessEqual(mydata.getcolumn("a"), [1, 4])
        self.failUnlessEqual(mydata.getcolumn(1), [2, 5])

    def testAdd(self):
        mydata = data.data([[1], [2]], ["a"])
        mydata.addcolumn("b=2*a")
        mydata.addcolumn("2*$1*a")
        #mydata.addcolumn("2*$(i)*a", context={"i":1}) # not supported
        self.failUnlessEqual(mydata.titles, ["a", "b", None])
        self.failUnlessEqual(mydata.data, [[1, 2.0, 4.0], [2, 4.0, 16.0]])

        a = "nothing"
        two = 2
        f = lambda x: x*x
        mydata = data.data([[1], [2]], ["a"])
        mydata.addcolumn("b=two*a", context=locals())
        mydata.addcolumn("two*$(-1)*a", context=locals())
        mydata.addcolumn("two*$(-1)*a", context=locals())
        mydata.addcolumn("f($(-1))", context=locals())
        self.failUnlessEqual(mydata.titles, ["a", "b", None, None, None])
        self.failUnlessEqual(mydata.data, [[1, 2.0, 4.0, 8.0, 64.0], [2, 4.0, 16.0, 64.0, 4096.0]])

    def testFile(self):
        teststr = """#a
0
1 eins
2 "2"
3 x"x
"""
        mydata = data.datafile(StringIO.StringIO(teststr))
        self.failUnlessEqual(mydata.titles, [None, "a", None])
        self.failUnlessEqual(len(mydata.data), 4)
        self.failUnlessEqual(mydata.data[0], [1, 0.0, None])
        self.failUnlessEqual(mydata.data[1], [2, 1.0, "eins"])
        self.failUnlessEqual(mydata.data[2], [3, 2.0, "2"])
        self.failUnlessEqual(mydata.data[3], [4, 3.0, "x\"x"])

    def testSec(self):
        teststr = """[sec1]
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
opt3=bla3"""

        mydata = data.sectionfile(StringIO.StringIO(teststr))

        configfile = ConfigParser.ConfigParser()
        configfile.optionxform = str
        configfile.readfp(StringIO.StringIO(teststr))

        sec1 = list(mydata.getcolumn("section"))
        sec1.sort()
        sec2 = list(configfile.sections())
        sec2.sort()
        self.failUnlessEqual(sec1, sec2)

        for line in mydata.data:
            sec = line[0]
            for i in range(1, len(mydata.titles)):
                opt = mydata.titles[i]
                if type(line[i]) == types.FloatType:
                    self.failUnlessEqual(configfile.getfloat(sec, opt), line[i])
                elif type(line[i]) == types.StringType:
                    self.failUnlessEqual(configfile.get(sec, opt), line[i])
                else:
                    self.failIf(configfile.has_option(sec, opt))


if __name__ == "__main__":
    unittest.main()
