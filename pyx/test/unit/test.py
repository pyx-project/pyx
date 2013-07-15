#!/usr/bin/env python
import sys
if sys.path[0] != "../..":
    sys.path.insert(0, "../..")

import unittest

import glob

def regressionTest():
    names = [name[:-3] for name in glob.glob("test_*.py")]
    modules = list(map(__import__, names))
    load = unittest.defaultTestLoader.loadTestsFromModule
    return unittest.TestSuite(list(map(load, modules)))

if __name__ == "__main__":
    unittest.main(defaultTest="regressionTest")

