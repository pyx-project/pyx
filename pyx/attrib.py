from math import sqrt
import unit

class halign:
   left   = "left"
   center = "center"
   right  = "right"
   
class valign:
   top    = "top"
   center = "center"
   bottom = "bottom"

class _linecap:
    def __init__(self, value=0):
       self.value=value
    def __str__(self):
       return "%d" % self.value
    def __int__(self):
       return self.value
    

class linecap:
    butt   = _linecap(0)
    round  = _linecap(1)
    square = _linecap(2)

class _linejoin:
    def __init__(self, value=0):
       self.value=value
    def __str__(self):
       return "%d" % self.value
    def __int__(self):
       return self.value
 
class linejoin(_linejoin):
    miter = _linejoin(0)
    round = _linejoin(1)
    bevel = _linejoin(2)

class _miterlimit:
    def __init__(self, value=10.0):
       self.value=value
    def __str__(self):
       return "%f" % self.value
    def __int__(self):
       return self.value

class miterlimit(_miterlimit):
    pass

class _dash:
    def __init__(self, pattern=[], offset=0):
       self.pattern=pattern
       self.offset=offset
    def __str__(self):
       patternstring=""
       for element in self.pattern:
           patternstring=patternstring + `element` + " "
                              
       return "[%s] %d" % (patternstring, self.offset)

class dash(_dash):
    pass
 
class _linestyle:
    def __init__(self, cap=linecap.butt, pattern=[], offset=0):
       self.cap=cap
       self.pattern=pattern
       self.offset=offset
       
class linestyle(_linestyle):
    solid      = _linestyle(linecap.butt,  [])
    dashed     = _linestyle(linecap.butt,  [2])
    dotted     = _linestyle(linecap.round, [0, 3])
    dashdotted = _linestyle(linecap.round, [0, 3, 3, 3])
 
class _linewidth(unit.length):
    def __init__(self, l):
       unit.length.__init__(self, l=l, default_type="w")
    

class linewidth(_linewidth):
    _base      = 0.02
 
    THIN       = _linewidth("%f cm" % (_base/sqrt(32)))
    THIn       = _linewidth("%f cm" % (_base/sqrt(16)))
    THin       = _linewidth("%f cm" % (_base/sqrt(8)))
    Thin       = _linewidth("%f cm" % (_base/sqrt(4)))
    thin       = _linewidth("%f cm" % (_base/sqrt(2)))
    normal     = _linewidth("%f cm" % _base)
    thick      = _linewidth("%f cm" % (_base*sqrt(2)))
    Thick      = _linewidth("%f cm" % (_base*sqrt(4)))
    THick      = _linewidth("%f cm" % (_base*sqrt(8)))
    THIck      = _linewidth("%f cm" % (_base*sqrt(16)))
    THICk      = _linewidth("%f cm" % (_base*sqrt(32)))
    THICK      = _linewidth("%f cm" % (_base*sqrt(64)))

class fontsize:
    tiny = "tiny"
    scriptsize = "scriptsize"
    footnotesize = "footnotesize"
    small = "small"
    normalsize = "normalsize"
    large = "large"
    Large = "Large"
    LARGE = "LARGE"
    huge = "huge"
    Huge = "Huge"
 
