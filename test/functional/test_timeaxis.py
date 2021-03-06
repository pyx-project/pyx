#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

import time, datetime
from pyx import *
from pyx.graph.axis import timeaxis
from pyx.graph import data

d = data.file("data/timedata", date=1, value=2)
d = data.points([[datetime.datetime(*(time.strptime(date)[:6])), value] for date, value in zip(d.columns["date"], d.columns["value"])], x=1, y=2)

g = graph.graphxy(height=5, x=timeaxis.timeaxis(manualticks=[timeaxis.timetick(2003, 8, 12),
                                                             timeaxis.timetick(2003, 8, 13),
                                                             timeaxis.timetick(2003, 8, 14),
                                                             timeaxis.timetick(2003, 8, 15),
                                                             timeaxis.timetick(2003, 8, 16)],
                                                texter=timeaxis.timetexter("%d %b")))
g.plot(d)
g.writeEPSfile("test_timeaxis")
g.writePDFfile("test_timeaxis")
g.writeSVGfile("test_timeaxis")

