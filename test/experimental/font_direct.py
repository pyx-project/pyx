import sys; sys.path.insert(0, "../..")

from pyx import *
from pyx.config import open, format
from pyx.font import T1font
from pyx.font.t1file import from_PF_bytes
from pyx.font.afmfile import AFMfile

f = T1font(from_PF_bytes(open("cmr10", [format.type1]).read()),
           AFMfile(open("cmr10", [format.afm], ascii=True)))

c = canvas.canvas()

def show(x_pt, y_pt, text, size_pt, **kwargs):
    t = f.text_pt(x_pt, y_pt, text, size_pt, **kwargs)
    c.insert(t)
    c.stroke(t.bbox().rect(), [style.linewidth(0)])

show(0, 0, "Hello, World!", 10)
show(0, -30, "Hello, World!", 10, spaced_pt=5)
show(0, -60, "Hello, World!", 10, spaced_pt=10)
show(0, -90, "Hello, World!", 10, kerning=True)

show(200, 0, "Hello, World!", 25)
show(200, -30, "Hello, World!", 25, spaced_pt=5)
show(200, -60, "Hello, World!", 25, spaced_pt=10)
show(200, -90, "Hello, World!", 25, kerning=True)

c.writeEPSfile()
c.writeEPSfile("font_direct_textaspath", write_textaspath=True)
c.writePDFfile(write_compress=False)
c.writePDFfile("font_direct_textaspath", write_textaspath=True, write_compress=False)
c.writeSVGfile(write_textaspath=False)
c.writeSVGfile("font_direct_textaspath", write_textaspath=True)
