import unittest, StringIO, ConfigParser, types

from pyx import *

class DataTestCase(unittest.TestCase):

    def testAccess(self):
        mydata = data.data(["a", "b", "b"], [[1, 2, 3], [4, 5, 6]])
        assert mydata.getcolumnno("a") == 0
        assert mydata.getcolumnno(1) == 1
        try:
            mydata.getcolumnno(3)
            assert 0, "ColumnError expected"
        except data.ColumnError: pass
        try:
            mydata.getcolumnno("b")
            assert 0, "ColumnError expected"
        except data.ColumnError: pass
        try:
            mydata.getcolumnno("c")
            assert 0, "ColumnError expected"
        except data.ColumnError: pass
        assert mydata.getcolumn("a") == [1, 4]
        assert mydata.getcolumn(1) == [2, 5]

    def testAdd(self):
        mydata = data.data(["a"], [[1], [2]])
        mydata.addcolumn("b=2*a")
        mydata.addcolumn("2*x*a", x="b")
        mydata.addcolumn("2*x", x=-1)
        assert mydata.titles == ["a", "b", None, None]
        assert mydata.data == [[1, 2.0, 4.0, 8.0], [2, 4.0, 16.0, 32.0]]
        try:
            mydata.addcolumn("2*x", x=-1, y=-2)
            assert 0, "KeyError expected"
        except KeyError: pass

        mydata = data.data(["a"], [[1], [2]])
        assert mydata._addcolumn("b=2*a") == ["a"]
        temp = mydata._addcolumn("2*x*a", x="b"); temp.sort(); assert temp == ["a", "x"]
        assert mydata._addcolumn("2*x", x=-1) == ["x"]
        assert mydata._addcolumn("2*x", x=-1, y=-2) == ["x"]
        assert mydata.titles == ["a", "b", None, None, None]
        assert mydata.data == [[1, 2.0, 4.0, 8.0, 16.0], [2, 4.0, 16.0, 32.0, 64.0]]

        x = "nothing"
        two = 2
        f = lambda x: x*x

        mydata = data.data(["a"], [[1], [2]], extern=locals())
        mydata.addcolumn("b=two*a")
        mydata.addcolumn("two*x*a", x="b")
        mydata.addcolumn("two*x", x=-1, two=0)
        mydata.addcolumn("two*x", x=-1, two="a")
        assert mydata.titles == ["a", "b", None, None, None]
        assert mydata.data == [[1, 2.0, 4.0, 4.0, 4.0], [2, 4.0, 16.0, 32.0, 64.0]]

        mydata = data.data(["a"], [[1], [2]], extern=locals())
        assert mydata._addcolumn("b=two*a") == ["a"]
        temp = mydata._addcolumn("two*x*a", x="b"); temp.sort(); assert temp == ["a", "x"]
        temp = mydata._addcolumn("two*x", x=-1, two=0); temp.sort(); assert temp == ["two", "x"]
        temp = mydata._addcolumn("two*x", x=-1, two="a"); temp.sort(); assert temp == ["two", "x"]
        assert mydata.titles == ["a", "b", None, None, None]
        assert mydata.data == [[1, 2.0, 4.0, 4.0, 4.0], [2, 4.0, 16.0, 32.0, 64.0]]

    def testFile(self):
        teststr = """#a
0
1 eins
2 "2"
3 x"x
"""
        mydata = data.datafile(StringIO.StringIO(teststr))
        assert mydata.titles == [None, "a", None]
        assert len(mydata.data) == 4
        assert mydata.data[0] == [1, 0.0, None]
        assert mydata.data[1] == [2, 1.0, "eins"]
        assert mydata.data[2] == [3, 2.0, "2"]
        assert mydata.data[3] == [4, 3.0, "x\"x"]

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
        assert sec1 == sec2

        for line in mydata.data:
            sec = line[0]
            for i in range(1, len(mydata.titles)):
                opt = mydata.titles[i]
                if type(line[i]) == types.FloatType:
                    assert configfile.getfloat(sec, opt) == line[i]
                elif type(line[i]) == types.StringType:
                    assert configfile.get(sec, opt) == line[i]
                else:
                    assert not configfile.has_option(sec, opt)

suite = unittest.TestSuite((unittest.makeSuite(DataTestCase, 'test'), ))

if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite)

