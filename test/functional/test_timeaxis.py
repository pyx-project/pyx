#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

try:
    import datetime
except:
    print "datetime import failed (needs python 2.3+) -> test skiped"
else:
    import time
    from pyx import *
    from pyx.graph import timeaxis

    d = data.datafile("data/timedata")
    d = data.data([[datetime.datetime(*(time.strptime(x[1])[:6])), x[2]] for x in d.data])

    g = graph.type.graphxy(height=5, x=timeaxis.timeaxis(manualticks=[timeaxis.timetick(2003, 8, 12),
                                                          timeaxis.timetick(2003, 8, 13),
                                                          timeaxis.timetick(2003, 8, 14),
                                                          timeaxis.timetick(2003, 8, 15),
                                                          timeaxis.timetick(2003, 8, 16)],
                                                    texter=timeaxis.timetexter("%d %b"),
                                                    painter=graph.painter.axispainter()))
    g.plot(graph.data.data(d, x=0, y=1))
    g.writeEPSfile("test_timeaxis")

