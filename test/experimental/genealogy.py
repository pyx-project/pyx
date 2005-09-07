from pyx import *

def bracepath(w1, w2, h=0.1, slant=0.1):
    p1 = path.path(path.moveto(-w1, -h),
                   path.lineto(-w1+slant, 0),
                   path.lineto(-slant, 0),
                   path.lineto(0, h))
    p2 = path.path(path.moveto(0, h),
                   path.lineto(slant, 0),
                   path.lineto(w2-slant, 0),
                   path.lineto(w2, -h))
    p1 = deformer.smoothed(10*h).deform(p1)
    p2 = deformer.smoothed(10*h).deform(p2)
    p = p1 << p2
    p = deformer.smoothed(0.1*h).deform(p)
    return p.split([0.05, p.end()-0.05])[1]

def brace(c, x, y, w1, w2):
    # This is a well known trick to draw a line with an eliptic pen.
    # you just stroke the path with a circular pen and transform the
    # result. Since we only do a horizontal scaling here, the widths
    # w1 and w2 don't need to be adjusted.
    sc = canvas.canvas([trafo.translate(x, y), trafo.scale(1, 2)])
    c.insert(sc)
    sc.stroke(bracepath(w1, w2), [style.linecap.round])

linespacing = 1.4*text.text(0, 0, "X").height

class person(canvas.canvas):

    def __init__(self, lines, childs=[],
                       distance=0.5, relpos=0.5):
        canvas.canvas.__init__(self)
        self.width = 0
        y = 0
        for line in lines:
            t = text.text(0, y, line, [text.halign.center])
            if t.width > self.width:
                self.width = t.width
            self.insert(t)
            y -= linespacing
        if childs:
            width = sum([child.width for child in childs], 0)
            width += distance*(len(childs)-1)
            brace(self, 0, y, relpos*width, (1-relpos)*width)
            x = -relpos*width
            for child in childs:
                x += 0.5*child.width
                self.insert(child, [trafo.translate(x, y-2*linespacing)])
                x += 0.5*child.width + distance

p = person([r"Otto III.", r"* 1215 -- $\dagger$ 1267"],
           [person(["Johann III."]),
            person(["Otto V. der Lange"],
                   [person(["Otto"]),
                    person(["Albrecht"]),
                    person(["Hermann"]),
                    person(["Beatrix", "etc."])],
                   relpos=0.8),
            person(["Albrecht III."],
                   [person(["Otto"]),
                    person(["Johann"]),
                    person(["Beatrix"]),
                    person(["Margarette"])],
                   relpos=0.2),
            person(["Otto IV. der Kleine"]),
            person(["Kunigunde"])])
p.writeEPSfile("genealogy")
