import datetime
import graph, helper

"""some experimental code for creating a time axis
- it needs python 2.3 to be used (it is based on the new datetime data type)
- a timeaxis is always based on the datetime data type (there is no distinction between times and dates)
"""

class _timemap:
    "time axis mapping based "

    __implements__ = graph._Imap

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
        self.labelattrs = helper.ensurelist(labelattrs)[:]

    def merge(self, other):
        if self.ticklevel is None or (other.ticklevel is not None and other.ticklevel < self.ticklevel):
            self.ticklevel = other.ticklevel
        if self.labellevel is None or (other.labellevel is not None and other.labellevel < self.labellevel):
            self.labellevel = other.labellevel


class timetexter:

    def __init__(self, formats="%c"):
        self.formats = formats

    def labels(self, ticks):
        for tick in ticks:
            if tick.labellevel is not None and tick.label is None:
                tick.label = tick.strftime(self.formats)


class timeaxis(graph._axis, _timemap):

     def __init__(self, part=[], rater=graph.axisrater(), **args):
        graph._axis.__init__(self, divisor=None, **args)
        if self.fixmin and self.fixmax:
            self.relsize = self.max - self.min
            self.relsize = 0.000001*self.relsize.microseconds + self.relsize.seconds + 3600*24*self.relsize.days
        self.part = part
        self.rater = rater


class symbol(graph.symbol):
    "skip float conversion -> symbol class"
    # shouldn't be needed -> the axis should be able to add data and find minimum and maximum!

    def minmidmax(self, point, i, mini, maxi, di, dmini, dmaxi):
        min = max = mid = None
        mid = point[i]
        if di is not None: min = point[i] - point[di]
        elif dmini is not None: min = point[i] - point[dmini]
        elif mini is not None: min = point[mini]
        if di is not None: max = point[i] + point[di]
        elif dmaxi is not None: max = point[i] + point[dmaxi]
        elif maxi is not None: max = point[maxi]
        if mid is not None:
            if min is not None and min > mid: raise ValueError("minimum error in errorbar")
            if max is not None and max < mid: raise ValueError("maximum error in errorbar")
        else:
            if min is not None and max is not None and min > max: raise ValueError("minimum/maximum error in errorbar")
        return min, mid, max

