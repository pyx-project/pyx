from math import sqrt

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
 
class linestyle:
    solid      = (linecap.butt,  [])
    dashed     = (linecap.butt,  [2])
    dotted     = (linecap.round, [0, 3])
    dashdotted = (linecap.round, [0, 3, 3, 3])
 
class linewidth:
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
 

# helper stuff TODO: discuss this, create helper module?

def isnumber(x):
    import types
    if type(x) in [types.IntType, types.FloatType]:
        return 1
    return 0

