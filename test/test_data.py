#!/usr/bin/env python
import sys, math
sys.path[:0] = [".."]

from pyx import *

mydata = data.sectionfile("test_data.conf")
print mydata.titles
print mydata.data

