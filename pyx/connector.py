import math
from math import sin, cos, atan2, tan, hypot, acos, sqrt
import path, trafo, unit, helper


#########################
##   helpers
#########################

def _topt(length, default_type=None):
    if length is None: return None
    if default_type is not None:
        return unit.topt(unit.length(length, default_type=default_type))
    else:
        return unit.topt(unit.length(length))

def _torad(deg):
    return deg * math.pi / 180

def _todeg(rad):
    return rad * 180.0 / math.pi

class _connector(path.normpath):

    def omitends(self, box1, box2):
        """intersect a path with the boxes' paths"""

        sp = self.intersect(box1.path())[0]
        try: self.path = self.split(sp[:1])[1].path
        except: pass

        sp = self.intersect(box2.path())[0]
        try: self.path = self.split(sp[-1:])[0].path
        except: pass

    def shortenpath(self, dists):
        """shorten a path by the given distances"""

        center = [unit.topt(self.begin()[i]) for i in [0,1]]
        sp = self.intersect( path.circle_pt(center[0], center[1], dists[0]) )[0]
        try: self.path = self.split(sp[:1])[1].path
        except: pass

        center = [unit.topt(self.end()[i]) for i in [0,1]]
        sp = self.intersect( path.circle_pt(center[0], center[1], dists[1]) )[0]
        try: self.path = self.split(sp[-1:])[0].path
        except: pass


################
## classes
################


class _line(_connector):

    def __init__(self, box1, box2, boxdists=[0,0]):

        self.box1 = box1
        self.box2 = box2

        _connector.__init__(self,
            path.moveto_pt(*self.box1.center),
            path.lineto_pt(*self.box2.center))

        self.omitends(box1, box2)
        self.shortenpath(boxdists)


class _arc(_connector):

    def __init__(self, box1, box2, relangle=45,
                 absbulge=None, relbulge=None, boxdists=[0,0]):

        self.box1 = box1
        self.box2 = box2

        rel = [self.box2.center[0] - self.box1.center[0],
               self.box2.center[1] - self.box1.center[1]]
        distance = hypot(*rel)

        # usage of bulge overrides the relangle parameter
        if relbulge is not None or absbulge is not None:
            relangle = None
            bulge = 0
            try: bulge += absbulge
            except: pass
            try: bulge += relbulge*distance
            except: pass

            try: radius = abs(0.5 * (bulge + 0.25 * distance**2 / bulge))
            except: radius = 10 * distance # default value for too straight arcs
            radius = min(radius, 10 * distance)
            center = 2.0*(radius-abs(bulge))/distance
            center *= 2*(bulge>0.0)-1
        # otherwise use relangle
        else:
            bulge=None
            try: radius = 0.5 * distance / abs(cos(0.5*math.pi - _torad(relangle)))
            except: radius = 10 * distance
            try: center = tan(0.5*math.pi - _torad(relangle))
            except: center = 0

        # up to here center is only
        # the distance from the middle of the straight connection
        center = [0.5 * (self.box1.center[0] + self.box2.center[0] - rel[1]*center),
                  0.5 * (self.box1.center[1] + self.box2.center[1] + rel[0]*center)]
        angle1 = atan2(*[self.box1.center[i] - center[i]  for i in [1,0]])
        angle2 = atan2(*[self.box2.center[i] - center[i]  for i in [1,0]])

        # draw the arc in positive direction by default
        # negative direction if relangle<0 or bulge<0
        if (relangle is not None and relangle < 0) or (bulge is not None and bulge < 0):
            _connector.__init__(self,
                path.moveto_pt(*self.box1.center),
                path.arcn_pt(center[0], center[1], radius, _todeg(angle1), _todeg(angle2)))
        else:
            _connector.__init__(self,
                path.moveto_pt(*self.box1.center),
                path.arc_pt(center[0], center[1], radius, _todeg(angle1), _todeg(angle2)))

        self.omitends(box1, box2)
        self.shortenpath(boxdists)


