import unittest

from pyx import *
from pyx.graph import tick, rationaltexter, decimaltexter


class RationalTexterTestCase(unittest.TestCase):

    def testFrac(self):
        # TODO: test all combinations (silly work)
        ticks = [graph.tick(1, 4), graph.tick(2, 4)]
        rationaltexter(enumsuffix=r"\pi").labels(ticks)
        assert [str(tick.label) for tick in ticks] == ["{{\\pi}\\over{4}}", "{{\\pi}\\over{2}}"]
        ticks = [graph.tick(0, 3), graph.tick(3, 3), graph.tick(6, 3)]
        rationaltexter(enumsuffix=r"\pi").labels(ticks)
        assert [str(tick.label) for tick in ticks] == ["0", "\\pi", "2\\pi"]
        ticks = [graph.tick(2, 3), graph.tick(4, 5)]
        rationaltexter(enumsuffix=r"\pi", equaldenom=1).labels(ticks)
        assert [str(tick.label) for tick in ticks] == ["{{10\\pi}\\over{15}}", "{{12\\pi}\\over{15}}"]


class DecimalTexterTestCase(unittest.TestCase):

    def testDec(self):
        # TODO: test all combinations (silly work)
        ticks = [graph.tick(1, 4), graph.tick(2, 4)]
        decimaltexter().labels(ticks)
        assert [str(tick.label) for tick in ticks] == ["0.25", "0.5"]
        ticks = [graph.tick(1, 17), graph.tick(17, 17)]
        decimaltexter().labels(ticks)
        assert [str(tick.label) for tick in ticks] == [r"0.\overline{0588235294117647}", "1"]


suite = unittest.TestSuite((unittest.makeSuite(RationalTexterTestCase, 'test'),
                            unittest.makeSuite(DecimalTexterTestCase, 'test')))

if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite)

