class color:

    pass

class _grey(color):

    def __init__(self, level):
        assert 0<=level and level<=1, "grey value must be between 0 and 1"
        self.level=level

    def _PSCmd(self, canvas):
        return "%f setgray" % self.level

class grey(_grey):
    black = _grey(0.0)
    white = _grey(1.0)
    

class _rgb(color):
    def __init__(self, r=0.0, g=0.0, b=0.0):
        assert 0<=r and r<=1, "red value must be between 0 and 1"
        assert 0<=g and g<=1, "green value must be between 0 and 1"
        assert 0<=b and b<=1, "blue value must be between 0 and 1"
        self.r=r
        self.g=g
        self.b=b

    def _PSCmd(self, canvas):
        return "%f %f %f setrgbcolor" % (self.r, self.g, self.b)

class rgb(_rgb):
    red   = _rgb(1,0,0)
    green = _rgb(0,1,0)
    blue  = _rgb(0,0,1)
       

class _hsb(color):
    def __init__(self, h=0.0, s=0.0, b=0.0):
        assert 0<=h and h<=1, "hue value must be between 0 and 1"
        assert 0<=s and s<=1, "saturation value must be between 0 and 1"
        assert 0<=b and b<=1, "brightness value must be between 0 and 1"
        self.h=h
        self.s=s
        self.b=b

    def _PSCmd(self, canvas):
        return "%f %f %f setrgbcolor" % (self.h, self.s, self.b)

class hsb(_hsb):
    pass

class _cmyk(color):
    def __init__(self, c=0.0, m=0.0, y=0.0, k=0.0):
        assert 0<=c and c<=1, "cyan value must be between 0 and 1"
        assert 0<=m and m<=1, "magenta value must be between 0 and 1"
        assert 0<=y and y<=1, "yellow value must be between 0 and 1"
        assert 0<=k and k<=1, "black value must be between 0 and 1"
        self.c=c
        self.m=m
        self.y=y
        self.k=k

    def _PSCmd(self, canvas):
        return "%f %f %f %f setcmykcolor" % (self.c, self.m, self.y, self.k)

class cmyk(_cmyk):
    pass
