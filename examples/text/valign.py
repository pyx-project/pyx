from pyx import *

c = canvas.canvas()

# apply global TeX setting
text.preamble(r"\parindent=0pt")
w = 1.2 # an appropriate parbox width for spam & eggs

# vertical alignments by margins
c.stroke(path.line(0, 4, 8, 4), [style.linewidth.THin])
c.text(0, 4, r"spam \& eggs", [text.parbox(w), text.valign.top])
c.text(3, 4, r"spam \& eggs", [text.parbox(w), text.valign.middle])
c.text(6, 4, r"spam \& eggs", [text.parbox(w), text.valign.bottom])

# vertical alignments by baselines
c.stroke(path.line(0, 2, 8, 2), [style.linewidth.THin])
c.text(0, 2, r"spam \& eggs", [text.parbox(w, baseline=text.parbox.top)])
c.text(3, 2, r"spam \& eggs", [text.parbox(w, baseline=text.parbox.middle)])
c.text(6, 2, r"spam \& eggs", [text.parbox(w, baseline=text.parbox.bottom)])

# vertical shifts
c.stroke(path.line(0, 0, 8, 0), [style.linewidth.THin])
c.text(0, 0, r"x=0", [text.mathmode, text.vshift.topzero])
c.text(2, 0, r"x=0", [text.mathmode, text.vshift.middlezero])
c.text(4, 0, r"x=0", [text.mathmode, text.vshift.bottomzero])
c.text(6, 0, r"x=0", [text.mathmode, text.vshift.mathaxis])

c.writeEPSfile("valign")
c.writePDFfile("valign")
c.writeSVGfile("valign")