class _curve(_connector):

    def __init__(self, box1, box2,
                 relangle1=45, relangle2=45,
                 absangle1=None, absangle2=None,
                 absbulge=0, relbulge=0.39, boxdists=[0,0]):
        # relbulge=0.39 and relangle1,2=45 leads
        # approximately to the arc with angle=45

        self.box1 = box1
        self.box2 = box2

        rel = [self.box2.center[0] - self.box1.center[0],
               self.box2.center[1] - self.box1.center[1]]
        distance = hypot(*rel)
        dangle = atan2(rel[1], rel[0])

        # calculate the armlength and angles for the control points
        bulge = abs(distance*relbulge + absbulge)

        if absangle1 is not None:
            angle1 = _torad(absangle1)
        else:
            angle1 = dangle - _torad(relangle1)
        if absangle2 is not None:
            angle2 = _torad(absangle2)
        else:
            angle2 = dangle + _torad(relangle2)

        control1 = [cos(angle1), sin(angle1)]
        control2 = [cos(angle2), sin(angle2)]
        control1 = [self.box1.center[i] + control1[i] * bulge  for i in [0,1]]
        control2 = [self.box2.center[i] - control2[i] * bulge  for i in [0,1]]

        _connector.__init__(self,
            path.moveto_pt(*self.box1.center),
            path.curveto_pt(*(control1 + control2 + helper.ensurelist(self.box2.center))))

        self.omitends(box1, box2)
        self.shortenpath(boxdists)


class _twolines(_connector):

    def __init__(self, box1, box2,
                 absangle1=None, absangle2=None,
                 relangle1=None, relangle2=None, relangleM=None,
                 length1=None, length2=None,
                 bezierradius=None, beziersoftness=1,
                 arcradius=None,
                 boxdists=[0,0]):

        self.box1 = box1
        self.box2 = box2

        begin = self.box1.center
        end = self.box2.center
        rel = [self.box2.center[0] - self.box1.center[0],
               self.box2.center[1] - self.box1.center[1]]
        distance = hypot(*rel)
        dangle = atan2(rel[1], rel[0])

        if relangle1 is not None: relangle1 = _torad(relangle1)
        if relangle2 is not None: relangle2 = _torad(relangle2)
        if relangleM is not None: relangleM = _torad(relangleM)
        # absangle has priority over relangle:
        if absangle1 is not None: relangle1 = dangle - _torad(absangle1)
        if absangle2 is not None: relangle2 = math.pi - dangle + _torad(absangle2)

        # check integrity of arguments
        no_angles, no_lengths=0,0
        for anangle in (relangle1, relangle2, relangleM):
            if anangle is not None: no_angles += 1
        for alength in (length1, length2):
            if alength is not None: no_lengths += 1

        if no_angles + no_lengths != 2:
            raise NotImplementedError, "Please specify exactly two angles or lengths"

        # calculate necessary angles and sidelengths
        # always length1 and relangle1 !
        # the case with two given angles
        if no_angles==2:
            if relangle1 is None: relangle1 = math.pi - relangle2 - relangleM
            elif relangle2 is None: relangle2 = math.pi - relangle1 - relangleM
            elif relangleM is None: relangleM = math.pi - relangle1 - relangle2
            length1 = distance * abs(sin(relangle2)/sin(relangleM))
            middle = self._middle_a(begin, dangle, length1, relangle1)
        # the case with two given lengths
        elif no_lengths==2:
            relangle1 = acos((distance**2 + length1**2 - length2**2) / (2.0*distance*length1))
            middle = self._middle_a(begin, dangle, length1, relangle1)
        # the case with one length and one angle
        else:
            if relangle1 is not None:
                if length1 is not None:
                    middle = self._middle_a(begin, dangle, length1, relangle1)
                elif length2 is not None:
                    length1 = self._missinglength(length2, distance, relangle1)
                    middle = self._middle_a(begin, dangle, length1, relangle1)
            elif relangle2 is not None:
                if length1 is not None:
                    length2 = self._missinglength(length1, distance, relangle2)
                    middle = self._middle_b(end, dangle, length2, relangle2)
                elif length2 is not None:
                    middle = self._middle_b(end, dangle, length2, relangle2)
            elif relangleM is not None:
                if length1 is not None:
                    length2 = self._missinglength(distance, length1, relangleM)
                    relangle1 = acos((distance**2 + length1**2 - length2**2) / (2.0*distance*length1))
                    middle = self._middle_a(begin, dangle, length1, relangle1)
                elif length2 is not None:
                    length1 = self._missinglength(distance, length2, relangleM)
                    relangle1 = acos((distance**2 + length1**2 - length2**2) / (2.0*distance*length1))
                    middle = self._middle_a(begin, dangle, length1, relangle1)
            else:
                raise NotImplementedError, "I found a strange combination of arguments"

        _connector.__init__(self,
            path.moveto_pt(*self.box1.center),
            path.lineto_pt(*middle),
            path.lineto_pt(*self.box2.center))

        self.omitends(box1, box2)
        self.shortenpath(boxdists)

    def _middle_a(self, begin, dangle, length1, angle1):
        a = dangle - angle1
        dir = [cos(a), sin(a)]
        return [begin[i] + length1*dir[i]  for i in [0,1]]

    def _middle_b(self, end, dangle, length2, angle2):
        # a = -math.pi + dangle + angle2
        return self._middle_a(end, -math.pi+dangle, length2, -angle2)

    def _missinglength(self, lenA, lenB, angleA):
        # calculate lenC, where side A and angleA are opposite
        tmp1 = lenB*cos(angleA)
        tmp2 = sqrt(tmp1**2 - lenB**2 + lenA**2)
        if tmp1>tmp2: return tmp1-tmp2
        return tmp1+tmp2



