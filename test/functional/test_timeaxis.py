#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

try:
    import datetime
except:
    print "datetime import failed (needs python 2.3+) -> test skiped"
else:
    import time
    from pyx import *
    import pyx.timeaxis as timeaxis

    d = data.datafile("data/timedata")
    d = data.data([[datetime.datetime(*(time.strptime(x[1])[:6])), x[2]] for x in d.data])

    g = graph.graphxy(height=5, x=timeaxis.timeaxis(), x2=None)
    g.plot(graph.data(d, x=0, y=1), timeaxis.symbol())
    g.writetofile("test_timeaxis")

