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

class linecap:
    butt   = 0
    round  = 1
    square = 2
 
class linejoin:
    miter = 0
    round = 1
    bevel = 2

class miterlimit:
    def __init__(self, limit=10.0)
        self.value=limit

class dash:
    def __init__(self, pattern=0, offset=0):
        self.value=(pattern, offset)
 
class linestyle:
    solid      = (linecap.butt,  [])
    dashed     = (linecap.butt,  [2])
    dotted     = (linecap.round, [0, 3])
    dashdotted = (linecap.round, [0, 3, 3, 3])
 
class linewidth(unit.length):
    _base      = 0.02
 
    THIN       = "%f w cm" % (_base/sqrt(32))
    THIn       = "%f w cm" % (_base/sqrt(16))
    THin       = "%f w cm" % (_base/sqrt(8))
    Thin       = "%f w cm" % (_base/sqrt(4))
    thin       = "%f w cm" % (_base/sqrt(2))
    normal     = "%f w cm" % _base
    thick      = "%f w cm" % (_base*sqrt(2))
    Thick      = "%f w cm" % (_base*sqrt(4))
    THick      = "%f w cm" % (_base*sqrt(8))
    THIck      = "%f w cm" % (_base*sqrt(16))
    THICk      = "%f w cm" % (_base*sqrt(32))
    THICK      = "%f w cm" % (_base*sqrt(64))

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
 
