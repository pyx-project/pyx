from pyx import *

text.set(text.LatexEngine, texenc='utf-8')
text.preamble(r'\usepackage[utf8]{inputenc}')

c = canvas.canvas()
c.text(0, 0, r'Héllò, wørłd!')
c.writeEPSfile()
c.writePDFfile()
c.writeSVGfile()
