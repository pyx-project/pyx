import sys
sys.path.insert(0, "..")
from pyx import *

text.set(mode="latex", docclass="scrartcl", docopt="11pt", fontmaps="tipa.map")
text.preamble(r"\usepackage{tipa}")
c = canvas.canvas()
c.text(0, 0, r"\textipa{[%s]}" % sys.argv[1])
c.writePDFfile("tipa%s.pdf" % sys.argv[2], bboxenlarge=0)
