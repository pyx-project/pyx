from pyx import canvas, unit
import t1file

class font:

    def text_pt(self, x, y, size, text, encoding, **features):
        # features: kerning, ligatures
        codepoints = [encoding[character] for character in text]
        return T1text_pt(self, x, y, size, codepoints)

    def text(self, x, y, size, text, encoding, **features):
        return self.text_pt(unit.topt(x), unit.topt(y), size, text, encoding, **features)


class T1font(font):

    def __init__(self, pfbname=None):
        self.t1file = t1file.PFBfile(pfbname)


class T1text_pt(canvas.canvasitem):

    def __init__(self, font, x_pt, y_pt, size, codepoints):
        self.font = font
        self.x_pt = x_pt
        self.y_pt = y_pt
        self.size = size
        self.codepoints = codepoints

    def processPS(self, file, writer, context, registry, bbox):
        # file.write("/%s-encoded %g selectfont\n" % (self.font.name, self.size))
        file.write("/%s-encoded %g selectfont\n" % ("XXX", self.size))
        file.write("%f %f moveto (" % (self.x_pt, self.y_pt))
        for codepoint in self.codepoints:
            if codepoint > 32 and codepoint < 127 and chr(codepoint) not in "()[]<>\\":
                file.write("%s" % chr(codepoint))
            else:
                file.write("\\%03o" % codepoint)
        file.write(") show\n")