class line(_line):

    """a line is the straight connector between the centers of two boxes"""

    def __init__(self, box1, box2, boxdists=[0,0]):

        boxdists_pt = [_topt(helper.getitemno(boxdists,i), default_type="v") for i in [0,1]]

        _line.__init__(self, box1, box2, boxdists=boxdists_pt)


class curve(_curve):

    """a curve is the curved connector between the centers of two boxes.
    The constructor needs both angle and bulge"""


    def __init__(self, box1, box2,
                 relangle1=45, relangle2=45,
                 absangle1=None, absangle2=None,
                 absbulge=0, relbulge=0.39,
                 boxdists=[0,0]):

        boxdists_pt = [_topt(helper.getitemno(boxdists,i), default_type="v") for i in [0,1]]

        _curve.__init__(self, box1, box2,
                        relangle1=relangle1, relangle2=relangle2,
                        absangle1=absangle1, absangle2=absangle2,
                        absbulge=_topt(absbulge), relbulge=relbulge,
                        boxdists=boxdists_pt)

class arc(_arc):

    """an arc is a round connector between the centers of two boxes.
    The constructor gets
         either an angle in (-pi,pi)
         or a bulge parameter in (-distance, distance)
           (relbulge and absbulge are added)"""

    def __init__(self, box1, box2, relangle=45,
                 absbulge=None, relbulge=None, boxdists=[0,0]):

        boxdists_pt = [_topt(helper.getitemno(boxdists,i), default_type="v") for i in [0,1]]

        _arc.__init__(self, box1, box2,
                      relangle=relangle,
                      absbulge=_topt(absbulge), relbulge=relbulge,
                      boxdists=boxdists_pt)


class twolines(_twolines):

    """a twolines is a connector consisting of two straight lines.
    The construcor takes a combination of angles and lengths:
      either two angles (relative or absolute)
      or two lenghts
      or one length and one angle"""

    def __init__(self, box1, box2,
                 absangle1=None, absangle2=None,
                 relangle1=None, relangle2=None, relangleM=None,
                 length1=None, length2=None,
                 bezierradius=None, beziersoftness=1,
                 arcradius=None,
                 boxdists=[0,0]):

        boxdists_pt = [_topt(helper.getitemno(boxdists,i), default_type="v") for i in [0,1]]

        _twolines.__init__(self, box1, box2,
                       absangle1=absangle1, absangle2=absangle2,
                       relangle1=relangle1, relangle2=relangle2,
                       relangleM=relangleM,
                       length1=_topt(length1), length2=_topt(length2),
                       bezierradius=_topt(bezierradius), beziersoftness=1,
                       arcradius=_topt(arcradius),
                       boxdists=boxdists_pt)



