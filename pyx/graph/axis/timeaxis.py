import datetime
from pyx.graph.axis import axis, rater, style

"""some experimental code for creating a time axis
- it needs python 2.3 to be used (it is based on the new datetime data type)
- a timeaxis is always based on the datetime data type (there is no distinction between times and dates)
"""

class _timemap:
    "time axis mapping based "

    __implements__ = axis._Imap

    def setbasepoints(self, basepoints):
        (self.x1, self.y1), (self.x2, self.y2) = basepoints
        self.dx = self.x2-self.x1
        self.dy = self.y2-self.y1
        if self.dx < datetime.timedelta(0):
            raise RuntimeError("reverse time axis is not expected to work") # and should not happen

    def convert(self, x):
        # XXX float division of timedelta instances
        def mstimedelta(td):
            "return the timedelta in microseconds"
            return td.microseconds + 1000000*(td.seconds + 3600*24*td.days)
        return self.y1 + self.dy * mstimedelta(x - self.x1) / float(mstimedelta(self.dx))
        # we could store float(mstimedelta(self.dx)) instead of self.dx, but
        # I prefer a different solution (not based on huge integers) for the
        # future

    def invert(self, y):
        f = (y - self.y1) / float(self.dy)
        return self.x1 + datetime.timedelta(days=f*self.dx.days, seconds=f*self.dx.seconds, microseconds=f*self.dx.seconds)


class timetick(datetime.datetime):

    def __init__(self, year, month, day, ticklevel=0, labellevel=0, label=None, labelattrs=[], **kwargs):
        datetime.datetime.__init__(self, year, month, day, **kwargs)
        self.ticklevel = ticklevel
        self.labellevel = labellevel
        self.label = label
        self.labelattrs = labelattrs[:]

    def merge(self, other):
        if self.ticklevel is None or (other.ticklevel is not None and other.ticklevel < self.ticklevel):
            self.ticklevel = other.ticklevel
        if self.labellevel is None or (other.labellevel is not None and other.labellevel < self.labellevel):
            self.labellevel = other.labellevel


class timetexter:

    def __init__(self, format="%c"):
        self.format = format

    def labels(self, ticks):
        for tick in ticks:
            if tick.labellevel is not None and tick.label is None:
                tick.label = tick.strftime(self.format)


class timeaxis(axis._axis, _timemap):

     def __init__(self, parter=None, rater=rater.axisrater(), **args):
        axis._axis.__init__(self, divisor=None, **args)
        if self.fixmin and self.fixmax:
            self.relsize = self.max - self.min
            self.relsize = 0.000001*self.relsize.microseconds + self.relsize.seconds + 60*60*24.0*self.relsize.days
        self.parter = parter
        self.rater = rater


