import sys; sys.path.insert(0, "../..")

from pyx import *

c = canvas.canvas()
c.text(0, 0, "$ooooooooooooowo$")
c.text(0, 1, "$E=mc^2$")
c.text(0, 2, r"\int\limits_{-\infty}^\infty \!{\rm d}x\, e^{-a x^2} = \sqrt{\pi\over a}", [text.mathmode])
c.writePDFfile("pdftext")
c.writeEPSfile("pdftext")
