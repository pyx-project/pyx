class _grey:

    def __init__(self, level):
        self.level=level

    def _PSAddCmd(self, canvas):
        canvas._PSAddCmd("%f setgray" % self.level)

class grey(_grey):
    black = _grey(0.0)
    white = _grey(1.0)
    

class _rgb:
    def __init__(self, r=0.0, g=0.0, b=0.0):
        self.r=r
        self.g=g
        self.b=b

    def _PSAddCmd(self, canvas):
        canvas._PSAddCmd("%f %f %f setrgbcolor" % (self.r, self.g, self.b))

class rgb(_rgb):
    pass
       

class _hsb:
    def __init__(self, h=0.0, s=0.0, b=0.0):
        self.h=h
        self.s=s
        self.b=b

    def _PSAddCmd(self, canvas):
        canvas._PSAddCmd("%f %f %f setrgbcolor" % (self.h, self.s, self.b))

class hsb(_hsb):
    pass

class _cmyk:
    def __init__(self, c=0.0, m=0.0, y=0.0, k=0.0):
        self.c=c
        self.m=m
        self.y=y
        self.k=k

    def _PSAddCmd(self, canvas):
        canvas._PSAddCmd("%f %f %f %f setcmykcolor" % (self.c, self.m, self.y, self.k))

class cmyk(_cmyk):
    pass
